"""Shared helpers for modules.tools.* tool wrappers."""


def render(result, desc=None, _indent=0):
    """Format a {'status': ..., **fields} result dict (values may themselves be
    dicts) as printable text, and derive an exit code from its status.
    `desc` (a one-line "what this tool is for" string) replaces the bare
    status word in the header line when given. Returns (text, exit_code)."""
    if isinstance(result, str):
        return result, 0
    pad = '    ' * (_indent + 1)
    lines = []
    if _indent == 0:
        status = result.get('status', 'info')
        header = desc or status
        lines.append('[error] %s' % header if status == 'error' else '[+] %s' % header)
    for key, value in result.items():
        if key == 'status':
            continue
        label = key.replace('_', ' ')
        if isinstance(value, dict):
            lines.append('%s%s:' % (pad, label))
            nested, _ = render(value, _indent=_indent + 1)
            lines.append(nested)
        else:
            lines.append('%s%s: %s' % (pad, label, value))
    exit_code = 1 if result.get('status') == 'error' else 0
    return '\n'.join(lines), exit_code
