"""
轨迹平滑算法

使用 One Euro Filter 算法减少手部追踪的抖动，同时保持低延迟。
参考: https://gery.casiez.net/1euro/
"""

import math
import time


class LowPassFilter:
    """低通滤波器"""
    
    def __init__(self, alpha: float = 0.5):
        """
        初始化低通滤波器
        
        Args:
            alpha: 平滑系数 (0-1, 越小越平滑)
        """
        self._alpha = alpha
        self._last_value: float | None = None
        self._last_time: float | None = None
    
    def filter(self, value: float, alpha: float | None = None) -> float:
        """
        过滤值
        
        Args:
            value: 输入值
            alpha: 可选的动态平滑系数
            
        Returns:
            过滤后的值
        """
        if alpha is None:
            alpha = self._alpha
            
        if self._last_value is None:
            self._last_value = value
        else:
            self._last_value = alpha * value + (1 - alpha) * self._last_value
            
        return self._last_value
    
    def reset(self):
        """重置滤波器状态"""
        self._last_value = None
        self._last_time = None
    
    @property
    def last_value(self) -> float | None:
        """获取上一个过滤值"""
        return self._last_value


class OneEuroFilter:
    """
    One Euro Filter - 自适应低通滤波器
    
    特点:
    - 低速运动时平滑（减少抖动）
    - 高速运动时响应快（减少延迟）
    """
    
    def __init__(
        self,
        min_cutoff: float = 1.0,
        beta: float = 0.007,
        d_cutoff: float = 1.0,
    ):
        """
        初始化 One Euro Filter
        
        Args:
            min_cutoff: 最小截止频率 (越小越平滑)
            beta: 速度系数 (越大对速度变化越敏感)
            d_cutoff: 导数截止频率
        """
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        
        self._x_filter = LowPassFilter()
        self._dx_filter = LowPassFilter()
        self._last_time: float | None = None
    
    def _alpha(self, cutoff: float, te: float) -> float:
        """计算平滑系数"""
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / te)
    
    def filter(self, value: float, timestamp: float | None = None) -> float:
        """
        过滤值
        
        Args:
            value: 输入值
            timestamp: 时间戳 (秒)，如果不提供则使用当前时间
            
        Returns:
            过滤后的值
        """
        if timestamp is None:
            timestamp = time.time()
        
        if self._last_time is None:
            # 第一次调用
            self._last_time = timestamp
            self._x_filter.filter(value)
            self._dx_filter.filter(0.0)
            return value
        
        # 计算时间间隔
        te = timestamp - self._last_time
        if te <= 0:
            te = 1e-6  # 避免除零
        self._last_time = timestamp
        
        # 计算导数（速度）
        if self._x_filter.last_value is not None:
            dx = (value - self._x_filter.last_value) / te
        else:
            dx = 0.0
        
        # 过滤导数
        edx = self._dx_filter.filter(dx, self._alpha(self.d_cutoff, te))
        
        # 根据速度动态调整截止频率
        cutoff = self.min_cutoff + self.beta * abs(edx)
        
        # 过滤值
        return self._x_filter.filter(value, self._alpha(cutoff, te))
    
    def reset(self):
        """重置滤波器状态"""
        self._x_filter.reset()
        self._dx_filter.reset()
        self._last_time = None


class Smoother:
    """
    坐标平滑器
    
    对 (x, y) 坐标进行平滑处理。
    """
    
    def __init__(
        self,
        min_cutoff: float = 1.0,
        beta: float = 0.007,
        enabled: bool = True,
    ):
        """
        初始化坐标平滑器
        
        Args:
            min_cutoff: 最小截止频率
            beta: 速度系数
            enabled: 是否启用平滑
        """
        self.enabled = enabled
        self._x_filter = OneEuroFilter(min_cutoff, beta)
        self._y_filter = OneEuroFilter(min_cutoff, beta)
    
    def smooth(
        self,
        x: float,
        y: float,
        timestamp: float | None = None,
    ) -> tuple[float, float]:
        """
        平滑坐标
        
        Args:
            x: X 坐标
            y: Y 坐标
            timestamp: 时间戳
            
        Returns:
            平滑后的 (x, y) 坐标
        """
        if not self.enabled:
            return x, y
        
        return (
            self._x_filter.filter(x, timestamp),
            self._y_filter.filter(y, timestamp),
        )
    
    def reset(self):
        """重置平滑器状态"""
        self._x_filter.reset()
        self._y_filter.reset()
    
    def set_params(self, min_cutoff: float, beta: float):
        """
        设置平滑参数
        
        Args:
            min_cutoff: 最小截止频率
            beta: 速度系数
        """
        self._x_filter.min_cutoff = min_cutoff
        self._x_filter.beta = beta
        self._y_filter.min_cutoff = min_cutoff
        self._y_filter.beta = beta
