# Research 05 — Cây SETTINGS: maplist / PK / battles / dữ liệu bot (đầy đủ đường dẫn)

> Rà 2026-07-18. `SET` = `/home/jxser/server1/settings`; `maps/` = `/home/jxser/server1/maps`.

## 1. `SET/maplist.ini` — danh bạ map (6.426 dòng, 1 section [List])

Mỗi map = cụm key `<id>=<đường dẫn thư mục map GBK>` + `<id>_Xxx`:
```ini
1=闹市区域\凤翔          ; path dữ liệu map (GBK)
1_name= Ph??ng T??ng     ; tên (TCVN3)
1_MapPos=169,287         ; toạ độ trên bản đồ thế giới (client)
1_MapType=City
1_NpcSeriesAuto=1
1_AutoGoldenNpc=2000
1_GoldenType=13
1_GoldenDropRate=\settings\droprate\goldennpc\golden_lv40.ini
1_NormalDropRate=\settings\droprate\npcdroprate10.ini
```
- **992 map**, id max 994. Key: name 992, NewWorldScript 599, NewWorldParam 596, MapPos 222, MapType 202, MapInfo 64 (trỏ mapinfo.txt battles/maps), NPC/droprate ~150-160.
- MapType (202 map): Battlefield 80, Cave 48, Tong 33, Field 23, Country 10, City 5, Capital 2, Others 1.
- 2 kiểu: map tĩnh (MapPos, 221) và map NewWorld/instance (`_NewWorldScript` trỏ Lua, 599 — vd `960_NewWorldScript=\script\maps\newworldscript.lua`). **264 map không có cả hai = quỹ map ẩn.**
- **KHÔNG có cột enable** — bật/tắt do `maps/worldset.ini` (mục 6). Mở map ẩn = thêm vào worldset + tạo lối vào.
- ~20 map tiêu biểu: 1 Phượng Tường (City), 2 Hoa Sơn, 3 Kiếm Các TB, 4 Kim Quang Động (Cave), 11 Thành Đô, 37 Biện Kinh, 78 Tương Dương, 80 Dương Châu, 162 Đại Lý, 176 Lâm An, 44 Chiến trường TK (Battlefield), 209 Diễn Võ Trường, 212 Hoa Sơn tuyệt đỉnh, 235 Đào Hoa Đảo, 323-325 báo danh TK, 344 Thành trấn sơ cấp, 416 Thuyền Rồng, 520 Minh Nguyệt Trận, 841 Lôi đài hào kiệt, 863 Đường đua, 898 Quốc chiến Giới Kiều, 905 Trường Ca Sơn Trang (dungeon), 925 Thí Luyện Đường, 927 Chiến trường Biện Kinh (thất thành), **960 Lôi Đài Hoàng Thành Tứ**.
- **`_NewWorldParam`** = cờ per-map (chỉ map NewWorld, xử lý `script/maps/newworldscript_h.lua`): `FIGHTSTATE_ON/OFF, PUNISH_OFF, PUNISH_PK10, HEART_OFF, STALL_OFF, PARTNER_OFF, NOTONGCLAIMWAR, TONG_MAP, NATIONALWAR, CreateTeam_OFF, USETOWNP_OFF, CD_Forbid_OFF, NOTIMELIMIT...`. Vd map luyện 917-922: `PUNISH_PK10|FIGHTSTATE_ON|NOTIMELIMIT`; map 960: `PUNISH_OFF|USETOWNP_OFF|HEART_OFF|CD_Forbid_OFF`; mẫu 892: `PUNISH_OFF|FIGHTSTATE_OFF|HEART_OFF|STALL_OFF`. Map thành tĩnh KHÔNG có cờ này.

## 2. `SET/maptraffic.ini` + `SET/map_type.txt`

- `maptraffic.ini` (15.960 dòng, 389 section `[<mapid>]`): dữ liệu CLIENT hiển thị bản đồ — `<n>_Type=0` (494): điểm truyền giữa map (`Point=x,y`, `TargetPoint=`, `Index=<map đích>` — vd `[1]`: `1_Point=1484,601 1_TargetPoint=89,448 1_Index=7`); `Type=1` (1.477): nhãn POI (`Content=Lý Quan`...); `Type=2` (1.779): icon spr.
- `map_type.txt` (36 dòng TSV): nhóm map đặc biệt → item bị cấm. Cột `MAP_TYPE MAP_ID FORBIT_ITEM_TYPE DESCRIPTION`; id dạng `a,b|c` (`|` = dải). Vd:
  - `SONGJIN 44,323|331,344|386,605,606,607 TRANSFER,MATE,CALLNPC,PK`
  - `BAIRENLEITAI 960 TRANSFER,MATE,CALLNPC,PK,SPECIAL`
  - Khác: FENGHUO 516-519, TONGLEITAI 212|220, TONGGONGCHENG 221-223, GUOZHAN 898-900, FUBEN 905,925, SEVENCITY 927|933.

## 3. PK: `citywar.ini` + `killer.ini` + `forbitheart.txt`

- `SET/citywar.ini` (90 dòng GBK): **Công Thành Chiến/bang chiếm thành** (không phải switch PK): `[CityArea]` 7 khu (`AreaName01=Phượng Tường/AreaIncludes01=1`, Thành Đô=11, Đại Lý=162, Biện Kinh=37, Tương Dương=78, Dương Châu=80, Lâm An=176 — trùng 7 file `SET/maps/city_out/{1,11,37,78,80,162,176}.txt`); `[InitCityMaster]` bang chủ đầu; `[CitySettings]` SignUpFee=1000000, MinTongLevel=18, MaxExchangeTax=20, MinTongCrowNumber=60, StartSetTaxTime=22/End=23, WarCycleValue=7.
- `SET/killer.ini` (16 dòng): truy nã: `MoneyPerHour=10000`, `MinTargetLevel=50`, `MaxActiveTaskTime=10` (giờ), `MinReward=100000` + messages TCVN3.
- `SET/forbitheart.txt` (10 dòng TSV `MAPID chú-thích`): map CẤM chế độ hoà bình (ép chiến đấu): 926-933 (thất thành) + 960 (ghi "Bách Nhân Lôi Đài"). Tương đương HEART_OFF. **Muốn ép PK map nào → thêm id (CẦN TEST với map tĩnh).**
- Không có switch "PK=1" cho map City tĩnh trong toàn cây settings → mở PK thành = can thiệp script (phase 02).

## 4. `SET/battles/` + `SET/maps/` + `SET/activitysys/`

- `SET/battles/maps/`: 15 địa hình chiến trường: barrack, boss, bridge, desert, forest, gucheng, jianta, jinshishan, narrow, olden, plain, river, town, valley, woods. Mỗi cái `mapinfo.txt` INI `[MapInfo]/[Area_N]` trỏ file TSV toạ độ (XPOS/YPOS hoặc TRAPX/TRAPY): homepos, trap đại doanh↔dã ngoại, bosspos, fixedflagpos/randomflagpos, **`[Area_SingleFight]` (`SingleFightMap1=357…`)** — map con đơn đấu. Map 326+ trong maplist trỏ `_MapInfo=\settings\battles\maps\plain\mapinfo.txt` v.v.
- `SET/maps/`: citydefence + newcitydefence (công thành: homepos/centerpos/trapline/trappos/boss/tướng/chủ soái), tongwar, tong_leitai (out_trap.txt), challengeoftime (lineup8..56), yandibaozang (waya_01..), dragonboat, huashanqunzhan, `city_out/<mapid>.txt` (TSV `nPosX nPosY map_ID` — vòng toạ độ quanh 7 thành), `missions/{bairenleitai, maze, sevencity}`, 4 thư mục vùng GBK.
- **`SET/maps/missions/bairenleitai/`** (map 960): file TSV `TRAPX TRAPY` (pixel = ô*32): `inmap.txt` (10 điểm thả người), `arena1..5.txt` (viền 5 đài, ~130 điểm/đài), `obstacle.txt`, `drummer.txt` (15 trống trận), `chefu.txt`/`chuwuxiang.txt`/`drugstore.txt` (1 điểm: xa phu/rương/tiệm thuốc). Logic ở `script/missions/bairenleitai/`.
- `SET/activitysys/`: `activity.txt` TSV `Id Name StartDate EndDate Description TaskGroup TaskVersion TaskIdSet` (vd `15 worldcup 201006100000 201006280000 … 10 1`; date 0/trống = vô hạn); `1/activitydetail.txt`, `2/activitydetail.txt` TSV `Id EventId Name StartDate EndDate Message Param1..20` (Param chứa lời gọi Lua `lib:CheckItemInBag(...)`); `42/npcpos.txt` TSV `nMapId nX nY` (NPC ở 78/11/37); `awardtable/<n>.txt` `TableId AwardName LuaBuff Count Rate AwardId ActivityId`.

## 5. `SET/global/vdk/simcity/maps/` — waypoint bot

- `thanhthi.txt`: bảng `WorldID WorldName PathFile Type`; mỗi map 2 file trong `thanhthi/`: **271 file (~135 map)** tên `<mapid>_<ten-khong-dau>_nodes/preset.txt` (có `10000_tongkim_nguyensoai` — id ảo TK).
- `_nodes.txt`: TSV `node_name linked_nodes is_exact type` — node tên `x_y` (ô game), linked = danh sách kề (đồ thị vô hướng): `1625_3161→1625_3161,1625_3183,1627_3175,1756_3093→0→0`.
- `_preset.txt`: TSV `PathName node_name` — nhóm node thành tuyến/khu.
- `trangtri.txt` + `trangtri/78_tuongduong.txt`; `attractions.txt` TSV `worldId worldName pX pY description npcId` (POI: Xa Phu, Lễ Quan, Thợ rèn... Lâm An 176); `haudoanh.txt` TSV `mapId camp nodename` (hậu doanh 2 phe map 885).

## 6. `maps/worldset.ini` (file duy nhất, 145 dòng) — CÔNG TẮC MAP

```ini
[Init]
ServerID=1
[World]
Count=139
World00=78
World01=392
...
World138=512
```
- Server CHỈ load 139 map liệt kê ở đây (7 thành, tân thủ thôn, cave, TK 605/608/609, phong lăng độ 336-341…). maplist khai 992 nhưng ngoài danh sách này = không load = "map ẩn". Có id lặp (57, 78, 209 xuất hiện 2 lần — vô hại). **Mở map: thêm `WorldNN=<id>` + tăng Count + restart + tạo lối vào.**

## 7. `SET/gamesetting.ini` — switch toàn cục (285 dòng)

- `[SYSTEM]`: `GlobalNpcDeathScript=\script\activitysys\g_npcdeath.lua` (hook mọi NPC chết), `IsCheckNpcBarrier=0` (NPC xuyên vật cản), `GoldCoinExtPointNew=1`.
- `[SHOP] nCurrtype=3`.
- `[ServerConfig]`: ExpRate=1000, MoneyRate=100, MaxPlayerCount=1200, **MaxNpcCount=150000, MaxSubWorldCount=1000**, MaxFreeLevel=60, PlayerPoisonDamageMax=600000, FreezeTimeReduceMax=77.
- `[AutoHang] RunScriptVer=0`, `[Relax] RelaxCount=0` → treo máy/relax TẮT. `player_limittime.ini CloseLimit=1` → chống nghiện TẮT.
- KHÔNG có switch PK toàn cục.

## Gợi ý áp dụng
- Mở map ẩn: worldset.ini + clone pattern NewWorldScript/Param + tái dùng mapinfo/trap TSV.
- PK thành: script bật fight-state trong map thành, hoặc forbitheart/HEART_OFF + PUNISH_OFF trên map NewWorld.
- Bot map mới: sinh cặp nodes/preset + đăng ký thanhthi.txt.

## Tồn đọng
- Ngữ nghĩa chính xác từng cờ NewWorldParam (PUNISH_PK10, TISHENZHIREN…) trong C++/`script/maps/newworldscript_h.lua` — đối chiếu khi làm.
- Engine đọc forbitheart.txt cho map tĩnh? — test thực tế khi mở PK thành.
