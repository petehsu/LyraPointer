"""
鼠标控制器

使用 PyAutoGUI 控制鼠标移动、点击、滚动等操作。
"""

import time
from typing import Optional

import pyautogui

# 禁用 PyAutoGUI 的故障保护（移到屏幕角落不会停止）
# 注意：这可能导致难以手动停止程序，请确保有其他退出方式
pyautogui.FAILSAFE = False

# 禁用 PyAutoGUI 的暂停（提高响应速度）
pyautogui.PAUSE = 0


class MouseController:
    """鼠标控制器"""
    
    def __init__(self, move_duration: float = 0.0):
        """
        初始化鼠标控制器
        
        Args:
            move_duration: 移动动画时长（秒），0 表示即时移动
        """
        self.move_duration = move_duration
        
        # 状态追踪
        self._is_dragging = False
        self._last_position: Optional[tuple[int, int]] = None
        self._last_click_time: float = 0
    
    def move_to(self, x: int, y: int, duration: Optional[float] = None):
        """
        移动鼠标到指定位置
        
        Args:
            x: x 坐标
            y: y 坐标
            duration: 移动时长
        """
        if duration is None:
            duration = self.move_duration
        
        try:
            pyautogui.moveTo(x, y, duration=duration)
            self._last_position = (x, y)
        except pyautogui.FailSafeException:
            pass
    
    def move_relative(self, dx: int, dy: int, duration: Optional[float] = None):
        """
        相对移动鼠标
        
        Args:
            dx: x 方向偏移
            dy: y 方向偏移
            duration: 移动时长
        """
        if duration is None:
            duration = self.move_duration
        
        try:
            pyautogui.moveRel(dx, dy, duration=duration)
            pos = pyautogui.position()
            self._last_position = (pos.x, pos.y)
        except pyautogui.FailSafeException:
            pass
    
    def click(self, button: str = "left", clicks: int = 1):
        """
        点击鼠标
        
        Args:
            button: 按钮 ("left", "right", "middle")
            clicks: 点击次数
        """
        try:
            pyautogui.click(button=button, clicks=clicks)
            self._last_click_time = time.time()
        except pyautogui.FailSafeException:
            pass
    
    def double_click(self, button: str = "left"):
        """
        双击鼠标
        
        Args:
            button: 按钮
        """
        self.click(button=button, clicks=2)
    
    def right_click(self):
        """右键点击"""
        self.click(button="right")
    
    def middle_click(self):
        """中键点击"""
        self.click(button="middle")
    
    def mouse_down(self, button: str = "left"):
        """
        按下鼠标按钮
        
        Args:
            button: 按钮
        """
        try:
            pyautogui.mouseDown(button=button)
            if button == "left":
                self._is_dragging = True
        except pyautogui.FailSafeException:
            pass
    
    def mouse_up(self, button: str = "left"):
        """
        释放鼠标按钮
        
        Args:
            button: 按钮
        """
        try:
            pyautogui.mouseUp(button=button)
            if button == "left":
                self._is_dragging = False
        except pyautogui.FailSafeException:
            pass
    
    def drag_to(self, x: int, y: int, duration: float = 0.1):
        """
        拖拽到指定位置
        
        Args:
            x: 目标 x 坐标
            y: 目标 y 坐标
            duration: 拖拽时长
        """
        try:
            pyautogui.moveTo(x, y, duration=duration)
            self._last_position = (x, y)
        except pyautogui.FailSafeException:
            pass
    
    def scroll(self, amount: int, horizontal: bool = False):
        """
        滚动
        
        Args:
            amount: 滚动量（正数向上/右，负数向下/左）
            horizontal: 是否水平滚动
        """
        try:
            if horizontal:
                pyautogui.hscroll(amount)
            else:
                pyautogui.scroll(amount)
        except pyautogui.FailSafeException:
            pass
    
    def scroll_up(self, amount: int = 3):
        """向上滚动"""
        self.scroll(amount)
    
    def scroll_down(self, amount: int = 3):
        """向下滚动"""
        self.scroll(-amount)
    
    @property
    def position(self) -> tuple[int, int]:
        """获取当前鼠标位置"""
        pos = pyautogui.position()
        return pos.x, pos.y
    
    @property
    def is_dragging(self) -> bool:
        """是否正在拖拽"""
        return self._is_dragging
    
    def stop_drag(self):
        """停止拖拽"""
        if self._is_dragging:
            self.mouse_up()
