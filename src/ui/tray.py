"""
系统托盘

提供系统托盘图标和菜单，支持后台运行。
"""

import threading
from typing import Callable, Optional

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False


class SystemTray:
    """系统托盘"""
    
    def __init__(
        self,
        on_show: Optional[Callable] = None,
        on_hide: Optional[Callable] = None,
        on_pause: Optional[Callable] = None,
        on_settings: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
    ):
        """
        初始化系统托盘
        
        Args:
            on_show: 显示窗口回调
            on_hide: 隐藏窗口回调
            on_pause: 暂停/恢复回调
            on_settings: 设置回调
            on_quit: 退出回调
        """
        self._on_show = on_show
        self._on_hide = on_hide
        self._on_pause = on_pause
        self._on_settings = on_settings
        self._on_quit = on_quit
        
        self._icon: Optional["pystray.Icon"] = None
        self._thread: Optional[threading.Thread] = None
        self._is_paused = False
        self._is_visible = True
    
    @property
    def available(self) -> bool:
        """检查系统托盘是否可用"""
        return HAS_TRAY
    
    def start(self):
        """启动系统托盘"""
        if not HAS_TRAY:
            print("Warning: pystray not available, system tray disabled")
            return
        
        # 创建图标
        icon_image = self._create_icon()
        menu = self._create_menu()
        
        self._icon = pystray.Icon(
            "LyraPointer",
            icon_image,
            "LyraPointer - Gesture Control",
            menu,
        )
        
        # 在后台线程运行
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()
    
    def stop(self):
        """停止系统托盘"""
        if self._icon:
            self._icon.stop()
            self._icon = None
    
    def update_status(self, is_paused: bool):
        """更新状态"""
        self._is_paused = is_paused
        if self._icon:
            # 更新图标
            self._icon.icon = self._create_icon()
    
    def _create_icon(self, size: int = 64) -> "Image.Image":
        """创建托盘图标"""
        if not HAS_TRAY:
            return None
        
        # 创建图标图像
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # 背景圆
        bg_color = (100, 100, 100) if self._is_paused else (0, 150, 0)
        draw.ellipse([4, 4, size - 4, size - 4], fill=bg_color)
        
        # 手指形状
        finger_color = (255, 255, 255)
        center = size // 2
        
        # 简化的手指图标
        draw.ellipse([center - 8, center - 20, center + 8, center - 4], fill=finger_color)
        draw.rectangle([center - 6, center - 8, center + 6, center + 15], fill=finger_color)
        
        return image
    
    def _create_menu(self) -> "pystray.Menu":
        """创建托盘菜单"""
        if not HAS_TRAY:
            return None
        
        return pystray.Menu(
            pystray.MenuItem(
                "Show/Hide Window",
                self._toggle_visibility,
                default=True,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda text: "Resume" if self._is_paused else "Pause",
                self._toggle_pause,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings", self._open_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )
    
    def _toggle_visibility(self, icon, item):
        """切换窗口可见性"""
        self._is_visible = not self._is_visible
        if self._is_visible:
            if self._on_show:
                self._on_show()
        else:
            if self._on_hide:
                self._on_hide()
    
    def _toggle_pause(self, icon, item):
        """切换暂停状态"""
        if self._on_pause:
            self._on_pause()
    
    def _open_settings(self, icon, item):
        """打开设置"""
        if self._on_settings:
            self._on_settings()
    
    def _quit(self, icon, item):
        """退出程序"""
        if self._on_quit:
            self._on_quit()
        if self._icon:
            self._icon.stop()
