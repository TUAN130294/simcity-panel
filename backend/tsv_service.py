"""Đọc/ghi file dữ liệu dạng bảng TAB của SimCity (names.txt, chat.txt, pets.txt).

Định dạng (đọc từ libs/data.lua + SimCityTableFromFile): các cột cách nhau bằng
TAB, dòng đầu là tiêu đề (game bỏ qua, đọc từ dòng 2). Chữ Việt lưu TCVN3 —
app.py lo phần chuyển mã, module này chỉ thao tác byte-faithful.

- names.txt : 1 cột (tên bot)             -> sửa cả file
- pets.txt  : 4 cột (id, nhóm, tên, giá)  -> sửa cả file
- chat.txt  : 2 cột (nhóm, câu nói)       -> sửa THEO NHÓM, giữ nguyên nhóm khác
  (chỉ đưa lên 7 nhóm rep_* code thật sự dùng; general/fighting là kho chết —
  bot lấy chat đi đường/đánh nhau từ pchat.lua, đã sửa được ở danh sách trên)
"""

DATA_DIR = "/home/jxser/server1/settings/global/vdk/simcity/"

_REP_GROUPS = [
    ("rep_chao", "🙋 Bot đáp khi được CHÀO", "Người chơi chào gần bot, bot đáp 1 câu ngẫu nhiên trong này."),
    ("rep_chung", "💬 Bot đáp chung chung", "Câu đáp khi không nhận ra người chơi đang nói gì."),
    ("rep_ok", "👍 Bot đáp ĐỒNG Ý", "Khi người chơi nói kiểu đồng ý/khen."),
    ("rep_no", "👎 Bot đáp TỪ CHỐI", "Khi người chơi nói kiểu phủ nhận/chê."),
    ("rep_giaodich", "🤝 Bot đáp về GIAO DỊCH", "Khi người chơi nhắc chuyện mua bán/giao dịch."),
    ("rep_boss", "👑 Bot đáp về BOSS", "Khi người chơi nhắc tới boss."),
    ("rep_chui", "😡 Bot đáp khi bị CHỬI", "Người chơi văng tục gần bot — bot đáp trả câu trong này."),
]

CATALOG = [
    {"id": "bot_names", "title": "👤 Tên bot", "abs": DATA_DIR + "names.txt",
     "ncols": 1, "edit_cols": [0],
     "cols": [{"label": "Tên bot", "type": "text"}],
     "desc": "Bot sinh ra bốc ngẫu nhiên 1 tên từ danh sách này. Gõ tiếng Việt bình thường, app tự chuyển mã."},
    {"id": "bot_pets", "title": "🐾 Thú cưng & giá bán", "abs": DATA_DIR + "pets.txt",
     "ncols": 4, "edit_cols": [0, 1, 2, 3],
     "cols": [{"label": "ID NPC", "type": "number"}, {"label": "Nhóm thú", "type": "text"},
              {"label": "Tên hiển thị", "type": "text"}, {"label": "Giá mua", "type": "number"}],
     "desc": "Thú cưng bán ở Lão Động Vật (Tây Độc Âu Dương Phong). Đổi giá thoải mái; ID NPC chỉ đổi khi biết chính xác id mới; đặt ID = 0 để tạm ẩn một con."},
] + [
    {"id": gid, "title": title, "abs": DATA_DIR + "chat.txt",
     "ncols": 2, "edit_cols": [1], "filter_col": 0, "filter_val": gid,
     "cols": [{"label": "Câu đáp", "type": "text"}],
     "desc": desc}
    for gid, title, desc in _REP_GROUPS
]
BY_ID = {c["id"]: c for c in CATALOG}


def _split_lines(text):
    eol = "\r\n" if "\r\n" in text else "\n"
    return text.split(eol), eol


def extract(text, meta):
    """Trả về list các dòng, mỗi dòng = list giá trị theo edit_cols."""
    lines, _ = _split_lines(text)
    fcol, fval = meta.get("filter_col"), meta.get("filter_val")
    rows = []
    for ln in lines[1:]:                      # dòng 0 là tiêu đề
        if ln.strip() == "":
            continue
        cells = ln.split("\t")
        while len(cells) < meta["ncols"]:
            cells.append("")
        if fval is not None and cells[fcol] != fval:
            continue
        rows.append([cells[c] for c in meta["edit_cols"]])
    return rows


def rebuild(text, meta, rows):
    """Ghi lại file. Không filter: thay toàn bộ phần dữ liệu (giữ tiêu đề).
    Có filter: chỉ thay các dòng thuộc nhóm đó, đúng vị trí cũ, nhóm khác giữ nguyên."""
    lines, eol = _split_lines(text)
    fcol, fval = meta.get("filter_col"), meta.get("filter_val")

    def make_line(row):
        cells = [""] * meta["ncols"]
        if fval is not None:
            cells[fcol] = fval
        for c, v in zip(meta["edit_cols"], row):
            cells[c] = v
        return "\t".join(cells)

    new_lines = [make_line(r) for r in rows]

    if fval is None:
        out = [lines[0] if lines else ""] + new_lines
        if len(lines) > 1 and lines[-1] == "":
            out.append("")                     # file gốc kết thúc bằng xuống dòng
        return eol.join(out)

    # Thay TỪNG DÒNG tại đúng vị trí cũ (nhóm có thể nằm rải nhiều cụm trong file):
    # dòng i của giao diện ghi đè lần xuất hiện thứ i; thừa thì chèn sau dòng cuối
    # của nhóm; thiếu thì các lần xuất hiện cuối bị xoá. Không đổi thì y nguyên byte.
    out, queue, last_at = [], list(new_lines), None
    for i, ln in enumerate(lines):
        if i == 0:
            out.append(ln)
            continue
        cells = ln.split("\t")
        matched = ln.strip() != "" and len(cells) > fcol and cells[fcol] == fval
        if matched:
            if queue:
                out.append(queue.pop(0))
                last_at = len(out) - 1
            continue                           # hết hàng mới -> dòng cũ này bị xoá
        out.append(ln)
    if queue:                                  # còn dòng mới thêm
        if last_at is not None:
            out[last_at + 1:last_at + 1] = queue
        elif out and out[-1] == "":            # nhóm chưa từng tồn tại -> thêm cuối
            out[-1:] = queue + [""]
        else:
            out.extend(queue)
    return eol.join(out)
