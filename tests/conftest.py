"""
LyraPointer 测试配置

配置 pytest 以正确导入项目模块。
"""

import sys
from pathlib import Path

# 获取项目根目录和 src 目录
project_root = Path(__file__).parent.parent
src_path = project_root / "src"

# 将 src 目录添加到 Python 路径
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 同时添加项目根目录，以支持 from src.xxx 导入
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# pytest fixtures 可以在这里定义，供所有测试使用

import pytest


@pytest.fixture
def sample_hand_landmarks():
    """提供示例手部关键点数据"""
    from tracker.hand_tracker import HandLandmarks, Point3D

    # 创建默认的 21 个关键点
    landmarks = [Point3D(0.5, 0.5, 0.0) for _ in range(21)]

    return HandLandmarks(
        landmarks=landmarks,
        handedness="Right",
        score=0.95,
    )


@pytest.fixture
def gesture_detector():
    """提供手势检测器实例"""
    from gestures.detector import GestureDetector

    return GestureDetector(
        pinch_threshold=0.05,
        click_hold_frames=3,
        double_click_interval=0.3,
    )


@pytest.fixture
def event_bus():
    """提供新的事件总线实例"""
    from core.events import EventBus

    return EventBus()


@pytest.fixture
def smoother():
    """提供平滑器实例"""
    from tracker.smoother import Smoother

    return Smoother(min_cutoff=1.0, beta=0.007)


@pytest.fixture
def state_machine():
    """提供状态机实例"""
    from core.state_machine import GestureStateMachine

    return GestureStateMachine()


@pytest.fixture
def config_validator():
    """提供配置验证器实例"""
    from config.validator import ConfigValidator

    return ConfigValidator()


@pytest.fixture
def sample_config():
    """提供示例配置字典"""
    return {
        "version": "1.0",
        "settings": {
            "sensitivity": 1.5,
            "smoothing": 0.7,
            "scroll_speed": 5,
            "control_zone": {
                "x_min": 0.15,
                "x_max": 0.85,
                "y_min": 0.15,
                "y_max": 0.85,
            },
            "camera": {
                "index": 0,
                "width": 640,
                "height": 480,
                "flip_x": True,
                "flip_y": False,
            },
            "performance": {
                "model_complexity": 0,
                "detection_confidence": 0.7,
                "tracking_confidence": 0.5,
            },
        },
        "ui": {
            "show_visualizer": True,
            "show_skeleton": True,
            "show_fps": True,
        },
    }
