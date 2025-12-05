"""
LyraPointer 测试模块

包含单元测试、集成测试和性能测试。
"""

import sys
from pathlib import Path

# 将 src 目录添加到路径，以便测试可以导入项目模块
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

__all__ = []
