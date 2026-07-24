# Tổng hợp nghiên cứu code — nền cho 8 tính năng

Rà ngày 2026-07-18 trên bản chép từ VM (`/home/jxser/server1/`). Viết tắt:
- `SIM` = `script/global/nobitaxd/vdk/simcity`
- `SET` = `settings`
- Toạ độ lưới = pixel/32. 18 frame = 1 giây. Engine Lua 5.0 (có `io.open`, `os.execute`; không `require`/socket).

## 1. Kiến trúc bot SimCity

- Boot: activity 801 (`activitysys/config/801/head.lua:15`) → `vdk/main.lua` → `SIM/main.lua` → `head.lua:31-46` nạp config → libs → plugins → data (đọc `SET/global/vdk/simcity/*.txt`) → 2 class `SimCitizen` (dân thành thị/Tống Kim/luyện công) + `SimTheoSau` (kéo xe/tiểu thiếp/pet).
- Bot là **NPC engine thật**: `AddNpcEx(npcId, level, series, mapIdx, x32, y32, 1, name, 0)` tại `SIM/components/sim.entity.lua:72`, sau đó `SetNpcCurCamp/SetNpcParam/SetNpcScript(sim.timer.lua)/ChangeNpcFeature/SetBotFaction/SetBotWeaponView/SetNpcTitle/SetNpcBang/SetNpcLevel(95)/SetNpcAtkSpeed(250)`.
- Tick: `AddTimer(18,"mainLoop")` ~1s/lần (`SIM/main.lua:22`) duyệt `fighterList`; `worldLoop` 3s (`pworld.lua:236`). Chết → `OnDeath` (`sim.timer.lua:3`) → respawn/swap.
- Composition 4 hệ theo role (`sim.core.lua:167-170`): movementSys / funSys / entitySys / fightSys.
- Đánh nhau: engine tính damage (bot chỉ chọn skill `SimPickSkill` `sim.core.lua:233-259`, bảng skill phái `SimBotSW` + `SET/global/vdk/simcity/skills.txt`). Tự vệ khi bị đánh (`selfDefTick` `sim.core.lua:720-766`), bot-vs-bot khi có player PK gần, KHÔNG đánh trong vùng an toàn (`SimCityIsPeaceZone` `SIM/libs/common.lua:344-371`, `cityPeace=1`, bán kính `SIMCITY_CITY_RADIUS=70`).
- **Tương tác có sẵn với người chơi:** duel (`PollDuel` `sim.core.lua:939-954` → `SimDuelMove:464-604`, `BotDuelArm`); tổ đội (`PollParty:955-968` → `SimPartyFollow:324-463`, đánh hộ, theo qua map, `PartyRebind`); giao dịch (`PollTradeStay:860-915` state 1-4, sau 8s `SendTradeItem` tặng đồ, 10 câu tạm biệt `:896`); trả lời chat (`HasPlayerSay`+`PollSayForBot` → `execChat` `sim.fun.lua:5-17` — **lưu ý: `funSys.Update` hiện là dead code, không được gọi từ OnTimer**); hàng đợi chửi `SimBotTaunt/SimBotTauntDrain` (`sim.core.lua:282-305`) đang sống.
- Di chuyển: đồ thị node `SET/global/vdk/simcity/maps/thanhthi/<mapid>_<ten>_nodes.txt` (TSV `node linked_nodes is_exact type`, node tên `x_y`) + `_preset.txt` (tuyến); đăng ký trong `thanhthi.txt`. 271 file/~135 map. Muốn bot đi map mới: sinh cặp nodes/preset + 1 dòng đăng ký.
- Legacy KHÔNG nạp: `SIM/class/group_fighter.*` (3 file), `plugins/pchat.lua` data bị `libs/data.lua:5` ghi đè (nguồn chat thật = `chat.txt`).

## 2. vdk.so — 48 hàm C vá (xác minh bằng `strings` 2026-07-18)

`BotAuraKeepAliveAll BotDashTo BotDismountSkill BotDoSkill BotDuelArm BotDuelDisarm BotForceCast BotLadderAdd BotLadderBroadcast BotLadderClear BotMountSync BotPlayerMove BotSayLocal BotShowAura EnforceBotHp GetBotPoints GetNpcAreaRaw GetNpcDoing GetNpcLastAttacker GetNpcRideHorse GetPlayerPkMode HasPlayerSay PartyClear PartyClearPlayer PartyRebind PollDuel PollParty PollSayForBot PollTradeStay SendTradeItem SetBotFaction SetBotPoints SetBotSpeed SetBotStallTier SetBotWeaponView SetNpcAtkSpeed SetNpcBang SetNpcCombat SetNpcDuelAI SetNpcDuelEnd SetNpcFightTarget SetNpcLevel SetNpcPeace SetNpcRideHorse SetNpcStall SetNpcTitle SimEnemyAround TradeStayClear`

- Chưa dùng trong Lua: `BotSayLocal`, `SetNpcDuelAI`, `BotForceCast`, `GetNpcAreaRaw`, `PartyClearPlayer`, `GetBotPoints`.
- File `/home/jxser/server1/vdk.so` build 2026-07-04, 54KB. **Không tìm thấy source trên VM** (đã tìm /root, /home). Keyword→category của `PollSayForBot` nằm trong C.

## 3. chat.txt — 21 category (SET/global/vdk/simcity/chat.txt, TSV `Type\tChat`)

`general`(1690) `fighting`(928) `rep_vonhom/tuchoinhom/tuchoi/cho/chao/camon`(10 mỗi loại) `rep_nhomfull`(8) `rep_chui`(6) `tantinh/solo/hoatdong`(5) `rep_ok/no/giaodich/chung/boss`(5) `giaodich`(5) `rep_solo`(4). Lua mới map 0-5 (`SIM/sim.fun.lua:3`: rep_chung/ok/no/chao/giaodich/boss) — C phân loại nhiều hơn mức Lua đang dùng.

## 4. API engine chuẩn (script gốc)

- **Teleport:** `NewWorld(mapid, x, y)` (`gmscript.lua:311,408`); `SetPos(x,y)`; `GetPos()`; `GetWorldPos()` → `w,x,y` (`gmscript.lua:444-447`); `SubWorldID2Idx(id)` → -1 nếu map không load. Teleport người khác: đổi `PlayerIndex` hoặc `CallPlayerFunction(pIdx, NewWorld, m, x, y)` (mẫu `battles/singlefight/gofight_dt.lua:79-128`).
- **PK:** `SetFightState(0|1)/GetFightState`, `SetPKFlag(0|1)`, `SetPunish(0|1)` (tắt phạt PK — mẫu `battles/guozhan/head.lua:388`, khôi phục `missions/challenge/challengehead.lua:48`), `ForbidChangePK`, `SetCurCamp/GetCamp`, `SetDeathScript(path)`.
- **1v1 sẵn có:** `battles/singlefight/gofight_dt.lua:2` `BT2DTFight(missionid, P1, P2)` — map riêng từ `[Area_SingleFight]` trong mapinfo battles, timer 3 phút, death/end script.
- **Trade:** KHÔNG có API mở cửa sổ trade từ Lua. Thay thế: `AddItem(genre,detail,particular,level,series,luck[,extra])`, `AddEventItem(id)`, `GetItemCountEx(id)`, `Earn/Pay/GetCash`, `tbAwardTemplet:GiveAwardByList`, `ForbitTrade(0|1)`, `CalcFreeItemCellCount()`.
- **Tổ đội:** `GetTeamSize/GetTeamMember(i)/IsCaptain/LeaveTeam/SetCreateTeam/GetTeam`; helper `lib/player.lua:53-82`.
- **Dialog:** `Say(text,n,"opt/Fn",...)`, `Talk(n,"cb",...)`, `CreateTaskSay{...}` (opt `"text/#Fn(1)"`), `AskClientForString/Number`, framework `dailogsys/` (menu per-player có state). Tag `<color=red>`, `<enter>`.
- **Timer/hook:** `AddTimer(frames,"Fn",param)` (return >0 = lặp), `DelTimer`; hook: `global/login.lua` (`login_add`), `global/logout.lua`, `global/autoexec.lua` (boot, `:549` LoadActivitys), map header `maps/newworldscript_h.lua` (bảng `aryFuncStore` bật/tắt tính năng per-map), trap = file lua có `main(sel)`, `SetDeathScript`.
- **Thông báo:** `Msg2Player`, `Msg2Map(worldId,msg)`, `Msg2SubWorld` (toàn server), `Msg2MSAll(missionid,msg)`, `NpcChat(idx,msg)` (bong bóng).
- **Mission/instance:** `OpenMission(id)/RunMission/SetMissionV/AddMSPlayer/GetMSPlayerCount`; phó bản động `PreApplyDungeonMap/ApplyDungeonMap/ReturnDungenonMap` (`missions/dungeon/dungeonmanager.lua:60-82`), `SubWorldIdx2MapCopy`.

## 5. Vận tiêu — activity 12 (`activitysys/config/12/`)

- `head.lua`: id 12, hạn 2012→2050 (còn hiệu lực). `carriage.lua:10-27` 17 waypoint; `:31-53` spawn xe NPC **1903** "<tên player> Xe Ngựa", `SetNpcAI(0)`, `SetNpcTimer(18)`; `:57-83` OnTimer NpcWalk theo tuyến → hết tuyến `TaskFinish`; `:94-120` **OnDeath → TaskFailed + rơi "Hỗn Nguyên Linh Lộ" cho KẺ GIẾT** (= cướp tiêu). `extend.lua`: nhận NV nộp 1 Hỗn Nguyên Linh Lộ, max 20 xe server, 3 lần/ngày, thưởng 40tr exp; `ServerStart` rải Giặc Cỏ 1607-1609 lv95 dọc đường. `config.lua`: NPC nhận "Tống Tiêu Đầu" + trả "Diêm Thương Thanh Thành Sơn" ở map 21.
- Entry hiện tại DUY NHẤT: NPC lái đò Phượng Tường include `config/12/extend.lua`. Cần xác minh activity 12 có trong danh sách `G_ACTIVITY` khi boot.
- Mảnh tái dụng: `battles/seizegrain` (vác lương `ChangeOwnFeature`, đốt xe bằng Hỏa thạch 1763, broadcast toạ độ); bot follower `SIM/plugins/pkeoxe.lua` + `SimTheoSau`.

## 6. Map & PK per-map

- `SET/maplist.ini`: 992 map (`<id>=path` + `_name/_MapPos/_MapType/_NewWorldScript/_NewWorldParam/_MapInfo...`). 599 map NewWorld (có script), 221 map tĩnh có MapPos, **264 map không có cả hai = quỹ map ẩn**.
- **Công tắc load map: `maps/worldset.ini`** — `[World] Count=139, World00..138=<id>`. Map ngoài danh sách = không load (`SubWorldID2Idx` = -1).
- Cờ `_NewWorldParam` (chỉ map NewWorld): `FIGHTSTATE_ON/OFF, PUNISH_OFF, PUNISH_PK10, HEART_OFF, STALL_OFF, CreateTeam_OFF, USETOWNP_OFF, NOTONGCLAIMWAR, TONG_MAP, NATIONALWAR...` — xử lý trong `maps/newworldscript_h.lua` (`aryFuncStore`).
- `SET/forbitheart.txt`: map cấm chế độ hoà bình (926-933, 960). `SET/map_type.txt`: nhóm map cấm item (`SONGJIN`, `BAIRENLEITAI 960 TRANSFER,MATE,CALLNPC,PK,SPECIAL`...). `SET/citywar.ini`: công thành/thuế 7 thành (không phải switch PK). `killer.ini`: hệ truy nã.
- 7 thành: 1 Phượng Tường, 11 Thành Đô, 37 Biện Kinh, 78 Tương Dương, 80 Dương Châu, 162 Đại Lý, 176 Lâm An (map tĩnh MapType=City — không có NewWorldParam).
- **Map 960 "Lôi Đài Hoàng Thành Tứ"** (Bách Nhân Lôi Đài): `PUNISH_OFF|USETOWNP_OFF|HEART_OFF|CD_Forbid_OFF`, dữ liệu `SET/maps/missions/bairenleitai/`: `inmap.txt` 10 điểm vào, `arena1..5.txt` viền 5 đài, `obstacle/drummer/chefu/chuwuxiang/drugstore.txt`.
- Quỹ map event script đã biết: `global/forbidmap.lua` — `__YANDIBAOZANG` {851-862,871-874,892-896,901} + dải 906-916.
- Activity system: thư mục `activitysys/config/<id>/` (head/config/extend/registe), message bus `G_ACTIVITY:OnMessage` (`ClickNpc/ServerStart/Chuanguan/ItemScript...`), boot `autoexec.lua:549-551`. Giờ mở kiểu Tống Kim: check `GetLocalDate("%H%M")` trong `battles/battlejoin.lua:190`.

## 7. Giả lập người chơi & đối thoại

- Mức hoá trang hiện tại: tên (pool 604 + `names.txt`), bang+chức vụ (`SetNpcBang`, 50% bot), danh hiệu rank TK (`SetNpcTitle`), ngoại trang+ngựa (`ChangeNpcFeature` từ `SET/npcres_simple/`), skill đúng phái, bán sạp, BXH TK client thấy như thật (`BotLadderAdd/Broadcast`).
- Đọc dữ liệu người chơi: CHỈ khi online (`GetName/GetLevel/GetFaction/GetTong/GetTongName` qua `CallPlayerFunction`). KHÔNG có API đọc save offline/DB từ Lua. `io.open` hoạt động (tiền lệ `vdk/tinhnang/taotrangbi.lua:1313`).
- Giới hạn cứng bot-NPC: không trong danh sách online/bạn bè, không whisper, không chat kênh bang/tổ đội thật, click bot không có hồ sơ trang bị.
- Hội thoại: 3 tầng — (1) FSM thuần Lua trên `chat.txt` mở rộng; (2) vá C `PollSayText` trả nguyên văn + playerIdx [CẦN SOURCE VDK.SO]; (3) cầu file `io.open` ↔ daemon Python/LLM ngoài (poll trong `pworld.lua ATick`).

## Câu hỏi tồn đọng

1. Source vdk.so? (chặn tầng C của phase 04/05/07)
2. `NpcChat`/`BotSayLocal` hiển thị ở đâu trên client — cần test in-game.
3. Chuỗi include `registe.lua` của activitysys không thấy trong cây — xác minh trên VM lúc làm phase 06.
4. Chữ ký chính xác `SendTradeItem/PollTradeStay` (mới suy được 1 tham số npcIndex).
