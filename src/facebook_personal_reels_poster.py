import time
import os
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def upload_personal_reel(driver, account, log_callback, video_path):
    """
    Xử lý đăng Reels lên Facebook Cá Nhân.
    Code được tách riêng ra 1 file để dễ quản lý.
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    acc_id = account.get('id', 'Unknown')
    desc = account.get('description', '')

    log(f"[{acc_id}] ===== BẮT ĐẦU ĐĂNG REELS CÁ NHÂN =====")

    try:
        # Bước 1: truy cập vào https://www.facebook.com/ load trang 2 lần
        log(f"[{acc_id}] [Bước 1] Truy cập facebook.com và load lại trang...")
        driver.get("https://www.facebook.com/")
        time.sleep(4)
        driver.refresh()
        time.sleep(4)
        driver.refresh()
        time.sleep(5)

        # Bước 2: click vào thước phim
        # xpath : //div[@aria-label='Thước phim' and @role='button']
        log(f"[{acc_id}] [Bước 2] Tìm và click nút 'Thước phim'...")
        try:
            reels_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Thước phim' and @role='button']"))
            )
            driver.execute_script("arguments[0].click();", reels_tab)
            time.sleep(3)
        except Exception as e:
            log(f"[{acc_id}] Không tìm thấy nút Thước phim (Reels): {e}")
            return

        # Bước 3: Đưa đường dẫn ngầm video vào
        log(f"[{acc_id}] [Bước 3] Tải video lên...")
        try:
            # Chờ phần tử chứa chữ "Thêm video" hoặc "kéo và thả" xuất hiện (dựa trên HTML user cung cấp)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Thêm video' or text()='hoặc kéo và thả']"))
            )
            time.sleep(1) # Đợi thêm một xíu cho DOM load hoàn toàn thẻ input
            
            # Facebook có nhiều thẻ input file ngầm (của bài viết thường, của Reels, v.v.)
            # Lấy tất cả và gửi đường dẫn vào thẻ cuối cùng (thẻ thuộc về popup Reels mới mở)
            file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
            if file_inputs:
                file_input = file_inputs[-1]
                abs_path = os.path.abspath(video_path)
                file_input.send_keys(abs_path)
            else:
                log(f"[{acc_id}] Lỗi: Không tìm thấy thẻ input file nào trên trang.")
                return
        except Exception as e:
            log(f"[{acc_id}] Lỗi truyền file video: {e}")
            return

        # Bước 4: đợi load 10~15 giây
        wait_time = random.uniform(10, 15)
        log(f"[{acc_id}] [Bước 4] Chờ {wait_time:.1f}s để tải video...")
        time.sleep(wait_time)

        # Bước 5: click vào nút Tiếp
        # xpath : //span[text()='Tiếp']/ancestor::div[@role='button'][1]
        log(f"[{acc_id}] [Bước 5] Bấm nút 'Tiếp' lần 1...")
        try:
            tiep_1 = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Tiếp']/ancestor::div[@role='button'][1]"))
            )
            driver.execute_script("arguments[0].click();", tiep_1)
            time.sleep(5)
        except Exception as e:
            log(f"[{acc_id}] Không bấm được nút Tiếp 1: {e}")

        # Bước 6: click vào nút Tiếp : (//div[@aria-label='Tiếp' and @role='button'])[last()]
        log(f"[{acc_id}] [Bước 6] Bấm nút 'Tiếp' lần 2...")
        try:
            tiep_2_els = driver.find_elements(By.XPATH, "//div[@aria-label='Tiếp' and @role='button']")
            valid_tiep_2 = [el for el in tiep_2_els if el.is_displayed()]
            if valid_tiep_2:
                tiep_2 = valid_tiep_2[-1]
                driver.execute_script("arguments[0].click();", tiep_2)
                time.sleep(5)
            else:
                log(f"[{acc_id}] Không tìm thấy nút Tiếp lần 2.")
        except Exception as e:
            log(f"[{acc_id}] Không bấm được nút Tiếp 2: {e}")

        # Bước 7: click vào mô tả thước phim của bạn
        # xpath : //div[@aria-placeholder='Mô tả thước phim của bạn...']
        if desc:
            log(f"[{acc_id}] [Bước 7] Viết mô tả từ từ...")
            try:
                desc_box = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@aria-placeholder='Mô tả thước phim của bạn...']"))
                )
                desc_box.click()
                time.sleep(1)
                
                for char in desc:
                    if char == '\n':
                        desc_box.send_keys(Keys.SHIFT, Keys.ENTER)
                        time.sleep(random.uniform(0.5, 1.0))
                    else:
                        desc_box.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.15))
                        if char in ['.', ',', '!', '?', ':', ';']:
                            time.sleep(random.uniform(0.3, 0.8))
                
                time.sleep(2)
            except Exception as e:
                log(f"[{acc_id}] Lỗi khi viết mô tả: {e}")

        # Bước 8: click vào nút Đăng hoặc post
        # xpath : (//div[@aria-label='Đăng' and @role='button'])[last()]
        log(f"[{acc_id}] [Bước 8] Tìm và bấm nút Đăng...")
        try:
            post_els = driver.find_elements(By.XPATH, "//div[@aria-label='Đăng' and @role='button']")
            valid_post = [el for el in post_els if el.is_displayed()]
            if valid_post:
                btn_post = valid_post[-1]
                driver.execute_script("arguments[0].click();", btn_post)
                log(f"[{acc_id}] Đã bấm nút Đăng.")
            else:
                log(f"[{acc_id}] Không tìm thấy nút Đăng.")
        except Exception as e:
            log(f"[{acc_id}] Không bấm được nút Đăng: {e}")

        # Bước 9: đợi upload tối đa 120s
        log(f"[{acc_id}] [Bước 9] Chờ tối đa 120s để tải lên hoàn tất...")
        time.sleep(120)
        
        log(f"[{acc_id}] ===== HOÀN TẤT ĐĂNG REELS CÁ NHÂN =====")
        return True

    except Exception as e:
        log(f"[{acc_id}] Lỗi trong quá trình đăng Reels Cá Nhân: {e}")
        return False
