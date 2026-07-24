# Plan: 8 tính năng nâng cấp bot SimCity & server VLTK/JX1

- **Ngày lập:** 2026-07-18 | **Trạng thái:** Draft — chưa thực thi
- **Phạm vi:** script Lua trên VM (`/home/jxser/server1/script`, `/home/jxser/server1/settings`, `/home/jxser/server1/maps`) + panel `simcity-panel/`
- **Nguồn nghiên cứu:** rà 6755 file script + 2160 file settings. Tóm tắt: `research-findings.md`. **Báo cáo đầy đủ (file:line + logic, agent code đọc thẳng, KHÔNG cần rà lại):** `research/01-kien-truc-bot-simcity.md`, `research/02-api-engine.md`, `research/03-van-tieu-activity-map-script.md`, `research/04-gia-lap-nguoi-choi-hoi-thoai.md`, `research/05-settings-map-pk.md`, `research/06-lien-dau-wlls.md` (đang bổ sung)

## Nguyên tắc chung (áp dụng mọi phase)

- Đọc/ghi file VM bằng `latin-1`; snapshot bằng `backend/backup_service.py` trước khi ghi đè.
- Code mới đặt tại `script/global/nobitaxd/vdk/<tên-tính-năng>/`, include từ `vdk/main.lua` (điểm boot: activity 801 → `vdk/main.lua` → `simcity/main.lua`).
- Sửa xong reload: `cd /root/quanlyserver/2.3.1 && DISPLAY=:0 XAUTHORITY=/root/.Xauthority ./jx.sh reload` (~3-4 phút), kiểm tra `pgrep -x jx_linux_y` + `gameserver.log`.
- Engine Lua 5.0: KHÔNG có `require`/socket; CÓ `io.open`, `os.execute`. Hàm C custom nằm trong `vdk.so` (48 export — danh sách trong research-findings.md); **source vdk.so chưa tìm thấy trên VM** → việc cần vá C mới đều đánh dấu [CẦN SOURCE VDK.SO].
- Mỗi thông số mới của tính năng đều thêm nhãn tiếng Việt vào catalog panel (`backend/simcity_catalog.py`).

## Các phase

| # | Phase | Ưu tiên | Độ khó | Phụ thuộc | Trạng thái |
|---|-------|---------|--------|-----------|------------|
| 00 | [Nền tảng: xác minh API vdk.so + khung module](phase-00-nen-tang-xac-minh-api.md) | P0 | Thấp | — | ⬜ |
| 01 | [Teleport nhanh đến toạ độ](phase-01-teleport-nhanh.md) | P1 | Thấp | 00 | ⬜ |
| 02 | [PK thành thị + solo với bot chỉ định](phase-02-pk-thanh-thi-solo-bot.md) | P1 | Vừa | 00 | ⬜ |
| 03 | [Liên đấu với bot — kích hoạt WLLS y game online](phase-03-lien-dau-voi-bot.md) | P2 | Cao | 00 | ⬜ |
| 04 | [Giao dịch thật với bot](phase-04-giao-dich-that-voi-bot.md) | P2 | Vừa→Cao | 00 | ⬜ |
| 05 | [Ngữ cảnh đối thoại người ↔ bot](phase-05-ngu-canh-doi-thoai.md) | P2 | Vừa (3 tầng) | 00 | ⬜ |
| 06 | [Vận tiêu & cướp tiêu](phase-06-van-tieu-cuop-tieu.md) | P1 | Vừa | 00, 01 | ⬜ |
| 07 | [Giả lập người chơi thật từ nhân vật đã tạo](phase-07-gia-lap-nguoi-choi-that.md) | P2 | Vừa | 00 | ⬜ |
| 08 | [Mở map ẩn + map hoạt động tùy chỉnh](phase-08-map-an-map-hoat-dong.md) | P2 | Vừa | 01 | ⬜ |

## Lộ trình đề xuất

1. **Đợt 1 (nhanh, ít rủi ro):** 00 → 01 (teleport) → 06 (vận tiêu — activity 12 có sẵn ~80%) → 02 (PK thành thị + solo bot — cơ chế duel có sẵn).
2. **Đợt 2:** 08 (map ẩn) → 03 (liên đấu: kích hoạt WLLS + relay giả lập local + bot lấp chỗ — đọc `research/06`) → 05 tầng 1 (đối thoại FSM Lua).
3. **Đợt 3:** 04 (giao dịch thật) → 07 (giả lập người chơi) → 05 tầng 2-3 (vá C / cầu LLM) [CẦN SOURCE VDK.SO].

## Phát hiện then chốt (chi phối thiết kế)

- Bot = NPC engine thật (`AddNpcEx`) + 48 hàm C vá trong `vdk.so`; ĐÃ có sẵn: duel với người (`PollDuel`+`BotDuelArm`), vào tổ đội (`PollParty`), giao dịch tặng đồ (`PollTradeStay`/`SendTradeItem`), trả lời chat theo keyword (`PollSayForBot` + `chat.txt` 21 category).
- Engine có sẵn: 1v1 (`battles/singlefight`), lôi đài map 960 Bách Nhân Lôi Đài (đủ toạ độ 5 đài), liên đấu WLLS, phó bản động (`ApplyDungeonMap`).
- Hộ tống xe = activity 12 (`activitysys/config/12/`): xe NPC 1903 đi 17 waypoint, giết xe → rơi thưởng cho kẻ cướp. Nền vận tiêu/cướp tiêu có sẵn.
- Map: `maplist.ini` 992 map, server chỉ load 139 (`maps/worldset.ini` = công tắc). PK per-map qua cờ `_NewWorldParam` + `forbitheart.txt`; không có switch PK toàn cục.
- Teleport: `NewWorld(mapid, x, y)` với x,y = pixel/32; `GetWorldPos()` trả sẵn bộ 3 dùng lại được.

## Quyết định từ user (2026-07-18)

- **Liên đấu:** làm **y như game online** (Võ Lâm Liên Đấu VNG: đăng ký → ghép trận theo lịch → đấu có giờ → điểm/hạng mùa giải) — phase 03 viết theo hướng này, khảo sát tái dùng `missions/leaguematch` (WLLS).
- **Giao dịch:** bot đã bày bán + tặng đồ khi người chơi xin (cửa sổ trade) — phase 04 chỉ làm phần thiếu: sạp mua được thật + giao dịch 2 chiều có giá.

## Câu hỏi chưa giải quyết (hỏi user trước khi vào Đợt 3)

1. **Source `vdk.so` ở đâu?** (file build 04/07/2026, 54KB — không có source trên VM). Cần cho: trade 2 chiều thật, chat nguyên văn, whisper.
2. `NpcChat` hiện lên bong bóng hay cả khung chat kênh gần? (`BotSayLocal` có trong vdk.so nhưng comment code nói cần fix client DLL — cần test in-game.)
3. (Phase 03) S3Relay có đang chạy trên VM không, và hàm `LG_*` khi thiếu relay trả 0 hay treo? — test lab trước khi sửa WLLS.
4. (Phase 03) Client SHXT còn render UI bảng thành tích liên đấu (task 1715-1732/2500/2501)? — nếu không, fallback NPC dialog.
