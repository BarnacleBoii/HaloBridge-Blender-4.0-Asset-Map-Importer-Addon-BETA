"""Complete, structured validation failures shared by scene and worker code."""
class ValidationError(RuntimeError):
    def __init__(self, issues, stage='Scene validation'):
        self.issues = list(dict.fromkeys(str(item) for item in issues if str(item).strip()))
        self.stage = stage
        super().__init__(stage + ': ' + str(len(self.issues)) + ' issue(s) found.\n' +
                         '\n'.join(f'{i}. {item}' for i, item in enumerate(self.issues, 1)))


def compiler_errors(text):
    """Retain every distinct error, even when progress output follows it."""
    markers = ('-ERROR-', '-FATAL-', 'LIGHTMAPPER FAILED', 'structure import pipeline failed')
    return list(dict.fromkeys(line.strip() for line in text.splitlines()
                             if any(marker in line for marker in markers)))

def geometry_warnings(text,names):
    import re
    result=[]
    for line in text.replace('\r','\n').splitlines():
        if 'WARNING' not in line or not any(marker in line.lower() for marker in ('overlapping surfaces','duplicate triangle','degenerate','open edge')):continue
        start=line.find('WARNING');line=line[start:].strip()
        line=re.sub(r'\(poop (hb_\d+)(?:\.\d+)?\)',lambda m:'(object '+names.get(m[1],m[1])+')',line)
        if line not in result:result.append(line)
    return result
