# Phase 07 — Giả lập "người chơi thật" từ dữ liệu nhân vật đã tạo

## Overview
- **Ưu tiên:** P2 | **Độ khó:** Vừa | **Thời lượng:** ~2 ngày (đường A)
- Trả lời yêu cầu "kiểm tra có thể giả lập người chơi thật từ dữ liệu nhân vật đã tạo không" — **KẾT LUẬN NGHIÊN CỨU: CÓ, ở mức "bot đội lốt nhân vật"** với dữ liệu thu lúc nhân vật online; KHÔNG thể biến save thành người chơi online thật (bot không phải connection).

## Key insights (đánh giá khả thi)
- Bot đã "hoá trang" rất sâu: tên riêng, bang + chức vụ (`SetNpcBang`), danh hiệu (`SetNpcTitle`), ngoại trang/ngựa (`ChangeNpcFeature`), đúng skill môn phái, bán sạp, có mặt BXH Tống Kim client (`BotLadderAdd`), nhận solo/tổ đội/giao dịch → đứng cạnh khó phân biệt.
- Dữ liệu nhân vật: Lua CHỈ đọc được khi nhân vật online (`GetName/GetLevel/GetFaction/GetSeries/GetTongName` qua `CallPlayerFunction`); KHÔNG có API đọc save `.db` offline. `io.open` dùng được để ghi profile.
- **Giới hạn cứng không vượt được bằng Lua** (ghi rõ cho user): bot không hiện trong danh sách online/bạn bè, không whisper được, không chat kênh bang/thế giới bằng "tài khoản" đó, click không xem được trang bị. Vượt các giới hạn này = vá C sâu (whisper: khả thi nếu có source vdk.so; danh sách online: đụng bishop, không khuyến nghị).
- Ngoại hình: bot dùng npcres index, khác không gian dữ liệu với trang bị thật → map gần đúng (phái+giới tính → bộ res tương ứng), không copy được đúng từng món đồ nếu không vá C đọc feature player.

## Architecture — đường A (khuyến nghị): profile capture → bot đội lốt
```
vdk/nguoiao/
  capture.lua   # hook login (login_add trong global/login.lua): thu name/level/faction/series/
                #   tong/tongname → ghi/ cập nhật SET/global/vdk/nguoiao/profiles.txt
                #   (TSV: name, level, faction, series, bang, lastseen)
  spawn.lua     # "triệu hồi người ảo": đọc profiles.txt → tạo SimCitizen với hardsetName=tên
                #   thật, faction/level/bang đúng, ngoại trang map theo phái+giới; đăng ký vào
                #   fighterList như bot thường → tự đi lại/chat/đánh/duel/party/trade
  manager.lua   # chống trùng: nhân vật thật online → despawn bản ảo ngay (check trong
                #   capture hook + SearchPlayer định kỳ); menu GM/panel chọn ai được ảo hoá
```
- Ứng dụng: giữ "người quen" xuất hiện trong thành khi chủ offline; dàn bot Tống Kim mang tên người chơi thật của server (đồng ý trước); kết hợp phase 05 để bot ảo chat đúng "tính cách" (bộ câu riêng per-profile — cột thêm trong profiles.txt).
- Đường B (nghiên cứu thêm, không cam kết): parse file save `.db` offline từ panel (Python trên VM đọc format goddess) để lấy level/faction không cần chờ online — đánh dấu research task riêng, chỉ làm nếu đường A thấy thiếu dữ liệu.

## Related files
- Tạo: 3 file `vdk/nguoiao/*`, `SET/global/vdk/nguoiao/profiles.txt`.
- Sửa: `global/login.lua` (thêm 1 dòng `login_add` — CẨN THẬN file boot chung, snapshot bắt buộc), `vdk/main.lua`, panel (tab "Người ảo": danh sách profile, bật/tắt từng người, số lượng).

## Implementation steps
1. `capture.lua` + hook login; test: login 2 nhân vật → profiles.txt có 2 dòng đúng TCVN3.
2. Bảng map phái+series+giới tính → bộ npcres đẹp (chọn tay ~20 bộ từ `SET/npcres_simple`).
3. `spawn.lua`: dựng bot từ profile (tái dùng nguyên `SimCitizen:New` với override), rải vào thành theo cấu hình số lượng.
4. `manager.lua`: despawn khi chủ online (check lúc login hook + timer 30s `SearchPlayer`), respawn khi logout (hook `global/logout.lua` tuỳ chọn).
5. Panel tab Người ảo.
6. Test: chủ online trong lúc bản ảo đang đứng (phải biến mất ≤30s), trùng tên 2 profile, profile bang TCVN3 hiển thị đúng, bot ảo tham gia duel/party bình thường.

## Todo
- [ ] capture.lua + hook login/logout
- [ ] Bảng map phái→npcres
- [ ] spawn.lua từ profile
- [ ] manager.lua chống trùng online
- [ ] Panel tab Người ảo
- [ ] Test 4 ca
- [ ] (Nghiên cứu) parse save .db offline — chỉ khi cần

## Success criteria
- Nhân vật từng online được "ảo hoá": xuất hiện trong thành với đúng tên/bang/phái/cấp, sinh hoạt như bot thường; chủ thật online thì bản ảo biến mất; danh sách quản lý được từ panel.

## Risks
- **Nhầm lẫn danh tính/lừa đảo trong game**: bot mang tên người thật có thể bị lợi dụng (giả vờ là chủ để "mượn đồ") → mặc định CHỈ ảo hoá nhân vật do admin chọn, thêm tuỳ chọn danh hiệu phân biệt (vd title "Phân Thân") bật/tắt.
- Sửa `global/login.lua` lỗi = không ai vào được game: snapshot + test syntax + include file riêng (login.lua chỉ thêm 1 dòng gọi hàm có guard `if Fn then`).
- Tên trùng NPC/player đang online lúc spawn: manager check trước khi spawn.
