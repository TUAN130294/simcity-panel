# Phase 00 — Nền tảng: xác minh API vdk.so + khung module mới

## Overview
- **Ưu tiên:** P0 (điều kiện cho mọi phase sau) | **Độ khó:** Thấp | **Thời lượng:** ~0.5 ngày
- Mục tiêu: chốt chữ ký các hàm C chưa rõ, dựng khung thư mục + include cho code mới, chuẩn hoá quy trình test/reload, chuẩn bị hạ tầng panel.

## Context
- `research-findings.md` mục 2 (48 hàm vdk.so), mục 4 (API engine).
- VM: `/home/jxser/server1/vdk.so`, `script/global/nobitaxd/vdk/main.lua`, `script/gmscript.lua`.

## Key insights
- `vdk/main.lua` là điểm include duy nhất của bộ vdk (được nạp qua activity 801) → module mới chỉ cần 1 dòng Include ở đây.
- Các hàm chưa dùng cần thử nghiệm: `BotSayLocal`, `SetNpcDuelAI`, `BotForceCast`, `GetNpcAreaRaw`, `GetBotPoints`, `PartyClearPlayer`.
- `gmscript.lua` có sẵn các hàm GM (`SPos`, `ShowWorldPos`...) → dùng làm sân thử in-game nhanh.

## Implementation steps
1. **Khung module:** tạo `script/global/nobitaxd/vdk/lab/lab.lua` (sandbox test) + include tạm trong `vdk/main.lua`. Mỗi tính năng sau này = 1 thư mục `vdk/<ten>/main.lua` + 1 dòng include.
2. **Xác minh hàm C:** viết hàm test trong lab gọi từng hàm với `if Fn then` guard, log kết quả ra file qua `io.open` (`/tmp/vdk_lab.log`):
   - `BotSayLocal(idx, msg)` — msg hiện ở đâu trên client? (trả lời câu hỏi tồn đọng #2)
   - `SetNpcDuelAI(idx, ?)` — thử 0/1/pIdx, quan sát hành vi.
   - `PollTradeStay/SendTradeItem` — thử thêm tham số thứ 2-3, xem có đổi hành vi/không crash.
   - `GetNpcAreaRaw`, `GetBotPoints` — giá trị trả về.
3. **Quy trình test chuẩn** (ghi vào README plan): sửa file → snapshot → reload → theo dõi `tail -f gameserver.log` + vào game bằng client `Client_VLTK_SHXT` kiểm chứng → ghi kết quả.
4. **Tìm source vdk.so:** hỏi user (câu hỏi tồn đọng #1). Nếu có → mở đường tầng C cho phase 04/05/07.
5. **Panel groundwork:** thêm vào `backend/` 1 service đọc/ghi file settings mới của các tính năng (tái dùng `lua_config_parser`/`list_service`); chưa cần UI.

## Todo
- [ ] Tạo `vdk/lab/lab.lua` + include
- [ ] Test 6 hàm C chưa dùng, ghi kết quả vào research-findings.md
- [ ] Chốt chữ ký PollTradeStay/SendTradeItem
- [ ] Hỏi user về source vdk.so
- [ ] Ghi quy trình test/reload

## Success criteria
- Bảng chữ ký hàm C được xác nhận bằng thử nghiệm thực tế (không đoán).
- Include khung lab không gây lỗi boot (gameserver.log sạch, bot vẫn spawn).

## Risks
- Gọi hàm C sai tham số có thể crash gameserver → test ngoài giờ chơi, luôn có snapshot + `jx.sh reload` sẵn.
- Lua 5.0: lỗi cú pháp trong file include làm hỏng cả chuỗi nạp → kiểm tra syntax trước khi ghi (panel đã có thói quen này).
