"""
手势检测器

根据手部关键点判断当前手势类型。
优化版本 - 更可靠的检测和更低的触发阈值。
"""

import math
import time
from enum import Enum
from typing import Optional

from ..tracker.hand_tracker import HandLandmarks, Point3D
from .gestures import Gesture, GestureType


class ClickState(Enum):
    """点击状态"""

    IDLE = "idle"
    PINCHING = "pinching"
    CLICKED = "clicked"
    HOLDING = "holding"


class GestureDetector:
    """手势检测器 - 优化版"""

    def __init__(
        self,
        pinch_threshold: float = 0.07,  # 增大阈值，更容易触发
        pinch_release_threshold: float = 0.10,  # 释放阈值（比触发大，防止抖动）
        click_hold_frames: int = 2,  # 减少，更快响应
        double_click_interval: float = 0.4,  # 增加间隔
        pause_hold_frames: int = 8,
        finger_extend_threshold: float = 0.6,  # 手指伸展判断阈值
    ):
        """
        初始化手势检测器

        Args:
            pinch_threshold: 捏合判定阈值（归一化距离）
            pinch_release_threshold: 捏合释放阈值
            click_hold_frames: 点击需要保持的帧数
            double_click_interval: 双击间隔（秒）
            pause_hold_frames: 暂停手势需要保持的帧数
            finger_extend_threshold: 手指伸展判断阈值
        """
        self.pinch_threshold = pinch_threshold
        self.pinch_release_threshold = pinch_release_threshold
        self.click_hold_frames = click_hold_frames
        self.double_click_interval = double_click_interval
        self.pause_hold_frames = pause_hold_frames
        self.finger_extend_threshold = finger_extend_threshold

        # 状态追踪
        self._last_gesture: Optional[Gesture] = None
        self._gesture_frames: int = 0

        # 点击状态机
        self._click_state = ClickState.IDLE
        self._pinch_start_time: float = 0
        self._last_click_time: float = 0
        self._click_count: int = 0

        # 滚动状态
        self._scroll_start_y: Optional[float] = None
        self._scroll_accumulator: float = 0

        # 调试计数
        self._debug_counter = 0

    def detect(self, hand: HandLandmarks) -> Gesture:
        """
        检测当前手势

        Args:
            hand: 手部关键点数据

        Returns:
            检测到的手势
        """
        # 获取手指状态
        fingers = self._get_fingers_extended(hand)

        # 计算捏合距离
        thumb_index_dist = self._get_pinch_distance(hand, "thumb", "index")
        thumb_middle_dist = self._get_pinch_distance(hand, "thumb", "middle")

        # 判断捏合状态（使用滞后阈值防止抖动）
        if self._click_state == ClickState.IDLE:
            is_thumb_index_pinch = thumb_index_dist < self.pinch_threshold
            is_thumb_middle_pinch = thumb_middle_dist < self.pinch_threshold
        else:
            # 已经在捏合状态，使用更大的释放阈值
            is_thumb_index_pinch = thumb_index_dist < self.pinch_release_threshold
            is_thumb_middle_pinch = thumb_middle_dist < self.pinch_release_threshold

        gesture_type = GestureType.NONE
        data = {
            "thumb_index_dist": thumb_index_dist,
            "thumb_middle_dist": thumb_middle_dist,
            "fingers": fingers,
        }

        current_time = time.time()

        # ===== 手势判断优先级 =====

        # 1. 检测五指张开（暂停）
        all_extended = all(
            [
                fingers["index"],
                fingers["middle"],
                fingers["ring"],
                fingers["pinky"],
            ]
        )
        if all_extended and fingers["thumb"]:
            gesture_type = GestureType.PALM
            self._reset_click_state()

        # 2. 检测握拳（休息）
        elif not any(
            [
                fingers["index"],
                fingers["middle"],
                fingers["ring"],
                fingers["pinky"],
            ]
        ):
            gesture_type = GestureType.FIST
            self._reset_click_state()

        # 3. 检测滚动模式（食指+中指伸出，其他收起）
        elif (
            fingers["index"]
            and fingers["middle"]
            and not fingers["ring"]
            and not fingers["pinky"]
            and not is_thumb_index_pinch  # 不能同时捏合
        ):
            gesture_type = self._detect_scroll(hand)
            self._reset_click_state()

        # 4. 检测右键（拇指+中指捏合）
        elif is_thumb_middle_pinch and not is_thumb_index_pinch:
            gesture_type = GestureType.RIGHT_CLICK
            data["pinch_distance"] = thumb_middle_dist
            self._reset_click_state()

        # 5. 检测左键/拖拽（拇指+食指捏合）
        elif is_thumb_index_pinch:
            gesture_type = self._handle_click_state(current_time)
            data["pinch_distance"] = thumb_index_dist

        # 6. 检测指针模式（只有食指伸出）
        elif (
            fingers["index"]
            and not fingers["middle"]
            and not fingers["ring"]
            and not fingers["pinky"]
        ):
            gesture_type = GestureType.POINTER
            index_tip = hand.get_finger_tip("index")
            data["pointer_position"] = (index_tip.x, index_tip.y)
            self._reset_click_state()

        # 如果没有捏合，重置点击状态
        if not is_thumb_index_pinch and self._click_state != ClickState.IDLE:
            # 检查是否是快速点击
            if self._click_state == ClickState.PINCHING:
                pinch_duration = current_time - self._pinch_start_time
                if pinch_duration < 0.3:  # 短按 = 点击
                    # 检查双击
                    if (
                        current_time - self._last_click_time
                        < self.double_click_interval
                    ):
                        self._click_count += 1
                    else:
                        self._click_count = 1
                    self._last_click_time = current_time

            self._reset_click_state()

        # 重置滚动状态（非滚动模式时）
        if gesture_type not in [
            GestureType.SCROLL,
            GestureType.SCROLL_UP,
            GestureType.SCROLL_DOWN,
        ]:
            self._scroll_start_y = None
            self._scroll_accumulator = 0

        # ===== 构建手势对象 =====
        gesture = Gesture(type=gesture_type, data=data)

        # 帧计数
        if self._last_gesture and self._last_gesture.type == gesture_type:
            self._gesture_frames += 1
        else:
            self._gesture_frames = 1

        gesture.frames = self._gesture_frames

        # 检查双击
        if gesture_type == GestureType.CLICK and self._click_count >= 2:
            gesture = Gesture(
                type=GestureType.DOUBLE_CLICK, data=data, frames=self._gesture_frames
            )
            self._click_count = 0

        self._last_gesture = gesture
        return gesture

    def _handle_click_state(self, current_time: float) -> GestureType:
        """
        处理点击状态机

        Returns:
            当前手势类型
        """
        if self._click_state == ClickState.IDLE:
            # 开始捏合
            self._click_state = ClickState.PINCHING
            self._pinch_start_time = current_time
            return GestureType.CLICK

        elif self._click_state == ClickState.PINCHING:
            # 检查是否应该变成拖拽
            pinch_duration = current_time - self._pinch_start_time
            if pinch_duration > 0.25:  # 保持 250ms 进入拖拽
                self._click_state = ClickState.HOLDING
                return GestureType.CLICK_HOLD
            return GestureType.CLICK

        elif self._click_state == ClickState.HOLDING:
            # 拖拽中
            return GestureType.CLICK_HOLD

        return GestureType.CLICK

    def _detect_scroll(self, hand: HandLandmarks) -> GestureType:
        """
        检测滚动方向

        Args:
            hand: 手部关键点

        Returns:
            滚动手势类型
        """
        index_tip = hand.get_finger_tip("index")
        current_y = index_tip.y

        if self._scroll_start_y is None:
            self._scroll_start_y = current_y
            return GestureType.SCROLL

        # 计算移动量
        delta_y = current_y - self._scroll_start_y
        self._scroll_accumulator += delta_y

        # 更新起始点（平滑跟踪）
        self._scroll_start_y = current_y

        # 滚动阈值
        scroll_threshold = 0.03

        if self._scroll_accumulator > scroll_threshold:
            self._scroll_accumulator = 0
            return GestureType.SCROLL_DOWN
        elif self._scroll_accumulator < -scroll_threshold:
            self._scroll_accumulator = 0
            return GestureType.SCROLL_UP

        return GestureType.SCROLL

    def _get_fingers_extended(self, hand: HandLandmarks) -> dict[str, bool]:
        """
        判断各手指是否伸出（改进算法）

        使用手指尖与手掌中心的相对位置，以及手指弯曲角度综合判断
        """
        result = {}
        wrist = hand.landmarks[0]  # 手腕

        # 拇指 - 使用 x 坐标相对位置
        thumb_tip = hand.get_finger_tip("thumb")
        thumb_ip = hand.landmarks[3]  # 拇指 IP 关节
        thumb_mcp = hand.get_finger_mcp("thumb")

        # 计算拇指伸展程度
        thumb_tip_to_ip = math.sqrt(
            (thumb_tip.x - thumb_ip.x) ** 2 + (thumb_tip.y - thumb_ip.y) ** 2
        )
        thumb_mcp_to_ip = math.sqrt(
            (thumb_mcp.x - thumb_ip.x) ** 2 + (thumb_mcp.y - thumb_ip.y) ** 2
        )

        # 根据手的类型调整判断
        if hand.handedness == "Right":
            result["thumb"] = thumb_tip.x < thumb_ip.x - 0.02
        else:
            result["thumb"] = thumb_tip.x > thumb_ip.x + 0.02

        # 其他手指 - 使用更可靠的判断方法
        finger_indices = {
            "index": (5, 6, 7, 8),
            "middle": (9, 10, 11, 12),
            "ring": (13, 14, 15, 16),
            "pinky": (17, 18, 19, 20),
        }

        for finger, (mcp_idx, pip_idx, dip_idx, tip_idx) in finger_indices.items():
            mcp = hand.landmarks[mcp_idx]
            pip = hand.landmarks[pip_idx]
            dip = hand.landmarks[dip_idx]
            tip = hand.landmarks[tip_idx]

            # 方法1: 指尖 y 坐标是否高于 PIP
            tip_above_pip = tip.y < pip.y

            # 方法2: 手指是否伸直（使用角度）
            # 计算 MCP->PIP 和 PIP->TIP 的向量夹角
            vec1 = (pip.x - mcp.x, pip.y - mcp.y)
            vec2 = (tip.x - pip.x, tip.y - pip.y)

            dot = vec1[0] * vec2[0] + vec1[1] * vec2[1]
            mag1 = math.sqrt(vec1[0] ** 2 + vec1[1] ** 2)
            mag2 = math.sqrt(vec2[0] ** 2 + vec2[1] ** 2)

            if mag1 > 0 and mag2 > 0:
                cos_angle = dot / (mag1 * mag2)
                cos_angle = max(-1, min(1, cos_angle))  # 限制范围
                is_straight = cos_angle > 0.5  # 夹角小于 60 度认为伸直
            else:
                is_straight = False

            # 方法3: 指尖到手腕的距离 vs MCP 到手腕的距离
            tip_to_wrist = math.sqrt((tip.x - wrist.x) ** 2 + (tip.y - wrist.y) ** 2)
            mcp_to_wrist = math.sqrt((mcp.x - wrist.x) ** 2 + (mcp.y - wrist.y) ** 2)
            tip_far = tip_to_wrist > mcp_to_wrist * 0.9

            # 综合判断：至少满足两个条件
            conditions_met = sum([tip_above_pip, is_straight, tip_far])
            result[finger] = conditions_met >= 2

        return result

    def _get_pinch_distance(
        self,
        hand: HandLandmarks,
        finger1: str,
        finger2: str,
    ) -> float:
        """
        计算两指尖之间的距离（归一化）

        Args:
            hand: 手部关键点数据
            finger1: 第一个手指名称
            finger2: 第二个手指名称

        Returns:
            归一化的距离 (0-1)
        """
        tip1 = hand.get_finger_tip(finger1)
        tip2 = hand.get_finger_tip(finger2)

        # 2D 距离（忽略 z，因为深度估计不准）
        distance = math.sqrt((tip1.x - tip2.x) ** 2 + (tip1.y - tip2.y) ** 2)

        return distance

    def _reset_click_state(self):
        """重置点击状态"""
        self._click_state = ClickState.IDLE
        self._pinch_start_time = 0

    def reset(self):
        """重置检测器状态"""
        self._last_gesture = None
        self._gesture_frames = 0
        self._click_state = ClickState.IDLE
        self._pinch_start_time = 0
        self._last_click_time = 0
        self._click_count = 0
        self._scroll_start_y = None
        self._scroll_accumulator = 0

    def get_debug_info(self) -> dict:
        """获取调试信息"""
        return {
            "click_state": self._click_state.value,
            "gesture_frames": self._gesture_frames,
            "click_count": self._click_count,
            "last_gesture": self._last_gesture.type.name
            if self._last_gesture
            else "None",
        }
