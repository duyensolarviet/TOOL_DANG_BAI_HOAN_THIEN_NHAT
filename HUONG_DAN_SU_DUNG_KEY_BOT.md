# HƯỚNG DẪN CẤU HÌNH & SỬ DỤNG HỆ THỐNG CHECK KEY BẢN QUYỀN (TELEGRAM BOT)

Hệ thống quản lý bản quyền phần mềm **Vũ Duyên Tools** hoạt động dựa trên cơ chế khóa mã máy **HWID (Hardware ID)** và quản lý tạo key tự động thông qua **Telegram Bot**.

---

## 1. TỔNG QUAN CÁC TÍNH NĂNG
- 💻 **Khóa Thiết Bị (HWID)**: Mỗi máy tính có 1 mã phần cứng duy nhất. Key sau khi kích hoạt sẽ được khóa chặt vào máy đó, không thể chia sẻ cho máy khác.
- 📦 **Hỗ trợ đầy đủ các gói thời hạn**:
  - **1 Tháng (30 Ngày)**
  - **3 Tháng (90 Ngày)**
  - **6 Tháng (180 Ngày)**
  - **1 Năm (365 Ngày)**
  - **Vĩnh Viễn (Lifetime)**
  - **Tùy chỉnh số ngày bất kỳ** (ví dụ: test 1 ngày, 3 ngày, 45 ngày...)
- 🤖 **Telegram Bot Quản Lý**: Quản trị viên chỉ cần dùng điện thoại bấm nút trên Telegram để tạo Key, gia hạn, đổi máy (Reset HWID), khóa/mở khóa Key.
- 🌐 **Cơ Sở Dữ Liệu Miễn Phí (Firebase Realtime DB)**: Đồng bộ tức thì giữa Bot Telegram và Tool Desktop của khách hàng qua mạng Internet.

---

## 2. HƯỚNG DẪN CÀI ĐẶT NHANH (MẤT 2 PHÚT)

### Bước 1: Tạo Database Firebase Realtime (Miễn phí 100%)
1. Truy cập [https://console.firebase.google.com/](https://console.firebase.google.com/) và đăng nhập tài khoản Google.
2. Nhấn **Create a project** (Tạo dự án) $\rightarrow$ Đặt tên (VD: `vuduyen-license`) $\rightarrow$ Nhấn Tiếp tục.
3. Ở menu bên trái, chọn **Build** $\rightarrow$ **Realtime Database** $\rightarrow$ Nhấn **Create Database**.
4. Chọn vị trí (VD: `Singapore` hoặc `United States`) $\rightarrow$ Chọn **Start in test mode** $\rightarrow$ Nhấn **Enable**.
5. Copy đường dẫn URL Database hiển thị trên màn hình (Có dạng: `https://vuduyen-license-default-rtdb.asia-southeast1.firebasedatabase.app` hoặc `https://vuduyen-license-default-rtdb.firebaseio.com`).

---

### Bước 2: Tạo Bot Telegram Qua @BotFather
1. Mở Telegram, tìm kiếm bot `@BotFather` (có tích xanh).
2. Gửi lệnh `/newbot` $\rightarrow$ Nhập tên hiển thị của Bot (VD: `Vũ Duyên Key Manager`).
3. Nhập username cho bot (kết thúc bằng chữ `bot`, VD: `vuduyen_key_bot`).
4. BotFather sẽ gửi cho bạn **HTTP API Token** (Có dạng: `789123456:AAFd4e...`).
5. Mở bot `@userinfobot` trên Telegram để lấy **ID Telegram** của bạn (dãy số dạng `123456789`).

---

### Bước 3: Điền Cấu Hình Vào Tool & Bot

Mở file `license_config.json` (trong thư mục gốc tool) và `bot_license/config.json`:

#### 1. File `license_config.json`:
```json
{
    "firebase_url": "DÁN_URL_FIREBASE_CỦA_BẠN_VÀO_ĐÂY",
    "telegram_support": "https://t.me/ten_telegram_cua_ban",
    "zalo_support": "https://zalo.me/g/nhom_zalo_cua_ban",
    "hotline": "0987.654.321"
}
```

#### 2. File `bot_license/config.json`:
```json
{
    "bot_token": "DÁN_TOKEN_BOTFATHER_VÀO_ĐÂY",
    "admin_ids": [
        123456789  <-- Điền ID Telegram của bạn
    ],
    "firebase_url": "DÁN_URL_FIREBASE_CỦA_BẠN_VÀO_ĐÂY"
}
```

---

## 3. CÁCH SỬ DỤNG

### 3.1. Khởi Chạy Telegram Bot Quản Lý Key
- Nhấp đúp chuột vào file: `bot_license/start_bot.bat`
- Hoặc chạy lệnh trong terminal:
  ```bash
  python bot_license/telegram_key_bot.py
  ```
- Mở Bot Telegram bạn vừa tạo, bấm `/start` để mở **Menu Quản Trị**.

### 3.2. Tạo Key Cho Khách Hàng
1. Trên Telegram, bấm nút **➕ Tạo Key Mới**.
2. Chọn gói: **1 Tháng**, **3 Tháng**, **6 Tháng**, **1 Năm**, hoặc **Vĩnh Viễn**.
3. Bot sẽ xuất ra mã Key (VD: `VD-1M-8K9F2A`). Bạn bấm vào mã để sao chép và gửi cho khách.
4. **Cơ chế**: Khi khách nhập mã này vào phần mềm lần đầu tiên, hệ thống mới bắt đầu tính ngày và tự động khóa chặt vào máy của khách.

### 3.3. Khi Khách Đổi Máy Tính (Reset HWID)
- Khách chuyển sang dùng máy tính mới $\rightarrow$ Bạn vào Telegram Bot, chọn **🔄 Reset HWID** $\rightarrow$ Nhập mã Key của khách.
- Sau khi reset, khách chỉ cần mở tool trên máy mới và dán lại mã Key là dùng được bình thường.

### 3.4. Gia Hạn Key (Extend Key)
- Vào Bot chọn **⏳ Gia Hạn Key** $\rightarrow$ Gửi tin nhắn theo cú pháp: `MÃ_KEY SỐ_NGÀY` (Ví dụ: `VD-1M-8K9F2A 30` để cộng thêm 30 ngày).

### 3.5. Chặn / Khóa Key (Ban)
- Vào Bot chọn **🚫 Khóa / Mở Key** $\rightarrow$ Nhập mã Key cần khóa. Khách hàng sẽ bị ngắt quyền truy cập ngay lập tức.

---

## 4. QUY TRÌNH HOẠT ĐỘNG TRÊN TOOL KHÁCH HÀNG

1. **Khách mở tool** (`start.bat` hoặc `python src/main.py`).
2. Tool tự động kiểm tra xem máy đã có bản quyền hay chưa:
   - **Nếu chưa có key hoặc key hết hạn**: Cửa sổ **Kích Hoạt Bản Quyền** sẽ hiện lên.
   - Hiển thị mã máy **HWID** của khách để khách gửi cho Admin khi cần.
   - Khách dán mã Key vào ô và bấm **🚀 KÍCH HOẠT BẢN QUYỀN & MỞ TOOL**.
3. **Khi kích hoạt thành công**: Giao diện chính của tool sẽ mở ra, trên thanh tiêu đề hiển thị rõ gói cước và số ngày còn lại (Ví dụ: `👑 Gói 1 Năm | HSD: 16/08/2027 (Còn 365 ngày)`).
4. Khách có thể bấm vào nút Huy hiệu bản quyền ở góc trên bên phải bất cứ lúc nào để xem chi tiết hoặc nhập Key mới.
