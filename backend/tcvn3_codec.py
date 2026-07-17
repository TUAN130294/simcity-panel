"""Chuyển mã TCVN3 (ABC) <-> Unicode cho tiếng Việt.

File Lua của game lưu chữ Việt bằng bảng mã TCVN3 (đọc byte-faithful qua
latin-1 nên hiển thị thành "Chµo c¸c b¹n"). Module này:
- tcvn3_to_unicode(): hiện chữ Việt chuẩn trên web.
- unicode_to_tcvn3(): người dùng gõ tiếng Việt Unicode bình thường,
  lưu xuống file tự chuyển về TCVN3 để game render đúng.

Bảng mã đối chiếu chuẩn TCVN 5712 (đã kiểm chứng: ViÖt->Việt, cña->của,
sè->số, ®îc->được, tÝnh->tính...). Ánh xạ 1-1 nên chuyển qua lại không mất chữ.
Lưu ý: TCVN3 không có chữ HOA kèm dấu (Ấ, Ộ...) — khi lưu sẽ dùng mã chữ
thường tương ứng (game vẫn đọc được, chỉ mất kiểu hoa).
"""
import unicodedata

# Hai chuỗi thẳng hàng theo từng ký tự: _TCVN3[i] <-> _UNI[i].
# \xad là soft-hyphen (byte 0xAD) = chữ "ư" trong TCVN3.
_TCVN3 = (
    "\xb5\xb8\xb6\xb7\xb9"          # à á ả ã ạ
    "\xa8\xbb\xbe\xbc\xbd\xc6"      # ă ằ ắ ẳ ẵ ặ
    "\xa9\xc7\xca\xc8\xc9\xcb"      # â ầ ấ ẩ ẫ ậ
    "\xae"                          # đ
    "\xcc\xd0\xce\xcf\xd1"          # è é ẻ ẽ ẹ
    "\xaa\xd2\xd5\xd3\xd4\xd6"      # ê ề ế ể ễ ệ
    "\xd7\xdd\xd8\xdc\xde"          # ì í ỉ ĩ ị
    "\xdf\xe3\xe1\xe2\xe4"          # ò ó ỏ õ ọ
    "\xab\xe5\xe8\xe6\xe7\xe9"      # ô ồ ố ổ ỗ ộ
    "\xac\xea\xed\xeb\xec\xee"      # ơ ờ ớ ở ỡ ợ
    "\xef\xf3\xf1\xf2\xf4"          # ù ú ủ ũ ụ
    "\xad\xf5\xf8\xf6\xf7\xf9"      # ư ừ ứ ử ữ ự
    "\xfa\xfd\xfb\xfc\xfe"          # ỳ ý ỷ ỹ ỵ
    "\xa1\xa2\xa7\xa3\xa4\xa5\xa6"  # Ă Â Đ Ê Ô Ơ Ư
)
_UNI = (
    "àáảãạ" "ăằắẳẵặ" "âầấẩẫậ" "đ" "èéẻẽẹ" "êềếểễệ" "ìíỉĩị"
    "òóỏõọ" "ôồốổỗộ" "ơờớởỡợ" "ùúủũụ" "ưừứửữự" "ỳýỷỹỵ" "ĂÂĐÊÔƠƯ"
)

_T2U = {t: u for t, u in zip(_TCVN3, _UNI)}
_U2T = {u: t for t, u in zip(_TCVN3, _UNI)}


def tcvn3_to_unicode(text):
    """Chuỗi đọc byte-faithful (latin-1) -> tiếng Việt Unicode để hiển thị."""
    return "".join(_T2U.get(ch, ch) for ch in text)


def unicode_to_tcvn3(text):
    """Tiếng Việt Unicode (người dùng gõ) -> chuỗi TCVN3 (latin-1-safe) để ghi file.

    - Chuẩn hoá NFC trước (phòng khi gõ/dán kiểu dấu rời NFD).
    - Chữ HOA có dấu không tồn tại trong TCVN3 -> dùng mã chữ thường.
    - Ký tự ngoài bảng và ngoài latin-1 (emoji...) -> "?" để không vỡ file.
    """
    text = unicodedata.normalize("NFC", text)
    out = []
    for ch in text:
        if ch in _U2T:
            out.append(_U2T[ch])
        elif ord(ch) < 128:
            out.append(ch)
        elif ch.lower() in _U2T:            # HOA có dấu -> mã chữ thường
            out.append(_U2T[ch.lower()])
        elif ord(ch) <= 0xFF:               # byte gốc chưa từng map -> giữ nguyên
            out.append(ch)
        else:
            out.append("?")
    return "".join(out)


def looks_like_tcvn3(text):
    """Đoán chuỗi có chứa byte TCVN3 (để biết có cần chuyển hiển thị không)."""
    return any(ch in _T2U for ch in text)
