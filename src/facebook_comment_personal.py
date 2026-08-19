import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

def comment_on_personal_post(driver, log_callback, comment_text):
    """
    Chức năng: Comment dưới bài viết / Reels vừa đăng trên Facebook cá nhân.
    Tự động cuộn trang tìm đúng bài đăng mới nhất và mở ô bình luận.
    """
    if not comment_text:
        return
        
    try:
        log_callback("Bắt đầu chức năng: Comment bài viết trên trang cá nhân FB.")
        
        # Bước 1: Vào trang cá nhân fb
        log_callback("Bước 1: Vào trang cá nhân fb...")
        driver.get("https://www.facebook.com/me")
        time.sleep(5)
        
        # Cuộn xuống tìm bài viết / Reels đầu tiên
        log_callback("Bước 2: Cuộn xuống tìm bài viết / Reels đầu tiên...")
        first_post = None
        for scroll_count in range(6):
            articles = driver.find_elements(
                By.XPATH, 
                "//div[@role='article'] | //div[contains(@data-pagelet, 'FeedUnit')] | //div[contains(@class, 'userContentWrapper')] | //div[contains(@data-pagelet, 'ProfileTimeline')]//div[@role='article']"
            )
            for art in articles:
                try:
                    if art.is_displayed() and art.size['height'] > 60:
                        first_post = art
                        break
                except:
                    pass
            if first_post:
                break
            driver.execute_script("window.scrollBy(0, 400);")
            time.sleep(2)
            
        if first_post:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_post)
                time.sleep(2)
            except:
                pass
        else:
            driver.execute_script("window.scrollBy(0, 400);")
            time.sleep(2)
        
        # Bước 3: Tìm nút 'Bình luận' của bài viết đầu tiên để kích hoạt mở ô nhập
        log_callback("Bước 3: Mở khung bình luận của bài viết mới nhất...")
        cmt_btn_xpaths = [
            ".//div[@role='button' and (contains(@aria-label, 'Bình luận') or contains(@aria-label, 'Viết bình luận') or contains(@aria-label, 'Comment') or contains(@aria-label, 'Leave a comment'))]",
            ".//div[@role='button'][.//span[contains(text(), 'Bình luận') or contains(text(), 'Comment')]]",
            "(//div[@role='article']//div[@role='button' and (contains(@aria-label, 'Bình luận') or contains(@aria-label, 'Viết bình luận') or contains(@aria-label, 'Comment'))])[1]",
            "(//div[@role='article']//div[@role='button'][.//span[contains(text(), 'Bình luận') or contains(text(), 'Comment')]])[1]",
            "(//div[@role='button' and (contains(@aria-label, 'Bình luận') or contains(@aria-label, 'Viết bình luận'))])[1]",
            "(//span[text()='Bình luận' or text()='Comment']/ancestor::div[@role='button'])[1]"
        ]
        
        btn_clicked = False
        search_contexts = [first_post, driver] if first_post else [driver]
        for ctx in search_contexts:
            for xp in cmt_btn_xpaths:
                try:
                    elements = ctx.find_elements(By.XPATH, xp)
                    for el in elements:
                        if el.is_displayed():
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                            time.sleep(1)
                            try:
                                el.click()
                            except:
                                driver.execute_script("arguments[0].click();", el)
                            btn_clicked = True
                            time.sleep(2)
                            break
                    if btn_clicked:
                        break
                except:
                    continue
            if btn_clicked:
                break

        # Bước 4: Tìm ô nhập bình luận (Lexical Textbox)
        log_callback("Bước 4: Định vị ô nhập bình luận...")
        textbox_xpaths = [
            "//div[@role='textbox' and (contains(@aria-label, 'Bình luận') or contains(@aria-label, 'Viết') or contains(@aria-label, 'Comment'))]",
            "//div[@role='textbox' and @contenteditable='true']",
            "//div[@role='textbox' and @data-lexical-editor='true']",
            "(//div[@role='textbox'])[last()]",
            "(//div[@role='textbox'])[1]"
        ]
        
        textbox = None
        for _ in range(8):
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
            if textbox:
                break
            time.sleep(1)
                
        if not textbox:
            raise Exception("Không tìm thấy ô nhập bình luận (div role='textbox').")
            
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textbox)
        time.sleep(1)
        try:
            ActionChains(driver).move_to_element(textbox).click().perform()
        except:
            driver.execute_script("arguments[0].click();", textbox)
        time.sleep(1)
        
        # Bước 5: Nhập nội dung
        log_callback(f"Bước 5: Nhập nội dung: {comment_text}")
        lines = comment_text.split('\n')
        for l_idx, line in enumerate(lines):
            for char in line:
                textbox.send_keys(char)
                time.sleep(random.uniform(0.015, 0.04))
            if l_idx < len(lines) - 1:
                textbox.send_keys(Keys.SHIFT, Keys.ENTER)
                time.sleep(0.1)
        time.sleep(2)
        
        # Bước 6: Ấn nút gửi bình luận
        log_callback("Bước 6: Ấn nút Đăng bình luận...")
        send_btn_xpaths = [
            "//div[@role='button' and (contains(@aria-label, 'Đăng bình luận') or contains(@aria-label, 'Đăng') or contains(@aria-label, 'Send') or contains(@aria-label, 'Post'))]",
            "//div[@role='button'][.//*[local-name()='path' and starts-with(@d, 'M1.32 6.2')]]",
            "//div[@role='button'][.//*[local-name()='svg'] and (contains(@aria-label, 'Bình luận') or contains(@aria-label, 'Đăng'))]"
        ]
        
        send_btn = None
        for xp in send_btn_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xp)
                for el in reversed(elements):
                    if el.is_displayed():
                        send_btn = el
                        break
                if send_btn:
                    break
            except:
                continue
                
        if send_btn:
            try:
                driver.execute_script("arguments[0].click();", send_btn)
            except:
                ActionChains(driver).move_to_element(send_btn).click().perform()
        else:
            log_callback("Không tìm thấy nút Đăng dạng icon, gửi phím Enter...")
            textbox.send_keys(Keys.ENTER)
            
        # Bước 7: Đợi load hoàn tất
        log_callback("Bước 7: Đợi 3 giây để hoàn tất lưu bình luận...")
        time.sleep(3)
        log_callback("Hoàn tất comment bài viết cá nhân thành công!")
        
    except Exception as e:
        log_callback(f"Lỗi khi comment cá nhân: {e}")
