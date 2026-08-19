import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

def comment_on_zalo_video(driver, log_callback, comment_text):
    """
    Chức năng: Comment dưới video vừa đăng trên Zalo Video.
    File độc lập theo yêu cầu tạo ra file mới không đụng tới chức năng khác.
    """
    if not comment_text:
        return
        
    try:
        log_callback("Bắt đầu chức năng: Comment dưới bài viết vừa đăng (Zalo video).")
        
        # Bước 1: Truy cập url
        log_callback("Bước 1: Truy cập trang danh sách video Zalo Creator: https://video.zalo.me/creator/video")
        driver.get("https://video.zalo.me/creator/video")
        time.sleep(5)
        
        # Bước 2: Click vào video mới nhất
        log_callback("Bước 2: Click vào video mới nhất...")
        video_xpath = "(//img[@class='w-full h-full object-cover rounded-sm'])[1]"
        
        video_clicked = False
        try:
            video_el = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, video_xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", video_el)
            time.sleep(1)
            try:
                driver.execute_script("arguments[0].click();", video_el)
                video_clicked = True
            except:
                ActionChains(driver).move_to_element(video_el).click().perform()
                video_clicked = True
        except:
            pass
            
        if not video_clicked:
            log_callback("Không click được trực tiếp, tự tạo mô phỏng click dưới bài viết có chữ bài đăng...")
            try:
                # Mô phỏng click dưới bài viết có chữ bài đăng
                fallback_xpaths = [
                    "//div[contains(text(), 'bài đăng') or contains(text(), 'Bài đăng')]/following::img[1]",
                    "(//img)[1]"
                ]
                for fb_xpath in fallback_xpaths:
                    try:
                        fb_el = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, fb_xpath))
                        )
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fb_el)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", fb_el)
                        video_clicked = True
                        break
                    except:
                        pass
            except Exception as e:
                log_callback(f"Lỗi khi mô phỏng click dự phòng: {e}")
                
        if not video_clicked:
            raise Exception("Không thể tìm hoặc click vào video mới nhất.")
            
        time.sleep(5)
        
        # Bước 3: Click vào nhập nội dung cần comment
        log_callback(f"Bước 3: Nhập nội dung comment: {comment_text}")
        input_xpath = "//input[contains(@class, 'ant-input') and @type='text']"
        
        cmt_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, input_xpath))
        )
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cmt_input)
        time.sleep(1)
        
        try:
            cmt_input.click()
        except:
            driver.execute_script("arguments[0].click();", cmt_input)
            
        time.sleep(1)
        
        for char in comment_text:
            cmt_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        time.sleep(1)
        
        # Bước 4: Click vào nút gửi
        log_callback("Bước 4: Click nút Gửi bình luận...")
        send_btn_xpath = "//div[text()='Gửi']"
        
        send_btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, send_btn_xpath))
        )
        
        try:
            driver.execute_script("arguments[0].click();", send_btn)
        except:
            ActionChains(driver).move_to_element(send_btn).click().perform()
            
        log_callback("Đã click nút gửi. Chờ 3 giây để load nội dung...")
        time.sleep(3)
        
        log_callback("Hoàn tất comment Zalo Video thành công!")
        
    except Exception as e:
        log_callback(f"Lỗi khi comment Zalo Video: {e}")
