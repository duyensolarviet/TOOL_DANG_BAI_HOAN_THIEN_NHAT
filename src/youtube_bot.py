import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

class YouTubeBot:
    def __init__(self, driver, account, log_callback=None, stop_event=None, type_slowly_func=None):
        self.driver = driver
        self.account = account
        self.log_callback = log_callback
        self.stop_event = stop_event
        self.type_slowly = type_slowly_func

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def is_stopped(self):
        if self.stop_event and self.stop_event.is_set():
            return True
        return False

    def interact_newsfeed(self):
        uid = self.account.get('id', 'Unknown')
        
        try:
            interact_time_str = self.account.get('yt_interact_time', '5')
            interact_time = float(interact_time_str) * 60
        except ValueError:
            interact_time = 300
            
        is_yt_like = self.account.get('is_yt_like', '0') == '1'
        yt_cmt = self.account.get('yt_cmt', '')
        
        self.log(f"[{uid}] [YouTube] Bắt đầu lướt newsfeed và xem video (Thời gian: {interact_time/60} phút)...")
        
        try:
            # Bước 1: Truy cập trang chủ và load lại 2 lần
            self.driver.get("https://www.youtube.com/")
            time.sleep(4)
            self.driver.refresh()
            time.sleep(4)
            self.driver.refresh()
            time.sleep(4)
            
            # Bước 2: Cuộn trang 3 giây rồi click ngẫu nhiên 1 video
            for _ in range(3):
                if self.is_stopped(): return
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(1)
                
            video_links = self.driver.find_elements(By.XPATH, "//a[contains(@class, 'ytLockupMetadataViewModelTitle')]")
            if not video_links:
                video_links = self.driver.find_elements(By.XPATH, "//a[@id='video-title-link' or @id='video-title']")
                
            if video_links:
                import random
                video = random.choice(video_links[:10])
                try:
                    video_title = video.text or "Video"
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", video)
                    time.sleep(1)
                    self.log(f"[{uid}] [YouTube] Đang mở video: {video_title}")
                    self.driver.execute_script("arguments[0].click();", video)
                except:
                    self.driver.get(video.get_attribute('href'))
            else:
                self.log(f"[{uid}] [YouTube] Vẫn không tìm thấy video, bỏ qua phần xem.")
                return
            
            # Đợi tải trang video
            time.sleep(6)
            
            def skip_ad():
                try:
                    skip_btn = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'ytp-skip-ad-button__text')] | //button[contains(@class, 'ytp-skip-ad-button')]")
                    if skip_btn and skip_btn[0].is_displayed():
                        self.driver.execute_script("arguments[0].click();", skip_btn[0])
                        self.log(f"[{uid}] [YouTube] Đã click Bỏ qua quảng cáo.")
                except:
                    pass
                    
            skip_ad()
            
            # Bước 3: Thích video
            if is_yt_like:
                self.driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(2)
                try:
                    like_btn = self.driver.find_element(By.XPATH, "//button[.//yt-animated-icon[@animated-icon-type='LIKE'] and @aria-pressed='false']")
                    self.driver.execute_script("arguments[0].click();", like_btn)
                    self.log(f"[{uid}] [YouTube] Đã thả Like video.")
                except Exception as e:
                    self.log(f"[{uid}] [YouTube] Không thể thả Like video (có thể đã like hoặc sai xpath).")
                    
            # Bước 4: Click nút xem thêm nội dung
            try:
                expand_btn = self.driver.find_elements(By.XPATH, "//tp-yt-paper-button[@id='expand']")
                if expand_btn and expand_btn[0].is_displayed():
                    self.driver.execute_script("arguments[0].click();", expand_btn[0])
                    time.sleep(1)
            except:
                pass
                    
            # Comment video
            if yt_cmt:
                try:
                    self.log(f"[{uid}] [YouTube] Chuẩn bị bình luận...")
                    self.driver.execute_script("window.scrollBy(0, 600);")
                    time.sleep(2)
                    
                    cmt_box = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@id='placeholder-area']"))
                    )
                    self.driver.execute_script("arguments[0].click();", cmt_box)
                    time.sleep(1)
                    
                    cmt_input = self.driver.find_element(By.XPATH, "//div[@id='contenteditable-root']")
                    if self.type_slowly:
                        self.type_slowly(cmt_input, yt_cmt)
                    else:
                        cmt_input.send_keys(yt_cmt)
                        
                    time.sleep(1)
                    
                    submit_btn = self.driver.find_element(By.XPATH, "//ytd-button-renderer[@id='submit-button']//button")
                    self.driver.execute_script("arguments[0].click();", submit_btn)
                    time.sleep(3)
                    self.log(f"[{uid}] [YouTube] Đã bình luận thành công: '{yt_cmt}'.")
                except Exception as e:
                    self.log(f"[{uid}] [YouTube] Lỗi khi bình luận: {e}")
            
            # Chờ (xem video) theo thời gian đã đặt
            self.log(f"[{uid}] [YouTube] Bắt đầu xem video trong {interact_time} giây...")
            start_watch = time.time()
            last_log = start_watch
            
            while time.time() - start_watch < interact_time:
                if self.is_stopped():
                    break
                time.sleep(5)
                skip_ad() # Liên tục check quảng cáo
                
                # Scroll random
                import random
                if random.random() < 0.2:
                    scroll_amount = random.randint(-200, 300)
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                    
                # Log 1 phút 1 lần
                if time.time() - last_log >= 60:
                    remaining = int(interact_time - (time.time() - start_watch))
                    self.log(f"[{uid}] [YouTube] Đang xem video... còn {remaining} giây.")
                    last_log = time.time()
                
            self.log(f"[{uid}] [YouTube] Hoàn thành phiên xem video YouTube.")
            
        except Exception as e:
            self.log(f"[{uid}] [YouTube] Lỗi tương tác Newsfeed: {e}")

    def upload_youtube_video(self, video_path):
        uid = self.account.get('id', 'Unknown')
        self.log(f"[{uid}] [YouTube] Bắt đầu tiến trình Đăng YouTube Video...")
        
        paths = [p.strip() for p in video_path.split('\n') if p.strip()]
        if not paths:
            self.log(f"[{uid}] [YouTube] Không có đường dẫn video hợp lệ.")
            return False
            
        first_video = os.path.abspath(paths[0]).replace('\\', '/')
        mp4_created_path = None
        
        if not first_video.lower().endswith('.mp4'):
            import shutil
            mp4_path = os.path.splitext(first_video)[0] + ".mp4"
            try:
                if not os.path.exists(mp4_path):
                    self.log(f"[{uid}] [YouTube] Tự động chuyển đuôi sang MP4: {mp4_path}")
                    shutil.copy2(first_video, mp4_path)
                    mp4_created_path = mp4_path
                first_video = mp4_path.replace('\\', '/')
            except Exception as e:
                self.log(f"[{uid}] [YouTube] Lỗi copy sang MP4: {e}")
                return False

        max_retries = 2
        for attempt in range(max_retries):
            if attempt > 0:
                self.log(f"[{uid}] [YouTube] Đang tải lại trang và thử lại (lần {attempt + 1}/{max_retries})...")
                try:
                    self.driver.refresh()
                    import time
                    time.sleep(5)
                except:
                    pass
            success = self._upload_attempt(first_video, uid)
            if success:
                return True
        self.log(f"[{uid}] [YouTube] Đã thử {max_retries} lần nhưng vẫn thất bại.")
        return False

    def _upload_attempt(self, first_video, uid):
        try:
            # Bước 1: Truy cập Youtube
            self.driver.get("https://www.youtube.com/")
            time.sleep(4)
            self.driver.refresh()
            time.sleep(4)
            self.driver.refresh()
            time.sleep(4)
            
            wait = WebDriverWait(self.driver, 15)
            
            # Kiểm tra đăng nhập Youtube
            try:
                # Bước 1: click vào nút Đăng nhập
                login_btn = wait.until(
                    EC.presence_of_element_located((By.XPATH, "//ytd-masthead//a[contains(@href, 'ServiceLogin')]"))
                )
                self.log(f"[{uid}] [YouTube] Cần đăng nhập. Bấm nút Đăng nhập...")
                self.driver.execute_script("arguments[0].click();", login_btn)
                time.sleep(3)
                
                # Bước 2: click vào tài khoản đầu tiên
                try:
                    self.log(f"[{uid}] [YouTube] Bấm chọn tài khoản đầu tiên...")
                    first_acc = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@data-item-index='0' and @role='link']"))
                    )
                    self.driver.execute_script("arguments[0].click();", first_acc)
                    time.sleep(3)
                except Exception as e:
                    self.log(f"[{uid}] [YouTube] Bỏ qua chọn tài khoản (không thấy danh sách).")
                    
                # Bước 3: click vào nút Tiếp tục
                try:
                    self.log(f"[{uid}] [YouTube] Bấm Tiếp tục...")
                    continue_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[text()='Tiếp tục']/ancestor::button[1]"))
                    )
                    self.driver.execute_script("arguments[0].click();", continue_btn)
                    time.sleep(5)
                except Exception as e:
                    self.log(f"[{uid}] [YouTube] Bỏ qua nút Tiếp tục (không thấy nút).")
                
                # Chờ đến khi nút Tạo (Create) xuất hiện
                WebDriverWait(self.driver, 90).until(
                    EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Tạo' or @aria-label='Create']"))
                )
                self.log(f"[{uid}] [YouTube] Đăng nhập thành công!")
                time.sleep(3)
            except TimeoutException:
                # Nếu không thấy nút Đăng nhập thì coi như đã đăng nhập
                self.log(f"[{uid}] [YouTube] Đã đăng nhập sẵn.")
                
            # Bước 2: Click nút Tạo
            self.log(f"[{uid}] [YouTube] Bấm nút Tạo...")
            create_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Tạo' or @aria-label='Create']")))
            self.driver.execute_script("arguments[0].click();", create_btn)
            time.sleep(2)
            
            # Bước 3: Click Tải video lên
            self.log(f"[{uid}] [YouTube] Chọn 'Tải video lên'...")
            upload_menu_item = wait.until(EC.element_to_be_clickable((By.XPATH, "//yt-formatted-string[text()='Tải video lên' or contains(text(), 'Upload video')]")))
            self.driver.execute_script("arguments[0].click();", upload_menu_item)
            time.sleep(5)
            
            # Đảm bảo Iframe nếu có (Studio YT thường dùng frame hoặc shadow DOM, ta thao tác thẳng nếu không có frame)
            
            # Bước 4: Tải file lên (truyền thẳng qua input type file thay vì click "Chọn tệp" để tránh hộp thoại OS)
            self.log(f"[{uid}] [YouTube] Đang gửi video...")
            try:
                file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
                file_input.send_keys(first_video)
            except Exception as e:
                self.log(f"[{uid}] [YouTube] Không tìm thấy thẻ tải video: {e}")
                return False
                
            self.log(f"[{uid}] [YouTube] Đợi giao diện Studio tải form và chờ video tải lên 100%...")
            time.sleep(5)
            
            try:
                start_upload_wait = time.time()
                last_up_status = ""
                while time.time() - start_upload_wait < 3600:
                    if self.is_stopped(): return False
                    
                    try:
                        progress_elems = self.driver.find_elements(By.XPATH, "//ytcp-video-upload-progress")
                        if not progress_elems:
                            time.sleep(3)
                            continue
                            
                        p_text = progress_elems[0].text.lower()
                        status_line = ""
                        for line in p_text.split('\n'):
                            if '%' in line or 'tải' in line or 'xử lý' in line or 'kiểm tra' in line:
                                status_line = line
                                break
                                
                        if not status_line:
                            status_line = p_text.replace('\n', ' ')
                            
                        if status_line != last_up_status and status_line.strip():
                            self.log(f"[{uid}] [YouTube] Trạng thái: {status_line.strip()}")
                            last_up_status = status_line
                            
                        # Chuyển sang bước tiếp theo khi thấy 100% hoặc đã bắt đầu xử lý/kiểm tra
                        if "100%" in p_text or "xử lý" in p_text or "hoàn tất" in p_text or "kiểm tra" in p_text or "không có vấn đề" in p_text:
                            self.log(f"[{uid}] [YouTube] Video đã tải lên 100%, tiếp tục điền thông tin...")
                            time.sleep(2) # đợi thêm xíu cho giao diện ổn định
                            break
                    except:
                        pass
                        
                    time.sleep(5)
            except Exception as e:
                self.log(f"[{uid}] [YouTube] Lỗi khi chờ tải lên: {e}")
            
            # Lấy Title & Description
            yt_title = self.account.get('yt_title', '')
            is_yt_ai_title = self.account.get('is_yt_ai_title', '0') == '1'
            desc = self.account.get('description', '')
            
            if is_yt_ai_title and desc:
                self.log(f"[{uid}] [YouTube] Đang tạo Tiêu đề AI từ nội dung mô tả...")
                try:
                    import json
                    import os
                    from ai_helper import GeminiHelper, GroqHelper
                    ai_config_file = "ai_config.json"
                    api_key = ""
                    provider = "Gemini"
                    if os.path.exists(ai_config_file):
                        with open(ai_config_file, 'r', encoding='utf-8') as f:
                            ai_config = json.load(f)
                            provider = ai_config.get("ai_provider", "Gemini")
                            if provider == "Groq":
                                api_key = ai_config.get("groq_api_key", "")
                            else:
                                api_key = ai_config.get("gemini_api_key", "")
                    
                    if api_key:
                        if provider == "Groq":
                            ai = GroqHelper(api_key=api_key)
                        else:
                            ai = GeminiHelper(api_key=api_key)
                        prompt = self.account.get('yt_ai_prompt', '')
                        if not prompt:
                            prompt = "Viết 1 tiêu đề Youtube thật ngắn gọn, thu hút (dưới 90 ký tự) dựa trên nội dung sau. Tuyệt đối không dùng ngoặc kép, không dùng hashtag, chỉ viết tiêu đề."
                        else:
                            prompt += " (Tuyệt đối không dùng ngoặc kép, không dùng hashtag)"
                            
                        ai_title = ai.rewrite_content(desc, prompt)
                        if ai_title:
                            # Xoá triệt để hashtag nếu AI vẫn ngoan cố sinh ra
                            import re
                            ai_title = re.sub(r'#\w+', '', ai_title).replace('"', '').strip()
                            
                            yt_title = ai_title
                            self.log(f"[{uid}] [YouTube] Đã tạo Tiêu đề AI: {yt_title}")
                    else:
                        self.log(f"[{uid}] [YouTube] Lỗi: Chưa cấu hình Gemini API Key trong Tab Quét TikTok. Dùng tiêu đề mặc định.")
                except Exception as e:
                    self.log(f"[{uid}] [YouTube] Lỗi tạo Tiêu đề AI: {e}. Dùng tiêu đề mặc định.")
                    
            # Fallback nếu yt_title vẫn rỗng (do không nhập hoặc AI lỗi)
            if not yt_title:
                if desc:
                    yt_title = desc.split('\n')[0][:90].strip()
                    self.log(f"[{uid}] [YouTube] Tiêu đề rỗng, lấy dòng đầu mô tả làm tiêu đề: {yt_title}")
                else:
                    yt_title = "Video mới"
                    self.log(f"[{uid}] [YouTube] Tiêu đề rỗng, dùng mặc định: {yt_title}")
                    
            is_yt_shorts = self.account.get('is_yt_shorts', '0') == '1'
            if is_yt_shorts:
                desc += "\n#Shorts"
                
            # Bước 5: Tiêu đề
            if yt_title:
                self.log(f"[{uid}] [YouTube] Nhập tiêu đề...")
                try:
                    title_box = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='textbox' and (contains(@aria-label, 'Thêm tiêu đề') or contains(@aria-label, 'Tiêu đề') or contains(@aria-label, 'bắt buộc') or contains(@aria-label, 'Title') or @aria-required='true')]")))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", title_box)
                    time.sleep(1)
                    title_box.click()
                    time.sleep(0.5)
                    title_box.send_keys(Keys.CONTROL, 'a')
                    time.sleep(0.5)
                    title_box.send_keys(Keys.BACKSPACE)
                    time.sleep(0.5)
                    self.type_slowly(title_box, yt_title)
                except Exception as e:
                    self.log(f"[{uid}] [YouTube] Lỗi nhập tiêu đề: {e}")
                    return False
                    
            # Bước 6: Mô tả
            if desc:
                self.log(f"[{uid}] [YouTube] Nhập mô tả...")
                try:
                    desc_box = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='textbox' and (contains(@aria-label, 'Giới thiệu về video') or contains(@aria-label, 'Description')) and not(contains(@aria-label, 'Thêm tiêu đề'))]")))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", desc_box)
                    time.sleep(1)
                    desc_box.click()
                    time.sleep(0.5)
                    desc_box.send_keys(Keys.CONTROL, 'a')
                    time.sleep(0.5)
                    desc_box.send_keys(Keys.BACKSPACE)
                    time.sleep(0.5)
                    self.type_slowly(desc_box, desc)
                except Exception as e:
                    self.log(f"[{uid}] [YouTube] Lỗi nhập mô tả: {e}")
                    return False
                    
            # Bước 7: Trẻ em
            yt_kids = self.account.get('yt_kids', '0')
            self.log(f"[{uid}] [YouTube] Chọn chính sách trẻ em...")
            try:
                if yt_kids == '1': # Có dành cho trẻ em
                    kids_radio = wait.until(EC.presence_of_element_located((By.XPATH, "//tp-yt-paper-radio-button[@name='VIDEO_MADE_FOR_KIDS_MFK'] | //tp-yt-paper-radio-button[.//ytcp-ve[contains(., 'Có, nội dung này dành cho trẻ em')]]")))
                else: # Không dành cho trẻ em
                    kids_radio = wait.until(EC.presence_of_element_located((By.XPATH, "//tp-yt-paper-radio-button[@name='VIDEO_MADE_FOR_KIDS_NOT_MFK'] | //tp-yt-paper-radio-button[.//ytcp-ve[contains(., 'Không, nội dung này không dành cho trẻ em')]]")))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", kids_radio)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", kids_radio)
            except Exception as e:
                self.log(f"[{uid}] [YouTube] Lỗi chọn chính sách trẻ em: {e}")
                return False
                
            # Bước 8, 9, 10: Bấm nút Tiếp x3
            self.log(f"[{uid}] [YouTube] Bấm Tiếp...")
            for i in range(3):
                try:
                    next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'ytcpButtonShapeImpl__button-text-content') and (text()='Tiếp' or text()='Next')] | //ytcp-button[@id='next-button']")))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", next_btn)
                    time.sleep(2)
                except Exception as e:
                    self.log(f"[{uid}] [YouTube] Lỗi khi bấm Tiếp (lần {i+1}): {e}")
                    return False
                    
            # Bước 11: Chọn Công khai
            self.log(f"[{uid}] [YouTube] Chọn Công khai...")
            try:
                public_radio = wait.until(EC.presence_of_element_located((By.XPATH, "//tp-yt-paper-radio-button[@name='PUBLIC'] | //tp-yt-paper-radio-button[.//div[contains(., 'Công khai') or contains(., 'Public')]]")))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", public_radio)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", public_radio)
            except Exception as e:
                self.log(f"[{uid}] [YouTube] Lỗi chọn Công khai: {e}")
                return False
                
            # Bước 12: Xuất bản
            self.log(f"[{uid}] [YouTube] Bấm Xuất bản...")
            try:
                publish_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'ytcpButtonShapeImpl__button-text-content') and (text()='Xuất bản' or text()='Publish')] | //ytcp-button[@id='done-button']")))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", publish_btn)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", publish_btn)
            except Exception as e:
                self.log(f"[{uid}] [YouTube] Lỗi bấm Xuất bản: {e}")
                return False
                
            # Đợi tải lên và xử lý video động
            self.log(f"[{uid}] [YouTube] Đang kiểm tra tiến trình tải lên/xử lý...")
            time.sleep(5)
            
            wait_timeout = 3600 # Tối đa 60 phút
            start_wait = time.time()
            last_status = ""
            
            uploaded_video_url = None
            while time.time() - start_wait < wait_timeout:
                if self.is_stopped():
                    break
                try:
                    dialogs = self.driver.find_elements(By.XPATH, "//ytcp-dialog | //tp-yt-paper-dialog")
                    if not dialogs or not dialogs[-1].is_displayed():
                        break
                        
                    dialog_text = dialogs[-1].text.lower()
                    
                    if not dialog_text:
                        break
                        
                    if "đã đăng video" in dialog_text or "video published" in dialog_text:
                        self.log(f"[{uid}] [YouTube] Bắt gặp thông báo 'Đã đăng video'. Xuất bản thành công!")
                        try:
                            link_els = dialogs[-1].find_elements(By.XPATH, ".//a[contains(@href, 'youtu.be') or contains(@href, 'youtube.com/watch') or contains(@href, 'youtube.com/shorts')]")
                            for l_el in link_els:
                                h = l_el.get_attribute('href')
                                if h and ('youtu.be' in h or '/watch' in h or '/shorts/' in h):
                                    uploaded_video_url = h
                                    self.log(f"[{uid}] [YouTube] Lấy được link video vừa xuất bản: {uploaded_video_url}")
                                    break
                        except Exception:
                            pass
                        break
                        
                    if "hoàn tất" in dialog_text or "đã xong" in dialog_text or "xử lý xong" in dialog_text or "complete" in dialog_text:
                        self.log(f"[{uid}] [YouTube] Quá trình tải lên/xử lý đã hoàn tất!")
                        try:
                            link_els = dialogs[-1].find_elements(By.XPATH, ".//a[contains(@href, 'youtu.be') or contains(@href, 'youtube.com/watch') or contains(@href, 'youtube.com/shorts')]")
                            for l_el in link_els:
                                h = l_el.get_attribute('href')
                                if h and ('youtu.be' in h or '/watch' in h or '/shorts/' in h):
                                    uploaded_video_url = h
                                    self.log(f"[{uid}] [YouTube] Lấy được link video vừa xuất bản: {uploaded_video_url}")
                                    break
                        except Exception:
                            pass
                        break
                        
                    # Lấy dòng thông báo trạng thái
                    status_lines = [line.strip() for line in dialog_text.split('\n') if ('%' in line or 'còn' in line or 'đang' in line or 'phút' in line or 'giây' in line) and len(line.strip()) > 5]
                    
                    # Nếu không còn dòng nào báo đang xử lý hoặc tải lên nữa thì thoát
                    if not status_lines:
                        self.log(f"[{uid}] [YouTube] Không thấy tiến trình nào đang chạy, tiếp tục đóng hộp thoại.")
                        break
                        
                    current_status = status_lines[-1]
                    
                    if current_status != last_status:
                        self.log(f"[{uid}] [YouTube] Trạng thái: {current_status}")
                        last_status = current_status
                        
                    time.sleep(10)
                except Exception:
                    time.sleep(10)
            
            # Bước 13: Đóng
            self.log(f"[{uid}] [YouTube] Bấm Đóng (nếu có)...")
            try:
                close_btn = self.driver.find_element(By.XPATH, "//div[contains(@class, 'ytcpButtonShapeImpl__button-text-content') and (text()='Đóng' or text()='Close')] | //ytcp-button[@id='close-button']")
                self.driver.execute_script("arguments[0].click();", close_btn)
                time.sleep(2)
            except Exception:
                pass
                
            self.log(f"[{uid}] [YouTube] Hoàn tất tiến trình Đăng YouTube Video!")
            
            # --- START YOUTUBE COMMENT AUTO ---
            cmt_yt = self.account.get('cmt_youtube', '0')
            cmt_text = self.account.get('cmt_text', '').strip()
            if cmt_yt == '1' and cmt_text:
                try:
                    self.log(f"[{uid}] [YouTube Comment] Đang chờ 60s (1 phút) để máy chủ YouTube render video và duyệt hoàn tất...")
                    time.sleep(60)
                    
                    from youtube_comment_video import comment_on_newest_youtube_video
                    def log_cb(msg):
                        self.log(f"[{uid}] [YouTube Comment] {msg}")
                    comment_on_newest_youtube_video(self.driver, cmt_text, log_cb, video_title=yt_title, direct_video_url=uploaded_video_url)
                except Exception as ex:
                    self.log(f"[{uid}] [YouTube Comment] Lỗi gọi file comment: {ex}")
            # --- END YOUTUBE COMMENT AUTO ---
            
            return True
            
        except Exception as e:
            self.log(f"[{uid}] [YouTube] Lỗi tiến trình YouTube: {e}")
            return False
        finally:
            try:
                self.driver.switch_to.default_content()
            except:
                pass
