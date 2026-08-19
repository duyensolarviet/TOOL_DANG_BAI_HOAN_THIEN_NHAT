import os
import time
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from tiktok_crawler import TikTokCrawler, sanitize_filename

class TikTokVideoStartCrawler(TikTokCrawler):
    """
    Chức năng: Vào trang cá nhân của kênh TikTok chứa video bắt đầu,
    tìm và click mở video đó trên trang cá nhân (mở modal popup),
    sau đó tải tuần tự từ video đó trở lên (Next video).
    """
    
    @staticmethod
    def extract_tiktok_info(url):
        """
        Trích xuất username và video_id từ link TikTok
        Ví dụ: https://www.tiktok.com/@username/video/7543217849368677650?_r=1
        """
        url = url.strip()
        username_match = re.search(r'@([a-zA-Z0-9_.-]+)', url)
        username = username_match.group(1) if username_match else ""
        
        video_id_match = re.search(r'/video/(\d+)', url)
        video_id = video_id_match.group(1) if video_id_match else ""
        if not video_id:
            video_id = sanitize_filename(url.split("/")[-1].split("?")[0])
            
        profile_url = f"https://www.tiktok.com/@{username}" if username else ""
        return username, video_id, profile_url

    def crawl_from_start_video(self, start_video_url, max_videos=5, profile_id="tiktok_crawler", on_video_downloaded=None, reset_history=False):
        start_video_url = start_video_url.strip()
        username, start_vid_id, profile_url = self.extract_tiktok_info(start_video_url)
        
        self.log(f"Bắt đầu tiến trình: Tải từ video {start_video_url}")
        self.log(f"-> Giới hạn: Tải tối đa {max_videos} video (từ video này trở lên).")
        if username:
            self.log(f"-> Kênh TikTok: @{username}")
            
        if not profile_url:
            profile_url = f"https://www.tiktok.com/@{username}" if username else start_video_url
            
        # Gọi trực tiếp qua crawl_profile với mốc start_video_id
        # Hệ thống sẽ mở trang cá nhân, cuộn tìm click mở video mốc trên profile (mở modal)
        # rồi lần lượt click Next từ video đó trở lên
        return self.crawl_profile(
            profile_url=profile_url,
            max_videos=max_videos,
            profile_id=profile_id,
            on_video_downloaded=on_video_downloaded,
            reset_history=reset_history,
            start_video_id=start_vid_id
        )

if __name__ == "__main__":
    crawler = TikTokVideoStartCrawler()
