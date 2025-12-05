"""
手势类型定义

定义所有支持的手势类型和手势数据结构。
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class GestureType(Enum):
    """手势类型枚举"""
    
    # 基础状态
    NONE = auto()           # 无手势/未检测到
    FIST = auto()           # 握拳 - 休息状态
    PALM = auto()           # 手掌张开
    
    # 指针模式
    POINTER = auto()        # 食指指向 - 移动鼠标
    
    # 点击相关
    CLICK = auto()          # 拇指+食指捏合 - 左键点击
    CLICK_HOLD = auto()     # 捏合保持 - 拖拽
    RIGHT_CLICK = auto()    # 拇指+中指捏合 - 右键点击
    DOUBLE_CLICK = auto()   # 快速双击
    
    # 滚动相关
    SCROLL = auto()         # 食指+中指 - 滚动模式
    SCROLL_UP = auto()      # 滚动模式+向上
    SCROLL_DOWN = auto()    # 滚动模式+向下
    
    # 控制相关
    PAUSE = auto()          # 五指张开 - 暂停控制


class ActionType(Enum):
    """动作类型枚举"""
    
    NONE = auto()
    MOVE_CURSOR = auto()
    LEFT_CLICK = auto()
    LEFT_DOUBLE_CLICK = auto()
    LEFT_HOLD = auto()
    LEFT_RELEASE = auto()
    RIGHT_CLICK = auto()
    MIDDLE_CLICK = auto()
    SCROLL_UP = auto()
    SCROLL_DOWN = auto()
    SCROLL_MODE = auto()
    TOGGLE_PAUSE = auto()


@dataclass
class Gesture:
    """手势数据"""
    
    type: GestureType
    # 手势置信度 (0-1)
    confidence: float = 1.0
    # 额外数据（如捏合距离、移动方向等）
    data: Optional[dict] = None
    # 持续帧数
    frames: int = 0
    
    def __eq__(self, other):
        if isinstance(other, Gesture):
            return self.type == other.type
        if isinstance(other, GestureType):
            return self.type == other
        return False
    
    def __hash__(self):
        return hash(self.type)


@dataclass
class GestureEvent:
    """手势事件"""
    
    gesture: Gesture
    action: ActionType
    # 事件类型：start, hold, end
    event_type: str
    # 相关坐标（归一化 0-1）
    position: Optional[tuple[float, float]] = None
    # 时间戳
    timestamp: float = 0.0


# 手势到动作的默认映射
DEFAULT_GESTURE_ACTIONS = {
    GestureType.POINTER: ActionType.MOVE_CURSOR,
    GestureType.CLICK: ActionType.LEFT_CLICK,
    GestureType.CLICK_HOLD: ActionType.LEFT_HOLD,
    GestureType.DOUBLE_CLICK: ActionType.LEFT_DOUBLE_CLICK,
    GestureType.RIGHT_CLICK: ActionType.RIGHT_CLICK,
    GestureType.SCROLL: ActionType.SCROLL_MODE,
    GestureType.SCROLL_UP: ActionType.SCROLL_UP,
    GestureType.SCROLL_DOWN: ActionType.SCROLL_DOWN,
    GestureType.PALM: ActionType.TOGGLE_PAUSE,
    GestureType.FIST: ActionType.NONE,
    GestureType.NONE: ActionType.NONE,
}
