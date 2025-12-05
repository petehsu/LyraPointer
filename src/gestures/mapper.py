"""
手势映射器

将手势映射到系统操作。
"""

from typing import Callable, Optional

from .gestures import ActionType, Gesture, GestureType, DEFAULT_GESTURE_ACTIONS


class GestureMapper:
    """手势映射器"""
    
    def __init__(self):
        """初始化映射器"""
        self._mappings: dict[GestureType, ActionType] = DEFAULT_GESTURE_ACTIONS.copy()
        self._callbacks: dict[ActionType, list[Callable]] = {}
    
    def set_mapping(self, gesture: GestureType, action: ActionType):
        """
        设置手势映射
        
        Args:
            gesture: 手势类型
            action: 动作类型
        """
        self._mappings[gesture] = action
    
    def get_action(self, gesture: Gesture) -> ActionType:
        """
        获取手势对应的动作
        
        Args:
            gesture: 手势
            
        Returns:
            动作类型
        """
        return self._mappings.get(gesture.type, ActionType.NONE)
    
    def register_callback(
        self,
        action: ActionType,
        callback: Callable[[Gesture], None],
    ):
        """
        注册动作回调
        
        Args:
            action: 动作类型
            callback: 回调函数
        """
        if action not in self._callbacks:
            self._callbacks[action] = []
        self._callbacks[action].append(callback)
    
    def trigger_action(self, gesture: Gesture) -> ActionType:
        """
        触发动作
        
        Args:
            gesture: 手势
            
        Returns:
            触发的动作类型
        """
        action = self.get_action(gesture)
        
        if action in self._callbacks:
            for callback in self._callbacks[action]:
                callback(gesture)
        
        return action
    
    def reset_mappings(self):
        """重置为默认映射"""
        self._mappings = DEFAULT_GESTURE_ACTIONS.copy()
    
    def get_all_mappings(self) -> dict[GestureType, ActionType]:
        """获取所有映射"""
        return self._mappings.copy()
