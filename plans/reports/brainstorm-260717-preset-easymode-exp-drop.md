# Brainstorm: Tab Máy Chủ + hệ số rơi đồ — SimCity Panel

> **CẬP NHẬT 2026-07-17 (đã triển khai xong):** User đổi hướng — bỏ preset/easy-mode, giữ triết lý chỉnh TỪNG THAM SỐ, mở rộng phạm vi ra config máy chủ chính. Đã làm:
> - Tab "⚙️ Máy Chủ": cfg_server.lua (64 nhãn VN: tân thủ, Dã Tẩu, Tống Kim, PHLT, boss, xu, test, ~28 công tắc tính năng + extras comment tự chuyển TCVN3), gamesetting.ini (**ExpRate, MoneyRate**), taxrates.ini (thuế bày bán), servercfg.ini (MaxPlayer).
> - `backend/ini_config_parser.py`: parse/patch INI theo dòng, giữ nguyên byte khác (test round-trip OK).
> - Khảo sát droprate: cơ chế = `[Main] RandRange` (vòng xổ số) vs `RandRate` (lát trúng); NPC map file qua npcs.txt (365 con → item/npcdroprate.ini; boss/goldennpc riêng).
> - `backend/droprate_service.py` + UI: hệ số rơi đồ x0.1–x50 theo 2 nhóm (Quái thường 21 file / Boss & hoàng kim 73 file), baseline gốc lưu trên VM nên áp nhiều lần vẫn tính từ gốc, x1 = về nguyên bản (test byte-identical OK), mỗi file snapshot vào tab Backup.
> Nội dung dưới là bản brainstorm gốc trước khi đổi hướng (preset/easy-mode KHÔNG làm).

**Ngày:** 2026-07-17 · **Trạng thái:** Đã chốt với user · **User:** không biết code, cần UI tiếng Việt dễ hiểu

## Vấn đề
Panel đã phủ 100% thông số SimCity nhưng chỉnh vẫn theo từng ô lẻ. User muốn:
1. Bộ config đóng gói, áp nhanh.
2. Chỉnh thông số kiểu "mức độ" không cần hiểu từng con số.
3. Mở rộng sang config server chính (exp/drop rate).

## Các hướng đã cân nhắc
- Dashboard giám sát, xem log lỗi, restart theo lịch → user KHÔNG chọn (bỏ).
- Quản lý tài khoản game qua MSSQL → user không cần (bỏ hẳn).
- servercfg.ini: chỉ MaxPlayer đáng đưa lên web; IP/port KHÔNG đưa (nguy hiểm, vô ích với non-dev).

## Giải pháp chốt (3 phần)

### 1. Preset cấu hình 1-click
- Chụp toàn bộ giá trị các field có nhãn (config.lua + hằng file khác) → JSON `presets.json` trong thư mục panel.
- 3 preset mẫu đóng sẵn: "Đông vui nhộn nhịp" / "Vắng vẻ để test" / "Hiếu chiến PK loạn thành".
- Áp preset = build changes list → đi qua /api/save sẵn có (tự snapshot backup, hoàn tác được) → nhắc Restart.
- API: GET/POST/DELETE /api/presets, POST /api/presets/apply.

### 2. Chế độ chỉnh nhanh (Easy mode)
- 4 thanh kéo 4 nấc (Tắt/Ít/Vừa/Nhiều) đầu tab Bảng điều khiển:
  - Độ đông đúc → THANHTHI_SIZE, THON_SIZE, *_STALL_MIN/MAX
  - Độ hung hăng → CHANCE_AUTO_ATTACK, CHANCE_JOIN_FIGHT, CHANCE_ATTACK_PLAYER, SIMBOT_AGGRO_PLAYER_PCT, SIMBOT_ATTACK_PLAYER_CHANCE, BOT_VS_BOT
  - Độ trâu bò → SIMBOT_HP_MIN/MAX, SIMBOT_HEAL_AMOUNT, LIFE_RESTORE_PERCENT
  - Độ lắm mồm → CHANCE_CHAT
- Kéo thanh = tự điền các ô liên quan (đánh dấu changed như thường) — user vẫn xem/duyệt trước khi Lưu. Không thay thế chế độ chi tiết.
- Bảng giá trị từng nấc định nghĩa tĩnh trong catalog (dễ tinh chỉnh sau).

### 3. Khảo sát exp/drop server chính (sweep mới)
- Dò trong /home/jxser/server1/script + settings: các hằng/setting exp rate, drop rate, tiền rơi...
- Quy trình như sweep SimCity: tìm → xác minh cách dùng trong code → gắn nhãn VN → đưa vào tab riêng "⚙️ Server chính".
- CHỈ đưa lên web thông số đã hiểu rõ tác dụng; không chắc = không đưa (tránh nhãn sai gây hại).
- Thêm MaxPlayer (servercfg.ini, parser INI mới — file này KHÔNG phải Lua).

## Rủi ro
- Nấc giá trị Easy mode cần cân bằng thử nghiệm thực tế (CPU VM 4 core, 8GB RAM — "Nhiều" không được đặt quá cao).
- Exp/drop có thể nằm trong binary/DB chứ không phải script → khảo sát có thể ra kết quả ít hơn kỳ vọng; báo trung thực.
- INI write cần giữ nguyên comment/format (viết parser bảo toàn dòng như lua_config_parser).

## Tiêu chí xong
- Lưu/áp/xoá preset chạy được, áp xong các ô đổi đúng, có backup entry.
- 4 thanh kéo điền đúng bộ ô, lưu xuống server OK.
- Tab Server chính hiện ≥ MaxPlayer + các rate tìm được có nhãn VN, lưu + backup + restore OK.
- Người không biết code tự thao tác được toàn bộ qua web.

## Câu hỏi còn mở
- Giá trị cụ thể từng nấc Easy mode (sẽ đề xuất mặc định, user chỉnh sau khi chơi thử).
- Exp/drop thực sự nằm ở đâu — chờ kết quả khảo sát.
