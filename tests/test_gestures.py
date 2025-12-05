"""
LyraPointer 手势检测单元测试

测试手势识别的准确性和稳定性。
"""

import math
import time
from typing import List
from unittest.mock import MagicMock, patch

import pytest

# conftest.py 已经设置了正确的导入路径
from src.gestures.detector import GestureDetector
from src.gestures.gestures import (
    DEFAULT_GESTURE_ACTIONS,
    ActionType,
    Gesture,
    GestureType,
)
from src.tracker.hand_tracker import HandLandmarks, Point3D


class MockHandBuilder:
    """用于构建模拟手部数据的辅助类"""

    def __init__(self, handedness: str = "Right"):
        # 初始化所有 21 个关键点到默认位置
        self.landmarks = [Point3D(0.5, 0.5, 0.0) for _ in range(21)]
        self.handedness = handedness
        self.score = 0.95

    def set_wrist(self, x: float, y: float, z: float = 0.0) -> "MockHandBuilder":
        """设置手腕位置"""
        self.landmarks[0] = Point3D(x, y, z)
        return self

    def set_finger_extended(
        self, finger: str, extended: bool = True
    ) -> "MockHandBuilder":
        """设置手指伸出状态"""
        finger_tips = {
            "thumb": (4, 3, 2),  # TIP, IP, MCP
            "index": (8, 6, 5),
            "middle": (12, 10, 9),
            "ring": (16, 14, 13),
            "pinky": (20, 18, 17),
        }

        if finger not in finger_tips:
            return self

        tip_idx, pip_idx, mcp_idx = finger_tips[finger]
        base_x = self.landmarks[mcp_idx].x

        if finger == "thumb":
            # 拇指使用 x 坐标判断
            if self.handedness == "Right":
                tip_x = base_x - 0.1 if extended else base_x + 0.05
            else:
                tip_x = base_x + 0.1 if extended else base_x - 0.05
            self.landmarks[tip_idx] = Point3D(tip_x, 0.5, 0.0)
            self.landmarks[pip_idx] = Point3D(base_x, 0.5, 0.0)
            self.landmarks[mcp_idx] = Point3D(base_x, 0.5, 0.0)
        else:
            # 其他手指使用 y 坐标判断
            base_y = 0.6
            self.landmarks[mcp_idx] = Point3D(base_x, base_y, 0.0)
            self.landmarks[pip_idx] = Point3D(base_x, base_y - 0.05, 0.0)
            if extended:
                # 伸出：指尖在 PIP 和 MCP 上方
                self.landmarks[tip_idx] = Point3D(base_x, base_y - 0.15, 0.0)
            else:
                # 弯曲：指尖在下方
                self.landmarks[tip_idx] = Point3D(base_x, base_y + 0.05, 0.0)

        return self

    def set_all_fingers(self, extended: bool = True) -> "MockHandBuilder":
        """设置所有手指状态"""
        for finger in ["thumb", "index", "middle", "ring", "pinky"]:
            self.set_finger_extended(finger, extended)
        return self

    def set_pinch(
        self, finger1: str, finger2: str, distance: float = 0.02
    ) -> "MockHandBuilder":
        """设置两指捏合"""
        tips = {
            "thumb": 4,
            "index": 8,
            "middle": 12,
            "ring": 16,
            "pinky": 20,
        }

        tip1_idx = tips.get(finger1)
        tip2_idx = tips.get(finger2)

        if tip1_idx is None or tip2_idx is None:
            return self

        # 将两指尖放在靠近的位置
        center_x, center_y = 0.5, 0.5
        self.landmarks[tip1_idx] = Point3D(center_x - distance / 2, center_y, 0.0)
        self.landmarks[tip2_idx] = Point3D(center_x + distance / 2, center_y, 0.0)

        return self

    def build(self) -> HandLandmarks:
        """构建 HandLandmarks 对象"""
        return HandLandmarks(
            landmarks=self.landmarks.copy(),
            handedness=self.handedness,
            score=self.score,
        )


class TestGestureType:
    """测试手势类型枚举"""

    def test_gesture_types_exist(self):
        """确认所有预期的手势类型都存在"""
        expected_types = [
            "NONE",
            "FIST",
            "PALM",
            "POINTER",
            "CLICK",
            "CLICK_HOLD",
            "RIGHT_CLICK",
            "DOUBLE_CLICK",
            "SCROLL",
            "SCROLL_UP",
            "SCROLL_DOWN",
        ]
        for type_name in expected_types:
            assert hasattr(GestureType, type_name), f"Missing GestureType.{type_name}"

    def test_default_gesture_actions_mapping(self):
        """测试默认手势-动作映射"""
        assert GestureType.POINTER in DEFAULT_GESTURE_ACTIONS
        assert GestureType.CLICK in DEFAULT_GESTURE_ACTIONS
        assert DEFAULT_GESTURE_ACTIONS[GestureType.POINTER] == ActionType.MOVE_CURSOR
        assert DEFAULT_GESTURE_ACTIONS[GestureType.CLICK] == ActionType.LEFT_CLICK


class TestGesture:
    """测试 Gesture 数据类"""

    def test_gesture_creation(self):
        """测试手势对象创建"""
        gesture = Gesture(type=GestureType.POINTER)
        assert gesture.type == GestureType.POINTER
        assert gesture.confidence == 1.0
        assert gesture.frames == 0

    def test_gesture_equality(self):
        """测试手势比较"""
        gesture1 = Gesture(type=GestureType.CLICK)
        gesture2 = Gesture(type=GestureType.CLICK)
        gesture3 = Gesture(type=GestureType.POINTER)

        assert gesture1 == gesture2
        assert gesture1 != gesture3
        assert gesture1 == GestureType.CLICK

    def test_gesture_with_data(self):
        """测试带数据的手势"""
        gesture = Gesture(
            type=GestureType.CLICK,
            data={"pinch_distance": 0.03},
            frames=5,
        )
        assert gesture.data["pinch_distance"] == 0.03
        assert gesture.frames == 5


class TestGestureDetector:
    """测试 GestureDetector"""

    @pytest.fixture
    def detector(self):
        """创建检测器实例"""
        return GestureDetector(
            pinch_threshold=0.05,
            click_hold_frames=3,
            double_click_interval=0.3,
        )

    @pytest.fixture
    def builder(self):
        """创建手部数据构建器"""
        return MockHandBuilder()

    # ===== 基础手势测试 =====

    def test_detect_pointer(self, detector, builder):
        """测试指针模式检测"""
        # 只有食指伸出
        hand = builder.set_all_fingers(False).set_finger_extended("index", True).build()

        gesture = detector.detect(hand)
        assert gesture.type == GestureType.POINTER

    def test_detect_fist(self, detector, builder):
        """测试握拳检测"""
        # 所有手指弯曲
        hand = builder.set_all_fingers(False).build()

        gesture = detector.detect(hand)
        assert gesture.type == GestureType.FIST

    def test_detect_palm(self, detector, builder):
        """测试手掌张开检测"""
        # 所有手指伸出
        hand = builder.set_all_fingers(True).build()

        gesture = detector.detect(hand)
        assert gesture.type == GestureType.PALM

    def test_detect_scroll_mode(self, detector, builder):
        """测试滚动模式检测"""
        # 食指和中指伸出
        hand = (
            builder.set_all_fingers(False)
            .set_finger_extended("index", True)
            .set_finger_extended("middle", True)
            .build()
        )

        gesture = detector.detect(hand)
        assert gesture.type == GestureType.SCROLL

    # ===== 点击手势测试 =====

    def test_detect_click(self, detector, builder):
        """测试点击检测（拇指+食指捏合）"""
        hand = (
            builder.set_all_fingers(False)
            .set_pinch("thumb", "index", distance=0.03)
            .build()
        )

        gesture = detector.detect(hand)
        assert gesture.type == GestureType.CLICK

    def test_detect_right_click(self, detector, builder):
        """测试右键检测（拇指+中指捏合）"""
        hand = (
            builder.set_all_fingers(False)
            .set_pinch("thumb", "middle", distance=0.03)
            .build()
        )

        gesture = detector.detect(hand)
        assert gesture.type == GestureType.RIGHT_CLICK

    def test_no_click_when_distance_too_large(self, detector, builder):
        """测试捏合距离过大时不触发点击"""
        hand = (
            builder.set_all_fingers(False)
            .set_pinch("thumb", "index", distance=0.1)  # 大于阈值
            .set_finger_extended("index", True)
            .build()
        )

        gesture = detector.detect(hand)
        # 应该是指针模式而不是点击
        assert gesture.type != GestureType.CLICK

    # ===== 帧计数测试 =====

    def test_frame_counter_increments(self, detector, builder):
        """测试帧计数递增"""
        hand = builder.set_all_fingers(False).set_finger_extended("index", True).build()

        # 连续检测相同手势
        for i in range(5):
            gesture = detector.detect(hand)
            assert gesture.frames == i + 1

    def test_frame_counter_resets_on_change(self, detector, builder):
        """测试手势变化时帧计数重置"""
        # 先检测指针模式
        pointer_hand = (
            MockHandBuilder()
            .set_all_fingers(False)
            .set_finger_extended("index", True)
            .build()
        )
        for _ in range(3):
            detector.detect(pointer_hand)

        # 切换到握拳
        fist_hand = MockHandBuilder().set_all_fingers(False).build()
        gesture = detector.detect(fist_hand)

        assert gesture.type == GestureType.FIST
        assert gesture.frames == 1

    # ===== 点击保持（拖拽）测试 =====

    def test_click_hold_detection(self, detector, builder):
        """测试点击保持（拖拽）检测"""
        hand = (
            builder.set_all_fingers(False)
            .set_pinch("thumb", "index", distance=0.03)
            .build()
        )

        # 连续检测超过 click_hold_frames
        for i in range(detector.click_hold_frames + 2):
            gesture = detector.detect(hand)

        # 应该变成 CLICK_HOLD
        assert gesture.type == GestureType.CLICK_HOLD

    # ===== 双击测试 =====

    def test_double_click_detection(self, detector):
        """测试双击检测"""
        # 第一次点击
        click_hand = (
            MockHandBuilder()
            .set_all_fingers(False)
            .set_pinch("thumb", "index", distance=0.03)
            .build()
        )
        detector.detect(click_hand)

        # 释放
        release_hand = (
            MockHandBuilder()
            .set_all_fingers(False)
            .set_finger_extended("index", True)
            .build()
        )
        detector.detect(release_hand)

        # 快速第二次点击
        gesture = detector.detect(click_hand)

        # 应该检测到双击
        assert gesture.type == GestureType.DOUBLE_CLICK

    def test_no_double_click_when_too_slow(self, detector):
        """测试间隔过长时不触发双击"""
        click_hand = (
            MockHandBuilder()
            .set_all_fingers(False)
            .set_pinch("thumb", "index", distance=0.03)
            .build()
        )

        detector.detect(click_hand)

        # 等待超过双击间隔
        time.sleep(detector.double_click_interval + 0.1)

        # 第二次点击
        gesture = detector.detect(click_hand)

        # 不应该是双击
        assert gesture.type != GestureType.DOUBLE_CLICK

    # ===== 状态重置测试 =====

    def test_reset(self, detector, builder):
        """测试检测器重置"""
        # 先进行一些检测
        hand = builder.set_all_fingers(False).set_finger_extended("index", True).build()
        for _ in range(5):
            detector.detect(hand)

        # 重置
        detector.reset()

        # 重置后帧计数应该重新开始
        gesture = detector.detect(hand)
        assert gesture.frames == 1


class TestHandLandmarks:
    """测试 HandLandmarks 数据类"""

    @pytest.fixture
    def hand(self):
        """创建测试用手部数据"""
        return MockHandBuilder().set_all_fingers(True).build()

    def test_get_finger_tip(self, hand):
        """测试获取手指尖端"""
        tip = hand.get_finger_tip("index")
        assert isinstance(tip, Point3D)
        assert tip.x is not None
        assert tip.y is not None

    def test_get_finger_pip(self, hand):
        """测试获取手指中间关节"""
        pip = hand.get_finger_pip("index")
        assert isinstance(pip, Point3D)

    def test_get_wrist(self, hand):
        """测试获取手腕"""
        wrist = hand.get_wrist()
        assert isinstance(wrist, Point3D)

    def test_finger_tip_indices(self):
        """测试手指尖端索引正确"""
        expected = {
            "thumb": 4,
            "index": 8,
            "middle": 12,
            "ring": 16,
            "pinky": 20,
        }
        assert HandLandmarks.FINGER_TIPS == expected


class TestPoint3D:
    """测试 Point3D 数据类"""

    def test_to_tuple(self):
        """测试转换为 2D 元组"""
        point = Point3D(0.5, 0.3, 0.1)
        result = point.to_tuple()
        assert result == (0.5, 0.3)

    def test_to_pixel(self):
        """测试转换为像素坐标"""
        point = Point3D(0.5, 0.5, 0.0)
        px, py = point.to_pixel(640, 480)
        assert px == 320
        assert py == 240

    def test_to_pixel_edge_cases(self):
        """测试边缘情况的像素转换"""
        # 左上角
        p1 = Point3D(0.0, 0.0, 0.0)
        assert p1.to_pixel(100, 100) == (0, 0)

        # 右下角
        p2 = Point3D(1.0, 1.0, 0.0)
        assert p2.to_pixel(100, 100) == (100, 100)


class TestEdgeCases:
    """测试边缘情况"""

    @pytest.fixture
    def detector(self):
        return GestureDetector()

    def test_left_hand(self, detector):
        """测试左手识别"""
        hand = MockHandBuilder(handedness="Left").set_all_fingers(True).build()
        gesture = detector.detect(hand)
        # 左手也应该能正确识别手掌
        assert gesture.type == GestureType.PALM

    def test_low_confidence_hand(self, detector):
        """测试低置信度手部数据"""
        builder = MockHandBuilder()
        builder.score = 0.3  # 低置信度
        hand = builder.set_all_fingers(True).build()

        # 应该仍然能检测（置信度过滤应该在 tracker 层处理）
        gesture = detector.detect(hand)
        assert gesture is not None

    def test_rapid_gesture_changes(self, detector):
        """测试快速手势切换"""
        gestures = []

        for _ in range(10):
            # 交替切换手势
            pointer = (
                MockHandBuilder()
                .set_all_fingers(False)
                .set_finger_extended("index", True)
                .build()
            )
            fist = MockHandBuilder().set_all_fingers(False).build()

            gestures.append(detector.detect(pointer).type)
            gestures.append(detector.detect(fist).type)

        # 应该有指针和握拳的交替
        assert GestureType.POINTER in gestures
        assert GestureType.FIST in gestures


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
