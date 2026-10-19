"""Recover BSP authoring data into private cache; never overwrite kit source files.

Recovery is a prerequisite for rebuilding original map pieces, not an export
success signal. Shader resolution and a validated compile are still required.
"""
import hashlib
import tempfile
import zlib
from pathlib import Path
from . import jobs
from .catalog import read_json, write_json

MAX_SOURCE_BYTES = 256 * 1024 * 1024


def unpack(data, size, crc32):
    if not isinstance(size, int) or not 0 < size <= MAX_SOURCE_BYTES:
        raise RuntimeError('Embedded source exceeds the supported recovery size.')
    decoder = zlib.decompressobj()
    raw = decoder.decompress(data, size + 1)
    if len(raw) != size or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise RuntimeError('Embedded geometry is incomplete or its stored size is incorrect.')
    # Halo stores the uncomplemented CRC register (opposite of zlib's result).
    if (zlib.crc32(raw) ^ 0xffffffff) != crc32:
        raise RuntimeError('Embedded geometry failed its checksum. It was not accepted for rebuilding.')
    return raw


def recover(config, bsp, cancel=None):
    kit = Path(config['kit']).resolve()
    parts = bsp.replace('\\', '/').split('/')
    if any(p in ('', '.', '..') or ':' in p for p in parts):
        raise RuntimeError('Invalid BSP source path.')
    source = kit / 'tags' / ('/'.join(parts) + '.scenario_structure_bsp')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    root = Path(config['cache']) / 'source_geometry' / digest
    record = read_json(root / 'source.json')
    if record and 'shaders' in record:
        valid = True
        for item in record['files']:
            path = root / item['file']
            if path.resolve().parent != root.resolve() or not path.is_file():
                valid = False; break
            if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                valid = False; break
        if valid:
            return dict(record, directory=str(root))
    root.parent.mkdir(parents=True, exist_ok=True)
    # Each invocation gets a fresh folder, including helper result and blobs.
    with tempfile.TemporaryDirectory(prefix='recover-', dir=root.parent) as work:
        work = Path(work)
        result = jobs.helper('tags', dict(operation='recover_source', kit=str(kit),
            scenario=bsp, output=str(work / 'result.json')), work, cancel)
        recovered = []
        for index, item in enumerate(result['files']):
            blob = work / item['compressed']
            if blob.resolve().parent != work.resolve():
                raise RuntimeError('Invalid compressed source path.')
            raw = unpack(blob.read_bytes(), item['size'], item['crc32'])
            name = 'source-' + str(index) + '.ass'
            (work / name).write_bytes(raw)
            recovered.append(dict(file=name, source_path=item['source_path'],
                sha256=hashlib.sha256(raw).hexdigest(), size=len(raw)))
        if not recovered:
            raise RuntimeError('No source geometry was recovered.')
        if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise RuntimeError('Source BSP changed during recovery. Retry with tag editors closed.')
        if cancel and cancel.is_set():
            raise jobs.Cancelled('Source recovery cancelled.')
        root.mkdir(exist_ok=True)
        for item in recovered:
            (root / item['file']).write_bytes((work / item['file']).read_bytes())
        record = dict(version=1, source=bsp, tag_sha256=digest, files=recovered,
                      shaders=result.get('shaders', []))
        write_json(root / 'source.json', record)
    return dict(record, directory=str(root))
