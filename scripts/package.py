"""Build audited public archives from this repository, never its parent folder."""
import ast
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
HELPERS={
    'extractor/HaloBridge.Extractor.exe','extractor/HaloBridge.Extractor.dll',
    'extractor/HaloBridge.Extractor.deps.json','extractor/HaloBridge.Extractor.runtimeconfig.json',
    'extractor/Reclaimer.Blam.dll','extractor/Reclaimer.Core.dll','tags/HaloBridge.Tags.exe',
}
SKIP={'__pycache__','obj','bin','.git','dist'}
FORBIDDEN={'.map','.blend','.blend1','.amf','.rmf','.jms','.ass','.dds','.tif','.png','.pdb','.pyc','.log'}
PRIVATE_NAMES={'catalogue.json','preview.json','stamp.json','collision.json','manifest.json','ManagedBlam.dll'}

def audit(name,data):
    path=Path(name)
    is_project_logo = name.replace('\\', '/') in {'docs/halobridgelogo.png', 'halo_bridge/docs/halobridgelogo.png'}
    if (path.suffix.lower() in FORBIDDEN and not is_project_logo) or path.name in PRIVATE_NAMES or path.name.lower() in ('xcompress32.dll','xcompress64.dll'):
        raise ValueError('Private or unsupported content in archive: '+name)
    # Scan text and binary contents for the build user's absolute home path.
    home=str(Path.home())
    variants={home,home.replace('\\','/'),home.replace('\\','\\\\')}
    if any(v.encode(enc).lower() in data.lower() for v in variants for enc in ('utf-8','utf-16-le')):
        raise ValueError('Personal build path in '+name)
    if path.suffix=='.py':compile(data.decode('utf-8-sig'),name,'exec')

def write_zip(path,files):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,file in sorted(files.items()):
            data=file.read_bytes();audit(name,data)
            entry=zipfile.ZipInfo(name.replace('\\','/'),(2026,1,1,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED;entry.external_attr=0o644<<16
            archive.writestr(entry,data)
    with zipfile.ZipFile(path) as archive:
        if archive.testzip():raise ValueError('Archive verification failed')

def main():
    info=ast.literal_eval(ast.parse((ROOT/'halo_bridge/__init__.py').read_text(encoding='utf-8-sig')).body[0].value)
    version='.'.join(map(str,info['version']))
    files={}
    for folder in ('halo_bridge','source','scripts','tests','docs','.github'):
        for file in (ROOT/folder).rglob('*'):
            if file.is_file() and not any(p in SKIP for p in file.relative_to(ROOT).parts):
                if file.suffix.lower() in ('.exe','.dll'):raise ValueError('Unexpected source binary: '+str(file))
                files[file.relative_to(ROOT).as_posix()]=file
    for file in ROOT.iterdir():
        if file.is_file() and (file.suffix=='.md' or file.name in ('LICENSE','.gitignore')):files[file.name]=file
    addon={k:v for k,v in files.items() if k.startswith('halo_bridge/')}
    for name,file in files.items():
        if name.startswith('docs/') or '/' not in name and (name.endswith('.md') or name=='LICENSE'):
            addon['halo_bridge/'+name]=file
    for name in HELPERS:
        file=ROOT/'halo_bridge/bin'/name
        if not file.is_file():raise ValueError('Build helpers first; missing '+name)
        addon['halo_bridge/bin/'+name]=file
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    outputs=[dist/f'HaloBridge-{version}.zip',dist/f'HaloBridge-{version}-source.zip']
    write_zip(outputs[0],addon);write_zip(outputs[1],files)
    for output in outputs:print(output.name)


if __name__=='__main__':main()
