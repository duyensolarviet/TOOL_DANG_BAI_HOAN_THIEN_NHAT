import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import pyotp
import random
from cleaner import clean_chrome_cache
import threading
import shutil

ACTIVE_DRIVERS = {}
DRIVER_INIT_LOCK = threading.Lock()

class FacebookBot:
    def __init__(self, account, log_callback=None, stop_event=None):
        self.account = account
        self.log_callback = log_callback
        self.driver = None
        self.stop_event = stop_event

    def is_stopped(self):
        if self.stop_event and self.stop_event.is_set():
            return True
        return False

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def get_2fa_code(self, secret):
        if not secret:
            return ""
        try:
            secret = secret.replace(" ", "").upper()
            totp = pyotp.TOTP(secret)
            return totp.now()
        except Exception as e:
            self.log(f"[{self.account['id']}] Lỗi tạo 2FA: {e}")
            return ""

    def type_slowly(self, element, text):
        for char in text:
            if self.is_stopped():
                break
            if char == '\n':
                element.send_keys(Keys.SHIFT, Keys.ENTER)
            else:
                element.send_keys(char)
            time.sleep(random.uniform(0.02, 0.1))

    def run(self, video_path="", image_path=""):
        global ACTIVE_DRIVERS
        profile_dir = os.path.join(os.getcwd(), 'profiles', self.account['id'])
        os.makedirs(profile_dir, exist_ok=True)
        
        is_post_reel = self.account.get('is_post_reel', '0') == '1'
        is_post_video = self.account.get('is_post_video', '1') == '1'
        is_post_image = self.account.get('is_post_image', '0') == '1'
        
        media_path = ""
        if (is_post_video or is_post_reel) and video_path:
            media_path = video_path
        elif is_post_image and image_path:
            media_path = image_path
            
        has_desc = bool(self.account.get('description', ''))
        
        if not media_path and not has_desc:
            self.log(f"[{self.account['id']}] Không có video, ảnh hay nội dung nào được nhập. Bỏ qua.")
            return False
            
        self.is_reused_driver = False
        
        try:
            if self.account['id'] in ACTIVE_DRIVERS:
                self.driver = ACTIVE_DRIVERS[self.account['id']]
                try:
                    # Check if driver is still alive
                    self.driver.current_url
                    self.is_reused_driver = True
                    self.log(f"[{self.account['id']}] ĐÃ TÌM THẤY Chrome mở sẵn. Trực tiếp sử dụng cửa sổ này!")
                except Exception:
                    del ACTIVE_DRIVERS[self.account['id']]
                    self.driver = None
                    self.is_reused_driver = False
            
            if not getattr(self, 'is_reused_driver', False):
                lock_file = os.path.join(profile_dir, "SingletonLock")
                if os.path.exists(lock_file):
                    try:
                        os.remove(lock_file)
                    except:
                        pass
                
                options = uc.ChromeOptions()
                prefs = {
                    "translate_whitelists": {"en": "vi", "zh": "vi", "fr": "vi", "es": "vi", "ko": "vi", "ja": "vi", "zh-CN": "vi", "zh-TW": "vi", "ru": "vi", "de": "vi", "th": "vi", "pt": "vi"},
                    "translate": {"enabled": True}
                }
                options.add_experimental_option("prefs", prefs)
                options.add_argument("--lang=vi")
                options.add_argument("--disable-notifications")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--remote-allow-origins=*")
                options.add_argument("--disable-gpu")
                options.add_argument("--disk-cache-size=10485760")
                options.add_argument("--media-cache-size=10485760")
                
                # Tắt tính năng tự động cập nhật của Chrome
                options.add_argument("--disable-component-update")
                options.add_argument("--simulate-outdated-no-au='Tue, 31 Dec 2099 23:59:59 GMT'")
                with DRIVER_INIT_LOCK:
                    try:
                        clean_chrome_cache(self.account['id'])
                        self.log(f"[{self.account['id']}] Đã dọn dẹp xong Cache rác. Đang mở Chrome (nếu trình duyệt chưa hiện ra, vui lòng chờ 1-2 phút để tải ngầm file cấu hình)...")
                        from cleaner import get_chrome_main_version
                        chrome_version = get_chrome_main_version()
                        self.driver = uc.Chrome(options=options, user_data_dir=profile_dir, version_main=chrome_version)
                        ACTIVE_DRIVERS[self.account['id']] = self.driver
                    except Exception as e:
                        err_str = str(e).lower()
                        if "user data directory is already in use" in err_str or "cannot connect to chrome" in err_str:
                            self.log(f"[{self.account['id']}] LỖI NGHIÊM TRỌNG: Profile đang bị khóa hoặc Chrome không thể khởi động! Lỗi gốc: {e}")
                            return
                        else:
                            self.log(f"[{self.account['id']}] Lỗi khởi tạo Chrome: {e}")
                            raise e
                
            self.driver.set_page_load_timeout(60)
            
            is_post_facebook = self.account.get("is_post_facebook", "1") == "1"
            if is_post_facebook:
                if self.login():
                    is_canhan = self.account.get('is_canhan', '1') == '1'
                    canhan_name = self.account.get('canhan_name', self.account.get('canhan_link', ''))
                    is_page = self.account.get('is_page', '0') == '1'
                    page_names = self.account.get('page_names', self.account.get('page_links', []))
                
                    group_links_raw = self.account.get('group_links', '')
                    group_links = [l.strip() for l in group_links_raw.split('\n') if l.strip()]
                    is_group_profile = self.account.get('is_group_profile', '0') == '1'
                    is_group_page = self.account.get('is_group_page', '0') == '1'
                
                    is_post_reel = self.account.get('is_post_reel', '0') == '1'
                    is_post_video = self.account.get('is_post_video', '1') == '1'
                    is_post_image = self.account.get('is_post_image', '0') == '1'

                    is_canhan_reels = self.account.get('is_canhan_reels', '0') == '1'
                    should_process_profile = is_canhan or is_canhan_reels or (is_group_profile and group_links)
                    should_process_page = is_page or (is_group_page and group_links)

                    if not should_process_profile and not (should_process_page and page_names):
                        self.log(f"[{self.account['id']}] Không chọn Đăng Tường/Reels Cá Nhân/Đăng Nhóm hay Page. Bỏ qua media.")
                    else:
                        if should_process_profile:
                            switched = True
                            if canhan_name:
                                self.log(f"[{self.account['id']}] Chuẩn bị profile: {canhan_name}")
                                switched = self.switch_profile(canhan_name)
                            else:
                                self.log(f"[{self.account['id']}] Không nhập Tên Profile. Sẽ sử dụng Profile mặc định hiện tại.")

                            if switched:
                                self.interact_newsfeed()
                                
                                # Xử lý Đăng Reels FB Trang Cá Nhân (độc lập)
                                if is_canhan_reels and video_path:
                                    try:
                                        from facebook_personal_reels_poster import upload_personal_reel
                                        upload_personal_reel(self.driver, self.account, self.log_callback, video_path)
                                        
                                        if self.account.get('cmt_fb', '0') == '1' and self.account.get('cmt_fb_canhan', '1') == '1':
                                            cmt_text = self.account.get('cmt_text', '')
                                            if cmt_text:
                                                try:
                                                    from facebook_comment_personal import comment_on_personal_post
                                                    comment_on_personal_post(self.driver, self.log, cmt_text)
                                                except Exception as e:
                                                    self.log(f"[{self.account['id']}] Lỗi CMT cá nhân reels: {e}")
                                    except Exception as e:
                                        self.log(f"[{self.account.get('id')}] Lỗi tải module Reels Cá Nhân: {e}")

                                # Xử lý Đăng Tường Cá Nhân (độc lập)
                                if is_canhan:
                                    posted_profile = False
                                    if is_post_reel and video_path:
                                        self.upload_reel(video_path, log_name="Trang Cá Nhân (Reels)")
                                        posted_profile = True
                                    elif is_post_video and video_path:
                                        self.upload_post(media_path, log_name="Trang Cá Nhân (Video)")
                                        posted_profile = True
                                    elif is_post_image and (image_path or self.account.get('description')):
                                        self.upload_post(media_path, log_name="Trang Cá Nhân")
                                        posted_profile = True
                                        
                                    if posted_profile and self.account.get('cmt_fb', '0') == '1' and self.account.get('cmt_fb_canhan', '1') == '1':
                                        cmt_text = self.account.get('cmt_text', '')
                                        if cmt_text:
                                            try:
                                                from facebook_comment_personal import comment_on_personal_post
                                                comment_on_personal_post(self.driver, self.log, cmt_text)
                                            except Exception as e:
                                                self.log(f"[{self.account['id']}] Lỗi CMT cá nhân: {e}")
                                    
                                if is_group_profile and group_links:
                                    self.log(f"[{self.account['id']}] Bắt đầu Đăng Nhóm bằng Cá nhân ({len(group_links)} nhóm)...")
                                    self.post_to_groups(group_links, media_path)
                            
                        if should_process_page:
                            for idx, name in enumerate(page_names):
                                if self.is_stopped():
                                    self.log(f"[{self.account['id']}] Nhận tín hiệu dừng khi đang chuẩn bị đăng Page.")
                                    break
                                if name:
                                    self.log(f"[{self.account['id']}] Chuẩn bị profile Page: {name}")
                                    if self.switch_profile(name):
                                        self.interact_newsfeed()
                                    
                                        if is_page:
                                            posted_page = False
                                            if is_post_reel and video_path:
                                                self.upload_reel(video_path, log_name=f"Page Reels {idx+1}: {name}")
                                                posted_page = True
                                            elif is_post_video and video_path:
                                                self.upload_post(media_path, log_name=f"Page Video {idx+1}: {name}")
                                                posted_page = True
                                            elif is_post_image and (image_path or self.account.get('description')):
                                                self.upload_post(media_path, log_name=f"Page Ảnh {idx+1}: {name}")
                                                posted_page = True
                                                
                                            if posted_page and self.account.get('cmt_fb', '0') == '1' and self.account.get('cmt_fb_page', '1') == '1':
                                                cmt_text = self.account.get('cmt_text', '')
                                                if cmt_text:
                                                    try:
                                                        from facebook_comment_page import comment_on_page_post
                                                        comment_on_page_post(self.driver, self.log, cmt_text)
                                                    except Exception as e:
                                                        self.log(f"[{self.account['id']}] Lỗi CMT page: {e}")
                                            
                                        if is_group_page and group_links:
                                            self.log(f"[{self.account['id']}] Bắt đầu Đăng Nhóm bằng Page '{name}' ({len(group_links)} nhóm)...")
                                            self.post_to_groups(group_links, media_path)
                else:
                    self.log(f"[{self.account['id']}] Hủy bỏ upload video vì đăng nhập thất bại.")
                
            else:
                self.log(f"[{self.account['id']}] Bỏ qua Facebook (tính năng Đăng Facebook đã tắt).")

            is_post_zalo = self.account.get('is_post_zalo', '0') == '1'
            if is_post_zalo and video_path:
                self.upload_zalo_video(video_path)
                
            is_post_tiktok = self.account.get('is_post_tiktok', '0') == '1'
            media_path_tiktok = video_path if video_path else image_path
            if is_post_tiktok and media_path_tiktok:
                self.upload_tiktok_video(media_path_tiktok)
                
            is_post_yt = self.account.get('is_post_yt', '0') == '1'
            is_yt_interact = self.account.get('is_yt_interact', '0') == '1'
            media_path_yt = video_path if video_path else image_path
            if is_post_yt or is_yt_interact:
                try:
                    from youtube_bot import YouTubeBot
                    yt_bot = YouTubeBot(self.driver, self.account, self.log_callback, self.stop_event, self.type_slowly)
                    if is_yt_interact:
                        yt_bot.interact_newsfeed()
                    if is_post_yt and media_path_yt:
                        yt_bot.upload_youtube_video(media_path_yt)
                except Exception as e:
                    self.log(f"[{self.account.get('id', 'Unknown')}] Lỗi tải YouTubeBot: {e}")
                    
            is_post_ig = self.account.get('is_post_ig', '0') == '1'
            if is_post_ig and (video_path or image_path):
                try:
                    from instagram_bot import InstagramBot
                    ig_bot = InstagramBot(self.driver, self.account, self.log_callback, self.stop_event, self.type_slowly)
                    ig_bot.upload_post(video_path, image_path)
                except Exception as e:
                    self.log(f"[{self.account.get('id', 'Unknown')}] Lỗi tải InstagramBot: {e}")
                    
            is_post_threads = self.account.get('is_post_threads', '0') == '1'
            if is_post_threads and (video_path or image_path or self.account.get('description')):
                try:
                    from threads_bot import ThreadsBot
                    threads_bot = ThreadsBot(self.driver, self.account, self.log_callback, self.stop_event, self.type_slowly)
                    threads_bot.upload_post(video_path, image_path)
                except Exception as e:
                    self.log(f"[{self.account.get('id', 'Unknown')}] Lỗi tải ThreadsBot: {e}")
                    
            return True
        except Exception as e:
            self.log(f"[{self.account['id']}] Lỗi: {e}")
        finally:
            pass
            
    def switch_profile(self, target_name):
        self.log(f"[{self.account['id']}] Bắt đầu kiểm tra Profile/Page: {target_name}...")
        self.driver.get("https://www.facebook.com/")
        time.sleep(4)
        self.driver.refresh()
        time.sleep(4)
        self.driver.refresh()
        time.sleep(4)
        
        def click_avatar():
            clicked = False
            try:
                account_btn = self.driver.find_element(By.XPATH, "//div[@role='button' and (contains(@aria-label, 'Tài khoản') or contains(@aria-label, 'Account') or contains(@aria-label, 'Trang cá nhân'))]")
                self.driver.execute_script("arguments[0].click();", account_btn)
                clicked = True
            except Exception as outer_e:
                self.log(f"[DEBUG Outer Exception] {outer_e}")
                import traceback
                traceback.print_exc()
                
            if not clicked:
                try:
                    banner_images = self.driver.find_elements(By.XPATH, "//div[@role='navigation' or @role='banner']//*[local-name()='image']")
                    if banner_images:
                        self.driver.execute_script("""
                            var el = arguments[0];
                            var btn = el.closest('div[role="button"]') || el;
                            btn.click();
                        """, banner_images[-1])
                        clicked = True
                except:
                    pass
            return clicked

        def find_and_click_name(attempt_idx):
            elements = self.driver.find_elements(By.XPATH, "//div[@role='dialog' or @role='menu']//*[self::span[@dir='auto'] or self::span or self::div[@role='button'] or self::div[@role='radio'] or self::div[@role='link']]")
            if not elements:
                elements = self.driver.find_elements(By.XPATH, "//span[@dir='auto'] | //span | //div[@role='button']")
                
            matches = []
            target_lower = target_name.strip().lower()
            for t in elements:
                try:
                    if t.is_displayed():
                        text = t.text.strip().lower()
                        # Khớp chính xác hoặc khớp tương đối (có kèm thông báo)
                        if target_lower == text or (target_lower in text and len(text) < len(target_lower) + 20):
                            matches.append(t)
                except:
                    pass
                    
            if matches:
                # Thử click vào kết quả thứ attempt_idx, nếu hết thì click cái cuối
                idx = min(attempt_idx, len(matches) - 1)
                t = matches[idx]
                try:
                    # Dùng ActionChains giả lập click chuột thật để xuyên qua lớp chống bot của React
                    from selenium.webdriver.common.action_chains import ActionChains
                    try:
                        ActionChains(self.driver).move_to_element(t).click().perform()
                    except:
                        pass
                        
                    # Backup bằng JS Events Lifecycle
                    self.driver.execute_script("""
                        var el = arguments[0];
                        var btn = el.closest('div[role="button"]') || el.closest('div[role="radio"]') || el.closest('div[role="menuitem"]') || el.closest('div[role="link"]') || el;
                        var events = ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'];
                        events.forEach(function(ev) {
                            btn.dispatchEvent(new MouseEvent(ev, {bubbles: true, cancelable: true, view: window}));
                            el.dispatchEvent(new MouseEvent(ev, {bubbles: true, cancelable: true, view: window}));
                        });
                    """, t)
                    return True
                except:
                    pass
            return False

        MAX_RETRIES = 5
        click_attempt = 0
        # Vòng lặp tối đa 5 lần để xác nhận (Mở menu -> Xác nhận -> Nếu sai thì Đổi -> Mở menu -> Xác nhận)
        for attempt in range(MAX_RETRIES):
            self.log(f"[{self.account['id']}] Bấm vào Avatar để kiểm tra (Lần {attempt + 1})...")
            if not click_avatar():
                self.log(f"[{self.account['id']}] Lỗi: Không thể tìm thấy nút Avatar Tài khoản!")
                return False
                
            time.sleep(4)
            
            # Kiểm tra tên tài khoản đang kích hoạt (Thường nằm ở phần tử có text đầu tiên trong menu)
            self.log(f"[{self.account['id']}] Xác minh tên tài khoản hiện tại...")
            active_correct = False
            active_btn = None
            try:
                active_profile_divs = self.driver.find_elements(By.XPATH, "//div[@role='dialog' or @role='menu']//*[self::div[@role='button'] or self::span[@dir='auto'] or self::h1]")
                for div in active_profile_divs:
                    if div.is_displayed():
                        text = div.text.strip().lower()
                        if not text or len(text) < 2 or "đóng" in text or "close" in text or text in ["tài khoản", "account", "menu", "chuyển trang cá nhân", "trang cá nhân"]:
                            continue # Bỏ qua các nút hệ thống và tiêu đề menu
                            
                        # Đây chính là tên tài khoản đầu tiên hiện ra (tức là Active Profile)
                        target_lower = target_name.strip().lower()
                        if target_lower == text or (target_lower in text and len(text) < len(target_lower) + 20):
                            active_correct = True
                        active_btn = div
                        break # Chỉ kiểm tra thẻ tên hợp lệ đầu tiên
            except Exception as outer_e:
                self.log(f"[DEBUG Outer Exception] {outer_e}")
                import traceback
                traceback.print_exc()
                
            if active_correct:
                self.log(f"[{self.account['id']}] Đã xác nhận: TRÚNG KHỚP trang '{target_name}'.")
                # Bấm vào chính tài khoản đó để đóng menu
                try:
                    if active_btn:
                        self.driver.execute_script("arguments[0].click();", active_btn)
                    else:
                        click_avatar() # Click lại để đóng
                except:
                    pass
                time.sleep(5)
                return True
                
            if attempt == MAX_RETRIES - 1:
                self.log(f"[{self.account['id']}] Chuyển đổi thất bại (Tên không khớp sau {MAX_RETRIES} lần thử chọn).")
                return False
                
            # Nếu chưa đúng, tiến hành chọn tài khoản
            self.log(f"[{self.account['id']}] Chưa đúng tài khoản, tìm '{target_name}' trong menu (Kết quả #{click_attempt + 1})...")
            target_found = find_and_click_name(click_attempt)
            
            if not target_found:
                self.log(f"[{self.account['id']}] Thử mở rộng 'Xem tất cả trang cá nhân'...")
                try:
                    see_all_btns = self.driver.find_elements(By.XPATH, "//div[@role='dialog' or @role='menu']//div[@role='button'] | //div[@role='button'] | //div[@aria-label='Xem tất cả trang cá nhân']")
                    for btn in see_all_btns:
                        try:
                            if btn.is_displayed():
                                text = btn.text.strip().lower()
                                aria = (btn.get_attribute("aria-label") or "").strip().lower()
                                if "xem tất cả" in text or "see all" in text or "xem tất cả" in aria or "see all" in aria:
                                    self.driver.execute_script("arguments[0].click();", btn)
                                    time.sleep(4)
                                    break
                        except:
                            pass
                except:
                    pass
                
                target_found = find_and_click_name(click_attempt)
                
            if target_found:
                self.log(f"[{self.account['id']}] Đã click chọn '{target_name}'. Đang đợi tải lại trang...")
                time.sleep(12)
                click_attempt += 1
            else:
                self.log(f"[{self.account['id']}] Không tìm thấy Profile/Page nào có tên '{target_name}'. Bỏ qua.")
                return False
                
        return False


    def interact_newsfeed(self):
        if self.account.get('interact_nf', '0') != '1':
            return
            
        import time
        import random
        from datetime import datetime
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains

        def log_msg(message):
            now = datetime.now().strftime("%H:%M:%S")
            full_msg = f"[{now}] [{self.account['id']}] {message}"
            print(full_msg)
            if self.log_callback:
                self.log_callback(full_msg)

        def automation_newfeed_fb(driver, max_tym=4, max_cmt=2, timeout_phut=5, text_cmt="Tuyệt vời quá!", react_type="like"):
            # BƯỚC 1: Truy cập trang chủ Facebook
            log_msg(f"[B1] Truy cập Facebook... Mục tiêu: {max_tym} Tym ({react_type}) | {max_cmt} Cmt | {timeout_phut} phút")
            driver.get("https://www.facebook.com/")
            time.sleep(5)

            count_tym = 0
            count_cmt = 0
            start_time = time.time()

            def detect_is_ad_post(container):
                if not container:
                    return False, ""
                
                # 1. Quét TOÀN BỘ nội dung văn bản trong container/dialog bằng JavaScript
                try:
                    raw_text = driver.execute_script("return (arguments[0].innerText || '');", container).lower()
                    ad_keywords = [
                        "được tài trợ", "sponsored", "tìm hiểu thêm", "xem chi tiết", "gửi tin nhắn", 
                        "mua ngay", "nhận ưu đãi", "đăng ký ngay", "đăng ký", "cài đặt ngay", 
                        "tải xuống", "áp dụng ngay", "nhận báo giá", "báo giá", "liên hệ với chúng tôi", 
                        "gửi tin nhắn qua whatsapp", "mẫu", "learn more", "shop now", "sign up", 
                        "send message", "get offer", "download", "install now", "apply now", 
                        "book now", "contact us", "get quote", "see details", "paid partnership"
                    ]
                    for kw in ad_keywords:
                        if kw in raw_text:
                            return True, f"Nội dung chứa từ khóa quảng cáo '{kw}'"
                except: pass

                # 2. Quét trực tiếp các nút kêu gọi hành động (CTA Buttons)
                try:
                    cta_buttons = container.find_elements(
                        By.XPATH, 
                        ".//*[contains(text(), 'Tìm hiểu thêm') or contains(text(), 'Xem chi tiết') or contains(text(), 'Gửi tin nhắn') or contains(text(), 'Mua ngay') or contains(text(), 'Đăng ký') or contains(text(), 'Nhận ưu đãi') or contains(text(), 'Learn more') or contains(text(), 'Shop now') or contains(text(), 'Sign up') or contains(text(), 'Send message') or contains(text(), 'Get offer') or contains(text(), 'Được tài trợ') or contains(text(), 'Sponsored')]"
                    )
                    if cta_buttons:
                        return True, "Chứa nút hành động quảng cáo (CTA)"
                except: pass

                # 3. Quét mã SVG quảng cáo #SvgT55
                try:
                    svg_ads = container.find_elements(By.XPATH, ".//*[local-name()='use'][@*[local-name()='href']='#SvgT55' or @*[local-name()='href']='SvgT55']")
                    if svg_ads:
                        return True, "Khớp mã SVG #SvgT55"
                except: pass

                # 4. Quét liên kết quảng cáo Facebook (/ads/, about_this_ad, fbclid)
                try:
                    ad_links = container.find_elements(By.XPATH, ".//a[contains(@href, '/ads/about/') or contains(@href, 'about_this_ad') or contains(@href, 'ad_id=') or contains(@href, 'fbclid=') or contains(@href, '/ads/')]")
                    if ad_links:
                        return True, "Chứa liên kết quảng cáo (/ads/)"
                except: pass

                return False, ""

            # Vòng lặp
            while True:
                if self.is_stopped() or (count_tym >= max_tym and count_cmt >= max_cmt):
                    log_msg("[Hoàn thành] Đã đạt đủ chỉ tiêu tương tác hoặc nhận lệnh dừng.")
                    break
                if (time.time() - start_time) > (timeout_phut * 60):
                    log_msg(f"[Hoàn thành] Hết thời gian. Kết quả: {count_tym} Tym, {count_cmt} Cmt.")
                    break

                processed_any_this_round = False
                
                # BƯỚC 2: Cuộn trang chậm như người thật và tìm tới bài viết dạng xpath
                story_messages = driver.find_elements(By.XPATH, "//div[@data-ad-rendering-role='story_message']")
                
                for story in story_messages:
                    if self.is_stopped() or (count_tym >= max_tym and count_cmt >= max_cmt):
                        break
                        
                    try:
                        # Đi ngược lên để tìm thẻ chứa toàn bộ bài viết (post container)
                        try:
                            post_container = story.find_element(By.XPATH, "./ancestor::div[@role='article' or @aria-posinset or @data-pagelet][1]")
                        except:
                            # Fallback nếu không thấy container rõ ràng, lùi 6 cấp
                            post_container = story.find_element(By.XPATH, "./ancestor::div[6]")
                            
                        # Nếu bài này đã xử lý rồi thì bỏ qua
                        if post_container.get_attribute("data-processed") == "true":
                            continue
                            
                        processed_any_this_round = True
                        
                        # Cuộn bài viết ra giữa màn hình
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", story)
                        time.sleep(2)
                        
                        # BƯỚC 9: Bỏ qua bài viết quảng cáo / Được tài trợ
                        is_sponsored, sponsored_reason = detect_is_ad_post(post_container)

                        if is_sponsored:
                            log_msg(f"[Bỏ qua quảng cáo] Phát hiện bài viết 'Được tài trợ' ({sponsored_reason}) -> Đang cuộn chậm lướt qua để tìm bài viết thật...")
                            driver.execute_script("arguments[0].setAttribute('data-processed', 'true');", post_container)
                            # Cuộn trang từ từ như người dùng thật lướt qua quảng cáo
                            driver.execute_script("window.scrollBy({top: 450, behavior: 'smooth'});")
                            time.sleep(random.uniform(2.5, 3.5))
                            continue

                        co_tuong_tac = False

                        # BƯỚC 3: Click vào nút like và thả cảm xúc
                        if count_tym < max_tym:
                            like_btn = None
                            try:
                                like_btn = post_container.find_element(By.XPATH, ".//div[@data-ad-rendering-role='like_button']/ancestor::div[@role='button'][1]")
                            except: pass
                            
                            if like_btn:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", like_btn)
                                time.sleep(1)
                                
                                log_msg(f"[Feed] Tìm thấy nút Like. Đang di chuột để chọn cảm xúc ({react_type})...")
                                
                                # Di chuyển chuột thả cảm xúc bằng Javascript (đáng tin cậy hơn trên Facebook)
                                driver.execute_script("""
                                    var ev1 = new MouseEvent('mouseover', {bubbles: true});
                                    var ev2 = new MouseEvent('mouseenter', {bubbles: true});
                                    arguments[0].dispatchEvent(ev1);
                                    arguments[0].dispatchEvent(ev2);
                                """, like_btn)
                                
                                try:
                                    ActionChains(driver).move_to_element(like_btn).pause(2).perform()
                                except: pass
                                time.sleep(2)
                                
                                # Tìm cảm xúc tương ứng trong khay
                                if react_type == 'love':
                                    reaction_xpath = "//div[@aria-label='Yêu thích' or @aria-label='Love' or @aria-label='Tym']"
                                elif react_type == 'haha':
                                    reaction_xpath = "//div[@aria-label='Haha']"
                                elif react_type == 'wow':
                                    reaction_xpath = "//div[@aria-label='Wow']"
                                elif react_type == 'sad':
                                    reaction_xpath = "//div[@aria-label='Buồn' or @aria-label='Sad']"
                                elif react_type == 'angry':
                                    reaction_xpath = "//div[@aria-label='Phẫn nộ' or @aria-label='Angry']"
                                elif react_type == 'care':
                                    reaction_xpath = "//div[@aria-label='Thương thương' or @aria-label='Care']"
                                else:
                                    reaction_xpath = "//div[@aria-label='Thích' or @aria-label='Like']"
                                    
                                reactions = driver.find_elements(By.XPATH, reaction_xpath)
                                if reactions:
                                    log_msg(f"[Feed] Đã tìm thấy biểu tượng {react_type}, đang click chọn...")
                                    try:
                                        ActionChains(driver).move_to_element(reactions[-1]).click().perform()
                                    except: pass
                                    try:
                                        # Kích hoạt thêm bằng JS MouseEvent để chắc chắn ăn click trên Facebook
                                        driver.execute_script("""
                                            var ev = new MouseEvent('click', {bubbles: true, cancelable: true, view: window});
                                            arguments[0].dispatchEvent(ev);
                                            arguments[0].click();
                                        """, reactions[-1])
                                    except: pass
                                else:
                                    log_msg(f"[Feed] Không thấy khay cảm xúc, tiến hành click nút Like thông thường...")
                                    try:
                                        ActionChains(driver).move_to_element(like_btn).click().perform()
                                    except: pass
                                    try:
                                        driver.execute_script("arguments[0].click();", like_btn)
                                    except: pass
                                    
                                time.sleep(1.5)
                                log_msg(f"[Thành công] Đã thả cảm xúc ({react_type}) bài viết ({count_tym+1}/{max_tym})")
                                count_tym += 1
                                co_tuong_tac = True
                                
                        # BƯỚC 4: Comment luôn vào bài viết
                        if count_cmt < max_cmt:
                            cmt_btn = None
                            try:
                                cmt_btn = post_container.find_element(By.XPATH, ".//div[@data-ad-rendering-role='comment_button']/ancestor::div[@role='button'][1]")
                            except: pass
                            
                            if cmt_btn:
                                log_msg("[Feed] Tìm thấy nút Bình luận. Đang click mở form...")
                                driver.execute_script("arguments[0].click();", cmt_btn)
                                time.sleep(2)
                                
                                # KIỂM TRA LẠI POPUP / MODAL VỪA MỞ RA
                                is_modal_ad = False
                                modal_ad_reason = ""
                                try:
                                    dialogs = driver.find_elements(By.XPATH, "//div[@role='dialog']")
                                    if dialogs:
                                        is_modal_ad, modal_ad_reason = detect_is_ad_post(dialogs[-1])
                                except: pass
                                
                                if is_modal_ad:
                                    log_msg(f"[Bỏ qua quảng cáo] Phát hiện popup bình luận là bài viết Quảng cáo ({modal_ad_reason}) -> Đóng popup ngay và không bình luận!")
                                    # Đóng modal
                                    try:
                                        close_btns = driver.find_elements(By.XPATH, "//div[@role='dialog']//div[@role='button' and (@aria-label='Đóng' or @aria-label='Close')] | //div[@role='dialog']//div[@role='button'][.//*[local-name()='svg']]")
                                        for cb in close_btns:
                                            if cb.is_displayed():
                                                driver.execute_script("arguments[0].click();", cb)
                                                break
                                    except:
                                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                                    time.sleep(1.5)
                                    driver.execute_script("window.scrollBy({top: 450, behavior: 'smooth'});")
                                    time.sleep(2.5)
                                    continue
                                
                                # Viết nội dung đã có sẵn vào ô
                                log_msg("[Feed] Bắt đầu gõ nội dung bình luận...")
                                active_el = driver.switch_to.active_element
                                for char in text_cmt:
                                    active_el.send_keys(char)
                                    time.sleep(random.uniform(0.05, 0.15))
                                time.sleep(0.5)
                                
                                # BƯỚC 5: Click vào nút Đăng bình luận
                                post_cmt_btn = None
                                try:
                                    post_cmt_btn = post_container.find_element(By.XPATH, ".//div[@role='button' and (contains(@aria-label, 'Đăng bình luận') or contains(@aria-label, 'Comment') or contains(@aria-label, 'Post'))]")
                                except: pass
                                
                                if post_cmt_btn:
                                    log_msg("[Feed] Click nút Gửi bình luận...")
                                    driver.execute_script("arguments[0].click();", post_cmt_btn)
                                else:
                                    log_msg("[Feed] Bấm phím Enter để gửi bình luận...")
                                    active_el.send_keys(Keys.ENTER)
                                    
                                time.sleep(3)
                                log_msg(f"[Thành công] Đã bình luận bài viết ({count_cmt+1}/{max_cmt})")
                                count_cmt += 1
                                co_tuong_tac = True

                        if not co_tuong_tac:
                            log_msg("[Feed] Bỏ qua bài viết (Không tìm thấy nút Thích/Bình luận hợp lệ)")

                        # BƯỚC 6: Tắt bài viết bằng nút X trên màn hình
                        close_svgs = driver.find_elements(By.XPATH, "//*[local-name()='svg' and ./*[local-name()='path' and starts-with(@d, 'M19.884')]]")
                        for svg in close_svgs:
                            try:
                                parent_btn = svg.find_element(By.XPATH, "./ancestor::div[@role='button'][1] | .")
                                driver.execute_script("arguments[0].click();", parent_btn)
                                time.sleep(1)
                            except: pass

                        # BƯỚC 7: Ấn vào nút rời trang
                        leave_btns = driver.find_elements(By.XPATH, "//div[@aria-label='Rời khỏi Trang' and @role='button']")
                        for lb in leave_btns:
                            try:
                                driver.execute_script("arguments[0].click();", lb)
                                time.sleep(1)
                            except: pass

                        # Đánh dấu đã xử lý
                        driver.execute_script("arguments[0].setAttribute('data-processed', 'true');", post_container)
                        
                    except Exception as e_post:
                        log_msg(f"[Feed] Lỗi xử lý bài, bỏ qua...")
                        try:
                            driver.execute_script("arguments[0].setAttribute('data-processed', 'true');", post_container)
                        except: pass
                        continue
                        
                # BƯỚC 8: Cuộn trang và lặp lại
                if not processed_any_this_round:
                    # Cuộn mạnh xuống dưới cùng bằng JS thay vì phím PAGE_DOWN để đảm bảo kích hoạt lazy-load
                    driver.execute_script("window.scrollBy(0, 1500);")
                    if story_messages:
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'end'});", story_messages[-1])
                        except: pass
                    time.sleep(3)

        # Đọc cấu hình
        try:
            so_phut_max = int(self.account.get('nf_time', '60')) / 60.0
        except Exception:
            so_phut_max = 1.0
        try:
            so_cam_xuc_max = int(self.account.get('nf_react_count', '4'))
        except Exception:
            so_cam_xuc_max = 4
        try:
            so_binh_luan_max = int(self.account.get('nf_cmt_count', '2'))
        except Exception:
            so_binh_luan_max = 2

        nf_cmts_str = self.account.get('nf_cmts', '').replace('|', '\n')
        nf_cmts = [c.strip() for c in nf_cmts_str.split('\n') if c.strip()]
        text_cmt = random.choice(nf_cmts) if nf_cmts else "Tuyệt vời quá!"

        # Kiểm tra nếu người dùng không tích Bật bình luận
        if self.account.get('nf_enable_cmt', '0') != '1':
            so_binh_luan_max = 0

        # Xác định loại cảm xúc người dùng đã cài đặt
        react_type = 'like'
        has_reaction_checked = False
        if self.account.get('nf_love', '0') == '1':
            react_type = 'love'
            has_reaction_checked = True
        elif self.account.get('nf_haha', '0') == '1':
            react_type = 'haha'
            has_reaction_checked = True
        elif self.account.get('nf_like', '0') == '1':
            react_type = 'like'
            has_reaction_checked = True
        elif self.account.get('nf_rand', '0') == '1':
            react_type = random.choice(['like', 'love', 'haha', 'wow', 'sad', 'angry', 'care'])
            has_reaction_checked = True
            
        # Nếu không có tích chọn cảm xúc nào, set max_tym = 0 để vô hiệu hoá tính năng Like
        if not has_reaction_checked:
            so_cam_xuc_max = 0

        if so_cam_xuc_max > 0 or so_binh_luan_max > 0:
            automation_newfeed_fb(
                self.driver,
                max_tym=so_cam_xuc_max,
                max_cmt=so_binh_luan_max,
                timeout_phut=so_phut_max,
                text_cmt=text_cmt,
                react_type=react_type
            )
    def login(self):
        self.log(f"[{self.account['id']}] Đang mở Facebook...")
        self.driver.get("https://www.facebook.com/")
        time.sleep(4)
        self.driver.refresh()
        time.sleep(4)
        self.driver.refresh()
        time.sleep(4)
        
        try:
            # Chờ tối đa 5 giây xem có ô nhập email/pass không.
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='email' or @name='email'] | //input[@id='pass' or @name='pass']"))
            )
        except:
            current_url = self.driver.current_url.lower()
            has_2fa_input = len(self.driver.find_elements(By.XPATH, "//input[@id='approvals_code' or @name='approvals_code']")) > 0
            
            if "checkpoint" in current_url or "two_step_verification" in current_url or has_2fa_input:
                self.log(f"[{self.account['id']}] Đang kẹt ở bước 2FA/Checkpoint...")
                # Đi tiếp xuống dưới để xử lý 2FA
            else:
                self.log(f"[{self.account['id']}] Đã đăng nhập từ trước!")
                return True

        self.log(f"[{self.account['id']}] Bắt đầu đăng nhập...")
        
        # Thử tắt popup cookies nếu có
        try:
            cookie_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Allow all cookies') or contains(text(), 'Cho phép') or contains(text(), 'Đồng ý')]")
            cookie_btn.click()
            time.sleep(2)
        except:
            pass
        try:
            # Nếu thấy form đăng nhập thì mới điền
            try:
                email_field = self.driver.find_element(By.XPATH, "//input[@id='email' or @name='email']")
                self.type_slowly(email_field, self.account['id'])
                time.sleep(random.uniform(0.5, 1.5))
                
                pass_field = self.driver.find_element(By.XPATH, "//input[@id='pass' or @name='pass']")
                self.type_slowly(pass_field, self.account['password'])
                time.sleep(random.uniform(0.5, 1.0))
                
                # Tìm nút đăng nhập bằng nhiều selector mở rộng
                login_selectors = [
                    "//button[@name='login']",
                    "//button[@type='submit']",
                    "//div[@role='none' or @role='button']//span[text()='Log in' or text()='Đăng nhập']",
                    "//span[text()='Log in' or text()='Đăng nhập']"
                ]
                
                login_btn = None
                for sel in login_selectors:
                    try:
                        btn = self.driver.find_element(By.XPATH, sel)
                        if btn.is_displayed():
                            login_btn = btn
                            break
                    except:
                        pass
                        
                if login_btn:
                    login_btn.click()
                else:
                    self.log(f"[{self.account['id']}] Không tìm thấy nút đăng nhập, thử dùng phím Enter...")
                    pass_field.send_keys(Keys.ENTER)
                
                time.sleep(5) 
            except Exception as e:
                pass # Bỏ qua bước nhập email/pass nếu không thấy form (có thể đang ở checkpoint)
            
            current_url = self.driver.current_url.lower()
            has_2fa_input = len(self.driver.find_elements(By.XPATH, "//input[@id='approvals_code' or @name='approvals_code']")) > 0
            if "checkpoint" in current_url or "two_step_verification" in current_url or has_2fa_input:
                self.log(f"[{self.account['id']}] Yêu cầu 2FA, đang lấy mã...")
                code = self.get_2fa_code(self.account.get('two_fa', ''))
                if code:
                    self.log(f"[{self.account['id']}] Mã 2FA tạo được: {code}")
                    try:
                        two_fa_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//input[@id='approvals_code' or @type='text' or @type='number']"))
                        )
                        self.type_slowly(two_fa_input, code)
                        
                        submit_btn = self.driver.find_element(By.XPATH, "//button[@id='checkpointSubmitButton' or @type='submit' or @name='submit[Continue]' or @name='submit[SubmitCode]']")
                        submit_btn.click()
                        time.sleep(5)
                        
                        for _ in range(3):
                            try:
                                btn = self.driver.find_element(By.XPATH, "//button[@id='checkpointSubmitButton' or @type='submit' or @name='submit[Continue]']")
                                btn.click()
                                time.sleep(3)
                            except:
                                break
                    except Exception as e:
                        self.log(f"[{self.account['id']}] Lỗi khi nhập 2FA: {e}")
                else:
                    self.log(f"[{self.account['id']}] CẢNH BÁO: Không có 2FA secret hợp lệ! Vui lòng tự nhập mã 2FA thủ công trên trình duyệt (có 30s để test).")
                    time.sleep(30)
                    
            self.log(f"[{self.account['id']}] Xử lý đăng nhập hoàn tất! Đợi 5 giây theo cấu hình...")
            time.sleep(5)
            return True
            
        except Exception as e:
             self.log(f"[{self.account['id']}] Lỗi login: Không tìm thấy ô nhập email/pass hoặc sai selector.")
             try:
                 err_img = f"error_login_{self.account['id']}.png"
                 self.driver.save_screenshot(err_img)
                 self.log(f"[{self.account['id']}] Đã lưu ảnh màn hình lỗi: {err_img}")
             except:
                 pass
             return False
             
    def upload_post(self, media_path, log_name=""):
        self.log(f"[{self.account['id']}] ===== BẮT ĐẦU ĐĂNG BÀI: {log_name} =====")

        is_page = "Page" in log_name

        # Điều hướng tới trang chủ fb.com (áp dụng cho cả Trang Cá Nhân và Page theo yêu cầu)
        self.log(f"[{self.account['id']}] Truy cập trang chủ (fb.com) để đăng bài...")
        self.driver.get("https://www.facebook.com/")
        time.sleep(4)
        self.driver.refresh()
        time.sleep(4)
        self.driver.refresh()
        time.sleep(4)

        try:
            # ═══════════════════════════════════════════════════════════════════
            # BƯỚC 1: Click nút "Ảnh/video"
            # DOM: <div aria-label="Ảnh/video" role="button">
            #        <span class="x1lliihq ... xlyipyv xuxw1ft">Ảnh/video</span>
            # ═══════════════════════════════════════════════════════════════════
            self.log(f"[{self.account['id']}] [B1] Tìm nút 'Ảnh/video'...")
            photo_btn = None

            selectors_photo = [
                # Ưu tiên 1: img icon chính xác 8_VnccIZfRa.webp từ yêu cầu
                "//img[contains(@src, '8_VnccIZfRa.webp')]",
                # Ưu tiên 2: aria-label chính xác (từ DOM thực)
                "//div[@aria-label='Ảnh/video' and @role='button']",
                "//div[@aria-label='Photo/video' and @role='button']",
                # Ưu tiên 2: span text bên trong
                "//span[contains(@class, 'x1lliihq') and contains(@class, 'xlyipyv') and (text()='Ảnh/video' or text()='Photo/video')]",
                # Ưu tiên 3: img icon 8_VnccIZfRa.webp trong div[role=button]
                "//div[@role='button']//img[contains(@src, '8_VnccIZfRa.webp')]",
                # Ưu tiên 4: span text đơn giản
                "//span[text()='Ảnh/video' or text()='Photo/video']",
            ]

            for xp in selectors_photo:
                try:
                    el = WebDriverWait(self.driver, 6).until(
                        EC.element_to_be_clickable((By.XPATH, xp))
                    )
                    if el and el.is_displayed():
                        photo_btn = el
                        self.log(f"[{self.account['id']}] [B1] Tìm thấy nút Ảnh/video bằng: {xp[:50]}...")
                        break
                except:
                    pass

            if not photo_btn:
                self.log(f"[{self.account['id']}] [B1] LỖI: Không tìm thấy nút Ảnh/video trên {log_name}.")
                return

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", photo_btn)
            time.sleep(0.8)
            self.driver.execute_script("arguments[0].click();", photo_btn)
            self.log(f"[{self.account['id']}] [B1] Đã click nút Ảnh/video. Chờ 2s...")
            time.sleep(2)

            # ═══════════════════════════════════════════════════════════════════
            # BƯỚC 2: Truyền đường dẫn ảnh vào <input type="file"> ẩn
            # (Tránh mở hộp thoại File Explorer của Windows)
            # ═══════════════════════════════════════════════════════════════════
            if media_path:
                self.log(f"[{self.account['id']}] [B2] Truyền đường dẫn ảnh vào input ẩn...")
                try:
                    file_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH,
                            "//div[@role='dialog']//input[@type='file' and contains(@accept, 'image')] | //div[@role='dialog']//input[@type='file'] | //input[@type='file' and contains(@accept, 'image')] | //input[@type='file']"
                        ))
                    )
                    abs_path = os.path.abspath(media_path)
                    self.log(f"[{self.account['id']}] [B2] Đường dẫn ảnh: {abs_path}")
                    file_input.send_keys(abs_path)
                    self.log(f"[{self.account['id']}] [B2] Đã truyền đường dẫn. Chờ 6s để ảnh hiển thị và load xong...")
                    time.sleep(6)
                except Exception as e:
                    self.log(f"[{self.account['id']}] [B2] Lỗi truyền file ảnh: {e}")

            # ═══════════════════════════════════════════════════════════════════
            # BƯỚC 3: Gõ nội dung bài viết vào ô Lexical Editor
            # DOM: <p class="xdj266r x14z9mp xat24cr ... " dir="auto">
            # Gõ chậm từng ký tự như người bình thường
            # ═══════════════════════════════════════════════════════════════════
            desc = self.account.get('description', '')
            if desc:
                self.log(f"[{self.account['id']}] [B3] Click ô soạn thảo và gõ nội dung từ từ...")
                try:
                    desc_box = None
                    selectors_box = [
                        # Ưu tiên 1: class xdj266r + dir=auto (từ DOM thực)
                        "//p[contains(@class, 'xdj266r') and @dir='auto']",
                        # Ưu tiên 2: div role=textbox có aria-label
                        "//div[@role='textbox' and contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'bạn đang nghĩ gì')]",
                        # Ưu tiên 3: div role=textbox contenteditable
                        "//div[@role='textbox' and @contenteditable='true']",
                        # Ưu tiên 4: p[dir=auto] bất kỳ
                        "//p[@dir='auto']",
                    ]
                    for xp_box in selectors_box:
                        try:
                            el = WebDriverWait(self.driver, 8).until(
                                EC.element_to_be_clickable((By.XPATH, xp_box))
                            )
                            if el and el.is_displayed():
                                desc_box = el
                                self.log(f"[{self.account['id']}] [B3] Tìm thấy ô soạn thảo.")
                                break
                        except:
                            pass

                    if not desc_box:
                        self.log(f"[{self.account['id']}] [B3] Không tìm thấy ô nhập nội dung.")
                    else:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", desc_box)
                        time.sleep(0.5)
                        desc_box.click()
                        time.sleep(1)

                        # Gõ từng ký tự chậm như người bình thường
                        self.log(f"[{self.account['id']}] [B3] Bắt đầu gõ {len(desc)} ký tự...")
                        for char in desc:
                            if char == '\n':
                                desc_box.send_keys(Keys.SHIFT, Keys.ENTER)
                                time.sleep(random.uniform(0.5, 1.0))
                            else:
                                desc_box.send_keys(char)
                                time.sleep(random.uniform(0.04, 0.13))
                                # Dừng thêm sau dấu câu
                                if char in ['.', ',', '!', '?', ':', ';']:
                                    time.sleep(random.uniform(0.4, 0.9))

                        time.sleep(2)
                        self.log(f"[{self.account['id']}] [B3] Hoàn thành gõ nội dung.")
                except Exception as e:
                    self.log(f"[{self.account['id']}] [B3] Lỗi gõ nội dung: {e}")

            # ═══════════════════════════════════════════════════════════════════
            # BƯỚC 4: Click nút "Tiếp"
            # DOM: <span class="x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft">Tiếp</span>
            # Dùng JS Click để vượt overlay
            # ═══════════════════════════════════════════════════════════════════
            self.log(f"[{self.account['id']}] [B4] Tìm và click nút 'Tiếp'...")
            clicked_next = False
            # Dùng WebDriverWait chờ tối đa 15s để nút Tiếp xuất hiện sau khi ảnh load xong
            selectors_tiep = [
                # Selector ưu tiên từ user: div[@aria-label='Tiếp' and @role='button']
                "//div[@aria-label='Tiếp' and @role='button']",
                "//div[@aria-label='Next' and @role='button']",
                "//div[@role='button']//span[text()='Tiếp' or text()='Next']",
                "//span[contains(@class, 'x1lliihq') and contains(@class, 'xlyipyv') and (text()='Tiếp' or text()='Next')]",
                "//span[contains(@class, 'x1lliihq') and (text()='Tiếp' or text()='Next')]",
                "//span[text()='Tiếp' or text()='Next']",
            ]
            # Lặp tối đa 3 lần để bấm nút Tiếp (để xử lý màn hình up video nhiều bước)
            for step_tiep in range(3):
                clicked_in_step = False
                for xp_tiep in selectors_tiep:
                    try:
                        els = self.driver.find_elements(By.XPATH, xp_tiep)
                        # Chọn các nút đang hiển thị trên màn hình
                        valid_els = [el for el in els if el.is_displayed()]
                        if valid_els:
                            # Lấy nút cuối cùng [last()] như user yêu cầu
                            tiep_el = valid_els[-1]
                            is_disabled = self.driver.execute_script(
                                "return arguments[0].closest('[aria-disabled=\"true\"]') !== null;", tiep_el
                            )
                            if not is_disabled:
                                self.driver.execute_script("arguments[0].click();", tiep_el)
                                self.log(f"[{self.account['id']}] [B4] Đã bấm nút 'Tiếp' (lần {step_tiep+1}).")
                                clicked_next = True
                                clicked_in_step = True
                                time.sleep(4) # Chờ load step tiếp theo
                                break
                    except:
                        pass
                
                # Nếu không tìm thấy nút Tiếp nào nữa thì thoát vòng lặp
                if not clicked_in_step:
                    break

            if not clicked_next:
                self.log(f"[{self.account['id']}] [B4] Không thấy nút 'Tiếp' (có thể không cần), tiếp tục tìm nút Đăng...")

            wait_tiep = 6 if is_page else 3
            # Đợi giao diện chuyển sang màn hình Đăng bài
            self.log(f"[{self.account['id']}] [B4] Chờ {wait_tiep} giây để giao diện load sẵn sàng...")
            time.sleep(wait_tiep)

            # ═══════════════════════════════════════════════════════════════════
            # BƯỚC 5: Xử lý Lên lịch (nếu bật) hoặc Click nút "Đăng" trực tiếp
            # ═══════════════════════════════════════════════════════════════════
            is_schedule = self.account.get('is_schedule') == '1'
            s_date = self.account.get('schedule_date', '')
            s_time = self.account.get('schedule_time', '')
            
            if is_schedule and s_date and s_time:
                self.log(f"[{self.account['id']}] [B5] Bật Lên lịch: {s_date} {s_time}...")
                # Tìm dropdown hoặc nút "Đăng" có mũi tên dropdown để mở tùy chọn
                schedule_done = False
                
                # Thử click vào biểu tượng mũi tên cạnh nút Đăng
                arrow_xpaths = [
                    "//div[@role='button'][.//i[contains(@class,'x15mokao')] or .//svg] [contains(@aria-label, 'Đăng') or contains(@aria-label, 'Post')]/following-sibling::div[@role='button']",
                    "//div[@aria-label='Mở dropdown' or @aria-label='Open dropdown' or @aria-label='More options']",
                    # Tìm nút có icon mũi tên xuống gần nút Đăng
                    "//div[@role='button' and (contains(@aria-label, 'Lên lịch') or contains(@aria-label, 'Schedule'))]",
                ]
                
                for xp_arr in arrow_xpaths:
                    try:
                        arr = self.driver.find_element(By.XPATH, xp_arr)
                        if arr and arr.is_displayed():
                            self.driver.execute_script("arguments[0].click();", arr)
                            time.sleep(1.5)
                            break
                    except:
                        pass
                
                # Sau khi mở dropdown, tìm và click "Lên lịch"
                sch_xpaths = [
                    "//div[@role='menu' or @role='listbox' or @role='dialog']//span[contains(text(),'Lên lịch') or contains(text(),'Schedule')]",
                    "//span[contains(text(),'Lên lịch') or contains(text(),'Schedule')]",
                    "//div[@role='button' and .//*[contains(text(),'Lên lịch') or contains(text(),'Schedule')]]",
                ]
                for xp_s in sch_xpaths:
                    try:
                        el_s = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, xp_s))
                        )
                        if el_s and el_s.is_displayed():
                            self.driver.execute_script("arguments[0].click();", el_s)
                            self.log(f"[{self.account['id']}] [B5] Đã chọn Lên lịch.")
                            schedule_done = True
                            time.sleep(2)
                            break
                    except:
                        pass
                
                if schedule_done:
                    # Nhập ngày giờ vào các ô input
                    all_inputs = self.driver.find_elements(By.XPATH,
                        "//input[@type='text' or @type='date' or @type='time' or @type='number'] | //input[contains(@aria-label,'Ngày') or contains(@aria-label,'Tháng') or contains(@aria-label,'Năm') or contains(@aria-label,'Giờ') or contains(@aria-label,'Phút') or contains(@aria-label,'Date') or contains(@aria-label,'Month') or contains(@aria-label,'Year') or contains(@aria-label,'Hour') or contains(@aria-label,'Minute')]"
                    )
                    visible_inputs = [inp for inp in all_inputs if inp.is_displayed() and inp.get_attribute('type') != 'hidden']
                    
                    def fill_schedule_input(inp, value):
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
                            time.sleep(0.3)
                            inp.click()
                            inp.send_keys(Keys.CONTROL + 'a')
                            time.sleep(0.2)
                            inp.send_keys(Keys.DELETE)
                            from selenium.webdriver.common.action_chains import ActionChains
                            ActionChains(self.driver).triple_click(inp).perform()
                            time.sleep(0.2)
                            inp.send_keys(value)
                            time.sleep(0.5)
                        except:
                            pass
                    
                    date_filled = False
                    time_filled = False
                    for inp in visible_inputs:
                        aria = (inp.get_attribute('aria-label') or '').lower()
                        ph = (inp.get_attribute('placeholder') or '').lower()
                        if any(k in aria for k in ['ngày', 'date', 'tháng', 'month', 'năm', 'year']) or 'dd' in ph or 'mm' in ph:
                            if not date_filled:
                                fill_schedule_input(inp, s_date)
                                self.log(f"[{self.account['id']}] [B5] Điền ngày: {s_date}")
                                date_filled = True
                        elif any(k in aria for k in ['giờ', 'time', 'hour', 'phút', 'minute']) or 'hh' in ph:
                            if not time_filled:
                                fill_schedule_input(inp, s_time)
                                self.log(f"[{self.account['id']}] [B5] Điền giờ: {s_time}")
                                time_filled = True
                    
                    if not date_filled and len(visible_inputs) >= 1:
                        fill_schedule_input(visible_inputs[0], s_date)
                    if not time_filled and len(visible_inputs) >= 2:
                        fill_schedule_input(visible_inputs[1], s_time)
                    
                    time.sleep(1)
                    # Xác nhận nếu có nút Save/Xong
                    for xp_save in ["//span[text()='Lưu' or text()='Save' or text()='Xong' or text()='Done']"]:
                        try:
                            b_save = self.driver.find_element(By.XPATH, xp_save)
                            if b_save and b_save.is_displayed():
                                self.driver.execute_script("arguments[0].click();", b_save)
                                time.sleep(1)
                                break
                        except:
                            pass
            
            # Bây giờ click nút "Đăng" hoặc "Lên lịch" (để submit)
            btn_label = 'Lên lịch' if is_schedule else 'Đăng'
            self.log(f"[{self.account['id']}] [B5] Tìm và click nút '{btn_label}'...")
            posted = False
            for attempt in range(30):
                try:
                    if is_schedule:
                        # Tìm cả nút Lên lịch và Đăng
                        post_btns = self.driver.find_elements(By.XPATH,
                            "//div[@role='button' and (contains(@aria-label,'Lên lịch') or contains(@aria-label,'Schedule') or contains(@aria-label,'Đăng') or contains(@aria-label,'Post'))] | //span[contains(@class, 'x1lliihq') and (text()='Lên lịch' or text()='Schedule' or text()='Đăng' or text()='Post')]"
                        )
                    else:
                        # Selector ưu tiên từ user: div[@aria-label='Đăng' and @role='button']
                        post_btns = self.driver.find_elements(By.XPATH,
                            "//div[@aria-label='Đăng' and @role='button']"
                        )
                        if not post_btns:
                            # Fallback 1: aria-label="Post"
                            post_btns = self.driver.find_elements(By.XPATH,
                                "//div[@aria-label='Post' and @role='button']"
                            )
                        if not post_btns:
                            # Fallback 2: Selector chính xác từ DOM: x1lliihq + xlyipyv + xuxw1ft + text Đăng
                            post_btns = self.driver.find_elements(By.XPATH,
                                "//span[contains(@class, 'x1lliihq') and contains(@class, 'xlyipyv') and (text()='Đăng' or text()='Post')]"
                            )
                        # Fallback 3: chỉ cần x1lliihq + text
                        if not post_btns:
                            post_btns = self.driver.find_elements(By.XPATH,
                                "//span[contains(@class, 'x1lliihq') and (text()='Đăng' or text()='Post')]"
                            )
                    for btn in reversed(post_btns):
                        try:
                            # Dùng JS kiểm tra xem có parent nào bị disabled không
                            is_disabled = self.driver.execute_script(
                                "return arguments[0].closest('div[aria-disabled=\"true\"]') !== null;", btn
                            )
                            if is_disabled:
                                continue

                            # JS Click – vượt qua mọi overlay và trạng thái tàng hình của Selenium
                            self.driver.execute_script("arguments[0].click();", btn)
                            self.log(f"[{self.account['id']}] [B5] Đã bấm nút {btn_label}! (attempt {attempt+1})")
                            posted = True
                            break
                        except:
                            pass
                    if posted:
                        break
                except:
                    pass
                time.sleep(1)

            if not posted:
                self.log(f"[{self.account['id']}] [B5] LỖI: Quá 30 giây chờ nút {btn_label}.")
                return

            # Nghỉ để Facebook xử lý và tải bài viết hoàn tất
            self.log(f"[{self.account['id']}] [B5] Chờ tối đa 120s để tải file và xử lý bài viết...")
            time.sleep(120)
            self.log(f"[{self.account['id']}] ===== {'LÊN LỊCH' if is_schedule else 'ĐĂNG BÀI'} HOÀN TẤT: {log_name} =====")

        except Exception as e:
            self.log(f"[{self.account['id']}] Lỗi đăng bài lên {log_name}: {e}")
             
    def upload_reel(self, video_path, url="https://www.facebook.com/reels/create", log_name=""):
        self.log(f"[{self.account['id']}] Đang thiết lập đăng lên {log_name}...")
        self.log(f"[{self.account['id']}] Bắt đầu tải lên Reels: {video_path}")
        self.driver.get(url)
        time.sleep(5)
        
        wait = WebDriverWait(self.driver, 20)
        
        try:
            file_input = wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
            )
            
            paths = [p.strip() for p in video_path.split('\n') if p.strip()]
            processed_paths = []
            for p in paths:
                p_abs = os.path.abspath(p)
                if not p_abs.lower().endswith('.mp4'):
                    import shutil
                    mp4_path = os.path.splitext(p_abs)[0] + ".mp4"
                    try:
                        if not os.path.exists(mp4_path):
                            self.log(f"[{self.account['id']}] Tự động chuyển đuôi sang MP4: {mp4_path}")
                            shutil.copy2(p_abs, mp4_path)
                        p_abs = mp4_path
                    except Exception as e:
                        self.log(f"[{self.account['id']}] Lỗi copy sang MP4: {e}")
                processed_paths.append(p_abs.replace('\\', '/'))
                
            abs_path_str = "\n".join(processed_paths)
            file_input.send_keys(abs_path_str)
            self.log(f"[{self.account['id']}] Đã chọn {len(processed_paths)} file video.")
            
            # Xử lý riêng cho file nặng
            self.log(f"[{self.account['id']}] Đợi 10s để tải video lên...")
            time.sleep(10)
        except Exception as e:
            self.log(f"[{self.account['id']}] Lỗi upload video: {e}")
            return
            
        try:
            next_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button']//span[text()='Tiếp' or text()='Next'] | //span[text()='Tiếp' or text()='Next']"))
            )
            next_btn.click()
            time.sleep(2)
        except Exception as e:
             self.log(f"[{self.account['id']}] Lỗi bấm Tiếp lần 1")
             
        try:
            next_btns = self.driver.find_elements(By.XPATH, "//div[@role='button']//span[text()='Tiếp' or text()='Next'] | //span[text()='Tiếp' or text()='Next']")
            if next_btns:
                for btn in reversed(next_btns):
                    try:
                        if btn.is_displayed():
                            btn.click()
                            break
                    except: pass
            time.sleep(2)
        except Exception as e:
             self.log(f"[{self.account['id']}] Lỗi bấm Tiếp lần 2")
             
        try:
            desc_box = wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))
            )
            desc_box.click()
            desc = self.account.get('description', '')
            if desc:
                self.type_slowly(desc_box, desc)
            self.log(f"[{self.account['id']}] Đã điền mô tả.")
            time.sleep(1)
        except Exception as e:
             self.log(f"[{self.account['id']}] Lỗi nhập mô tả")
             
        try:
            # XỬ LÝ LÊN LỊCH NẾU CÓ CHỌN
            if self.account.get('is_schedule') == '1':
                try:
                    self.log(f"[{self.account['id']}] Đang thiết lập chế độ Lên lịch (Schedule)...")
                    
                    s_date = self.account.get('schedule_date', '')  # dd/mm/yyyy
                    s_time_raw = self.account.get('schedule_time', '')  # HH:MM
                    
                    # Chuyển đổi 24h sang 12h (AM/PM)
                    s_time = s_time_raw
                    try:
                        if s_time_raw and ':' in s_time_raw:
                            h_str, m_str = s_time_raw.split(':')
                            h = int(h_str)
                            ampm = "PM" if h >= 12 else "AM"
                            h_12 = h % 12
                            if h_12 == 0:
                                h_12 = 12
                            s_time = f"{h_12:02d}:{m_str} {ampm}"
                    except Exception as e:
                        self.log(f"[{self.account['id']}] Lỗi chuyển đổi giờ 12h: {e}")
                    sch_d = self.account.get('sch_d', '')
                    sch_m = self.account.get('sch_m', '')
                    sch_y = self.account.get('sch_y', '')
                    sch_h = self.account.get('sch_h', '')
                    sch_min = self.account.get('sch_min', '')
                    
                    # BƯỚC A: Tìm và click nút/radio "Lên lịch" / "Schedule"
                    schedule_clicked = False
                    schedule_xpaths = [
                        # Radio / switch / button có text Lên lịch
                        "//div[@role='radio' and .//*[contains(text(),'Lên lịch') or contains(text(),'Schedule')]]",
                        "//div[@role='button' and .//*[contains(text(),'Lên lịch') or contains(text(),'Schedule')]]",
                        "//span[contains(text(),'Lên lịch') or contains(text(),'Schedule') or contains(text(),'lịch')]/ancestor::div[@role='radio' or @role='button'][1]",
                        # Selector dự phòng: chỉ span text
                        "//span[text()='Lên lịch' or text()='Schedule']",
                        "//span[contains(text(),'Lên lịch')]",
                    ]
                    for xp in schedule_xpaths:
                        try:
                            el = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, xp))
                            )
                            if el and el.is_displayed():
                                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                                time.sleep(0.5)
                                try:
                                    from selenium.webdriver.common.action_chains import ActionChains
                                    ActionChains(self.driver).move_to_element(el).click().perform()
                                except:
                                    self.driver.execute_script("arguments[0].click();", el)
                                schedule_clicked = True
                                self.log(f"[{self.account['id']}] Đã click tùy chọn Lên lịch.")
                                break
                        except:
                            pass
                    
                    if not schedule_clicked:
                        self.log(f"[{self.account['id']}] Không tìm thấy nút Lên lịch. Tiếp tục đăng ngay.")
                    else:
                        time.sleep(2)
                        
                        # BƯỚC B: Nhập Ngày, Tháng, Năm, Giờ, Phút vào các ô input
                        # Facebook Reels thường có input riêng cho từng trường
                        all_inputs = self.driver.find_elements(By.XPATH,
                            "//input[@type='text' or @type='date' or @type='time' or @type='number'] | //input[contains(@aria-label,'Ngày') or contains(@aria-label,'Tháng') or contains(@aria-label,'Năm') or contains(@aria-label,'Giờ') or contains(@aria-label,'Phút') or contains(@aria-label,'Date') or contains(@aria-label,'Month') or contains(@aria-label,'Year') or contains(@aria-label,'Hour') or contains(@aria-label,'Minute')]"
                        )
                        visible_inputs = [inp for inp in all_inputs if inp.is_displayed() and inp.get_attribute('type') != 'hidden']
                        
                        def fill_input(inp, value):
                            """Xóa sạch và nhập giá trị vào ô input."""
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
                                time.sleep(0.3)
                                inp.click()
                                time.sleep(0.3)
                                inp.send_keys(Keys.CONTROL + 'a')
                                time.sleep(0.2)
                                inp.send_keys(Keys.DELETE)
                                time.sleep(0.2)
                                # Triple-click để chọn toàn bộ text cũ
                                from selenium.webdriver.common.action_chains import ActionChains
                                ActionChains(self.driver).triple_click(inp).perform()
                                time.sleep(0.2)
                                inp.send_keys(value)
                                time.sleep(0.5)
                            except Exception as ex:
                                self.log(f"[{self.account['id']}] Lỗi fill input: {ex}")
                        
                        if visible_inputs and s_date and s_time:
                            # Thử cách 1: Tìm input theo aria-label
                            date_filled = False
                            time_filled = False
                            
                            for inp in visible_inputs:
                                aria = (inp.get_attribute('aria-label') or '').lower()
                                placeholder = (inp.get_attribute('placeholder') or '').lower()
                                
                                if any(k in aria for k in ['ngày', 'date', 'tháng', 'month', 'năm', 'year']) or 'dd' in placeholder or 'mm' in placeholder:
                                    if not date_filled:
                                        fill_input(inp, s_date)
                                        self.log(f"[{self.account['id']}] Đã điền ngày: {s_date}")
                                        date_filled = True
                                elif any(k in aria for k in ['giờ', 'time', 'hour', 'phút', 'minute']) or 'hh' in placeholder:
                                    if not time_filled:
                                        fill_input(inp, s_time)
                                        self.log(f"[{self.account['id']}] Đã điền giờ: {s_time}")
                                        time_filled = True
                            
                            # Cách 2 fallback: dùng vị trí input nếu không xác định được
                            if not date_filled and len(visible_inputs) >= 1:
                                fill_input(visible_inputs[0], s_date)
                                self.log(f"[{self.account['id']}] Fallback: điền ngày vào input[0]: {s_date}")
                            if not time_filled and len(visible_inputs) >= 2:
                                fill_input(visible_inputs[1], s_time)
                                self.log(f"[{self.account['id']}] Fallback: điền giờ vào input[1]: {s_time}")
                        
                        self.log(f"[{self.account['id']}] Đã nhập thời gian lên lịch: {s_date} {s_time}")
                        time.sleep(2)
                        
                        # BƯỚC C: Xác nhận (click nút Save / Xong / Xác nhận nếu có)
                        confirm_xpaths = [
                            "//div[@role='button']//span[text()='Lưu' or text()='Save' or text()='Xong' or text()='Done' or text()='Xác nhận' or text()='Confirm']",
                            "//span[text()='Lưu' or text()='Save' or text()='Xong' or text()='Done']",
                        ]
                        for xp_c in confirm_xpaths:
                            try:
                                btn_c = self.driver.find_element(By.XPATH, xp_c)
                                if btn_c and btn_c.is_displayed():
                                    self.driver.execute_script("arguments[0].click();", btn_c)
                                    self.log(f"[{self.account['id']}] Đã xác nhận lên lịch.")
                                    time.sleep(1)
                                    break
                            except:
                                pass
                        
                        time.sleep(1)
                except Exception as e:
                    self.log(f"[{self.account['id']}] Lỗi cấu hình nút Lên lịch: {e}. Sẽ tiếp tục Đăng ngay.")
                    
        except Exception as e:
            pass
             
        try:
            clicked = False
            is_schedule = self.account.get('is_schedule') == '1'
            self.log(f"[{self.account['id']}] Đang chờ nút {'Lên lịch' if is_schedule else 'Đăng'} sáng lên...")
            for _ in range(60): # Đợi tối đa 60 giây để video xử lý xong
                # Khi lên lịch: ưu tiên click nút "Lên lịch" / "Schedule", nếu không có thì mới click "Đăng"
                if is_schedule:
                    btn_texts = "'Lên lịch' or text()='Schedule' or text()='Đăng' or text()='Post' or text()='Publish'"
                else:
                    btn_texts = "'Đăng' or text()='Post' or text()='Publish'"
                post_btns = self.driver.find_elements(By.XPATH,
                    f"//div[@aria-label='Đăng' or @aria-label='Post' or @aria-label='Publish' or @aria-label='Lên lịch' or @aria-label='Schedule'] | //span[@dir='auto']//span[text()={btn_texts}] | //span[text()={btn_texts}]")
                for btn in reversed(post_btns):
                    try:
                        if btn.is_displayed():
                            # Kiểm tra xem nút có bị mờ (disabled) không (kiểm tra ngược lên 6 lớp cha)
                            is_disabled = self.driver.execute_script("""
                                var el = arguments[0];
                                var current = el;
                                for(var i=0; i<6; i++) {
                                    if(current && current.getAttribute('aria-disabled') === 'true') {
                                        return true;
                                    }
                                    if(current) current = current.parentElement;
                                }
                                return false;
                            """, btn)
                            
                            if is_disabled:
                                continue
                                
                            # Bổ sung selector mạnh hơn cho nút Đăng
                            try:
                                # Ưu tiên dùng ActionChains giả lập chuột thật
                                from selenium.webdriver.common.action_chains import ActionChains
                                ActionChains(self.driver).move_to_element(btn).click().perform()
                            except:
                                pass
                                
                            self.driver.execute_script("""
                                var el = arguments[0];
                                var current = el;
                                // Thực hiện click trên chính thẻ span và 5 thẻ cha bọc ngoài nó để đảm bảo trúng React listener
                                for (var i = 0; i < 6; i++) {
                                    if (current) {
                                        try { current.click(); } catch(e) {}
                                        var events = ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'];
                                        events.forEach(function(ev) {
                                            try {
                                                current.dispatchEvent(new MouseEvent(ev, {bubbles: true, cancelable: true, view: window}));
                                            } catch(e) {}
                                        });
                                        current = current.parentElement;
                                    }
                                }
                            """, btn)
                            clicked = True
                            break
                    except:
                        pass
                if clicked:
                    break
                time.sleep(1)
                
            if clicked:
                self.log(f"[{self.account['id']}] Đã bấm nút Đăng!")
            else:
                self.log(f"[{self.account['id']}] Lỗi: Không thể tìm thấy nút Đăng để click.")
            
            self.log(f"[{self.account['id']}] Đang chờ hoàn tất upload (đợi 1 phút)...")
            time.sleep(60) 
            

                
        except Exception as e:
             self.log(f"[{self.account['id']}] Lỗi bấm Đăng")

    def post_to_groups(self, group_links, media_path):
        for link in group_links:
            if self.is_stopped():
                self.log(f"[{self.account['id']}] Nhận tín hiệu dừng khi đang đăng Nhóm.")
                break
            try:
                uid = self.account["id"]
                self.log(f"[{uid}] ===== [Group] Bắt đầu đăng bài vào nhóm: {link} =====")

                # ═══════════ BƯỚC 0: Kiểm tra đã tham gia nhóm chưa ═══════════
                self.driver.get(link)
                time.sleep(3)
                try:
                    join_btns = self.driver.find_elements(By.XPATH,
                        "//div[@role='button'][contains(., 'Tham gia nhóm') or contains(., 'Join group')] | "
                        "//span[text()='Tham gia nhóm' or text()='Join group']/ancestor::div[@role='button']"
                    )
                    for jb in join_btns:
                        if jb.is_displayed():
                            self.log(f"[{uid}] [Group] Phát hiện nút Tham gia Nhóm. Đang gửi yêu cầu...")
                            self.driver.execute_script("arguments[0].click();", jb)
                            time.sleep(5)
                            self.log(f"[{uid}] [Group] Đã gửi yêu cầu Tham gia. Sẽ thử đăng nếu nhóm mở...")
                            break
                except Exception:
                    pass

                if "groups" not in self.driver.current_url:
                    self.log(f"[{uid}] [Group] Không thể vào nhóm (bị khoá hoặc không có quyền). Bỏ qua.")
                    continue

                # ═══════════ BƯỚC 1: Click tab "Thảo luận" ═══════════
                self.log(f"[{uid}] [Group][B2] Tìm và click tab 'Thảo luận'...")
                try:
                    thao_luan_xpaths = [
                        "//a[@id='posts' and @role='tab']",
                        "//span[text()='Thảo luận' or text()='Discussion']/ancestor::a",
                        "//a[contains(@href, 'discussion')]",
                    ]
                    clicked_tab = False
                    for xp in thao_luan_xpaths:
                        try:
                            el = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, xp))
                            )
                            if el and el.is_displayed():
                                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                                time.sleep(0.5)
                                self.driver.execute_script("arguments[0].click();", el)
                                clicked_tab = True
                                self.log(f"[{uid}] [Group][B1] Đã click tab Thảo luận.")
                                break
                        except Exception:
                            pass
                    if not clicked_tab:
                        self.log(f"[{uid}] [Group][B1] Không tìm thấy tab Thảo luận. Tiếp tục...")
                    time.sleep(2)
                except Exception as e:
                    self.log(f"[{uid}] [Group][B1] Lỗi click tab Thảo luận: {e}")

                # ═══════════ BƯỚC 2: Click ô "Bạn viết gì đi..." ═══════════
                self.log(f"[{uid}] [Group][B3] Tìm và click ô 'Bạn viết gì đi...'...")
                composer_clicked = False
                composer_xpaths = [
                    "//span[contains(text(), 'Bạn viết gì đi')]",
                    "//span[contains(text(), 'Write something')]",
                    "//div[@role='button' and (contains(., 'Bạn viết gì đi') or contains(., 'Write something'))]",
                ]
                for xp in composer_xpaths:
                    try:
                        els = self.driver.find_elements(By.XPATH, xp)
                        for el in els:
                            try:
                                if el.is_displayed():
                                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                                    time.sleep(0.5)
                                    self.driver.execute_script("arguments[0].click();", el)
                                    composer_clicked = True
                                    self.log(f"[{uid}] [Group][B2] Đã click ô soạn bài.")
                                    break
                            except Exception:
                                pass
                        if composer_clicked:
                            break
                    except Exception:
                        pass

                if not composer_clicked:
                    self.log(f"[{uid}] [Group][B3] Không tìm thấy ô soạn bài. Bỏ qua nhóm này.")
                    continue

                # Đợi 6 giây để popup "Tạo bài viết" bật lên hoàn toàn (Yêu cầu bước 4)
                time.sleep(6)

                # ═══════════ BƯỚC 3, 4, 5: Điền nội dung văn bản (Caption) ═══════════
                desc = self.account.get("description", "")
                if desc:
                    self.log(f"[{uid}] [Group][B4] Tìm ô Lexical Editor và điền nội dung...")
                    desc_box = None
                    desc_xpaths = [
                        "//div[@aria-placeholder='Tạo bài viết công khai...' and @role='textbox']",
                        "//div[@aria-placeholder='Create a public post…' and @role='textbox']",
                        "//div[@role='textbox' and contains(@aria-label, 'Bạn viết gì đi')]",
                        "//div[@contenteditable='true']",
                    ]
                    for xp in desc_xpaths:
                        try:
                            el = WebDriverWait(self.driver, 8).until(
                                EC.element_to_be_clickable((By.XPATH, xp))
                            )
                            if el and el.is_displayed():
                                desc_box = el
                                self.log(f"[{uid}] [Group][B3] Tìm thấy ô soạn thảo.")
                                break
                        except Exception:
                            pass

                    if desc_box:
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", desc_box)
                        time.sleep(0.5)
                        try:
                            desc_box.click()
                        except:
                            try:
                                ActionChains(self.driver).move_to_element(desc_box).click().perform()
                            except:
                                self.driver.execute_script("arguments[0].click(); arguments[0].focus();", desc_box)
                        time.sleep(0.5)
                        self.type_slowly(desc_box, desc)
                        self.log(f"[{uid}] [Group][B5] Đã điền nội dung ({len(desc)} ký tự).")
                        time.sleep(1)
                    else:
                        self.log(f"[{uid}] [Group][B4] Không tìm thấy ô nhập nội dung.")
                else:
                    self.log(f"[{uid}] [Group][B4] Không có caption để điền.")

                # ═══════════ BƯỚC 6: Upload Media qua nút Ảnh/Video ═══════════
                if media_path:
                    paths = [p.strip() for p in media_path.split('\n') if p.strip()]
                    processed_paths = []
                    is_video = False
                    for p in paths:
                        p_abs = os.path.abspath(p)
                        if p_abs.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                            is_video = True
                            if not p_abs.lower().endswith('.mp4'):
                                import shutil
                                mp4_path = os.path.splitext(p_abs)[0] + ".mp4"
                                try:
                                    if not os.path.exists(mp4_path):
                                        self.log(f"[{uid}] [Group][B6] Tự động chuyển đuôi sang MP4: {mp4_path}")
                                        shutil.copy2(p_abs, mp4_path)
                                    p_abs = mp4_path
                                except Exception as e:
                                    self.log(f"[{uid}] [Group][B6] Lỗi copy sang MP4: {e}")
                        processed_paths.append(p_abs.replace('\\', '/'))
                    
                    abs_path_str = "\n".join(processed_paths)
                    self.log(f"[{uid}] [Group][B6] Đang upload {len(processed_paths)} media...")

                    # (Đã bỏ qua thao tác click nút Ảnh/video theo yêu cầu vì không cần thiết khi truyền ngầm)

                    # 2. Truyền đường dẫn file vào thẻ <input type="file"> ẩn
                    file_input = None
                    
                    if is_video:
                        file_input_xpaths = [
                            "//div[@role='dialog']//input[@type='file' and contains(@accept, 'video')]",
                            "//div[@role='dialog']//input[@type='file']",
                            "//input[@type='file' and contains(@accept, 'video')]",
                            "//input[@type='file']",
                        ]
                    else:
                        file_input_xpaths = [
                            "//div[@role='dialog']//input[@type='file' and contains(@accept, 'image')]",
                            "//div[@role='dialog']//input[@type='file']",
                            "//input[@type='file' and contains(@accept, 'image')]",
                            "//input[@type='file']",
                        ]
                    for xp in file_input_xpaths:
                        try:
                            el = WebDriverWait(self.driver, 4).until(
                                EC.presence_of_element_located((By.XPATH, xp))
                            )
                            file_input = el
                            break
                        except Exception:
                            pass

                    if file_input:
                        try:
                            file_input.send_keys(abs_path_str)
                            self.log(f"[{uid}] [Group][B6] Đã truyền {len(processed_paths)} file ngầm thành công.")
                        except Exception as e:
                            self.log(f"[{uid}] [Group][B6] Lỗi send_keys file: {e}")
                    else:
                        self.log(f"[{uid}] [Group][B6] Không tìm thấy input file ẩn sau khi mở Dropzone.")

                    # Đợi ảnh/video tải lên khung xem trước
                    if is_video:
                        self.log(f"[{uid}] [Group][B4] Video đang tải... đợi 15s...")
                        time.sleep(15)
                    else:
                        self.log(f"[{uid}] [Group][B4] Ảnh đang tải... đợi 5s...")
                        time.sleep(5)
                else:
                    self.log(f"[{uid}] [Group][B4] Không có media để upload.")

                # ═══════════ BƯỚC 7: Tìm và bấm nút "Đăng" bằng JS Click ═══════════
                self.log(f"[{uid}] [Group][B7] Chờ nút 'Đăng' sáng lên và click...")
                post_btn = None
                post_btn_xpaths = [
                    "//div[@role='button' and (@aria-label='Đăng' or @aria-label='Post')]",
                    "//span[text()='Đăng' or text()='Post']/ancestor::div[@role='button']",
                    "//div[@role='button']//span[text()='Đăng' or text()='Post']",
                ]

                for attempt in range(30):  # Đợi tối đa 30 giây
                    for xp in post_btn_xpaths:
                        try:
                            btns = self.driver.find_elements(By.XPATH, xp)
                            for btn in reversed(btns):
                                try:
                                    if btn.is_displayed():
                                        is_disabled = self.driver.execute_script("""
                                            var el = arguments[0];
                                            for (var i = 0; i < 5; i++) {
                                                if (el && el.getAttribute('aria-disabled') === 'true') return true;
                                                if (el) el = el.parentElement;
                                            }
                                            return false;
                                        """, btn)
                                        if not is_disabled:
                                            post_btn = btn
                                            break
                                except Exception:
                                    pass
                            if post_btn:
                                break
                        except Exception:
                            pass
                    if post_btn:
                        break
                    time.sleep(1)

                if post_btn:
                    # Dùng JavaScript Click để bấm trực tiếp (tránh bị overlay cản trở)
                    self.driver.execute_script("arguments[0].click();", post_btn)
                    self.log(f"[{uid}] [Group] Đã bấm nút Đăng bài nhóm thành công!")
                    # Đợi 1 phút để bài hoàn tất tải lên trước khi chuyển sang nhóm tiếp theo
                    self.log(f"[{uid}] [Group][B7] Đợi 1 phút để bài đăng (ảnh/video) tải lên hoàn tất...")
                    time.sleep(60)
                else:
                    self.log(f"[{uid}] [Group][B7] LỖI: Không tìm thấy nút 'Đăng' sau 30 giây. Bỏ qua nhóm.")

                self.log(f"[{uid}] ===== [Group] Hoàn tất nhóm: {link} =====")

            except Exception as e:
                self.log(f"[{self.account['id']}] [Group] Lỗi không mong muốn khi xử lý nhóm {link}: {e}")
                time.sleep(random.uniform(5, 10))

    def upload_zalo_video(self, video_path):
        uid = self.account['id']
        self.log(f"[{uid}] [Zalo] Bắt đầu tiến trình Đăng Zalo Video...")
        
        paths = [p.strip() for p in video_path.split('\n') if p.strip()]
        if not paths:
            self.log(f"[{uid}] [Zalo] Không có đường dẫn video hợp lệ.")
            return
            
        first_video = os.path.abspath(paths[0]).replace('\\', '/')
        if not first_video.lower().endswith('.mp4'):
            import shutil
            mp4_path = os.path.splitext(first_video)[0] + ".mp4"
            try:
                if not os.path.exists(mp4_path):
                    self.log(f"[{uid}] [Zalo] Tự động chuyển đuôi sang MP4: {mp4_path}")
                    shutil.copy2(first_video, mp4_path)
                first_video = mp4_path.replace('\\', '/')
            except Exception as e:
                self.log(f"[{uid}] [Zalo] Lỗi copy sang MP4: {e}")
                return
                
        try:
            self.driver.get("https://video.zalo.me/creator")
            time.sleep(4)
            self.driver.refresh()
            time.sleep(4)
            self.driver.refresh()
            time.sleep(4)
            
            wait = WebDriverWait(self.driver, 10)
            
            try:
                state_element = wait.until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'styles_login-btn__3HqY4') or contains(text(), 'Đăng nhập Zalo')] | //div[contains(., 'Trang quản lý')] | //span[contains(text(), 'Đăng video')]"))
                )
                
                text_content = state_element.text.strip().lower()
                if "đăng nhập" in text_content or "login" in text_content:
                    self.log(f"[{uid}] [Zalo] Cần đăng nhập. Vui lòng quét mã QR trong 60 giây...")
                    self.driver.execute_script("arguments[0].click();", state_element)
                    
                    WebDriverWait(self.driver, 60).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(., 'Trang quản lý')] | //span[contains(text(), 'Đăng video')]"))
                    )
                    self.log(f"[{uid}] [Zalo] Đăng nhập thành công!")
                else:
                    self.log(f"[{uid}] [Zalo] Đã đăng nhập sẵn.")
                    
            except TimeoutException:
                self.log(f"[{uid}] [Zalo] Lỗi: Không thể tải trang Zalo hoặc cấu trúc đổi.")
                
            time.sleep(3)
            
            try:
                trang_quan_ly = self.driver.find_element(By.XPATH, "//div[contains(., 'Trang quản lý')]")
                self.driver.execute_script("arguments[0].click();", trang_quan_ly)
                time.sleep(3)
            except Exception:
                pass
                
            try:
                dang_video_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Đăng video')]")))
                self.driver.execute_script("arguments[0].click();", dang_video_btn)
                time.sleep(3)
            except Exception as e:
                self.log(f"[{uid}] [Zalo] Không tìm thấy nút Đăng video: {e}")
                return
                
            self.log(f"[{uid}] [Zalo] Đang tải video lên...")
            file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
            file_input.send_keys(first_video)
            
            time.sleep(15)
            
            desc = self.account.get('description', '')
            if desc:
                self.log(f"[{uid}] [Zalo] Đang nhập nội dung mô tả...")
                desc_box = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'input-conteneditable') and @contenteditable='true']")))
                desc_box.click()
                time.sleep(1)
                self.type_slowly(desc_box, desc)
                
            time.sleep(2)
            
            self.log(f"[{uid}] [Zalo] Thêm nhãn liên hệ...")
            try:
                them_nhan_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'ant-dropdown-trigger') and .//span[contains(text(), 'Thêm nhãn')]] | //a[.//span[contains(text(), 'Thêm nhãn')]]")))
                self.driver.execute_script("arguments[0].click();", them_nhan_btn)
                time.sleep(1)
                
                lien_he_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Liên hệ')] or .//img[contains(@src, 'contact-label-cta')]]")))
                self.driver.execute_script("arguments[0].click();", lien_he_btn)
                time.sleep(1)
                
                nhan_tin_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Nhắn tin liên hệ')]")))
                self.driver.execute_script("arguments[0].click();", nhan_tin_btn)
                time.sleep(1)
                
                chon_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Chọn')]")))
                self.driver.execute_script("arguments[0].click();", chon_btn)
                time.sleep(2)
            except Exception as e:
                self.log(f"[{uid}] [Zalo] Bỏ qua thêm nhãn (không tìm thấy yếu tố): {e}")
                
            self.log(f"[{uid}] [Zalo] Bấm nút Đăng video cuối cùng...")
            dang_btn_final = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//button[.//span[text()='Đăng video' or text()='Đăng']]")))[-1]
            self.driver.execute_script("arguments[0].click();", dang_btn_final)
            
            self.log(f"[{uid}] [Zalo] Đợi 120 giây để xử lý video hoàn tất...")
            time.sleep(120)
            
            # Kiểm tra bài đăng thành công
            self.log(f"[{uid}] [Zalo] Đang kiểm tra xác minh video vừa đăng...")
            try:
                self.driver.get("https://video.zalo.me/creator/video")
                time.sleep(5)
                
                # Click vào video đầu tiên (vừa đăng)
                first_video_img = wait.until(EC.element_to_be_clickable((By.XPATH, "//img[contains(@class, 'w-full h-full object-cover rounded-sm')]")))
                self.driver.execute_script("arguments[0].click();", first_video_img)
                time.sleep(5)
                
                # Lấy toàn bộ text trên trang hoặc tìm phần tử chứa text
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                
                if desc and desc in page_text:
                    self.log(f"[{uid}] [Zalo] Kiểm tra THÀNH CÔNG! Nội dung bài đăng trùng khớp: '{desc[:30]}...'")
                elif not desc:
                    self.log(f"[{uid}] [Zalo] Đã đăng video thành công (không có mô tả để kiểm tra).")
                else:
                    self.log(f"[{uid}] [Zalo] Cảnh báo: Video đã đăng nhưng không tìm thấy nội dung mô tả trùng khớp.")
                    
            except Exception as e:
                self.log(f"[{uid}] [Zalo] Không thể xác minh tự động (nhưng video có thể đã lên): {e}")

            self.log(f"[{uid}] [Zalo] Hoàn tất tiến trình Đăng Zalo Video!")
            
            if self.account.get('cmt_zalo_video', '0') == '1':
                cmt_text = self.account.get('cmt_text', '')
                if cmt_text:
                    try:
                        from zalo_comment_video import comment_on_zalo_video
                        comment_on_zalo_video(self.driver, self.log, cmt_text)
                    except Exception as e:
                        self.log(f"[{uid}] [Zalo] Lỗi CMT video: {e}")
                        
        except Exception as e:
            self.log(f"[{uid}] [Zalo] Lỗi tiến trình Zalo: {e}")

    def upload_tiktok_video(self, video_path):
        uid = self.account['id']
        self.log(f"[{uid}] [TikTok] Bắt đầu tiến trình Đăng TikTok Video...")
        
        paths = [p.strip() for p in video_path.split('\n') if p.strip()]
        if not paths:
            self.log(f"[{uid}] [TikTok] Không có đường dẫn video hợp lệ.")
            return
            
        first_video = os.path.abspath(paths[0]).replace('\\', '/')
        is_video = first_video.lower().endswith(('.mp4', '.mov', '.avi'))
        if is_video and not first_video.lower().endswith('.mp4'):
            import shutil
            mp4_path = os.path.splitext(first_video)[0] + ".mp4"
            try:
                if not os.path.exists(mp4_path):
                    self.log(f"[{uid}] [TikTok] Tự động chuyển đuôi sang MP4: {mp4_path}")
                    shutil.copy2(first_video, mp4_path)
                first_video = mp4_path.replace('\\', '/')
            except Exception as e:
                self.log(f"[{uid}] [TikTok] Lỗi copy sang MP4: {e}")
                return
                
        try:
            # Bước 1: Truy cập Tiktok
            self.driver.get("https://www.tiktok.com/")
            time.sleep(4)
            self.driver.refresh()
            time.sleep(4)
            self.driver.refresh()
            time.sleep(4)
            
            wait = WebDriverWait(self.driver, 15)
            
            # Bước 2 & 3: Kiểm tra Đăng nhập
            try:
                state_element = wait.until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'TUXButton-label') and (text()='Log in' or text()='Đăng nhập')] | //button[contains(., 'Log in') or contains(., 'Đăng nhập')] | //button[@aria-label='Upload' or contains(@class, 'StyledTUXNavButton')] | //a[contains(@href, '/upload')] | //div[text()='Upload']"))
                )
                text_content = state_element.text.lower()
                if 'đăng nhập' in text_content or 'log in' in text_content:
                    self.log(f"[{uid}] [TikTok] Cần đăng nhập. Vui lòng quét mã QR trong 90 giây...")
                    self.driver.execute_script("arguments[0].click();", state_element)
                    
                    WebDriverWait(self.driver, 90).until(
                        EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Upload' or contains(@class, 'StyledTUXNavButton')] | //a[contains(@href, '/upload')] | //div[text()='Upload']"))
                    )
                    self.log(f"[{uid}] [TikTok] Đăng nhập thành công!")
                    time.sleep(3)
                else:
                    self.log(f"[{uid}] [TikTok] Đã đăng nhập sẵn. Bỏ qua bước đăng nhập!")
            except TimeoutException:
                self.log(f"[{uid}] [TikTok] Cảnh báo: Web load chậm hoặc giao diện thay đổi.")
                
            # Bước 4: Click vào up video/ảnh
            self.log(f"[{uid}] [TikTok] Bấm nút Upload để chuyển sang trang tải lên...")
            try:
                upload_nav_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Upload'] | //a[contains(@href, '/upload')] | //div[text()='Upload']/ancestor::button")))
                self.driver.execute_script("arguments[0].click();", upload_nav_btn)
            except Exception:
                self.driver.get("https://www.tiktok.com/creator-center/upload")
            
            time.sleep(5)
            
            # Đảm bảo Iframe nếu có
            try:
                iframe = self.driver.find_element(By.XPATH, "//iframe[contains(@src, 'creator')] | //iframe")
                self.driver.switch_to.frame(iframe)
                self.log(f"[{uid}] [TikTok] Đã chuyển vào Iframe tải lên.")
                time.sleep(2)
            except Exception:
                pass
                
            # Chọn loại video hay ảnh (Tab)
            try:
                if is_video:
                    video_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-controls='panel-video' or contains(text(), 'Videos')]")))
                    self.driver.execute_script("arguments[0].click();", video_tab)
                else:
                    photo_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-controls='panel-photo' or contains(text(), 'Photos')]")))
                    self.driver.execute_script("arguments[0].click();", photo_tab)
                time.sleep(2)
            except Exception:
                pass
                
            # Bước 5: Click Select Videos và đưa đường dẫn
            self.log(f"[{uid}] [TikTok] Đang tải file lên...")
            try:
                # Thay vì click nút Select videos, truyền thẳng vào thẻ input type=file ẩn
                file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
                if not is_video and len(paths) > 1:
                    file_paths_str = '\n'.join([os.path.abspath(p).replace('\\', '/') for p in paths])
                    file_input.send_keys(file_paths_str)
                else:
                    file_input.send_keys(first_video)
            except Exception as e:
                self.log(f"[{uid}] [TikTok] Không tìm thấy input file: {e}")
                return
                
            self.log(f"[{uid}] [TikTok] Đợi file tải lên...")
            # Ảnh tải nhanh hơn video, điều chỉnh thời gian chờ tối đa
            max_wait = 60 if is_video else 20
            time.sleep(5)
            
            try:
                WebDriverWait(self.driver, max_wait).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Thay thế') or contains(text(), 'Replace') or contains(text(), 'Edit video') or contains(text(), 'Chỉnh sửa') or contains(@class, 'replace') or contains(text(), 'Uploaded') or contains(text(), 'Đã tải lên')]"))
                )
                self.log(f"[{uid}] [TikTok] Nhận diện tải lên file hoàn tất!")
            except TimeoutException:
                self.log(f"[{uid}] [TikTok] Bỏ qua chờ tải lên (giao diện không phản hồi mốc hoàn tất). Tiếp tục điền mô tả...")
                
            # Điền caption
            desc = self.account.get('description', '')
            if desc:
                self.log(f"[{uid}] [TikTok] Đang nhập nội dung mô tả...")
                
                # Chế độ ảnh có thêm ô nhập Tiêu đề (Title)
                if not is_video:
                    try:
                        title_box = self.driver.find_element(By.XPATH, "//input[@type='text' and (@placeholder='Add a catchy title' or contains(@class, 'titleInput'))]")
                        title_box.send_keys(desc[:80]) # Giới hạn ký tự cho tiêu đề
                        time.sleep(1)
                    except Exception:
                        pass
                        
                try:
                    desc_box = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'public-DraftEditor-content')] | //div[@contenteditable='true']")))
                    # JS click to ensure focus even if obscured
                    self.driver.execute_script("arguments[0].click();", desc_box)
                    time.sleep(1)
                    
                    # Xóa nội dung cũ (nếu có) bằng phím tắt để không làm hỏng React DraftEditor
                    desc_box.send_keys(Keys.CONTROL, 'a')
                    time.sleep(0.5)
                    desc_box.send_keys(Keys.BACKSPACE)
                    time.sleep(1)
                    self.type_slowly(desc_box, desc)
                except Exception as e:
                    self.log(f"[{uid}] [TikTok] Lỗi nhập mô tả: {e}")
                    
            time.sleep(2)
            
            # Bước 6: Cuộn trang xuống dưới cùng
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # Bước 7: Bấm nút Đăng
            self.log(f"[{uid}] [TikTok] Bấm nút Đăng chính...")
            try:
                post_btns = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//button[@data-e2e='post_video_button'] | //button[contains(., 'Post') or contains(., 'Đăng')] | //div[contains(@class, 'button-wrapper')]//button")))
                post_btn = post_btns[-1]
                self.driver.execute_script("arguments[0].click();", post_btn)
            except Exception as e:
                self.log(f"[{uid}] [TikTok] Không tìm thấy nút Đăng chính: {e}")
                
            # Bắt Popup xác nhận bản quyền/kiểm duyệt (Continue to post? -> Post now)
            try:
                self.log(f"[{uid}] [TikTok] Chờ xử lý Popup xác nhận (nếu có)...")
                confirm_btn = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[.//div[contains(text(), 'Post now') or contains(text(), 'Đăng ngay')]] | //div[contains(@class, 'TUXButton-label') and (text()='Post now' or text()='Đăng ngay')]"))
                )
                self.driver.execute_script("arguments[0].click();", confirm_btn)
                self.log(f"[{uid}] [TikTok] Đã bấm 'Post now' trên cửa sổ xác nhận!")
            except TimeoutException:
                pass # Không bị hỏi xác nhận
                
            self.log(f"[{uid}] [TikTok] Đợi 60 giây để xử lý video hoàn tất...")
            time.sleep(60)
            
            self.log(f"[{uid}] [TikTok] Hoàn tất tiến trình Đăng TikTok Video!")
            
        except Exception as e:
            self.log(f"[{uid}] [TikTok] Lỗi tiến trình TikTok: {e}")
        finally:
            try:
                self.driver.switch_to.default_content()
            except:
                pass
