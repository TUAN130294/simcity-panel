# Research 06 — Võ Lâm Liên Đấu (WLLS / missions/leaguematch) — đầy đủ file:line

> Rà 2026-07-18, đọc trọn `missions\leaguematch\` (5.651 dòng) + lib + settings. Gốc: `script\` và `settings\` trên VM.
> ⚠️ Hiệu đính bởi controller: mục 5 báo cáo gốc đề xuất dùng `GroupFighter` — SAI, `simcity/class/group_fighter.*` là LEGACY KHÔNG NẠP (xem research/01 mục "Kiến trúc tổng thể"). Bot tham chiến phải dùng máy SimCitizen hiện hành (đã sửa trong mục 5).

## 1. Luồng đầy đủ

### 1.1 Kiến trúc 2 nửa GS + Relay
- **Game Server (GS)**: NPC, map, mission thi đấu, luật trận, phát thưởng.
- **Relay (S3Relay)**: control plane — DB chiến đội, lịch mùa/trận, trọng tài vào trận, xếp hạng. GS gọi relay qua `LG_ApplyDoScript(...)` trỏ 3 script CHỈ có trên relay: `\script\leaguematch\league.lua`, `joinmatch.lua`, `log.lua` — **cả 3 KHÔNG tồn tại trong cây script GS** (grep toàn cây chỉ thấy call-site).

### 1.2 Global value & phase (`missions\leaguematch\head.lua:27-34`)
| GLB | ID | Ý nghĩa |
|---|---|---|
| GLB_WLLS_PHASE | 820 | Giai đoạn |
| GLB_WLLS_SID | 821 | Season id |
| GLB_WLLS_MATCHID | 822 | Trận hiện tại (hiển thị `mod(mid,100)`) |
| GLB_WLLS_TYPE | 823 | Loại giải mùa này (1-7) |
| GLB_WLLS_NEXT | 824 | Loại giải mùa sau (= loại đang mở đăng ký) |
| GLB_WLLS_TIME | 825 | Bộ đếm tick timer |
| GLB_WLLS_CLOSE | 826 | Bit tắt giải sơ/cao cấp |

PHASE (suy từ `wlls_gmscript.lua:112-173`, `glbmission\combat.lua:9`, `npc\signup.lua:26-58`, `npc\officer.lua:104`):
- **1** = nghỉ giữa mùa (nhận thưởng hạng/danh hiệu, rời/giải tán đội, SID sắp +1)
- **2** = trong mùa, chưa tới giờ trận
- **3** = nghỉ giữa 2 trận trong ngày (`glbmission\combat.lua:9`)
- **4** = mở báo danh trận (relay gửi matchid → mở mission chuẩn bị)
- **5** = đang thi đấu

Chuyển phase do relay gọi `wlls_setphase(sid, type, phase, matchid, next, tbOpen)` (`wlls_gmscript.lua:69`); GS chỉ tự chuyển 4→5→3 bằng timer nội bộ.

### 1.3 Đăng ký đội
- NPC "Sứ Giả Liên Đấu" (NpcID 308, script `npc\officer.lua`) spawn tại map 80 (1753,3035), 162 (1599,3150), 1 (1673,3219), 11 (3214,5149); nhánh "Kiệt xuất" 176/37/78 (`wlls_autoexec.lua:4-8`). NPC 87 (`npc\helper.lua`) = sổ tìm đồng đội (LGTYPE 2 `WLLS_REG_LGTYPE`, `head.lua:116`).
- Lập đội: `wlls_createleague` (`npc\officer.lua:311-363`) → `LG_ApplyDoScript(WLLS_LGTYPE=5, ..., "league.lua", "wlls_create")` — đội nằm TRÊN RELAY.
- Thêm thành viên: đội trưởng lập party rồi "đăng ký đội viên" (`wlls_want2addmember`/`wlls_checkteam`, `officer.lua:367-464`) → relay `wlls_add`.
- Số người/đội theo loại (`macthtype\*.lua`, key `max_member`): 1 Song đấu=2, 2 Môn phái=1, 3 Sư đồ=2, 4 Tam đấu=3, **5 Đơn đấu tự do=1**, 6 Song đấu cộng hưởng=2, 7 Nam-nữ=2. Đăng ký vào WLLS_TAB qua `wllstab_additem` (`tb_head.lua`, include `head.lua:323-338`).
- Cấp: sơ 80-119, cao 120+ (`WLLS_LEVEL_JUNIOR/SENIOR` `head.lua:118-119`); bản mod phân bằng `GetLevel()<120` (`officer.lua:252-259,528-533`) và ÉP `n_group=1` (`officer.lua:534`).
- League Task (relay): MTYPE/POINT/RANK/WIN/TIE/TOTAL/TIME/EMY1-3 (`head.lua:37-62`).

### 1.4 Lịch
- Gốc VNG (`macthtype\normal.lua:62`): T2-T6 4 trận/ngày 19-20h; T7-CN 8 trận; mùa 108 trận, đội max 48 trận — bản mod BỎ giới hạn 48 (`head.lua:757-765`).
- Chuỗi 1 trận: relay `wlls_setphase(phase=4, matchid)` → `OpenGlbMission(26)` + `OpenMission(24)` tại map chuẩn bị (`wlls_gmscript.lua:139-168`) → `glbmission\mission.lua:3-9` chạy timer 50 (10s/tick).
- Báo danh 4 phút (`WLLS_TIMER_PREP_TOTAL=24` tick, `head.lua:108-109`): player nói "Quan viên hội trường" (`npc\signup.lua:94-109`) → relay `joinmatch.wlls_want2join` → relay gọi ngược `wlls_player_join` (`wlls_gmscript.lua:177-214`): check item cấm (`wlls_en_check` `head.lua:899-943`; danh sách `WLLS_FORBID_ITEM/STATES` `head.lua:144-277`), xóa buff cấm, dịch vào map chuẩn bị `WLLS_MAPPOS_PRE={1596,2977}` (`head.lua:124`) → `schedule\newworld.lua:4-46`: `AddMSPlayer(24, camp)` — mỗi đội 1 camp (max 200, `WLLS_MAX_COUNT` `head.lua:139`), đồng đội gom camp qua `wlls_findfriend`.

### 1.5 Ghép cặp
`glbmission\schedule.lua:OnTimer` hết 4 phút (:196-257):
- Gom camp có người (`wlls_get_ms_troop`) → **`wlls_buildup_vs`** (:20-108): điểm = (win×3+tie)/total, chia 10 rổ winrate, xáo trong 5 block, tránh gặp lại 3 đối thủ gần nhất (EMY1-3, `wlls_SaveMeetEmy` :13-17); **đội lẻ xử thắng không đấu** (:98-104, 249-252).
- Mở mission 25 trên map đấu, `wlls_addtroop_combat` (:168-186): cặp k đặt tại hàng k của `settings\maps\championship\champion_gmpos.txt` (load :4-7; điểm chạy chéo map: 1706,3109 / 1749,3154 / ...), camp MS = i, i+1, `SetCurCamp(mod(camp,2)+2)` (:148), gắn death script, bật đếm damage (`ST_StartDamageCounter`).

### 1.6 Map + luật trận
- Bộ 3 map/group `{hội trường, chuẩn bị, đấu trường}` — sơ cấp: {396,560,**397**} ... {410,567,**411**}; cao cấp: {540,570,**541**} ... {554,577,**555**} (`macthtype\single.lua:19-43`; loại khác trong từng `macthtype\*.lua`). Binding: `settings\maplist.ini:3369+` (combat→`combat\newworld.lua`), `:4096+` (prep→`schedule\newworld.lua`); mission 24/25/26: `settings\task\missions.txt:25-27`; timer 50/51: `settings\timertask.txt:51-52`.
- Timer 51 (5s/tick, `glbmission\combat.lua`): tick<2 chuẩn bị 10s; tick 2 → `RunMission(25)` → `combat\mission.lua:7-21`: `SetPKFlag(2)` (đồ sát), khóa đổi PK, `SetFightState(1)`; tick 120 = 10 phút → `CloseMission(25)`.
- Phân định (`combat\mission.lua:23-60` EndMission): còn nhiều người hơn thắng; bằng → so tổng damage NHẬN (`ST_GetDamageCounter`, ít hơn thắng); vẫn bằng → hòa. Chết (`combat\playerdeath.lua`): rời mission về hội trường. Phe hết người giữa trận → thắng ngay (`combat\mission.lua:62-137` OnLeave).
- Trạng thái thi đấu: cấm đổi camp/bày bán/trade/hồi thành/không mất điểm PK (`wlls_set_pl_state` `head.lua:569-592`).

### 1.7 Điểm/hạng/thưởng
- Điểm trận: `wlls_GetAddPoint = win*5*level + tie*2*level + 5` (`head.lua:1044-1046`, đã mod). Ghi đội qua `LG_ApplyAppendLeagueTask` (POINT/WIN/TIE/TOTAL/TIME); cá nhân: task 2500 (tích lũy) + **2501 (vinh dự)** (`wlls_award_pl` `head.lua:682-695`); offline bù khi login `LG_GetMemberTask` (`wlls_login.lua:27-36`).
- Mỗi trận: EXP (thắng 1tr + buff 451, hòa 800k, thua 500k — `head.lua:355-383`), Uy danh 3/2/1 (`head.lua:768-820`); kết quả gửi relay log (`wlls_matchresult` `head.lua:835-863`).
- Hạng: relay tính, lưu `WLLS_LGTASK_RANK` (task 5); top-10 đọc `Ladder_GetLadderInfo(ladder_id, i)` từ lib RELAYLADDER (`npc\head.lua:61-79`), ladder đơn đấu 10235/10236 (`single.lua:17,33`).
- Cuối mùa (PHASE=1): vinh dự theo `award_rank` (hạng 1: 4000 ... 65-128: 150, `single.lua:47-73`) qua `wlls_getaward_rank` (`officer.lua:212-248`); danh hiệu top-4 20 ngày (`Title_AddTitle`, `officer.lua:154-209`, bảng title `head.lua:280-292`). Shop vinh dự `Sale(146,11)` (`officer.lua:617-643`).

## 2. Phụ thuộc liên server
- `IL("LEAGUE")`/`IL("RELAYLADDER")` = IncludeLib lib C++ trong binary (không phải Lua; các lib khác cùng kiểu: `lib\gb_taskfuncs.lua:10`, `lib\player.lua:4`, `lib\alonelib.lua:3`). LEAGUE cấp `LG_*`, RELAYLADDER cấp `Ladder_*` — dữ liệu vật lý trên S3Relay.
- PHẢI thay khi standalone: (1) DB đội — ~40 call-site `LG_*` trong leaguematch; (2) 3 script relay thiếu; (3) scheduler mùa/trận (không ai gọi `wlls_setphase` → hệ đứng im); (4) rank/ladder cuối mùa.
- Chạy local 100%: máy trạng thái trận — mission 24/25/26, timer 50/51, `wlls_buildup_vs`, luật trận, đếm damage, thưởng, NPC, map.
- `RemoteExecute/ObjBuffer` không được WLLS dùng.

## 3. Hiện trạng kích hoạt — "chết lâm sàng"
- `global\autoexec.lua:14` include `wlls_autoexec.lua`; `:473` gọi `wlls_autoexe()` khi `CFG_LienDau==1` — **đang =1** (`global\nobitaxd\config\cfg_server.lua:60`) → NPC ĐÃ spawn.
- `gmscript.lua:7` include `wlls_gmscript.lua` → `wlls_setphase` sẵn sàng.
- `global\login.lua:16` include `wlls_login.lua` nhưng `login_add(wlls_login, 2)` BỊ COMMENT (`wlls_login.lua:48`).
- `NPCVoLamLienDau=1` (`cfg_server.lua:61`) nhưng `GLB_WLLS_NEXT=0` → NPC trả lời "Tính năng chưa được mở" (`npc\officer.lua:12-16`).
- Settings ĐẦY ĐỦ: maplist bindings, missions.txt, timertask.txt, champion_gmpos.txt, item vinh dự (`settings\item\004\magicscript.txt:1262+`).
- Thiếu: nguồn gọi wlls_setphase định kỳ; backend league; trọng tài join; rank/ladder. **Bug tiềm ẩn:** `GetnGroup` hard-code SubWorld INDEX 506-513/516-523 (`wlls_gmscript.lua:3-24`) thay vì `SubWorldID2Idx(mapid)` — phải sửa.

## 4. So sánh & kiến trúc đề xuất
- `missions\challenge\` = trận camp tự do GM mở (map 209-211); `battles\singlefight\` = 1v1 nội bộ TK — cả 2 KHÔNG có đội/lịch/mùa/điểm/BXH → xây mới = viết lại gần hết.
- **Chọn: giữ WLLS + viết "relay giả lập local" (~500-700 dòng, 4 module):**
  1. `local\league_store.lua`: `tbWLLSLeague[name]={members={},task={1..17},memtask={}}`, persist file (io latin-1). Wrapper `WLLS_LG_*` cùng chữ ký, đổi call-site CHỈ trong thư mục leaguematch (không override built-in toàn cục — `gb_taskfuncs` và event khác cũng dùng `LG_*`).
  2. `local\scheduler.lua`: timer local theo giờ thật — 19h00 `wlls_setphase(sid, type, 4, mid+1, type, {1,1})` (đề xuất loại 5 Đơn đấu tự do max_member=1 — hợp server ít người + bot; hoặc loại 4 Tam đấu 3v3); chu kỳ ~15'/trận (4' báo danh + 10' đấu); 20h00 phase 2; chủ nhật cuối tháng phase 1 + tính rank + sid+1.
  3. Join local: `npc\signup.lua:108` `wlls_en3` → gọi thẳng `wlls_player_join(GetName(), n_mtype, n_group, 0)`; các `LG_ApplyDoScript → joinmatch/log` → no-op/WriteLog (`schedule\newworld.lua:52`, `glbmission\schedule.lua:285`, `head.lua:861`, `wlls_gmscript.lua:166,190`).
  4. Rank local: chuyển phase 1 → sort store theo (point, winrate, time) → `task[RANK]`; `wlls_query_top10` (`npc\head.lua:61`) → đọc top-10 từ store.
  5. Sửa `GetnGroup` dùng `SubWorldID2Idx` với map 560-567/570-577.

## 5. Bot tham chiến (ĐÃ HIỆU ĐÍNH — không dùng GroupFighter legacy)
- WLLS đặt player camp 2/3 (`SetCurCamp(mod(camp,2)+2)`, `glbmission\schedule.lua:148`) + `SetFightState(1)` khi trận bắt đầu → NPC camp ngược tự đánh.
- **Spawn bot bằng máy SimCitizen hiện hành** (KHÔNG dùng `GroupFighter:New` — legacy không nạp): mẫu spawn bot chiến đấu theo camp là `pchientranh.lua taoNV:115` (bot `mode="chiendau"` + camp chỉ định) hoặc `SimCitizen:New` trực tiếp với opts `{camp=<camp ngược>, hardsetName=..., noRevive=1}` như `pthanhthi createNpcSoCapByMap:497` — bot trong `fighterList` sẽ tự vệ/đánh player khác camp (`sim.movement.lua IsActive:15-52`, `TriggerFightWithPlayer`); ép hung hãn bằng set `duelPlayerId` = đối thủ (máy duel `SimDuelMove sim.core.lua:464-604`).
- Điểm chèn:
  1. `glbmission\schedule.lua:237-254` — sau `wlls_buildup_vs`: đội LẺ (hiện auto-thắng :249-252) hoặc CHỈ 1 đội báo danh → gán `WLLS_BOTMATCH[campMS]=nListId`, spawn N bot SimCitizen tại tọa độ cặp (`wlls_GetPosFileData` :9-11 đọc champion_gmpos.txt), camp ngược, số bot = số người đội player.
  2. `combat\mission.lua` EndMission (:23) + OnLeave (:62): camp đối là bot → thắng/thua theo số bot còn sống (đếm `fighterList` filter map + camp, `isDead==0`) so `GetMSPlayerCount(25, camp)`; đội bot có league giả trong store (vd "Kim Binh Doanh") để `wlls_matchresult` ghi điểm bình thường.
  3. Dọn bot trong EndMission + `wlls_remove_camp`: `Remove` từng bot khỏi fighterList (mẫu `SimCityChienTranh:removeAll` — `vdk/main.lua simcity_clearTongKim`).
- Map trận thực tế (group ép =1): **397** (sơ cấp) và **541** (cao cấp); dải đủ 397-411 lẻ, 541-555 lẻ (`macthtype\single.lua:19-43`), binding `settings\maplist.ini:3368-3370, 4001+`.

## Tồn đọng
1. VM có chạy S3Relay không? `LG_*` khi relay chết trả 0 hay TREO? — test trên VM trước khi quyết giữ `LG_*` hay thay wrapper hoàn toàn.
2. `head.lua.bak` + `schedule\newworld.lua.bak` — có người từng mod dở "chế độ offline": DIFF .bak trước khi sửa.
3. Client SHXT còn render UI bảng thành tích liên đấu (task 1715-1732/2500/2501)? — cần xác nhận in-game.
