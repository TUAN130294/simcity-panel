# Phase 03 — Liên đấu với bot, Y NHƯ GAME ONLINE (kích hoạt lại WLLS)

## Overview
- **Ưu tiên:** P2 | **Độ khó:** Cao | **Thời lượng:** ~4-6 ngày | **Phụ thuộc:** phase 00
- **Quyết định user (2026-07-18): làm y game online VNG.** → Không xây mới: **kích hoạt lại hệ Võ Lâm Liên Đấu (WLLS) có sẵn** trong `missions/leaguematch/` — NPC, 16 map chuyên dụng, mission 24/25/26, luật trận, thưởng exp/vinh dự/uy danh/danh hiệu, shop vinh dự đều còn nguyên và ĐÃ đăng ký trong settings. Chỉ thiếu "control plane" (vốn nằm trên S3Relay liên server) → viết bản **relay giả lập local** ~500-700 dòng + chèn bot SimCity làm đối thủ khi thiếu người.
- **MUST READ trước khi code:** `research/06-lien-dau-wlls.md` (toàn bộ file:line + luồng), `research/01` mục 8 (máy duel bot).

## Key insights (tóm tắt từ research/06)
- WLLS "chết lâm sàng": `CFG_LienDau=1` nên NPC Sứ Giả Liên Đấu ĐANG spawn ở 4 thành, nhưng `GLB_WLLS_NEXT=0` → NPC báo "Tính năng chưa được mở". Nguyên nhân: toàn bộ lịch mùa/đội/hạng nằm trên S3Relay với 3 script `league.lua/joinmatch.lua/log.lua` không tồn tại.
- Máy trạng thái trận chạy local 100%: phase 4 (báo danh 4') → ghép cặp theo winrate + tránh gặp lại (`wlls_buildup_vs`) → phase 5 đấu 10' trên map 397/541 (SetPKFlag(2), đếm damage tie-break) → thưởng exp/uy danh/vinh dự → phase 3.
- 7 loại giải (`macthtype/`): đề xuất chạy **loại 5 Đơn đấu tự do (1 người/đội)** trước — hợp server ít người + dễ chèn bot; sau đó loại 4 Tam đấu 3v3.
- Bug có sẵn phải sửa: `GetnGroup` hard-code SubWorld index (`wlls_gmscript.lua:3-24`) → đổi sang `SubWorldID2Idx`.
- ⚠️ Bot đối thủ dùng máy **SimCitizen hiện hành** (spawn theo camp như `pchientranh taoNV`), KHÔNG dùng `GroupFighter` (legacy không nạp — báo cáo gốc của agent đề xuất sai, đã hiệu đính trong research/06 mục 5).

## Architecture — 4 module mới trong `missions/leaguematch/local/`
1. **`league_store.lua`** — DB đội local: `tbWLLSLeague[name] = {members, task[1..17], memtask}`, persist file latin-1 (io.open). Wrapper `WLLS_LG_GetLeagueObjByRole/_GetLeagueTask/_ApplyAppendLeagueTask/...` cùng chữ ký hàm relay; đổi call-site CHỈ trong thư mục leaguematch (~40 chỗ, KHÔNG override `LG_*` toàn cục vì gb_taskfuncs còn dùng).
2. **`scheduler.lua`** — thay relay bấm phase: timer local theo giờ thật (panel chỉnh): 19h00 `wlls_setphase(sid, 5, 4, mid+1, 5, {1,1})`, chu kỳ ~15'/trận (4' báo danh + 10' đấu + nghỉ), 20h00 → phase 2; chủ nhật cuối tháng → phase 1 (kết mùa) + tính rank + sid+1.
3. **Join local** — `npc/signup.lua:108` `wlls_en3` gọi thẳng `wlls_player_join(GetName(), n_mtype, n_group, 0)`; các `LG_ApplyDoScript → joinmatch/log` thành no-op/ghi log file (4 call-site: `schedule/newworld.lua:52`, `glbmission/schedule.lua:285`, `head.lua:861`, `wlls_gmscript.lua:166,190`).
4. **`rank.lua`** — kết mùa: sort store theo (point, winrate, time) → task[RANK]; `wlls_query_top10` (`npc/head.lua:61`) đọc top-10 từ store thay `Ladder_GetLadderInfo`.

### Bot lấp chỗ (điểm chèn trong research/06 mục 5)
- `glbmission/schedule.lua:237-254`: đội LẺ hoặc chỉ 1 đội báo danh → thay auto-thắng bằng spawn N bot SimCitizen camp ngược tại tọa độ cặp (champion_gmpos.txt), N = số người đội player; đội bot có league giả trong store ("Kim Binh Doanh"...) để ghi điểm/BXH như đội thật.
- `combat/mission.lua` EndMission/OnLeave: camp bot → phân định theo số bot sống (đếm fighterList) vs `GetMSPlayerCount(25, camp)`; dọn bot khi trận kết thúc.
- Độ mạnh bot theo hạng giải: level/HP/atkspeed cấu hình panel; ép hung hãn qua `duelPlayerId` (máy `SimDuelMove`).

## Related files
- Tạo: `missions/leaguematch/local/{league_store,scheduler,rank}.lua`, cấu hình `SET/global/vdk/liendau/config.txt`.
- Sửa: `missions/leaguematch/npc/signup.lua` (join local), `npc/officer.lua` (bỏ đường relay tạo đội → league_store), `npc/head.lua` (top10), `glbmission/schedule.lua` (bot lấp chỗ), `combat/mission.lua` (phân định bot), `wlls_gmscript.lua` (GetnGroup fix + no-op relay), `head.lua` (:861 no-op log), `global/login.lua`/`wlls_login.lua:48` (bật lại login_add nếu cần bù điểm offline), `maps/worldset.ini` (bảo đảm map 396-411/540-555/560-577 được load — kiểm tra, hiện worldset có 139 map), panel catalog.
- KHÔNG sửa: máy trận mission 24/25/26, timer 50/51, luật trận, thưởng — giữ nguyên để "y game online".

## Implementation steps
1. **Khảo sát VM trước** (blocker check): (a) S3Relay có chạy không, `LG_*` khi relay chết trả gì (test lab: gọi `LG_GetLeagueTask` in kết quả — nếu TREO thì mọi call-site phải thay wrapper, nếu trả 0 thì thay dần); (b) diff `head.lua.bak` + `schedule/newworld.lua.bak` — người trước từng mod dở "offline mode", tránh đè công; (c) map 396-411/540-555/560-577 có trong worldset.ini không.
2. `league_store.lua` + wrapper + persist; đổi call-site trong leaguematch.
3. Join local + no-op relay calls; fix `GetnGroup`.
4. `scheduler.lua` (giờ mở panel chỉnh) → chạy trọn 1 trận người-vs-người: đăng ký đội tại NPC → 19h báo danh → ghép → đấu 10' → thưởng đúng (exp/uy danh/vinh dự/task 2500-2501).
5. Bot lấp chỗ: spawn/phân định/dọn; league giả cho bot; độ mạnh theo config.
6. `rank.lua` kết mùa + danh hiệu top-4 + shop vinh dự (`Sale(146,11)` — verify shop 146 tồn tại trong settings shop).
7. Panel: tab Liên Đấu — giờ mở, loại giải, số trận/ngày, độ mạnh bot, xem BXH/store.
8. Test: 1 người + bot (đơn đấu); 2 người thật; đội lẻ 3 đội; rớt mạng giữa trận; kết mùa nhận thưởng hạng; client hiển thị bảng thành tích (task 1715-1732/2500/2501) — nếu client SHXT không render thì hiển thị qua NPC dialog.

## Todo
- [ ] Check S3Relay + hành vi LG_* + diff .bak + worldset maps
- [ ] league_store + wrapper + đổi call-site
- [ ] Join local + no-op relay + fix GetnGroup
- [ ] scheduler + chạy trọn trận người thật
- [ ] Bot lấp chỗ + league giả + độ mạnh config
- [ ] rank kết mùa + danh hiệu + shop vinh dự
- [ ] Panel tab Liên Đấu
- [ ] Test 6 ca

## Success criteria
- Trải nghiệm y VNG: đăng ký đội tại Sứ Giả Liên Đấu → khung giờ tối tự mở trận → báo danh 4' → ghép cặp → đấu 10' map liên đấu → điểm/hạng/vinh dự/danh hiệu mùa giải; server vắng vẫn có trận nhờ bot lấp chỗ; BXH top-10 xem tại NPC.

## Risks
- `LG_*` treo khi không có relay → GS đơ: bước 1 phải test trước trong lab, có kill-switch `CFG_LienDau=0`.
- Map liên đấu chưa load trong worldset → SubWorldID2Idx=-1: check + thêm map cần thiết (phối hợp phase 08).
- Sửa nhiều file gốc WLLS: snapshot từng file, giữ diff tối thiểu, mọi no-op có comment đánh dấu `-- [LOCAL-RELAY]` để trace.
- Client cũ không render UI thành tích: fallback NPC dialog + Msg2Player.
