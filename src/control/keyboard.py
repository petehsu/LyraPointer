"""
键盘控制器

使用 PyAutoGUI 控制键盘输入。
"""

from typing import Optional

import pyautogui


class KeyboardController:
    """键盘控制器"""
    
    def __init__(self):
        """初始化键盘控制器"""
        self._pressed_keys: set[str] = set()
    
    def press(self, key: str):
        """
        按下并释放按键
        
        Args:
            key: 按键名称
        """
        try:
            pyautogui.press(key)
        except Exception:
            pass
    
    def key_down(self, key: str):
        """
        按下按键（不释放）
        
        Args:
            key: 按键名称
        """
        try:
            pyautogui.keyDown(key)
            self._pressed_keys.add(key)
        except Exception:
            pass
    
    def key_up(self, key: str):
        """
        释放按键
        
        Args:
            key: 按键名称
        """
        try:
            pyautogui.keyUp(key)
            self._pressed_keys.discard(key)
        except Exception:
            pass
    
    def hotkey(self, *keys: str):
        """
        按下组合键
        
        Args:
            keys: 按键序列
        """
        try:
            pyautogui.hotkey(*keys)
        except Exception:
            pass
    
    def type_text(self, text: str, interval: float = 0.0):
        """
        输入文本
        
        Args:
            text: 要输入的文本
            interval: 按键间隔（秒）
        """
        try:
            pyautogui.typewrite(text, interval=interval)
        except Exception:
            pass
    
    def release_all(self):
        """释放所有按下的按键"""
        for key in list(self._pressed_keys):
            self.key_up(key)
    
    @property
    def pressed_keys(self) -> set[str]:
        """获取当前按下的按键"""
        return self._pressed_keys.copy()
