# Phase 02 — Mở PK thành thị + yêu cầu solo với bot chỉ định

## Overview
- **Ưu tiên:** P1 | **Độ khó:** Vừa | **Thời lượng:** ~2 ngày
- Hai phần: (A) cho phép đánh nhau trong 7 map thành (kèm công tắc bật/tắt từ panel); (B) người chơi chọn đích danh 1 bot để solo, có luật đấu rõ ràng.

## Key insights
- KHÔNG có switch PK toàn cục; PK per-map qua cờ `_NewWorldParam` (chỉ map NewWorld) + `forbitheart.txt`. 7 map thành là map tĩnh `MapType=City` — không nhận cờ NewWorldParam. Chưa rõ engine có đọc `forbitheart.txt` cho map tĩnh không (câu hỏi tồn đọng — phải TEST).
- Phía bot: bot bất khả xâm phạm trong thành là do **script** (`SimCityIsPeaceZone`/`SimCityCanFight` `SIM/libs/common.lua:344-371`: `cityPeace=1` + bán kính 70 quanh attraction) — gỡ được thuần Lua.
- Phía người: đánh nhau cần cả 2 bên `SetFightState(1)`; phạt PK tắt bằng `SetPunish(0)` (mẫu `battles/guozhan/head.lua:388`); `SetPKFlag(1)` bật chế độ PK (mẫu `battles/guozhan/hometrap1.lua:22-23`).
- Duel bot đã có sẵn 2 đường: client mời (`PollDuel` `sim.core.lua:939`) và tự vệ (`selfDefDuel` `sim.core.lua:725`); toàn bộ máy trạng thái `SimDuelMove/SimDuelEnd/BotDuelArm` tái dùng nguyên vẹn. `SetNpcDuelAI` (chưa dùng) có thể liên quan — test ở phase 00.

## Architecture
### (A) PK thành thị
- Config mới trong `SIM/config.lua`: `SIMCITY_CITY_PK = 0|1` (+ per-map override trong `pworld` flags qua menu Triệu Mẫn "Cài đặt map").
- Khi bật: `SimCityIsPeaceZone` trả false cho map đó → bot đánh trả/tham chiến trong thành; giữ ngoại lệ bán kính nhỏ (r=20) quanh Đà Tẩu + NPC chức năng để không loạn khu bán hàng.
- Người-vs-người trong thành: thử 3 mức, dừng ở mức chạy được: (1) thêm 7 map id vào `forbitheart.txt` → test; (2) hook `EventSys EnterMap` gọi `SetFightState(1)` + `SetPunish(0)` cho người vào thành khi công tắc bật (dùng đúng EventSys mà simcity đã reg — `vdk/main.lua:20-24`); (3) nếu cần map NewWorld: bỏ qua, không clone thành (YAGNI).
- Giờ vàng PK (tuỳ chọn): timer check `GetLocalDate("%H%M")` bật/tắt tự động + `Msg2SubWorld` thông báo.

### (B) Solo với bot chỉ định
```
vdk/solobot/main.lua  # menu "Thách đấu bot" gắn thêm vào NPC Triệu Mẫn (controllers/thanhthi.lua)
```
- Menu liệt kê bot đang sống trên map hiện tại (duyệt `fighterList`, lọc theo `nMapIndex`, phân trang `__saypage` `lib/say.lua:34`), kèm ô nhập tên bot (`AskClientForString` + so khớp).
- Chọn bot → xác nhận luật (thời gian `duelTicks`, tiền cược `Pay/Earn` tuỳ chọn) → kích duel: set `tbNpc.duelPlayerId = playerIdx`, `tbNpc.duelTicks`, đổi camp đối địch, `SetNpcCombat`, để `SimDuelMove` chạy phần còn lại; người chơi được `SetFightState(1)` + `SetPunish(0)` trong trận.
- Kết thúc: thắng (bot chết → `OnDeath` cộng thưởng + `SimBotTaunt` đổi lời chúc mừng), thua (player chết → bot taunt), hết giờ (`SimDuelEnd`). Trả `SetPunish(1)`.

## Related files
- Sửa: `SIM/config.lua`, `SIM/libs/common.lua` (IsPeaceZone), `SIM/components/sim.core.lua` (nhánh khởi tạo duel chủ động), `SIM/controllers/thanhthi.lua` (menu), `SET/forbitheart.txt` (test), `vdk/main.lua`.
- Tạo: `vdk/solobot/main.lua`.
- Panel: nhãn `SIMCITY_CITY_PK` + các thông số luật solo vào `simcity_catalog.py`.

## Implementation steps
1. Test forbitheart với 1 map thành (37) — xác định mức (1) hay (2) ở phần A.
2. Gỡ peace-zone theo công tắc; giữ ngoại lệ khu chức năng; test bot đánh trong thành.
3. Hook EnterMap bật FightState/Punish khi công tắc bật; test người-vs-người + hồi chuông giờ vàng.
4. Xây menu thách đấu (danh sách bot + nhập tên); kích duel qua duelPlayerId; luật cược/thưởng.
5. Test: solo giữa thành, bot thắng/thua/hết giờ, 2 người cùng thách 1 bot (khoá bot đang duel), người chạy trốn sang map khác (SimDuelEnd).

## Todo
- [ ] Test forbitheart map tĩnh
- [ ] Công tắc SIMCITY_CITY_PK + gỡ peace-zone
- [ ] Hook EnterMap FightState/Punish + giờ vàng
- [ ] Menu thách đấu bot chỉ định + cược
- [ ] Khoá bot đang bận duel/trade/party
- [ ] Catalog panel + test 5 ca

## Success criteria
- Bật công tắc: đánh được bot lẫn người trong thành, không bị cộng điểm PK; tắt công tắc: về nguyên trạng.
- Chọn đích danh bot theo tên và solo trọn trận với thưởng/phạt đúng.

## Risks
- Giết người trong thành khi quên `SetPunish(0)` → dính truy nã (`killer.ini`): luôn đi cặp FightState+Punish, có test riêng.
- PK thành phá gameplay bán hàng: ngoại lệ khu Đà Tẩu + lính gác tuần tra (tái dùng `CreatePatrol` `pthanhthi.lua:99`).
- Bot đang party/trade bị thách đấu → xung đột state: check `partyPlayerId/tradeState` trước khi nhận.
