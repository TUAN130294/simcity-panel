"""Đọc/ghi các DANH SÁCH chuỗi trong file Lua (chat bot, tên bang...).

Tìm bảng theo 'marker' (vd 'SimCityChat.chatCollection'), lấy span từ '{' tới '}'
khớp (đếm độ sâu ngoặc), trích các chuỗi "..." (byte-faithful bằng latin-1).
Ghi lại: dựng lại phần giữa 2 ngoặc, giữ nguyên phần trước '{' và sau '}'.
"""
import re

_STR = re.compile(r'"((?:[^"\\]|\\.)*)"')

# Danh mục các danh sách dữ liệu cho phép sửa trên web.
CATALOG = [
    {"id": "chat_normal", "title": "💬 Câu chat thường của bot",
     "rel": "plugins/pchat.lua", "marker": "SimCityChat.chatCollection",
     "desc": "Các câu bot nói ngẫu nhiên khi đi lại."},
    {"id": "chat_fight", "title": "⚔️ Câu chat khi đánh nhau",
     "rel": "plugins/pchat.lua", "marker": "SimCityChat.chatCollectionFight",
     "desc": "Các câu bot nói khi đang chiến đấu."},
    {"id": "bang_names", "title": "🏳️ Tên bang hội của bot",
     "rel": "class/sim_citizen.lua", "marker": "g_TK_BangNames",
     "desc": "Pool tên bang gắn trước tên bot (nếu bật % tên bang)."},
    {"id": "bang_ranks", "title": "🎖️ Chức vụ trong bang",
     "rel": "class/sim_citizen.lua", "marker": "g_TK_BangRanks",
     "desc": "Bang Chủ / Trưởng lão / Đường Chủ / Đệ Tử..."},
]
BY_ID = {c["id"]: c for c in CATALOG}


def _span(text, marker):
    """Trả về (brace_open_index, brace_close_index) của bảng chứa marker."""
    idx = text.find(marker)
    if idx < 0:
        return None
    open_i = text.find("{", idx)
    if open_i < 0:
        return None
    depth = 0
    i = open_i
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return open_i, i
        i += 1
    return None


def extract(text, marker):
    sp = _span(text, marker)
    if not sp:
        return None
    open_i, close_i = sp
    inner = text[open_i + 1:close_i]
    raw_items = _STR.findall(inner)
    # unescape để hiển thị chuỗi thật (\" -> ", \\ -> \)
    items = [it.replace('\\"', '"').replace("\\\\", "\\") for it in raw_items]
    return {"items": items, "open": open_i, "close": close_i}


def rebuild(text, marker, items):
    sp = _span(text, marker)
    if not sp:
        return None
    open_i, close_i = sp
    # dò indent của dòng chứa '{' để căn ngoặc đóng
    line_start = text.rfind("\n", 0, open_i) + 1
    indent = ""
    for ch in text[line_start:open_i]:
        if ch in " \t":
            indent += ch
        else:
            indent = ""  # có chữ trước -> lấy indent đầu dòng
    lead = text[line_start:open_i]
    base_indent = lead[:len(lead) - len(lead.lstrip(" \t"))]
    body = "\n"
    for it in items:
        esc = it.replace("\\", "\\\\").replace('"', '\\"')
        body += f'{base_indent}\t"{esc}",\n'
    body += base_indent
    return text[:open_i + 1] + body + text[close_i:]
