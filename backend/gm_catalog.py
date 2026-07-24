"""Danh mục vật phẩm/boss/skill cho tab GM (trích từ npcthunghiem.lua + gm_script.lua).

Mọi thứ phát qua "hòm thư lệnh" (gm_service): đổi PlayerIndex sang nhân vật đích
rồi gọi hàm engine — giống hệt cách file GM gốc phát đồ cho người chơi khác.
Tên đã ở dạng Unicode (hiển thị web); khi cần ghi file thì mới encode TCVN3.
"""


def _rng(pairs):
    """Nở [a,b] thành a..b; số lẻ giữ nguyên. VD [141,142,[159,163]] -> 141,142,159..163."""
    out = []
    for x in pairs:
        if isinstance(x, (list, tuple)):
            out.extend(range(x[0], x[1] + 1))
        else:
            out.append(x)
    return out


# ---- Hoàng Kim môn phái: phái -> {tên bộ: [gold-item id...]} (AddGoldItem(0,id)) ----
HKMP = {
    "Thiếu Lâm": {
        "Đao Tứ Không": [11, 12, 13, 14, 15, 776],
        "Bổng Phục Ma": [6, 7, 8, 9, 10, 771],
        "Quyền Mộng Long": [1, 2, 3, 4, 5, 769],
    },
    "Thiên Vương": {
        "Chùy Hám Thiên": [16, 17, 18, 19, 20],
        "Thương Kế Nghiệp": [21, 22, 23, 24, 25],
        "Đao Ngự Long": [26, 27, 28, 29, 30, 793],
    },
    "Đường Môn": {
        "Nỏ Thiên Quang": [76, 77, 78, 79, 80, 843],
        "Phi Đao Băng Hàn": [71, 72, 73, 74, 75],
        "Phi Tiêu Sâm Hoàng": [81, 82, 83, 84, 85],
        "Bẫy Địa Phách": [86, 87, 88, 89, 90, 854],
    },
    "Ngũ Độc": {
        "Đao Minh Ảo": [61, 62, 63, 64, 65, 829],
        "Chưởng U Lung": [56, 57, 58, 59, 60],
        "Bùa Chú Phược": [66, 67, 68, 69, 70, 834],
    },
    "Nga My": {
        "Kiếm Vô Gian": [31, 32, 33, 34, 35, 796],
        "Chưởng Vô Ma": [36, 37, 38, 39, 40, 801],
        "Buff Vô Trần": [41, 42, 43, 44, 45],
    },
    "Thúy Yên": {
        "Đao Tê Hoàng": [46, 47, 48, 49, 50, 811],
        "Song Đao Bích Hải": [51, 52, 53, 54, 55, 816],
    },
    "Thiên Nhẫn": {
        "Đao Ma Thị": [111, 112, 113, 114, 115, 876],
        "Kích Ma Sát": [101, 102, 103, 104, 105, 868],
        "Bùa Ma Hoàng": [106, 107, 108, 109, 110, 874],
    },
    "Cái Bang": {
        "Rồng Đồng Cừu": [91, 92, 93, 94, 95, 855],
        "Bổng Địch Khái": [96, 97, 98, 99, 100],
    },
    "Võ Đang": {
        "Kiếm Cập Phong": [121, 122, 123, 124, 125, 888],
        "Khí Lăng Nhạc": [116, 117, 118, 119, 120, 881],
    },
    "Côn Lôn": {
        "Đao Sương Tinh": [126, 127, 128, 129, 130, 891],
        "Kiếm Lôi Khung": [131, 132, 133, 134, 135, 898],
        "Bùa Vụ Ảo": [136, 137, 138, 139, 140],
    },
}

# ---- Hoàng Kim set (không theo phái) -> [gold-item id...] ----
HK_SET = {
    "Thiên Hoàng": _rng([[168, 176]]),
    "Kim Phong": _rng([[177, 185]]),
    "Kim Quang": _rng([[194, 203]]),
    "Động Sát": _rng([[143, 146]]),
    "An Bang": _rng([[164, 167]]),
    "Định Quốc": [159, 163],
    "Hiệp Cốt": _rng([[186, 189]]),
    "Nhu Tình": _rng([[190, 193]]),
    "Hồng Ảnh": _rng([[204, 207]]),
    "Hoàn Mỹ An Bang": _rng([[210, 213]]),
    "Cực Phẩm Định Quốc": _rng([[403, 407]]),
    "Cực Phẩm An Bang": _rng([[408, 411]]),
}

# ---- 21 Boss Hoàng Kim: {tên, npcId, series, level} — spawn tại chỗ nhân vật ----
BOSS = [
    {"name": "Huyền Giác Đại Sư", "npcId": 740, "series": 0, "level": 95},
    {"name": "Đường Bất Nhiễm", "npcId": 741, "series": 1, "level": 95},
    {"name": "Bạch Doanh Doanh", "npcId": 742, "series": 1, "level": 95},
    {"name": "Thanh Tuyệt Sư Thái", "npcId": 743, "series": 2, "level": 95},
    {"name": "Yên Hiểu Trái", "npcId": 744, "series": 2, "level": 95},
    {"name": "Hà Nhân Ngã", "npcId": 745, "series": 3, "level": 95},
    {"name": "Từ Đại Nhạc", "npcId": 746, "series": 4, "level": 95},
    {"name": "Tuyền Cơ Tử", "npcId": 747, "series": 4, "level": 95},
    {"name": "Hàn Ngu Dốt", "npcId": 748, "series": 3, "level": 95},
    {"name": "Đoạn Mộc Duệ", "npcId": 565, "series": 3, "level": 95},
    {"name": "Cổ Bách", "npcId": 566, "series": 0, "level": 95},
    {"name": "Đường Phi Yến", "npcId": 1366, "series": 1, "level": 95},
    {"name": "Hà Linh Phiêu", "npcId": 568, "series": 2, "level": 95},
    {"name": "Lam Y Y", "npcId": 582, "series": 1, "level": 95},
    {"name": "Mạnh Thương Lương", "npcId": 583, "series": 3, "level": 95},
    {"name": "Gia Luật Tị Ly", "npcId": 563, "series": 3, "level": 95},
    {"name": "Đạo Thanh Chân Nhân", "npcId": 562, "series": 4, "level": 95},
    {"name": "Vương Tá", "npcId": 739, "series": 0, "level": 95},
    {"name": "Huyền Nan Đại Sư", "npcId": 1365, "series": 0, "level": 95},
    {"name": "Chung Linh Tú", "npcId": 567, "series": 2, "level": 95},
    {"name": "Thanh Liên Tử", "npcId": 1368, "series": 4, "level": 95},
]

# ---- Skill theo phái: học toàn bộ (base cấp 1 + skill 90/120) ----
_SK = {
    "Thiếu Lâm": {"base": [14, 10, 8, 4, 6, 15, 16, 20, 271, 11, 19, 273, 21], "adv": [318, 319, 321, 709]},
    "Thiên Vương": {"base": [34, 30, 29, 26, 23, 24, 33, 37, 35, 31, 40, 42, 32, 36, 41, 324], "adv": [322, 323, 325, 708]},
    "Đường Môn": {"base": [45, 43, 347, 303, 50, 54, 47, 343, 345, 349, 249, 48, 58, 341], "adv": [339, 302, 342, 351, 710]},
    "Nga My": {"base": [63, 65, 62, 60, 67, 70, 66, 68, 384, 64, 69, 356, 73, 72, 71, 75, 74], "adv": [353, 355, 390, 711]},
    "Cái Bang": {"base": [85, 80, 77, 79, 93, 385, 82, 89, 86, 92, 88, 252, 91, 282], "adv": [328, 380, 332, 712]},
    "Thúy Yên": {"base": [99, 102, 95, 97, 269, 105, 113, 100, 109, 108, 114, 111], "adv": [336, 337, 713]},
    "Thiên Nhẫn": {"base": [122, 119, 116, 115, 129, 274, 124, 277, 128, 125, 130, 360], "adv": [357, 359, 714]},
    "Võ Đang": {"base": [135, 145, 132, 131, 136, 137, 141, 138, 140, 364, 143, 142, 150, 148], "adv": [361, 362, 391, 715]},
    "Côn Lôn": {"base": [153, 155, 152, 151, 159, 164, 158, 160, 157, 165, 166, 267], "adv": [365, 368, 716]},
    "Ngũ Độc": {"base": [169, 179, 167, 168, 392, 171, 174, 178, 172, 393, 173, 175, 181, 176, 275, 182, 630], "adv": [372, 375, 394, 717]},
}
# skill học cấp mặc định (support) — còn lại đặt cấp 20
_SKILL_SUPPORT = {351, 390, 332, 391, 394}
SKILL = {ph: {"base": d["base"], "adv": d["adv"]} for ph, d in _SK.items()}
