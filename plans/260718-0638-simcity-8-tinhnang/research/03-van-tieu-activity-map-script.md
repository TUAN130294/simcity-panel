# Research 03 — Vận tiêu / Activity system / Map trong script (đầy đủ file:line)

> Rà 2026-07-18. `S:\` = `/home/jxser/server1/script`.

## (A) Vận tiêu / Cướp tiêu

**Kết luận: ĐÃ CÓ hệ hộ tống xe hoàn chỉnh — activity 12, đang "ngủ" (chỉ kích hoạt qua 1 NPC lái đò Phượng Tường). Không có hệ 运镖 cổ điển khác; NPC "tiêu cục/tiêu đầu" trong thành chỉ là dialog trang trí.**

### Activity 12 — hộ tống xe ngựa
- `S:\activitysys\config\12\head.lua:1-9` — pActivity nId=12, tên "2012年4月护送活动", nStartDate=201204020000, nEndDate=205005010000 (còn hạn).
- `S:\activitysys\config\12\carriage.lua`:
  - `:10-27` TRACK_LIST = 17 waypoint (toạ độ *32).
  - `:31-53 add_carriage()` — spawn NPC id **1903** ("<tên player> Xe Ngựa") tại waypoint 1, `SetNpcAI(0)`, `SetNpcTimer(18)`, gắn camp người nhận.
  - `:57-83 OnTimer` — mỗi ~1s `NpcWalk()` tới waypoint kế; hết tuyến → `pActivity:TaskFinish` + DelNpc.
  - `:94-120 OnDeath` — xe bị giết → `TaskFailed` + **rơi "Hỗn Nguyên Linh Lộ" CHO KẺ GIẾT** (`tbDropTemplet:GiveAwardByList`) = cơ chế CƯỚP TIÊU.
- `S:\activitysys\config\12\extend.lua`:
  - `GiveTask` (:16-49): nộp 1 Hỗn Nguyên Linh Lộ (compose :150-170) nhận xe; max 20 xe toàn server, 1 xe/người, phải nhận thưởng trước khi nhận tiếp.
  - `TaskFailed/TaskFinish/AddWinner` (:66-100); `GiveAward` (:135-143): 40e6 exp + item.
  - `ServerStart` (:126-133): rải "Giặc Cỏ" (NPC 1607-1609 lv95) dọc tuyến theo `MOSTER_POS` (variables.lua).
- `S:\activitysys\config\12\config.lua`: tbConfig[1] ClickNpc "Tống Tiêu Đầu" (nhận NV), [2] điều kiện lv≥50 + 3 lần/ngày (`CheckTaskDaily`), [3] trả thưởng NPC "Diêm Thương Thanh Thành Sơn", [4] ServerStart spawn 2 NPC map 21 (`NpcFunLib:AddDialogNpc {"…",244,{{21,1949,3499}}}` và `{376,{{21,2873,3649}}}`).
- Entry hiện tại: `S:\Î÷±±ÄÏÇø\·ïÏè\ְÄÜnpc\Î÷±±ÄÏÇø-·ïÏ踮-Âëͷ´¬·ò¶Ի°.lua:8` include `config\12\extend.lua` (NPC lái đò Phượng Tường).

### Mảnh ghép tái dụng
- **battles/seizegrain (Cướp Lương TK)** — "vác hàng + cướp + đốt": `head.lua:70-71` NPC 1348 xe lương, 1350 bao lương; `sf_addgrain/sf_addgharry :105-150`. `graingharry.lua:33-64` — nhặt bao: `ChangeOwnFeature(0,0,1341/1342)` (đổi ngoại hình người vác), aura 460/461, buff tốc 656, broadcast toạ độ người vác toàn trận; `:65-88` — địch dùng **Hỏa thạch (item 1763)** đốt xe (`ConsumeItem` + đổi xe thành xe chiến đấu có DeathScript).
- **SimCity keoxe** (bám player, KHÔNG theo tuyến): `S:\global\nobitaxd\vdk\simcity\plugins\pkeoxe.lua` — `taoNV :28-89` role/mode="keoxe" qua `SimTheoSau:New`; tự respawn khi xa/đổi map (`sim.movement.lua:1310-1370`); menu :276-290. Tái dụng làm "tiêu sư/hộ vệ".
- **Route graph simcity** (tuyến tốt nhất cho vận tiêu dài): `S:\global\nobitaxd\vdk\simcity\libs\data.lua:3` settingsPath = `\settings\global\vdk\simcity\`; pathfinding `find_all_paths` + `NextPathSegment` `sim.movement.lua:253-337`.
- NPC tiêu cục trang trí (chỉ Say 7 dòng): `S:\ÖÐԭ±±Çø\ã꾩\ã꾩\npc\ã꾩_ïھÖÀϰå¶Ի°.lua` (+ tương tự Tương Dương/Dương Châu/Thành Đô/Phượng Tường); `S:\task\newtask\master\xiepai\ÑïÖÝ_ïÚʶ.lua` = mốc nhiệm vụ lv30.

## (B) Activity system

### Kiến trúc
- Registry: `S:\activitysys\g_activity.lua` — `G_ACTIVITY:AddActivity` (:114), `RegisteMessage/OnMessage(szKey,...)` (:34-53) — bus sự kiện.
- ActivityClass: `S:\activitysys\activity.lua` — `CheckDate` theo nStartDate/nEndDate `YYYYMMDDHHMM` (:33-51), `LoadConfig` → Detail (:66-84), task qua TaskManager (nGroupId/nVersion), `CheckTaskDaily/AddTaskDaily` (:163-228), `GiveAward` templet (:246).
- 1 activity = thư mục `S:\activitysys\config\<id>\`: `head.lua` (pActivity + id + ngày), `config.lua` (tbConfig: mảng detail `{szMessageType, tbMessageParam, tbCondition, tbActition}`), `extend.lua` (logic riêng), `registe.lua` (AddActivity). Message types: `ClickNpc`, `ServerStart`, `Chuanguan`, `CreateCompose`, `ItemScript`, `nil` (gọi tay `ExecActivityDetail`).
- Boot: `S:\global\autoexec.lua:549-551` — `G_ACTIVITY:LoadActivitys(); G_TASK:LoadAllConfig(); G_ACTIVITY:OnMessage("ServerStart")`. Nguồn bắn message: `activitysys\npcdailog.lua` (click NPC), `g_npcdeath.lua` (OnGlobalNpcDeath), `g_itemuse.lua`, battles (`seizegrain\head.lua:501` "SignUpSongJin"), `missions\challengeoftime\npc_death.lua:163` "Chuanguan".

### 3 mẫu để nhái
1. Activity 12 — hộ tống (trên): ClickNpc + ServerStart spawn NPC + daily limit + compose + NPC di chuyển theo tuyến.
2. Activity 36 — "Đa năng động" (đang dùng cho event server này): `config\36\head.lua` (nStartDate=0/nEndDate=0 = vĩnh viễn), `config.lua:8-40` detail `Chuanguan` thưởng theo ải — mẫu hook sự kiện gameplay.
3. Activity 26 — Đại Yến Quần Hiệp: `config\26\variables.lua:26` + `config.lua:536-568` — `AddNpcFromFile("...", 1660, "\settings\maps\dayanqunxia\datouwawa.txt", 176)` — mẫu spawn hàng loạt NPC theo file toạ độ.

### Lập lịch
- Check giờ trong dialog: Tống Kim `S:\battles\battlejoin.lua:190-191` `GetLocalDate("%H%M")` cửa 20:45–23:00; tương tự `missions\challengeoftime\npc\transfer.lua:38`.
- Timeline system: `S:\misc\timeline\timelinemanager.lua` + `timelinelist.lua:1-60` (3 loại: `ServerOpenTimeEvent` (N ngày sau mở server), `FixTimeEvent` (ngày cố định), `RefTimeEvent`); load `autoexec.lua:553` `tbTimeLineManager:LoadAllTimeLine(tbTimeLineList)`.
- Mission theo map: `S:\missions\basemission\class.lua:135-160` — `StartGameInMap(nMapId)` → `SubWorldID2Idx` → `doFunInWorld(nMapIndex, OpenMission, self.nMissionId)`; battles: `S:\battles\battlemain.lua:4-49` `main(battleid, mapid, ruleid, level, seriesid)` → GAME_* rồi `OpenMission(ruleid)` (engine gọi theo cấu hình battle ngoài cây script).

## (C) Map trong script

### API
- `SubWorldID2Idx(mapId)` → index runtime, **-1 nếu không load** (234 file dùng; `autoexec.lua:581`, `config\12\carriage.lua:35`). `SubWorldIdx2ID(SubWorld)` ngược lại.
- `SubWorldIdx2MapCopy(idx)` → map id template gốc khi đứng trong bản copy (`maps\checkmap.lua:73`, `item\checkmapid.lua:11`, `global\judgeoffline.lua:199`).
- `NewWorld(mapid,x,y)`; `doFunInWorld(idx, fn, ...)` chạy hàm trong context map khác (`missions\dungeon\dungeonmanager.lua:39,352`).
- Bảng phân loại trong script: `S:\maps\checkmap.lua:1-47` (thành thị {1,11,37,78,80,162,176}, tân thủ, bang hội template 586-597); `S:\global\forbidmap.lua` (guard BAN_HEAD): `__SJMAPS` TK {44,326-374,375-386,863}, `__BWMAPS` {396-415,527-538,540-579,864-867}, `__ZQMAPS`, `__FHMAPS` (516-519,580-581,605-613), `__TONGMAPS` {586-597}, `__YANDIBAOZANG` **quỹ map event** {851-862,871-874,892-896,901}; `checkActMaps` nhận thêm dải **906-916**. Event dùng chúng: `missions\yandibaozang`, NPC vào cửa `autoexec.lua:228-235`.

### Instance động
- Dungeon: `S:\missions\dungeon\dungeonmanager.lua:60-61` — `PreApplyDungeonMap(nMapTemplet,1,1)` + `ApplyDungeonMap(nMapTemplet)` cấp bản copy động, trả bằng `ReturnDungenonMap(...)` (:82,161); đăng ký `RegDungeon{strDungeon, nMapTemplet}` (:11-18); sync liên server `RemoteExc` (:105,145). `maps\newworldscript_h.lua:155` xử lý player rơi vào map copy.
- Map bang hội: pool copy động `S:\tong\addtongnpc.lua:44-69` (`aDynMapCopy`, `GetMapEnterPos(nMapCopy)`).

### Đường dẫn `\settings\` mà script đọc
- `\settings\maps\dayanqunxia\*.txt`, `\settings\maps\chrismas\player.txt`, `\settings\maps\springfestival2006\player.txt`, `\settings\maps\dragonboatfestival_06\player.txt`, `\settings\maps\championship\champion_gmpos.txt`.
- `\settings\activitysys\42\npcpos.txt`, `\settings\activitysys\awardtable\<id>.txt` (`activitysys\functionlib.lua:69`).
- `\settings\task\dailytask\{gather,killmonster,talk}*.txt`; `\settings\droprate\npcdroprate<level>.ini` (`g_npcdeath.lua:231`).
- `\settings\global\vdk\simcity\` (names/chat/pets/skills + maps\*) — `simcity\libs\data.lua:3,64-75,113`.

## Tồn đọng
1. Không thấy nơi include `activitysys\config\<id>\registe.lua` trong cây → danh sách activity có thể load từ file ngoài cây/bản trên VM khác — **grep trực tiếp trên VM khi làm phase 06**.
2. Lịch gọi `battles\battlemain.lua:main()` (giờ mở trận theo battleid) = engine + cấu hình battle ngoài script.
