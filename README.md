# Tool Đăng Bài Đa Nền Tảng & Tự Động Quét TikTok Lên Lịch AI

Phần mềm tự động hóa quản trị và đăng bài đa nền tảng (**Facebook, Instagram, Threads, TikTok, YouTube Shorts, Zalo**) kết hợp **AI (Gemini / Groq)** tự động quét video TikTok hoặc tải tiếp từ video chỉ định để lên lịch đăng bài hoàn toàn tự động, tích hợp hệ thống bản quyền / kích hoạt Key License qua Telegram Bot.

---

## 🚀 Hướng Dẫn Cài Đặt và Sử Dụng

### 1. Cài đặt môi trường Python
* Khuyến nghị sử dụng **Python 3.10 - 3.12** (hỗ trợ Windows 10/11).
* Khi cài đặt Python, **bắt buộc tích chọn checkbox "Add Python to PATH"**.

### 2. Cài đặt các thư viện phụ thuộc
Mở CMD hoặc PowerShell tại thư mục dự án và chạy:
```bash
pip install -r requirements.txt
```

### 3. Khởi chạy ứng dụng
- **Cách 1**: Nhấp đúp vào file `start.bat`.
- **Cách 2**: Mở terminal tại thư mục gốc và chạy lệnh:
```bash
python src/main.py
```

---

## 🔑 Hệ Thống Key Bản Quyền & Telegram Bot

- Hệ thống quản lý bản quyền HWID tích hợp sẵn.
- Khởi động Telegram Key Bot bằng cách vào thư mục `bot_license/` và chạy `start_bot.bat` (hoặc `python bot_license/telegram_key_bot.py`).
- Xem chi tiết tại tài liệu [HUONG_DAN_SU_DUNG_KEY_BOT.md](HUONG_DAN_SU_DUNG_KEY_BOT.md).

---

## ✨ Tính Năng Nổi Bật

1. **Quản lý đa tài khoản độc lập**: Thêm, sửa, xóa, lưu trữ cấu hình riêng biệt cho từng tài khoản.
2. **Đăng bài đa nền tảng**:
   - Facebook cá nhân & Fanpage (Bài viết, Reels, Video).
   - Instagram (Reels & Bài viết).
   - Threads.
   - YouTube Shorts / Video.
   - Zalo Video.
   - TikTok.
3. **AI Tự động quét TikTok & Lên lịch (Tab TikTok AI)**:
   - Tải video theo link kênh hoặc tải nối tiếp từ link video cụ thể.
   - Tích hợp Gemini & Groq AI tự động viết lại content và tiêu đề YouTube Shorts thu hút người xem.
   - Tự động phân bổ lịch đăng cho từng bài viết.
   - Quét và lên lịch hàng loạt cho tất cả tài khoản cùng lúc.
4. **Tự động bình luận, tương tác Newfeed**:
   - Tự động comment vào bài đăng vừa tải lên cho từng nền tảng.
   - Tùy chọn xóa file media sau khi đăng để tiết kiệm dung lượng đĩa.
5. **Sắp xếp cửa sổ Chrome tự động**: Hỗ trợ mở trình duyệt và tự động chia lưới màn hình tiện theo dõi.

---

## 📁 Cấu Trúc Thư Mục Dự Án

```
├── assets/                  # Icon, logo ứng dụng
├── bot_license/             # Telegram Bot quản lý và cấp phát Key
│   ├── config.json          # Cấu hình Token Bot Telegram & gói cước
│   ├── start_bot.bat        # File khởi động Bot Key
│   └── telegram_key_bot.py  # Mã nguồn Bot Telegram
├── src/                     # Mã nguồn chính của Tool
│   ├── assets/              # Tài nguyên giao diện
│   ├── license_manager/     # Module kiểm tra bản quyền & HWID
│   ├── ui_actions/          # Các tab chức năng giao diện CustomTkinter
│   ├── ai_helper.py         # Module AI (Gemini, Groq)
│   ├── bot_manager.py       # Trình điều khiển luồng đăng bài
│   ├── main.py              # Điểm khởi chạy giao diện chính
│   ├── tiktok_crawler.py    # Trình cào video TikTok theo kênh
│   └── ...
├── accounts.json            # Dữ liệu tài khoản
├── ai_config.json           # Cấu hình AI & TikTok AI cho các tài khoản
├── global_config.json       # Cấu hình hệ thống
├── license_config.json      # Cấu hình gói bản quyền
├── local_keys_db.json       # Cơ sở dữ liệu Key cục bộ
├── requirements.txt         # Danh sách thư viện Python cần thiết
├── start.bat                # Khởi động Tool nhanh trên Windows
└── README.md
```
