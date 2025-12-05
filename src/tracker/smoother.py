"""
轨迹平滑算法

使用改进的 One Euro Filter 算法减少手部追踪的抖动，同时保持低延迟。
参考: https://gery.casiez.net/1euro/

改进点：
- 添加预设模式（响应优先/平衡/稳定优先）
- 优化参数映射，提升跟手感
- 添加抖动检测和自适应平滑
- 支持动态参数调整
"""

import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class SmoothingPreset(Enum):
    """平滑预设模式"""

    RESPONSIVE = "responsive"  # 响应优先 - 最跟手，适合快速操作
    BALANCED = "balanced"  # 平衡模式 - 默认推荐
    STABLE = "stable"  # 稳定优先 - 最平滑，适合精细操作
    CUSTOM = "custom"  # 自定义


@dataclass
class SmoothingParams:
    """平滑参数"""

    min_cutoff: float  # 最小截止频率 (越小越平滑)
    beta: float  # 速度系数 (越大对速度变化越敏感)
    d_cutoff: float  # 导数截止频率

    @classmethod
    def from_preset(cls, preset: SmoothingPreset) -> "SmoothingParams":
        """从预设创建参数"""
        presets = {
            # 响应优先：高 min_cutoff，高 beta，快速响应
            SmoothingPreset.RESPONSIVE: cls(
                min_cutoff=1.5,
                beta=0.5,
                d_cutoff=1.0,
            ),
            # 平衡模式：中等参数
            SmoothingPreset.BALANCED: cls(
                min_cutoff=0.8,
                beta=0.4,
                d_cutoff=1.0,
            ),
            # 稳定优先：低 min_cutoff，低 beta，更平滑
            SmoothingPreset.STABLE: cls(
                min_cutoff=0.3,
                beta=0.1,
                d_cutoff=1.0,
            ),
            # 自定义默认值
            SmoothingPreset.CUSTOM: cls(
                min_cutoff=0.8,
                beta=0.4,
                d_cutoff=1.0,
            ),
        }
        return presets.get(preset, presets[SmoothingPreset.BALANCED])

    @classmethod
    def from_smoothing_value(cls, smoothing: float) -> "SmoothingParams":
        """
        从 0-1 的平滑值创建参数

        smoothing = 0: 最跟手（几乎无平滑）
        smoothing = 0.5: 平衡
        smoothing = 1: 最平滑（延迟较大）
        """
        # 限制范围
        smoothing = max(0.0, min(1.0, smoothing))

        # 非线性映射，让中间值更实用
        # 使用平方曲线，让低平滑值变化更明显
        t = smoothing

        # min_cutoff: 1.5 -> 0.2 (越平滑越小)
        min_cutoff = 1.5 - t * 1.3

        # beta: 0.6 -> 0.05 (越平滑越小)
        beta = 0.6 - t * 0.55

        return cls(
            min_cutoff=max(0.1, min_cutoff),
            beta=max(0.01, beta),
            d_cutoff=1.0,
        )


class LowPassFilter:
    """低通滤波器"""

    def __init__(self, alpha: float = 0.5):
        """
        初始化低通滤波器

        Args:
            alpha: 平滑系数 (0-1, 越小越平滑)
        """
        self._alpha = alpha
        self._last_value: Optional[float] = None

    def filter(self, value: float, alpha: Optional[float] = None) -> float:
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

    @property
    def last_value(self) -> Optional[float]:
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
        min_cutoff: float = 0.8,
        beta: float = 0.4,
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
        self._last_time: Optional[float] = None

    def _compute_alpha(self, cutoff: float, te: float) -> float:
        """计算平滑系数"""
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / te)

    def filter(self, value: float, timestamp: Optional[float] = None) -> float:
        """
        过滤值

        Args:
            value: 输入值
            timestamp: 时间戳 (秒)

        Returns:
            过滤后的值
        """
        if timestamp is None:
            timestamp = time.perf_counter()

        if self._last_time is None:
            # 第一次调用，直接返回
            self._last_time = timestamp
            self._x_filter.filter(value)
            self._dx_filter.filter(0.0)
            return value

        # 计算时间间隔
        te = timestamp - self._last_time
        if te <= 0:
            te = 1e-6
        self._last_time = timestamp

        # 计算导数（速度）
        dx = 0.0
        if self._x_filter.last_value is not None:
            dx = (value - self._x_filter.last_value) / te

        # 过滤导数
        edx = self._dx_filter.filter(dx, self._compute_alpha(self.d_cutoff, te))

        # 根据速度动态调整截止频率
        # 速度越快，cutoff 越大，响应越快
        cutoff = self.min_cutoff + self.beta * abs(edx)

        # 过滤值
        return self._x_filter.filter(value, self._compute_alpha(cutoff, te))

    def reset(self):
        """重置滤波器状态"""
        self._x_filter.reset()
        self._dx_filter.reset()
        self._last_time = None

    def set_params(self, min_cutoff: float, beta: float, d_cutoff: float = 1.0):
        """设置参数"""
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff


class Smoother:
    """
    坐标平滑器

    对 (x, y) 坐标进行平滑处理，支持多种预设模式。
    """

    def __init__(
        self,
        preset: SmoothingPreset = SmoothingPreset.BALANCED,
        smoothing: Optional[float] = None,
        enabled: bool = True,
    ):
        """
        初始化坐标平滑器

        Args:
            preset: 预设模式
            smoothing: 0-1 的平滑值（如果提供，覆盖预设）
            enabled: 是否启用平滑
        """
        self.enabled = enabled
        self._preset = preset

        # 获取参数
        if smoothing is not None:
            params = SmoothingParams.from_smoothing_value(smoothing)
        else:
            params = SmoothingParams.from_preset(preset)

        self._params = params
        self._x_filter = OneEuroFilter(params.min_cutoff, params.beta, params.d_cutoff)
        self._y_filter = OneEuroFilter(params.min_cutoff, params.beta, params.d_cutoff)

        # 抖动检测
        self._jitter_threshold = 0.002  # 小于此值视为抖动
        self._last_x: Optional[float] = None
        self._last_y: Optional[float] = None
        self._jitter_count = 0

    def smooth(
        self,
        x: float,
        y: float,
        timestamp: Optional[float] = None,
    ) -> Tuple[float, float]:
        """
        平滑坐标

        Args:
            x: X 坐标 (0-1)
            y: Y 坐标 (0-1)
            timestamp: 时间戳

        Returns:
            平滑后的 (x, y) 坐标
        """
        if not self.enabled:
            return x, y

        if timestamp is None:
            timestamp = time.perf_counter()

        # 抖动检测：如果移动很小，增加额外平滑
        if self._last_x is not None and self._last_y is not None:
            dx = abs(x - self._last_x)
            dy = abs(y - self._last_y)
            movement = math.sqrt(dx * dx + dy * dy)

            if movement < self._jitter_threshold:
                self._jitter_count = min(self._jitter_count + 1, 10)
            else:
                self._jitter_count = max(self._jitter_count - 2, 0)

        self._last_x = x
        self._last_y = y

        # 应用滤波
        filtered_x = self._x_filter.filter(x, timestamp)
        filtered_y = self._y_filter.filter(y, timestamp)

        # 如果检测到持续抖动，额外平滑
        if self._jitter_count > 5:
            # 使用更强的低通滤波
            alpha = 0.3
            if hasattr(self, "_extra_x"):
                self._extra_x = alpha * filtered_x + (1 - alpha) * self._extra_x
                self._extra_y = alpha * filtered_y + (1 - alpha) * self._extra_y
            else:
                self._extra_x = filtered_x
                self._extra_y = filtered_y
            return self._extra_x, self._extra_y

        # 清除额外平滑状态
        if hasattr(self, "_extra_x"):
            del self._extra_x
            del self._extra_y

        return filtered_x, filtered_y

    def reset(self):
        """重置平滑器状态"""
        self._x_filter.reset()
        self._y_filter.reset()
        self._last_x = None
        self._last_y = None
        self._jitter_count = 0
        if hasattr(self, "_extra_x"):
            del self._extra_x
            del self._extra_y

    def set_preset(self, preset: SmoothingPreset):
        """设置预设模式"""
        self._preset = preset
        params = SmoothingParams.from_preset(preset)
        self._apply_params(params)

    def set_smoothing(self, smoothing: float):
        """
        设置平滑值

        Args:
            smoothing: 0-1 的值，0=最跟手，1=最平滑
        """
        self._preset = SmoothingPreset.CUSTOM
        params = SmoothingParams.from_smoothing_value(smoothing)
        self._apply_params(params)

    def set_params(self, min_cutoff: float, beta: float, d_cutoff: float = 1.0):
        """直接设置滤波器参数"""
        self._preset = SmoothingPreset.CUSTOM
        self._params = SmoothingParams(min_cutoff, beta, d_cutoff)
        self._x_filter.set_params(min_cutoff, beta, d_cutoff)
        self._y_filter.set_params(min_cutoff, beta, d_cutoff)

    def _apply_params(self, params: SmoothingParams):
        """应用参数到滤波器"""
        self._params = params
        self._x_filter.set_params(params.min_cutoff, params.beta, params.d_cutoff)
        self._y_filter.set_params(params.min_cutoff, params.beta, params.d_cutoff)

    @property
    def preset(self) -> SmoothingPreset:
        """当前预设"""
        return self._preset

    @property
    def params(self) -> SmoothingParams:
        """当前参数"""
        return self._params

    @property
    def min_cutoff(self) -> float:
        """最小截止频率"""
        return self._params.min_cutoff

    @min_cutoff.setter
    def min_cutoff(self, value: float):
        """设置最小截止频率"""
        self._params.min_cutoff = value
        self._x_filter.min_cutoff = value
        self._y_filter.min_cutoff = value

    @property
    def beta(self) -> float:
        """速度系数"""
        return self._params.beta

    @beta.setter
    def beta(self, value: float):
        """设置速度系数"""
        self._params.beta = value
        self._x_filter.beta = value
        self._y_filter.beta = value
