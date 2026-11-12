"""Read the ASS/JMS authoring sources that Editing Kit tags keep as import info.

Halo 3 Editing Kit BSP and render-model tags retain the source files Tool
compiled them from. Reading those sources gives the level's real instance
names, transforms and shader names instead of a reconstruction of compiled
.map data. This module has no Blender dependency so it can be tested anywhere.

Coordinates stay in source units: 1 world unit = 100 source units, which is
also HaloBridge's 100x Blender working scale.
"""
import math
import re

TOKEN = re.compile(r'"[^"]*"|[^\s"]+')
LOD_TOKEN = re.compile(r'l[1-6]', re.IGNORECASE)
SLOT_TOKEN = re.compile(r'\(\d+\)')
# Material symbols used by Halo source files (see the Tool documentation).
SYMBOLS = '%#!@*$^-&?<|>=+.'
# Trailing "key:value" material parameters (lightmap resolution, power, ...).
MATERIAL_PARAMETER = re.compile(r'\s+[A-Za-z]{1,3}:\S*\s*$')
BM_FLAG_NAMES = ('two_sided', 'transparent_1_sided', 'transparent_2_sided', 'render_only',
                 'collision_only', 'sphere_collision_only', 'fog_plane', 'ladder', 'breakable',
                 'ai_deafening', 'no_shadow', 'shadow_only', 'lightmap_only', 'precise',
                 'conveyor', 'portal_1_way', 'portal_door', 'portal_vis_blocker',
                 'ignored_by_lightmaps', 'blocks_sound', 'decal_offset', 'slip_surface')
# Single-character name symbols, mapped to the same flag names.
SYMBOL_FLAGS = {'%': 'two_sided', '#': 'transparent_1_sided', '!': 'render_only',
                '@': 'collision_only', '*': 'sphere_collision_only', '$': 'fog_plane',
                '^': 'ladder', '-': 'breakable', '&': 'ai_deafening', '?': 'no_shadow',
                '<': 'shadow_only', '|': 'lightmap_only', '>': 'precise'}


class SourceError(RuntimeError):
    pass


def _strip_comment(line):
    quoted = False
    for index, char in enumerate(line):
        if char == '"':
            quoted = not quoted
        elif char == ';' and not quoted:
            return line[:index]
    return line


class Reader:
    def __init__(self, text, label='source'):
        self.items, self.rows, self.lines = [], [], []
        for number, line in enumerate(text.splitlines()):
            content = _strip_comment(line)
            tokens = TOKEN.findall(content)
            if tokens:
                self.items.extend(tokens)
                self.rows.extend([len(self.lines)] * len(tokens))
                self.lines.append(content.strip())
        self.index = 0
        self.label = label

    def next(self):
        if self.index >= len(self.items):
            raise SourceError(self.label + ' ended early (truncated or unsupported file).')
        value = self.items[self.index]
        self.index += 1
        return value

    def line(self):
        """The rest of the current source line as one string.

        JMS names and material definitions are whole unquoted lines that may
        contain spaces ("frame box", "(1) base base"); ASS strings are quoted.
        """
        if self.index >= len(self.items):
            raise SourceError(self.label + ' ended early (truncated or unsupported file).')
        row = self.rows[self.index]
        if self.index > 0 and self.rows[self.index - 1] == row:
            # Mid-line: return the remaining tokens only.
            start = self.index
            while self.index < len(self.items) and self.rows[self.index] == row:
                self.index += 1
            value = ' '.join(self.items[start:self.index])
        else:
            while self.index < len(self.items) and self.rows[self.index] == row:
                self.index += 1
            value = self.lines[row]
        # A whole quoted line is one string, even with an embedded quote
        # (Outskirts: "%"-?bridge_cliffsupp05").
        return value[1:-1] if len(value) >= 2 and value[0] == value[-1] == '"' else value

    def string(self):
        value = self.next()
        return value[1:-1] if len(value) >= 2 and value[0] == value[-1] == '"' else value

    def integer(self):
        value = self.string()
        try:
            return int(value)
        except ValueError:
            try:
                return int(float(value))
            except ValueError:
                raise SourceError(self.label + ': expected a whole number, found ' + repr(value)) from None

    def number(self):
        value = self.string().replace(',', '.')
        try:
            result = float(value)
        except ValueError:
            # 3ds Max writes 1.#QNAN0 / -1.#IND00 / 1.#INF00 for invalid values.
            if '#' in value:
                return 0.0
            raise SourceError(self.label + ': expected a number, found ' + repr(value)) from None
        return result if math.isfinite(result) else 0.0

    def vector(self, size=3):
        return [self.number() for _ in range(size)]

    def count(self, limit=50_000_000):
        value = self.integer()
        if not 0 <= value <= limit:
            raise SourceError(self.label + ': invalid count ' + str(value))
        return value


# ---------------------------------------------------------------- matrices
# Column-vector 4x4 matrices stored as four rows, the same layout as
# mathutils.Matrix, so Blender can use them directly.

def identity():
    return [[1.0 if r == c else 0.0 for c in range(4)] for r in range(4)]


def multiply(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def compose(quaternion, translation, scale):
    """Translation @ Rotation @ Scale from a Halo (x, y, z, w) quaternion."""
    x, y, z, w = quaternion
    length = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / length, y / length, z / length, w / length
    if isinstance(scale, (int, float)):
        scale = (scale, scale, scale)
    sx, sy, sz = scale
    rotation = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [[rotation[r][0] * sx, rotation[r][1] * sy, rotation[r][2] * sz, translation[r]] for r in range(3)] + [[0.0, 0.0, 0.0, 1.0]]


def euler_matrix(yaw, pitch, roll, position, scale):
    """Scenario placement transform; angles in degrees, as ManagedBlam reports them.

    Matches Reclaimer's EulerAngles conversion (Rx(roll) Ry(-pitch) Rz(yaw)),
    which is Blender Euler((roll, -pitch, yaw), 'ZYX').
    """
    yaw, pitch, roll = (math.radians(v) for v in (yaw, pitch, roll))
    def rx(a):
        c, s = math.cos(a), math.sin(a)
        return [[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]]
    def ry(a):
        c, s = math.cos(a), math.sin(a)
        return [[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]
    def rz(a):
        c, s = math.cos(a), math.sin(a)
        return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    m = multiply(multiply(rx(roll), ry(-pitch)), rz(yaw))
    scale = scale or 1.0
    for r in range(3):
        for c in range(3):
            m[r][c] *= scale
        m[r][3] = float(position[r])
    return m


def scaled(matrix, factor):
    """Scale only the translation, e.g. world units to source units."""
    result = [row[:] for row in matrix]
    for r in range(3):
        result[r][3] *= factor
    return result


# ---------------------------------------------------------------- materials

def split_material_name(name):
    """Return (base name, flag symbols) for a source material name."""
    # Halo 3 names may end with lighting parameters such as "lm:5.0" or "lp:2";
    # they are not part of the shader name (Guardian: "guardian guardian_floor_a lm:5.0").
    name = name.strip()
    while True:
        trimmed = MATERIAL_PARAMETER.sub('', name)
        if trimmed == name:
            break
        name = trimmed
    # Some shipped names end in an unbalanced ")" before or after their symbols
    # ("display=?)", "blur)!="); render models reference the shader without it.
    symbols = ''
    while True:
        match = re.fullmatch(r'(.*?)([' + re.escape(SYMBOLS) + r']*)', name.strip())
        name, found = match.groups()
        symbols = found + symbols
        if name.endswith(')') and name.count(')') > name.count('('):
            name = name[:-1].rstrip()
            continue
        break
    # A stray leading apostrophe ("'water_030") is not part of the shader name.
    base = name.lstrip("'")
    # A leading symbol (for example %name) is also a flag.
    while base and base[0] in SYMBOLS and not base.startswith('+'):
        symbols += base[0]
        base = base[1:]
    return base.strip(), symbols


def material_flags(name, lighting=()):
    flags = {SYMBOL_FLAGS[s] for s in split_material_name(name)[1] if s in SYMBOL_FLAGS}
    for entry in lighting:
        parts = entry.split()
        if len(parts) >= 2 and parts[0] == 'BM_FLAGS':
            flags.update(n for n, bit in zip(BM_FLAG_NAMES, parts[1]) if bit == '1')
    return sorted(flags)


def is_special(name):
    """Engine surfaces such as +portal, +sky and +seamsealer, not shader materials."""
    return name.strip().startswith('+')


# ---------------------------------------------------------------- ASS

def parse_ass(text, label='ASS'):
    r = Reader(text, label)
    version = r.integer()
    if not 1 <= version <= 7:
        raise SourceError(label + ': ASS version ' + str(version) + ' is not supported.')
    for _ in range(4):
        r.line()  # tool name, tool version, user, machine
    materials = []
    for _ in range(r.count(65536)):
        name = r.line()
        variant = r.line()
        lighting = [r.line() for _ in range(r.count(4096))] if version >= 4 else []
        materials.append(dict(name=name, variant=variant, lighting=lighting))
    objects = []
    for _ in range(r.count(1_000_000)):
        kind = r.line()
        xref_path = r.line()
        xref_name = r.line()
        item = dict(kind=kind, xref_path=xref_path, xref_name=xref_name, positions=[], normals=[],
                    uvs=[], triangles=[], nodes=[])
        if kind == 'SPHERE':
            item['material'] = r.integer(); item['radius'] = r.number()
        elif kind == 'BOX':
            item['material'] = r.integer(); item['extents'] = r.vector()
        elif kind == 'PILL':
            item['material'] = r.integer(); item['height'] = r.number(); item['radius'] = r.number()
        elif kind == 'MESH':
            for _ in range(r.count()):
                item['positions'].append(r.vector())
                item['normals'].append(r.vector())
                if version >= 6:
                    r.vector()  # vertex color
                for _ in range(r.count(64)):
                    node = r.integer(); r.number()
                    if node not in item['nodes']:
                        item['nodes'].append(node)
                uv_sets = r.count(64)
                first = None
                for _ in range(uv_sets):
                    uv = r.vector(3 if version >= 5 else 2)
                    if first is None:
                        first = uv[:2]
                item['uvs'].append(first or [0.0, 0.0])
            for _ in range(r.count()):
                material, a, b, c = r.integer(), r.integer(), r.integer(), r.integer()
                item['triangles'].append((material, a, b, c))
        elif kind == 'GENERIC_LIGHT':
            r.line(); r.vector()
            for _ in range(3): r.number()
            r.integer(); r.number(); r.number()
            r.integer(); r.number(); r.number()
            r.integer(); r.number()
        else:
            raise SourceError(label + ': unknown ASS object class ' + repr(kind) + '.')
        objects.append(item)
    instances = []
    for _ in range(r.count(1_000_000)):
        index = r.integer()
        if index < -1 or index >= len(objects):
            raise SourceError(label + ': instance refers to a missing object.')
        name = r.line()
        unique_id = r.integer()
        parent = r.integer()
        inheritance = r.integer()
        transforms = []
        for _ in range(2):
            rotation = r.vector(4)
            translation = r.vector()
            scale = r.vector() if version == 1 else r.number()
            transforms.append((rotation, translation, scale))
        # Weighted objects list one node instance per distinct influence.
        # Level geometry is rigid, so these bone groups are read and ignored.
        for _ in range(len(objects[index]['nodes']) if index >= 0 else 0):
            r.integer()
        instances.append(dict(object=index, name=name, unique_id=unique_id, parent=parent,
                              inheritance=inheritance, local=transforms[0], pivot=transforms[1]))
    return dict(version=version, materials=materials, objects=objects, instances=instances)


def ass_world_matrices(ass):
    """Object-to-scene matrix of each instance: parents' local transforms @ local @ pivot."""
    instances = ass['instances']
    chain = {}
    def parent_chain(index, depth=0):
        if index < 0:
            return identity()
        if index >= len(instances) or depth > len(instances):
            raise SourceError('ASS instance hierarchy is invalid or cyclic.')
        if index not in chain:
            item = instances[index]
            chain[index] = multiply(parent_chain(item['parent'], depth + 1), compose(*item['local']))
        return chain[index]
    result = []
    for item in instances:
        local = multiply(compose(*item['local']), compose(*item['pivot']))
        result.append(multiply(parent_chain(item['parent']), local))
    return result


# ---------------------------------------------------------------- JMS

def material_definition(text, default_permutation='default', default_region='default'):
    """(lod, permutation, region) from a Halo 2/3 JMS material definition string."""
    words = [w for w in text.split() if not SLOT_TOKEN.fullmatch(w)]
    lod = next((w.lower() for w in words if LOD_TOKEN.fullmatch(w)), '')
    words = [w for w in words if not LOD_TOKEN.fullmatch(w)]
    region = words.pop() if words else default_region
    permutation = words.pop() if words else default_permutation
    return lod, permutation, region


def parse_jms(text, label='JMS', default_permutation='default'):
    r = Reader(text, label)
    version = r.integer()
    if not 8205 <= version <= 8213:
        raise SourceError(label + ': JMS version ' + str(version) + ' is not supported (Halo 3 uses 8205-8213).')
    nodes = []
    for _ in range(r.count(1024)):
        name = r.line(); parent = r.integer()
        rotation = r.vector(4); translation = r.vector()
        nodes.append(dict(name=name, parent=parent, rotation=rotation, translation=translation))
    materials = []
    for _ in range(r.count(65536)):
        name = r.line()
        definition = r.line()
        lod, permutation, region = material_definition(definition, default_permutation)
        materials.append(dict(name=name, definition=definition, lod=lod, permutation=permutation, region=region))
    for _ in range(r.count(65536)):  # markers
        r.line(); r.integer(); r.vector(4); r.vector(); r.number()
    xrefs = [(r.line(), r.line() if version >= 8208 else '') for _ in range(r.count(65536))]
    for _ in range(r.count(65536)):  # xref markers
        r.line(); r.integer(); r.integer(); r.vector(4); r.vector()
    positions, normals, uvs = [], [], []
    for _ in range(r.count()):
        positions.append(r.vector()); normals.append(r.vector())
        for _ in range(r.count(64)):
            r.integer(); r.number()
        first = None
        for _ in range(r.count(64)):
            uv = r.vector(2)
            if first is None:
                first = uv
        uvs.append(first or [0.0, 0.0])
        if version >= 8211:
            r.vector()  # vertex color
    triangles = []
    for _ in range(r.count()):
        triangles.append((r.integer(), r.integer(), r.integer(), r.integer()))
    # Collision, physics and skylight sections follow; render import ignores them.
    return dict(version=version, nodes=nodes, materials=materials, xrefs=xrefs,
                positions=positions, normals=normals, uvs=uvs, triangles=triangles)


def select_render_triangles(jms, wanted):
    """Keep one LOD and the chosen permutation for each region.

    wanted maps region name -> permutation name. Regions that are absent use
    'default', then 'base', then their first permutation, like the map route.
    Returns (triangles, selection report).
    """
    by_region = {}
    for material in jms['materials']:
        by_region.setdefault(material['region'], [])
        if material['permutation'] not in by_region[material['region']]:
            by_region[material['region']].append(material['permutation'])
    # Untagged faces belong to every level of detail. Of the tagged ones keep
    # the highest in-game level (L5); L6 is cinematic-only, used when it is all there is.
    tagged = {}
    for m in jms['materials']:
        if m['lod']:
            tagged.setdefault((m['region'], m['permutation']), set()).add(int(m['lod'][1:]))
    best = {key: 'l' + str(max([v for v in levels if v <= 5] or levels)) for key, levels in tagged.items()}
    chosen = {}
    report = []
    wanted = {str(k).lower(): str(v).lower() for k, v in (wanted or {}).items()}
    for region, permutations in by_region.items():
        lowered = {p.lower(): p for p in permutations}
        pick = lowered.get(wanted.get(region.lower(), ''))
        pick = pick or lowered.get('default') or lowered.get('base') or permutations[0]
        chosen[region] = pick
        report.append(dict(region=region, selected=[pick], available=list(permutations)))
    keep = []
    for triangle in jms['triangles']:
        index = triangle[0]
        if not 0 <= index < len(jms['materials']):
            raise SourceError('JMS triangle uses a missing material.')
        material = jms['materials'][index]
        if material['lod'] and material['lod'] != best.get((material['region'], material['permutation'])):
            continue
        if chosen.get(material['region']) == material['permutation']:
            keep.append(triangle)
    return keep, report


# ---------------------------------------------------------------- mesh data

def mesh_record(positions, normals, uvs, triangles, material_ids, matrix=None, unit=100.0):
    """Build a HaloBridge preview mesh from triangle lists.

    material_ids maps a source material index to the manifest material id.
    Positions are divided by unit: source units become world units, matching
    meshes extracted from maps (objects then carry HaloBridge's 100x scale).
    Only referenced vertices are kept. Degenerate triangles are dropped.
    """
    remap = {}
    out_positions, out_normals, out_uvs = [], [], []
    segments = {}
    dropped = 0
    def vertex(index):
        if index not in remap:
            if not 0 <= index < len(positions):
                raise SourceError('Triangle refers to a missing vertex.')
            p = positions[index]; n = normals[index] if index < len(normals) else [0.0, 0.0, 1.0]
            if matrix is not None:
                p = [sum(matrix[r][c] * (p[c] if c < 3 else 1.0) for c in range(4)) for r in range(3)]
                n = [sum(matrix[r][c] * n[c] for c in range(3)) for r in range(3)]
                length = math.sqrt(sum(v * v for v in n)) or 1.0
                n = [v / length for v in n]
            remap[index] = len(out_positions)
            out_positions.append([v / unit for v in p]); out_normals.append(n)
            out_uvs.append(uvs[index] if index < len(uvs) else [0.0, 0.0])
        return remap[index]
    for material, a, b, c in triangles:
        if len({a, b, c}) < 3:
            dropped += 1
            continue
        segments.setdefault(material_ids[material], []).extend((vertex(a), vertex(b), vertex(c)))
    return dict(positions=out_positions, normals=out_normals, uv=out_uvs,
                segments=[dict(material=m, indices=i) for m, i in segments.items()]), dropped
