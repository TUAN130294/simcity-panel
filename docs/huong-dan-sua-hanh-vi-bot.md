# Hướng dẫn sửa HÀNH VI bot SimCity (logic code)

> Số & công tắc → chỉnh ở tab **Bảng điều khiển**. Danh sách chữ (chat, tên bang) → tab **Danh sách dữ liệu**.
> Còn **cách bot *quyết định*** (đuổi ai, khi nào đánh, hồi máu ra sao…) là **code Lua** — sửa theo hướng dẫn dưới.

## 0. Quy tắc an toàn (đọc trước khi sửa)
1. **Luôn có backup.** App tự tạo `<file>.bak` mỗi lần lưu. Ngoài ra đã có backup nguyên thư mục: `/home/jxser/simcity-presweep-*.tar.gz`.
2. Sửa 1 chỗ nhỏ → **Restart server** → vào game xem → ổn mới sửa tiếp. Đừng sửa 10 chỗ rồi mới test.
3. Chỉ đổi thứ mình hiểu. Nếu bot biến mất / không đánh sau khi sửa → khôi phục `.bak` rồi restart.
4. **Không xoá dấu `end`, `)`, `,`** — Lua rất nhạy. Sai 1 ký tự là cả file lỗi, bot không chạy.

## 1. Sửa ở đâu?
Dùng tab **📝 Sửa file thô** trong app: mở file → sửa → **Save vào VM** (tự backup). Hoặc dùng tab Bảng điều khiển cho số.

## 2. Bản đồ FILE → hành vi (biết chỗ mà tìm)
| File | Điều khiển hành vi gì |
|---|---|
| `config.lua` | Toàn bộ số/công tắc (đã có ở panel) |
| `components/sim.core.lua` | Vòng đời bot mỗi tick, ép level/tốc đánh, hàng đợi chào/khiêu khích |
| `components/sim.fun.lua` | **Hồi máu** (`execRestoreLife`), cộng điểm quanh bot |
| `components/sim.fight.lua` | Cách đánh, buff Nga Mi, ra chiêu môn phái |
| `components/sim.entity.lua` | Tạo NPC: ngoại trang, phái, vũ khí, danh hiệu, set HP |
| `components/sim.movement.lua` | Di chuyển, tìm đường, đi tuần |
| `class/group_fighter.class.lua` | Đánh theo nhóm, tính điểm, **chết & hồi sinh**, aggro người chơi |
| `class/sim_citizen.lua` | Sinh nhân sĩ, bảng xếp hạng, gắn tên bang |
| `class/sim_theosau.lua` | Pet / đi theo người chơi |
| `plugins/pthanhthi.lua` | Sinh bot thành thị, đội tuần tra |
| `plugins/ptongkim.lua` | Tính điểm Tống Kim (giết người chơi) |
| `plugins/pchat.lua` | Câu chat (đã có list editor) |
| `plugins/pchientranh.lua` | Chiến trường |

## 3. Cách đọc 1 đoạn logic (ví dụ)
Trong `sim.fun.lua`, hàm hồi máu:
```lua
function execRestoreLife(tbNpc)
    if tbNpc.isDead == 0 and tbNpc.tick_breath > 0
        and mod(tbNpc.tick_breath, 10*18/REFRESH_RATE) == 0 then   -- cứ ~10 giây 1 lần
        ...
        local restoreAmount = SIMBOT_HEAL_AMOUNT     -- lượng hồi (đã đưa lên panel)
        local newLife = currentLife + restoreAmount
        if newLife > maxLife then newLife = maxLife end
        NPCINFO_SetNpcCurrentLife(tbNpc.finalIndex, newLife)
    end
end
```
Đọc: *cứ ~10 giây, nếu bot còn sống thì cộng `SIMBOT_HEAL_AMOUNT` máu, không vượt máu tối đa.*

## 4. Công thức "recipe" hay dùng
### a) Bot CHỈ hồi máu khi KHÔNG đánh nhau (giống người thật)
Trong `sim.fun.lua`, thêm điều kiện `tbNpc.isFighting == 0`:
```lua
    if tbNpc.isDead == 0 and tbNpc.isFighting == 0 and tbNpc.tick_breath > 0
        and mod(tbNpc.tick_breath, 10*18/REFRESH_RATE) == 0 then
```
→ Bot đang combat sẽ **không tự hồi**, thoát combat mới hồi.

### b) Bot đánh người chơi hung hơn / hiền hơn
Không cần sửa code — chỉnh trên panel: `CHANCE_ATTACK_PLAYER`, `SIMBOT_AGGRO_PLAYER_PCT`, `SIMBOT_ATTACK_PLAYER_CHANCE`.

### c) Bot bất tử (test) / có số máu cố định
Panel: `SIMBOT_HEAL_AMOUNT` cao = trâu. Muốn máu cố định không hồi → đặt `LIFE_RESTORE_PERCENT = 0`.

### d) Đổi câu bot nói khi bị đánh (khiêu khích)
Logic đã sẵn trong `sim.core.lua` (`SimBotTaunt`/`SimBotTauntDrain`) nhưng cần danh sách `SimCityChat.rep_chui`. Thêm vào cuối `plugins/pchat.lua`:
```lua
SimCityChat.rep_chui = {
	"§¸nh l¹i xem!",
	"Ngon th× vµo!",
}
```
(gõ TCVN3 hoặc copy câu có sẵn rồi sửa). → bot sẽ bung câu này khi bị khiêu khích.

### e) Bot không hồi sinh sau khi chết
Trong `group_fighter.class.lua`, chỗ `if tbNpc.noRevive == 1 then return end` — đặt `noRevive = 1` khi sinh bot (trong `pthanhthi.lua` config) để bot chết là mất luôn.

## 5. Sau khi sửa
1. **Save** (app tự backup).
2. Bấm **Restart server** (nút đỏ) hoặc `cd /root/quanlyserver/2.3.1 && ./jx.sh restart`.
3. Vào game kiểm tra. Lỗi → khôi phục `.bak` → restart.

## 6. Khôi phục toàn bộ nếu hỏng nặng
```
cd /home/jxser/server1/script/global/nobitaxd/vdk/simcity
tar xzf /home/jxser/simcity-presweep-*.tar.gz
```
(rồi Restart server) — trả mọi file về trước khi sửa.

## 7. Giới hạn thành thật
- Thêm **hoạt động MỚI hoàn toàn** (vd Phong Lăng Độ, săn boss theo tổ đội) = viết plugin mới + móc vào engine → việc lớn, cần lập trình Lua bài bản, không phải sửa 1 dòng.
- Một số hành vi phụ thuộc **hàm engine** (biên dịch sẵn trong `jx_linux_y`) — chỉ gọi được, không sửa được logic bên trong.
