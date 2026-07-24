# Phase 01 — Teleport nhanh đến toạ độ chỉ định

## Overview
- **Ưu tiên:** P1 | **Độ khó:** Thấp | **Thời lượng:** ~1 ngày
- Cho phép dịch chuyển tức thì: (a) tới địa điểm đặt sẵn, (b) tới toạ độ `map,x,y` tự nhập, (c) từ panel đẩy 1 người chơi tới toạ độ. Đồng thời là "cửa vào" cho map ẩn (phase 08).

## Key insights
- `NewWorld(mapid, x, y)` — x,y = pixel/32 (`gmscript.lua:311,408`); `GetWorldPos()` trả `w,x,y` dùng lại được ngay (`gmscript.lua:444-447`).
- `SubWorldID2Idx(id) < 0` = map chưa load → phải check trước khi NewWorld, tránh crash/kẹt nhân vật.
- `map_type.txt` cấm `TRANSFER` ở map chiến trường/lôi đài → script phải tự chặn teleport từ/đến các map nhóm cấm (engine chỉ chặn item, không chặn script).
- Mẫu NPC dialog: `add_dialognpc`/`AddNpc` + `SetNpcScript` (`global/nobitaxd/autoexec_nobitaxd.lua:8-18`); dialog nhiều tầng: `CreateTaskSay` + `AskClientForNumber` (wrapper `dailogsys/dailogsay.lua:63-100`).

## Architecture
```
vdk/teleport/
  main.lua        # include, spawn NPC "Thần Hành Thái Bảo" ở 7 thành (toạ độ cạnh Xa Phu)
  npc.lua         # dialog: [Địa điểm hot] [Thành thị] [Nhập toạ độ] [Vị trí đã lưu]
  data.lua        # đọc SET/global/vdk/teleport/locations.txt (TSV: nhóm, tên, mapid, x, y)
  guard.lua       # danh sách map cấm đi/đến (đồng bộ map_type.txt) + check SubWorldID2Idx
```
- `locations.txt` chỉnh qua panel (tab Danh sách dữ liệu — tái dùng `list_service` + TCVN3 codec).
- "Vị trí đã lưu": lệnh lưu vị trí hiện tại (`GetWorldPos()` → ghi TaskString/id task trống hoặc file per-player), tối đa ~5 slot.
- Panel → game: endpoint mới ghi 1 file lệnh `SET/global/vdk/teleport/queue.txt` (`player_name\tmapid\tx\ty`); timer Lua 3s đọc queue, `SearchPlayer(name)` → `CallPlayerFunction(pIdx, NewWorld, ...)` → xoá dòng. (Không cần restart khi teleport từ panel.)

## Related files
- Tạo: 4 file `vdk/teleport/*` (VM), `SET/global/vdk/teleport/locations.txt`.
- Sửa: `vdk/main.lua` (+1 include), `backend/` panel (endpoint + catalog nhãn), `static/app.js` (nút teleport trong tab mới).

## Implementation steps
1. Dựng `data.lua` + `locations.txt` với bộ địa điểm khởi đầu: 7 thành, các bãi luyện công 9x, boss, Tống Kim báo danh 323-325.
2. `npc.lua`: menu 2 cấp (nhóm → địa điểm), mục "Nhập toạ độ" dùng `AskClientForNumber` 3 lần (map, x, y) có validate; thu phí tuỳ chọn (`Pay`).
3. `guard.lua`: chặn khi đang trong map nhóm SONGJIN/BAIRENLEITAI/FENGHUO... hoặc `GetFightState()==1` (chống lạm dụng thoát chiến đấu); đích không load → báo "Map chưa mở".
4. Spawn NPC ở 7 thành qua `main.lua` (mẫu autoexec_nobitaxd).
5. Queue teleport từ panel + timer đọc queue.
6. Test: teleport giữa các thành, vào map luyện công, nhập toạ độ sai/map chưa load, teleport khi đang PK.

## Todo
- [ ] locations.txt + data.lua
- [ ] npc.lua dialog + phí
- [ ] guard.lua chặn map cấm
- [ ] Spawn NPC 7 thành
- [ ] Queue teleport từ panel
- [ ] Nhãn catalog + UI panel
- [ ] Test 6 ca

## Success criteria
- Người chơi teleport được tới điểm đặt sẵn và toạ độ tự nhập; bị chặn đúng ở map cấm; panel teleport được người chơi online theo tên.

## Risks
- Teleport vào toạ độ không đi được (trong tường) → kẹt: cung cấp nút "Về thành" trong cùng NPC; validate x,y > 0.
- Lạm dụng trong PK/chiến trường → guard.lua + phí tiền.
