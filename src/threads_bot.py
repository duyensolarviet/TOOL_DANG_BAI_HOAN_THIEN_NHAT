import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException
import os
from threads_comment_post import comment_on_newest_threads_post

class ThreadsBot:
    def __init__(self, driver, account, log_callback, stop_event, type_slowly_func):
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

    def robust_click(self, element):
        try:
            element.click()
        except:
            try:
                self.driver.execute_script("arguments[0].click();", element)
            except:
                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", element)

    def upload_post(self, video_path, image_path):
        uid = self.account.get('id', 'Unknown')
        self.log(f"[{uid}] [Threads] Truy cập trang chủ Threads...")
        
        try:
            # Bước 1: Truy cập và F5 2 lần
            self.driver.get("https://www.threads.net/")
            time.sleep(4)
            self.driver.refresh()
            time.sleep(4)
            self.driver.refresh()
            time.sleep(4)

            wait = WebDriverWait(self.driver, 15)

            media_paths = []
            if video_path:
                media_paths.extend([p.strip() for p in video_path.split('\n') if p.strip()])
            if image_path:
                media_paths.extend([p.strip() for p in image_path.split('\n') if p.strip()])
            
            first_media = media_paths[0] if media_paths else ""
            if not first_media or not os.path.isfile(first_media):
                if not self.account.get('description'):
                    self.log(f"[{uid}] [Threads] Không có nội dung hoặc file hợp lệ để đăng.")
                    return False

            try:
                login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Đăng nhập' or text()='Log in']")))
                if login_btn:
                    self.log(f"[{uid}] [Threads] Yêu cầu đăng nhập, Threads chưa lưu phiên!")
                    # Click đăng nhập bằng Instagram
                    self.robust_click(login_btn)
                    time.sleep(3)
                    ig_login = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Tiếp tục với Instagram') or contains(text(), 'Continue with Instagram')]")))
                    self.robust_click(ig_login)
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Trường văn bản trống. Hãy nhập vào để soạn bài viết mới.' or @aria-label='Ô trống để soạn bài viết mới.' or contains(text(), 'Có gì mới?')]"))
                    )
                    self.log(f"[{uid}] [Threads] Đăng nhập thành công!")
                    time.sleep(3)
            except TimeoutException:
                self.log(f"[{uid}] [Threads] Đã đăng nhập sẵn hoặc bỏ qua bước đăng nhập.")

            # Bước 2: Click vào ô "Có gì mới?"
            self.log(f"[{uid}] [Threads] Mở khung soạn thảo bài viết mới...")
            new_post_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Trường văn bản trống. Hãy nhập vào để soạn bài viết mới.' or @aria-label='Ô trống để soạn bài viết mới.' or @aria-label='Start a thread' or @aria-label='Start a thread...'] | //span[contains(text(), 'Có gì mới?') or contains(text(), 'Start a thread')]")))
            self.robust_click(new_post_box)
            time.sleep(2)

            # Bước 3: Điền nội dung
            desc = self.account.get('description', '')
            if desc:
                self.log(f"[{uid}] [Threads] Đang viết nội dung...")
                try:
                    text_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true']")))
                    self.robust_click(text_input)
                    time.sleep(1)
                    self.type_slowly(text_input, desc)
                    time.sleep(2)
                except Exception as e:
                    self.log(f"[{uid}] [Threads] Không thể điền nội dung: {e}")

            # Bước 4: Đính kèm phương tiện
            if first_media:
                self.log(f"[{uid}] [Threads] Đang tải file lên...")
                try:
                    file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file' or @accept]")))
                    file_input.send_keys(first_media)
                    self.log(f"[{uid}] [Threads] Đợi video/ảnh load (10-15s)...")
                    time.sleep(12)
                except Exception as e:
                    self.log(f"[{uid}] [Threads] Không tìm thấy input file ẩn: {e}")
                
            # Đợi hiển thị nút Đăng rồi click
            self.log(f"[{uid}] [Threads] Đang tìm nút Đăng (Post)...")
            post_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "(//div[@role='dialog']//div[text()='Đăng' or text()='Post' or text()='Bưu kiện'])[last()] | (//div[@role='dialog']//div[contains(@class, 'xc26acl') and (text()='Đăng' or text()='Post')])[last()]")))
            self.robust_click(post_btn)

            # Bước 5 & 6: Chờ tiến trình Đang đăng và Đã đăng
            self.log(f"[{uid}] [Threads] Chờ quá trình upload đăng bài hoàn tất (tối đa 120s)...")
            try:
                wait_long = WebDriverWait(self.driver, 120)
                # Theo dõi thông báo "Đã đăng"
                success_toast = wait_long.until(EC.presence_of_element_located((By.XPATH, "//*[text()='Đã đăng' or text()='Posted' or contains(text(), 'Đã đăng')]")))
                if success_toast:
                    self.log(f"[{uid}] [Threads] đăng thành công instagram (Threads) - Xác minh qua thông báo!")
            except TimeoutException:
                self.log(f"[{uid}] [Threads] Hết thời gian chờ 120s nhưng không thấy thông báo 'Đã đăng'.")
                
            # Tích hợp comment sau khi đã hoàn thành toàn bộ chức năng đăng bài
            if self.account.get('cmt_threads', '0') == '1':
                comment_text = self.account.get('cmt_text', '')
                if comment_text:
                    comment_on_newest_threads_post(self.driver, comment_text, lambda msg: self.log(f"[{uid}] {msg}"))
                else:
                    self.log(f"[{uid}] [Threads] Đã tích comment nhưng không có nội dung comment.")

            return True

        except InvalidSessionIdException:
            self.log(f"[{uid}] [Threads] Trình duyệt đã bị đóng đột ngột!")
            return False
        except Exception as e:
            self.log(f"[{uid}] [Threads] Lỗi tiến trình Threads: {e}")
            return False
