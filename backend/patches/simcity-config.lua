CHANCE_AUTO_ATTACK = 1    -- 1/8000 co hoi chuyen sang chien dau
CHANCE_JOIN_FIGHT = 1     -- 1/3000 co hoi tham gia danh nhau khi di ngang qua dam danh nhau
CHANCE_ATTACK_PLAYER = 1  -- 1/3000 co hoi danh nguoi neu den gan nguoi choi dang chien dau

STARTUP_AUTOADD_THANHTHI = 1 -- tu dong moi nhan si tren tat ca ban do
THANHTHI_SIZE = 300   		 -- so luong nhan si trong thanh thi
THON_SIZE = 50               -- so luong bot trong THON nho (it hon thanh, chong ket/chay 1 cho)

THANHTHI_STALL_MIN = 45      -- bot bay ban hang (stall) moi THANH THI: it nhat
THANHTHI_STALL_MAX = 65      -- bot bay ban hang moi THANH THI: nhieu nhat
THON_STALL_MIN = 0          -- bot bay ban hang moi THON: it nhat
THON_STALL_MAX = 1          -- bot bay ban hang moi THON: nhieu nhat
DATAU_STALL_MIN = 20         -- bot tu tap quanh Da Tau: it nhat
DATAU_STALL_MAX = 30         -- bot tu tap quanh Da Tau: nhieu nhat

SIMBOT_TK_LA_NGUOI = 1       -- 1 = bot Tong Kim luon mang loai NGUOI (auto nhan de PK); 0 = nhu cu

SIMBOT_WALK_SPEED = 15       -- toc do DI BO cua bot (nguoi choi ~15)
SIMBOT_RUN_SPEED = 24        -- toc do CHAY cua bot (nguoi choi ~24; cao hon = bot chay nhanh hon nguoi)

-- ===== Bo sung dot ra soat 2026-07-17 =====
TONGKIM_BOT_WAVE_MIN = 20    -- so bot Tong Kim moi dot (moi duong): it nhat
TONGKIM_BOT_WAVE_MAX = 40    -- so bot Tong Kim moi dot: nhieu nhat
LUYENCONG_NHOM_MIN = 6       -- so bot moi nhom o map luyen cong: it nhat
LUYENCONG_NHOM_MAX = 7       -- so bot moi nhom o map luyen cong: nhieu nhat
THANHTHI_QUAI_1IN = 3        -- cu N suat bot thanh thi thi 1 suat la quai (khi bat THANHTHI_QUAI)
THANHTHI_BANG_PCT = 50       -- % bot thanh thi duoc gan ten bang hoi
CHANCE_PREFER_PLAYER = 25    -- % bot uu tien chon NGUOI lam muc tieu khi co ca bot lan nguoi
SIMBOT_PROACTIVE_PLAYER = 0  -- 1 = bot chu dong lung nguoi choi de gay chien (mac dinh 0)
SIMBOT_CITY_BUFF_PCT = 30    -- % bot trong thanh duoc bat buff (hieu ung ho tro)
SIMBOT_KEEP_WALKING_PCT = 90 -- % bot tiep tuc di khi den diem dung (thap = hay dung nghi)
SIMBOT_HP_CAP1_MIN = 10000   -- mau bot cap 1 (thanh thi): it nhat
SIMBOT_HP_CAP1_MAX = 20000   -- mau bot cap 1: nhieu nhat
SIMBOT_HP_CAP2_MIN = 30000   -- mau bot cap 2: it nhat
SIMBOT_HP_CAP2_MAX = 40000   -- mau bot cap 2: nhieu nhat
SIMBOT_HP_CAP3_MIN = 50000   -- mau bot cap 3 (cao nhat): it nhat
SIMBOT_HP_CAP3_MAX = 80000   -- mau bot cap 3: nhieu nhat
DROP_MONEY_WALK_MIN = 1000   -- tien roi moi lan khi bot DI: it nhat
DROP_MONEY_WALK_MAX = 10000  -- tien roi khi bot di: nhieu nhat
DROP_MONEY_DIE_MIN = 1000    -- tien roi khi bot CHET: it nhat
DROP_MONEY_DIE_MAX = 100000  -- tien roi khi bot chet: nhieu nhat

-- ===== Tieu Thiep (xin tien/thuoc/TDP qua doi thoai) =====
TIEUTHIEP_CHO_TIEN_PCT = 10  -- % tieu thiep DONG Y cho tien khi nguoi choi xin (con lai tu choi)
TIEUTHIEP_TIEN_MIN = 1       -- cho it nhat (van luong)
TIEUTHIEP_TIEN_MAX = 5       -- cho nhieu nhat (van luong)
TIEUTHIEP_SO_THUOC = 25      -- so vien thuoc roi ra khi xin thuoc
TIEUTHIEP_SO_TDP = 3         -- so TDP roi ra khi xin TDP
THANHTHI_QUAI = 0			 -- co cho phep quai nhan tu dong xuat hien trong thanh thi hay khong
LUYENCONG_AUTOADD = 1		 -- tu dong them nhan si luyen cong vao map 9x

RADIUS_FIGHT_PLAYER = 20     -- tam quet+tan cong player 
RADIUS_FIGHT_NPC = 8         -- tam quet NPC chung quanh va tan cong
RADIUS_FIGHT_SCAN = 8        -- tam quet dam danh nhau chung quanh de tham gia


CHANCE_CHAT = 10               -- 10/1000 co hoi noi chuyen moi giay
CHANCE_DROP_MONEY = 0 		   -- 1/10000 co hoi lam rot tien khi di chuyen


TIME_FIGHTING = { -- khoang thoi gian danh nhau  (45-120giay)
	minTs = 6000,
	maxTs = 6000
}

TIME_RESTING = { -- nghi ngoi, khong danh nhau lai trong vong thoi gian nay
	minTs = 0,
	maxTs = 1
}

-- TONG KIM setup
TONGKIM_SPAWN_MINSTAY = 0         -- thoi gian toi thieu o lai dai doanh truoc khi xong len
TONGKIM_SPAWN_MAXSTAY = 1        -- thoi gian toi da co the nup trong dai doanh


-- PARAM setup
PARAM_LIST_ID = 1                  -- param to store fighter id
PARAM_CHILD_ID = 2                 -- param to store child id
PARAM_TYPE = 3                     -- param to store type
REFRESH_RATE = 18                  -- refresh rate
BOT_VS_BOT = 1                     -- bot ngoai thanh TU tim+danh bot khac camp (BAT KE PK-mode/vi tri player). 0=tat
BOT_COMBAT_RADIUS = 20             -- tam quet bot combat

-- CHILD SIM CITIZEN/KEOXE setup
DISTANCE_CAN_CONTINUE = 5          -- start next position if within 3 points from destination
DISTANCE_CAN_SPIN = 2              -- when spinning make sure the check is tighter
SPINNING_WAIT_TIME = 0             -- wait time to correct position
CHAR_SPACING = 1                   -- spacing between fighter characters
DISTANCE_FOLLOW_PLAYER = 28        -- chay theo nguoi choi neu cach xa
DISTANCE_SUPPORT_PLAYER = 8        -- neu gan nguoi choi khoang cach 12 thi chuyen sang chien dau
DISTANCE_FOLLOW_PLAYER_TOOFAR = 30 -- neu qua xa nguoi choi vi chay nhanh thi phai bien hinh theo
DISTANCE_VISION = 15               -- qua 15 = phai respawn vi no se quay ve cho cu

LIFE_RESTORE_PERCENT = 5       -- phan tram life se duoc hoi lai moi 1s

ENABLE_BANNGUAMIXDEV = 0	   -- sua lai thanh 1 neu xai ban mix dev vi bi mat ban ngua


-- === SIMBOT NANG CAO (gom so cung ve day de chinh tren web) ===
SIMBOT_HP_MIN = 60000            -- mau bot toi thieu (khi capHP auto)
SIMBOT_HP_MAX = 120000           -- mau bot toi da
SIMBOT_LEVEL = 95                -- cap do bot
SIMBOT_ATKSPEED = 250            -- toc do danh bot (nho hon = danh nhanh hon)
SIMBOT_HEAL_AMOUNT = 3000        -- luong mau hoi moi 10 giay
SIMBOT_AGGRO_PLAYER_PCT = 30     -- %% bot chu dong aggro nguoi choi
SIMBOT_ATTACK_PLAYER_CHANCE = 3  -- ti le bot danh nguoi (thap hon = de danh hon)
