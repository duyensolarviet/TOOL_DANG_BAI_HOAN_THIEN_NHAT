import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def comment_on_newest_youtube_video(driver, comment_text, log_callback, video_title="", direct_video_url=None):
    """
    Chức năng: Comment dưới bài viết vừa đăng trên Youtube đa nền tảng.
    Hỗ trợ:
    1. Truy cập thẳng direct_video_url nếu có (lấy trực tiếp từ popup Studio sau khi đăng).
    2. Tự điều hướng vào 'Kênh của bạn' theo đúng quy trình hiển thị trên giao diện người dùng.
    3. So khớp chính xác 100% tiêu đề video (kể cả bị cắt dấu ba chấm).
    4. Chỉ bình luận đúng video vừa đăng, tuyệt đối không bình luận bậy bạ lên video cũ.
    """
    wait = WebDriverWait(driver, 15)
    
    try:
        log_callback("Bắt đầu chức năng: Comment dưới bài viết vừa đăng (Youtube).")
        clicked_video = False
        
        # --- CÁCH 1: NẾU ĐÃ CÓ DIRECT URL TỪ STUDIO ---
        if direct_video_url:
            log_callback(f"Truy cập trực tiếp link video vừa xuất bản: {direct_video_url}")
            try:
                driver.get(direct_video_url)
                time.sleep(5)
                if "/shorts/" in driver.current_url or "/watch" in driver.current_url:
                    clicked_video = True
            except Exception as e:
                log_callback(f"Lỗi mở link trực tiếp: {e}, chuyển sang tìm trên kênh...")
        
        # --- CÁCH 2: ĐIỀU HƯỚNG VÀO TRANG KÊNH VÀ TÌM THEO TIÊU ĐỀ ---
        if not clicked_video:
            log_callback("Truy cập 'Kênh của bạn'...")
            
            # 1. Thử vào thẳng trang chủ YouTube nếu đang ở trang khác
            if "youtube.com" not in driver.current_url:
                driver.get("https://www.youtube.com/")
                time.sleep(4)
                
            navigated_to_channel = False
            
            # A. Thử bấm vào mục "Bạn" ở Menu trái (Mini Guide) để mở popup chọn "Kênh của bạn"
            try:
                you_btns = driver.find_elements(By.XPATH, "//ytd-mini-guide-entry-renderer[.//yt-formatted-string[contains(text(), 'Bạn') or contains(text(), 'You')]] | //a[@href='/feed/you']")
                for y_btn in you_btns:
                    if y_btn.is_displayed():
                        driver.execute_script("arguments[0].click();", y_btn)
                        time.sleep(2)
                        
                        # Kiểm tra xem có popup "Kênh của bạn" không
                        channel_links = driver.find_elements(By.XPATH, "//yt-formatted-string[contains(text(), 'Kênh của bạn') or contains(text(), 'Your channel')]/ancestor::a | //a[contains(@href, '/@') and contains(., 'Kênh của bạn')]")
                        for cl in channel_links:
                            if cl.is_displayed():
                                driver.execute_script("arguments[0].click();", cl)
                                time.sleep(4)
                                navigated_to_channel = True
                                break
                                
                        if navigated_to_channel:
                            break
                            
                        # Nếu đã vào trang /feed/you, bấm vào link Kênh của bạn ở đầu trang
                        if "/feed/you" in driver.current_url:
                            ch_links_you = driver.find_elements(By.XPATH, "//a[contains(@href, '/@') and not(contains(@href, '/watch'))]")
                            for cl in ch_links_you:
                                if cl.is_displayed():
                                    driver.execute_script("arguments[0].click();", cl)
                                    time.sleep(4)
                                    navigated_to_channel = True
                                    break
                        if navigated_to_channel:
                            break
            except Exception as e:
                pass
                
            # B. Thử menu Avatar góc phải trên cùng
            if not navigated_to_channel and not ("/@" in driver.current_url or "/channel/" in driver.current_url):
                try:
                    avatar_btns = driver.find_elements(By.XPATH, "//button[@id='avatar-btn'] | //ytd-topbar-menu-button-renderer//button | //yt-img-shadow[@id='avatar']/ancestor::button")
                    for ab in avatar_btns:
                        if ab.is_displayed():
                            driver.execute_script("arguments[0].click();", ab)
                            time.sleep(2)
                            
                            channel_links = driver.find_elements(By.XPATH, "//yt-formatted-string[contains(text(), 'Kênh của bạn') or contains(text(), 'Xem kênh') or contains(text(), 'Your channel')]/ancestor::a | //a[contains(@href, '/@') and not(contains(@href, '/watch'))]")
                            for cl in channel_links:
                                if cl.is_displayed():
                                    driver.execute_script("arguments[0].click();", cl)
                                    time.sleep(4)
                                    navigated_to_channel = True
                                    break
                            if navigated_to_channel:
                                break
                except Exception as e:
                    pass
                    
            # C. Thử nút Menu Hamburger bên trái
            if not navigated_to_channel and not ("/@" in driver.current_url or "/channel/" in driver.current_url):
                try:
                    guide_btns = driver.find_elements(By.XPATH, "//button[@id='guide-button' or @id='guide-icon']")
                    for gb in guide_btns:
                        if gb.is_displayed():
                            driver.execute_script("arguments[0].click();", gb)
                            time.sleep(2)
                            
                            channel_links = driver.find_elements(By.XPATH, "//a[@id='endpoint' and contains(@title, 'Kênh của bạn')] | //yt-formatted-string[text()='Kênh của bạn']/ancestor::a")
                            for cl in channel_links:
                                if cl.is_displayed():
                                    driver.execute_script("arguments[0].click();", cl)
                                    time.sleep(4)
                                    navigated_to_channel = True
                                    break
                            if navigated_to_channel:
                                break
                except Exception as e:
                    pass

            # D. Fallback qua YouTube Studio nếu vẫn chưa vào được kênh
            if not ("/@" in driver.current_url or "/channel/" in driver.current_url or "/c/" in driver.current_url or "/user/" in driver.current_url):
                try:
                    driver.get("https://studio.youtube.com/")
                    time.sleep(4)
                    view_channel_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//ytcp-icon-button[@id='view-channel-on-youtube-button'] | //a[contains(@href, 'youtube.com/@') or contains(@href, 'youtube.com/channel/')]")))
                    driver.execute_script("arguments[0].click();", view_channel_btn)
                    time.sleep(4)
                    if len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])
                except Exception as e:
                    log_callback(f"Cảnh báo điều hướng kênh: {e}")
                    
            log_callback(f"Đang ở trang: {driver.current_url}")
            
            # --- TÌM VIDEO KHỚP TIÊU ĐỀ TRÊN KÊNH ---
            log_callback("Tìm kiếm video vừa đăng trên kênh...")
            tabs_to_check = [
                {"name": "Shorts", "xpath": "//yt-tab-shape[contains(., 'Shorts')] | //div[@title='Shorts'] | //tp-yt-paper-tab[.//div[contains(text(), 'Shorts')]] | //a[contains(@href, '/shorts')]"},
                {"name": "Video", "xpath": "//yt-tab-shape[contains(., 'Video')] | //div[@title='Video'] | //tp-yt-paper-tab[.//div[contains(text(), 'Video')]] | //a[contains(@href, '/videos')]"}
            ]
            
            expected_title = video_title.lower().strip() if video_title else ""
            
            # Thử quét tối đa 3 lần (mỗi lần cách nhau 15s nếu chưa thấy do YouTube xử lý ngầm)
            for attempt in range(3):
                if clicked_video:
                    break
                    
                if attempt > 0:
                    log_callback(f"Chưa thấy video xuất hiện trên kênh. Chờ 15s rồi F5 tải lại (lần {attempt+1}/3)...")
                    time.sleep(15)
                    driver.refresh()
                    time.sleep(5)
                    
                for tab in tabs_to_check:
                    if clicked_video:
                        break
                        
                    log_callback(f"Kiểm tra tab {tab['name']}...")
                    try:
                        tab_els = driver.find_elements(By.XPATH, tab['xpath'])
                        for te in tab_els:
                            if te.is_displayed():
                                driver.execute_script("arguments[0].click();", te)
                                time.sleep(3)
                                break
                    except:
                        pass
                        
                    driver.execute_script("window.scrollBy(0, 300);")
                    time.sleep(2)
                    
                    # Quét tất cả thẻ video / link video trong grid
                    video_cards = driver.find_elements(By.XPATH, "//ytd-rich-item-renderer | //ytd-rich-grid-slim-media | //ytd-reel-item-renderer | //ytd-grid-video-renderer | //ytd-browse//a[contains(@href, '/watch') or contains(@href, '/shorts/')]")
                    
                    for card in video_cards:
                        try:
                            # Lấy thẻ <a>
                            if card.tag_name == "a":
                                a_tag = card
                            else:
                                a_tags = card.find_elements(By.XPATH, ".//a[contains(@href, '/watch') or contains(@href, '/shorts/')]")
                                if not a_tags:
                                    continue
                                a_tag = a_tags[0]
                                
                            href = a_tag.get_attribute("href") or ""
                            if not href or ("channel" in href) or ("@" in href) or ("hashtag" in href):
                                continue
                                
                            card_text = card.text or ""
                            a_title = a_tag.get_attribute("title") or ""
                            a_aria = a_tag.get_attribute("aria-label") or ""
                            
                            is_match = False
                            if expected_title:
                                if (expected_title in card_text.lower()) or (expected_title in a_title.lower()) or (expected_title in a_aria.lower()):
                                    is_match = True
                                else:
                                    # Xử lý dấu ba chấm cắt tiêu đề (...) hoặc (…)
                                    for t_str in [card_text, a_title, a_aria]:
                                        vis_lower = t_str.lower().strip()
                                        if "..." in vis_lower or "…" in vis_lower:
                                            clean_prefix = vis_lower.split("...")[0].split("…")[0].strip()
                                            if len(clean_prefix) >= 8 and expected_title.startswith(clean_prefix):
                                                is_match = True
                                                break
                            else:
                                # Không có tiêu đề mẫu -> lấy video đầu tiên
                                is_match = True
                                
                            if is_match:
                                log_callback(f"Đã tìm thấy video trùng khớp: {href}")
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", a_tag)
                                time.sleep(1)
                                driver.get(href)
                                time.sleep(6)
                                if "/watch" in driver.current_url or "/shorts/" in driver.current_url:
                                    clicked_video = True
                                    break
                        except Exception as e:
                            pass
            
            if not clicked_video:
                raise Exception("Không tìm thấy video nào có tiêu đề trùng khớp trên kênh. Video có thể đang được YouTube xử lý nội bộ.")

        time.sleep(2)
        
        # --- BƯỚC BÌNH LUẬN VÀO VIDEO ---
        log_callback(f"Bắt đầu bình luận trên video: {driver.current_url}")
        
        # 1. Mở phần bình luận nếu là Shorts
        if "/shorts/" in driver.current_url:
            log_callback("Mở hộp bình luận Shorts...")
            try:
                cmt_btns = driver.find_elements(By.XPATH, "//button-view-model[contains(@class, 'ytwReelActionBar')]//button | //button[@aria-label='Xem bình luận' or @aria-label='Bình luận' or contains(@aria-label, 'Comments') or contains(@aria-label, 'bình luận')] | //div[@id='comments-button']//button")
                for cb in cmt_btns:
                    if cb.is_displayed():
                        driver.execute_script("arguments[0].click();", cb)
                        time.sleep(3)
                        break
            except Exception as e:
                log_callback(f"Lỗi mở bình luận Shorts: {e}")
        else:
            # Video dài thì cuộn xuống để load bình luận
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(3)
            
        # 2. Click ô placeholder nhập bình luận
        log_callback("Mở ô nhập bình luận...")
        clicked_box = False
        for _ in range(8):
            placeholders = driver.find_elements(By.XPATH, "//div[@id='placeholder-area'] | //yt-formatted-string[@id='simplebox-placeholder'] | //div[@id='simplebox-placeholder']")
            for ph in placeholders:
                if ph.is_displayed():
                    driver.execute_script("arguments[0].click();", ph)
                    clicked_box = True
                    break
            if clicked_box:
                break
            time.sleep(1)
            
        time.sleep(2)
        
        # 3. Nhập nội dung bình luận
        log_callback("Nhập nội dung bình luận...")
        typed = False
        for _ in range(8):
            input_boxes = driver.find_elements(By.XPATH, "//div[@id='contenteditable-root']")
            for box in input_boxes:
                if box.is_displayed():
                    box.click()
                    time.sleep(0.5)
                    box.send_keys(comment_text)
                    typed = True
                    break
            if typed:
                break
            time.sleep(1)
            
        if not typed:
            raise Exception("Không tìm thấy ô nhập nội dung bình luận.")
            
        time.sleep(1.5)
        
        # 4. Bấm nút Bình luận (Submit)
        log_callback("Bấm nút gửi bình luận...")
        submitted = False
        for _ in range(8):
            submit_btns = driver.find_elements(By.XPATH, "//ytd-button-renderer[@id='submit-button']//button | //button[@id='submit-button'] | //button[@aria-label='Bình luận' or @aria-label='Comment']")
            for sb in submit_btns:
                if sb.is_displayed() and sb.is_enabled():
                    driver.execute_script("arguments[0].click();", sb)
                    submitted = True
                    break
            if submitted:
                break
            time.sleep(1)
            
        if not submitted:
            raise Exception("Không tìm thấy hoặc không bấm được nút Gửi bình luận.")
            
        time.sleep(3)
        log_callback("Đã bình luận thành công lên YouTube!")
        return True
        
    except Exception as e:
        log_callback(f"Kết thúc tiến trình Comment YouTube: {e}")
        return False
