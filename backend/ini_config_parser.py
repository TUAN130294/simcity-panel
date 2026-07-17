"""Parse & patch file INI của server (gamesetting.ini, taxrates.ini, servercfg.ini...)
theo SỐ DÒNG — cùng triết lý với lua_config_parser: chỉ thay đúng token giá trị
trên dòng cần sửa, mọi byte khác (comment tiếng Trung/TCVN3, tab...) giữ nguyên.

Định dạng nhận diện:
  [Section]        -> đổi section hiện tại
  Key=Value        -> entry (key ASCII; value tới trước comment ';')
  ; comment / -- comment / # comment -> bỏ qua
key trả về dạng "SECTION.Key" để không đụng key trùng tên giữa các section.
"""
import re

_SECTION = re.compile(r'^\s*\[(?P<name>[^\]\r\n]+)\]')
# Chấp nhận cả kiểu "Key = 10 ;" (auction.ini có dấu cách quanh dấu bằng)
_ENTRY = re.compile(
    r'^(?P<key>[A-Za-z_][A-Za-z0-9_]*)'
    r'[ \t]*=[ \t]*(?P<value>[^;\r\n]*?)'
    r'(?P<rest>[ \t]*(?:;.*)?)$'
)


def parse_all(text):
    """Trả về list {name, key, section, value, type, line, comment, parent}.

    line = chỉ số dòng 0-based (dùng làm handle sửa). parent = section
    (để tương thích shape với lua_config_parser).
    """
    out = []
    section = ""
    for i, line in enumerate(text.splitlines()):
        s = line.strip()
        if not s or s[0] in ";#" or s.startswith("--"):
            continue
        msec = _SECTION.match(line)
        if msec:
            section = msec.group("name").strip()
            continue
        m = _ENTRY.match(line.rstrip())
        if not m:
            continue
        value = m.group("value").strip()
        vtype = "int" if re.fullmatch(r"-?\d+", value) else (
            "float" if re.fullmatch(r"-?\d+\.\d+", value) else "string")
        name = m.group("key")
        out.append({
            "name": name,
            "key": f"{section}.{name}" if section else name,
            "section": section,
            "value": value,
            "type": vtype,
            "line": i,
            "comment": "",
            "parent": section or None,
        })
    return out


def apply_patch_by_line(text, changes):
    """changes: {line_index: new_value} -> (new_text, applied_lines).
    Giữ nguyên phần key=, comment ';' và ký tự xuống dòng gốc."""
    lines = text.splitlines(keepends=True)
    applied = []
    norm = {int(k): v for k, v in changes.items()}
    for i, line in enumerate(lines):
        if i not in norm:
            continue
        stripped = line.rstrip("\r\n")
        m = _ENTRY.match(stripped.rstrip())
        if not m:
            continue
        eol = line[len(stripped):]
        # phần đuôi sau value (tab/comment) nằm trong stripped sau match value
        prefix = m.group("key") + "="
        rest = m.group("rest")
        lines[i] = f"{prefix}{norm[i]}{rest}{eol}"
        applied.append(i)
    return "".join(lines), applied
