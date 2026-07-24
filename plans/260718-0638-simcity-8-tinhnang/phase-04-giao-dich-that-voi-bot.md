# Phase 04 — Giao dịch thật với bot

## Overview
- **Ưu tiên:** P2 | **Độ khó:** Vừa (tầng 1) → Cao (tầng 2, cần source vdk.so) | **Thời lượng:** ~2 ngày (tầng 1)
- **Hiện trạng (user xác nhận 2026-07-18):** bot ĐÃ bày bán (ngồi sạp `SetNpcStall`) và người chơi xin đồ ĐÃ có giao dịch — mở cửa sổ trade với bot là được tặng đồ (`PollTradeStay` → `SendTradeItem` sau 8s). Coi như phần "cho đồ theo yêu cầu" xong.
- **Phần còn thiếu = mục tiêu phase này:** (a) sạp bày bán mới chỉ là "diễn" — click sạp chưa mua được món đang bày; (b) giao dịch mới 1 chiều bot→người: bot không nhận đồ/tiền của người chơi, không định giá, không mặc cả → làm cho có qua có lại.

## Key insights
- KHÔNG có API Lua chuẩn mở/điều khiển cửa sổ trade 2 người; cặp `PollTradeStay(idx)` (state 1-4) + `SendTradeItem(idx)` là hàng C vá riêng (`sim.core.lua:860-915`), Lua không kiểm soát được item nào được đưa và không đọc được item người chơi đặt vào → **trade 2 chiều thật qua cửa sổ = phải mở rộng vdk.so** [CẦN SOURCE VDK.SO].
- Trao đổi kinh tế thật làm được ngay bằng API chuẩn: `AddItem(genre,detail,particular,level,series,luck)`, `GetItemCountEx`, `CheckItemInBag`/`ConsumeEquiproomItem` (mẫu `activitysys/2/activitydetail.txt`), `Earn/Pay/GetCash`, `CalcFreeItemCellCount` (check túi đầy), `Sale(shopId)` (mở shop chuẩn).
- Bot bày bán đã có hình thức: `NpcSit + SetNpcStall + SetBotStallTier` (45-65 bot sạp/thành) — nhưng sạp chỉ là "diễn", click không mua được.
- Category chat `giaodich/rep_giaodich` có sẵn trong `chat.txt` → bot có thể rao hàng.

## Architecture — 2 tầng
### Tầng 1 (Lua thuần — làm ngay): "Sạp thật" qua dialog
- Click bot đang ngồi sạp → mở menu buôn bán (gắn script dialog cho bot stall qua `SetNpcScript`, giống cách tiểu thiếp có menu `controllers/tieuthiep.lua`):
  - **Mua của bot:** danh mục 3-8 món/bot lấy từ "kho cá nhân" của bot (sinh ngẫu nhiên lúc spawn từ `SET/global/vdk/botshop/goods.txt` — TSV: nhóm hàng, genre/detail/particular/level, giá gốc, biên độ giá ±%). Trả tiền `Pay` → `AddItem`. Mỗi món có số lượng hữu hạn → tạo cảm giác "hàng thật", hết hàng bot rao câu khác.
  - **Bán cho bot:** danh mục vật phẩm bot thu mua (dược phẩm, nguyên liệu...) — `CheckItemInBag` → consume → `Earn` giá thu mua (thấp hơn giá bán, chỉnh panel).
  - **Trả giá (tuỳ chọn vui):** `AskClientForNumber` — bot chấp nhận trong biên độ, hạ giá dần theo số lần trả, từ chối thì `NpcChat` câu `rep_no`.
- Giữ nguyên hành vi tặng đồ `SendTradeItem` hiện có (user hài lòng); chỉ THÊM giới hạn lần/ngày/người qua task-id để chống farm, số lần chỉnh trên panel.
- Log mọi giao dịch ra file (`io.open` append `SET/global/vdk/botshop/trade.log`) để panel hiển thị + cân bằng kinh tế.

### Tầng 2 (mở rộng vdk.so — sau khi có source): trade cửa sổ 2 chiều
- Thêm export: `TradeGetOfferedItems(npcIdx)` (đọc item+tiền player đặt vào), `SendTradeItemEx(npcIdx, genre, detail, particular, count)`, `TradeAcceptEx/TradeCancel`.
- Lua định giá offer của player theo bảng giá goods.txt → đồng ý/đưa hàng đối ứng/huỷ kèm câu chat phù hợp.

## Related files
- Tạo: `vdk/botshop/{main,shop,pricing,log}.lua`, `SET/global/vdk/botshop/goods.txt`, `buyback.txt`.
- Sửa: `SIM/components/sim.entity.lua` (gắn NpcScript menu cho bot stall + sinh kho lúc spawn), `SIM/components/sim.core.lua` (giới hạn quà tặng), `vdk/main.lua`, `simcity_catalog.py` + UI panel (bảng hàng hoá, hệ số giá, log).

## Implementation steps
1. Thiết kế `goods.txt`/`buyback.txt` (bắt đầu ~30 mặt hàng an toàn: dược, nguyên liệu, đồ event Túi nguyên liệu đã có ở server).
2. `shop.lua`: menu mua/bán/phân trang + kho per-bot + số lượng hữu hạn + restock khi respawn.
3. `pricing.lua`: giá dao động ±%, trả giá, chênh lệch mua/bán.
4. Gắn script menu cho bot stall; bot rao hàng dùng category `giaodich` (tần suất thấp).
5. Giới hạn quà tặng SendTradeItem theo ngày/người; log giao dịch.
6. Panel: bảng chỉnh goods/giá (TCVN3), xem log.
7. Test: mua khi túi đầy (`CalcFreeItemCellCount`), tiền không đủ, bán item không có, farm quà tặng, 2 người cùng mở menu 1 bot.
8. [Tầng 2 — chờ source vdk.so] thiết kế + vá + test cửa sổ trade thật.

## Todo
- [ ] goods.txt + buyback.txt khởi đầu
- [ ] shop.lua menu + kho per-bot
- [ ] pricing.lua trả giá
- [ ] Giới hạn quà + log
- [ ] Panel bảng hàng + log viewer
- [ ] Test 5 ca
- [ ] (Tầng 2) mở rộng vdk.so

## Success criteria
- Click bot sạp mua/bán được hàng thật với giá dao động, tiền/vật phẩm trừ-cộng chính xác, không có đường farm vô hạn; mọi giao dịch có log.

## Risks
- Lạm phát/farm: số lượng hữu hạn + giá thu mua < giá bán + giới hạn ngày + log để audit.
- `AddItem` genre/detail/particular sai → item lỗi: chỉ dùng bộ mã đã thấy trong script gốc (đối chiếu `bonus_onlinetime/func_onlineaward.lua:153`, `baoruongthanbi/key/keyupgrade.lua:121`), test từng mặt hàng.
- Click bot = chọn mục tiêu khi PK thành thị bật (phase 02): chỉ gắn menu cho bot stall (đứng yên, khu an toàn).
