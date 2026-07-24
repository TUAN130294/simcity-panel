# Research 01 — Kiến trúc bot SimCity (đầy đủ file:line)

> Rà 2026-07-18 trên bản chép từ VM. Gốc: `/home/jxser/server1/script/global/nobitaxd/vdk/simcity` (viết tắt `simcity/`). Tổng ~13.200 dòng, 39 file active (không tính .bak).

## Kiến trúc tổng thể

- **Entry**: `main.lua` include `head.lua`; `head.lua:31-46` nạp theo thứ tự: config → libs → **plugins** → data (đọc file settings) → 2 class chính `sim_theosau.lua`, `sim_citizen.lua`, rồi gọi `SimCityNgoaiTrang:init()` + `SimCityNPCInfo:init()`.
  - ⚠️ Thứ tự nạp quan trọng: plugins TRƯỚC data → `libs/data.lua:5` gán đè `SimCityChat = {}` rồi nạp `chat.txt` → dữ liệu chat hard-code trong `plugins/pchat.lua` bị xoá sổ.
- **2 "instance" bot**: `SimCitizen` (bot thành thị/Tống Kim/luyện công — objCopy từ `SimCore`, `class/sim_citizen.lua:2`) và `SimTheoSau` (bot theo sau người chơi: kéo xe/tiểu thiếp/pet, `class/sim_theosau.lua:2`).
- **Composition pattern**: mỗi bot (1 record Lua `tbNpc` trong `fighterList`) gắn 4 hệ theo role tại `components/sim.core.lua:167-170`: `movementSys` (SimMovement.Citizen/KeoXe/FormationChild), `funSys`, `entitySys` (SimEntity.Citizen/KeoXe), `fightSys` (SimFight.Citizen/KeoXe).
- **`class/group_fighter.class.lua` (1927 dòng) + 2 file timer = LEGACY KHÔNG NẠP** — không được include từ `head.lua` hay file active nào (chỉ tự tham chiếu + .bak). Phiên bản cũ tự chứa (SetNpcTimer per-NPC, ParentTick/ChildrenTick). Tham khảo lịch sử, không ảnh hưởng runtime.

## 1. Tạo bot — API engine

Bot **là NPC thật của engine**, tạo bằng `AddNpcEx`:

- `components/sim.entity.lua:72`: `nNpcIndex = AddNpcEx(tbNpc.nNpcId, level, series, nMapIndex, tX32, tY32, 1, name, 0)` (hàm `execCreateChar`). Nếu `GetNpcKind(nNpcIndex) ~= 0` thì xoá ngay (line 75-77).
- Sau khi tạo: `SetNpcCurCamp` (:89), `SetNpcActiveRegion(idx,1)` (:91), `SetNpcParam(idx, PARAM_LIST_ID, id)` (:92), `SetNpcParam(idx, 4, 1)` — cờ "SIM npc" (:100), `SetNpcScript(idx, ".../components/sim.timer.lua")` nhận callback OnDeath (:106), `ChangeNpcFeature` (ngoại trang, qua `pngoaitrang.lua:138`), `SetBotFaction` (:115-118), `SetBotWeaponView` (:120-124), `NpcSit` + `SetNpcStall` + `SetBotStallTier` cho bot bày bán (:126-130), `SetNpcTitle` (rank Tống Kim, :132-134), `SetNpcKind` (:147-151), `SetNpcAI` (qua `fightSys:SetFightState`, `sim.fight.lua:329`), `NPCINFO_SetNpcCurrentMaxLife/SetNpcCurrentLife` (:157-169), `SetNpcLevel(SIMBOT_LEVEL)`, `SetNpcAtkSpeed(SIMBOT_ATKSPEED)` (:161-162).
- Bot tiểu thiếp có menu khi click: `sim.entity.lua:103-105` gán NpcScript = `controllers/tieuthiep.lua`.
- NPC menu điều khiển (Triệu Mẫn/Vô Kỵ) tạo bằng `AddNpc` thường: `ptongkim.lua:327,331,389`.
- Trang trí hội chợ cũng là NPC: `pworld.lua:162` `AddNpcEx(...)` + `SetNpcAI(index,0)`.

**API engine dùng trong simcity** (grep toàn thư mục):
- NPC chuẩn: `AddNpc, AddNpcEx, DelNpc` (bọc `DelNpcSafe` `libs/common.lua:93`), `GetNpcPos, GetNpcName, GetNpcKind/SetNpcKind, GetNpcCurCamp/SetNpcCurCamp, SetNpcAI, SetNpcParam/GetNpcParam, SetNpcScript/GetNpcScript, SetNpcActiveRegion, ChangeNpcFeature, NpcCastSkill, NpcRun, NpcWalk, NpcSit, NpcChat, NpcDropMoney, DropItem, GetNpcSettingIdx, NPCINFO_GetNpcCurrentLife/MaxLife, NPCINFO_SetNpcCurrentLife/MaxLife, NPCINFO_GetLevel, AddNpcSkillState` (`sim.fight.lua:159-163`), `GetNpcAroundNpcList, GetNpcAroundPlayerList, GetAroundNpcList`.
- API custom vdk.so (luôn gọi trong guard `if X then`): xem research-findings.md mục 2 (48 hàm, đã verify bằng strings).
- Player/world: `CallPlayerFunction, SearchPlayer, PIdx2NpcIdx/NpcIdx2PIdx, SubWorldID2Idx/SubWorldIdx2ID, NewWorld` (chỉ dịch chuyển NGƯỜI: `ptieuthiep.lua:179,191,213`, `pbatanh.lua:110`), `Msg2Map, AddTimer/DelTimer, TabFile_*`.
- `SetLogoInfo` KHÔNG xuất hiện trong simcity.

## 2. Vòng đời — timer & state machine

**Timer** (`main.lua:22-23`): `AddTimer(REFRESH_RATE=18, "mainLoop")` ~1s; `AddTimer(54, "worldLoop")` ~3s.
- `mainLoop` (`main.lua:9-15`): `SimCitizen:ATick()` + `SimTheoSau:ATick()`. FastCastTick đã tắt (comment 2026-06-27: ghi đè target engine-AI làm hỏng bot-vs-bot).
- `SimCore:ATick` (`sim.core.lua:1002-1015`): duyệt `fighterList` gọi `OnTimer(fighter)`; >2000 bot thì chia 2 `processGroup` chạy xen kẽ.
- `worldLoop` → `SimCityWorld:ATick(20)` (`pworld.lua:236-265`): `UpdateCombatFlagsAll`, `BotAuraKeepAliveAll`, `SimBotTauntDrain` (hàng đợi chat chửi), `UpdateStallFlags`, `UpdateBotLadder` (BXH TK mỗi ~phút).
- Spawn theo lô: `processBatches` mỗi 3s (`pthanhthi.lua:744-799`, 5-6 batch/map); `autoCreateNpc` khi player vào/ra map (`pthanhthi.lua:453,473`); TimerList cho bả tánh (`pbatanh.lua:212`).
- Chết: engine callback `OnDeath` trong `components/sim.timer.lua:3-11` (route theo PARAM_TYPE: 1=SimCitizen, 2=SimTheoSau) → `SimCore:OnDeath` (`sim.core.lua:195`) → `entitySys.OnDeath` (`sim.entity.lua:229`): swap xác với child còn sống, trừ 30% điểm, respawn (`Respawn` = DelNpc + CreateChar lại) hoặc `Remove` nếu `noRevive=1`.

**State machine mỗi bot** — không có FSM tường minh; tổ hợp cờ trong `SimCore:OnTimer` (`sim.core.lua:685-1000`), thứ tự ưu tiên mỗi tick:
1. Housekeeping: `SetNpcPeace` debounce 3 flip (:697-711); **tụt HP → tự vệ** (`prevHP` :720-766: set `selfDefTick`, lock `duelPlayerId` vào kẻ đánh, `BotDashTo` lướt 12 ô); hồi máu `EnforceBotHp` (heal 350/tick khi <90% HP, tối đa 40s, :767-787); `SetBotSpeed`, `BotMountSync`, lên/xuống ngựa theo skill melee (`SIMBOT_DISMOUNT_SKILLS` :802-819).
2. Quét bot-vs-bot (`BOT_VS_BOT=1`, :826-857): chỉ khi có player PK-mode trong 32 ô; `SimEnemyAround(idx,20)` → `botDuelTarget`.
3. Trade state (`PollTradeStay` trả 1..4, :860-915 — mục 8).
4. `movementSys:IsActive == 0` (không player quanh 32 ô) → `MoveInactive` (đi tuần rẻ).
5. `tick_breath` + reset chống tràn mỗi 1800 tick (:926-937).
6. Poll duel (:939-954) và party (:955-968).
7. Nhánh di chuyển: `dashUntil` → `SimDuelMove` (solo player) → `SimBotDuelMove` (đánh bot) → `SimPartyFollow` → `movementSys:Move`.
8. Mỗi 10 tick: `fightSys:Update` (cast skill) + `fightingScore += 100` nếu đang đánh (:980-989); có `isPlayerEnemyAround` → ép `SetNpcCombat` + cast (:991-998).

Trạng thái chính: đi dạo (`Move`), dừng nghỉ (10% khi tới node), ngồi bán (`stall=1, isStanding=1` — stuck-respawn tắt tại `sim.movement.lua:891-897`), `isFighting=1` (giữ `TIME_FIGHTING` rồi `LeaveFight` nghỉ `TIME_RESTING`), duel/party/trade/dash, isDead.

## 3. Logic đánh nhau (`sim.fight.lua` + sim.core)

**Chọn mục tiêu:**
- NPC quanh: `IsNpcEnemyAround` (`sim.fight.lua:252-269`) — `GetNpcAroundNpcList(RADIUS_FIGHT_SCAN)`, hợp lệ nếu `kind==0` và `IsAttackableCamp(camp1,camp2)==1` (`libs/common.lua:105-119`: khác camp, xử lý đặc biệt camp 0/5); mode "train" đánh cả NPC không phải sim (`GetNpcParam(idx,4)~=1`).
- Player quanh: `IsActive` (`sim.movement.lua:15-52`) quét `GetNpcAroundPlayerList(32/60 ô)`; set `isPlayerEnemyAround = pID` khi: (a) khác camp trong `RADIUS_FIGHT_PLAYER=20` VÀ (`SIMBOT_AGGRO_PLAYER==1` hoặc mode=="train"); (b) tự vệ: có `selfDefTick` và player = `GetNpcLastAttacker` và player KHÔNG peace-mode (`GetPlayerPkMode ~= 0`) — bot chỉ đánh trả khi bị đánh (comment 2026-06-25/26).
- Ưu tiên trong `Move` (`sim.movement.lua:820-867`): 25% (`CHANCE_PREFER_PLAYER`) nhắm player → `TriggerFightWithPlayer`; rồi `CHANCE_JOIN_FIGHT`; rồi `CHANCE_ATTACK_PLAYER` (hoặc khi mất máu); rồi `CHANCE_ATTACK_NPC` tự gây war + kéo đồng bọn qua `GetFightingNPCs` (`sim.fight.lua:391-411` — dây chuyền JoinFight trong `RADIUS_FIGHT_NPC`).

**4 đường bot đánh người thật:** (1) tự vệ; (2) chủ động nếu `SIMBOT_AGGRO_PLAYER`/`SIMBOT_PROACTIVE_PLAYER` (mặc định 0); (3) Tống Kim camp đối địch; (4) duel do player mời. Chặn tuyệt đối bởi `SimCityIsPeaceZone`/`SimCityCanFight` (`libs/common.lua:344-371`): trong thành (`cityPeace=1`, bán kính `SIMCITY_CITY_RADIUS=70` quanh attraction hoặc `cityRect`) và 3 map báo danh 323/324/325 (`SIMBOT_NOFIGHT_MAPS`).

**Skill:** gán lúc init (`sim.core.lua:106-152`): bảng `SimBotSW` mỗi phái 2-3 skill (Thiếu Lâm 318/319/321, Thiên Vương 322/323/325, Đường Môn 339/342/302 + bom 351, Ngũ Độc 353/355 + debuff {72,73,390}, Nga Mi 328/380, Thúy Yên 336/337, Cái Bang 357/359, Thiên Nhẫn 361/362, Võ Đang 365/368, Côn Lôn 372/375); map cứng theo NPC id 1906-1924/2000-2023 (`SimBotNpc`).
- `SimPickSkill` (`sim.core.lua:233-259`): chuỗi debuff Ngũ Độc (reset 60s) → 40% bom 351 (Đường Môn) → skill chính (`skillCastBua`, toggle 2 skill) → fallback `normalCast` từ `settings/global/vdk/simcity/skills.txt` (nạp `libs/data.lua:316-368`).
- Buff: `BuffChar` (`sim.fight.lua:131-229`) — Nga Mi `AddNpcSkillState` 86/89/92/282/332 + aura 92, trận pháp phái (`needCast`) 60s, aura `SetNpcAuraSkill`, hào quang `BotShowAura`.
- Cast: `BotDoSkill(idx, skillId, lv=20, targetIdx)` hoặc `NpcCastSkill(idx, skill, lv, x, y)` (`sim.fight.lua:67-71,79`); duel dùng `BotDuelArm` (engine tự đánh liên tục, `sim.core.lua:551-556`).
- **Sát thương do ENGINE tính** (skill lv 20, `SetNpcLevel(95)`, `SetNpcAtkSpeed(250)`). Lua chỉ quản HP (`maxHP` random 60k-120k, heal 3000/10s hoặc `EnforceBotHp`), giữ khoảng cách theo `SIMBOT_SKILL_RANGE` (`sim.core.lua:214-231`: melee sát 1-2 ô, ranged giữ band `castDist-2..castDist`, kite bằng `NpcRun`).
- Đuổi mục tiêu `NpcRun` mỗi 10 tick (`sim.movement.lua:787-803`); thoát trận khi vào peace zone / hết `tick_canswitch` / `CanLeaveFight`.

## 4. Controllers & Plugins

**Controllers** (`controllers/`) = script dialog gắn NPC qua SetNpcScript (entry mở menu):
- `thanhthi.lua:3` — `SimCityWorld:initThanhThi()` (đăng ký map từ data) + menu Triệu Mẫn; `main.lua` (8 dòng): `main_trieuman()`; `tongkim.lua`: menu TK; `keoxe.lua`: `main_voky()`; `tieuthiep.lua`: menu tiểu thiếp (đồng thời là NpcScript của bot tiểu thiếp → click bot mở menu); `vatnuoi.lua`: menu Lão Độc Vật; `batanh.lua`: menu hộ tống tiêu xa (SimCityBaTanh).

**Plugins** (`plugins/index.lua` nạp 9 file; mỗi plugin = global singleton `SimCityXxx`; kích hoạt qua menu `CreateTaskSay` hoặc hook `onPlayerEnterMap/onPlayerExitMap` từ EventSys):
- **pworld.lua** — registry map `SimCityWorld` (flags allowFighting/allowChat/showName/cityPeace…, `New:99-126`), `IsTongKimMap:194-227`, `IsThanhThiMap:229-234` (37,78,176,162,80,1,11), build path TK map 378/379/380 từ template map 10000 (`modifyTongKimMap:8-98`), `ATick:236-265`.
- **pthanhthi.lua** — spawn dân cư: `onPlayerEnterMap:432` → `autoCreateNpc:478` → `createNpcSoCapByMap:497`: 300 bot/thành (`THANHTHI_SIZE`), 50/thôn, +45-65 stall, +20-30 quanh Đà Tẩu; map báo danh TK 323-325/518/519 spawn wave 20-40 diễu hành; map luyện công 9x: 10 nhóm × 6-7 bot mode "train" chia 4 camp (`:666-735`); batch 3s (`:744-799`). Menu: phát thiếp, tuần tra (`CreatePatrol:99`), giải tán, cài đặt map.
- **pchientranh.lua** — chiến loạn/TK: `taoNV:115` bot `mode="chiendau", tongkim=1` theo `walkPathNames`; `taodoi/taophe:190-324` đội hình nguyên soái + lính formation; `taoHauDoanh:732` (20 bot); `khaiChienTongKim:618` (SetMissionV, thả bot `tick_canWalk=0`).
- **ptongkim.lua** — RANKS 6 cấp (Binh sĩ→Nguyên Soái), `updateRank:247-278` theo `fightingScore` (1k/3k/6k/10k/20k) + SetNpcTitle; player giết bot → `OnDeath:87-221` (liên trảm, `BT_*` ladder thật, `dropItem:223` theo bảng 6 rank); bot giết player → `OnNpcKillPlayer:64`; đặt NPC Triệu Mẫn/Vô Kỵ khi vào map (`onPlayerEnterMap:395-438`).
- **pkeoxe.lua** — đoàn bot SimTheoSau theo player (`taoNV:28`, role="keoxe"), formation vuông `ATick:308-329` + `genCoords_squareshape`; kết giao bằng hữu theo phái (`taoBangHuu:226`).
- **ptieuthiep.lua** — 10 mỹ nhân (1198 Triệu Mẫn…2424 Ân Ly), giá 10 vạn (`nhanTieuThiepConfirm:139`: Pay(100000), faction ngami, skill hồi máu 93); xin thuốc/TDP/tiền (`nhanTien:256` — 10% cho 1-5 vạn), triệu hồi PT/bang (`GoiPTToiNoi:163`, NewWorld), bãi luyện clone quái (`TaoBai:375`), đứng chờ/đi theo.
- **pvatnuoi.lua** — pet shop: tối đa 3 pet từ `pets.txt` (Pay/Earn hoàn 5 vạn), lưu task-byte 2480-2484 (`savePetsToProfile:298`), tự spawn khi vào map (`onPlayerEnterMap:371`), skill theo phái, ẩn/hiện.
- **pbatanh.lua** — hộ tống heo/hươu/voi/xe lương + gia nhân (`NewJob:52`), theo player TimerList 1s (`WalkAllTieu:139`), thưởng 10 vạn + buff 509.
- **pname.lua** — `SimCityPlayerName.data` ~600 tên giả, `getName():608`. (Bot thật lấy tên `SimCityNPCInfo:generateName()` → `names.txt` qua `data.lua:15-20`.)
- **pngoaitrang.lua** — đọc npcres `\settings\npcres_simple\*.txt` (:33-95), whitelist/blacklist (:102-127), `makeup:130` → `ChangeNpcFeature` + `SetNpcRideHorse(1)`.
- **pnpcinfo.lua** — DB NPC đọc `\settings\npcs.txt` (name/kind/camp/series/maxLife/runspeed, `init:247-352`), blacklist ~200 id, pool theo cấp; `SIMBOT_UNIFY_2000=1` → mọi pool trả id 2000-2023 (24 mẫu bot phái).
- **pchat.lua** — bảng chat hard-code cũ (BỊ `data.lua:5` GHI ĐÈ `SimCityChat = {}` vì data nạp SAU plugin — nguồn chat thực = `chat.txt`).

## 5. Chat bot

- Nguồn: `settings/global/vdk/simcity/chat.txt` — 2 cột (loại, câu), nạp `libs/data.lua:23-31` thành `SimCityChat[type]`. Type dùng trong code: `general`, `fighting`, bộ reply `rep_chung/rep_ok/rep_no/rep_chao/rep_giaodich/rep_boss/rep_chui` (map từ số C, `sim.fun.lua:3`).
- Phản hồi người chơi: `execChat` (`sim.fun.lua:5-17`): `HasPlayerSay()` + `PollSayForBot(idx)` trả category (keyword matching Ở TẦNG C) → `NpcChat` câu random đúng loại. Chat vu vơ 1%/lần (`CHANCE_CHAT=10/1000`).
- ⚠️ **`funSys.Update` (nơi duy nhất gọi execChat, `sim.fun.lua:177,203`) KHÔNG còn được gọi từ `SimCore:OnTimer`** (grep: chỉ `funSys:OnDeath` được gọi, `sim.entity.lua:234,357`) → chat vu vơ + reply + rơi tiền khi đi + hồi máu SimFun = DEAD CODE bản hiện tại. Kênh sống: (1) taunt `SimBotTaunt/SimBotTauntDrain` (`sim.core.lua:282-305`, `rep_chui`, drain 1 câu/1-2s từ worldLoop) khi bot thắng duel/đối thủ chạy vào peace zone; (2) 10 câu tạm biệt trade hard-code (`sim.core.lua:896`).

## 6. Di chuyển & waypoint

- Data: `settings/global/vdk/simcity/maps/thanhthi.txt` (worldId, tên, file, loại nodes|preset) + `attractions.txt` (địa danh) + `haudoanh.txt` + `trangtri.txt` — nạp `libs/data.lua:70-313`. Node tên `"x_y"`, có `linkedNodes` (đồ thị), `isExact`, `nodeType` (0 thường/1 war), tự đánh dấu `isNearAtraction` nếu cách địa danh <8 ô; preset path = danh sách node theo tuyến, node thiếu snap/nối tự động bán kính 16.
- 3 kiểu đi (`sim.movement.lua`):
  - `Citizen` random-walk: chọn cạnh kề chưa đi 2 lần gần nhất (`GetRandomWalkPoint:528-608`), tới nơi (`HasArrived` < `DISTANCE_CAN_CONTINUE=5`) → 90% đi tiếp/10% dừng; bước = `NpcRun(idx, x±walkVar, y±walkVar)`.
  - `preset/formation`: path tuần tự 2 chiều (`pathDirection ±1`); TK ghép segment (`walkPathNames`); hết đường mode chiendau lùi 10 điểm hoặc sang segment kế (`NextPathSegment:253-398`, BFS/DFS `libs/walk_chientranh.lua` `find_all_paths/build/autoFindPathNames`); TK rally: thủ boss mình/đánh boss địch/dồn giữa map (`Move:873-888`).
  - `FormationChild`: bám cha hình thoi (`genCoords_squareshape` `libs/walk.lua:123-198`), cha đứng con đứng (`:1283-1287`); `KeoXe.Move` bám player, respawn khi khác map/quá 30 ô (`:206-224`).
- Map áp dụng: 7 thành (37,78,176,162,80,1,11), 8 thôn (53,20,99,100,101,121,153,174), luyện công 9x, TK 375-386/580/581/868-870/883-885/900-904 (378-380 dùng node map 10000), báo danh 323-325.

## 7. config.lua — thông số chính (:1-107)

| Nhóm | Thông số |
|---|---|
| Xác suất đánh | CHANCE_AUTO_ATTACK/JOIN_FIGHT/ATTACK_PLAYER=1, CHANCE_PREFER_PLAYER=25%, SIMBOT_PROACTIVE_PLAYER=0, SIMBOT_AGGRO_PLAYER_PCT=30, SIMBOT_ATTACK_PLAYER_CHANCE=3, BOT_VS_BOT=1, BOT_COMBAT_RADIUS=20 |
| Số lượng | THANHTHI_SIZE=300, THON_SIZE=50, stall thành 45-65/thôn 0-1/Đà Tẩu 20-30, TONGKIM_BOT_WAVE 20-40, LUYENCONG_NHOM 6-7 |
| Chỉ số | SIMBOT_LEVEL=95, SIMBOT_HP_MIN/MAX=60k-120k, SIMBOT_HP_CAP1..3, SIMBOT_ATKSPEED=250, SIMBOT_HEAL_AMOUNT=3000, SIMBOT_WALK_SPEED=15/RUN=24, LIFE_RESTORE_PERCENT=5 |
| Bán kính | RADIUS_FIGHT_PLAYER=20, RADIUS_FIGHT_NPC=8, RADIUS_FIGHT_SCAN=8, DISTANCE_FOLLOW_PLAYER=28/SUPPORT=8/TOOFAR=30 |
| Thời gian | TIME_FIGHTING 6000/6000, TIME_RESTING 0-1, REFRESH_RATE=18, TONGKIM_SPAWN_STAY 0-1 |
| Kinh tế/chat | CHANCE_CHAT=10/1000, CHANCE_DROP_MONEY=0, DROP_MONEY_WALK 1k-10k, DROP_MONEY_DIE 1k-100k, tiểu thiếp cho tiền 10% 1-5 vạn, 25 thuốc, 3 TDP |
| Khác | SIMBOT_TK_LA_NGUOI=1, THANHTHI_QUAI=0, THANHTHI_BANG_PCT=50, SIMBOT_CITY_BUFF_PCT=30, SIMBOT_KEEP_WALKING_PCT=90, PARAM_LIST_ID/CHILD_ID/TYPE=1/2/3, STARTUP_AUTOADD_THANHTHI=1, LUYENCONG_AUTOADD=1 |

## 8. Trade / tổ đội / duel — CÓ ĐỦ CẢ 3 (logic hiện tại)

- **Trade**: `sim.core.lua:860-915` — `PollTradeStay(idx)` trả state: `2` = đang trade → sau 8s `SendTradeItem` (bot đưa item); `3` = post-trade chờ 27s → `TradeStayClear`; `1` = player mời chưa mở → chờ 38s, chat 1/10 câu "thoi t di nha :)" (`:896`) rồi bỏ đi; `4` = greet-stay 54s. Trong trade bot đứng yên (return 0 mỗi tick).
- **Party**: `PollParty` (`sim.core.lua:955-968`) — player mời bot vào PT; bot đổi camp theo player; `SimPartyFollow` (`:324-463`): theo 1/8 hướng octant, theo qua map khác (DelNpc + CreateChar tại chỗ player + `PartyRebind` giữ icon PT), quét địch quanh player 12-16 ô ĐÁNH HỘ (`BotDuelArm/BotDoSkill`, camp tạm `partyHuntCamp` đánh cả mob trung lập), rời khi player chết 2 lần/mất tích 90 tick/`PollParty<=0` → `PartyEnd` (`:307-322`, `PartyClear`).
- **Duel**: `PollDuel` (`sim.core.lua:939-954`) — player thách; bot đổi camp đối địch, `duelTicks=300`, `SimDuelMove` (`:464-604`): giữ khoảng cách theo skill, `BotDuelArm` đánh liên tục, buff trận 60s, `BotPlayerMove/BotMountSync` (di chuyển kiểu player, protocol 75), kết thúc `SimDuelEnd` (`:261-280`, `SetNpcDuelEnd`, hồi camp) khi hết giờ/player vào thành/tắt PK-mode. Nhánh `selfDefDuel=1` = duel tự phát khi bị đánh lén (`OnTimer:725-735`), có `BotDashTo` né + taunt khi đối thủ bỏ chạy.
