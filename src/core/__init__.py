"""
核心模块

提供事件系统、状态机等核心功能。
"""

from .events import Event, EventBus, EventType
from .state_machine import ControlState, GestureStateMachine

__all__ = [
    "Event",
    "EventBus",
    "EventType",
    "ControlState",
    "GestureStateMachine",
]
