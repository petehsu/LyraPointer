"""
可视化窗口

显示摄像头画面、手部骨架和手势状态。
"""

import time
from typing import Optional

import cv2
import numpy as np

from ..gestures.gestures import Gesture, GestureType


class Visualizer:
    """可视化窗口"""
    
    WINDOW_NAME = "LyraPointer"
    
    # 颜色定义 (BGR)
    COLOR_GREEN = (0, 255, 0)
    COLOR_RED = (0, 0, 255)
    COLOR_BLUE = (255, 0, 0)
    COLOR_YELLOW = (0, 255, 255)
    COLOR_WHITE = (255, 255, 255)
    COLOR_GRAY = (128, 128, 128)
    COLOR_DARK = (40, 40, 40)
    
    def __init__(
        self,
        show_skeleton: bool = True,
        show_gesture_info: bool = True,
        show_control_zone: bool = True,
        show_fps: bool = True,
    ):
        """
        初始化可视化器
        
        Args:
            show_skeleton: 是否显示手部骨架
            show_gesture_info: 是否显示手势信息
            show_control_zone: 是否显示控制区域
            show_fps: 是否显示 FPS
        """
        self.show_skeleton = show_skeleton
        self.show_gesture_info = show_gesture_info
        self.show_control_zone = show_control_zone
        self.show_fps = show_fps
        
        self._window_created = False
        self._fps_counter = FPSCounter()
        self._is_paused = False
    
    def create_window(self):
        """创建窗口"""
        if not self._window_created:
            cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.WINDOW_NAME, 800, 600)
            self._window_created = True
    
    def destroy_window(self):
        """销毁窗口"""
        if self._window_created:
            cv2.destroyWindow(self.WINDOW_NAME)
            self._window_created = False
    
    def render(
        self,
        frame: np.ndarray,
        gesture: Optional[Gesture] = None,
        control_zone: Optional[tuple[int, int, int, int]] = None,
        cursor_pos: Optional[tuple[int, int]] = None,
    ) -> np.ndarray:
        """
        渲染可视化界面
        
        Args:
            frame: 摄像头画面
            gesture: 当前手势
            control_zone: 控制区域 (x1, y1, x2, y2)
            cursor_pos: 指针位置（在画面上的像素坐标）
            
        Returns:
            渲染后的画面
        """
        display = frame.copy()
        h, w = display.shape[:2]
        
        # 1. 绘制控制区域
        if self.show_control_zone and control_zone:
            x1, y1, x2, y2 = control_zone
            cv2.rectangle(display, (x1, y1), (x2, y2), self.COLOR_BLUE, 2)
            # 半透明遮罩
            overlay = display.copy()
            cv2.rectangle(overlay, (0, 0), (w, y1), self.COLOR_DARK, -1)  # 上
            cv2.rectangle(overlay, (0, y2), (w, h), self.COLOR_DARK, -1)  # 下
            cv2.rectangle(overlay, (0, y1), (x1, y2), self.COLOR_DARK, -1)  # 左
            cv2.rectangle(overlay, (x2, y1), (w, y2), self.COLOR_DARK, -1)  # 右
            cv2.addWeighted(overlay, 0.3, display, 0.7, 0, display)
        
        # 2. 绘制指针位置
        if cursor_pos:
            cx, cy = cursor_pos
            cv2.circle(display, (cx, cy), 15, self.COLOR_YELLOW, 3)
            cv2.circle(display, (cx, cy), 5, self.COLOR_RED, -1)
        
        # 3. 绘制手势信息
        if self.show_gesture_info:
            display = self._draw_gesture_info(display, gesture)
        
        # 4. 绘制 FPS
        if self.show_fps:
            fps = self._fps_counter.update()
            self._draw_text(
                display,
                f"FPS: {fps:.1f}",
                (10, 30),
                color=self.COLOR_GREEN,
            )
        
        # 5. 绘制设置按钮 (右上角)
        self._draw_settings_button(display)
        
        # 6. 绘制暂停状态
        if self._is_paused:
            self._draw_text(
                display,
                "PAUSED",
                (w // 2 - 60, h // 2),
                font_scale=1.5,
                color=self.COLOR_RED,
                thickness=3,
            )
        
        return display
    
    def _draw_settings_button(self, frame: np.ndarray):
        """绘制设置按钮"""
        h, w = frame.shape[:2]
        # 齿轮图标位置 (右上角)
        center = (w - 30, 30)
        radius = 15
        
        # 简单的齿轮形状
        cv2.circle(frame, center, radius, self.COLOR_GRAY, -1)
        cv2.circle(frame, center, radius - 5, self.COLOR_DARK, 2)
        cv2.putText(frame, "S", (center[0] - 6, center[1] + 6),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.COLOR_WHITE, 2)

    def check_click(self, x: int, y: int, frame_width: int) -> str:
        """
        检查点击位置
        
        Args:
            x: 点击 x 坐标
            y: 点击 y 坐标
            frame_width: 画面宽度
            
        Returns:
            点击的元素名称，如果没有则返回 None
        """
        # 检查设置按钮 (右上角 30,30 半径 20)
        btn_x, btn_y = frame_width - 30, 30
        dist = ((x - btn_x) ** 2 + (y - btn_y) ** 2) ** 0.5
        if dist < 20:
            return "settings"
        return None
    
    def set_mouse_callback(self, callback):
        """设置鼠标回调"""
        cv2.namedWindow(self.WINDOW_NAME)
        cv2.setMouseCallback(self.WINDOW_NAME, callback)

    def show(self, frame: np.ndarray) -> int:
        """
        显示画面
        
        Args:
            frame: 要显示的画面
            
        Returns:
            按键值 (无按键返回 -1)
        """
        if not self._window_created:
            self.create_window()
        
        cv2.imshow(self.WINDOW_NAME, frame)
        return cv2.waitKey(1) & 0xFF
    
    def set_paused(self, paused: bool):
        """设置暂停状态"""
        self._is_paused = paused
    
    def _draw_gesture_info(
        self,
        frame: np.ndarray,
        gesture: Optional[Gesture],
    ) -> np.ndarray:
        """绘制手势信息"""
        h, w = frame.shape[:2]
        
        # 信息面板背景
        panel_h = 80
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - panel_h), (w, h), self.COLOR_DARK, -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # 手势名称
        gesture_name = "No Hand Detected"
        gesture_color = self.COLOR_GRAY
        
        if gesture:
            gesture_name = self._get_gesture_display_name(gesture.type)
            gesture_color = self._get_gesture_color(gesture.type)
        
        self._draw_text(
            frame,
            gesture_name,
            (10, h - 45),
            font_scale=0.8,
            color=gesture_color,
            thickness=2,
        )
        
        # 手势图标
        if gesture:
            icon_x = w - 70
            icon_y = h - panel_h + 10
            frame = self._draw_gesture_icon(
                frame,
                gesture.type,
                (icon_x, icon_y),
                size=60,
            )
        
        return frame
    
    def _draw_gesture_icon(
        self,
        frame: np.ndarray,
        gesture_type: GestureType,
        position: tuple[int, int],
        size: int = 60,
    ) -> np.ndarray:
        """绘制手势图标"""
        x, y = position
        center = (x + size // 2, y + size // 2)
        
        # 简化的图标表示
        if gesture_type == GestureType.POINTER:
            # 指向图标
            pts = np.array([
                [center[0], center[1] - 20],
                [center[0] - 10, center[1] + 10],
                [center[0] + 10, center[1] + 10],
            ], np.int32)
            cv2.fillPoly(frame, [pts], self.COLOR_YELLOW)
            
        elif gesture_type in [GestureType.CLICK, GestureType.DOUBLE_CLICK]:
            # 点击图标（圆）
            cv2.circle(frame, center, 20, self.COLOR_GREEN, -1)
            cv2.circle(frame, center, 20, self.COLOR_WHITE, 2)
            
        elif gesture_type == GestureType.RIGHT_CLICK:
            # 右键图标
            cv2.circle(frame, center, 20, self.COLOR_BLUE, -1)
            cv2.circle(frame, center, 20, self.COLOR_WHITE, 2)
            cv2.putText(frame, "R", (center[0] - 8, center[1] + 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.COLOR_WHITE, 2)
            
        elif gesture_type in [GestureType.SCROLL, GestureType.SCROLL_UP, GestureType.SCROLL_DOWN]:
            # 滚动图标
            cv2.arrowedLine(frame, (center[0], center[1] + 15),
                           (center[0], center[1] - 15), self.COLOR_YELLOW, 3)
            
        elif gesture_type == GestureType.PALM:
            # 手掌图标
            cv2.circle(frame, center, 25, self.COLOR_GREEN, 3)
            for i in range(5):
                angle = -90 + i * 36
                rad = angle * 3.14159 / 180
                ex = int(center[0] + 20 * np.cos(rad))
                ey = int(center[1] + 20 * np.sin(rad))
                cv2.circle(frame, (ex, ey), 5, self.COLOR_GREEN, -1)
            
        elif gesture_type == GestureType.FIST:
            # 握拳图标
            cv2.circle(frame, center, 20, self.COLOR_GRAY, -1)
            
        return frame
    
    def _get_gesture_display_name(self, gesture_type: GestureType) -> str:
        """获取手势显示名称"""
        names = {
            GestureType.NONE: "No Gesture",
            GestureType.POINTER: "Pointer Mode",
            GestureType.CLICK: "Click",
            GestureType.DOUBLE_CLICK: "Double Click",
            GestureType.CLICK_HOLD: "Dragging",
            GestureType.RIGHT_CLICK: "Right Click",
            GestureType.SCROLL: "Scroll Mode",
            GestureType.SCROLL_UP: "Scrolling Up",
            GestureType.SCROLL_DOWN: "Scrolling Down",
            GestureType.PALM: "Pause Control",
            GestureType.FIST: "Rest",
        }
        return names.get(gesture_type, "Unknown")
    
    def _get_gesture_color(self, gesture_type: GestureType) -> tuple:
        """获取手势对应的颜色"""
        colors = {
            GestureType.POINTER: self.COLOR_YELLOW,
            GestureType.CLICK: self.COLOR_GREEN,
            GestureType.DOUBLE_CLICK: self.COLOR_GREEN,
            GestureType.CLICK_HOLD: self.COLOR_GREEN,
            GestureType.RIGHT_CLICK: self.COLOR_BLUE,
            GestureType.SCROLL: self.COLOR_YELLOW,
            GestureType.SCROLL_UP: self.COLOR_YELLOW,
            GestureType.SCROLL_DOWN: self.COLOR_YELLOW,
            GestureType.PALM: self.COLOR_RED,
            GestureType.FIST: self.COLOR_GRAY,
        }
        return colors.get(gesture_type, self.COLOR_WHITE)
    
    def _draw_text(
        self,
        frame: np.ndarray,
        text: str,
        position: tuple[int, int],
        font_scale: float = 0.7,
        color: tuple = (255, 255, 255),
        thickness: int = 2,
    ):
        """绘制文字"""
        cv2.putText(
            frame,
            text,
            position,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA,
        )


class FPSCounter:
    """FPS 计数器"""
    
    def __init__(self, avg_frames: int = 30):
        """
        初始化 FPS 计数器
        
        Args:
            avg_frames: 平均帧数
        """
        self._times: list[float] = []
        self._avg_frames = avg_frames
    
    def update(self) -> float:
        """
        更新并返回 FPS
        
        Returns:
            当前 FPS
        """
        now = time.time()
        self._times.append(now)
        
        # 保留最近的帧时间
        while len(self._times) > self._avg_frames:
            self._times.pop(0)
        
        if len(self._times) < 2:
            return 0.0
        
        elapsed = self._times[-1] - self._times[0]
        if elapsed <= 0:
            return 0.0
        
        return (len(self._times) - 1) / elapsed
