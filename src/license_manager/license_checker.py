import os
import json
import datetime
from typing import Tuple, Optional, Dict, Any

from .hwid import get_device_hwid, get_device_info
from .storage_backend import CloudStorageBackend, get_network_time, load_license_config
from .crypto_token import verify_signed_license_token

LICENSE_CACHE_FILE = "license_info.json"

PACKAGE_NAMES = {
    "trial_auto": "Dùng Thử Miễn Phí",
    "trial_1day": "Dùng Thử (1 Ngày)",
    "trial_3days": "Dùng Thử (3 Ngày)",
    "trial_7days": "Dùng Thử (7 Ngày)",
    "1_month": "Gói 1 Tháng (30 Ngày)",
    "3_months": "Gói 3 Tháng (90 Ngày)",
    "6_months": "Gói 6 Tháng (180 Ngày)",
    "1_year": "Gói 1 Năm (365 Ngày)",
    "lifetime": "Gói Vĩnh Viễn",
    "custom": "Gói Tùy Chỉnh"
}

class LicenseChecker:
    def __init__(self):
        self.storage = CloudStorageBackend()
        self.config = load_license_config()
        self.current_hwid = get_device_hwid()
        self.device_info = get_device_info()
        self.cache_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            LICENSE_CACHE_FILE
        )

    def _get_cache(self) -> Optional[dict]:
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data
            except Exception:
                pass
        return None

    def _save_cache(self, license_data: dict):
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(license_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[LicenseChecker] Error saving cache: {e}")

    def clear_cache(self):
        if os.path.exists(self.cache_path):
            try:
                os.remove(self.cache_path)
            except Exception:
                pass

    def check_current_license(self, force_online: bool = False) -> Tuple[bool, str, Optional[dict]]:
        """
        Check if the tool currently has a valid license or auto free trial.
        Returns: (is_valid, message, license_or_trial_data)
        """
        self.config = load_license_config()
        cache = self._get_cache()

        # 1. Check if user already activated a paid key or signed token
        if cache and cache.get("key") and cache.get("type") != "trial":
            saved_key = cache.get("key", "").strip()
            saved_hwid = cache.get("hwid", "")
            if saved_hwid and saved_hwid != self.current_hwid:
                self.clear_cache()
                return False, "Mã thiết bị không khớp với bản quyền đã lưu!", None

            cloud_key = None
            try:
                cloud_key = self.storage.get_key(saved_key)
            except Exception as e:
                print(f"[LicenseChecker] Cloud check error: {e}")

            if cloud_key:
                is_valid, msg, lic = self._evaluate_key(cloud_key)
                if is_valid:
                    return True, msg, lic
                else:
                    self.clear_cache()
                    return False, msg, None
            else:
                # Key was deleted from storage (Local DB or Cloud) -> Revoke immediately!
                self.clear_cache()
                return False, "Mã Key bản quyền đã bị xóa khỏi hệ thống hoặc không còn tồn tại!", None

        # 2. Check if this HWID was activated directly online by Admin
        try:
            hwid_license = self.storage.get_key_by_hwid(self.current_hwid)
            if hwid_license:
                is_valid, msg, lic = self._evaluate_key(hwid_license)
                if is_valid:
                    return True, msg, lic
        except Exception as e:
            print(f"[LicenseChecker] HWID check error: {e}")

        return False, "Thiết bị chưa được kích hoạt bản quyền. Vui lòng nhập mã Key để sử dụng!", None

    def activate_key(self, raw_key: str) -> Tuple[bool, str, Optional[dict]]:
        """
        Validates and activates a key entered by user.
        Supports both offline signed tokens (LIC-...) and online/local keys (VD-...).
        """
        key_code = raw_key.strip()
        if not key_code:
            return False, "Vui lòng nhập mã bản quyền (Key)!", None

        # 1. Support offline cryptographic token (LIC-...)
        if key_code.startswith("LIC-") or ("." in key_code and len(key_code) > 50):
            token_str = key_code if key_code.startswith("LIC-") else f"LIC-{key_code}"
            is_valid, msg, token_payload = verify_signed_license_token(token_str, self.current_hwid)
            if is_valid and token_payload:
                token_payload["type"] = "paid"
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                token_payload["activated_at"] = token_payload.get("activated_at") or now_str
                token_payload["last_seen"] = now_str
                token_payload["status"] = "active"
                
                # Save cache and sync to storage
                self._save_cache(token_payload)
                try:
                    self.storage.save_key(token_payload)
                    self.storage.save_device_license(self.current_hwid, token_payload)
                except Exception:
                    pass
                
                pkg_label = token_payload.get("duration_label") or PACKAGE_NAMES.get(token_payload.get("package", ""), "Bản quyền")
                return True, f"Kích hoạt thành công {pkg_label}!\nHạn dùng đến: {token_payload.get('expires_at')}", token_payload
            else:
                return False, msg, None

        # 2. Support standard key codes (VD-...) or direct HWID
        key_data = self.storage.get_key(key_code)
        if not key_data:
            # Check if user entered HWID that has an active key in database
            hwid_license = self.storage.get_key_by_hwid(key_code)
            if hwid_license:
                key_data = hwid_license

        if not key_data:
            return False, "Mã Key không tồn tại trên hệ thống! Vui lòng kiểm tra lại.", None

        # Check if key is unused -> First time activation
        key_hwid = key_data.get("hwid", "")
        if not key_hwid or key_hwid.strip() == "":
            return self._perform_first_activation(key_data)

        # Key already activated -> verify
        return self._evaluate_key(key_data)

    def _perform_first_activation(self, key_data: dict) -> Tuple[bool, str, Optional[dict]]:
        """Binds HWID and computes expiration date upon first activation"""
        key_code = key_data.get("key")
        duration_days = int(key_data.get("duration_days", 30))
        now = get_network_time()
        
        expires_at_dt = now + datetime.timedelta(days=duration_days)
        
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        expires_at_str = expires_at_dt.strftime("%Y-%m-%d %H:%M:%S")

        update_fields = {
            "type": "paid",
            "hwid": self.current_hwid,
            "device_name": f"{self.device_info.get('hostname')} ({self.device_info.get('username')})",
            "activated_at": now_str,
            "expires_at": expires_at_str,
            "status": "active"
        }

        success = self.storage.update_key_fields(key_code, update_fields)
        if not success:
            return False, "Không thể kết nối đến máy chủ kích hoạt. Vui lòng kiểm tra mạng!", None

        # Merge fields
        key_data.update(update_fields)
        self._save_cache(key_data)

        pkg_label = PACKAGE_NAMES.get(key_data.get("package", ""), f"{duration_days} Ngày")
        return True, f"Kích hoạt thành công {pkg_label}!\nHạn dùng đến: {expires_at_str}", key_data

    def _evaluate_key(self, key_data: dict) -> Tuple[bool, str, Optional[dict]]:
        """Evaluates an existing key for validity, HWID lock, and expiration"""
        key_code = key_data.get("key")
        status = key_data.get("status", "active")
        
        if status == "banned":
            return False, "Mã Key này đã bị KHÓA bởi Quản trị viên!", None

        key_hwid = key_data.get("hwid", "")
        if key_hwid and key_hwid != self.current_hwid:
            return False, f"Key này đã được kích hoạt trên thiết bị khác ({key_hwid})!\nVui lòng liên hệ Admin nếu bạn vừa đổi máy tính.", None

        expires_at_str = key_data.get("expires_at", "")
        if expires_at_str:
            try:
                expires_at_dt = datetime.datetime.fromisoformat(expires_at_str)
                now = get_network_time()
                if now > expires_at_dt:
                    return False, f"Mã Key đã HẾT HẠN sử dụng vào ngày {expires_at_str}!\nVui lòng liên hệ Admin để gia hạn thêm.", None

                # Anti-clock-tamper check: Detect if local machine clock was rolled back
                last_seen_str = key_data.get("last_seen", "")
                if last_seen_str:
                    try:
                        last_seen_dt = datetime.datetime.fromisoformat(last_seen_str[:19])
                        if now < last_seen_dt - datetime.timedelta(hours=2):
                            return False, "Phát hiện thời gian máy tính bị chỉnh lùi về quá khứ!\nVui lòng cài đặt lại đúng ngày giờ thực tế để tiếp tục.", None
                    except Exception:
                        pass
            except Exception:
                pass

        # Valid! Record last_seen and save cache
        now = get_network_time()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        key_data["type"] = "paid"
        key_data["last_seen"] = now_str
        self._save_cache(key_data)

        # Update last_seen in storage
        try:
            self.storage.update_key_fields(key_code, {"last_seen": now_str})
        except Exception:
            pass
        
        pkg = key_data.get("package", "")
        pkg_name = PACKAGE_NAMES.get(pkg, f"{key_data.get('duration_days', 30)} Ngày")
        return True, f"Bản quyền hợp lệ: {pkg_name}", key_data

    def update_heartbeat(self, license_data: dict = None):
        """Update last_seen timestamp in storage backend for online statistics"""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            if not license_data:
                cache = self._get_cache()
                if cache:
                    license_data = cache
            if license_data:
                is_trial = license_data.get("type") == "trial" or license_data.get("package") == "trial_auto"
                if is_trial:
                    hwid = license_data.get("hwid") or self.current_hwid
                    self.storage.update_trial_fields(hwid, {"last_seen": now_str})
                else:
                    key = license_data.get("key")
                    if key:
                        self.storage.update_key_fields(key, {"last_seen": now_str})
        except Exception:
            pass

    @staticmethod
    def format_license_badge(key_data: dict) -> str:
        """Returns compact badge string for UI header"""
        if not key_data:
            return "Chưa kích hoạt bản quyền"
        
        pkg = key_data.get("package", "")
        is_trial = key_data.get("type") == "trial" or pkg == "trial_auto"
        pkg_name = PACKAGE_NAMES.get(pkg, "Bản quyền" if not is_trial else "Dùng Thử")
        
        expires_at_str = key_data.get("expires_at", "")
        if not expires_at_str:
            return f"🎁 {pkg_name}" if is_trial else f"👑 {pkg_name}"
            
        try:
            expires_at_dt = datetime.datetime.fromisoformat(expires_at_str)
            now = datetime.datetime.now()
            diff = expires_at_dt - now
            days_left = diff.days
            hours_left = int(diff.seconds / 3600)
            
            if diff.total_seconds() <= 0:
                return "❌ HẾT HẠN DÙNG THỬ" if is_trial else "❌ Bản quyền HẾT HẠN"
            elif pkg == "lifetime":
                return "👑 VIP Vĩnh Viễn"
            elif is_trial:
                if days_left > 0:
                    time_str = f"Còn {days_left} ngày {hours_left}h"
                elif hours_left > 0:
                    mins_left = (diff.seconds % 3600) // 60
                    time_str = f"Còn {hours_left}h {mins_left}p"
                else:
                    time_str = f"Còn {max(1, diff.seconds // 60)} phút"
                return f"🎁 DÙNG THỬ MIỄN PHÍ ({time_str})"
            else:
                if days_left > 0:
                    date_fmt = expires_at_dt.strftime("%d/%m/%Y")
                    return f"👑 {pkg_name} | HSD: {date_fmt} (Còn {days_left} ngày {hours_left}h)"
                elif hours_left > 0:
                    time_fmt = expires_at_dt.strftime("%H:%M:%S")
                    mins_left = (diff.seconds % 3600) // 60
                    return f"👑 {pkg_name} | HSD: {time_fmt} (Còn {hours_left}h {mins_left}p)"
                else:
                    time_fmt = expires_at_dt.strftime("%H:%M:%S")
                    mins_left = max(1, diff.seconds // 60)
                    return f"👑 {pkg_name} | HSD: {time_fmt} (Còn {mins_left} phút)"
        except Exception:
            return f"👑 {pkg_name}"
