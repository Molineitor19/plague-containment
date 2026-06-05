"""
run.py — Plague Containment Launcher
=====================================
Compiles the C++ engine and launches both the engine and
the Pygame interface automatically.

Usage:
    python run.py

Requirements:
    - g++ (MinGW) installed and in PATH
    - pygame-ce installed: pip install pygame-ce
"""

import subprocess
import sys
import os
import time
from pathlib import Path

# ── Paths ─────────────────────────────────────
ROOT      = Path(__file__).parent
ENGINE_DIR = ROOT / "src" / "engine"
IFACE_DIR  = ROOT / "src" / "interface"

ENGINE_SRC = [
    str(ENGINE_DIR / "engine.cpp"),
    str(ENGINE_DIR / "InfectionList.cpp"),
    str(ENGINE_DIR / "AVLTree.cpp"),
]

if sys.platform == "win32":
    ENGINE_BIN = str(ENGINE_DIR / "engine.exe")
else:
    ENGINE_BIN = str(ENGINE_DIR / "engine")

UI_SCRIPT = str(IFACE_DIR / "plague_ui.py")

# ── Step 1: Check dependencies ────────────────

def check_gpp():
    try:
        subprocess.run(["g++", "--version"],
                       capture_output=True, check=True)
        print("[launcher] g++ found.")
        return True
    except Exception:
        print("[launcher] ERROR: g++ not found.")
        print("           Install MinGW and add it to PATH.")
        return False

def check_pygame():
    try:
        import pygame
        print(f"[launcher] pygame found ({pygame.version.ver}).")
        return True
    except ImportError:
        print("[launcher] pygame not found. Installing pygame-ce...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pygame-ce"],
                       check=True)
        return True

# ── Step 2: Compile C++ engine ────────────────

def compile_engine():
    print("[launcher] Compiling C++ engine...")
    result = subprocess.run(
        ["g++", "-O2", "-o", ENGINE_BIN] + ENGINE_SRC,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("[launcher] Compilation FAILED:")
        print(result.stderr)
        return False
    print("[launcher] Engine compiled successfully.")
    return True

# ── Step 3: Clean up old JSON files ──────────

def clean_json():
    action_json = IFACE_DIR / "action.json"
    if action_json.exists():
        action_json.unlink()
        print("[launcher] Cleaned up old action.json.")

# ── Step 4: Launch both processes ─────────────

def launch():
    print("[launcher] Starting C++ engine...")
    engine_proc = subprocess.Popen(
        [ENGINE_BIN],
        cwd=str(ENGINE_DIR),
    )

    # small delay so engine writes state.json before UI starts
    time.sleep(1.0)

    print("[launcher] Starting Pygame interface...")
    ui_proc = subprocess.Popen(
        [sys.executable, UI_SCRIPT],
        cwd=str(IFACE_DIR),
    )

    print("[launcher] Game running. Close the window to exit.\n")

    # wait for UI to close
    ui_proc.wait()

    # when UI closes, also stop the engine
    print("[launcher] UI closed. Stopping engine...")
    engine_proc.terminate()
    print("[launcher] Done.")

# ── Main ──────────────────────────────────────

if __name__ == "__main__":
    print("╔══════════════════════════════════════╗")
    print("║     Plague Containment Launcher      ║")
    print("╚══════════════════════════════════════╝\n")

    if not check_gpp():
        sys.exit(1)

    check_pygame()

    if not compile_engine():
        sys.exit(1)

    clean_json()
    launch()
