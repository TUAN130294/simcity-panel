# Research 04 — Giả lập người chơi thật & hội thoại có ngữ cảnh (đầy đủ file:line)

> Rà 2026-07-18. Gốc `/home/jxser/server1/script`; `simcity/` = `global/nobitaxd/vdk/simcity/`.
> Phát hiện chi phối: engine `jx_linux` vá C rất sâu qua `vdk.so` (48 export, xem research-findings.md mục 2) — grep `function HasPlayerSay|PollSayForBot|PollDuel|PollParty|NpcChat|SetNpcBang` = 0 kết quả Lua → toàn hàm C. Mọi giới hạn "Lua không làm được" đều có tiền lệ giải bằng vá C.

## Câu 1: Giả lập "người chơi thật" từ dữ liệu nhân vật

### 1.1 Mức "hoá trang" hiện tại (đã rất cao)

| Yếu tố | Cơ chế | File:line |
|---|---|---|
| Tên riêng | `AddNpcEx(..., name, 0)`; pool 604 tên VN `pname.lua` + `names.txt` → `SimCityPlayerNames` | `simcity/components/sim.entity.lua:53-72`; `pname.lua:608-610`; `libs/data.lua:15-20`; `pnpcinfo.lua:454-456` |
| Cấp | spawn level + `SetNpcLevel(idx, SIMBOT_LEVEL)` | `sim.entity.lua:71-72,161`; `config.lua:102` |
| Ngoại trang nam/nữ | `ChangeNpcFeature(idx,0,0,gender,helm,armor,weapon,horse)` — index từ `\settings\npcres_simple\*.txt`, có WL/BL; ngựa `SetNpcRideHorse` | `pngoaitrang.lua:130-143` (makeup), `:33-95` (đọc), `:102-127` (WL/BL) |
| Môn phái + skill thật | `SetBotFaction(idx,1..10)`; cast `NpcCastSkill/BotDoSkill` theo bảng phái + `skills.txt`; aura TL/VĐ/NM | `sim.entity.lua:114-118`; `class/sim_citizen.lua:237-304`; `libs/data.lua:316-368` |
| Vũ khí theo skill | `SetBotWeaponView` | `sim.entity.lua:120-124` |
| Danh hiệu + bang | `SetNpcTitle(idx, rank)`; `SetNpcBang(idx,"AnhEm-[Bang Chủ]")` — bang random `g_TK_BangNames` × chức vụ, 50% bot | `sim_citizen.lua:137-151` (bảng), `:179-188` (gán); `sim.core.lua:687-693` (bang bot kéo xe) |
| Bán sạp | `NpcSit` + `SetNpcStall(idx,1)`; tụ quanh Dã Tẩu (`daTauNodes`) | `sim.entity.lua:126-130`; `libs/data.lua:151-172` |
| Hành vi "người" | đi graph node, rớt tiền/item gần tiệm thuốc (`sim.fun.lua:38-66`), "uống thuốc" (`EnforceBotHp` `sim.core.lua:767-787`), lên/xuống ngựa khi đánh (`sim.core.lua:802-819`) | |
| Tương tác | tự vệ + đuổi (`sim.core.lua:723-762`); nhận solo (`PollDuel :939-954`); vào nhóm + theo (`PollParty/PartyRebind/SimPartyFollow :955-968,324-345`); chờ trade + TẶNG item + chat tạm biệt (`PollTradeStay/SendTradeItem :860-915`, 10 câu `:896`) | |
| BXH | `BotLadderAdd/BotLadderBroadcast`, `SetBotPoints` — client thấy như người thật | `sim_citizen.lua:153-213` |

### 1.2 API đọc dữ liệu người chơi
- Chỉ đọc được người ONLINE, trong ngữ cảnh player hoặc `CallPlayerFunction(nPlayerIndex, fn)`: `GetName/GetLevel` (`lib/player.lua:213-218`), `GetTong/GetTongName` (`lib/player.lua:304-310`, `activitysys/playerfunlib.lua:99,124`), `GetFaction/GetSeries/GetCamp` (`lib/player.lua:596`).
- KHÔNG có API đọc save offline/DB: grep `GetPlayerData|dbsync|GetGlobalValue|SetGlobalValue|.db"` toàn cây = 0. Save do bishop/goddess quản.
- Lua CÓ `io.open` + `os.execute` (tiền lệ `global/nobitaxd/vdk/tinhnang/taotrangbi.lua:1313-1322,1950-1959`). `TabFile_Load/GetTabFileData` chỉ đọc file settings tab (`pngoaitrang.lua:33`, `pnpcinfo.lua:285-286`).
- Trang bị thật: không đọc được từ Lua để suy ngoại hình; hệ `changefeature/equip_tryon.lua` chỉ đổi feature. Ngoại hình bot = npcres index (khác không gian dữ liệu trang bị người) → copy "bộ đồ thật" chỉ gần đúng (map tay hoặc vá C đọc feature player).

### 1.3 Kết luận
- **Đạt được:** đứng cạnh gần như không phân biệt — tên VN, bang+chức vụ, danh hiệu, ngoại trang/ngựa, skill đúng phái, chat, bán sạp, rớt tiền, nhận solo, vào nhóm theo, trade tặng đồ, có mặt BXH TK.
- **"Từ dữ liệu nhân vật đã tạo":** không load save trực tiếp. Đường khả thi: (a) lúc nhân vật online, Lua thu `GetName/GetLevel/GetFaction/GetTongName` ghi profile qua `io.open`; (b) nạp profile làm config bot (`hardsetName`, `faction`, `level`, `bangDisp`, gender/armor — các field bot ĐÃ hỗ trợ: `sim.entity.lua:67-71,114`, `sim_citizen.lua:184-187`). "Bot đội lốt nhân vật X" làm được ngay.
- **Giới hạn cứng (bot là NPC):** không trong danh sách bạn bè/whisper/tìm người; không hồ sơ trang bị khi click (bot kind 0, click = chọn mục tiêu; script bot = `sim.timer.lua` chỉ có OnDeath — trừ tiểu thiếp có menu); không gửi thư; không chat kênh bang/tổ đội thật; số online server không tăng. Vượt = vá C tiếp.

## Câu 2: Hội thoại có ngữ cảnh

### 2.1 Cơ chế hiện tại
- Phát ngẫu nhiên: `execChat` — xác suất `CHANCE_CHAT=10/1000` (`config.lua:57`), câu random `SimCityChat.general/.fighting`, phát `NpcChat(npcIdx,msg)` = bong bóng (comment `sim.fun.lua:13`: định hướng `CH_NEARBY`/`BotSayLocal` vào khung chat kênh gần — cần fix client DLL, tạm bong bóng).
- Nguồn thật: `settings/global/vdk/simcity/chat.txt` (2 cột, nạp `libs/data.lua:23-31`). `data.lua:5` gán đè `SimCityChat={}` SAU pchat.lua → dữ liệu pchat + `getChat/getChatFight` (`pchat.lua:126-131`) chết; chỉ legacy `group_fighter.class.lua:1553,1557` còn gọi (sẽ lỗi nếu chạy). **Thêm câu → sửa chat.txt.**

### 2.2 Hook bắt chat người chơi — CÓ TIỀN LỆ
- Không có hook Lua `OnChat/ChatMsg/TalkMsg` (grep = 0). Bản vá C có sẵn: `HasPlayerSay()` (có người nói gần bot?) + `PollSayForBot(npcIdx)` → category số (C phân loại keyword). Lua map `SIM_SAY_REPLY = {[0]="rep_chung",[1]="rep_ok",[2]="rep_no",[3]="rep_chao",[4]="rep_giaodich",[5]="rep_boss"}` → `NpcChat` câu random (`sim.fun.lua:3-17`).
- Bị chửi → queue `SimBotTaunt/SimBotTauntDrain` nhóm `rep_chui`, rate-limit 1-2s/câu, max 12 chờ (`sim.core.lua:282-305`).
- ⚠️ chat.txt thực tế có 21 category (solo/rep_solo/giaodich/hoatdong/tantinh/rep_camon/rep_cho/rep_tuchoi/rep_tuchoinhom/rep_vonhom/rep_nhomfull...) — C classifier trả nhiều mã hơn 6 mã Lua đang map. Cần dò mã (lab phase 00).

### 2.3 dailogsys/
Framework hộp thoại NPC chuẩn (5 file): `dailog.lua` — class `DailogClass` (title + options + callback); `dailogsay.lua` — `CreateNewSayEx(title, tbOpt)` lưu option theo PlayerIndex vào `G_PlayerDailogData`, render `TaskSay/Describe`, click → `g_DailogBack(nSelectId)` (:21-63); `g_dialog.lua` — registry dialog theo tên NPC. Là hội thoại MENU per-player có state (tiểu thiếp dùng: `ptieuthiep.lua:134-320`).

### 2.4 Kênh server → người chơi
| Kênh | Hàm | Ví dụ |
|---|---|---|
| Bong bóng NPC | `NpcChat(npcIdx,msg)` (C) | `sim.fun.lua:13,22,26`; `sim.core.lua:896` |
| Hệ thống 1 người | `Msg2Player(msg)` | `lib/awardtype/item.lua:103` |
| Cả map | `Msg2Map(worldId,msg)` | `sim_citizen.lua:332,367` |
| Toàn server | `Msg2SubWorld(msg)` | `gmscript.lua:195`; `taotrangbi.lua:267` |
| Menu | `Say/TaskSay/Describe` | `task/equipex/head.lua:80`; `dailogsys/dailogsay.lua:33-38` |

### 2.5 Sandbox: `io.open`/`os.execute` CÓ (`taotrangbi.lua:1313-1322`); `require`/luasocket KHÔNG (0 kết quả) — Lua 5.0 nhúng.

### 2.6 Ba phương án (tăng dần)
1. **FSM thuần Lua:** mở rộng chat.txt thành topic nhiều bước (`rep_chao_1/2/...`); `tbNpc.convState={cat,step,tick}` — cùng category trong N giây → câu bước kế. Không đụng C. Giới hạn: chỉ biết NHÓM keyword, không biết nguyên văn/ai nói.
2. **Vá nhẹ C:** nâng `PollSayForBot` trả thêm playerIdx + nguyên văn (hoặc thêm `PollSayText(npcIdx)`). Lua giữ hội thoại theo cặp (bot, player), xưng tên, nhớ 3-5 lượt, bảng rule keyword Việt chỉnh qua panel. Đúng mô hình C-làm-cầu/Lua-làm-logic của duel/party/trade.
3. **Cầu LLM:** Lua ghi `{botIdx, playerName, text}` vào file queue (vd `.../chatbridge/in.txt`), daemon Python trên VM đọc → LLM → `out.txt`; `pworld.lua ATick` (`:236`) poll + NpcChat. Trễ 1-3s chấp nhận được. Điều kiện: phương án 2 (cần nguyên văn). Chống nghẽn: rate-limit như SimBotTauntDrain.

## Tồn đọng
- (a) bảng keyword→category trong C — cần source vdk.so; (b) `NpcChat` bong bóng hay khung chat — test in-game; (c) mã category >5 chưa dò.
