"""
屏幕管理器

处理摄像头坐标到屏幕坐标的转换，支持多显示器。
"""

from dataclasses import dataclass
from typing import Optional

try:
    from screeninfo import get_monitors
except ImportError:
    get_monitors = None


@dataclass
class ScreenInfo:
    """屏幕信息"""
    x: int
    y: int
    width: int
    height: int
    is_primary: bool = False


class ScreenManager:
    """屏幕管理器"""
    
    def __init__(
        self,
        control_zone: Optional[dict] = None,
        sensitivity: float = 1.5,
    ):
        """
        初始化屏幕管理器
        
        Args:
            control_zone: 控制区域 (x_min, x_max, y_min, y_max)
            sensitivity: 灵敏度倍数
        """
        self.sensitivity = sensitivity
        self.control_zone = control_zone or {
            "x_min": 0.15,
            "x_max": 0.85,
            "y_min": 0.15,
            "y_max": 0.85,
        }
        
        self._screens: list[ScreenInfo] = []
        self._primary_screen: Optional[ScreenInfo] = None
        self._total_width = 0
        self._total_height = 0
        
        self._detect_screens()
    
    def _detect_screens(self):
        """检测所有显示器"""
        self._screens = []
        
        if get_monitors is not None:
            try:
                for m in get_monitors():
                    screen = ScreenInfo(
                        x=m.x,
                        y=m.y,
                        width=m.width,
                        height=m.height,
                        is_primary=m.is_primary,
                    )
                    self._screens.append(screen)
                    if m.is_primary:
                        self._primary_screen = screen
            except Exception:
                pass
        
        # 如果没有检测到屏幕，使用默认值
        if not self._screens:
            import pyautogui
            size = pyautogui.size()
            self._screens = [ScreenInfo(
                x=0,
                y=0,
                width=size.width,
                height=size.height,
                is_primary=True,
            )]
            self._primary_screen = self._screens[0]
        
        # 计算总尺寸
        self._total_width = max(s.x + s.width for s in self._screens)
        self._total_height = max(s.y + s.height for s in self._screens)
    
    @property
    def primary_screen(self) -> ScreenInfo:
        """获取主显示器"""
        return self._primary_screen or self._screens[0]
    
    @property
    def screen_size(self) -> tuple[int, int]:
        """获取主屏幕尺寸"""
        return self.primary_screen.width, self.primary_screen.height
    
    def normalize_to_zone(self, x: float, y: float) -> tuple[float, float]:
        """
        将摄像头坐标归一化到控制区域
        
        Args:
            x: 摄像头 x 坐标 (0-1)
            y: 摄像头 y 坐标 (0-1)
            
        Returns:
            归一化后的坐标 (0-1)
        """
        zone = self.control_zone
        
        # 映射到控制区域
        zone_width = zone["x_max"] - zone["x_min"]
        zone_height = zone["y_max"] - zone["y_min"]
        
        # 归一化到 0-1
        nx = (x - zone["x_min"]) / zone_width
        ny = (y - zone["y_min"]) / zone_height
        
        # 应用灵敏度
        # 灵敏度 > 1 使控制区域更小（移动更大范围）
        center_x, center_y = 0.5, 0.5
        nx = center_x + (nx - center_x) * self.sensitivity
        ny = center_y + (ny - center_y) * self.sensitivity
        
        # 限制在 0-1 范围内
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))
        
        return nx, ny
    
    def camera_to_screen(
        self,
        x: float,
        y: float,
        use_zone: bool = True,
    ) -> tuple[int, int]:
        """
        将摄像头坐标转换为屏幕像素坐标
        
        Args:
            x: 摄像头 x 坐标 (0-1)
            y: 摄像头 y 坐标 (0-1)
            use_zone: 是否使用控制区域
            
        Returns:
            屏幕像素坐标 (px, py)
        """
        if use_zone:
            x, y = self.normalize_to_zone(x, y)
        
        # 摄像头是镜像的，需要翻转 x
        x = 1.0 - x
        
        screen = self.primary_screen
        px = int(screen.x + x * screen.width)
        py = int(screen.y + y * screen.height)
        
        # 确保在屏幕范围内
        px = max(screen.x, min(screen.x + screen.width - 1, px))
        py = max(screen.y, min(screen.y + screen.height - 1, py))
        
        return px, py
    
    def is_in_control_zone(self, x: float, y: float) -> bool:
        """
        检查坐标是否在控制区域内
        
        Args:
            x: x 坐标 (0-1)
            y: y 坐标 (0-1)
            
        Returns:
            是否在控制区域内
        """
        zone = self.control_zone
        return (
            zone["x_min"] <= x <= zone["x_max"] and
            zone["y_min"] <= y <= zone["y_max"]
        )
    
    def set_control_zone(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
    ):
        """设置控制区域"""
        self.control_zone = {
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min,
            "y_max": y_max,
        }
    
    def set_sensitivity(self, sensitivity: float):
        """设置灵敏度"""
        self.sensitivity = max(0.1, min(5.0, sensitivity))
    
    def get_zone_rect(
        self,
        frame_width: int,
        frame_height: int,
    ) -> tuple[int, int, int, int]:
        """
        获取控制区域在图像上的矩形坐标
        
        Args:
            frame_width: 图像宽度
            frame_height: 图像高度
            
        Returns:
            (x1, y1, x2, y2) 矩形坐标
        """
        zone = self.control_zone
        x1 = int(zone["x_min"] * frame_width)
        y1 = int(zone["y_min"] * frame_height)
        x2 = int(zone["x_max"] * frame_width)
        y2 = int(zone["y_max"] * frame_height)
        return x1, y1, x2, y2
