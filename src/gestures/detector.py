"""
手势检测器

根据手部关键点判断当前手势类型。
"""

import math
import time
from typing import Optional

from ..tracker.hand_tracker import HandLandmarks, Point3D
from .gestures import Gesture, GestureType


class GestureDetector:
    """手势检测器"""
    
    def __init__(
        self,
        pinch_threshold: float = 0.05,
        click_hold_frames: int = 3,
        double_click_interval: float = 0.3,
        pause_hold_frames: int = 10,
    ):
        """
        初始化手势检测器
        
        Args:
            pinch_threshold: 捏合判定阈值（归一化距离）
            click_hold_frames: 点击需要保持的帧数
            double_click_interval: 双击间隔（秒）
            pause_hold_frames: 暂停手势需要保持的帧数
        """
        self.pinch_threshold = pinch_threshold
        self.click_hold_frames = click_hold_frames
        self.double_click_interval = double_click_interval
        self.pause_hold_frames = pause_hold_frames
        
        # 状态追踪
        self._last_gesture: Optional[Gesture] = None
        self._gesture_frames: int = 0
        self._last_click_time: float = 0
        self._click_count: int = 0
        self._was_pinching: bool = False
        self._scroll_start_y: Optional[float] = None
    
    def detect(self, hand: HandLandmarks) -> Gesture:
        """
        检测当前手势
        
        Args:
            hand: 手部关键点数据
            
        Returns:
            检测到的手势
        """
        # 获取手指状态
        fingers_extended = self._get_fingers_extended(hand)
        
        # 检测捏合
        thumb_index_pinch = self._get_pinch_distance(hand, "thumb", "index")
        thumb_middle_pinch = self._get_pinch_distance(hand, "thumb", "middle")
        
        is_thumb_index_pinching = thumb_index_pinch < self.pinch_threshold
        is_thumb_middle_pinching = thumb_middle_pinch < self.pinch_threshold
        
        gesture_type = GestureType.NONE
        data = {}
        
        # ===== 手势判断逻辑 =====
        
        # 1. 五指张开 = 暂停
        if all(fingers_extended.values()):
            gesture_type = GestureType.PALM
            
        # 2. 握拳 = 休息
        elif not any([
            fingers_extended["index"],
            fingers_extended["middle"],
            fingers_extended["ring"],
            fingers_extended["pinky"],
        ]):
            gesture_type = GestureType.FIST
            
        # 3. 拇指+食指捏合 = 点击
        elif is_thumb_index_pinching:
            gesture_type = GestureType.CLICK
            data["pinch_distance"] = thumb_index_pinch
            
        # 4. 拇指+中指捏合 = 右键
        elif is_thumb_middle_pinching:
            gesture_type = GestureType.RIGHT_CLICK
            data["pinch_distance"] = thumb_middle_pinch
            
        # 5. 食指+中指伸出 = 滚动模式
        elif (
            fingers_extended["index"]
            and fingers_extended["middle"]
            and not fingers_extended["ring"]
            and not fingers_extended["pinky"]
        ):
            gesture_type = GestureType.SCROLL
            # 检测滚动方向
            index_tip = hand.get_finger_tip("index")
            if self._scroll_start_y is None:
                self._scroll_start_y = index_tip.y
            else:
                delta_y = index_tip.y - self._scroll_start_y
                if delta_y > 0.05:
                    gesture_type = GestureType.SCROLL_DOWN
                    self._scroll_start_y = index_tip.y
                elif delta_y < -0.05:
                    gesture_type = GestureType.SCROLL_UP
                    self._scroll_start_y = index_tip.y
            data["scroll_y"] = index_tip.y
            
        # 6. 只有食指伸出 = 指针模式
        elif (
            fingers_extended["index"]
            and not fingers_extended["middle"]
            and not fingers_extended["ring"]
            and not fingers_extended["pinky"]
        ):
            gesture_type = GestureType.POINTER
            index_tip = hand.get_finger_tip("index")
            data["pointer_position"] = (index_tip.x, index_tip.y)
        
        # 如果不是滚动模式，重置滚动起始点
        if gesture_type not in [GestureType.SCROLL, GestureType.SCROLL_UP, GestureType.SCROLL_DOWN]:
            self._scroll_start_y = None
        
        # ===== 帧计数和状态管理 =====
        
        gesture = Gesture(type=gesture_type, data=data)
        
        if self._last_gesture and self._last_gesture.type == gesture_type:
            self._gesture_frames += 1
        else:
            self._gesture_frames = 1
        
        gesture.frames = self._gesture_frames
        
        # ===== 双击检测 =====
        
        current_time = time.time()
        
        if gesture_type == GestureType.CLICK and not self._was_pinching:
            if current_time - self._last_click_time < self.double_click_interval:
                self._click_count += 1
                if self._click_count >= 2:
                    gesture = Gesture(type=GestureType.DOUBLE_CLICK, data=data)
                    self._click_count = 0
            else:
                self._click_count = 1
            self._last_click_time = current_time
        
        # ===== 点击保持检测（拖拽） =====
        
        if gesture_type == GestureType.CLICK:
            if self._gesture_frames > self.click_hold_frames:
                gesture = Gesture(
                    type=GestureType.CLICK_HOLD,
                    data=data,
                    frames=self._gesture_frames,
                )
        
        self._was_pinching = is_thumb_index_pinching
        self._last_gesture = gesture
        
        return gesture
    
    def _get_fingers_extended(self, hand: HandLandmarks) -> dict[str, bool]:
        """
        判断各手指是否伸出
        
        Args:
            hand: 手部关键点数据
            
        Returns:
            各手指的伸出状态
        """
        result = {}
        
        # 拇指 - 使用 x 坐标判断（相对于手掌）
        thumb_tip = hand.get_finger_tip("thumb")
        thumb_mcp = hand.get_finger_mcp("thumb")
        # 根据手的类型调整判断方向
        if hand.handedness == "Right":
            result["thumb"] = thumb_tip.x < thumb_mcp.x
        else:
            result["thumb"] = thumb_tip.x > thumb_mcp.x
        
        # 其他手指 - 使用 y 坐标判断（指尖在关节上方）
        for finger in ["index", "middle", "ring", "pinky"]:
            tip = hand.get_finger_tip(finger)
            pip = hand.get_finger_pip(finger)
            mcp = hand.get_finger_mcp(finger)
            
            # 指尖 y 值小于 PIP 和 MCP（在屏幕上方 = 手指伸出）
            result[finger] = tip.y < pip.y and tip.y < mcp.y
        
        return result
    
    def _get_pinch_distance(
        self,
        hand: HandLandmarks,
        finger1: str,
        finger2: str,
    ) -> float:
        """
        计算两指尖之间的距离
        
        Args:
            hand: 手部关键点数据
            finger1: 第一个手指名称
            finger2: 第二个手指名称
            
        Returns:
            归一化的距离 (0-1)
        """
        tip1 = hand.get_finger_tip(finger1)
        tip2 = hand.get_finger_tip(finger2)
        
        distance = math.sqrt(
            (tip1.x - tip2.x) ** 2 +
            (tip1.y - tip2.y) ** 2 +
            (tip1.z - tip2.z) ** 2
        )
        
        return distance
    
    def reset(self):
        """重置检测器状态"""
        self._last_gesture = None
        self._gesture_frames = 0
        self._last_click_time = 0
        self._click_count = 0
        self._was_pinching = False
        self._scroll_start_y = None
