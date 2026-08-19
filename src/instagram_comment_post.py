import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def comment_on_newest_instagram_post(driver, comment_text, log_callback):
    """
    Chức năng: Comment dưới bài viết vừa đăng trên Instagram đa nền tảng.
    Xử lý chống stale element reference khi Instagram tự render lại khung soạn thảo.
    """
    if not comment_text:
        return False
        
    wait = WebDriverWait(driver, 15)
    
    try:
        log_callback("Bắt đầu chức năng: Comment dưới bài viết vừa đăng (Instagram).")
        
        # Bước 1: Điều hướng vào trang cá nhân Instagram
        log_callback("Truy cập trang cá nhân Instagram...")
        try:
            # Lấy link trang cá nhân trực tiếp nếu có
            profile_url = driver.execute_script("""
                let links = document.querySelectorAll("a[role='link']");
                for (let a of links) {
                    let img = a.querySelector("img[alt*='Ảnh đại diện'], img[alt*='profile picture']");
                    if (img && a.href) return a.href;
                }
                return '';
            """)
            
            if profile_url:
                driver.get(profile_url)
                time.sleep(5)
            else:
                driver.get("https://www.instagram.com/")
                time.sleep(5)
                profile_btns = driver.find_elements(By.XPATH, "//span[text()='Trang cá nhân' or text()='Profile'] | //a[descendant::img[contains(@alt, 'Ảnh đại diện') or contains(@alt, 'profile picture')]]")
                if profile_btns:
                    driver.execute_script("arguments[0].click();", profile_btns[0])
                    time.sleep(5)
                else:
                    raise Exception("Không tìm thấy nút Trang cá nhân")
        except Exception as e:
            log_callback(f"Lỗi truy cập trang cá nhân Instagram: {e}")
            return False
            
        # Bước 2: Click vào video/ảnh mới nhất
        log_callback("Click vào video/ảnh mới nhất...")
        try:
            first_post_xpath = "//article//a[contains(@href, '/p/') or contains(@href, '/reel/')] | //div[contains(@class, '_aagw')] | //a[contains(@href, '/p/') or contains(@href, '/reel/')]"
            first_posts = driver.find_elements(By.XPATH, first_post_xpath)
            if not first_posts:
                raise Exception("Không tìm thấy bài đăng nào trên trang cá nhân.")
            driver.execute_script("arguments[0].click();", first_posts[0])
            time.sleep(4)
        except Exception as e:
            log_callback(f"Lỗi click bài đăng mới nhất: {e}")
            return False
            
        # Bước 3: Click vào nút / ô bình luận
        log_callback("Click vào nút/ô bình luận...")
        try:
            # Thử click vào icon bình luận trước nếu có
            cmt_icons = driver.find_elements(By.XPATH, "//*[local-name()='svg' and (@aria-label='Bình luận' or @aria-label='Comment')]")
            if cmt_icons:
                driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", cmt_icons[0])
                time.sleep(1)
        except:
            pass
            
        # Bước 4: Nhập nội dung bình luận (Chống lỗi Stale Element Reference)
        log_callback("Nhập nội dung bình luận...")
        typed_successfully = False
        
        for attempt in range(5):
            try:
                # Tìm lại phần tử textarea tươi mới nhất trên DOM
                textareas = driver.find_elements(
                    By.XPATH, 
                    "//textarea[contains(@aria-label, 'Bình luận') or contains(@placeholder, 'Bình luận') or contains(@aria-label, 'comment') or contains(@placeholder, 'comment') or contains(@aria-label, 'Add a comment')] | //div[@role='textbox' and @contenteditable='true'] | //textarea"
                )
                
                target_box = None
                for ta in reversed(textareas):
                    if ta.is_displayed():
                        target_box = ta
                        break
                        
                if target_box:
                    driver.execute_script("arguments[0].focus();", target_box)
                    time.sleep(0.5)
                    try:
                        target_box.click()
                    except:
                        driver.execute_script("arguments[0].click();", target_box)
                    time.sleep(0.5)
                    
                    # Nhập văn bản từng ký tự
                    for char in comment_text:
                        target_box.send_keys(char)
                        time.sleep(random.uniform(0.015, 0.04))
                    time.sleep(1.5)
                    typed_successfully = True
                    break
            except Exception as ex_type:
                time.sleep(1)
                
        if not typed_successfully:
            # Fallback dùng active_element
            try:
                active_el = driver.switch_to.active_element
                active_el.send_keys(comment_text)
                time.sleep(1.5)
                typed_successfully = True
            except Exception as e_active:
                log_callback(f"Lỗi nhập nội dung: {e_active}")
                return False
                
        # Bước 5: Click nút Đăng hoặc gửi phím Enter
        log_callback("Click nút Đăng bình luận...")
        try:
            post_btn_xpath = "//div[@role='button' and (text()='Đăng' or text()='Post')] | //button[@type='submit' and (text()='Đăng' or text()='Post')] | //div[contains(text(), 'Đăng') or contains(text(), 'Post')][@role='button']"
            post_btns = driver.find_elements(By.XPATH, post_btn_xpath)
            
            clicked_post = False
            for pb in reversed(post_btns):
                if pb.is_displayed():
                    try:
                        driver.execute_script("arguments[0].click();", pb)
                        clicked_post = True
                        break
                    except:
                        pass
                        
            if not clicked_post:
                # Gửi Enter vào phần tử đang focus
                active_el = driver.switch_to.active_element
                active_el.send_keys(Keys.ENTER)
                
            time.sleep(3.5)
            log_callback("Đã bình luận thành công trên Instagram!")
            return True
            
        except Exception as e_send:
            log_callback(f"Lỗi khi gửi bình luận Instagram: {e_send}")
            return False
            
    except Exception as e:
        log_callback(f"Lỗi không xác định khi comment Instagram: {e}")
        return False
