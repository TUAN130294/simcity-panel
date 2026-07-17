"""SimCity Control Panel — local web app.

Run:  python app.py   then open http://127.0.0.1:5666
Connects over SSH/SFTP to the game VM, browses and edits the SimCity Lua files,
backs up each file before overwriting, and (optionally) restarts the server.
"""
import os
import posixpath
import re
import webbrowser
from threading import Timer

from flask import Flask, request, jsonify, render_template

from backend import config_store as cfg
from backend.ssh_service import SSHService
from backend import lua_config_parser as luaparse
from backend import simcity_catalog as catalog
from backend import scan_service
from backend import list_service
from backend import tcvn3_codec
from backend import backup_service
from backend import ini_config_parser as iniparse
from backend import server_config_catalog as servercat
from backend import droprate_service
from backend import detect_service
from backend import power_service
from backend import tsv_service

app = Flask(__name__)
PORT = 5666


def _svc():
    s = cfg.load_settings()
    return SSHService(s["host"], s["port"], s["user"], s["password"]), s


def _guard_remote(path, root):
    """Only allow paths under the configured server_root (avoid stray edits)."""
    path = posixpath.normpath(path)
    if not path.startswith(root.rstrip("/")):
        raise ValueError(f"Path outside server root: {path}")
    return path


def _asset_version():
    """Dấu thời gian của css/js — gắn vào link để trình duyệt KHÔNG dùng bản cũ trong
    bộ nhớ đệm sau khi cập nhật (đổi file = đổi số = tải lại, khỏi cần Ctrl+F5)."""
    stamp = 0
    base = os.path.dirname(os.path.abspath(__file__))
    for rel in ("static/style.css", "static/app.js"):
        try:
            stamp = max(stamp, int(os.path.getmtime(os.path.join(base, rel))))
        except OSError:
            pass
    return stamp


@app.route("/")
def index():
    return render_template("index.html", v=_asset_version())


@app.route("/api/settings", methods=["GET"])
def get_settings():
    s = cfg.load_settings()
    safe = dict(s)
    safe["password"] = "********" if s.get("password") else ""
    return jsonify(safe)


@app.route("/api/settings", methods=["POST"])
def post_settings():
    patch = request.get_json(force=True) or {}
    if patch.get("password") == "********":
        patch.pop("password")  # unchanged -> keep existing
    return jsonify(cfg.save_settings(patch))


@app.route("/api/detect", methods=["POST"])
def detect_server():
    """Tự dò máy chủ game (đọc config.ini của client, hoặc quét mạng nội bộ).

    body: {user?, password?, port?} — trả thông tin tìm được, CHƯA lưu.
    Người dùng xem rồi bấm Lưu mới ghi vào settings.
    """
    body = request.get_json(force=True) or {}
    cur = cfg.load_settings()
    try:
        res = detect_service.autodetect(
            user=body.get("user") or cur.get("user") or "root",
            password=body.get("password") or "",
            port=int(body.get("port") or cur.get("port") or 22),
        )
        return jsonify({"ok": True, **res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/import-client-config", methods=["POST"])
def import_client_config():
    body = request.get_json(force=True) or {}
    try:
        saved = cfg.import_client_config(body.get("ini_path"))
        saved = dict(saved)
        saved["password"] = "********" if saved.get("password") else ""
        return jsonify({"ok": True, "settings": saved})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/test", methods=["POST"])
def test_conn():
    try:
        svc, _ = _svc()
        return jsonify({"ok": True, "info": svc.test()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/tree", methods=["GET"])
def tree():
    svc, s = _svc()
    path = request.args.get("path") or s["simcity_path"]
    try:
        return jsonify({"ok": True, "path": path, "entries": svc.list_dir(path)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/file", methods=["GET"])
def read_file():
    svc, s = _svc()
    path = request.args.get("path")
    enc = request.args.get("encoding") or s["encoding"]
    viet = request.args.get("viet") == "1"  # hiển thị chữ TCVN3 thành Unicode
    try:
        content = svc.read_file(path, enc)
        if viet:
            content = tcvn3_codec.tcvn3_to_unicode(content)
        return jsonify({"ok": True, "path": path, "content": content, "encoding": enc, "viet": viet})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/file", methods=["POST"])
def save_file():
    svc, s = _svc()
    body = request.get_json(force=True) or {}
    path = body.get("path")
    enc = body.get("encoding") or s["encoding"]
    try:
        content = body.get("content", "")
        if body.get("viet"):  # nội dung đang hiển thị Unicode -> chuyển về TCVN3 trước khi ghi
            content = tcvn3_codec.unicode_to_tcvn3(content)
        backup_service.snapshot(svc, path, "Sửa file thô: " + posixpath.basename(path))
        n = svc.write_file(path, content, enc, make_backup=True)
        return jsonify({"ok": True, "bytes": n, "backup": path + ".bak"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/catalog", methods=["GET"])
def get_catalog():
    """Nhãn tiếng Việt + nhóm (không cần VM). Dùng để vẽ giao diện trước."""
    return jsonify({"ok": True, "groups": catalog.GROUPS})


@app.route("/api/config", methods=["GET"])
def get_config():
    """config.lua đã gắn nhãn, chia nhóm. Mỗi field kèm path+line để sửa theo dòng.

    - groups: field trong catalog + value/line/found
    - extras: hằng số top-level trong config.lua chưa gán nhãn
    """
    svc, s = _svc()
    path = request.args.get("path") or posixpath.join(s["simcity_path"], "config.lua")
    enc = request.args.get("encoding") or s["encoding"]
    try:
        text = svc.read_file(path, enc)
        parsed = luaparse.parse_all(text)
        by_key = {c["key"]: c for c in parsed}

        groups = []
        for g in catalog.GROUPS:
            fields = []
            for f in g["fields"]:
                cur = by_key.get(f["key"])
                fields.append({**f, "path": path,
                               "value": cur["value"] if cur else None,
                               "line": cur["line"] if cur else None,
                               "type": cur["type"] if cur else "int",
                               "found": cur is not None})
            groups.append({"title": g["title"], "note": g.get("note", ""), "fields": fields})

        extras = [{"key": c["key"], "name": c["name"], "label": c["name"],
                   "desc": c["comment"] or "Chưa gắn nhãn.", "value": c["value"],
                   "type": c["type"], "line": c["line"], "path": path,
                   "widget": "text" if c["type"] == "string" else "number"}
                  for c in parsed if c["key"] not in catalog.LOOKUP and c["parent"] is None]

        return jsonify({"ok": True, "path": path, "groups": groups, "extras": extras})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/server-config", methods=["GET"])
def get_server_config():
    """Thông số MÁY CHỦ CHÍNH (cfg_server.lua, gamesetting.ini, taxrates.ini,
    servercfg.ini) — cùng cơ chế nhãn + sửa theo dòng như tab SimCity."""
    svc, s = _svc()
    enc = request.args.get("encoding") or s["encoding"]
    sources = []
    for src in servercat.SOURCES:
        item = {"id": src["id"], "title": src["title"], "path": src["path"], "groups": [], "extras": []}
        try:
            text = svc.read_file(src["path"], enc)
        except Exception as e:
            item["error"] = str(e)
            sources.append(item)
            continue
        parser = luaparse if src["type"] == "lua" else iniparse
        parsed = parser.parse_all(text)
        by_key = {c["key"]: c for c in parsed}
        for g in src["groups"]:
            fields = []
            for f in g["fields"]:
                cur = by_key.get(f["key"])
                fields.append({**f, "path": src["path"],
                               "value": cur["value"] if cur else None,
                               "line": cur["line"] if cur else None,
                               "found": cur is not None})
            item["groups"].append({"title": g["title"], "note": g.get("note", ""), "fields": fields})
        if src.get("show_extras"):
            item["extras_title"] = src.get("extras_title", "🗂️ Khác (chưa gắn nhãn)")
            item["extras"] = [
                {"key": c["key"], "name": c["name"], "label": c["name"],
                 # comment trong file là TCVN3 -> hiện tiếng Việt đọc được
                 "desc": tcvn3_codec.tcvn3_to_unicode(c["comment"]) or "Chưa gắn nhãn.",
                 "value": c["value"], "line": c["line"], "path": src["path"],
                 "widget": "text" if c["type"] == "string" else "number"}
                for c in parsed
                if c["key"] not in servercat.LOOKUP and c["parent"] is None]
        sources.append(item)
    return jsonify({"ok": True, "sources": sources})


@app.route("/api/droprate", methods=["GET"])
def get_droprate():
    """Hiện trạng hệ số rơi đồ từng nhóm (so với bản gốc)."""
    try:
        svc, _ = _svc()
        return jsonify({"ok": True, "scopes": droprate_service.status(svc)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/droprate", methods=["POST"])
def set_droprate():
    """Đặt hệ số rơi đồ: body {scope, mult}. mult=1 trả về nguyên bản."""
    body = request.get_json(force=True) or {}
    try:
        svc, _ = _svc()
        res = droprate_service.apply(svc, body.get("scope"), body.get("mult"))
        return jsonify({"ok": True, **res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/scan", methods=["GET"])
def scan_other_files():
    """Quét hằng số global ở các file SimCity khác (ngoài config.lua)."""
    svc, s = _svc()
    try:
        return jsonify(scan_service.scan_globals(svc, s["simcity_path"]))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/save", methods=["POST"])
def save_changes():
    """Lưu thay đổi đa-file theo dòng.
    body: {encoding?, changes: [{path, line, value}]}  -> gom theo path, backup, ghi.
    """
    svc, s = _svc()
    body = request.get_json(force=True) or {}
    enc = body.get("encoding") or s["encoding"]
    changes = body.get("changes") or []
    if not changes:
        return jsonify({"ok": False, "error": "Không có thay đổi"}), 400
    # gom theo path: {path: {line: value}} + gom nhãn để ghi lịch sử backup
    by_path = {}
    desc_by_path = {}
    for ch in changes:
        by_path.setdefault(ch["path"], {})[int(ch["line"])] = ch["value"]
        label = ch.get("label") or ("dòng " + str(ch.get("line")))
        desc_by_path.setdefault(ch["path"], []).append(f"{label} = {ch['value']}")
    try:
        results = []
        for path, line_map in by_path.items():
            text = svc.read_file(path, enc)
            # file .ini dùng parser INI, còn lại (lua) dùng parser Lua
            patcher = iniparse if path.lower().endswith(".ini") else luaparse
            new_text, applied = patcher.apply_patch_by_line(text, line_map)
            if applied:
                desc = "Chỉnh thông số: " + "; ".join(desc_by_path.get(path, []))[:400]
                backup_service.snapshot(svc, path, desc)
                svc.write_file(path, new_text, enc, make_backup=True)
            results.append({"path": path, "applied": len(applied)})
        total = sum(r["applied"] for r in results)
        return jsonify({"ok": True, "total": total, "results": results})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/lists", methods=["GET"])
def list_catalog():
    """Danh mục các danh sách dữ liệu sửa được (không cần VM).

    Gồm 2 loại: bảng trong file Lua (list_service) và file bảng TAB (tsv_service).
    Mục có 'cols' là bảng nhiều cột — giao diện vẽ theo cột.
    """
    lua_lists = [{"id": c["id"], "title": c["title"], "desc": c["desc"],
                  "rel": c.get("rel") or c.get("abs")}
                 for c in list_service.CATALOG]
    tsv_lists = [{"id": c["id"], "title": c["title"], "desc": c["desc"],
                  "rel": c["abs"],
                  "cols": [cl["label"] for cl in c["cols"]],
                  "types": [cl["type"] for cl in c["cols"]]}
                 for c in tsv_service.CATALOG]
    return jsonify({"ok": True, "lists": lua_lists + tsv_lists})


@app.route("/api/list", methods=["GET"])
def get_list():
    svc, s = _svc()
    lid = request.args.get("id")
    enc = request.args.get("encoding") or s["encoding"]
    tmeta = tsv_service.BY_ID.get(lid)
    if tmeta:
        try:
            text = svc.read_file(tmeta["abs"], enc)
            rows = tsv_service.extract(text, tmeta)
            types = [c["type"] for c in tmeta["cols"]]
            # cột chữ: TCVN3 -> Unicode để hiển thị; cột số giữ nguyên
            rows = [[tcvn3_codec.tcvn3_to_unicode(v) if types[j] == "text" else v
                     for j, v in enumerate(r)] for r in rows]
            items = rows if len(types) > 1 else [r[0] for r in rows]
            return jsonify({"ok": True, "id": lid, "title": tmeta["title"], "desc": tmeta["desc"],
                            "path": tmeta["abs"], "items": items,
                            "cols": [c["label"] for c in tmeta["cols"]], "types": types})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 400
    meta = list_service.BY_ID.get(lid)
    if not meta:
        return jsonify({"ok": False, "error": "Không rõ danh sách: " + str(lid)}), 400
    path = meta.get("abs") or posixpath.join(s["simcity_path"], meta["rel"])
    try:
        text = svc.read_file(path, enc)
        if meta.get("kind") == "number":
            res = list_service.extract_numbers(text, meta["marker"])
            items = res["items"] if res else None
        else:
            res = list_service.extract(text, meta["marker"])
            # Hiển thị tiếng Việt chuẩn trên web (file gốc lưu TCVN3)
            items = [tcvn3_codec.tcvn3_to_unicode(it) for it in res["items"]] if res else None
        if items is None:
            return jsonify({"ok": False, "error": "Không tìm thấy bảng trong file"}), 400
        return jsonify({"ok": True, "id": lid, "title": meta["title"], "desc": meta["desc"],
                        "path": path, "items": items})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/list", methods=["POST"])
def save_list():
    svc, s = _svc()
    body = request.get_json(force=True) or {}
    lid = body.get("id")
    enc = body.get("encoding") or s["encoding"]
    items = body.get("items")
    tmeta = tsv_service.BY_ID.get(lid)
    if tmeta:
        if not isinstance(items, list):
            return jsonify({"ok": False, "error": "Dữ liệu không hợp lệ"}), 400
        types = [c["type"] for c in tmeta["cols"]]
        rows, bad = [], []
        for it in items:
            row = [str(v) for v in it] if isinstance(it, list) else [str(it)]
            while len(row) < len(types):
                row.append("")
            row = row[:len(types)]
            if all(v.strip() == "" for v in row):
                continue                        # bỏ dòng trống
            for j, v in enumerate(row):
                v = v.replace("\t", " ").replace("\n", " ").strip()
                if types[j] == "number":
                    if not re.fullmatch(r"-?\d+", v):
                        bad.append(v or "(trống)")
                else:
                    v = tcvn3_codec.unicode_to_tcvn3(v)
                row[j] = v
            rows.append(row)
        if bad:
            return jsonify({"ok": False, "error": "Cột số chỉ được nhập SỐ. Sai: " + ", ".join(bad[:5])}), 400
        if not rows:
            return jsonify({"ok": False, "error": "Danh sách này không được để trống"}), 400
        try:
            text = svc.read_file(tmeta["abs"], enc)
            new_text = tsv_service.rebuild(text, tmeta, rows)
            backup_service.snapshot(svc, tmeta["abs"], f"Sửa danh sách: {tmeta['title']} ({len(rows)} dòng)")
            svc.write_file(tmeta["abs"], new_text, enc, make_backup=True)
            return jsonify({"ok": True, "count": len(rows), "backup": tmeta["abs"] + ".bak"})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 400
    meta = list_service.BY_ID.get(lid)
    if not meta or not isinstance(items, list):
        return jsonify({"ok": False, "error": "Dữ liệu không hợp lệ"}), 400
    path = meta.get("abs") or posixpath.join(s["simcity_path"], meta["rel"])
    if meta.get("kind") == "number":
        items = [str(it).strip() for it in items if str(it).strip()]
        bad = [it for it in items if not re.fullmatch(r"\d{1,6}", it)]
        if bad:
            return jsonify({"ok": False, "error": "Chỉ được nhập SỐ (vd 0100, 2300). Sai: " + ", ".join(bad[:5])}), 400
        if not items:
            return jsonify({"ok": False, "error": "Danh sách này không được để trống"}), 400
    else:
        # Người dùng gõ Unicode trên web -> chuyển về TCVN3 để game đọc đúng
        items = [tcvn3_codec.unicode_to_tcvn3(it) for it in items]
    try:
        text = svc.read_file(path, enc)
        if meta.get("kind") == "number":
            new_text = list_service.rebuild_numbers(text, meta["marker"], items)
        else:
            new_text = list_service.rebuild(text, meta["marker"], items)
        if new_text is None:
            return jsonify({"ok": False, "error": "Không tìm thấy bảng để ghi"}), 400
        backup_service.snapshot(svc, path, f"Sửa danh sách: {meta['title']} ({len(items)} dòng)")
        svc.write_file(path, new_text, enc, make_backup=True)
        return jsonify({"ok": True, "count": len(items), "backup": path + ".bak"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/reload", methods=["POST"])
def reload_server():
    """Gửi lệnh restart CHẠY NỀN trên VM rồi trả về ngay (không chờ server boot xong).

    jx.sh reload mất vài phút; nếu chờ đồng bộ sẽ timeout. Frontend sẽ tự
    poll /api/status để biết khi nào game lên lại.
    """
    svc, s = _svc()
    cmd = s.get("reload_cmd", "")
    if not cmd:
        return jsonify({"ok": False, "error": "Chưa cấu hình lệnh restart"}), 400
    wrapped = "nohup bash -c " + _shquote(cmd) + " >/tmp/simcity-panel-reload.log 2>&1 & echo STARTED"
    try:
        out, err = svc.run(wrapped, timeout=20)
        if "STARTED" not in out:
            return jsonify({"ok": False, "error": (err or out or "Không gửi được lệnh")}), 400
        return jsonify({"ok": True, "started": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


def _shquote(cmd):
    """Bọc lệnh trong nháy đơn an toàn cho bash -c."""
    return "'" + cmd.replace("'", "'\\''") + "'"


@app.route("/api/status", methods=["GET"])
def server_status():
    """Game server (jx_linux_y) đang chạy trên VM không? Dùng để poll sau restart."""
    try:
        svc, _ = _svc()
        # pgrep -x: khớp ĐÚNG tên process game (pgrep -f dính cả process vỏ terminal)
        out, _err = svc.run("pgrep -x jx_linux_y >/dev/null && echo UP || echo DOWN", timeout=15)
        return jsonify({"ok": True, "game": "UP" in out})
    except Exception as e:
        # SSH chưa vào được (VM đang bận/khởi động) -> coi như DOWN, không phải lỗi
        return jsonify({"ok": True, "game": False, "note": str(e)})


@app.route("/api/power", methods=["GET"])
def power_status():
    """Trạng thái 2 tầng: máy ảo VMware và game server bên trong."""
    s = cfg.load_settings()
    vmrun = power_service.find_vmrun()
    vmx = s.get("vmx_path") or ""
    if vmrun and not vmx:
        vmx = power_service.find_vmx() or ""      # dò giúp, chưa lưu
    res = {"ok": True, "vmrun": vmrun, "vmx": vmx, "vm": None, "game": None}
    if not vmrun:
        res["vm_note"] = "Không thấy VMware Workstation trên máy này — chỉ bật/tắt được game."
    elif not vmx:
        res["vm_note"] = "Chưa biết file .vmx của máy ảo. Mở ⚙ Cài đặt để chỉ đường."
    else:
        try:
            res["vm"] = power_service.vm_running(vmrun, vmx)
        except Exception as e:
            res["vm_note"] = str(e)
    if res["vm"] is not False:      # máy ảo đang bật (hoặc không rõ) thì mới hỏi game
        try:
            svc, _ = _svc()
            res["game"] = power_service.game_running(svc)
        except Exception:
            res["game"] = False     # SSH không vào được -> coi như game chưa chạy
    else:
        res["game"] = False
    return jsonify(res)


@app.route("/api/power/vm", methods=["POST"])
def power_vm():
    """body: {action: 'start'|'stop'} — bật/tắt MÁY ẢO."""
    body = request.get_json(force=True) or {}
    action = body.get("action")
    s = cfg.load_settings()
    vmrun = power_service.find_vmrun()
    vmx = s.get("vmx_path") or power_service.find_vmx() or ""
    if not vmrun:
        return jsonify({"ok": False, "error": "Không tìm thấy vmrun.exe (VMware Workstation)."}), 400
    if not vmx or not os.path.exists(vmx):
        return jsonify({"ok": False, "error": "Không tìm thấy file .vmx của máy ảo. "
                                              "Vào ⚙ Cài đặt điền đường dẫn."}), 400
    try:
        if action == "start":
            return jsonify(power_service.vm_start(vmrun, vmx))
        if action == "stop":
            return jsonify(power_service.vm_stop(lambda: _svc()[0], vmrun, vmx))
        return jsonify({"ok": False, "error": "Lệnh không hợp lệ"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/power/game", methods=["POST"])
def power_game():
    """body: {action: 'start'|'stop'|'reload'} — bật/tắt/khởi động lại GAME SERVER."""
    body = request.get_json(force=True) or {}
    action = body.get("action")
    try:
        svc, s = _svc()
        root = (s.get("reload_cmd") or "").split("cd ", 1)[-1].split(" &&", 1)[0].strip() \
               or "/root/quanlyserver/2.3.1"
        power_service.game_cmd(svc, action, root)
        return jsonify({"ok": True, "started": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/backups", methods=["GET"])
def get_backups():
    """Lịch sử backup: sửa gì, lúc nào — mới nhất trước."""
    try:
        svc, _ = _svc()
        return jsonify({"ok": True, "backups": backup_service.list_backups(svc)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/restore", methods=["POST"])
def restore_backup():
    """Khôi phục 1 file về bản backup đã chọn (tự chụp bản hiện tại trước)."""
    body = request.get_json(force=True) or {}
    fid = body.get("id")
    try:
        svc, _ = _svc()
        entry = backup_service.restore(svc, fid)
        return jsonify({"ok": True, "restored": entry})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/guide", methods=["GET"])
def get_guide():
    """Trả nội dung hướng dẫn sửa hành vi (markdown)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "huong-dan-sua-hanh-vi-bot.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return jsonify({"ok": True, "md": f.read()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


def _open_browser():
    webbrowser.open(f"http://127.0.0.1:{PORT}")


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        Timer(1.0, _open_browser).start()
    app.run(host="127.0.0.1", port=PORT, debug=False)
