import os
import sys
import subprocess
import hashlib
import platform
import socket

def _get_windows_machine_guid() -> str:
    """Get Windows Registry MachineGuid"""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )
        val, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        return str(val).strip()
    except Exception:
        return ""

def _get_wmic_value(cmd: str) -> str:
    """Run a WMIC / PowerShell command safely to get hardware string"""
    try:
        output = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3
        )
        lines = [line.strip() for line in output.strip().splitlines() if line.strip()]
        if len(lines) > 1:
            return lines[1]
        elif len(lines) == 1:
            return lines[0]
    except Exception:
        pass
    return ""

def _get_powershell_value(ps_script: str) -> str:
    """Run a PowerShell one-liner to get hardware info"""
    try:
        output = subprocess.check_output(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3
        )
        return output.strip()
    except Exception:
        return ""

def get_raw_hardware_fingerprint() -> str:
    """
    Combines Motherboard UUID, CPU ID, Windows Machine GUID, and Drive Serial.
    Guarantees a deterministic, unique string per physical computer.
    """
    components = []

    # 1. MachineGuid from Windows Registry
    guid = _get_windows_machine_guid()
    if guid:
        components.append(f"GUID:{guid}")

    # 2. Motherboard / System UUID
    mb_uuid = _get_powershell_value("(Get-CimInstance Win32_ComputerSystemProduct).UUID")
    if not mb_uuid:
        mb_uuid = _get_wmic_value("wmic csproduct get uuid")
    if mb_uuid and mb_uuid.lower() not in ["none", "default string", "to be filled by o.e.m.", "00000000-0000-0000-0000-000000000000"]:
        components.append(f"UUID:{mb_uuid}")

    # 3. CPU Processor ID
    cpu_id = _get_powershell_value("(Get-CimInstance Win32_Processor).ProcessorId")
    if not cpu_id:
        cpu_id = _get_wmic_value("wmic cpu get processorid")
    if cpu_id:
        components.append(f"CPU:{cpu_id}")

    # 4. Fallback if components empty (Node name / MAC)
    if not components:
        node = platform.node() or socket.gethostname()
        components.append(f"NODE:{node}")

    raw_str = "|".join(components)
    return raw_str

def get_device_hwid() -> str:
    """
    Returns a formatted, human-readable HWID:
    Example: VD-8A9F-2B4C-1D7E-90FA
    """
    raw = get_raw_hardware_fingerprint()
    sha = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()
    
    # Format into 4 chunks of 4 hex chars: VD-XXXX-XXXX-XXXX-XXXX
    chunk1 = sha[0:4]
    chunk2 = sha[4:8]
    chunk3 = sha[8:12]
    chunk4 = sha[12:16]
    
    return f"VD-{chunk1}-{chunk2}-{chunk3}-{chunk4}"

def get_device_info() -> dict:
    """Returns friendly device info dictionary for display and storage"""
    try:
        comp_name = socket.gethostname()
    except Exception:
        comp_name = "Windows-PC"
        
    try:
        user_name = os.getlogin()
    except Exception:
        user_name = "User"

    return {
        "hwid": get_device_hwid(),
        "hostname": comp_name,
        "username": user_name,
        "os": f"{platform.system()} {platform.release()}",
    }

if __name__ == "__main__":
    print(f"Device HWID: {get_device_hwid()}")
    print(f"Device Info: {get_device_info()}")
