# Research 02 — Bề mặt API Lua của engine (đầy đủ file:line)

> Rà 2026-07-18. BASE mọi `file:line` = `/home/jxser/server1/script`. Quy ước engine: script chạy trong ngữ cảnh ngầm `PlayerIndex` / `SubWorld` (biến global — đổi giá trị = đổi người chơi/map hiện tại); 18 frame = 1 giây (`FRAME2TIME = 18` tại `missions\challenge\challengehead.lua:19`); tọa độ lưới = pixel/32.

## 1. TELEPORT

| Hàm | Chữ ký | Ghi chú |
|---|---|---|
| `NewWorld(mapid, x, y)` | mapid = ID map (không phải index), x,y = lưới (pixel/32) | Hàm chính |
| `SetPos(x, y)` | lưới, map hiện tại | `gmscript.lua:457` `SetPos(47584/32, 106880/32)` |
| `GetPos()` | trả x,y lưới | `gmscript.lua:417-420` hàm `SPos()` |
| `GetWorldPos()` | trả `w, x, y` | `gmscript.lua:444-447` `ShowWorldPos()` trả chuỗi `"NewWorld(w,x,y)"` dùng lại được |
| `SubWorldID2Idx(id)` / `SubWorldIdx2ID(idx)` | ID↔index; index <0 = map không load | `battles\singlefight\gofight_dt.lua:21,34` |
| `SetRevPos(revid,...)` / `SetTempRevPos` / `GetPlayerRev()` / `RevID2WXY(nMapId,nRevId)` | điểm hồi sinh | `lib\player.lua:654-668`, `missions\challenge\challengehead.lua:47` |

- `gmscript.lua:311` — `NewWorld(2,2350,3493)`; `gmscript.lua:408` — `NewWorld(worldindex, PosX/32, PosY/32)` (xác nhận đơn vị /32).
- Wrapper OOP: `lib\player.lua:329-331` `Player:NewWorld(mapid,x,y)` qua `CallPlayerFunction`.
- Trap teleport mẫu: file trap chỉ cần `function main(sel) SetFightState(1); NewWorld(80, 1956, 2829) end` (vd `ÖÐԭÄÏÇø\ؤ°ï\ؤ°ï\trap\ؤ°ïtoÑïÖÝ.lua`).
- Teleport NGƯỜI KHÁC: đổi `PlayerIndex = pindex` rồi `NewWorld` (mẫu chuẩn `battles\singlefight\gofight_dt.lua:79-128` `dt_EnterMap`), hoặc `CallPlayerFunction(nPlayerIndex, NewWorld, mapid, x, y)`.

## 2. PK / TRẠNG THÁI CHIẾN ĐẤU

- `SetFightState(0|1)` / `GetFightState()` — 1 = có thể bị đánh. Trap chuyển đổi: `ÖÐԭÄÏÇø\ؤ°ï\ؤ°ï\trap\ؤ°ïÇл»µã1.lua:7-12`.
- `SetPKFlag(0|1)` — chế độ PK. `battles\guozhan\hometrap1.lua:22-23` (đi cặp SetFightState(1)+SetPKFlag(1)); kết thúc trận cả 2 về 0: `battles\battlehead.lua:966-969`.
- `SetPunish(0|1)` / `GetPunish()` — hình phạt PK (điểm sát nhân). Map chiến trường tắt: `battles\guozhan\head.lua:388,464`; rời trận bật lại: `missions\challenge\challengehead.lua:48` (comment "恢复PK惩罚"). Không có hàm Lua đọc/ghi PKValue trực tiếp — engine tự quản khi giết lúc `GetPunish()==1`.
- `ForbidChangePK(0|1)`, `ForbidEnmity(0|1)`, `GetForbidEnmity()` — `maps\newworldscript_h.lua:29-39` (`CD_ForbidEnemy`), `lib\player.lua:365-371`.
- Camp: `SetCurCamp(n)/GetCurCamp()`, `GetCamp()`, `SetTmpCamp/GetTmpCamp` (`lib\player.lua:317-323`, `gmscript.lua:453`).
- Script chết: `SetDeathScript("\\script\\...\\death.lua")` — `gmscript.lua:456`, `gofight_dt.lua:127`.
- **Duel/solo sẵn có**: `battles\singlefight\` = hệ 1v1 hoàn chỉnh: `gofight_dt.lua:2` `BT2DTFight(orgmissionid, Player1, Player2)` — cấp map đấu qua ini `Area_SingleFight`, đưa 2 người vào, SetPKFlag(1), timer 3 phút (`dt_smalltimer.lua`, `dt_timerend.lua`, `dt_death.lua`). Ngoài ra `missions\challenge\` (khiêu chiến 5v5 2 đội, cần chiến thư — `Player:GetTiaozhanlingCount()` `lib\player.lua:397-415`), `missions\bairenleitai\` (lôi đài trăm người, bảng tọa độ đài `head.lua:10-30`), `missions\new_qiecuo\` (`qiecuo_manager.lua` RỖNG — chưa kích hoạt).

## 3. TRADE

- **KHÔNG có API Lua mở cửa sổ giao dịch 2 người.** Chỉ có:
  - `ForbitTrade(0|1)` — cấm/cho trade (đúng chính tả "Forbit"): `missions\yandibaozang\readymap\include.lua:114,268`; `missions\tong\tong_springfestival\head.lua:238`.
  - `DisabledStall(flag)` / `IsDisabledStall()` — cấm bày bán: `lib\player.lua:646-652`.
  - 2 hàm C vdk.so (chỉ simcity dùng, guard `if Fn then`): `PollTradeStay(npcIndex)`, `SendTradeItem(npcIndex)` — `global\nobitaxd\vdk\simcity\components\sim.core.lua:860,866`.
- Trao đồ/tiền từ script:
  - `AddItem(genre, detail, particular, level, series, luck[, extra])` → itemIndex: `bonus_onlinetime\func_onlineaward.lua:153` `AddItem(6,2,1020,0,1,0,0)`; `baoruongthanbi\key\keyupgrade.lua:121` `AddItem(6,1,30037,1,0,0)`.
  - `AddEventItem(id)`: `gmscript.lua:310`, `global\christmas.lua:95`. `GetItemCountEx(id)`: `global\cn\gamebank_proc.lua:166`.
  - Tiền: `Earn(money)` (`newscript\gmtool.lua:44` `Earn(10000000)`), `Pay(money)`, `GetCash()` (`lib\player.lua:389-395`).
  - Khác: `AddItemIntoEquipmentBox`, `ConsumeEquiproomItem`, `CalcEquiproomItemCount(genre,detail,particular,level)`, `CalcFreeItemCellCount()` (`lib\player.lua:268-278,571-578`); hệ thưởng `tbAwardTemplet:GiveAwardByList({tbProp={6,1,2351,1,0,0},...}, szLogTitle)` (`missions\yandibaozang\npc\yandituteng.lua:107`).

## 4. LIÊN ĐẤU / ĐẤU TRƯỜNG

- **WLLS (Võ Lâm Liên Đấu liên server)**: `missions\leaguematch\` — `head.lua` (GLB_WLLS_PHASE/SID/MATCHID..., LG task point/rank/win), `wlls_login.lua`, `wlls_autoexec.lua`, `wlls_gmscript.lua:208` (`NewWorld(n_mapid, WLLS_MAPPOS_PRE[...])`), thư mục con `combat/`, `glbmission/`, `macthtype/`, `schedule/`, `npc/`. Lib `IL("LEAGUE")`, `IL("RELAYLADDER")`; API `LG_GetMemberTask(538,...)`/`LG_ApplyAppendMemberTask` (`lib\player.lua:402,413`). → Chi tiết sâu hơn: research/06-lien-dau-wlls.md.
- **Arena instance**: `missions\arena\` — OOP dungeon: `rule.lua:11` `Dungeon:new_type("arena")`, map template 975, FIGHT_TIME 5 phút, 2 camp, cấm item CALLNPC/TRANSFER, tự spawn NPC rương/dược điếm; `cmd.lua` dùng `RemoteExecute(script, fn, handle, callback)` + `ObjBuffer` (cross-server). Hạ tầng dungeon: `missions\basemission\dungeon.lua`.
- **Bách nhân lôi đài**: `missions\bairenleitai\` (head.lua, trap_arena.lua, player_death.lua...).
- `battles\`: `guozhan` (quốc chiến), `seizegrain` (vận lương), `seizeflag` (cướp cờ), `jianta`, `boss`, `butcher`, `marshal`, `singlefight`; khung chung `battlehead.lua`, `battlemain.lua`, `battlejoin*.lua`.
- Mission API: `OpenMission(id)`, `RunMission(id)`, `SetMissionV/GetMissionV`, `SetMissionS`, `AddMSPlayer(missionid, camp)`, `GetMSPlayerCount(missionid, camp)`, `Msg2MSAll(missionid, str)` — đủ tại `battles\singlefight\gofight_dt.lua:43-152`.

## 5. TỔ ĐỘI

- `GetTeamSize()` → n; `GetTeamMember(i)` → playerIndex (i = 1..size, GỒM CẢ bản thân); `IsCaptain()` → 0/1; `LeaveTeam()`; `SetCreateTeam(0|1)`; `GetTeam()` → teamId.
- Ví dụ: `eventthanglong1000\box\openbox.lua:6-29` (duyệt đội chia thưởng); `activitysys\g_npcdeath.lua:58-61`; `maps\newworldscript_h.lua:41-48` (`forbidCreateTeam`: vào map → LeaveTeam + SetCreateTeam(0)); `activitysys\npctimer.lua:18` `GetTeamSize(nTeamId)` (biến thể nhận teamId).
- Helper: `getTeamInfo(playerIndex, baseInfo, task, tasktmp)` và `traversalTeam(...)` — `lib\player.lua:53-82`.

## 6. TASK / DIALOG NPC

- `Say(szText, nOptCount, "opt1/fn1", ...)`; `Say(str, 0)` = chỉ text: `bonus_onlinetime\func_onlineaward.lua:67`.
- `Talk(nCount, "szCallback", str1[,str2...])` — nhiều trang, callback khi OK ("" = không): `award_start_tk\head.lua:46`, `gofight_dt.lua:119`.
- `CreateTaskSay(tbOpt)` — phần tử 1 = title, tiếp theo `"Nhãn/HàmCallback"` hoặc `"Nhãn/#Hàm(param)"`: mẫu `bonus_onlinetime\func_onlineaward.lua:48-59`.
- `Describe(szText, nOptCount, tbOptions)` — bản table: `lib\say.lua:34` (helper phân trang `__saypage`).
- `AskClientForString("cbFn", szDefault, nMinLen, nMaxLen, szTitle)` / `AskClientForNumber("cbFn", nDefault, nMax, szTitle)`; wrapper chống đè state: `dailogsys\dailogsay.lua:63-100` (`g_AskClientStringEx`, `g_AskClientNumberEx`).
- Cú pháp option: `"text/FuncName"` không tham số; `"text/#FuncName(1)"` kèm tham số — `missions\yandibaozang\npc\yandituteng.lua:43-44`.
- `Sale(nId[, nCurrencyType, nScale])` mở shop; `OpenProgressBar(...)`; tag `<color=red>`, `<enter>` (`gofight_dt.lua:119`).
- Task var: `SetTask(id,v)/GetTask(id)`, `SetTaskTemp/GetTaskTemp` (mất khi logout) — vd `gmscript.lua:459-461`.

## 7. TIMER / HOOK

- `AddTimer(nFrames, "TênHàmToànCục", nParam)` → timerId; callback return >0 = chạy lại sau bấy nhiêu frame, 0 = dừng. `DelTimer(id)`, `SuspendTimer(id)`, `ResumeTimer(id)`. Vd: `global\npc\huoke.lua:48` `AddTimer(nNextTime*18, "CallHuoKeTime", 0)`; callback method `"tbYanhuaNpc:OnTime"` được (`global\npc\yanhua.lua:16`). Wrapper OOP: `lib\timerlist.lua:9-67` (`TimerList:AddTimer(timerObj, timeoutFrames, param)` → `timerObj:OnTime(param, index)`).
- Hook file cố định:
  - Login: `global\login.lua` — cơ chế `login_add(fun, n_time)` đăng ký việc lúc login (mẫu `missions\leaguematch\wlls_login.lua`).
  - Logout: `global\logout.lua:18` `function main()` chạy trước thoát.
  - Boot: `global\autoexec.lua` — spawn NPC toàn cục, include `*_autoexec.lua`; `:549-551` `G_ACTIVITY:LoadActivitys(); G_TASK:LoadAllConfig(); G_ACTIVITY:OnMessage("ServerStart")`.
  - Vào/rời map: script map khai `OnNewWorld(szParam)` / `OnLeaveWorld(szParam)` — `changefeature\maps.lua:2-11`; header per-map `maps\newworldscript_h.lua` bảng `aryFuncStore["CreateTeam_OFF"] = forbidCreateTeam` (dòng 209) bật/tắt tính năng từng map.
  - Chết: `SetDeathScript(path)` per-player; NPC chết: script `npcdeath.lua` (`battles\seizegrain\npcdeath.lua:80`); global: `gamesetting.ini [SYSTEM] GlobalNpcDeathScript=\script\activitysys\g_npcdeath.lua`.
  - Trap: file lua có `function main(sel)` chạy khi đạp.
- Cross-context: `CallPlayerFunction(pid, fn, ...)` (`lib\player.lua:128-142`), `SearchPlayer(szName)` → playerIndex (`lib\player.lua:191`), `RemoteExecute(script, fn, handle, cb)` + `ObjBuffer` cross-server (`missions\arena\cmd.lua:9`), `PIdx2NpcIdx(playerIndex)` (`lib\player.lua:512`).
- Thông báo: `Msg2Player(str)`, `Msg2SubWorld(str)` (cả map hiện tại — `gmscript.lua:403`; lưu ý một số nơi dùng như toàn server), `Msg2Map(worldId, str)`, `Msg2MSAll(missionid, str)` (`dt_smalltimer.lua:9`).

## Tồn đọng
- Chữ ký chính xác `PollTradeStay`/`SendTradeItem` mới suy được 1 tham số (npcIndex) — cần source vdk.so.
- `AddItem` tham số 7 (thấy cả 6 và 7 args) — nghi bind-flag, chưa xác minh.
- `missions\new_qiecuo\qiecuo_manager.lua` rỗng — hệ thí võ chưa kích hoạt.
