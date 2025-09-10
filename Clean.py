#!/usr/bin/env python3
"""
chromedge_cleaner.py
A focused privacy cleaner for Chromium-based browsers: Google Chrome and Microsoft Edge.

WARNING: This permanently deletes browser data. Use --dry-run first.
"""

import os
import sys
import shutil
import sqlite3
import argparse
import glob
import time
import random

from pathlib import Path
import platform
import subprocess

# Optional: graceful fallback if psutil not installed
try:
    import psutil
except Exception:
    psutil = None

# ---------------------------
# Configuration & utilities
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

def user_notify(msg):
    print(msg)

# ---------------------------
# Find profiles
# ---------------------------
def find_browser_userdata(browser_key):
    base = APP_NAMES[browser_key].get(OS_KEY)
    if not base:
        return None
    base = os.path.expanduser(base)
    if not os.path.exists(base):
        return None
    # Profiles typically: "Default", "Profile 1", "Profile 2", etc.
    profiles = []
    for p in os.listdir(base):
        pf = os.path.join(base, p)
        if os.path.isdir(pf) and (p == "Default" or p.startswith("Profile") or p.lower().endswith("default")):
            profiles.append(pf)
    # Some installations may use 'Profile 1' etc; fallback: include all directories that contain 'History' file
    if not profiles:
        for p in os.listdir(base):
            pf = os.path.join(base, p)
            if os.path.isdir(pf) and os.path.exists(os.path.join(pf, "History")):
                profiles.append(pf)
    return base, profiles

# ---------------------------
# Terminate browser processes
# ---------------------------
def kill_browser_processes(browser_key, dry_run=False, force=False):
    names = BROWSER_PROCS[browser_key]
    found = []
    if psutil:
        for proc in psutil.process_iter(["name", "exe", "cmdline"]):
            try:
                pname = proc.info.get("name") or ""
                if any(n.lower() in pname.lower() for n in names):
                    found.append(proc)
            except Exception:
                pass
        if not found:
            return []
        for proc in found:
            if dry_run:
                user_notify(f"[DRY RUN] Would terminate process PID={proc.pid} ({proc.name()})")
                continue
            try:
                proc.terminate()
                gone, alive = psutil.wait_procs([proc], timeout=5)
                if alive and force:
                    for p in alive:
                        p.kill()
                user_notify(f"Terminated PID={proc.pid} ({proc.name()})")
            except Exception as e:
                user_notify(f"Failed to terminate PID={proc.pid}: {e}")
        return found
    else:
        # Fallback: platform kill by name
        if dry_run:
            user_notify(f"[DRY RUN] Would attempt to kill processes by name: {names}")
            return []
        if platform.system().lower().startswith("windows"):
            for n in names:
                subprocess.run(["taskkill", "/F", "/IM", n], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            for n in names:
                subprocess.run(["pkill", "-f", n], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        user_notify("Kill commands issued (psutil not available to check).")
        return []

# ---------------------------
# Secure overwrite (shred) helper
# ---------------------------
def overwrite_and_remove(path, passes=1):
    try:
        size = os.path.getsize(path)
        with open(path, "r+b") as f:
            for _ in range(passes):
                f.seek(0)
                f.write(os.urandom(size))
                f.flush()
                os.fsync(f.fileno())
        os.remove(path)
        return True
    except Exception:
        try:
            os.remove(path)
            return True
        except Exception:
            return False

# ---------------------------
# Clearing functions
# ---------------------------

def remove_path(path, dry_run=False, shred=False):
    if not os.path.exists(path):
        return False
    if dry_run:
        user_notify(f"[DRY RUN] Would remove: {path}")
        return True
    try:
        if os.path.isfile(path):
            if shred:
                ok = overwrite_and_remove(path)
                if not ok:
                    os.remove(path)
            else:
                os.remove(path)
        else:
            # remove directory tree
            shutil.rmtree(path, ignore_errors=False)
        user_notify(f"Removed: {path}")
        return True
    except Exception as e:
        user_notify(f"Failed to remove {path}: {e}")
        return False

def clear_sqlite_table(db_path, queries, dry_run=False):
    if not os.path.exists(db_path):
        return False
    if dry_run:
        user_notify(f"[DRY RUN] Would execute cleanup queries on DB: {db_path}")
        return True
    try:
        # Connect and run queries
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        for q in queries:
            cur.execute(q)
        conn.commit()
        conn.close()
        user_notify(f"Run cleanup queries on {db_path}")
        return True
    except sqlite3.OperationalError as e:
        user_notify(f"DB locked or operation failed ({db_path}): {e}")
        return False
    except Exception as e:
        user_notify(f"Error cleaning DB {db_path}: {e}")
        return False

# ---------------------------
# Browser-specific cleaning plan
# ---------------------------

COMMON_ITEMS = [
    # file/folder names (relative to profile dir) that are safe to delete
    "Cache", "Code Cache", "GPUCache", "Service Worker", "Service Worker/CacheStorage",
    "IndexedDB", "Local Storage", "Session Storage", "Sessions", "Shortcuts",
    "Crashpad", "Crash Reports", "Safe Browsing",
    "Top Sites", "Favicons", "History Provider Cache", "Thumbnails"
]

DB_CLEAN_QUERIES = {
    # Maps DB name -> SQL queries to wipe sensitive tables (non exhaustive)
    "History": [
        "DELETE FROM urls;",
        "DELETE FROM visits;",
        "DELETE FROM downloads;",
        "VACUUM;"
    ],
    "Cookies": [
        "DELETE FROM cookies;",
        "VACUUM;"
    ],
    "Web Data": [
        "DELETE FROM autofill;",
        "DELETE FROM autofill_profiles;",
        "VACUUM;"
    ],
    "Login Data": [
        "DELETE FROM logins;",
        "VACUUM;"
    ],
    # Note: databases names may vary by version; we will try matching exact filenames
}

def clean_profile(profile_path, options):
    """
    options: dict with keys:
      dry_run, shred, remove_passwords(bool), verbose
    """
    results = {"deleted": [], "failed": []}
    # 1) Delete common folders
    for name in COMMON_ITEMS:
        rel = os.path.join(profile_path, name)
        if os.path.exists(rel):
            ok = remove_path(rel, dry_run=options["dry_run"], shred=options["shred"])
            (results["deleted"] if ok else results["failed"]).append(rel)

    # 2) Databases: History, Cookies, Web Data, Login Data
    db_files = {
        "History": os.path.join(profile_path, "History"),
        "Cookies": os.path.join(profile_path, "Cookies"),
        "Web Data": os.path.join(profile_path, "Web Data"),
        "Login Data": os.path.join(profile_path, "Login Data"),
        "Network Action Predictor": os.path.join(profile_path, "Network Action Predictor")
    }
    # Some versions embed history DB under 'databases' folder or with suffixes; attempt matches
    for dbname, dbpath in db_files.items():
        if os.path.exists(dbpath):
            # For passwords, only delete if option set
            if dbname == "Login Data" and not options.get("remove_passwords", False):
                user_notify(f"Skipping saved passwords DB (Login Data). Use --remove-passwords to remove.")
            else:
                queries = DB_CLEAN_QUERIES.get(dbname, [])
                if queries:
                    ok = clear_sqlite_table(dbpath, queries, dry_run=options["dry_run"])
                    (results["deleted"] if ok else results["failed"]).append(dbpath)
                else:
                    # If no queries defined, remove file entirely
                    ok = remove_path(dbpath, dry_run=options["dry_run"], shred=options["shred"])
                    (results["deleted"] if ok else results["failed"]).append(dbpath)

    # 3) Other files: Cookies/journal, Last Session, Last Tabs, Current Session, Current Tabs
    loose_files = ["Cookies-journal", "Current Session", "Current Tabs", "Last Session", "Last Tabs", "Preferences", "Secure Preferences", "Visited Links"]
    for fname in loose_files:
        fpath = os.path.join(profile_path, fname)
        if os.path.exists(fpath):
            ok = remove_path(fpath, dry_run=options["dry_run"], shred=options["shred"])
            (results["deleted"] if ok else results["failed"]).append(fpath)

    # 4) Downloaded files history: downloads metadata is in History DB (deleted above), but also 'Cache' may hold bits
    # 5) Optionally wipe 'Local State' if user requests (this affects sign-in state), not per profile but in user data root
    return results

# ---------------------------
# High-level runner
# ---------------------------

def run_clean(args):
    options = {
        "dry_run": args.dry_run,
        "shred": args.shred,
        "remove_passwords": args.remove_passwords,
        "verbose": args.verbose
    }

    targets = []
    if args.chrome:
        targets.append("chrome")
    if args.edge:
        targets.append("edge")
    if not targets:
        targets = ["chrome", "edge"]

    overall = {"cleaned": {}, "skipped": []}

    for t in targets:
        info = find_browser_userdata(t)
        if not info:
            user_notify(f"No user data folder found for {t} on this machine.")
            overall["skipped"].append(t)
            continue
        base_path, profiles = info
        if not profiles:
            user_notify(f"No profiles detected for {t} in {base_path}.")
            overall["skipped"].append(t)
            continue

        user_notify(f"Preparing to clean {t}. Found base: {base_path}. Profiles: {len(profiles)}")

        # Attempt to terminate running browser processes
        if not args.no_kill:
            kill_browser_processes(t, dry_run=args.dry_run, force=args.force_kill)

        per_browser_results = {}
        for p in profiles:
            user_notify(f"Cleaning profile: {p}")
            res = clean_profile(p, options)
            per_browser_results[p] = res
        overall["cleaned"][t] = per_browser_results

        # optional: wipe 'Local State' (contains last active profile, signed-in accounts)
        if args.remove_local_state:
            ls = os.path.join(base_path, "Local State")
            remove_path(ls, dry_run=args.dry_run, shred=args.shred)

    # summary
    user_notify("\n=== Cleaning complete — Summary ===")
    for b, profiles in overall["cleaned"].items():
        user_notify(f"Browser: {b}")
        for p, res in profiles.items():
            user_notify(f"  Profile: {p}")
            user_notify(f"    Deleted/cleaned: {len(res.get('deleted', []))}")
            if args.verbose:
                for d in res.get("deleted", []):
                    user_notify("      - " + str(d))
            if res.get("failed"):
                user_notify(f"    Failed: {len(res.get('failed'))}")
                for f in res.get("failed", []):
                    user_notify("      ! " + str(f))
    return overall

# ---------------------------
# CLI
# ---------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Chromium privacy cleaner for Chrome & Edge (safe-mode: dry-run available).")
    p.add_argument("--chrome", action="store_true", help="Only target Google Chrome")
    p.add_argument("--edge", action="store_true", help="Only target Microsoft Edge")
    p.add_argument("--all", action="store_true", help="Target both browsers (default)")
    p.add_argument("--dry-run", action="store_true", help="Show what would be removed, don't delete")
    p.add_argument("--shred", action="store_true", help="Attempt to overwrite files before deletion (slower)")
    p.add_argument("--remove-passwords", action="store_true", help="Remove saved passwords (destructive!)")
    p.add_argument("--remove-local-state", action="store_true", help="Also remove Local State (affects sign-in state)")
    p.add_argument("--no-kill", action="store_true", help="Do not attempt to close/kill running browsers")
    p.add_argument("--force-kill", action="store_true", help="If browser processes don't terminate, force kill them")
    p.add_argument("--verbose", action="store_true", help="Verbose logging")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    if args.remove_passwords:
        user_notify("WARNING: --remove-passwords is ON. This will permanently delete saved passwords!")
    if args.dry_run:
        user_notify("Dry run enabled — no destructive actions will be taken.")
    run_clean(args)
