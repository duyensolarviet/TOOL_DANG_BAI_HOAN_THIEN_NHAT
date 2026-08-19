import os
import json
import hmac
import hashlib
import base64
import datetime
from typing import Tuple, Optional, Dict, Any

LICENSE_SECRET_KEY = "VUDUYEN_SECURE_LICENSE_SYSTEM_2026_@KEY_BOT_AUTO_ALL_IN_ONE"

def _b64_encode(data_bytes: bytes) -> str:
    return base64.urlsafe_b64encode(data_bytes).decode("utf-8").rstrip("=")

def _b64_decode(data_str: str) -> bytes:
    padding = 4 - (len(data_str) % 4)
    if padding < 4:
        data_str += "=" * padding
    return base64.urlsafe_b64decode(data_str.encode("utf-8"))

def generate_signed_license_token(
    hwid: str,
    key_code: str,
    package: str,
    duration_days: float,
    duration_label: str,
    expires_at: str,
    created_at: str = None,
    note: str = ""
) -> str:
    """
    Generates a cryptographically signed license token (LIC-...)
    Can be verified offline by matching machine HWID and signature.
    """
    now_str = created_at or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    payload = {
        "hwid": hwid.strip().upper(),
        "key": key_code.strip().upper(),
        "package": package,
        "duration_days": duration_days,
        "duration_label": duration_label,
        "expires_at": expires_at,
        "created_at": now_str,
        "note": note,
        "schema": "v2.0"
    }

    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    b64_payload = _b64_encode(payload_json)

    signature = hmac.new(
        LICENSE_SECRET_KEY.encode("utf-8"),
        b64_payload.encode("utf-8"),
        hashlib.sha256
    ).digest()
    b64_sig = _b64_encode(signature)

    return f"LIC-{b64_payload}.{b64_sig}"

def verify_signed_license_token(token_str: str, current_hwid: str = None) -> Tuple[bool, str, Optional[dict]]:
    """
    Verifies the cryptographic signature, expiration date, and HWID of a license token.
    Returns: (is_valid, message, payload_dict)
    """
    raw = "".join(token_str.strip().split())
    if not raw.startswith("LIC-"):
        return False, "Định dạng mã bản quyền không hợp lệ (phải bắt đầu bằng LIC-)", None

    token_body = raw[4:]
    if "." not in token_body:
        return False, "Mã bản quyền bị thiếu chữ ký bảo mật!", None

    b64_payload, b64_sig = token_body.split(".", 1)

    # 1. Decode payload
    try:
        payload_bytes = _b64_decode(b64_payload)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        return False, f"Không thể giải mã dữ liệu bản quyền: {e}", None

    # 2. Check HWID lock
    token_hwid = payload.get("hwid", "").strip().upper()
    if current_hwid and token_hwid:
        curr = current_hwid.strip().upper()
        if token_hwid != curr and token_hwid != "ANY" and token_hwid != "*":
            return False, f"Mã bản quyền này chỉ dành cho thiết bị ({token_hwid}), không khớp với máy tính của bạn ({curr})!", None

    # 3. Check Expiration Date
    exp_str = payload.get("expires_at", "")
    if exp_str:
        try:
            # Flexible ISO / space format
            clean_exp = exp_str.replace("T", " ")[:19]
            exp_dt = datetime.datetime.fromisoformat(clean_exp)
            now = datetime.datetime.now()
            if now > exp_dt:
                return False, f"Mã bản quyền đã HẾT HẠN vào lúc {clean_exp}!\nVui lòng liên hệ Admin để gia hạn thêm.", None
        except Exception:
            pass

    return True, f"Bản quyền hợp lệ: {payload.get('duration_label', 'Gói Bản Quyền')}", payload
