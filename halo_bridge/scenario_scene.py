"""Import a Halo 3 level from its Editing Kit .scenario tag.

The scenario is the authoritative description of the level: which BSPs it
uses, which objects are placed where, and which shader each surface uses.
This route reads that tag hierarchy with ManagedBlam and builds geometry from
the authoring sources (ASS/JMS) that the kit tags retain as import info. No
compiled .map data is used for geometry, placement or shader identity.

The installed MCC map is only an optional preview-texture source, looked up by
exact shader tag path, and a fallback mesh for render models that have no
embedded source. Both uses are reported in the import report.
"""
import glob
import json
import shutil
import time
from pathlib import Path
from . import jobs
from . import source_formats as sf
from .catalog import read_json, write_json, stable_id, fingerprint
from .source_geometry import unpack

KIND = 'halo3_scenario_scene'
# 2: JMS line strings, lighting-parameter names and <collection>\shaders lookup;
# 3: ASS line strings, "blur)!=" / "'name" material names, collection-folder preference.
# 4: game field (Halo 3, ODST, Reach); BSPs without kit sources borrow the map geometry.
# Cached scenes from earlier versions are rebuilt.
# 5: faces without a material are skipped individually instead of failing the import
# or dropping their whole BSP object.
VERSION = 5
# Placement categories built into Blender, and how each one exports.
EXPORT = {'Scenery': 'scenery', 'Vehicles': 'vehicle', 'Crates': 'static',
          'Machines': 'static', 'Controls': 'static'}
REFERENCE_ONLY = ('Weapons', 'Equipment')
LIMITATIONS = [
    'Geometry comes from the source files stored in the Editing Kit tags; shader assignments come from the tags.',
    'Scenery stays original scenery while its mesh is unedited; vehicles keep their vehicle tags. Edited objects export as static geometry.',
    'Crates, machines and controls export as static geometry. Doors, lifts and other device behavior are not reproduced.',
    'Weapons and equipment are imported for reference only and are not exported.',
    'Portals, sky, seam sealer and other special surfaces are kept in a separate collection and are not exported.',
    'AI, scripts, triggers, decals, lighting and gameplay settings stay in the original scenario; they are not copied to the prepared level.',
]


def safe_tag(path):
    value = str(path or '').strip().replace('/', '\\')
    parts = value.split('\\')
    if not value or any(p in ('', '.', '..') or ':' in p for p in parts):
        raise RuntimeError('Enter a scenario path relative to the Editing Kit tags folder, for example levels\\multi\\guardian\\guardian.')
    return value.removesuffix('.scenario')


def tag_file(kit, tag, extension):
    """Path of a tag inside the kit; tag paths always use backslashes."""
    parts = safe_tag(tag).split('\\')
    return Path(kit, 'tags', *parts[:-1], parts[-1] + extension)


def scenarios(kit):
    """Every .scenario under the kit's tags\\levels folder, as tag paths."""
    root = Path(kit) / 'tags'
    levels = root / 'levels'
    if not levels.is_dir():
        return []
    found = [str(p.relative_to(root).with_suffix('')).replace('/', '\\') for p in levels.rglob('*.scenario') if p.is_file()]
    return sorted(found, key=str.casefold)


def leaf(path):
    return str(path or '').replace('\\', '/').rsplit('/', 1)[-1]


def texture_map(config, scenario):
    """The installed MCC map for this scenario, if one exists (texture previews only)."""
    folder = Path(config.get('maps') or '')
    if not config.get('maps') or not folder.is_dir():
        return None
    candidate = folder / (leaf(scenario) + '.map')
    return candidate if candidate.is_file() else None


def shader_collections(kit):
    """Collection prefix -> tags folder, from levels\\shader_collections.txt."""
    path = Path(kit) / 'tags' / 'levels' / 'shader_collections.txt'
    result = {}
    if not path.is_file():
        return result
    for line in path.read_text(errors='replace').splitlines():
        parts = line.split(';')[0].split()
        if len(parts) == 2 and parts[0] != '*':
            result[parts[0].lower()] = parts[1].rstrip('\\').replace('/', '\\')
    return result


class Materials:
    """Manifest material table shared by every mesh in one scenario import."""

    def __init__(self, kit):
        self.kit = Path(kit)
        self.collections = shader_collections(kit)
        self.table = {}
        self.unresolved = {}

    def _resolve(self, base, shaders):
        lowered = {s.lower(): s for s in shaders}
        name, folder = base, None
        if ' ' in base:
            prefix, name = base.split(None, 1)
            folder = self.collections.get(prefix.lower())
            if folder:
                # Level collections keep shaders in a "shaders" subfolder
                # (guardian -> levels\multi\guardian\shaders\...); shared ones
                # already name the shader folder (mpshare -> levels\shared\shaders\multi).
                candidates = [folder + '\\shaders\\' + name, folder + '\\' + name]
                for candidate in candidates:
                    if candidate.lower() in lowered:
                        return lowered[candidate.lower()]
                for candidate in candidates:
                    try:
                        probe = tag_file(self.kit, candidate, '')
                    except RuntimeError:
                        continue  # Not a usable tag path.
                    if probe.parent.is_dir() and any(probe.parent.glob(glob.escape(probe.name) + '.shader*')):
                        return candidate
        matches = [s for s in shaders if leaf(s).lower() in (base.lower(), name.lower())]
        if len(matches) > 1 and folder:
            # Shaders may sit in subfolders (voi rubber_wire -> 040_voi\shaders\plastic\rubber_wire);
            # prefer the one inside the named collection.
            matches = [s for s in matches if s.lower().startswith(folder.lower() + '\\')]
        return matches[0] if len(matches) == 1 else ''

    def get(self, source_name, shaders, lighting=(), owner=''):
        """Material id for a source material name in a tag's shader set."""
        if sf.is_special(source_name):
            key = ('special', source_name.strip().lower())
            shader, flags, name = '', [], source_name.strip()
        else:
            base, symbols = sf.split_material_name(source_name)
            shader = self._resolve(base, shaders)
            flags = sf.material_flags(source_name, lighting)
            name = leaf(shader) if shader else base
            if symbols:
                name += ' ' + symbols
            key = ('shader', shader.lower() if shader else 'unresolved:' + base.lower(), tuple(flags))
            if not shader:
                self.unresolved.setdefault(base, set()).add(owner)
        if key not in self.table:
            self.table[key] = dict(id=len(self.table), name=name or 'unnamed', shader=shader, alpha='opaque',
                                   textures=[], flags=flags, source_name=source_name, special=key[0] == 'special')
        return self.table[key]['id']

    def metas(self):
        return list(self.table.values())

    def special(self, material_id):
        return any(m['id'] == material_id and m['special'] for m in self.table.values())


def _sources(row, blobs):
    """Decompress and checksum each embedded source file."""
    result = []
    for item in row.get('sources', []):
        blob = (blobs / item['compressed']).resolve()
        if blob.parent != blobs.resolve():
            raise RuntimeError('Invalid compressed source path.')
        raw = unpack(blob.read_bytes(), item['size'], item['crc32'])
        result.append((item['source_path'], raw.decode('utf-8', errors='replace')))
    return result


def _variant_selection(info, variant):
    """Region -> permutation chosen by the model's variant definition."""
    variants = info.get('variants') or []
    chosen = None
    # Placement variant, then the object's default model variant, then 'default', then the first.
    for name in (variant, info.get('default_variant', ''), 'default'):
        if name and chosen is None:
            chosen = next((v for v in variants if v.get('name', '').lower() == name.lower()), None)
    if chosen is None and variants:
        chosen = variants[0]
    wanted = {}
    if chosen:
        blocks = chosen.get('blocks', {})
        regions = blocks.get('regions') or next(iter(blocks.values()), [])
        for region in regions:
            inner = region.get('blocks', {})
            permutations = inner.get('permutations') or next(iter(inner.values()), [])
            if region.get('name') and permutations and permutations[0].get('name'):
                wanted[region['name']] = permutations[0]['name']
    return wanted, (chosen or {}).get('name', '')


def _write_mesh(folder, name, materials, records):
    meshes = [r for r in records if r['segments']]
    if not meshes:
        return None
    used = {s['material'] for m in meshes for s in m['segments']}
    write_json(folder / name, dict(version=1, materials=[m for m in materials if m['id'] in used], meshes=meshes))
    return name


def build(config, scenario, data, folder, progress=None, cancel=None):
    """Turn the tag helper's scenario description into a HaloBridge scene manifest."""
    progress = progress or (lambda message: None)
    materials = Materials(config['kit'])
    warnings = list(data.get('warnings', []))
    meshes, placements, pending = {}, [], {}
    counts = {}
    decoded = 0

    def check():
        if cancel and cancel.is_set():
            raise jobs.Cancelled('Scenario import cancelled.')

    # ---- BSPs: one Blender object per ASS instance, sharing instanced meshes.
    for bsp in data.get('bsps', []):
        check()
        name = leaf(bsp['tag'])
        try:
            files = [(p, t) for p, t in _sources(bsp, folder) if p.lower().endswith('.ass')]
        except RuntimeError as error:
            warnings.append('BSP ' + bsp['tag'] + ': ' + str(error))
            continue
        if not files:
            warnings.append('BSP ' + bsp['tag'] + ': no embedded source geometry in its Editing Kit tag. Use Import entire .map for this level.')
            continue
        bsp_ok = False
        for number, (source_path, text) in enumerate(files):
            progress('Reading BSP source ' + name + ' (' + leaf(source_path) + ')')
            try:
                ass = sf.parse_ass(text, leaf(source_path))
                matrices = sf.ass_world_matrices(ass)
            except sf.SourceError as error:
                warnings.append('BSP ' + bsp['tag'] + ': ' + str(error))
                continue
            ids = [materials.get(m['name'], bsp.get('shaders', []), m['lighting'], bsp['tag']) for m in ass['materials']]
            special_ids = {i for i in ids if materials.special(i)}
            built = {}
            unassigned = 0
            for index, item in enumerate(ass['objects']):
                check()
                if item['kind'] != 'MESH' or not item['triangles']:
                    continue
                # Faces without a material (-1) were never assigned a shader in the
                # source scene; only those faces are left out, not the whole object.
                valid = [t for t in item['triangles'] if 0 <= t[0] < len(ids)]
                unassigned += len(item['triangles']) - len(valid)
                if not valid:
                    continue
                parts = (('geometry', [t for t in valid if ids[t[0]] not in special_ids]),
                         ('special', [t for t in valid if ids[t[0]] in special_ids]))
                for kind, triangles in parts:
                    if not triangles:
                        continue
                    try:
                        record, dropped = sf.mesh_record(item['positions'], item['normals'], item['uvs'], triangles, ids)
                    except sf.SourceError as error:
                        warnings.append('BSP ' + bsp['tag'] + ': ' + str(error))
                        continue
                    key = 'bsp%d_%d_%d_%s' % (bsp['index'], number, index, kind)
                    file = _write_mesh(folder, key + '.json', materials.metas(), [record])
                    if file:
                        meshes[key] = file
                        built.setdefault(index, {})[kind] = key
                    if dropped:
                        warnings.append(bsp['tag'] + ': skipped ' + str(dropped) + ' degenerate source triangle(s).')
            if unassigned:
                warnings.append('BSP ' + bsp['tag'] + ': ' + str(unassigned) + ' face(s) have no material in the original source file and were skipped.')
            for instance, matrix in zip(ass['instances'], matrices):
                for kind, key in built.get(instance['object'], {}).items():
                    group = 'Special surfaces' if kind == 'special' else ('BSP instances' if instance['name'].startswith('%') else 'Structure')
                    placements.append(dict(name=name + ' / ' + instance['name'], mesh=key, group=group, source_tag=bsp['tag'],
                                           kind='special' if kind == 'special' else 'scenario_bsp', export='none' if kind == 'special' else 'static',
                                           matrix=matrix, bsp=bsp['tag']))
                    counts[group] = counts.get(group, 0) + 1
                    bsp_ok = bsp_ok or kind == 'geometry'
        decoded += bool(bsp_ok)

    # ---- Objects: render-model sources, chosen per variant.
    objects = data.get('objects', {})
    parsed = {}

    def object_mesh(key, variant):
        info = objects.get(key) or {}
        render = info.get('render_model', '')
        if not render:
            return None, None, 'has no render model'
        wanted, variant_name = _variant_selection(info, variant)
        if key not in parsed:
            parsed[key] = []
            try:
                sources = _sources(info, folder)
            except RuntimeError as error:
                warnings.append(render + ': ' + str(error))
                sources = []
            for path, text in sources:
                if not path.lower().endswith('.jms'):
                    continue
                try:
                    parsed[key].append((path, sf.parse_jms(text, leaf(path), Path(path.replace('\\', '/')).stem)))
                except sf.SourceError as error:
                    warnings.append(render + ': ' + str(error))
        if not parsed[key]:
            return None, None, 'no embedded render-model source'
        signature = json.dumps(sorted(wanted.items()))
        mesh_key = 'object_' + stable_id(key, signature)
        if mesh_key not in meshes:
            records, selection = [], []
            for path, jms in parsed[key]:
                ids = [materials.get(m['name'], info.get('shaders', []), (), render) for m in jms['materials']]
                triangles, report = sf.select_render_triangles(jms, wanted)
                unassigned = sf.unassigned_triangles(jms)
                if unassigned:
                    warnings.append(render + ': ' + str(unassigned) + ' face(s) in ' + leaf(path) + ' have no material in the source file and were skipped.')
                selection.extend(report)
                record, dropped = sf.mesh_record(jms['positions'], jms['normals'], jms['uvs'], triangles, ids)
                records.append(record)
            file = _write_mesh(folder, mesh_key + '.json', materials.metas(), records)
            if not file:
                return None, None, 'its source has no faces for the selected variant'
            meshes[mesh_key] = file
            pending[mesh_key] = selection
        return mesh_key, variant_name, None

    fallback = []
    for row in data.get('placements', []):
        check()
        category = row['category']
        if category not in EXPORT and category not in REFERENCE_ONLY:
            continue
        info = objects.get(row['object_tag']) or {}
        mesh_key, variant_name, problem = object_mesh(row['object_tag'], row.get('variant', ''))
        label = (row.get('name') or leaf(row['object_tag']).rsplit('.', 1)[0]) + ' #' + str(row['index'])
        matrix = sf.scaled(sf.euler_matrix(*row['rotation'], row['position'], row.get('scale') or 1.0), 100)
        entry = dict(name=label, group=category, source_tag=info.get('render_model', ''), object_tag=row['object_tag'],
                     model_tag=info.get('model', ''), collision_model=info.get('collision_model', ''),
                     variant=variant_name or '', kind='scenario_object', category=category,
                     export=EXPORT.get(category, 'none'), matrix=matrix)
        if mesh_key is None:
            if info.get('render_model') and problem == 'no embedded render-model source':
                entry['fallback_render'] = info['render_model']
                fallback.append(entry)
            else:
                warnings.append(category + ' ' + label + ' (' + row['object_tag'] + '): ' + problem + '.')
            continue
        entry['mesh'] = mesh_key
        entry['selection'] = pending.get(mesh_key, [])
        placements.append(entry)
        counts[category] = counts.get(category, 0) + 1

    for key in data.get('skies', []):
        check()
        mesh_key, _, problem = object_mesh(key, '')
        info = objects.get(key) or {}
        if mesh_key is None:
            if info.get('render_model') and problem == 'no embedded render-model source':
                fallback.append(dict(name=leaf(key).rsplit('.', 1)[0], group='Skies', source_tag=info['render_model'], object_tag=key,
                                     model_tag=info.get('model', ''), kind='sky', export='none', matrix=sf.identity(),
                                     fallback_render=info['render_model']))
            else:
                warnings.append('Sky ' + key + ': ' + problem + '.')
            continue
        placements.append(dict(name=leaf(key).rsplit('.', 1)[0], mesh=mesh_key, group='Skies', source_tag=info.get('render_model', ''),
                               object_tag=key, model_tag=info.get('model', ''), kind='sky', export='none', matrix=sf.identity()))
        counts['Skies'] = counts.get('Skies', 0) + 1

    for name, owners in sorted(materials.unresolved.items()):
        warnings.append('Material "' + name + '" has no unique shader reference in ' + ', '.join(sorted(owners)) + '. Assign a Halo shader before preparing.')
    return dict(materials=materials, meshes=meshes, placements=placements, fallback=fallback,
                warnings=warnings, counts=counts, decoded=decoded)


def _apply_textures(config, folder, result, map_path, cancel, progress):
    """Fill preview textures from the installed map by exact shader tag path."""
    metas = result['materials'].metas()
    shaders = sorted({m['shader'] for m in metas if m['shader']}, key=str.casefold)
    if not shaders:
        return []
    if map_path is None:
        return ['No installed MCC map named after this scenario was found, so materials have no preview textures. Shader assignments are unaffected.']
    progress('Loading preview textures for ' + str(len(shaders)) + ' shaders from ' + map_path.name)
    jobs.helper('extractor', dict(operation='materials', game=config.get('game', 'halo3'), map=str(map_path), tags=shaders, output=str(folder)),
                Path(config['cache']) / 'jobs', cancel)
    found = read_json(folder / 'materials.json', {})
    textures = {k.lower(): v for k, v in found.get('materials', {}).items()}
    notes = list(found.get('warnings', []))
    missing = 0
    for meta in metas:
        source = textures.get(meta['shader'].lower()) if meta['shader'] else None
        if not source:
            missing += bool(meta['shader'])
            continue
        for key in ('textures', 'alpha', 'options', 'tints', 'source_game'):
            if key in source:
                meta[key] = source[key]
    if missing:
        notes.append(str(missing) + ' shader(s) were not found in ' + map_path.name + '; they have no preview texture.')
    # Rewrite mesh files so their material tables carry the textures.
    by_id = {m['id']: m for m in metas}
    for file in result['meshes'].values():
        path = folder / file
        if Path(file).is_absolute() or Path(file).parent != Path('.'):
            continue
        data = read_json(path)
        data['materials'] = [by_id[m['id']] for m in data['materials']]
        write_json(path, data)
    return notes


def _apply_fallback(config, folder, result, map_path, cancel, progress):
    rows = result['fallback']
    if not rows:
        return []
    if map_path is None:
        return [row['group'] + ' ' + row['name'] + ': its render model ' + row['fallback_render'] + ' has no embedded source and no MCC map was found for a fallback mesh.' for row in rows]
    notes = []
    done = {}
    game = config.get('game', 'halo3')
    for row in rows:
        render = row['fallback_render']
        if render not in done:
            progress('Loading mesh without embedded source from the map: ' + leaf(render))
            target = folder / 'fallback' / stable_id(render)
            try:
                # Compiled tag names are lowercase; the map lookup is exact.
                jobs.helper('extractor', dict(operation='extract', game=game, map=str(map_path), tag=render.lower(), section=-1, output=str(target)),
                            Path(config['cache']) / 'jobs', cancel)
                done[render] = 'fallback/' + target.name + '/preview.json' if (target / 'preview.json').is_file() else None
            except jobs.Cancelled:
                raise
            except Exception as error:
                notes.append(render + ': fallback mesh failed: ' + (str(error).splitlines() or [''])[0])
                done[render] = None
            if done[render] and game != 'reach':
                notes.append(render + ': no embedded source in its tag; used the map mesh with its default variant.')
        file = done[render]
        if not file:
            continue
        key = 'fallback_' + stable_id(render)
        result['meshes'][key] = file
        row = dict(row, mesh=key, selection=read_json(folder / file, {}).get('selection', []))
        result['placements'].append(row)
        result['counts'][row['group']] = result['counts'].get(row['group'], 0) + 1
    if game == 'reach' and any(done.values()):
        notes.append('Halo: Reach Editing Kit tags carry no source models, so ' + str(sum(1 for v in done.values() if v))
                     + ' object model(s) use the mesh from ' + map_path.name + ' with their default variant. Placements still come from the scenario.')
    return notes


def _has_source(bsp):
    return any(s['source_path'].lower().endswith('.ass') for s in bsp.get('sources', []))


def _apply_map_bsps(config, result, data, map_path, cancel, progress):
    """BSPs whose kit tag has no source files (all of Reach) use the map's geometry."""
    wanted = {b['tag'].lower(): b['tag'] for b in data.get('bsps', [])
              if b.get('tag') and not b.get('missing') and not _has_source(b)}
    if not wanted or map_path is None:
        return []
    progress('Loading BSP geometry from ' + map_path.name + ' (the Editing Kit has no source files for it)...')
    manifest = Path(jobs.extract_map_scene(dict(config, maps=str(map_path.parent)), map_path.name, cancel, progress))
    scene = read_json(manifest, {})
    used = set()
    for row in scene.get('placements', []):
        tag = row.get('source_tag', '')
        if row.get('group') not in ('Terrain', 'BSP instances') or tag.lower() not in wanted:
            continue
        key = 'mapbsp_' + stable_id(str(manifest), row['mesh'])
        result['meshes'][key] = str((manifest.parent / scene['meshes'][row['mesh']]).resolve())
        # Whole-map rows are row-vector matrices in world units; scenario rows are
        # column matrices with translations in working units.
        m = row['matrix']
        matrix = sf.scaled([[m[c][r] for c in range(4)] for r in range(4)], 100)
        group = 'Structure' if row['group'] == 'Terrain' else 'BSP instances'
        result['placements'].append(dict(name=leaf(tag) + ' / ' + row['name'].split(' / ', 1)[-1], mesh=key, group=group,
                                         source_tag=tag, kind='scenario_bsp', export='static', matrix=matrix, bsp=tag, from_map=True))
        result['counts'][group] = result['counts'].get(group, 0) + 1
        used.add(tag.lower())
    notes = []
    if scene.get('decoded_bsps') == scene.get('expected_bsps'):
        # Every BSP decoded; one with no rows simply has no visible geometry (Reach "hidden" BSPs).
        for tag in sorted(set(wanted) - used):
            notes.append('BSP ' + wanted[tag] + ': no visible geometry in ' + map_path.name + '.')
            used.add(tag)
    result['decoded'] += len(used)
    result['warnings'] = [w for w in result['warnings']
                          if not (w.startswith('BSP ') and 'no embedded source geometry' in w and w[4:].split(':')[0].lower() in used)]
    return notes + ['BSP ' + wanted[t] + ': geometry from ' + map_path.name + ' (its Editing Kit tag has no source files).'
                    for t in sorted(used) if not any(wanted[t] in n for n in notes)]


def _stamp(config, scenario, data, map_path):
    tags = {(scenario, '.scenario')}
    tags.update((b['tag'], '.scenario_structure_bsp') for b in data.get('bsps', []))
    tags.update((o['render_model'], '.render_model') for o in data.get('objects', {}).values() if o.get('render_model'))
    paths = [tag_file(config['kit'], t, e) for t, e in sorted(tags, key=lambda item: (item[0].casefold(), item[1]))]
    files = [fingerprint(p) for p in paths if p.is_file()]
    return dict(version=VERSION, kind=KIND, game=config.get('game', 'halo3'), scenario=scenario, tags=files,
                map=fingerprint(map_path) if map_path else None)


def extract(config, scenario, cancel=None, progress=None):
    """Read the scenario through the tag helper; return the scene manifest path."""
    progress = progress or (lambda message: None)
    scenario = safe_tag(scenario)
    kit = Path(config['kit'])
    tag = tag_file(kit, scenario, '.scenario')
    if not tag.is_file():
        raise RuntimeError('Scenario not found in the Editing Kit tags: ' + scenario + '.scenario. Extract the Editing Kit tag archives, or check the path.')
    map_path = texture_map(config, scenario)
    root = Path(config['cache']) / 'scenario_scenes' / stable_id(str(kit.resolve()).lower(), scenario.lower())
    for candidate in sorted(root.glob('scene_*'), reverse=True):
        stamp = read_json(candidate / 'stamp.json')
        manifest = candidate / 'scene.json'
        if stamp and manifest.is_file():
            data = read_json(candidate / 'tags.json', {})
            if _stamp(config, scenario, data, map_path) == stamp:
                return manifest
    folder = root / ('scene_' + str(time.time_ns()))
    folder.mkdir(parents=True)
    try:
        progress('Reading ' + leaf(scenario) + '.scenario and its tags...')
        try:
            jobs.helper('tags', dict(operation='scenario_scene', kit=str(kit), scenario=scenario, output=str(folder / 'tags.json')),
                        Path(config['cache']) / 'jobs', cancel)
        except Exception as error:
            if 'Unknown operation' in str(error):
                raise RuntimeError('The installed tag helper is older than this add-on. Rebuild the helpers with source\\Build.ps1 (see CONTRIBUTING.md) or install a release ZIP that includes them.') from error
            details = str(error) + ' ' + ' '.join(str(i) for i in getattr(error, 'issues', []))
            if 'TagLoadException' in details and leaf(scenario).lower() + '.scenario could not be loaded' in details.lower():
                raise RuntimeError('The Editing Kit could not open ' + scenario + '.scenario. Its tags may be unfinished or damaged '
                                   'or saved by a different kit version. Try opening it in Sapien to check, or choose another scenario.') from error
            raise
        data = read_json(folder / 'tags.json')
        if not data or data.get('kind') != 'halo3_scenario_tags':
            raise RuntimeError('The tag helper did not describe the scenario.')
        result = build(config, scenario, data, folder, progress, cancel)
        notes = _apply_textures(config, folder, result, map_path, cancel, progress)
        notes += _apply_fallback(config, folder, result, map_path, cancel, progress)
        notes += _apply_map_bsps(config, result, data, map_path, cancel, progress)
        manifest = dict(version=VERSION, kind=KIND, game=config.get('game', 'halo3'), scenario=scenario, units='source', matrix_convention='column',
                        expected_bsps=len(data.get('bsps', [])), decoded_bsps=result['decoded'],
                        meshes=result['meshes'], placements=result['placements'], counts=result['counts'],
                        scenario_counts=data.get('counts', {}), texture_map=str(map_path) if map_path else '',
                        warnings=list(dict.fromkeys(result['warnings'] + notes)), limitations=LIMITATIONS)
        if not manifest['placements']:
            raise RuntimeError('Nothing could be imported from ' + scenario + '. ' + ' '.join(manifest['warnings'][:5]))
        for blob in folder.glob('*.zlib'):
            blob.unlink()
        write_json(folder / 'scene.json', manifest)
        write_json(folder / 'stamp.json', _stamp(config, scenario, data, map_path))
        return folder / 'scene.json'
    except BaseException:
        shutil.rmtree(folder, ignore_errors=True)
        raise


# ---------------------------------------------------------------- asset list

# Scenario placement groups that become browsable assets, and their asset kind.
INDEX_KINDS = {'Scenery': 'scenery', 'Crates': 'model', 'Machines': 'model', 'Controls': 'model',
               'Vehicles': 'model', 'Weapons': 'model', 'Equipment': 'model', 'BSP instances': 'instance'}
INDEX_STATUS = {
    'scenery': 'From the Editing Kit scenario. Unedited, it prepares as its original scenery tag.',
    'model': 'From the Editing Kit scenario. Exports as static geometry with generated collision.',
    'instance': 'BSP instanced geometry from the Editing Kit scenario. Exports as static geometry.',
}


def index_assets(manifest, config):
    """Catalogue rows for each distinct object, instanced mesh and shader in an imported scenario."""
    from .catalog import category
    manifest = Path(manifest)
    data = read_json(manifest)
    if not data or data.get('kind') != KIND:
        raise RuntimeError('Unsupported scenario scene manifest.')
    folder = manifest.parent
    scenario = data['scenario']
    game = data.get('game', config.get('game', 'halo3'))
    level = leaf(scenario)
    owner = (str(Path(config['kit']).resolve()).lower(), scenario.lower())
    rows, seen, shaders = [], set(), {}

    def mesh_file(key):
        return (folder / data['meshes'][key]).resolve()

    for row in data['placements']:
        kind = INDEX_KINDS.get(row['group'])
        key = row.get('mesh')
        if not kind or not key or key in seen:
            continue
        seen.add(key)
        if kind == 'instance':
            name = row['name'].split(' / ')[-1].lstrip('%?')
            tag = row.get('source_tag', '')
        else:
            name = leaf(row.get('object_tag', '')).rsplit('.', 1)[0]
            if row.get('variant'):
                name += ' (' + row['variant'] + ')'
            tag = row.get('object_tag', '')
        path = mesh_file(key)
        status = INDEX_STATUS[kind]
        if row.get('from_map') or row.get('fallback_render'):
            status = 'Mesh from the installed map (the Editing Kit tag has no source files). ' + status.split('. ', 1)[1]
        rows.append(dict(id=stable_id('scenario', *owner, key), name=name, tag=tag, kind=kind, section=-1,
                         scenery_tag=row['object_tag'].rsplit('.', 1)[0] if kind == 'scenery' else '',
                         level=level, category=category(name), game=game, source='scenario', scenario=scenario,
                         mesh=key, path=str(path), map='', status=status))
        try:
            for meta in read_json(path, {}).get('materials', []):
                if meta.get('shader') and not meta.get('special') and meta['shader'].lower() not in shaders:
                    shaders[meta['shader'].lower()] = (meta, path.parent)
        except (OSError, ValueError):
            pass
    for shader, (meta, directory) in sorted(shaders.items()):
        asset_id = stable_id('scenario', *owner, 'shader', shader)
        # One short folder for every shader keeps paths under Windows' 260-character limit;
        # texture paths become absolute because the textures stay beside their mesh.
        path = folder / 'shaders' / (asset_id[:16] + '.json')
        if not path.is_file():
            textures = [dict(t, path=str((directory / t['path']).resolve())) for t in meta.get('textures', [])]
            write_json(path, dict(version=1, materials=[dict(meta, id=0, textures=textures)], meshes=[]))
        rows.append(dict(id=asset_id, name=leaf(meta['shader']), tag=meta['shader'], kind='material', section=-1, scenery_tag='',
                         level=level, category='Materials', game=game, source='scenario', scenario=scenario, mesh='',
                         path=str(path), map='', status='Shader from the Editing Kit scenario, with preview textures from the installed map.'))
    return rows


def asset_path(asset, config, cancel=None):
    """The cached mesh or material file for a scenario asset, rebuilding the scene if it was cleared."""
    path = Path(asset.get('path', ''))
    if path.is_file():
        return path
    manifest = extract(dict(config, game=asset.get('game', config.get('game', 'halo3'))), asset['scenario'], cancel)
    match = next((row for row in index_assets(manifest, config) if row['id'] == asset['id']), None)
    if match is None:
        raise RuntimeError(asset['name'] + ' is no longer in ' + asset['scenario'] + '. Index the scenario again.')
    asset['path'] = match['path']
    return Path(match['path'])


# ---------------------------------------------------------------- Blender

def is_scenario_object(obj):
    return bool(obj.get('hb_scenario_manifest'))


def import_scene(context, manifest, progress=None):
    """Build the scene off-screen; publish the collection once every object exists."""
    import bpy
    from mathutils import Matrix
    from .blender_ops import mesh_from_preview, mesh_signature, new_id
    manifest = Path(manifest)
    data = read_json(manifest)
    if not data or data.get('kind') != KIND:
        raise RuntimeError('Unsupported scenario scene manifest.')
    progress = progress or (lambda message: None)
    folder = manifest.parent.resolve()
    # Borrowed map geometry lives in the shared map-scene cache next to scenario_scenes.
    map_scenes = (folder.parent.parent.parent / 'map_scenes').resolve()
    game = data.get('game', 'halo3')
    collection = bpy.data.collections.new('Level: ' + leaf(data['scenario']) + ' (Editing Kit scenario)')
    collection['hb_scenario_manifest'] = str(manifest)
    groups, objects, new_meshes, cache, signatures = {}, [], [], {}, {}
    try:
        rows = data['placements']
        for index, row in enumerate(rows):
            progress('Building ' + leaf(data['scenario']) + ' ' + str(index + 1) + '/' + str(len(rows)) + ': ' + row['group'])
            key = row['mesh']
            if key not in cache:
                path = (folder / data['meshes'][key]).resolve()
                if not (path.is_relative_to(folder) or path.is_relative_to(map_scenes)):
                    raise RuntimeError('Invalid scenario mesh path.')
                # Always build from the cached source data: a reused, edited mesh
                # must never be mistaken for the original object geometry.
                mesh = mesh_from_preview(path, 'scenario_v1_' + stable_id(str(manifest.resolve()), key))
                new_meshes.append(mesh)
                _apply_material_flags(mesh, path)
                cache[key] = mesh
                signatures[key] = mesh_signature(mesh)
            group = row['group']
            if group not in groups:
                child = bpy.data.collections.new(group)
                collection.children.link(child)
                groups[group] = child
            obj = bpy.data.objects.new(row['name'], cache[key])
            groups[group].objects.link(obj)
            objects.append(obj)
            # Meshes are in world units; objects carry HaloBridge's 100x working scale.
            obj.matrix_world = Matrix(row['matrix']) @ Matrix.Scale(100, 4)
            obj['hb_game'] = game
            obj['hb_working_units'] = 100
            obj['hb_scenario_manifest'] = str(manifest)
            obj['hb_scenario_index'] = index
            obj['hb_map_manifest'] = str(manifest)
            obj['hb_map_placement_index'] = index
            obj['hb_source_tag'] = row.get('source_tag', '')
            obj['hb_cache'] = str((folder / data['meshes'][key]).parent)
            exported = row.get('export') not in (None, 'none') or row['kind'] == 'sky'
            if exported:
                # Same inclusion rules as a whole-map import: exported unless removed.
                obj['hb_map_reference'] = True
            obj['hb_ignore'] = True
            if row['kind'] == 'scenario_bsp':
                obj['hb_kind'] = 'scenario_bsp'
            elif row['kind'] == 'scenario_object':
                obj['hb_kind'] = 'scenery' if row['export'] == 'scenery' else 'model'
                obj['hb_scenario_kind'] = row['category']
                obj['hb_scenario_object'] = row['object_tag']
                obj['hb_model_tag'] = row.get('model_tag', '')
                obj['hb_mesh_signature'] = signatures[key]
                obj['hb_model_selection'] = json.dumps(row.get('selection', []))
                tag = row['object_tag'].rsplit('.', 1)[0]
                if row['export'] == 'scenery':
                    obj['hb_scenery_tag'] = tag
                    obj['hb_id'] = new_id()
                elif row['export'] == 'vehicle':
                    obj['hb_vehicle_tag'] = tag
                    obj['hb_vehicle_render'] = row.get('source_tag', '')
                if row.get('variant'):
                    obj['hb_variant'] = row['variant']
            yield
        context.scene.collection.children.link(collection)
        context.scene['hb_working_units'] = 100
        context.scene.unit_settings.system = 'METRIC'
        context.scene.unit_settings.scale_length = .03048
        if 'Special surfaces' in groups:
            groups['Special surfaces'].hide_render = True
            for layer in _layer_collections(context.view_layer.layer_collection, groups['Special surfaces']):
                layer.hide_viewport = True
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces.active.shading.type = 'MATERIAL'
        # Whole levels at 100x working scale extend far past Blender's default view distance.
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D' and area.spaces.active.clip_end < 999_999:
                    area.spaces.active.clip_end = 999_999
                    area.spaces.active.clip_start = max(area.spaces.active.clip_start, 1.0)
    except BaseException:
        for obj in objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        for child in groups.values():
            bpy.data.collections.remove(child)
        bpy.data.collections.remove(collection)
        for mesh in new_meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        raise


def _layer_collections(layer, target):
    if layer.collection == target:
        yield layer
    for child in layer.children:
        yield from _layer_collections(child, target)


def _apply_material_flags(mesh, path):
    """Carry source material flags (collision only, two sided, ...) to Blender materials."""
    directory = Path(path).parent
    metas = {'hb_' + stable_id(m.get('shader'), str(directory), m['id']): m
             for m in read_json(path, {}).get('materials', [])}
    for material in mesh.materials:
        if material is None or material.get('hb_ass_flags') is not None:
            continue
        meta = metas.get(material.get('hb_material_key', ''))
        if meta is None:
            continue
        material['hb_ass_flags'] = json.dumps(meta.get('flags', []))
        if meta.get('source_name'):
            material['hb_source_material'] = meta['source_name']
        flags = getattr(material, 'ass_jms', None)
        if flags is not None:
            flags.is_bm = True
            for name in meta.get('flags', []):
                if hasattr(flags, name):
                    setattr(flags, name, True)


def material_flags(material):
    try:
        return set(json.loads(material.get('hb_ass_flags') or '[]'))
    except (TypeError, ValueError):
        return set()


def report(data):
    lines = ['Editing Kit scenario: ' + data['scenario'], '',
             'Terrain BSPs with source geometry: ' + str(data['decoded_bsps']) + '/' + str(data['expected_bsps'])]
    lines += [k + ': ' + str(v) for k, v in sorted(data.get('counts', {}).items())]
    skipped = {k: v for k, v in data.get('scenario_counts', {}).items() if k in REFERENCE_ONLY}
    if data.get('texture_map'):
        lines.append('Preview textures: ' + Path(data['texture_map']).name + ' (looked up by shader tag path)')
    lines += ['', 'Import scope:'] + data.get('limitations', [])
    if data.get('warnings'):
        lines += ['', 'Missing or approximated elements:'] + data['warnings']
    if skipped:
        lines += ['', 'Scenario totals (reference only): ' + ', '.join(k + ' ' + str(v) for k, v in skipped.items())]
    return '\n'.join(lines)
