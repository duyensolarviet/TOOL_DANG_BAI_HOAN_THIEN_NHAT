import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

class ZaloBot:
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
            time.sleep(5)
            
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
            
            self.log(f"[{uid}] [Zalo] Đợi 60 giây để xử lý video hoàn tất...")
            time.sleep(60)
            
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
            
        except Exception as e:
            self.log(f"[{uid}] [Zalo] Lỗi tiến trình Zalo: {e}")


