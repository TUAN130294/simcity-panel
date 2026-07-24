# Phase 08 — Mở map ẩn + tạo map hoạt động tùy chỉnh

## Overview
- **Ưu tiên:** P2 | **Độ khó:** Vừa | **Thời lượng:** ~2-3 ngày | **Phụ thuộc:** phase 01 (teleport làm lối vào)
- Hai phần: (A) mở các map có trong dữ liệu nhưng server không load ("map ẩn"); (B) quy trình + công cụ panel biến 1 map thành "map hoạt động" (PK tự do, phó bản, event) và cho bot SimCity sinh sống ở map mới.

## Key insights
- `SET/maplist.ini` khai 992 map; **server chỉ load 139 map theo `maps/worldset.ini`** (`[World] Count=139, WorldNN=<id>`) → mở map ẩn = thêm `WorldNN` + tăng `Count` + restart. `SubWorldID2Idx(id)` = -1 là dấu hiệu map chưa load (test được ngay từ lab).
- Phân loại 992 map: 221 map tĩnh có `MapPos` (hiện trên bản đồ thế giới), 599 map NewWorld (`_NewWorldScript` — thường là chiến trường/phó bản/event), 264 map không có cả hai = quỹ map ẩn tự do. Quỹ map event script đã dùng quen: 851-862, 871-874, 892-896, 901, 906-916 (`global/forbidmap.lua`).
- Hành vi per-map cấu hình bằng cờ `_NewWorldParam` trong maplist.ini (`FIGHTSTATE_ON, PUNISH_OFF, PUNISH_PK10, HEART_OFF, STALL_OFF, CreateTeam_OFF, USETOWNP_OFF...`) — xử lý tại `maps/newworldscript_h.lua` (`aryFuncStore`); + `SET/forbitheart.txt` (ép chiến đấu) + `SET/map_type.txt` (cấm item theo nhóm).
- Phó bản/instance động: `PreApplyDungeonMap/ApplyDungeonMap/ReturnDungenonMap` (`missions/dungeon/dungeonmanager.lua:60-82`) — tạo bản copy map template theo nhu cầu.
- Bot sang map mới chỉ cần: cặp file `<mapid>_<ten>_nodes.txt` + `_preset.txt` + 1 dòng đăng ký `SET/global/vdk/simcity/maps/thanhthi.txt`.
- Lối vào map: NPC teleport (phase 01), trap file lua `main(sel)` → `NewWorld`, hoặc `maptraffic.ini` (chỉ là hiển thị client — không tự tạo lối đi server).

## Architecture
### (A) Mở map ẩn — quy trình chuẩn (làm tay lần đầu, sau đó panel tự động)
1. Chọn map từ maplist (panel hiển thị 992 map: id, tên TCVN3, MapType, đã load chưa).
2. Ghi `maps/worldset.ini` (+WorldNN, Count) — qua backup_service.
3. Thêm lối vào: điểm đến trong `locations.txt` của teleport (phase 01) — nhóm "Map khám phá".
4. Restart → verify `SubWorldID2Idx` >= 0 + teleport vào xem (một số map cổ có thể thiếu tài nguyên client → client crash: ghi chú map đó vào blacklist panel).

### (B) Map hoạt động tùy chỉnh
```
vdk/custommap/
  main.lua      # đọc SET/global/vdk/custommap/maps.txt (TSV: mapid, chế độ, tham số)
  modes.lua     # bộ chế độ đóng gói sẵn, áp lên map qua hook EnterMap/LeaveMap + trap:
                #   - "pk_tudo": SetFightState(1)+SetPunish(0) khi vào, khôi phục khi ra
                #   - "san_boss": spawn boss định giờ (AddNpc + DeathScript thưởng)
                #   - "botcity": gọi simcity spawn dân cư (cần nodes/preset — xem dưới)
                #   - "phoban": cấp instance ApplyDungeonMap cho tổ đội (thu phí vào)
  entry.lua     # đặt NPC/trap lối vào tại thành, thu phí/điều kiện cấp độ
```
- **Công cụ sinh node graph cho bot** (panel, Python): chưa có cách lấy dữ liệu địa hình map từ file server dễ dàng → phương án thực dụng: "ghi lộ trình" — admin chạy nhân vật trong map mới, script Lua ghi `GetWorldPos()` mỗi 2s vào file (lệnh bật/tắt qua NPC lab); panel convert log thành `<mapid>_<ten>_nodes.txt` (nối tuần tự + nối điểm gần nhau <16 ô, đúng format TSV `node linked is_exact type`) + preset. Đăng ký vào thanhthi.txt → bot sống ở map mới.

## Related files
- Sửa: `maps/worldset.ini`, `SET/maplist.ini` (chỉ khi cần thêm cờ NewWorldParam cho map custom), `SET/forbitheart.txt`, `SET/global/vdk/simcity/maps/thanhthi.txt`, `vdk/main.lua`.
- Tạo: `vdk/custommap/*` (3 file), `SET/global/vdk/custommap/maps.txt`, recorder trong `vdk/lab`, converter Python trong panel `backend/`.
- Panel: tab "Bản đồ" — bảng 992 map (parse maplist.ini + worldset.ini), nút mở/đóng map, gán chế độ, blacklist client-crash.

## Implementation steps
1. Panel parse maplist.ini + worldset.ini → bảng map (đọc qua SSH, TCVN3 decode tên).
2. Thử mở 2-3 map ẩn tiêu biểu (1 map Field 264-nhóm, 1 map trong quỹ 906-916) → xác minh quy trình + ghi nhận map crash client.
3. `modes.lua` chế độ `pk_tudo` + `san_boss` (dựa EventSys EnterMap như simcity đang dùng, `vdk/main.lua:20-24`).
4. Chế độ `phoban` bằng ApplyDungeonMap (thử với map template quỹ event; nếu API khó tính → lùi: dùng map thường + giới hạn 1 tổ đội/lượt qua mission var).
5. Recorder lộ trình + converter node graph + đăng ký thanhthi.txt → thả 50 bot vào 1 map mới làm mẫu.
6. Panel tab Bản đồ hoàn chỉnh (mở map, gán chế độ, đặt lối vào tự động qua locations.txt).
7. Test: mở/tắt map, PK tự do đúng phạm vi map, boss spawn đúng giờ, bot đi lại tự nhiên ở map mới, map blacklist không mở được từ panel.

## Todo
- [ ] Panel bảng 992 map + trạng thái load
- [ ] Mở thử 2-3 map ẩn + blacklist crash
- [ ] modes.lua pk_tudo + san_boss
- [ ] phoban qua ApplyDungeonMap
- [ ] Recorder + converter node graph
- [ ] Bot sống ở map mới (mẫu 1 map)
- [ ] Panel tab Bản đồ + test 5 ca

## Success criteria
- Từ panel: chọn map ẩn → mở → có lối vào teleport → vào chơi được; gán chế độ PK/boss/bot cho map bất kỳ; 1 map mới có bot sinh sống bằng node graph tự ghi.

## Risks
- Map thiếu tài nguyên phía client → crash client: mở từng map có kiểm chứng, duy trì blacklist; không mở hàng loạt.
- Tăng số map load tăng RAM/CPU server (`MaxSubWorldCount=1000` — trần xa, nhưng RAM VM hữu hạn): mở dần, theo dõi `free -m` sau restart.
- worldset.ini sai cú pháp = server không boot: backup + validate Count khớp số dòng trước khi ghi.
