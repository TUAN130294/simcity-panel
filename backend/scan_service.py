"""Quét toàn bộ thư mục SimCity tìm hằng số global (UPPERCASE = number/string)
ở cột 0 (top-level) của mọi file .lua, trừ config.lua (đã có bảng riêng).

Trả về danh sách nhóm-theo-file, mỗi hằng kèm path + line (0-index) để sửa.
Gắn nhãn tiếng Việt nếu có trong catalog, còn lại hiện tên gốc + comment.
"""
import posixpath
from backend.lua_config_parser import _ASSIGN
from backend import simcity_catalog as catalog


def scan_globals(ssh, simcity_path):
    """ssh: SSHService. Trả về {ok, groups:[{file, path, fields:[...]}]}"""
    # grep hằng số global (cả UPPER & lower) gán SỐ/CHUỖI ở cột 0, trừ config.lua.
    # Chỉ khớp giá trị số/chuỗi trực tiếp -> bỏ qua "= floor(...)", "= (x or 0)+1"...
    cmd = (
        "grep -rnE '^[A-Za-z_][A-Za-z0-9_]*[ \\t]*=[ \\t]*(-?[0-9]|\")' "
        f"'{simcity_path}' --include='*.lua' | grep -v '/config.lua:'"
    )
    out, _err = ssh.run(cmd, timeout=40)

    by_file = {}
    for row in out.splitlines():
        # format: /path/file.lua:LINENO:content
        parts = row.split(":", 2)
        if len(parts) < 3:
            continue
        path, lineno_s, content = parts[0], parts[1], parts[2]
        try:
            lineno = int(lineno_s) - 1  # -> 0-index
        except ValueError:
            continue
        m = _ASSIGN.match(content.rstrip("\r\n"))
        if not m:
            continue
        raw = m.group("value")
        if raw[0] in "\"'":
            vtype, value = "string", raw[1:-1]
        elif "." in raw:
            vtype, value = "float", raw
        else:
            vtype, value = "int", raw
        name = m.group("name")
        rest = m.group("rest").strip()
        comment = rest[2:].strip() if rest.startswith("--") else ""

        meta = catalog.OTHER_FILE_LABELS.get(name, {})
        field = {
            "key": name,
            "name": name,
            "label": meta.get("label", name),
            "desc": meta.get("desc", comment or "Hằng số trong mã nguồn (chưa gắn nhãn)."),
            "widget": meta.get("widget", "text" if vtype == "string" else "number"),
            "unit": meta.get("unit", ""),
            "min": meta.get("min"), "max": meta.get("max"), "step": meta.get("step", 1),
            "value": value, "type": vtype, "line": lineno, "path": path,
            "comment": comment, "labelled": name in catalog.OTHER_FILE_LABELS,
        }
        by_file.setdefault(path, []).append(field)

    groups = []
    for path in sorted(by_file):
        # nhóm có nhãn lên trước
        fields = sorted(by_file[path], key=lambda f: (not f["labelled"], f["name"]))
        groups.append({"file": posixpath.basename(path), "path": path, "fields": fields})
    return {"ok": True, "groups": groups}
