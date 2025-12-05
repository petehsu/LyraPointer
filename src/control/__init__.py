"""系统控制模块

提供鼠标、键盘和屏幕控制功能。
支持 X11 和 Wayland 环境。
"""

from .keyboard import KeyboardController
from .mouse import MouseController
from .screen import ScreenInfo, ScreenManager
from .wayland_mouse import WaylandMouseController, get_mouse_controller, is_wayland

__all__ = [
    # Mouse controllers
    "MouseController",
    "WaylandMouseController",
    # Keyboard controller
    "KeyboardController",
    # Screen management
    "ScreenManager",
    "ScreenInfo",
    # Utility functions
    "get_mouse_controller",
    "is_wayland",
]
