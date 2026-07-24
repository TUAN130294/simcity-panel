# Phase 05 — Ngữ cảnh đối thoại giữa người chơi và bot

## Overview
- **Ưu tiên:** P2 | **Độ khó:** Vừa, chia 3 tầng độc lập | **Thời lượng:** tầng 1 ~1-2 ngày; tầng 2-3 phụ thuộc source vdk.so
- Hiện trạng: C phân loại keyword câu nói của người chơi (`PollSayForBot` → category số), Lua trả 1 câu random đúng nhóm. Mục tiêu: bot nhớ ngữ cảnh, đối đáp nhiều lượt, cá nhân hoá, tiến tới nối LLM.

## Key insights
- Đường ống có sẵn: `HasPlayerSay()` + `PollSayForBot(idx)` → map `SIM_SAY_REPLY` 0-5 (`sim.fun.lua:3-17`) → `NpcChat`. Nhưng **`funSys.Update` (nơi gọi execChat) hiện là DEAD CODE** — không được gọi từ `SimCore:OnTimer`; kênh sống duy nhất là hàng đợi taunt (`SimBotTauntDrain`).
- `chat.txt` có 21 category (nhiều hơn 6 mức Lua đang map): thêm sẵn `solo/rep_solo`, `giaodich`, `hoatdong`, `tantinh`, `rep_camon`, `rep_cho`, `rep_tuchoi(nhom)`, `rep_vonhom`, `rep_nhomfull` → C classifier nhận nhiều nhóm hơn, Lua chưa khai thác.
- `BotSayLocal` có trong vdk.so (chưa dùng ở Lua) — khả năng đưa lời bot vào khung chat kênh gần thay vì chỉ bong bóng; comment `sim.fun.lua:13` nói cần fix client DLL → PHẢI test (phase 00).
- Lua có `io.open`/`os.execute`, không socket → cầu ra ngoài = file queue; panel đã chạy trên máy Windows với SSH sẵn — daemon đặt ngay trên VM là gọn nhất.
- Giới hạn hiện tại của `PollSayForBot`: chỉ trả category, không trả playerIdx + nguyên văn → tầng 2 cần vá C.

## Architecture — 3 tầng
### Tầng 1 (Lua thuần): hồi sinh chat + FSM hội thoại theo nhóm
1. **Hồi sinh execChat:** gọi `funSys:Update()` (hoặc chuyển logic vào `SimCore:OnTimer` mỗi N tick, chỉ khi `movementSys:IsActive` — có người gần) — sửa đúng chỗ, giữ tần suất `CHANCE_CHAT`.
2. **Khai thác đủ 21 category:** mở rộng `SIM_SAY_REPLY` map hết các mã C trả về (dò mã bằng lab phase 00: nói các câu mẫu in-game, log category số).
3. **FSM ngữ cảnh per-bot:** `tbNpc.conv = {cat, step, expireTick}` — khi cùng category đến trong 15s, trả câu bước kế (`rep_chao_2`, `rep_chao_3`... thêm vào `chat.txt` theo quy ước `<cat>_<step>`), tạo hội thoại 2-4 lượt; hết hạn thì reset. Chống spam: cooldown per-bot 3-5s (tái dùng cấu trúc `SimBotTauntDrain`).
4. **Cá nhân hoá rẻ:** khi bot ở trạng thái duel/party/trade đã biết playerIdx → chèn tên người chơi (`CallPlayerFunction(pIdx, GetName)`) vào câu có placeholder `{ten}`.
5. Panel: tab Danh sách dữ liệu đã sửa được `chat.txt` (TCVN3) — bổ sung nhóm câu mới + hướng dẫn quy ước step.

### Tầng 2 (vá C) [CẦN SOURCE VDK.SO]
- Thêm export `PollSayText(npcIdx)` → `playerIdx, szText` (nguyên văn). Lua giữ hội thoại theo cặp (bot, player): nhớ 3-5 lượt, rule keyword tiếng Việt phong phú (bảng rule trong settings, panel chỉnh), xưng tên, nhớ chủ đề trước.

### Tầng 3 (LLM bridge): 
- Lua ghi `{botIdx, playerName, text}` vào `SET/global/vdk/chatbridge/in.txt`; daemon Python trên VM (systemd, gọi API LLM — hoặc forward về panel máy Windows) ghi `out.txt`; `pworld.lua ATick` poll 3s → `NpcChat/BotSayLocal`. Rate-limit như taunt queue; fallback tầng 1-2 khi daemon chết/timeout; lọc nội dung + độ dài trước khi phát.

## Related files
- Sửa: `SIM/components/sim.core.lua` (gọi lại funSys), `SIM/components/sim.fun.lua` (FSM + map category đủ), `SET/global/vdk/simcity/chat.txt` (nhóm câu mới), `SIM/plugins/pworld.lua` (poll bridge — tầng 3).
- Tạo (tầng 3): `vdk/chatbridge/bridge.lua`, daemon `/root/chatbridge/daemon.py`, systemd unit.
- Panel: hướng dẫn + editor nhóm câu (đã có list_service).

## Implementation steps
1. Lab phase 00: dò bảng mã category C (nói từng câu keyword, log số) + test `BotSayLocal`.
2. Hồi sinh execChat có điều kiện (config `SIMBOT_CHAT_REPLY=1`).
3. FSM step + soạn ~15 chuỗi hội thoại tiếng Việt (chào hỏi, xin đồ, rủ solo, rủ nhóm, hỏi đường → kết hợp teleport phase 01: bot chỉ đường kèm toạ độ).
4. Cá nhân hoá `{ten}` trong duel/party/trade.
5. Test tầng 1: 2 người cùng bắt chuyện 1 bot, spam chat, chat lúc bot đang đánh.
6. Tầng 2-3 sau khi có source vdk.so (thiết kế đã chốt ở trên).

## Todo
- [ ] Dò bảng category C + test BotSayLocal
- [ ] Hồi sinh execChat + config switch
- [ ] FSM step + 15 chuỗi hội thoại
- [ ] Placeholder {ten}
- [ ] Panel editor nhóm câu
- [ ] Test 3 ca
- [ ] (Tầng 2) PollSayText | (Tầng 3) chatbridge daemon

## Success criteria
- Tầng 1: chào bot → bot chào lại đúng; nói tiếp cùng chủ đề → bot trả lời bước kế, không lặp câu; đang duel bot gọi đúng tên người chơi.
- Tầng 3: câu tự do bất kỳ được LLM trả lời trong ≤3s, có fallback khi daemon tắt.

## Risks
- Hồi sinh funSys.Update kéo theo logic cũ (rơi tiền khi đi, heal) chạy lại ngoài ý muốn → chỉ gọi phần chat, không gọi cả Update nếu side-effect: tách hàm.
- Chat quá dày gây lag/phiền: cooldown + CHANCE_CHAT thấp + công tắc tắt nhanh trong config.
- LLM trả nội dung không phù hợp: filter + giới hạn độ dài + system prompt chặt (daemon side).
