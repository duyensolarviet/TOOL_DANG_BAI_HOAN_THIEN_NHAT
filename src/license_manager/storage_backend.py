import os
import json
import time
import datetime
import requests
from typing import Optional, Dict, Any, List

CONFIG_FILE = "license_config.json"

DEFAULT_CONFIG = {
    "firebase_url": "",  # e.g., "https://vuduyen-tools-default-rtdb.firebaseio.com"
    "firebase_auth_secret": "",  # Optional database secret
    "telegram_support": "https://t.me/vuduyen_support",
    "zalo_support": "https://zalo.me/0987654321",
    "hotline": "0987.654.321",
    "offline_cache_enabled": True
}

def load_license_config() -> dict:
    """Load configuration from license_config.json or use defaults"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg_path = os.path.join(base_dir, CONFIG_FILE)
    if not os.path.exists(cfg_path):
        cfg_path = os.path.join(os.getcwd(), CONFIG_FILE)

    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass
    return DEFAULT_CONFIG

def save_license_config(config_data: dict):
    """Save configuration to license_config.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg_path = os.path.join(base_dir, CONFIG_FILE)
    try:
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def get_network_time() -> datetime.datetime:
    """
    Fetches real-world current datetime from online sources (Vietnam Time UTC+7).
    Prevents users from tampering with local computer clock to bypass expiration.
    Falls back to local time if offline.
    """
    time_urls = [
        "https://worldtimeapi.org/api/timezone/Asia/Ho_Chi_Minh",
        "https://timeapi.io/api/time/current/zone?timeZone=Asia/Ho_Chi_Minh"
    ]
    for url in time_urls:
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if "datetime" in data:
                    dt_str = data["datetime"][:19]
                    return datetime.datetime.fromisoformat(dt_str)
                elif "dateTime" in data:
                    dt_str = data["dateTime"][:19]
                    return datetime.datetime.fromisoformat(dt_str)
        except Exception:
            continue
            
    # Fallback to local machine time
    return datetime.datetime.now()

class CloudStorageBackend:
    """
    Handles cloud CRUD operations for License Keys.
    Uses Firebase Realtime Database REST API.
    Falls back to local keys_database.json if Firebase URL is not configured yet.
    """
    def __init__(self, firebase_url: str = None, auth_secret: str = None):
        self.config = load_license_config()
        self.firebase_url = (firebase_url or self.config.get("firebase_url", "")).rstrip("/")
        self.auth_secret = auth_secret or self.config.get("firebase_auth_secret", "")
        self.local_db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "local_keys_db.json"
        )

    def _format_key_id(self, raw_key: str) -> str:
        """Sanitize key for URL / path safe storage"""
        return raw_key.strip().replace("/", "_").replace(".", "_").replace("#", "_").replace("$", "_").replace("[", "_").replace("]", "_")

    def _get_url(self, path: str) -> str:
        url = f"{self.firebase_url}/{path}.json"
        if self.auth_secret:
            url += f"?auth={self.auth_secret}"
        return url

    def is_cloud_enabled(self) -> bool:
        return bool(self.firebase_url and self.firebase_url.startswith("http"))

    # ==================== CLOUD OPERATIONS ====================

    def get_key(self, key_code: str) -> Optional[dict]:
        """Fetch a specific key from database"""
        clean_key = key_code.strip()
        key_id = self._format_key_id(clean_key)

        if self.is_cloud_enabled():
            try:
                url = self._get_url(f"keys/{key_id}")
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and data:
                        return data
                return None
            except Exception as e:
                print(f"[CloudStorage] Error fetching key {clean_key}: {e}")
                return None
        else:
            # Fallback to local DB
            return self._local_get_key(clean_key)

    def save_key(self, key_data: dict) -> bool:
        """Save or update a key in database"""
        key_code = key_data.get("key", "").strip()
        if not key_code:
            return False
        key_id = self._format_key_id(key_code)

        if self.is_cloud_enabled():
            try:
                url = self._get_url(f"keys/{key_id}")
                resp = requests.put(url, json=key_data, timeout=6)
                return resp.status_code in [200, 201, 204]
            except Exception as e:
                print(f"[CloudStorage] Error saving key {key_code}: {e}")
                return False
        else:
            return self._local_save_key(key_data)

    def update_key_fields(self, key_code: str, fields: dict) -> bool:
        """Update specific fields of a key (e.g. hwid, activated_at, expires_at, status)"""
        clean_key = key_code.strip()
        key_id = self._format_key_id(clean_key)

        if self.is_cloud_enabled():
            try:
                url = self._get_url(f"keys/{key_id}")
                resp = requests.patch(url, json=fields, timeout=6)
                key_data = self.get_key(clean_key)
                if key_data and key_data.get("hwid"):
                    dev_url = self._get_url(f"devices/{self._format_key_id(key_data['hwid'])}")
                    requests.patch(dev_url, json=fields, timeout=6)
                return resp.status_code in [200, 204]
            except Exception as e:
                print(f"[CloudStorage] Error updating key {clean_key}: {e}")
                return False
        else:
            return self._local_update_fields(clean_key, fields)

    def delete_key(self, key_code: str) -> bool:
        """Delete a key from database and remove any device mapping linked to it"""
        clean_key = key_code.strip()
        key_id = self._format_key_id(clean_key)

        key_data = self.get_key(clean_key)
        hwid = key_data.get("hwid") if key_data else ""

        if self.is_cloud_enabled():
            try:
                url = self._get_url(f"keys/{key_id}")
                resp = requests.delete(url, timeout=6)
                if hwid:
                    dev_url = self._get_url(f"devices/{self._format_key_id(hwid)}")
                    requests.delete(dev_url, timeout=6)
                return resp.status_code in [200, 204]
            except Exception as e:
                print(f"[CloudStorage] Error deleting key {clean_key}: {e}")
                return False
        else:
            return self._local_delete_key(clean_key)

    def list_all_keys(self) -> List[dict]:
        """List all keys in database"""
        if self.is_cloud_enabled():
            try:
                url = self._get_url("keys")
                resp = requests.get(url, timeout=7)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict):
                        return list(data.values())
                    elif isinstance(data, list):
                        return [item for item in data if item is not None]
                return []
            except Exception as e:
                print(f"[CloudStorage] Error listing keys: {e}")
                return []
        else:
            return self._local_list_all_keys()

    def get_key_by_hwid(self, hwid: str) -> Optional[dict]:
        """Find an active key or license matching a specific HWID"""
        clean_hwid = hwid.strip()
        if not clean_hwid:
            return None
        
        # 1. Search in all active keys for exact HWID match
        all_keys = self.list_all_keys()
        for k in all_keys:
            if k.get("hwid") and k.get("hwid").strip() == clean_hwid:
                if k.get("status") == "active":
                    return k

        # 2. Check cloud device direct map if available
        if self.is_cloud_enabled():
            try:
                url = self._get_url(f"devices/{self._format_key_id(clean_hwid)}")
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and data:
                        k_code = data.get("key")
                        main_key = self.get_key(k_code) if k_code else None
                        if main_key and main_key.get("status") == "active":
                            return data
                        else:
                            requests.delete(url, timeout=5)
            except Exception:
                pass
        else:
            db = self._load_local_db()
            dev_lic = db.get("_devices", {}).get(clean_hwid)
            if dev_lic:
                k_code = dev_lic.get("key")
                main_key = self._local_get_key(k_code) if k_code else None
                if main_key and main_key.get("status") == "active":
                    return dev_lic
                else:
                    if "_devices" in db and clean_hwid in db["_devices"]:
                        del db["_devices"][clean_hwid]
                        self._save_local_db(db)

        return None

    def save_device_license(self, hwid: str, key_data: dict) -> bool:
        """Saves a direct device license record for fast HWID lookup"""
        clean_hwid = self._format_key_id(hwid)
        if self.is_cloud_enabled():
            try:
                url = self._get_url(f"devices/{clean_hwid}")
                resp = requests.put(url, json=key_data, timeout=6)
                return resp.status_code in [200, 201, 204]
            except Exception:
                return False
        else:
            db = self._load_local_db()
            if "_devices" not in db:
                db["_devices"] = {}
            db["_devices"][hwid] = key_data
            self._save_local_db(db)
            return True

    # ==================== TRIAL OPERATIONS ====================

    def get_trial(self, hwid: str) -> Optional[dict]:
        """Fetch trial record for an HWID"""
        clean_hwid = self._format_key_id(hwid)
        if self.is_cloud_enabled():
            try:
                url = self._get_url(f"trials/{clean_hwid}")
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and data:
                        return data
                return None
            except Exception as e:
                print(f"[CloudStorage] Error fetching trial for {hwid}: {e}")
                return None
        else:
            db = self._load_local_db()
            trials = db.get("_trials", {})
            return trials.get(hwid)

    def save_trial(self, trial_data: dict) -> bool:
        """Save or update trial record for an HWID"""
        hwid = trial_data.get("hwid", "").strip()
        if not hwid:
            return False
        clean_hwid = self._format_key_id(hwid)

        if self.is_cloud_enabled():
            try:
                url = self._get_url(f"trials/{clean_hwid}")
                resp = requests.put(url, json=trial_data, timeout=6)
                return resp.status_code in [200, 201, 204]
            except Exception as e:
                print(f"[CloudStorage] Error saving trial: {e}")
                return False
        else:
            db = self._load_local_db()
            if "_trials" not in db:
                db["_trials"] = {}
            db["_trials"][hwid] = trial_data
            self._save_local_db(db)
            return True

    def update_trial_fields(self, hwid: str, fields: dict) -> bool:
        """Update specific fields of a trial (e.g. last_seen, expires_at)"""
        clean_hwid = self._format_key_id(hwid)
        if self.is_cloud_enabled():
            try:
                url = self._get_url(f"trials/{clean_hwid}")
                resp = requests.patch(url, json=fields, timeout=6)
                return resp.status_code in [200, 204]
            except Exception as e:
                return False
        else:
            db = self._load_local_db()
            if "_trials" in db and hwid in db["_trials"]:
                db["_trials"][hwid].update(fields)
                self._save_local_db(db)
                return True
            return False

    def delete_trial(self, hwid: str) -> bool:
        """Reset / delete trial record for an HWID (allows re-trial)"""
        clean_hwid = self._format_key_id(hwid)
        if self.is_cloud_enabled():
            try:
                url = self._get_url(f"trials/{clean_hwid}")
                resp = requests.delete(url, timeout=6)
                return resp.status_code in [200, 204]
            except Exception as e:
                return False
        else:
            db = self._load_local_db()
            if "_trials" in db and hwid in db["_trials"]:
                del db["_trials"][hwid]
                self._save_local_db(db)
                return True
            return False

    def list_all_trials(self) -> List[dict]:
        """List all registered device trials"""
        if self.is_cloud_enabled():
            try:
                url = self._get_url("trials")
                resp = requests.get(url, timeout=7)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict):
                        return list(data.values())
                    elif isinstance(data, list):
                        return [item for item in data if item is not None]
                return []
            except Exception:
                return []
        else:
            db = self._load_local_db()
            return list(db.get("_trials", {}).values())

    # ==================== LOCAL DB FALLBACK ====================

    def _load_local_db(self) -> dict:
        if os.path.exists(self.local_db_path):
            try:
                with open(self.local_db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_local_db(self, db: dict):
        try:
            with open(self.local_db_path, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def _local_get_key(self, key_code: str) -> Optional[dict]:
        db = self._load_local_db()
        return db.get(key_code)

    def _local_save_key(self, key_data: dict) -> bool:
        db = self._load_local_db()
        db[key_data["key"]] = key_data
        self._save_local_db(db)
        return True

    def _local_update_fields(self, key_code: str, fields: dict) -> bool:
        db = self._load_local_db()
        changed = False
        if key_code in db:
            db[key_code].update(fields)
            changed = True

        if "_devices" in db:
            for hwid, dev in db["_devices"].items():
                if dev.get("key") == key_code:
                    dev.update(fields)
                    changed = True

        if changed:
            self._save_local_db(db)
            return True
        return False

    def _local_delete_key(self, key_code: str) -> bool:
        db = self._load_local_db()
        changed = False
        if key_code in db:
            del db[key_code]
            changed = True

        if "_devices" in db:
            to_del = [hwid for hwid, dev in db["_devices"].items() if dev.get("key") == key_code]
            for hwid in to_del:
                del db["_devices"][hwid]
                changed = True

        if changed:
            self._save_local_db(db)
            return True
        return False

    def _local_list_all_keys(self) -> List[dict]:
        db = self._load_local_db()
        return [v for k, v in db.items() if not k.startswith("_")]
