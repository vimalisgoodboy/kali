#!/usr/bin/env python3
"""
Clean.py
Privacy cleaner for Chrome & Edge — deletes everything without requiring options.

⚠️ WARNING: This will delete ALL browsing data, cookies, history, cache,
saved passwords, session data, etc. USE CAREFULLY.
"""

import os
import shutil
import sqlite3
import platform
import subprocess
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

# ---------------------------
# Paths
# ---------------------------

APP_NAMES = {
    "chrome": {
        "win": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data"),
        "mac": os.path.expanduser("~/Library/Application Support/Google/Chrome"),
        "linux": os.path.expanduser("~/.config/google-chrome"),
    },
    "edge": {
        "win": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Edge", "User Data"),
        "mac": os.path.expanduser("~/Library/Application Support/Microsoft Edge"),
        "linux": os.path.expanduser("~/.config/microsoft-edge"),
    }
}

BROWSER_PROCS = {
    "chrome": ["chrome", "chrome.exe", "Google Chrome"],
    "edge": ["msedge", "msedge.exe", "Microsoft Edge"]
}

def get_os_key():
    pf = platform.system().lower()
    if "windows" in pf:
        return "win"
    if "darwin" in pf:
        return "mac"
    return "linux"

OS_KEY = get_os_key()

# ---------------------------
# Kill browser processes
# ---------------------------

def kill_browser_processes(names):
    if psutil:
        for proc in psutil.process_iter(["name"]):
            try:
                if any(n.lower() in (proc.info.get("name") or "").lower() for n in names):
                    proc.kill()
                    print(f"Killed {proc.info['name']} (PID {proc.pid})")
            except Exception:
                pass
    else:
        if platform.system().lower().startswith("windows"):
            for n in names:
                subprocess.run(["taskkill", "/F", "/IM", n], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            for n in names:
                subprocess.run(["pkill", "-f", n], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ---------------------------
# Remove helper
# ---------------------------

def remove_path(path):
    if os.path.exists(path):
        try:
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path, ignore_errors=True)
            print(f"Deleted: {path}")
        except Exception as e:
            print(f"Failed: {path} ({e})")

# ---------------------------
# Clean profile
# ---------------------------

COMMON_ITEMS = [
    "Cache", "Code Cache", "GPUCache", "Service Worker", "IndexedDB",
    "Local Storage", "Session Storage", "Sessions", "Shortcuts", "Crashpad",
    "Top Sites", "Favicons", "History Provider Cache", "Thumbnails"
]

DB_FILES = ["History", "Cookies", "Web Data", "Login Data"]

LOOSE_FILES = [
    "Cookies-journal", "Current Session", "Current Tabs",
    "Last Session", "Last Tabs", "Preferences", "Secure Preferences"
]

def clean_profile(profile_path):
    for item in COMMON_ITEMS:
        remove_path(os.path.join(profile_path, item))
    for db in DB_FILES:
        remove_path(os.path.join(profile_path, db))
    for f in LOOSE_FILES:
        remove_path(os.path.join(profile_path, f))

def find_profiles(browser_key):
    base = APP_NAMES[browser_key].get(OS_KEY)
    if not base or not os.path.exists(base):
        return []
    return [os.path.join(base, d) for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]

# ---------------------------
# Main
# ---------------------------

def run_cleaner():
    for browser, procs in BROWSER_PROCS.items():
        print(f"\n🔹 Cleaning {browser.capitalize()}...")
        kill_browser_processes(procs)
        profiles = find_profiles(browser)
        if not profiles:
            print("No profiles found.")
            continue
        for p in profiles:
            print(f"Cleaning profile: {p}")
            clean_profile(p)
        # Also remove Local State (sign-in info)
        base = APP_NAMES[browser][OS_KEY]
        remove_path(os.path.join(base, "Local State"))
    print("\n✅ Cleaning complete!")

if __name__ == "__main__":
    run_cleaner()
