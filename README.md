# SimCity Control Panel — bảng điều khiển bot VLTK/JX1

Phần mềm chạy trên máy tính của bạn, giúp **chỉnh thông số bot SimCity và máy chủ game**
(VLTK/JX1 private server) bằng giao diện web tiếng Việt — **không cần biết code**.

Mọi thông số đều có nhãn tiếng Việt + giải thích. Sửa xong bấm Lưu là ghi thẳng vào máy chủ,
tự sao lưu bản cũ, khôi phục được bất cứ lúc nào.

---

## Cài đặt — chỉ 1 dòng lệnh

1. Bấm nút **Start** của Windows, gõ `powershell`, mở **Windows PowerShell**.
2. Dán dòng dưới đây vào rồi nhấn Enter:

```powershell
irm https://raw.githubusercontent.com/TUAN130294/simcity-panel/main/install.ps1 | iex
```

Vậy là xong. Máy sẽ tự:
- Cài Python nếu chưa có
- Tải panel về
- **Tạo shortcut "SimCity Panel" ngoài màn hình**
- Mở luôn trang điều khiển

Lần sau chỉ cần **bấm đúp shortcut ngoài Desktop**.

> **Cập nhật bản mới:** chạy lại đúng dòng lệnh trên. Cài đặt kết nối của bạn được giữ nguyên.

---

## Lần chạy đầu — kết nối tới máy chủ

App tự mở cửa sổ Cài đặt và **tự dò máy chủ game** giúp bạn:
- Tìm file `config.ini` của client VLTK (trong đó có sẵn IP + mật khẩu máy chủ), hoặc
- Quét mạng nội bộ tìm máy có thư mục game `/home/jxser`

Nếu dò không ra: nhập tay **VM Host** (IP máy ảo), **User** (`root`), **Password** rồi bấm
**Test** để kiểm tra, xong bấm **Lưu**.

---

## Các tab

| Tab | Dùng để làm gì |
|---|---|
| 🎛️ **Bot SimCity** | Số lượng bot, tốc độ chạy/đánh, máu, độ hung hăng, chat, tiền rơi... |
| ⚙️ **Máy Chủ** | Tỉ lệ Exp/tiền, tỉ lệ rơi đồ toàn server, Tống Kim, Phong Hỏa Liên Thành, bật/tắt tính năng |
| 🧩 **Nâng cao** | Thông số nằm ở các file khác |
| 📜 **Danh sách dữ liệu** | Câu chat của bot, tên bang hội, chức vụ — gõ tiếng Việt bình thường |
| 📝 **Sửa file thô** | Mở thẳng file `.lua` để sửa tay (có nút hiện tiếng Việt) |
| 🕐 **Backup** | Lịch sử sao lưu: sửa gì, lúc nào — bấm để khôi phục |
| ❓ **Hướng dẫn** | Cách sửa hành vi bot |

**Lưu ý quan trọng:** chỉnh xong phải bấm **Restart server** thì máy chủ mới áp dụng (mất 1–3 phút).

---

## Câu hỏi thường gặp

**Có an toàn không?** Panel chỉ chạy trên máy bạn (`127.0.0.1`), người ngoài không truy cập được.
Mỗi lần ghi đè file game đều tự chụp lại bản cũ — vào tab **Backup** khôi phục được.

**Chữ tiếng Việt trong game bị vỡ?** File game dùng bảng mã cũ TCVN3. Panel **tự chuyển đổi** —
bạn cứ gõ tiếng Việt Unicode bình thường (Unikey như thường ngày).

**Lỡ chỉnh hỏng game?** Vào tab **Backup**, tìm bản trước lúc chỉnh sai, bấm **Khôi phục**,
rồi **Restart server**.

**Bấm shortcut không lên gì?** Mở thư mục `%LOCALAPPDATA%\SimCityPanel`, xem file
`loi-khoi-dong.txt`. Hoặc chạy `start.bat` trong thư mục đó để thấy thông báo lỗi chi tiết.

---

## Dành cho người rành kỹ thuật

Chạy từ mã nguồn:

```bash
pip install -r requirements.txt
python app.py     # http://127.0.0.1:5666
```

- **Kết nối:** SSH/SFTP qua `paramiko`. Thông tin lưu ở `settings.json` (đã `.gitignore` —
  **không bao giờ** commit file này, nó chứa mật khẩu VM).
- **Sửa file:** đọc/ghi bằng `latin-1` (byte-faithful) để không vỡ chữ TCVN3/GBK. Chỉ ghi lại
  đúng dòng thay đổi, giữ nguyên comment và mọi byte khác.
- **Nhãn thông số:** `backend/simcity_catalog.py` (bot), `backend/server_config_catalog.py` (máy chủ).
- **Backup:** `backend/backup_service.py` — snapshot + manifest trên VM tại
  `/home/jxser/simcity-panel-backups/`.
- **Restart game:** `jx.sh reload` chạy nền (script này **không có** lệnh `restart`), panel poll
  `pgrep -x jx_linux_y` để biết khi nào game lên lại.

### Cấu trúc

```
simcity-panel/
  app.py                        # Flask + REST API
  launcher.pyw                  # bộ khởi động cho shortcut (chạy ẩn)
  install.ps1                   # bộ cài 1 lệnh
  backend/
    config_store.py             # settings.json + nhập từ client config.ini
    detect_service.py           # tự dò máy chủ (config.ini / quét LAN)
    ssh_service.py              # paramiko SSH/SFTP
    lua_config_parser.py        # parse & patch hằng số Lua theo dòng
    ini_config_parser.py        # parse & patch file .ini theo dòng
    simcity_catalog.py          # nhãn tiếng Việt cho thông số bot
    server_config_catalog.py    # nhãn tiếng Việt cho thông số máy chủ
    scan_service.py             # quét hằng global ở file khác
    list_service.py             # danh sách chuỗi (chat, tên bang)
    tcvn3_codec.py              # chuyển mã TCVN3 <-> Unicode
    droprate_service.py         # hệ số rơi đồ toàn server
    backup_service.py           # lịch sử backup + khôi phục
  templates/index.html
  static/app.js, style.css, favicon.ico
  settings.json                 # tự tạo, chứa mật khẩu VM — KHÔNG commit
```
