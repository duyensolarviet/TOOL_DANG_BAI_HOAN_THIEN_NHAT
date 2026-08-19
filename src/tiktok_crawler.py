import re
import os
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def sanitize_filename(name):
    clean = str(name).split("?")[0].split("&")[0].split("#")[0].strip()
    clean = re.sub(r'[\\/*?:"<>|]', "", clean)
    return clean

class TikTokCrawler:
    def __init__(self, log_callback=None, download_dir=None):
        self.log_callback = log_callback
        self.history_file = os.path.join(os.getcwd(), 'tiktok_history.json')
        if download_dir and download_dir.strip():
            self.download_dir = download_dir.strip()
        else:
            self.download_dir = os.path.join(os.getcwd(), 'tiktok_downloads')
            
        if not os.path.exists(self.download_dir):
            try:
                os.makedirs(self.download_dir)
            except Exception as e:
                self.log(f"Không thể tạo thư mục {self.download_dir}: {e}")
                self.download_dir = os.path.join(os.getcwd(), 'tiktok_downloads')
                if not os.path.exists(self.download_dir):
                    os.makedirs(self.download_dir)
                    
        try:
            from anticaptcha_solver import AntiCaptchaTikTokSolver
            self.captcha_solver = AntiCaptchaTikTokSolver(api_key="5fb2919ec337277c83fb4925fc406869", log_callback=self.log)
        except:
            self.captcha_solver = None

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)
        else:
            print(msg)

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                import json
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_history(self, history):
        try:
            import json
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            self.log(f"Lỗi lưu lịch sử: {e}")

    def go_to_next_item(self, driver):
        """
        Chuyển sang item tiếp theo trên modal TikTok
        """
        try:
            clicked = driver.execute_script("""
                let svgPath = document.querySelector('path[d^="m24 19.25 13.67"]') || document.querySelector('path[d*="19.25 13.67"]') || document.querySelector('path[d*="19.25"]');
                if (svgPath) {
                    let btn = svgPath.closest('button') || svgPath.closest('div[class*="Arrow"]') || svgPath.parentElement;
                    if (btn) { btn.click(); return true; }
                }
                let btns = document.querySelectorAll('button');
                for (let b of btns) {
                    if (b.innerHTML.includes('19.25') || b.getAttribute('data-e2e') === 'arrow-left' || (b.className && typeof b.className === 'string' && b.className.includes('Arrow'))) {
                        b.click(); return true;
                    }
                }
                return false;
            """)
            if not clicked:
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    ActionChains(driver).send_keys(Keys.ARROW_UP).perform()
                except: pass
            time.sleep(2)
            return True
        except Exception as e:
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(driver).send_keys(Keys.ARROW_UP).perform()
                time.sleep(2)
                return True
            except:
                return False

    def init_driver(self, profile_id):
        options = uc.ChromeOptions()
        options.add_argument("--disable-notifications")
        options.add_argument("--lang=vi")
        options.add_argument("--window-size=1024,768")
        
        # Tắt tính năng tự động cập nhật của Chrome
        options.add_argument("--disable-component-update")
        options.add_argument("--simulate-outdated-no-au='Tue, 31 Dec 2099 23:59:59 GMT'")
        
        # Cấu hình tải mặc định
        prefs = {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0
        }
        options.add_experimental_option("prefs", prefs)
        
        # Sử dụng profile của tài khoản đích để tận dụng session đã đăng nhập
        profile_dir = os.path.join(os.getcwd(), 'profiles', str(profile_id))
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
            
        from cleaner import get_chrome_main_version
        chrome_version = get_chrome_main_version()
        
        try:
            driver = uc.Chrome(options=options, user_data_dir=profile_dir, version_main=chrome_version)
        except Exception as ex:
            if "183" in str(ex) or "already exists" in str(ex).lower() or "permission" in str(ex).lower():
                try:
                    import shutil
                    appdata_uc = os.path.join(os.environ.get('APPDATA', ''), 'undetected_chromedriver')
                    if os.path.exists(appdata_uc):
                        os.system("taskkill /f /im chromedriver.exe >nul 2>&1")
                        time.sleep(1)
                        for f in os.listdir(appdata_uc):
                            fp = os.path.join(appdata_uc, f)
                            try:
                                if os.path.isfile(fp):
                                    os.remove(fp)
                                elif os.path.isdir(fp):
                                    shutil.rmtree(fp, ignore_errors=True)
                            except: pass
                except: pass
                time.sleep(1)
                driver = uc.Chrome(options=options, user_data_dir=profile_dir, version_main=chrome_version)
            else:
                raise ex
        return driver

    def crawl_profile(self, profile_url, max_videos=5, profile_id="tiktok_crawler", on_video_downloaded=None, reset_history=False, start_video_id=None):
        # Trích xuất username chuẩn của kênh (ví dụ: thaihong653705)
        username_match = re.search(r'@([a-zA-Z0-9_.-]+)', profile_url)
        channel_user = username_match.group(1) if username_match else ""
        
        self.log(f"Bắt đầu phân tích kênh TikTok: @{channel_user} ({profile_url}) (Giới hạn: {max_videos} video)")
        self.log("Đang mở trình duyệt Chrome siêu cấp để vượt tường lửa TikTok...")
        
        driver = None
        results = []
        try:
            try:
                driver = self.init_driver(profile_id)
            except Exception as ex:
                err_msg = str(ex).lower()
                if "session not created" in err_msg or "cannot connect to chrome" in err_msg or "in use" in err_msg:
                    self.log(f"LỖI NGHIÊM TRỌNG: Profile Chrome '{profile_id}' ĐANG MỞ!")
                    self.log("=> BẠN PHẢI TẮT CỬA SỔ CHROME ĐÓ ĐI THÌ AI MỚI CHẠY ĐƯỢC!")
                    self.log("=> Hướng dẫn: Bấm nút 'Đóng Tất Cả Chrome' ở phần mềm rồi thử lại.")
                    return results
                else:
                    raise ex
                    
            driver.get(profile_url)
            time.sleep(4)
            
            # Tự động phát hiện và giải Captcha nếu có ngay khi mở trang
            for _ in range(4):
                if self.captcha_solver and self.captcha_solver.is_captcha_present(driver):
                    self.log("Phát hiện Captcha TikTok khi mở kênh. Đang giải tự động...")
                    solved = self.captcha_solver.solve_tiktok_captcha(driver)
                    time.sleep(3)
                    if solved:
                        break
                else:
                    break
            
            # Load history for deduplication
            history = self.load_history()
            
            if reset_history and profile_url in history:
                history[profile_url] = []
                self.save_history(history)
                self.log(f"Đã làm sạch lịch sử tải cho kênh này. Sẽ tải lại từ đầu!")
                
            if profile_url not in history:
                history[profile_url] = []
                
            self.log(f"Đang cuộn trang để quét và phân loại toàn bộ bài đăng của kênh @{channel_user}...")
            all_urls = []
            photo_urls = set()
            last_height = driver.execute_script("return document.body.scrollHeight")
            no_change_count = 0
            
            while True:
                # Kiểm tra giải Captcha nếu xuất hiện bất ngờ khi cuộn trang
                if self.captcha_solver and self.captcha_solver.is_captcha_present(driver):
                    self.log("Phát hiện Captcha TikTok khi cuộn trang. Đang giải tự động...")
                    self.captcha_solver.solve_tiktok_captcha(driver)
                    time.sleep(3)
                # Thu thập url video CHÍNH XÁC của kênh này (bỏ qua video đề xuất của kênh khác)
                els = driver.find_elements(By.CSS_SELECTOR, "a[href*='/video/']")
                for el in els:
                    url = el.get_attribute("href")
                    if url and "/video/" in url:
                        if channel_user and f"@{channel_user}/video/" not in url:
                            continue
                        if url not in all_urls:
                            all_urls.append(url)
                
                # Quét nhận diện bài đăng dạng ảnh (Photo) của chính kênh này
                els_photo = driver.find_elements(By.CSS_SELECTOR, "a[href*='/photo/']")
                for el in els_photo:
                    p_url = el.get_attribute("href")
                    if p_url and "/photo/" in p_url:
                        if channel_user and f"@{channel_user}/photo/" not in p_url:
                            continue
                        if p_url not in photo_urls:
                            photo_urls.add(p_url)
                            p_id = p_url.split('/photo/')[1].split('?')[0]
                            self.log(f"   -> [Bỏ qua hình ảnh]: Phát hiện bài đăng Ảnh (Photo ID: {p_id}) của kênh @{channel_user} -> Tự động bỏ qua.")
                        
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2.5)
                
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    no_change_count += 1
                    if no_change_count >= 3:
                        break
                else:
                    no_change_count = 0
                    last_height = new_height
                    
            self.log(f"-> Kết quả quét kênh @{channel_user}: Tìm thấy {len(all_urls)} video và {len(photo_urls)} bài đăng dạng ảnh.")
            if photo_urls:
                self.log(f"-> [Bỏ qua hình ảnh]: Đã loại bỏ hoàn toàn {len(photo_urls)} bài đăng ảnh khỏi danh sách tải.")
                
            if not all_urls:
                self.log(f"Lỗi: Quá thời gian nhưng không thấy video nào của kênh @{channel_user}! (Hãy đảm bảo bạn đã giải quyết captcha nếu có).")
                return results
                
            valid_urls = []
            skipped_history_count = 0
            
            # Đảo ngược toàn bộ danh sách thu thập được để duyệt từ dưới cùng (cũ nhất) lên trên
            all_urls.reverse()
            
            if start_video_id:
                start_vid_clean = sanitize_filename(start_video_id.split("/video/")[1] if "/video/" in start_video_id else start_video_id.split("/")[-1])
                found_start = False
                for i, u in enumerate(all_urls):
                    if start_vid_clean in u:
                        self.log(f"-> Đã định vị chính xác video bắt đầu (ID: {start_vid_clean}) tại vị trí {i+1}/{len(all_urls)} trên kênh (tính từ dưới lên). Bắt đầu tải từ video này trở lên!")
                        all_urls = all_urls[i:]
                        found_start = True
                        break
                if not found_start:
                    self.log(f"-> Không tìm thấy ID video bắt đầu ({start_vid_clean}) trên kênh. Tải từ video đầu tiên tìm được.")
            
            for url in all_urls:
                vid_id_check = sanitize_filename(url.split("/video/")[1] if "/video/" in url else url.split("/")[-1])
                is_downloaded = False
                for h_url in history.get(profile_url, []):
                    if vid_id_check in h_url:
                        is_downloaded = True
                        skipped_history_count += 1
                        self.log(f"   -> [Lịch sử]: Bỏ qua video ID {vid_id_check} vì đã tải và lên lịch trong lịch sử.")
                        break
                if not is_downloaded:
                    valid_urls.append(url)
                if len(valid_urls) >= max_videos:
                    break
                    
            if not valid_urls:
                self.log(f"[Thông báo] Toàn bộ video trên kênh @{channel_user} đã được tải trước đó hoặc không còn video mới. Hoàn thành!")
                return results

            if len(valid_urls) < max_videos:
                self.log(f"[Thông báo] Bạn cài đặt lấy {max_videos} video nhưng trang cá nhân @{channel_user} chỉ có {len(valid_urls)} video mới (đã loại bỏ {len(photo_urls)} bài ảnh). Tool sẽ quét và lên lịch toàn bộ {len(valid_urls)} video này!")
            else:
                self.log(f"[Thông báo] Đã lọc và chọn đủ {len(valid_urls)} video mới nhất của kênh @{channel_user} theo yêu cầu.")
                
            for idx, vid_url in enumerate(valid_urls):
                self.log(f"[{idx+1}/{len(valid_urls)}] Đang tải: {vid_url}")
                vid_id = sanitize_filename(vid_url.split("/video/")[1] if "/video/" in vid_url else vid_url.split("/")[-1])
                if not vid_id:
                    vid_id = f"video_{int(time.time())}_{idx+1}"
                
                try:
                    if idx == 0:
                        # Bước 3: Click vào video dưới cùng trước (Mở modal popup)
                        self.log(f"   -> Cuộn tìm và click mở video trên tab Profile...")
                        driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(0.5)
                        el = None
                        for _ in range(20):
                            els = driver.find_elements(By.CSS_SELECTOR, f"a[href*='{vid_id}']")
                            if els:
                                el = els[0]
                                break
                            driver.execute_script("window.scrollBy(0, 800);")
                            time.sleep(0.3)
                            
                        if el:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                            time.sleep(1)
                            try:
                                from selenium.webdriver.common.action_chains import ActionChains
                                ActionChains(driver).move_to_element(el).click().perform()
                            except:
                                driver.execute_script("arguments[0].click();", el)
                            time.sleep(3)
                            
                            # Click vào video player theo xpath user yêu cầu (trong modal)
                            try:
                                video_el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//video[@crossorigin='use-credentials'] | //video")))
                                driver.execute_script("arguments[0].click();", video_el)
                            except: pass
                            time.sleep(2)
                        else:
                            raise Exception("Không thấy thumbnail video, có thể đã bị ẩn hoặc lỗi tải trang.")
                    else:
                        # Kiểm tra xem modal đã chuyển sang đúng video mục tiêu chưa
                        if vid_id not in driver.current_url:
                            self.go_to_next_item(driver)
                            time.sleep(2)
                            
                        # Nếu vẫn chưa chuyển sang đúng video mục tiêu, mở trực tiếp URL video đó
                        if vid_id not in driver.current_url:
                            self.log(f"   -> Mở trực tiếp video: {vid_url}")
                            driver.get(vid_url)
                            time.sleep(3)
                            try:
                                video_el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//video[@crossorigin='use-credentials'] | //video")))
                                driver.execute_script("arguments[0].click();", video_el)
                            except: pass
                            time.sleep(1.5)
                        else:
                            self.log(f"   -> Đã chuyển sang video tiếp theo trên modal: {vid_url}")
                        
                    # Bước 4 & 5: Đợi load 2~4 giây rồi click Chia sẻ & Sao chép
                    try:
                        time.sleep(3) # Wait 2~4 seconds as requested
                        wait_long = WebDriverWait(driver, 10)
                        
                        # Click Chia sẻ
                        try:
                            share_btn = wait_long.until(EC.presence_of_element_located((By.XPATH, "//button[@data-e2e='browse-share'] | //span[@data-e2e='browse-share'] | //div[@data-e2e='share-icon'] | //button[@data-e2e='share-icon'] | //span[@data-e2e='share-icon']")))
                            driver.execute_script("arguments[0].click();", share_btn)
                            time.sleep(1.5)
                        except:
                            self.log(f"   -> Không tìm thấy nút Chia sẻ bằng Xpath chuẩn, thử bằng JS...")
                            driver.execute_script("""
                                let btns = document.querySelectorAll('button, span, div');
                                for(let b of btns) {
                                    if(b.innerText && b.innerText.includes('Chia sẻ')) {
                                        b.click(); break;
                                    }
                                }
                            """)
                            time.sleep(1.5)
                        
                        # Click copy icon with SVG path as requested by user
                        try:
                            # Try finding button that contains this exact svg path
                            copy_icon = wait_long.until(EC.presence_of_element_located((By.XPATH, "//*[local-name()='path' and @d='M24 48a24 24 0 1 0 0-48 24 24 0 0 0 0 48Z']/ancestor::button | //*[local-name()='path' and @d='M24 48a24 24 0 1 0 0-48 24 24 0 0 0 0 48Z']/ancestor::div[contains(@class, 'DivItemContainer')] | //div[@data-e2e='share-copy'] | //*[contains(@class, 'CopyLink')]")))
                            driver.execute_script("arguments[0].click();", copy_icon)
                        except:
                            # Fallback to copy link JS
                            self.log(f"   -> Thử click nút Sao chép bằng JS...")
                            driver.execute_script("""
                                let btns = document.querySelectorAll('span, p, div');
                                for(let b of btns) {
                                    if(b.innerText && b.innerText.includes('Sao chép liên kết')) {
                                        b.click(); break;
                                    }
                                }
                            """)
                            
                        time.sleep(1)
                        self.log("   -> Đã mô phỏng click Chia sẻ & Sao chép link thành công.")
                    except Exception as e:
                        self.log(f"   -> Lỗi click Chia sẻ/Sao chép: {e}")
                    
                    # Bước 6: Mở tab mới để tải video qua qload
                    is_download_success = False
                    filepath = os.path.join(self.download_dir, f"{vid_id}.mp4")
                    try:
                        self.log("   -> Mở tab mới để tải ngầm qua hệ thống tự động...")
                        original_window = driver.current_window_handle
                        
                        # Mở tab mới
                        driver.switch_to.new_window('tab')
                        
                        download_sites = [
                            {
                                "id": "cobalt",
                                "url": "https://cobalt.tools/",
                                "input_sel": "#link-area"
                            },
                            {
                                "id": "ttdownloader",
                                "url": "https://ttdownloader.com/",
                                "input_sel": "#url",
                                "submit_sel": "#submit"
                            },
                            {
                                "id": "qload",
                                "url": "https://qload.info/fr/",
                                "input_sel": "input[name='link']",
                                "download_sel": "a#download-btn"
                            }
                        ]
                        

                        for retry_idx in range(2):
                            if is_download_success:
                                break
                            if retry_idx > 0:
                                self.log("   -> Đang thử lại toàn bộ các nguồn tải...")
                                
                            for site in download_sites:
                                try:
                                    existing_files = set(os.listdir(self.download_dir))
                                    self.log(f"   -> Đang thử lấy link từ: {site['url']}")
                                    driver.get(site['url'])
                                    time.sleep(3)
                                    
                                    wait_short = WebDriverWait(driver, 25)
                                    input_box = wait_short.until(EC.presence_of_element_located((By.CSS_SELECTOR, site["input_sel"])))
                                    
                                    input_box.send_keys(vid_url)
                                    
                                    if site["id"] == "cobalt":
                                        input_box.send_keys(Keys.RETURN)
                                        # Cobalt might also need explicit click on the '>>' button if enter fails
                                        try:
                                            dl_btn = driver.find_element(By.ID, "download-button")
                                            driver.execute_script("arguments[0].click();", dl_btn)
                                        except: pass
                                    elif site["id"] == "ttdownloader":
                                        submit_btn = driver.find_element(By.CSS_SELECTOR, site["submit_sel"])
                                        driver.execute_script("arguments[0].click();", submit_btn)
                                        time.sleep(5)
                                        # Mở khóa bằng cách bấm nút No watermark / Không có hình mờ
                                        try:
                                            # Đợi một chút để danh sách kết quả tải hiện ra
                                            time.sleep(3)
                                            clicked = False
                                            
                                            # Lấy các khối kết quả (mỗi thẻ tải là 1 div.result)
                                            results = driver.find_elements(By.CSS_SELECTOR, "div.result")
                                            
                                            # Cách 1: Tìm chính xác khối chứa chữ "không có hình mờ" hoặc "no watermark"
                                            for res in results:
                                                res_text = res.text.lower()
                                                if "không có hình mờ" in res_text or "no watermark" in res_text:
                                                    if "audio" not in res_text and "âm thanh" not in res_text:
                                                        dl_link = res.find_element(By.CSS_SELECTOR, "a.download-link")
                                                        # Xoá target="_blank" để tránh bị Chrome chặn popup
                                                        driver.execute_script("arguments[0].removeAttribute('target'); arguments[0].scrollIntoView({block: 'center'});", dl_link)
                                                        time.sleep(1)
                                                        driver.execute_script("arguments[0].click();", dl_link)
                                                        clicked = True
                                                        break
                                            
                                            # Cách 2: Nếu không tìm thấy bằng text cụ thể, click thẻ tải video đầu tiên
                                            if not clicked:
                                                for res in results:
                                                    res_text = res.text.lower()
                                                    if "audio" not in res_text and "âm thanh" not in res_text:
                                                        try:
                                                            dl_link = res.find_element(By.CSS_SELECTOR, "a.download-link")
                                                            driver.execute_script("arguments[0].removeAttribute('target'); arguments[0].scrollIntoView({block: 'center'});", dl_link)
                                                            time.sleep(1)
                                                            driver.execute_script("arguments[0].click();", dl_link)
                                                            break
                                                        except:
                                                            pass
                                                            
                                        except Exception as e:
                                            self.log(f"   -> Lỗi click TTDownloader: {e}")
                                    else:
                                        input_box.send_keys(Keys.RETURN)
                                    
                                    self.log("   -> Đang xử lý link (Đợi tự động tải hoặc nút tải)...")
                                    
                                    new_file_path = None
                                    download_btn_clicked = False
                                    
                                    for _ in range(50):
                                        current_files = set(os.listdir(self.download_dir))
                                        new_files = current_files - existing_files
                                        
                                        completed_files = [f for f in new_files if f.endswith(".mp4") and not any(cf.startswith(f) and cf.endswith(".crdownload") for cf in new_files)]
                                        is_downloading = any(f.endswith(".crdownload") or f.endswith(".tmp") for f in new_files)
                                        
                                        if completed_files and not is_downloading:
                                            new_file_path = os.path.join(self.download_dir, completed_files[0])
                                            break
                                            
                                        if not download_btn_clicked and not is_downloading:
                                            if site["id"] == "qload":
                                                try:
                                                    btn = driver.find_element(By.CSS_SELECTOR, site["download_sel"])
                                                    if btn.is_displayed():
                                                        driver.execute_script("arguments[0].click();", btn)
                                                        download_btn_clicked = True
                                                        self.log("   -> Gửi lệnh tải xuống cho Chrome (qload)...")
                                                except:
                                                    pass
                                            elif site["id"] == "cobalt":
                                                try:
                                                    clicked = driver.execute_script("""
                                                        let els = document.querySelectorAll('button, div, span, a');
                                                        for(let el of els) {
                                                            let txt = el.innerText ? el.innerText.trim().toLowerCase() : '';
                                                            if((txt === 'tải xuống' || txt === 'download') && el.offsetParent !== null) {
                                                                el.click();
                                                                return true;
                                                            }
                                                        }
                                                        return false;
                                                    """)
                                                    if clicked:
                                                        self.log("   -> Đã bấm nút 'tải xuống' thủ công trên Cobalt vì trình duyệt chặn tải ngầm...")
                                                        download_btn_clicked = True
                                                except:
                                                    pass
                                                
                                        time.sleep(1)
                                    
                                    if new_file_path:
                                        try:
                                            if new_file_path != filepath:
                                                if os.path.exists(filepath):
                                                    try: os.remove(filepath)
                                                    except: pass
                                                os.rename(new_file_path, filepath)
                                        except Exception as ren_err:
                                            filepath = new_file_path
                                        is_download_success = True
                                        self.log(f"   -> Đã tải thành công bằng Native Chrome!")
                                        break
                                    else:
                                        self.log(f"   -> Lỗi: Không thấy file tải về ở thư mục. Thử trang khác...")
                                        
                                except Exception as e:
                                    err_msg = str(e).strip().split('\n')[0]
                                    self.log(f"   -> Mạng chặn hoặc lỗi {site['url']} ({err_msg}). Thử nguồn khác...")
                        
                        # Đóng tab mới qload và quay lại tab tiktok
                        driver.close()
                        driver.switch_to.window(original_window)
                    except Exception as e:
                        self.log(f"   -> Lỗi khi tải video ở tab mới: {e}")
                        try:
                            driver.switch_to.window(original_window)
                        except: pass
                        
                    if not is_download_success:
                        self.log("   -> Không thể tải video này, bỏ qua.")
                        # Close modal
                        try:
                            close_btn = driver.find_element(By.XPATH, "//button[@data-e2e='browse-close'] | //button[contains(@class, 'Close')]")
                            driver.execute_script("arguments[0].click();", close_btn)
                            time.sleep(1)
                        except: pass
                        continue
                        
                    # Bước 7: Quay trở về tab video vừa sao chép click sao chép nội dung ngầm
                    try:
                        # Click nút "thêm" nếu hiển thị
                        try:
                            them_btn = driver.find_element(By.XPATH, "//button[text()='thêm' or text()='Thêm' or text()='more' or text()='More']")
                            if them_btn.is_displayed():
                                driver.execute_script("arguments[0].click();", them_btn)
                                time.sleep(1)
                        except:
                            pass
                            
                        desc = driver.execute_script("""
                            let desc = '';
                            let selectors = [
                                '[data-e2e="browse-video-desc"]',
                                '[data-e2e="video-desc"]',
                                'h1[class*="H1Container"]',
                                'div[class*="DivVideoDesc"]',
                                'div[class*="VideoDescription"]',
                                '[class*="Caption"]',
                                'span[data-e2e*="desc-span"]'
                            ];

                            let targetContainer = null;
                            for (let selector of selectors) {
                                let elements = document.querySelectorAll(selector);
                                for (let i = elements.length - 1; i >= 0; i--) {
                                    let el = elements[i];
                                    let rect = el.getBoundingClientRect();
                                    if (rect.width > 0 && rect.height > 0) {
                                        let centerY = rect.top + rect.height / 2;
                                        let centerX = rect.left + rect.width / 2;
                                        if (centerY >= 0 && centerY <= window.innerHeight && centerX >= 0 && centerX <= window.innerWidth) {
                                            targetContainer = el;
                                            break;
                                        }
                                    }
                                }
                                if (targetContainer) break;
                            }

                            if (targetContainer) {
                                let clone = targetContainer.cloneNode(true);
                                let anchors = clone.querySelectorAll('a');
                                anchors.forEach(a => a.remove());
                                desc = clone.textContent;
                            }

                            if (!desc) {
                                for (let sel of selectors) {
                                    let el = document.querySelector(sel);
                                    if (el && el.innerText && el.innerText.trim().length > 0) {
                                        desc = el.innerText.trim();
                                        break;
                                    }
                                }
                            }

                            if (!desc) {
                                let meta = document.querySelector('meta[name="description"]');
                                if (meta && meta.content) {
                                    desc = meta.content.trim();
                                }
                            }

                            if (desc) {
                                desc = desc.replace(/#\\S+/g, '').replace(/\\s+/g, ' ').trim();
                            }
                            return desc || '';
                        """)
                            
                        if not desc:
                            desc = f"Tiktok Video {vid_id}"
                            
                        self.log(f"   -> [Kiểm tra Video {vid_id}]: Đã copy nội dung: '{desc[:60].replace(chr(10), ' ')}...'")
                    except Exception as e:
                        self.log(f"   -> Lỗi copy text: {e}")
                        desc = f"Tiktok Video {vid_id}"
                        
                    res_obj = {
                        'video_path': os.path.abspath(filepath).replace('\\', '/'),
                        'description': desc
                    }
                    results.append(res_obj)
                    
                    if on_video_downloaded:
                        try:
                            on_video_downloaded(res_obj)
                        except Exception as e:
                            self.log(f"   -> Lỗi xử lý callback AI: {e}")
                    
                    history[profile_url].append(vid_url)
                    self.save_history(history)
                    self.log(f"   -> Đã tải & lưu trữ thành công video {vid_id}.")
                    
                    # Bước cuối: Thay vì đóng modal, click mũi tên lên để chuyển video tiếp theo
                    if idx < len(valid_urls) - 1:
                        self.log("   -> Click mũi tên LÊN để chuyển sang video tiếp theo...")
                        self.go_to_next_item(driver)
                        
                except Exception as e:
                    self.log(f"   -> Lỗi xử lý video này: {e}")
                    
            if len(results) > 0:
                if len(results) < max_videos:
                    self.log(f"[Hoàn thành] Đã tải và lên lịch toàn bộ {len(results)}/{len(valid_urls)} video (Lý do: bạn cài đặt lấy {max_videos} video nhưng kênh bạn đưa chỉ có {len(valid_urls)} video nên đã lấy hết {len(results)} video có sẵn trên kênh)!")
                else:
                    self.log(f"[Hoàn thành] Đã tải và lên lịch đủ {len(results)}/{max_videos} video theo yêu cầu!")
                    
        except Exception as e:
            self.log(f"Lỗi hệ thống: {e}")
        finally:
            if driver:
                driver.quit()
                
        return results

if __name__ == "__main__":
    crawler = TikTokCrawler()
    # test
