from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(script: Path, *arguments: str) -> None:
    subprocess.run([sys.executable, str(script), *arguments], check=True, cwd=script.parent)


def main() -> None:
    directory = Path(__file__).resolve().parent
    first_six = [
        "复现第01图_渐变柱形图.py",
        "复现第02图_带均值柱形图.py",
        "复现第03图_渐变圆角柱形图.py",
        "复现第04图_标注柱形图.py",
        "复现第05图_层叠柱形图.py",
        "复现第06图_蝴蝶图.py",
    ]
    for script_name in first_six:
        run(directory / script_name)
    run(directory / "复现第07至30图.py", "--start", "7", "--end", "30")
    run(directory / "逐图审查.py")
    print("30 个图表已全部重新生成。")


if __name__ == "__main__":
    main()
