import os
import time
import json
import base64
import random
import requests
import io
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AntiCaptchaTikTokSolver:
    """
    Module giải Captcha TikTok tự động thông qua dịch vụ AntiCaptcha.top
    Hỗ trợ:
    - Captcha Xoay hình 3D / Xoay vòng tròn ghép hình (Type 43 - Rotate Captcha)
    - Captcha Trượt mảnh ghép / Kéo thả Puzzle (Type 41 - Slide Captcha)
    """
    
    API_URL_CAPTCHA = "https://anticaptcha.top/api/captcha"
    API_URL_BALANCE = "https://anticaptcha.top/api/getbalance"
    
    def __init__(self, api_key="5fb2919ec337277c83fb4925fc406869", log_callback=None):
        self.api_key = api_key.strip() if api_key else "5fb2919ec337277c83fb4925fc406869"
        self.log_callback = log_callback

    def log(self, msg):
        if self.log_callback:
            try:
                self.log_callback(f"[AntiCaptcha] {msg}")
            except:
                print(f"[AntiCaptcha] {msg}")
        else:
            print(f"[AntiCaptcha] {msg}")

    def get_balance(self):
        """
        Kiểm tra số dư tài khoản trên anticaptcha.top
        """
        if not self.api_key:
            return 0
        try:
            r = requests.get(f"{self.API_URL_BALANCE}?apikey={self.api_key}", timeout=8)
            if r.status_code == 200:
                res = r.json()
                if res.get("success"):
                    return float(res.get("balance", 0))
        except Exception as e:
            self.log(f"Lỗi kiểm tra số dư: {e}")
        return 0

    def _switch_to_captcha_frame_if_needed(self, driver):
        """
        Chuyển context vào iframe chứa captcha nếu có
        """
        try:
            driver.switch_to.default_content()
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for frame in iframes:
                try:
                    src = (frame.get_attribute("src") or "").lower()
                    fid = (frame.get_attribute("id") or "").lower()
                    fcls = (frame.get_attribute("class") or "").lower()
                    if "captcha" in src or "verify" in src or "secsdk" in src or "captcha" in fid or "secsdk" in fid or "captcha" in fcls:
                        driver.switch_to.frame(frame)
                        return True
                except:
                    pass
        except:
            pass
        return False

    def is_captcha_present(self, driver):
        """
        Kiểm tra xem trên trình duyệt có xuất hiện hộp thoại Captcha TikTok không
        (Kiểm tra cả cửa sổ chính và bên trong iframe)
        """
        # 1. Kiểm tra trên DOM chính
        try:
            driver.switch_to.default_content()
            page_text = driver.execute_script("return document.body ? (document.body.innerText || '') : '';")
            if "Thanh trượt để ghép hình" in page_text or "Drag the slider to fit the puzzle" in page_text or "xoay" in page_text.lower() or "thanh trượt" in page_text.lower():
                return True
                
            selectors = [
                "#captcha-verify-image",
                ".captcha_verify_img",
                ".secsdk_captcha_drag_icon",
                ".secsdk-captcha-drag-icon",
                "[class*='captcha_verify']",
                "[class*='captcha-verify']",
                "div[class*='captcha-modal']",
                "div[class*='captcha_drag']",
                "div[class*='secsdk']",
                "div[id*='captcha']"
            ]
            for sel in selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in elements:
                    try:
                        if el.is_displayed() and el.size['width'] > 0:
                            return True
                    except:
                        pass
        except:
            pass

        # 2. Kiểm tra bên trong iframe nếu có
        try:
            driver.switch_to.default_content()
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for frame in iframes:
                try:
                    src = (frame.get_attribute("src") or "").lower()
                    fid = (frame.get_attribute("id") or "").lower()
                    if "captcha" in src or "verify" in src or "secsdk" in src or "captcha" in fid or "secsdk" in fid:
                        return True
                except:
                    pass
        except:
            pass

        return False

    def _get_image_base64(self, driver, img_element):
        """
        Lấy chuỗi base64 của phần tử ảnh từ canvas, src hoặc requests
        """
        try:
            src = img_element.get_attribute("src")
            if src and src.startswith("data:image"):
                return src.split("base64,")[1]
            elif src and src.startswith("http"):
                r = requests.get(src, timeout=10)
                if r.status_code == 200:
                    return base64.b64encode(r.content).decode("utf-8")
        except:
            pass

        try:
            b64 = driver.execute_script("""
                let img = arguments[0];
                let canvas = document.createElement('canvas');
                canvas.width = img.naturalWidth || img.width || 300;
                canvas.height = img.naturalHeight || img.height || 300;
                let ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                return canvas.toDataURL('image/png').substring(22);
            """, img_element)
            if b64 and len(b64) > 100:
                return b64
        except:
            pass
        return ""

    def solve_tiktok_captcha(self, driver, max_retries=4):
        """
        Tự động nhận diện và giải Captcha TikTok
        """
        for attempt in range(1, max_retries + 1):
            if not self.is_captcha_present(driver):
                self.log("Không phát hiện Captcha hoặc Captcha đã được giải thành công.")
                return True

            self.log(f"-> [Lần {attempt}/{max_retries}]: Đang trích xuất ảnh Captcha TikTok...")
            time.sleep(1.5)

            # Chuyển vào iframe nếu captcha nằm trong iframe
            self._switch_to_captcha_frame_if_needed(driver)

            try:
                # 1. Tìm các ảnh trong khung Captcha
                img_main = None
                img_sub = None

                # Selector ảnh nền / ngoài
                main_selectors = [
                    "#captcha-verify-image",
                    "img[class*='captcha_verify_img']",
                    "img[class*='captcha_verify_slide']",
                    "img[class*='verify-image']",
                    "img[src*='tiktokcdn'][src*='outer']",
                    "img[src*='3d']"
                ]
                for s in main_selectors:
                    els = driver.find_elements(By.CSS_SELECTOR, s)
                    for el in els:
                        if el.is_displayed() and el.size['width'] > 30:
                            img_main = el
                            break
                    if img_main:
                        break

                # Selector ảnh trong / mảnh ghép
                sub_selectors = [
                    "#captcha-verify-sub-image",
                    "img[class*='captcha_verify_sub_img']",
                    "img[class*='captcha_verify_piece']",
                    "img[src*='tiktokcdn'][src*='inner']"
                ]
                for s in sub_selectors:
                    els = driver.find_elements(By.CSS_SELECTOR, s)
                    for el in els:
                        if el.is_displayed() and el.size['width'] > 20:
                            img_sub = el
                            break
                    if img_sub:
                        break

                # Nếu chưa tìm thấy, quét tất cả ảnh hiển thị trên trang/frame
                if not img_main or not img_sub:
                    all_imgs = driver.find_elements(By.TAG_NAME, "img")
                    visible_imgs = [im for im in all_imgs if im.is_displayed() and im.size['width'] > 30]
                    visible_imgs.sort(key=lambda x: x.size['width'] * x.size['height'], reverse=True)
                    if len(visible_imgs) >= 2:
                        img_main = visible_imgs[0]
                        img_sub = visible_imgs[1]
                    elif len(visible_imgs) == 1:
                        img_main = visible_imgs[0]

                if not img_main:
                    self.log("Không tìm thấy thẻ ảnh Captcha. Thử lại sau 2 giây...")
                    driver.switch_to.default_content()
                    time.sleep(2)
                    continue

                b64_main = self._get_image_base64(driver, img_main)
                b64_sub = self._get_image_base64(driver, img_sub) if img_sub else ""

                if not b64_main:
                    self.log("Không lấy được dữ liệu ảnh base64.")
                    driver.switch_to.default_content()
                    time.sleep(2)
                    continue

                # 2. Gửi request lên AntiCaptcha.top
                captcha_type = 43 if b64_sub else 41
                img_payload = f"{b64_main}|{b64_sub}" if b64_sub else b64_main

                self.log(f"-> Đang gửi ảnh lên AntiCaptcha.top (Type: {captcha_type})...")
                payload = {
                    "apikey": self.api_key,
                    "type": captcha_type,
                    "img": img_payload
                }

                r = requests.post(self.API_URL_CAPTCHA, json=payload, timeout=25)
                if r.status_code != 200:
                    self.log(f"Lỗi kết nối AntiCaptcha.top: HTTP {r.status_code}")
                    driver.switch_to.default_content()
                    continue

                res_data = r.json()
                if not res_data.get("success"):
                    self.log(f"AntiCaptcha.top báo lỗi: {res_data.get('message', 'Thất bại')}")
                    driver.switch_to.default_content()
                    time.sleep(2)
                    continue

                captcha_res = res_data.get("captcha", "")
                self.log(f"-> AntiCaptcha.top phản hồi kết quả: {captcha_res}")

                # 3. Phân tích kết quả xoay / trượt
                target_rotate = 0.0
                target_x = 0.0
                try:
                    if isinstance(captcha_res, str) and "{" in captcha_res:
                        parsed = json.loads(captcha_res)
                        target_rotate = float(parsed.get("rotate", 0))
                        target_x = float(parsed.get("x", 0))
                    elif isinstance(captcha_res, (int, float)):
                        target_rotate = float(captcha_res)
                    else:
                        target_rotate = float(str(captcha_res).strip())
                except Exception as ex:
                    self.log(f"Lỗi parse kết quả: {ex}")

                # 4. Tìm nút kéo thanh trượt (Slider Handle)
                slider_btn = None
                slider_selectors = [
                    ".secsdk_captcha_drag_icon",
                    ".secsdk-captcha-drag-icon",
                    "div[class*='captcha_drag_icon']",
                    "div[class*='drag-icon']",
                    "div[class*='slider-handle']",
                    "div[role='slider']",
                    "div[class*='secsdk_captcha_drag'] div[class*='icon']",
                    "div[class*='captcha_drag'] div",
                    "div[class*='sc-']"
                ]
                for s in slider_selectors:
                    els = driver.find_elements(By.CSS_SELECTOR, s)
                    for el in els:
                        if el.is_displayed() and el.size['width'] > 10:
                            slider_btn = el
                            break
                    if slider_btn:
                        break

                if not slider_btn:
                    self.log("Không tìm thấy nút trượt (Slider Handle).")
                    driver.switch_to.default_content()
                    continue

                # 5. Đo đạc chính xác thanh ray trượt qua JavaScript (tìm thanh ngang thực tế)
                geo_info = driver.execute_script("""
                    let btn = arguments[0];
                    // Tìm đúng container thanh ray ngang (chiều cao ~30-55px, chiều rộng ~200-300px)
                    let p = btn.parentElement;
                    let track = p;
                    while (p && p !== document.body) {
                        let r = p.getBoundingClientRect();
                        if (r.width >= 180 && r.width <= 320 && r.height <= 60 && r.height >= 25) {
                            track = p;
                            break;
                        }
                        p = p.parentElement;
                    }
                    let btnRect = btn.getBoundingClientRect();
                    let trackRect = track ? track.getBoundingClientRect() : {width: 260};
                    let maxMove = trackRect.width - btnRect.width;
                    if (maxMove < 150 || maxMove > 280) {
                        maxMove = 216; // Độ dài tiêu chuẩn thanh trượt TikTok Web
                    }
                    return {
                        trackWidth: trackRect.width,
                        btnWidth: btnRect.width,
                        maxDistance: maxMove
                    };
                """, slider_btn)

                max_dist = geo_info.get("maxDistance", 216)

                # 6. Tính toán khoảng cách kéo chuột chính xác
                if target_rotate > 0:
                    if target_rotate <= 1.0:
                        move_distance = target_rotate * max_dist
                    else:
                        move_distance = (target_rotate / 360.0) * max_dist
                elif target_x > 0:
                    move_distance = target_x
                else:
                    move_distance = max_dist * 0.5

                self.log(f"-> Đang kéo thanh trượt {round(move_distance, 1)}px (Chiều dài ray chuẩn: {round(max_dist, 1)}px)...")

                # 7. Mô phỏng kéo chuột tự nhiên bằng ActionChains
                actions = ActionChains(driver)
                actions.move_to_element(slider_btn)
                actions.click_and_hold(slider_btn)
                actions.pause(0.15)

                current_x = 0
                step_count = random.randint(20, 28)
                for step in range(step_count):
                    progress = (step + 1) / step_count
                    # Đồ thị chuyển động mượt mà EaseOutCubic
                    ease_progress = 1 - (1 - progress) ** 3
                    next_x = move_distance * ease_progress
                    delta_x = next_x - current_x
                    current_x = next_x
                    delta_y = random.uniform(-0.3, 0.3)
                    actions.move_by_offset(delta_x, delta_y)
                    actions.pause(random.uniform(0.012, 0.025))

                actions.pause(0.2)
                actions.release()
                actions.perform() # THỰC THI TOÀN BỘ CHUỖI 1 LẦN DUY NHẤT

                self.log("-> Đã thả thanh trượt. Đợi TikTok duyệt...")
                time.sleep(3.5)

                driver.switch_to.default_content()

                if not self.is_captcha_present(driver):
                    self.log("🎉 GIẢI CAPTCHA THÀNH CÔNG RỰC RỠ!")
                    return True
                else:
                    self.log("TikTok chưa duyệt xong. Đang bấm nút Làm Mới Captcha để lấy hình mới...")
                    try:
                        self._switch_to_captcha_frame_if_needed(driver)
                        refresh_btns = driver.find_elements(By.CSS_SELECTOR, ".captcha_verify_refresh_btn, [class*='refresh'], [aria-label*='refresh'], svg[class*='refresh']")
                        for rb in refresh_btns:
                            if rb.is_displayed():
                                driver.execute_script("arguments[0].click();", rb)
                                break
                    except:
                        pass
                    driver.switch_to.default_content()
                    time.sleep(2.5)

            except Exception as e:
                self.log(f"Lỗi trong quá trình giải Captcha: {e}")
                driver.switch_to.default_content()
                time.sleep(2)

        driver.switch_to.default_content()
        return not self.is_captcha_present(driver)

if __name__ == "__main__":
    solver = AntiCaptchaTikTokSolver()
    bal = solver.get_balance()
    print(f"So du tai khoan AntiCaptcha.top: {bal:,.0f} VND")
