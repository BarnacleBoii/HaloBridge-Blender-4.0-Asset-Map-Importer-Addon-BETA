"""Resolve recovered ASS material names through the BSP's actual shader references."""
import re
from .catalog import material_name


def resolve(text, kit, shaders):
    lines = text.splitlines(keepends=True)
    logical = [i for i, line in enumerate(lines) if line.strip() and not line.lstrip().startswith(';')]
    cursor = 0
    def take():
        nonlocal cursor
        if cursor >= len(logical):
            raise RuntimeError('Truncated ASS header or material table.')
        index = logical[cursor]; cursor += 1
        return index, lines[index].strip()
    def quoted(value):
        if len(value) < 2 or not value.startswith('"') or not value.endswith('"'):
            raise RuntimeError('Expected a quoted ASS material string.')
        return value[1:-1]
    if take()[1] != '7':
        raise RuntimeError('Source material recovery currently requires ASS version 7.')
    for _ in range(4): take()
    count = int(take()[1])
    if not 0 <= count <= 65536: raise RuntimeError('Invalid ASS material count.')
    by_name = {}
    for shader in shaders:
        name = shader.replace('/', '\\').rsplit('\\', 1)[-1].lower()
        by_name.setdefault(name, set()).add(shader)
    changes = []
    for _ in range(count):
        index, value = take(); name = quoted(value)
        quoted(take()[1])
        properties = int(take()[1])
        if not 0 <= properties <= 4096: raise RuntimeError('Invalid material property count.')
        for _ in range(properties): quoted(take()[1])
        # Existing collection names and special engine materials remain verbatim.
        if ' ' in name or name.startswith('+'): continue
        match = re.fullmatch(r'([A-Za-z0-9_]+)([^A-Za-z0-9_]*)', name)
        if not match: raise RuntimeError('Unsupported source material name: ' + name)
        base, flags = match.groups()
        candidates = by_name.get(base.lower(), set())
        if len(candidates) != 1:
            raise RuntimeError('Source material has no unique BSP shader reference: ' + name)
        replacement = material_name(kit, next(iter(candidates))) + flags
        ending = '\r\n' if lines[index].endswith('\r\n') else '\n'
        lines[index] = '"' + replacement + '"' + ending
        changes.append(dict(original=name, resolved=replacement))
    return ''.join(lines), changes
