#!/usr/bin/env python3
"""
LyraPointer 启动脚本

用摄像头识别手势，完全替代鼠标控制电脑。

Usage:
    python run.py [--config CONFIG] [--camera CAMERA] [--no-gui]

Examples:
    python run.py                    # 默认启动
    python run.py --camera 1         # 使用第二个摄像头
    python run.py --no-gui           # 无界面模式
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.main import main

if __name__ == "__main__":
    main()
