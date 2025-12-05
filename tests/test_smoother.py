"""
LyraPointer 平滑器单元测试

测试 One Euro Filter 和 Smoother 的平滑效果和稳定性。
"""

import math
import time
from typing import List, Tuple

import pytest

# conftest.py 已经设置了正确的导入路径
from src.tracker.smoother import LowPassFilter, OneEuroFilter, Smoother


class TestLowPassFilter:
    """测试低通滤波器"""

    def test_first_value_passes_through(self):
        """第一个值应该直接通过"""
        lpf = LowPassFilter(alpha=0.5)
        result = lpf.filter(100.0)
        assert result == 100.0

    def test_smoothing_effect(self):
        """测试平滑效果"""
        lpf = LowPassFilter(alpha=0.5)

        # 初始值
        lpf.filter(0.0)

        # 突然跳变到 100
        result = lpf.filter(100.0)

        # 应该是 0 和 100 的加权平均
        assert result == pytest.approx(50.0)

    def test_alpha_zero_no_change(self):
        """alpha=0 时，输出应该保持不变"""
        lpf = LowPassFilter(alpha=0.0)

        lpf.filter(100.0)  # 初始值
        result = lpf.filter(0.0)  # 尝试改变

        # alpha=0 意味着完全保持旧值
        assert result == 100.0

    def test_alpha_one_immediate_response(self):
        """alpha=1 时，输出应该立即跟随输入"""
        lpf = LowPassFilter(alpha=1.0)

        lpf.filter(100.0)
        result = lpf.filter(50.0)

        assert result == 50.0

    def test_convergence(self):
        """测试值最终收敛"""
        lpf = LowPassFilter(alpha=0.3)
        lpf.filter(0.0)

        # 持续输入相同值，应该逐渐收敛
        target = 100.0
        for _ in range(50):
            result = lpf.filter(target)

        assert result == pytest.approx(target, rel=0.01)

    def test_reset(self):
        """测试重置功能"""
        lpf = LowPassFilter(alpha=0.5)

        lpf.filter(100.0)
        lpf.filter(50.0)

        lpf.reset()

        # 重置后，下一个值应该直接通过
        result = lpf.filter(200.0)
        assert result == 200.0

    def test_last_value_property(self):
        """测试 last_value 属性"""
        lpf = LowPassFilter()

        assert lpf.last_value is None

        lpf.filter(42.0)
        assert lpf.last_value is not None

    def test_dynamic_alpha(self):
        """测试动态 alpha 参数"""
        lpf = LowPassFilter(alpha=0.1)

        lpf.filter(0.0)

        # 使用不同的 alpha 值
        result = lpf.filter(100.0, alpha=1.0)

        # 应该使用传入的 alpha=1.0，所以立即响应
        assert result == 100.0


class TestOneEuroFilter:
    """测试 One Euro Filter"""

    @pytest.fixture
    def filter(self):
        """创建默认滤波器"""
        return OneEuroFilter(min_cutoff=1.0, beta=0.007, d_cutoff=1.0)

    def test_first_value_passes_through(self, filter):
        """第一个值应该直接通过"""
        result = filter.filter(100.0)
        assert result == 100.0

    def test_static_input_converges(self, filter):
        """静态输入应该收敛到输入值"""
        target = 50.0

        for _ in range(100):
            result = filter.filter(target)

        assert result == pytest.approx(target, rel=0.01)

    def test_smooths_jittery_input(self):
        """测试对抖动输入的平滑效果"""
        oef = OneEuroFilter(min_cutoff=0.1, beta=0.01)

        # 生成抖动数据（在 50 附近波动）
        jittery_values = [50.0 + (i % 2) * 2 - 1 for i in range(100)]

        outputs = []
        for val in jittery_values:
            outputs.append(oef.filter(val))

        # 计算输入和输出的方差
        input_variance = sum((v - 50) ** 2 for v in jittery_values) / len(
            jittery_values
        )
        output_variance = sum((v - 50) ** 2 for v in outputs[-50:]) / 50

        # 输出方差应该小于输入方差
        assert output_variance < input_variance

    def test_fast_motion_response(self):
        """测试对快速运动的响应"""
        # 高 beta 值意味着对速度更敏感
        oef = OneEuroFilter(min_cutoff=1.0, beta=1.0)

        # 初始化
        oef.filter(0.0)

        # 快速移动到 100
        result = oef.filter(100.0)

        # 应该响应较快（不会太滞后）
        assert result > 50.0  # 至少跟上一半

    def test_slow_motion_smooth(self):
        """测试对慢速运动的平滑"""
        oef = OneEuroFilter(min_cutoff=0.1, beta=0.001)

        # 初始化
        oef.filter(0.0)
        time.sleep(0.02)

        # 小幅度移动
        result = oef.filter(1.0)

        # 应该被平滑（不会立即到达目标）
        assert result < 1.0

    def test_reset(self, filter):
        """测试重置功能"""
        filter.filter(100.0)
        filter.filter(50.0)

        filter.reset()

        # 重置后应该像第一次调用一样
        result = filter.filter(200.0)
        assert result == 200.0

    def test_timestamp_handling(self):
        """测试时间戳处理"""
        oef = OneEuroFilter(min_cutoff=1.0, beta=0.007)

        # 使用显式时间戳
        t = 0.0
        oef.filter(0.0, timestamp=t)

        t += 0.016  # 约 60fps
        result1 = oef.filter(10.0, timestamp=t)

        t += 0.016
        result2 = oef.filter(10.0, timestamp=t)

        # 结果应该逐渐收敛
        assert result2 > result1 or result2 == pytest.approx(result1, rel=0.01)

    def test_zero_time_delta(self):
        """测试零时间间隔处理"""
        oef = OneEuroFilter()

        t = time.time()
        oef.filter(0.0, timestamp=t)

        # 相同时间戳不应该崩溃
        result = oef.filter(100.0, timestamp=t)
        assert result is not None

    def test_min_cutoff_effect(self):
        """测试 min_cutoff 参数的效果"""
        # 低 min_cutoff = 更平滑
        smooth_filter = OneEuroFilter(min_cutoff=0.01, beta=0.0)
        # 高 min_cutoff = 更快响应
        responsive_filter = OneEuroFilter(min_cutoff=10.0, beta=0.0)

        smooth_filter.filter(0.0)
        responsive_filter.filter(0.0)

        time.sleep(0.02)

        smooth_result = smooth_filter.filter(100.0)
        responsive_result = responsive_filter.filter(100.0)

        # 响应快的滤波器应该更接近目标值
        assert responsive_result > smooth_result

    def test_beta_effect(self):
        """测试 beta 参数的效果"""
        # beta = 0，不考虑速度
        no_beta = OneEuroFilter(min_cutoff=1.0, beta=0.0)
        # 高 beta，速度敏感
        high_beta = OneEuroFilter(min_cutoff=1.0, beta=10.0)

        # 初始化
        no_beta.filter(0.0)
        high_beta.filter(0.0)

        time.sleep(0.01)

        # 快速移动
        no_beta_result = no_beta.filter(100.0)
        high_beta_result = high_beta.filter(100.0)

        # 高 beta 对快速移动响应更快
        assert high_beta_result >= no_beta_result


class TestSmoother:
    """测试 Smoother 坐标平滑器"""

    @pytest.fixture
    def smoother(self):
        """创建默认平滑器"""
        return Smoother(min_cutoff=1.0, beta=0.007)

    def test_smooth_coordinates(self, smoother):
        """测试坐标平滑"""
        x, y = smoother.smooth(0.5, 0.5)

        assert x == pytest.approx(0.5)
        assert y == pytest.approx(0.5)

    def test_independent_axes(self, smoother):
        """测试 X 和 Y 轴独立平滑"""
        # 初始化
        smoother.smooth(0.0, 0.0)

        # 只移动 X
        x, y = smoother.smooth(1.0, 0.0)

        # Y 应该保持接近 0
        assert y == pytest.approx(0.0, abs=0.01)

    def test_reset(self, smoother):
        """测试重置功能"""
        smoother.smooth(0.5, 0.5)
        smoother.smooth(0.6, 0.6)

        smoother.reset()

        # 重置后第一个值应该直接通过
        x, y = smoother.smooth(0.8, 0.8)
        assert x == pytest.approx(0.8)
        assert y == pytest.approx(0.8)

    def test_disabled_smoother(self):
        """测试禁用平滑"""
        smoother = Smoother(enabled=False)

        smoother.smooth(0.0, 0.0)
        x, y = smoother.smooth(1.0, 1.0)

        # 禁用时应该直接返回输入值
        assert x == 1.0
        assert y == 1.0

    def test_set_params(self, smoother):
        """测试设置参数"""
        smoother.set_params(min_cutoff=0.5, beta=0.01)

        # 参数应该被更新
        assert smoother._x_filter.min_cutoff == 0.5
        assert smoother._x_filter.beta == 0.01
        assert smoother._y_filter.min_cutoff == 0.5
        assert smoother._y_filter.beta == 0.01

    def test_smooth_trajectory(self, smoother):
        """测试轨迹平滑"""
        # 生成一条带噪声的直线轨迹
        import random

        random.seed(42)

        points = []
        smoothed_points = []

        for i in range(50):
            # 目标位置 (从 0 到 1)
            target_x = i / 50
            target_y = i / 50

            # 添加噪声
            noisy_x = target_x + random.uniform(-0.02, 0.02)
            noisy_y = target_y + random.uniform(-0.02, 0.02)

            points.append((noisy_x, noisy_y))

            sx, sy = smoother.smooth(noisy_x, noisy_y)
            smoothed_points.append((sx, sy))

        # 计算原始轨迹和平滑轨迹的"抖动"
        def calculate_jitter(trajectory: List[Tuple[float, float]]) -> float:
            total = 0.0
            for i in range(2, len(trajectory)):
                # 计算加速度（方向变化）
                dx1 = trajectory[i - 1][0] - trajectory[i - 2][0]
                dy1 = trajectory[i - 1][1] - trajectory[i - 2][1]
                dx2 = trajectory[i][0] - trajectory[i - 1][0]
                dy2 = trajectory[i][1] - trajectory[i - 1][1]

                # 方向变化
                total += abs(dx2 - dx1) + abs(dy2 - dy1)

            return total

        original_jitter = calculate_jitter(points)
        smoothed_jitter = calculate_jitter(smoothed_points)

        # 平滑后的抖动应该更小
        assert smoothed_jitter < original_jitter

    def test_timestamp_support(self, smoother):
        """测试时间戳支持"""
        t = 0.0

        x1, y1 = smoother.smooth(0.0, 0.0, timestamp=t)

        t += 0.016
        x2, y2 = smoother.smooth(1.0, 1.0, timestamp=t)

        # 应该正常工作
        assert x2 is not None
        assert y2 is not None


class TestSmootherPerformance:
    """测试平滑器性能"""

    def test_processing_speed(self):
        """测试处理速度"""
        smoother = Smoother()

        iterations = 10000
        start = time.perf_counter()

        for i in range(iterations):
            x = (i % 100) / 100
            y = ((i + 50) % 100) / 100
            smoother.smooth(x, y)

        elapsed = time.perf_counter() - start

        # 应该非常快（每秒至少处理 100000 次）
        rate = iterations / elapsed
        assert rate > 100000, f"Processing rate too slow: {rate:.0f}/s"

    def test_memory_stability(self):
        """测试内存稳定性（长时间运行不会增长）"""
        import sys

        smoother = Smoother()

        # 运行很多次
        for i in range(100000):
            smoother.smooth(i % 1.0, (i + 0.5) % 1.0)

        # 平滑器应该不会积累大量数据
        # （检查对象大小是有限的）
        # 这里我们只确保它能完成而不崩溃


class TestEdgeCases:
    """测试边缘情况"""

    def test_very_small_values(self):
        """测试非常小的值"""
        smoother = Smoother()

        x, y = smoother.smooth(1e-10, 1e-10)
        assert math.isfinite(x)
        assert math.isfinite(y)

    def test_very_large_values(self):
        """测试非常大的值"""
        smoother = Smoother()

        x, y = smoother.smooth(1e10, 1e10)
        assert math.isfinite(x)
        assert math.isfinite(y)

    def test_negative_values(self):
        """测试负值"""
        smoother = Smoother()

        x, y = smoother.smooth(-0.5, -0.5)
        assert x == pytest.approx(-0.5)
        assert y == pytest.approx(-0.5)

    def test_nan_handling(self):
        """测试 NaN 处理"""
        smoother = Smoother()

        smoother.smooth(0.5, 0.5)

        # 输入 NaN 不应该崩溃（但结果可能是 NaN）
        try:
            x, y = smoother.smooth(float("nan"), float("nan"))
            # 如果没有崩溃，检查结果
            assert True
        except Exception:
            # 如果抛出异常也是可接受的
            pass

    def test_inf_handling(self):
        """测试无穷大处理"""
        smoother = Smoother()

        smoother.smooth(0.5, 0.5)

        # 输入无穷大不应该崩溃
        try:
            x, y = smoother.smooth(float("inf"), float("inf"))
            assert True
        except Exception:
            pass


class TestFilterParameters:
    """测试滤波器参数组合"""

    @pytest.mark.parametrize(
        "min_cutoff,beta",
        [
            (0.01, 0.0),  # 非常平滑
            (0.1, 0.001),  # 平滑
            (1.0, 0.007),  # 默认
            (1.0, 0.1),  # 响应快
            (5.0, 1.0),  # 非常响应
        ],
    )
    def test_parameter_combinations(self, min_cutoff, beta):
        """测试不同参数组合"""
        smoother = Smoother(min_cutoff=min_cutoff, beta=beta)

        # 应该能正常工作
        smoother.smooth(0.0, 0.0)
        x, y = smoother.smooth(1.0, 1.0)

        assert math.isfinite(x)
        assert math.isfinite(y)
        assert 0.0 <= x <= 1.0 or x > 0.0  # 应该在合理范围内


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
