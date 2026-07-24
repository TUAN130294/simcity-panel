# Phase 06 — Vận tiêu & cướp tiêu

## Overview
- **Ưu tiên:** P1 (nền có sẵn ~80%) | **Độ khó:** Vừa | **Thời lượng:** ~2-3 ngày | **Phụ thuộc:** phase 00; phase 01 (NPC/lối vào) hỗ trợ
- Kích hoạt + nâng cấp hệ hộ tống xe có sẵn (activity 12) thành tính năng vận tiêu/cướp tiêu đầy đủ: nhiều tuyến, bot cũng đi tiêu, người chơi cướp của nhau và của bot.

## Key insights
- **Activity 12 đã là vận tiêu hoàn chỉnh** (`activitysys/config/12/`): nhận NV tại NPC → spawn xe NPC 1903 mang tên chủ → xe tự đi 17 waypoint (`carriage.lua:10-27`, NpcWalk mỗi 1s) → tới đích `TaskFinish` thưởng 40tr exp; **xe bị giết → `TaskFailed` + rơi "Hỗn Nguyên Linh Lộ" CHO KẺ GIẾT (`carriage.lua:94-120`) = cơ chế cướp tiêu có sẵn**; Giặc Cỏ 1607-1609 rải dọc đường; giới hạn 20 xe server, 3 lần/ngày.
- Entry duy nhất hiện tại: NPC lái đò Phượng Tường; chuỗi `registe.lua` không thấy include trong cây → **phải xác minh activity 12 có được G_ACTIVITY load không** (câu hỏi tồn đọng #3).
- Tuyến đường: 17 waypoint hard-code (toạ độ *32). Nguồn tuyến mới tốt nhất: đồ thị node simcity (`SET/global/vdk/simcity/maps/thanhthi/*_nodes.txt`, ~135 map) — nối preset path thành tuyến dài.
- Hộ vệ: bot follower `SimTheoSau` (pkeoxe) bám theo player — làm "tiêu sư" thuê được.
- Mẫu bổ sung: `battles/seizegrain` — vác hàng trên người (`ChangeOwnFeature`), đốt xe bằng item, broadcast toạ độ người vác toàn map (dùng cho "lộ hàng").

## Architecture
```
vdk/vantieu/
  main.lua      # include + spawn NPC "Tống Tiêu Đầu" tại 7 thành + timer
  config.lua    # tuyến (đọc routes.txt), giá vốn theo hạng tiêu, thưởng, giới hạn, giờ cao điểm
  routes.lua    # build tuyến từ node graph simcity hoặc waypoint tay (SET/.../vantieu/routes.txt
                #   TSV: tên tuyến, mapid, danh sách x_y, độ khó, thưởng)
  carriage.lua  # fork activity-12 carriage: spawn xe theo tuyến bất kỳ, tốc độ/HP xe theo hạng,
                #   OnDeath → rơi "tiêu ngân" cho kẻ cướp + báo toàn map, OnFinish → thưởng
  robber.lua    # cướp: (a) người cướp người: giết xe là xong (sẵn có); (b) BOT cướp: khi xe đi
                #   qua, toán bot phục kích (spawn SimCitizen camp địch, aggro xe + chủ xe)
  bottieu.lua   # bot cũng đi tiêu: định kỳ chọn bot + spawn xe cho bot, đoàn hộ tống 2-4 bot
                #   (SimTheoSau đổi parent = NPC xe), người chơi cướp được → drop thưởng
```
- Hạng tiêu (chọn khi nhận NV): vốn đặt cọc `Pay` tăng dần → thưởng tăng (mẫu kinh tế: cọc 5 vạn/hạng thấp... panel chỉnh).
- Thông báo: nhận tiêu hạng cao → `Msg2SubWorld` "X đang vận tiêu hạng Thiên tuyến Biện Kinh→Tương Dương" (mồi PvP, bật/tắt được).
- Giờ cao điểm: khung giờ thưởng x2 (timer + `GetLocalDate`).

## Related files
- Tạo: 6 file `vdk/vantieu/*`, `SET/global/vdk/vantieu/routes.txt`, `config.txt`.
- Sửa: `vdk/main.lua` (+1 include), `simcity_catalog.py` + UI panel.
- Tham khảo/không sửa: `activitysys/config/12/*` (giữ nguyên hệ cũ chạy song song hoặc tắt bằng cách không spawn NPC của nó).

## Implementation steps
1. **Xác minh activity 12 trên VM**: grep chuỗi include registe/config 12 trong bản script THẬT trên VM (bản chép có thể thiếu file); test in-game NPC lái đò. Quyết định: tái dùng trực tiếp pActivity 12 hay fork sạch sang `vdk/vantieu` (khuyến nghị fork — độc lập activity system, tránh vướng TaskManager cũ).
2. `routes.lua` + `routes.txt`: 3 tuyến khởi đầu (nội thành Biện Kinh, Biện Kinh→ngoại ô, tuyến dài liên map nếu xe qua map được — NPC không tự chuyển map: tuyến liên map = xe mới ở map kế khi chủ qua trap, giữ state trong bảng Lua).
3. `carriage.lua`: fork + tổng quát hoá (tuyến/HP/tốc độ tham số), OnDeath rơi "tiêu ngân" (item event/tiền `NpcDropMoney`) + `Msg2Map` báo cướp.
4. `robber.lua`: điểm phục kích ngẫu nhiên trên tuyến, spawn 3-5 bot camp địch aggro xe (`SetNpcFightTarget` vào xe) — người chơi phải bảo vệ; thuê tiêu sư bot (SimTheoSau) đánh hộ.
5. `bottieu.lua`: mỗi X phút chọn 1 bot "đi tiêu" (xe + đoàn hộ tống bot), người chơi giết xe nhận thưởng — chống farm: giới hạn lượt cướp/ngày/người (task-id đếm), thưởng theo đóng góp damage nếu được (`GetNpcLastAttacker` — chỉ biết người đánh cuối, chấp nhận).
6. NPC Tống Tiêu Đầu 7 thành: menu nhận tiêu (chọn hạng/tuyến), xem trạng thái xe, huỷ (mất cọc).
7. Panel: bảng tuyến/hạng/thưởng/giới hạn + bật tắt bot cướp, bot đi tiêu.
8. Test: đi trọn tuyến nhận thưởng; bị người cướp (mất cọc, kẻ cướp có tiêu ngân); bị bot phục kích; cướp tiêu của bot; 20 xe đồng thời; logout giữa đường (xe phải bị dọn — timer orphan check).

## Todo
- [ ] Xác minh activity 12 load trên VM
- [ ] routes.txt 3 tuyến + routes.lua
- [ ] carriage.lua fork tổng quát
- [ ] robber.lua bot phục kích
- [ ] bottieu.lua bot đi tiêu + chống farm
- [ ] NPC 7 thành + menu
- [ ] Panel + test 6 ca

## Success criteria
- Nhận tiêu → xe đi theo tuyến → tới đích thưởng đúng hạng; giết xe người khác nhận tiêu ngân; bot phục kích hoạt động; cướp xe bot có giới hạn/ngày; không rò rỉ NPC xe (orphan) sau logout/reload.

## Risks
- NPC xe kẹt địa hình (NpcWalk không pathfind): tuyến phải bám node graph đã đi được của simcity; watchdog: xe không nhích >30s → dịch tới waypoint kế.
- Farm cướp xe bot: giới hạn lượt + thưởng vừa phải + hạng thấp cho bot.
- Fork trùng NPC id 1903 với activity 12 cũ: dùng id xe khác trong pool `SET/npcs.txt` nếu chạy song song.
