import threading
from tkinter import messagebox

def open_manual_browser(app, frame):
    """
    Hàm xử lý khi người dùng bấm nút Mở Trình Duyệt.
    """
    acc_id = ""
    for acc in app.account_frames:
        if acc['frame'] == frame:
            acc_id = acc['id_entry'].get().strip()
            break
            
    if not acc_id:
        messagebox.showwarning("Cảnh báo", "Vui lòng nhập ID tài khoản trước khi mở trình duyệt!")
        return
    
    def _open():
        app.write_log(f"Đang chuẩn bị mở trình duyệt cho [{acc_id}]...")
        try:
            import undetected_chromedriver as uc
            import os
            import shutil
            from facebook_bot import DRIVER_INIT_LOCK, ACTIVE_DRIVERS
            
            options = uc.ChromeOptions()
            prefs = {
                "translate_whitelists": {"en": "vi", "zh": "vi", "fr": "vi", "es": "vi", "ko": "vi", "ja": "vi", "zh-CN": "vi", "zh-TW": "vi", "ru": "vi", "de": "vi", "th": "vi", "pt": "vi"},
                "translate": {"enabled": True}
            }
            options.add_experimental_option("prefs", prefs)
            options.add_argument("--lang=vi")
            profile_dir = os.path.join(os.getcwd(), 'profiles', acc_id)
            options.add_argument("--disable-notifications")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--remote-allow-origins=*")
            # Disable extensions that might interfere
            options.add_argument("--disable-extensions")
            
            # Tắt tính năng tự động cập nhật của Chrome
            options.add_argument("--disable-component-update")
            options.add_argument("--simulate-outdated-no-au='Tue, 31 Dec 2099 23:59:59 GMT'")
            
            with DRIVER_INIT_LOCK:
                if acc_id in ACTIVE_DRIVERS:
                    try:
                        ACTIVE_DRIVERS[acc_id].current_url
                        app.write_log(f"[{acc_id}] Trình duyệt đã được mở sẵn, không mở thêm!")
                        return
                    except Exception:
                        del ACTIVE_DRIVERS[acc_id]
                        
                try:
                    from cleaner import clean_chrome_cache, get_chrome_main_version
                    clean_chrome_cache(acc_id)
                    app.write_log(f"[{acc_id}] Đã dọn dẹp xong Cache rác. Đang mở Chrome (nếu trình duyệt chưa hiện ra, vui lòng chờ 1-2 phút để tải ngầm file cấu hình)...")
                    chrome_version = get_chrome_main_version()
                    driver = uc.Chrome(options=options, user_data_dir=profile_dir, version_main=chrome_version)
                except Exception as e:
                    err_str = str(e).lower()
                    if "user data directory is already in use" in err_str or "cannot connect to chrome" in err_str:
                        app.write_log(f"[{acc_id}] KHÔNG THỂ MỞ TRÌNH DUYỆT: Vui lòng nhấn nút 'Đóng Tất Cả Chrome' hoặc tắt các trình duyệt đang mở của tài khoản này!")
                        return
                    else:
                        app.write_log(f"[{acc_id}] Lỗi khởi tạo Chrome: Vui lòng kiểm tra lại đường truyền mạng hoặc khởi động lại phần mềm.")
                        raise e
                        
            # Ghi nhận driver này vào danh sách để chạy auto không mở thêm cửa sổ mới
            ACTIVE_DRIVERS[acc_id] = driver
            
            driver.get("https://facebook.com")
        except Exception as e:
            app.write_log(f"Lỗi mở trình duyệt: {e}")

    threading.Thread(target=_open, daemon=True).start()
