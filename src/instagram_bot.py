import time
import os
import shutil
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidSessionIdException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from instagram_comment_post import comment_on_newest_instagram_post

class InstagramBot:
    def __init__(self, driver, account, log_callback, stop_event, type_slowly):
        self.driver = driver
        self.account = account
        self.log = log_callback
        self.stop_event = stop_event
        self.type_slowly = type_slowly

    def is_stopped(self):
        return self.stop_event and self.stop_event.is_set()

    def upload_post(self, video_path, image_path):
        uid = self.account.get('id', 'Unknown')
        
        # Decide media paths
        is_video = bool(video_path)
        paths = []
        if is_video:
            paths = [p.strip() for p in video_path.split('\n') if p.strip()]
        elif image_path:
            paths = [p.strip() for p in image_path.split('\n') if p.strip()]
            
        if not paths:
            self.log(f"[{uid}] [Instagram] Không có video/ảnh để đăng.")
            return False
            
        first_media = os.path.abspath(paths[0]).replace('\\', '/')
        ext = os.path.splitext(first_media)[1].lower()
        if ext in ['.mov', '.avi', '.mkv', '.wmv', '.flv', '.mp4']:
            if not first_media.lower().endswith('_h264.mp4'):
                mp4_path = os.path.splitext(first_media)[0] + "_h264.mp4"
                try:
                    if not os.path.exists(mp4_path):
                        self.log(f"[{uid}] [Instagram] Đang ép chuẩn video về H.264 (Có thể mất vài phút tuỳ độ dài video)...")
                        import subprocess
                        import imageio_ffmpeg
                        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                        cmd = [
                            ffmpeg_exe, "-y",
                            "-i", first_media,
                            "-c:v", "libx264",
                            "-crf", "18",
                            "-preset", "fast",
                            "-c:a", "aac",
                            "-b:a", "128k",
                            "-movflags", "+faststart",
                            mp4_path
                        ]
                        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                        self.log(f"[{uid}] [Instagram] Chuyển đổi thành công!")
                    
                    converted_video_path = mp4_path
                    first_media = mp4_path.replace('\\', '/')
                except Exception as e:
                    self.log(f"[{uid}] [Instagram] Lỗi xử lý video: {e}")
                    return False
            is_video = True

        max_retries = 3
        for attempt in range(max_retries):
            if self.is_stopped():
                return False
                
            try:
                if attempt > 0:
                    self.log(f"[{uid}] [Instagram] Đang thử lại lần {attempt + 1}... (Đã refresh trang)")
                    try:
                        self.driver.refresh()
                        time.sleep(5)
                    except:
                        pass
                
                # Bước 1: Truy cập trang chủ (Load 2 lần)
                self.log(f"[{uid}] [Instagram] Truy cập trang chủ...")
                self.driver.get("https://www.instagram.com/")
                time.sleep(4)
                if attempt == 0:
                    self.driver.refresh()
                    time.sleep(4)
                    self.driver.refresh()
                    time.sleep(4)
                
                wait = WebDriverWait(self.driver, 15)
                
                # Bước 2: Đăng nhập
                try:
                    login_indicator = wait.until(
                        EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Log in') or contains(., 'Đăng nhập')] | //input[@name='username']"))
                    )
                    if login_indicator:
                        self.log(f"[{uid}] [Instagram] Cần đăng nhập. Vui lòng đăng nhập trong 90 giây...")
                        WebDriverWait(self.driver, 90).until(
                            EC.presence_of_element_located((By.XPATH, "//*[local-name()='svg' and (@aria-label='Bài viết mới' or @aria-label='New post')] | //span[contains(text(), 'Trang chủ')]"))
                        )
                        self.log(f"[{uid}] [Instagram] Đăng nhập thành công!")
                        time.sleep(3)
                except TimeoutException:
                    self.log(f"[{uid}] [Instagram] Đã đăng nhập sẵn hoặc bỏ qua bước đăng nhập.")
                    
                # Bước 3 & 4: Popup "Tiếp tục" nếu có
                try:
                    continue_btn = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Tiếp tục')]/ancestor::div[@role='button'][1]")
                    self.driver.execute_script("arguments[0].click();", continue_btn)
                    time.sleep(2)
                    confirm_btn = self.driver.find_element(By.XPATH, "//button[@name='__CONFIRM__' and @type='submit']")
                    self.driver.execute_script("arguments[0].click();", confirm_btn)
                    time.sleep(2)
                except NoSuchElementException:
                    pass # Không có popup
                    
                # Bước 5: Click vào biểu tượng + (Bài viết mới)
                self.log(f"[{uid}] [Instagram] Click tạo bài viết mới...")
                new_post_svg = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[local-name()='svg' and (@aria-label='Bài viết mới' or @aria-label='New post')]/parent::*")))
                self.driver.execute_script("arguments[0].click();", new_post_svg)
                time.sleep(3)
                
                # Bước 6 & 7: Tải file lên
                self.log(f"[{uid}] [Instagram] Đang tải file lên...")
                file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file' or @accept]")))
                file_input.send_keys(first_media)
                time.sleep(5)
                
                # Bước 9: Click nút Tiếp lần 1
                next_btn_1 = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and (normalize-space(text())='Tiếp' or normalize-space(text())='Next')]")))
                self.driver.execute_script("arguments[0].click();", next_btn_1)
                time.sleep(3)
                
                # Bước 10: Click nút Tiếp lần 2
                next_btn_2 = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and (text()='Tiếp' or text()='Next') and not(@aria-disabled='true')]")))
                self.driver.execute_script("arguments[0].click();", next_btn_2)
                time.sleep(3)
                
                # Bước 11: Viết nội dung
                desc = self.account.get('description', '')
                if desc:
                    self.log(f"[{uid}] [Instagram] Đang viết nội dung...")
                    desc_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='textbox' and (contains(@aria-label, 'Viết chú thích') or contains(@aria-label, 'Write a caption'))]")))
                    self.type_slowly(desc_box, desc)
                    time.sleep(2)
                    
                # Bước 12: Xử lý 2 Checkbox (Threads & Facebook)
                is_ig_threads = self.account.get('is_ig_threads', '0') == '1'
                is_ig_fb = self.account.get('is_ig_fb', '0') == '1'
                
                is_ig_threads_txt = self.account.get('ig_threads_txt', '')
                is_ig_fb_txt = self.account.get('ig_fb_txt', '')
                
                    
                # Bước 13: Click Chia sẻ
                self.log(f"[{uid}] [Instagram] Nhấn Chia sẻ...")
                share_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and (normalize-space(text())='Chia sẻ' or normalize-space(text())='Share')]")))
                self.driver.execute_script("arguments[0].click();", share_btn)
                
                # Bước 14: Đợi nút Xong xuất hiện (chờ upload)
                try:
                    self.log(f"[{uid}] [Instagram] Chờ quá trình upload hoàn tất để bấm nút Xong (tối đa 120s)...")
                    done_btn = WebDriverWait(self.driver, 120).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and (text()='Xong' or text()='Done' or contains(., 'Xong') or contains(., 'Done'))] | //*[text()='Xong' or text()='Done']/ancestor-or-self::div[@role='button']"))
                    )
                    self.driver.execute_script("arguments[0].click();", done_btn)
                    self.log(f"[{uid}] [Instagram] Đã bấm nút Xong (Video đã đăng hoàn thành)!")
                    time.sleep(2)
                except Exception as e:
                    self.log(f"[{uid}] [Instagram] Lỗi chờ/click nút Xong: {e}")
                    
                is_ig_threads = self.account.get('is_ig_threads', '0') == '1'
                is_ig_fb = self.account.get('is_ig_fb', '0') == '1'
                
                if is_ig_threads or is_ig_fb:
                    try:
                        self.log(f"[{uid}] [Instagram] Bắt đầu chia sẻ sau khi đăng (Threads/Facebook)...")
                        
                        # Click vào nút "Trang cá nhân" trên menu thay vì dùng URL vì uid có thể là email
                        profile_btns = self.driver.find_elements(By.XPATH, "//span[text()='Trang cá nhân' or text()='Profile']")
                        if profile_btns:
                            self.driver.execute_script("arguments[0].click();", profile_btns[0])
                        else:
                            avatar_btns = self.driver.find_elements(By.XPATH, "//a[@role='link' and descendant::img[contains(@alt, 'Ảnh đại diện') or contains(@alt, 'profile picture')]]")
                            if avatar_btns:
                                self.driver.execute_script("arguments[0].click();", avatar_btns[0])
                            else:
                                self.log(f"[{uid}] [Instagram] Không tìm thấy nút về Trang cá nhân!")
                                
                        time.sleep(5)
                        
                        first_post_xpath = "//div[@class='x1ey2m1c xtijo5x x1o0tod x10l6tqk x13vifvy'] | //article//a[contains(@href, '/p/') or contains(@href, '/reel/')]"
                        first_post = self.driver.find_elements(By.XPATH, first_post_xpath)
                        if first_post:
                            self.driver.execute_script("arguments[0].click();", first_post[0])
                            time.sleep(3)
                            
                            if is_ig_threads:
                                try:
                                    self.log(f"[{uid}] [Instagram] Đang chia sẻ lên Threads...")
                                    dot_menu = self.driver.find_elements(By.XPATH, "//*[local-name()='svg' and @aria-label='Lựa chọn khác']")
                                    if dot_menu:
                                        dot_btn = dot_menu[0].find_element(By.XPATH, "./ancestor::button | ./ancestor::div[@role='button']")
                                        self.driver.execute_script("arguments[0].click();", dot_btn)
                                        time.sleep(2)
                                        
                                        share_to = self.driver.find_elements(By.XPATH, "//span[text()='Chia sẻ lên...' or text()='Share to...']")
                                        if share_to:
                                            self.driver.execute_script("arguments[0].click();", share_to[0])
                                            time.sleep(2)
                                            
                                            threads_link = self.driver.find_elements(By.XPATH, "//span[text()='Chia sẻ lên Threads' or text()='Share to Threads']")
                                            if threads_link:
                                                main_window = self.driver.current_window_handle
                                                ActionChains(self.driver).move_to_element(threads_link[0]).click().perform()
                                                time.sleep(3)
                                                
                                                for handle in self.driver.window_handles:
                                                    if handle != main_window:
                                                        self.driver.switch_to.window(handle)
                                                        break
                                                
                                                threads_txt_box = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@role='textbox'] | //p[@dir='auto']")))
                                                self.driver.execute_script("arguments[0].click();", threads_txt_box)
                                                time.sleep(1)
                                                threads_txt_box.send_keys(Keys.CONTROL + "a")
                                                threads_txt_box.send_keys(Keys.BACKSPACE)
                                                
                                                is_ig_threads_txt = self.account.get('ig_threads_txt', '')
                                                if is_ig_threads_txt:
                                                    self.type_slowly(threads_txt_box, is_ig_threads_txt)
                                                    
                                                time.sleep(3)
                                                post_btn = self.driver.find_elements(By.XPATH, "//*[text()='Post' or text()='Đăng' or text()='Bưu kiện' or text()='Đăng bài']")
                                                if post_btn:
                                                    self.driver.execute_script("arguments[0].click();", post_btn[-1])
                                                    self.log(f"[{uid}] [Instagram] Đã bấm Đăng Threads, đang chờ xử lý...")
                                                    time.sleep(10)
                                                    self.log(f"[{uid}] [Instagram] Chia sẻ Threads hoàn tất (thành công)!")
                                                    
                                                self.driver.close()
                                                self.driver.switch_to.window(main_window)
                                                time.sleep(1)
                                except Exception as e:
                                    self.log(f"[{uid}] [Instagram] Lỗi chia sẻ Threads: {e}")
                                    try:
                                        self.driver.switch_to.window(self.driver.window_handles[0])
                                    except:
                                        pass
                                        
                            if is_ig_fb:
                                try:
                                    self.log(f"[{uid}] [Instagram] Đang chia sẻ lên Facebook...")
                                    dot_menu = self.driver.find_elements(By.XPATH, "//*[local-name()='svg' and @aria-label='Lựa chọn khác']")
                                    if dot_menu:
                                        dot_btn = dot_menu[0].find_element(By.XPATH, "./ancestor::button | ./ancestor::div[@role='button']")
                                        self.driver.execute_script("arguments[0].click();", dot_btn)
                                        time.sleep(2)
                                        
                                        share_to = self.driver.find_elements(By.XPATH, "//span[text()='Chia sẻ lên...' or text()='Share to...']")
                                        if share_to:
                                            self.driver.execute_script("arguments[0].click();", share_to[0])
                                            time.sleep(2)
                                            
                                            fb_btn = self.driver.find_elements(By.XPATH, "//span[text()='Chia sẻ lên Facebook' or text()='Share to Facebook']")
                                            if fb_btn:
                                                main_window = self.driver.current_window_handle
                                                ActionChains(self.driver).move_to_element(fb_btn[0]).click().perform()
                                                time.sleep(3)
                                                
                                                for handle in self.driver.window_handles:
                                                    if handle != main_window:
                                                        self.driver.switch_to.window(handle)
                                                        break
                                                
                                                fb_txt_box = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']")))
                                                self.driver.execute_script("arguments[0].click();", fb_txt_box)
                                                time.sleep(1)
                                                fb_txt_box.send_keys(Keys.CONTROL + "a")
                                                fb_txt_box.send_keys(Keys.BACKSPACE)
                                                
                                                is_ig_fb_txt = self.account.get('ig_fb_txt', '')
                                                if is_ig_fb_txt:
                                                    self.type_slowly(fb_txt_box, is_ig_fb_txt)
                                                    time.sleep(1)
                                                    
                                                fb_next = self.driver.find_elements(By.XPATH, "//div[@role='button' and (@aria-label='Tiếp' or @aria-label='Next' or contains(., 'Tiếp') or contains(., 'Next'))]")
                                                if fb_next:
                                                    self.driver.execute_script("arguments[0].click();", fb_next[0])
                                                    time.sleep(3)
                                                    
                                                fb_share = self.driver.find_elements(By.XPATH, "//div[@role='button' and (@aria-label='Chia sẻ' or @aria-label='Share' or contains(., 'Chia sẻ') or contains(., 'Share') or contains(., 'Đăng') or contains(., 'Post') or contains(., 'Bưu kiện'))]")
                                                if fb_share:
                                                    self.driver.execute_script("arguments[0].click();", fb_share[-1])
                                                    self.log(f"[{uid}] [Instagram] Đã bấm chia sẻ FB, chờ 60s để hoàn tất...")
                                                    time.sleep(60)
                                                    self.log(f"[{uid}] [Instagram] Chia sẻ FB hoàn tất (thành công)!")
                                                    
                                                self.driver.close()
                                                self.driver.switch_to.window(main_window)
                                                time.sleep(1)
                                except Exception as e:
                                    self.log(f"[{uid}] [Instagram] Lỗi chia sẻ Facebook: {e}")
                                    try:
                                        self.driver.switch_to.window(self.driver.window_handles[0])
                                    except:
                                        pass
                    except Exception as e:
                        self.log(f"[{uid}] [Instagram] Lỗi click bài đăng mới nhất: {e}")

                # Tích hợp comment sau khi đã hoàn thành toàn bộ chức năng đăng bài / chia sẻ
                if self.account.get('cmt_instagram', '0') == '1':
                    comment_text = self.account.get('cmt_text', '')
                    if comment_text:
                        comment_on_newest_instagram_post(self.driver, comment_text, lambda msg: self.log(f"[{uid}] {msg}"))
                    else:
                        self.log(f"[{uid}] [Instagram] Đã tích comment nhưng không có nội dung comment.")

                if 'converted_video_path' in locals() and converted_video_path and os.path.exists(converted_video_path):
                    try:
                        os.remove(converted_video_path)
                        self.log(f"[{uid}] [Instagram] Đã xoá video tạm sau khi đăng thành công.")
                    except Exception as e:
                        pass

                return True
                
            except InvalidSessionIdException:
                self.log(f"[{uid}] [Instagram] Trình duyệt đã bị đóng đột ngột!")
                return False
            except Exception as e:
                self.log(f"[{uid}] [Instagram] Lỗi (không tìm thấy nút click hoặc lỗi khác): {e}")
                if attempt == max_retries - 1:
                    import traceback
                    traceback.print_exc()
                    return False
        return False
