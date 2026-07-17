"""Parse & patch Lua config constants — by LINE NUMBER (robust to name collisions).

Handles:
  NAME = 123            (top-level scalar)
  NAME = "text"         (string)
  TABLE = {             (opens a table...)
      minTs = 6000      ( ...nested field, parent = TABLE )
  }
Editing is done by line index, so duplicate inner names (e.g. two `minTs`) never
clash. Only the value token on the target line is rewritten — indentation,
comments and every other byte are preserved.
"""
import re

# indent, name, value(number|"str"|'str'), trailing(comment)
_ASSIGN = re.compile(
    r'^(?P<indent>[ \t]*)(?P<name>[A-Za-z_][A-Za-z0-9_]*)'
    r'[ \t]*=[ \t]*(?P<value>-?\d+\.?\d*|"[^"\n]*"|\'[^\'\n]*\')'
    r'(?P<rest>[ \t]*,?[ \t]*(?:--.*)?)$'
)
_TABLE_OPEN = re.compile(r'^[ \t]*(?P<name>[A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*\{[ \t]*(?:--.*)?$')
_TABLE_CLOSE = re.compile(r'^[ \t]*\}[ \t]*,?[ \t]*(?:--.*)?$')


def parse_all(text):
    """Return list of {name, key, value, type, line, comment, parent}.

    key = name for top-level, or "PARENT.name" for a field inside a table.
    line = 0-indexed line number (stable handle for editing).
    """
    out = []
    parent = None
    for i, line in enumerate(text.splitlines()):
        topen = _TABLE_OPEN.match(line)
        if topen:
            parent = topen.group("name")
            continue
        if _TABLE_CLOSE.match(line):
            parent = None
            continue
        m = _ASSIGN.match(line)
        if not m:
            continue
        raw = m.group("value")
        if raw[0] in "\"'":
            vtype, value = "string", raw[1:-1]
        elif "." in raw:
            vtype, value = "float", raw
        else:
            vtype, value = "int", raw
        indented = m.group("indent") != ""
        this_parent = parent if indented else None
        name = m.group("name")
        comment = ""
        rest = m.group("rest").strip()
        if rest.startswith("--"):
            comment = rest[2:].strip()
        out.append({
            "name": name,
            "key": f"{this_parent}.{name}" if this_parent else name,
            "value": value,
            "type": vtype,
            "line": i,
            "comment": comment,
            "parent": this_parent,
        })
    return out


def apply_patch_by_line(text, changes):
    """changes: {line_index(int or str): new_value}. Rewrites the value token on
    each target line. Returns (new_text, applied_line_indexes)."""
    lines = text.splitlines(keepends=True)
    applied = []
    norm = {int(k): v for k, v in changes.items()}
    for i, line in enumerate(lines):
        if i not in norm:
            continue
        stripped = line.rstrip("\r\n")
        m = _ASSIGN.match(stripped)
        if not m:
            continue
        newval = str(norm[i])
        raw = m.group("value")
        if raw[0] in "\"'":
            q = raw[0]
            token = f"{q}{newval}{q}"
        else:
            token = newval
        eol = line[len(stripped):]
        lines[i] = f"{m.group('indent')}{m.group('name')} = {token}{m.group('rest')}{eol}"
        applied.append(i)
    return "".join(lines), applied
