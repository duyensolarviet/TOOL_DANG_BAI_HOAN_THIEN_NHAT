import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def comment_on_newest_threads_post(driver, comment_text, log_callback):
    """
    Chức năng: Comment dưới bài viết vừa đăng trên Threads.
    Được tối ưu tương thích 100% với giao diện Threads Web mới nhất.
    """
    if not comment_text:
        return False
        
    wait = WebDriverWait(driver, 15)
    
    try:
        log_callback("Bắt đầu chức năng: Comment dưới bài viết vừa đăng (Threads).")
        
        # Bước 1: Điều hướng vào trang cá nhân Threads
        log_callback("Bước 1: Truy cập trang cá nhân Threads...")
        
        # Thử lấy link trang cá nhân trực tiếp từ menu điều hướng
        profile_url = driver.execute_script("""
            let links = document.querySelectorAll("a[href*='/@']");
            for (let a of links) {
                if (a.href && a.href.includes('/@')) {
                    return a.href;
                }
            }
            return '';
        """)
        
        if profile_url:
            log_callback(f"Tìm thấy link trang cá nhân: {profile_url}, đang truy cập...")
            driver.get(profile_url)
            time.sleep(5)
        else:
            log_callback("Không lấy được link trực tiếp, về trang chủ Threads và tìm nút Profile...")
            driver.get("https://www.threads.net/")
            time.sleep(5)
            
            # Click nút Trang cá nhân
            clicked_profile = False
            profile_selectors = [
                "//a[contains(@href, '/@')]",
                "//*[@aria-label='Trang cá nhân' or @aria-label='Profile']",
                "//div[@role='button'][.//*[local-name()='svg' and (@aria-label='Trang cá nhân' or @aria-label='Profile')]]"
            ]
            for sel in profile_selectors:
                try:
                    btns = driver.find_elements(By.XPATH, sel)
                    for b in reversed(btns):
                        if b.is_displayed():
                            driver.execute_script("arguments[0].click();", b)
                            clicked_profile = True
                            time.sleep(5)
                            break
                    if clicked_profile:
                        break
                except:
                    pass
                    
        # Cuộn nhẹ xuống để nạp bài viết mới nhất
        log_callback("Bước 2: Cuộn xuống tìm bài viết Threads mới nhất...")
        driver.execute_script("window.scrollBy(0, 350);")
        time.sleep(3)
        
        # Bước 3: Tìm nút Trả lời (Bình luận) trên bài viết đầu tiên
        log_callback("Bước 3: Mở khung bình luận (Trả lời)...")
        reply_btn_xpaths = [
            "(//div[@role='button'][.//*[local-name()='svg' and (@aria-label='Trả lời' or @aria-label='Reply')]])[1]",
            "(//*[local-name()='svg' and (@aria-label='Trả lời' or @aria-label='Reply')])[1]",
            "(//div[@role='button' and (contains(@aria-label, 'Trả lời') or contains(@aria-label, 'Reply'))])[1]",
            "(//*[local-name()='svg' and descendant::*[local-name()='title' and (text()='Trả lời' or text()='Reply')]])[1]"
        ]
        
        reply_btn = None
        for xp in reply_btn_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xp)
                for el in elements:
                    if el.is_displayed():
                        reply_btn = el
                        break
                if reply_btn:
                    break
            except:
                continue
                
        if not reply_btn:
            raise Exception("Không tìm thấy nút Trả lời / Bình luận trên bài viết Threads.")
            
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reply_btn)
        time.sleep(1)
        
        try:
            ActionChains(driver).move_to_element(reply_btn).click().perform()
        except:
            driver.execute_script("arguments[0].click();", reply_btn)
        time.sleep(2.5)
        
        # Bước 4: Nhập nội dung bình luận
        log_callback("Bước 4: Nhập nội dung bình luận...")
        textbox_xpaths = [
            "//div[@role='dialog']//div[@role='textbox' and @contenteditable='true']",
            "//div[@role='textbox' and @contenteditable='true']",
            "//div[@contenteditable='true' and contains(@aria-label, 'Trả lời')]",
            "//div[@contenteditable='true']"
        ]
        
        textbox = None
        for xp in textbox_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xp)
                for el in reversed(elements):
                    if el.is_displayed():
                        textbox = el
                        break
                if textbox:
                    break
            except:
                continue
                
        if not textbox:
            raise Exception("Không tìm thấy ô nhập bình luận trên Threads.")
            
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textbox)
        time.sleep(1)
        
        try:
            textbox.click()
        except:
            driver.execute_script("arguments[0].click();", textbox)
        time.sleep(1)
        
        # Nhập văn bản từng ký tự
        lines = comment_text.split('\n')
        for l_idx, line in enumerate(lines):
            for char in line:
                textbox.send_keys(char)
                time.sleep(random.uniform(0.015, 0.04))
            if l_idx < len(lines) - 1:
                textbox.send_keys(Keys.SHIFT, Keys.ENTER)
                time.sleep(0.1)
        time.sleep(2)
        
        # Bước 5: Click nút Đăng hoặc gửi phím Ctrl+Enter
        log_callback("Bước 5: Gửi bình luận...")
        post_btn_xpaths = [
            "//div[@role='dialog']//div[@role='button' and (text()='Đăng' or text()='Post' or text()='Trả lời' or text()='Reply')]",
            "//div[@role='button' and (text()='Đăng' or text()='Post' or text()='Trả lời' or text()='Reply')]",
            "//div[@role='dialog']//div[contains(@class, 'x1i10hfl') and @role='button' and (text()='Đăng' or text()='Post')]"
        ]
        
        post_btn = None
        for xp in post_btn_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xp)
                for el in reversed(elements):
                    if el.is_displayed():
                        post_btn = el
                        break
                if post_btn:
                    break
            except:
                continue
                
        if post_btn:
            try:
                driver.execute_script("arguments[0].click();", post_btn)
            except:
                ActionChains(driver).move_to_element(post_btn).click().perform()
        else:
            log_callback("Không tìm thấy nút Đăng dạng text, dùng phím tắt Ctrl+Enter...")
            textbox.send_keys(Keys.CONTROL, Keys.ENTER)
            
        time.sleep(4)
        log_callback("Đã bình luận thành công trên Threads!")
        return True
        
    except Exception as e:
        log_callback(f"Lỗi khi comment Threads: {e}")
        return False
