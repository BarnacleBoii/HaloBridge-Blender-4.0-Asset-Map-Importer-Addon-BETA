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
