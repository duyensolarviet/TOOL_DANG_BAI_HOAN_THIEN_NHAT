"""
License Manager Package for Vu Duyen Auto Tool
Handles HWID generation, license validation, and activation UI.
"""

from .hwid import get_device_hwid, get_device_info
from .license_checker import LicenseChecker

try:
    from .activation_dialog import show_activation_dialog, check_and_prompt_license
except ImportError:
    show_activation_dialog = None
    check_and_prompt_license = None

__all__ = [
    "get_device_hwid",
    "get_device_info",
    "LicenseChecker",
    "show_activation_dialog",
    "check_and_prompt_license"
]
