import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

class TikTokBot:
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
            
            # BƯỚC MỚI: Tự động thêm nhạc (Add sound -> Use)
            self.log(f"[{uid}] [TikTok] Tìm nút thêm nhạc...")
            try:
                add_sound_btns = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'Button__content') and (contains(., 'Add sound') or contains(., 'Thêm âm thanh') or contains(., 'Thêm nhạc'))] | //div[text()='Add sound' or text()='Thêm âm thanh' or text()='Thêm nhạc'] | //span[text()='Add sound' or text()='Thêm âm thanh'] | //button[contains(., 'Add sound') or contains(., 'Thêm âm thanh')]")
                add_sound_btn = None
                for btn in add_sound_btns:
                    if btn.is_displayed():
                        add_sound_btn = btn
                        break
                
                if add_sound_btn:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_sound_btn)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", add_sound_btn)
                    self.log(f"[{uid}] [TikTok] Đã bấm 'Add sound', đợi 3 giây tải danh sách nhạc...")
                    time.sleep(3)
                    
                    use_btns = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'Button__content') and (text()='Use' or text()='Dùng' or text()='Sử dụng')] | //button[text()='Use' or text()='Dùng' or text()='Sử dụng'] | //div[text()='Use' or text()='Dùng' or text()='Sử dụng']")
                    visible_use_btns = [btn for btn in use_btns if btn.is_displayed()]
                    
                    if visible_use_btns:
                        import random
                        random_use_btn = random.choice(visible_use_btns)
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", random_use_btn)
                        time.sleep(1)
                        self.driver.execute_script("arguments[0].click();", random_use_btn)
                        self.log(f"[{uid}] [TikTok] Đã chọn và thêm nhạc ngẫu nhiên thành công!")
                        time.sleep(2)
                    else:
                        self.log(f"[{uid}] [TikTok] Không tìm thấy nút 'Use' nhạc nào.")
                else:
                    self.log(f"[{uid}] [TikTok] Không tìm thấy nút 'Add sound', bỏ qua bước thêm nhạc.")
            except Exception as e:
                self.log(f"[{uid}] [TikTok] Lỗi khi thêm nhạc: {e}")
            
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


