"""Complete, structured validation failures shared by scene and worker code."""
import re

_instance_edge = re.compile(r'-ERROR- \(poop hb_\d+(?:\.\d+)?\) degenerate collision edge')

class ValidationError(RuntimeError):
    def __init__(self, issues, stage='Scene validation'):
        self.issues = list(dict.fromkeys(str(item) for item in issues if str(item).strip()))
        self.stage = stage
        super().__init__(stage + ': ' + str(len(self.issues)) + ' issue(s) found.\n' +
                         '\n'.join(f'{i}. {item}' for i, item in enumerate(self.issues, 1)))


def compiler_errors(text, completed_structure=None):
    """Retain every distinct error, even when progress output follows it."""
    markers = ('-ERROR-', '-FATAL-', 'LIGHTMAPPER FAILED', 'structure import pipeline failed')
    issues = list(dict.fromkeys(line.strip() for line in text.splitlines()
                                if any(marker in line for marker in markers)))
    if completed_structure and f"=== imported structure '{completed_structure}' in " in text:
        issues = [line for line in issues if not _instance_edge.fullmatch(line)]
    return issues

def geometry_warnings(text,names):
    result=[]
    for line in text.replace('\r','\n').splitlines():
        if _instance_edge.fullmatch(line.strip()):
            line=line.replace('-ERROR-', 'WARNING')+'; check collision on this object in Sapien'
        if 'WARNING' not in line or not any(marker in line.lower() for marker in ('overlapping surfaces','duplicate triangle','degenerate','open edge','collision edge too short')):continue
        start=line.find('WARNING');line=line[start:].strip()
        line=re.sub(r'\(poop (hb_\d+)(?:\.\d+)?\)',lambda m:'(object '+names.get(m[1],m[1])+')',line)
        if line not in result:result.append(line)
    return result
