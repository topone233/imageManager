from __future__ import annotations

import subprocess
import sys


def main() -> int:
    cmd = [sys.executable, "-m", "streamlit", "run", "image_manager/app.py"]
    try:
        return subprocess.call(cmd)
    except FileNotFoundError:
        print("未检测到 streamlit。请先执行: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
