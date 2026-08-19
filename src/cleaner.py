import os
import shutil

def get_chrome_main_version():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        return int(version.split('.')[0])
    except Exception:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome")
            version, _ = winreg.QueryValueEx(key, "Version")
            return int(version.split('.')[0])
        except Exception:
            return None

def clean_chrome_cache(acc_id):
    """
    Dọn dẹp các thư mục cache rác và file Preferences bị phình to 
    của Chrome profile để tránh đầy ổ cứng và làm mượt tool.
    """
    profile_dir = os.path.join(os.getcwd(), 'profiles', acc_id)
    default_dir = os.path.join(profile_dir, 'Default')
    
    if not os.path.exists(default_dir):
        return
        
    # Xoá file Preferences nếu nó bị lỗi phình to bất thường (trên 30MB)
    # Lỗi này do undetected_chromedriver thỉnh thoảng gây ra
    prefs_file = os.path.join(default_dir, 'Preferences')
    if os.path.exists(prefs_file):
        try:
            if os.path.getsize(prefs_file) > 30 * 1024 * 1024:
                os.remove(prefs_file)
        except Exception:
            pass
            
    # Xoá các thư mục rác sinh ra trong quá trình lướt web/xem video
    junk_folders = [
        'Cache', 
        'Code Cache', 
        'GPUCache', 
        os.path.join('Service Worker', 'CacheStorage'),
        'Crashpad'
    ]
    
    for folder in junk_folders:
        folder_path = os.path.join(default_dir, folder)
        if os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path, ignore_errors=True)
            except Exception:
                pass
                
    # Tự động đóng các tiến trình Chrome cũ (ghost process) đang sử dụng profile này để tránh lỗi "Profile đang bị khóa"
    try:
        import subprocess
        cmd = 'wmic process where "name=\'chrome.exe\' or name=\'chromedriver.exe\'" get ProcessId,CommandLine'
        output = subprocess.check_output(cmd, shell=True, text=True, errors='ignore')
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            if acc_id in line and ('chrome.exe' in line or 'chromedriver.exe' in line):
                parts = line.split()
                if parts:
                    pid = parts[-1]
                    if pid.isdigit():
                        try:
                            subprocess.call(f'taskkill /F /PID {pid}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except Exception:
                            pass
    except Exception:
        pass
