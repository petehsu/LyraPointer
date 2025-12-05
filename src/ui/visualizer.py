"""
LyraPointer 可视化窗口

显示摄像头画面、手部骨架和手势状态。
现代化 UI 设计版本 - 简洁、优雅、高效。
"""

import math
import time
from typing import Optional, Tuple

import cv2
import numpy as np

from ..gestures.gestures import Gesture, GestureType
from ..utils.i18n import get_i18n, t


class Visualizer:
    """可视化窗口 - 现代化 UI"""

    WINDOW_NAME = "LyraPointer"

    # 现代配色方案 (BGR) - 低饱和度、高级感
    COLORS = {
        # 主色调 - 靛蓝色系
        "primary": (240, 130, 90),  # #5A82F0 靛蓝
        "primary_light": (255, 170, 130),  # #82AAF0
        "primary_dark": (200, 100, 70),  # #4664C8
        "primary_glow": (255, 180, 140),  # 发光效果
        # 强调色
        "accent": (180, 100, 255),  # #FF64B4 品红
        "accent_soft": (200, 140, 255),  # 柔和版本
        # 功能色 - 柔和版本
        "success": (160, 210, 120),  # #78D2A0 薄荷绿
        "warning": (120, 200, 250),  # #FAC878 琥珀色
        "danger": (120, 120, 230),  # #E67878 珊瑚红
        "info": (220, 180, 140),  # #8CB4DC 天蓝
        # 中性色 - 深色主题
        "bg_dark": (30, 28, 26),  # #1A1C1E 最深背景
        "bg_medium": (42, 40, 38),  # #26282A 中等背景
        "bg_light": (55, 52, 48),  # #30343B 浅背景
        "bg_hover": (70, 65, 60),  # 悬停背景
        # 文字色
        "text_primary": (255, 255, 255),  # 主要文字
        "text_secondary": (180, 180, 185),  # #B9B4B4 次要文字
        "text_muted": (120, 118, 115),  # #737678 静音文字
        # 边框和分割线
        "border": (70, 65, 60),  # #3C4146
        "border_light": (90, 85, 80),  # #505A5A
        "divider": (50, 48, 45),  # #2D3032
        # 特殊效果
        "glass": (50, 48, 45),  # 玻璃效果背景
        "shadow": (15, 14, 13),  # 阴影色
        "glow": (255, 200, 150),  # 发光色
    }

    # 手势颜色映射 - 更柔和的颜色
    GESTURE_COLORS = {
        GestureType.POINTER: "warning",
        GestureType.CLICK: "success",
        GestureType.DOUBLE_CLICK: "success",
        GestureType.CLICK_HOLD: "primary",
        GestureType.RIGHT_CLICK: "info",
        GestureType.SCROLL: "accent_soft",
        GestureType.SCROLL_UP: "accent_soft",
        GestureType.SCROLL_DOWN: "accent_soft",
        GestureType.PALM: "danger",
        GestureType.FIST: "text_muted",
        GestureType.NONE: "text_muted",
    }

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

        # 缓存（性能优化）
        self._overlay_cache = {}
        self._last_frame_size = (0, 0)

        # 设置按钮区域
        self._settings_btn_rect: Optional[Tuple[int, int, int, int]] = None

        # i18n
        self._i18n = get_i18n()

        # 动画状态
        self._pulse_phase = 0.0

        # 教程模式
        self._show_tutorial = True  # 首次启动显示教程
        self._tutorial_step = 0
        self._help_btn_rect: Optional[Tuple[int, int, int, int]] = None

    def create_window(self):
        """创建窗口"""
        if not self._window_created:
            # 使用 WINDOW_GUI_NORMAL 禁用 Qt 工具栏
            flags = cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL
            cv2.namedWindow(self.WINDOW_NAME, flags)
            cv2.resizeWindow(self.WINDOW_NAME, 960, 720)
            self._window_created = True

    def destroy_window(self):
        """销毁窗口"""
        if self._window_created:
            try:
                cv2.destroyWindow(self.WINDOW_NAME)
            except Exception:
                pass
            self._window_created = False
            self._overlay_cache.clear()

    def render(
        self,
        frame: np.ndarray,
        gesture: Optional[Gesture] = None,
        control_zone: Optional[Tuple[int, int, int, int]] = None,
        cursor_pos: Optional[Tuple[int, int]] = None,
    ) -> np.ndarray:
        """
        渲染可视化界面

        Args:
            frame: 摄像头画面
            gesture: 当前手势
            control_zone: 控制区域 (x1, y1, x2, y2)
            cursor_pos: 指针位置

        Returns:
            渲染后的画面
        """
        display = frame.copy()
        h, w = display.shape[:2]

        # 检查尺寸变化
        if (h, w) != self._last_frame_size:
            self._overlay_cache.clear()
            self._last_frame_size = (h, w)

        # 更新动画
        self._pulse_phase = (self._pulse_phase + 0.1) % (2 * math.pi)

        # 1. 控制区域
        if self.show_control_zone and control_zone:
            display = self._draw_control_zone(display, control_zone)

        # 2. 光标
        if cursor_pos:
            self._draw_cursor(display, cursor_pos, gesture)

        # 3. 顶部状态栏
        display = self._draw_status_bar(display, gesture)

        # 4. 底部信息面板
        if self.show_gesture_info:
            display = self._draw_info_panel(display, gesture)

        # 5. 暂停覆盖
        if self._is_paused:
            display = self._draw_pause_overlay(display)

        # 6. 新手教程覆盖
        if self._show_tutorial:
            display = self._draw_tutorial_overlay(display)

        return display

    def _draw_rounded_rect(
        self,
        frame: np.ndarray,
        pt1: Tuple[int, int],
        pt2: Tuple[int, int],
        color: Tuple[int, int, int],
        radius: int = 10,
        thickness: int = -1,
    ):
        """绘制圆角矩形"""
        x1, y1 = pt1
        x2, y2 = pt2

        # 限制半径
        radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)

        if thickness == -1:
            # 填充
            # 中间矩形
            cv2.rectangle(frame, (x1 + radius, y1), (x2 - radius, y2), color, -1)
            cv2.rectangle(frame, (x1, y1 + radius), (x2, y2 - radius), color, -1)
            # 四个角
            cv2.circle(
                frame, (x1 + radius, y1 + radius), radius, color, -1, cv2.LINE_AA
            )
            cv2.circle(
                frame, (x2 - radius, y1 + radius), radius, color, -1, cv2.LINE_AA
            )
            cv2.circle(
                frame, (x1 + radius, y2 - radius), radius, color, -1, cv2.LINE_AA
            )
            cv2.circle(
                frame, (x2 - radius, y2 - radius), radius, color, -1, cv2.LINE_AA
            )
        else:
            # 边框
            cv2.line(
                frame,
                (x1 + radius, y1),
                (x2 - radius, y1),
                color,
                thickness,
                cv2.LINE_AA,
            )
            cv2.line(
                frame,
                (x1 + radius, y2),
                (x2 - radius, y2),
                color,
                thickness,
                cv2.LINE_AA,
            )
            cv2.line(
                frame,
                (x1, y1 + radius),
                (x1, y2 - radius),
                color,
                thickness,
                cv2.LINE_AA,
            )
            cv2.line(
                frame,
                (x2, y1 + radius),
                (x2, y2 - radius),
                color,
                thickness,
                cv2.LINE_AA,
            )
            cv2.ellipse(
                frame,
                (x1 + radius, y1 + radius),
                (radius, radius),
                180,
                0,
                90,
                color,
                thickness,
                cv2.LINE_AA,
            )
            cv2.ellipse(
                frame,
                (x2 - radius, y1 + radius),
                (radius, radius),
                270,
                0,
                90,
                color,
                thickness,
                cv2.LINE_AA,
            )
            cv2.ellipse(
                frame,
                (x1 + radius, y2 - radius),
                (radius, radius),
                90,
                0,
                90,
                color,
                thickness,
                cv2.LINE_AA,
            )
            cv2.ellipse(
                frame,
                (x2 - radius, y2 - radius),
                (radius, radius),
                0,
                0,
                90,
                color,
                thickness,
                cv2.LINE_AA,
            )

    def _draw_glass_panel(
        self,
        frame: np.ndarray,
        pt1: Tuple[int, int],
        pt2: Tuple[int, int],
        alpha: float = 0.75,
        radius: int = 12,
    ) -> np.ndarray:
        """绘制毛玻璃效果面板"""
        x1, y1 = pt1
        x2, y2 = pt2

        # 创建遮罩
        overlay = frame.copy()
        self._draw_rounded_rect(overlay, pt1, pt2, self.COLORS["bg_dark"], radius)

        # 混合
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # 边框高光（顶部）
        cv2.line(
            frame,
            (x1 + radius, y1 + 1),
            (x2 - radius, y1 + 1),
            self.COLORS["border_light"],
            1,
            cv2.LINE_AA,
        )

        return frame

    def _draw_control_zone(
        self,
        frame: np.ndarray,
        control_zone: Tuple[int, int, int, int],
    ) -> np.ndarray:
        """绘制控制区域"""
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = control_zone

        # 缓存遮罩
        cache_key = f"zone_{w}_{h}_{x1}_{y1}_{x2}_{y2}"
        if cache_key not in self._overlay_cache:
            mask = np.zeros((h, w), dtype=np.uint8)
            mask[:y1, :] = 1
            mask[y2:, :] = 1
            mask[y1:y2, :x1] = 1
            mask[y1:y2, x2:] = 1
            self._overlay_cache[cache_key] = mask

        mask = self._overlay_cache[cache_key]

        # 暗化区域外
        frame[mask == 1] = (
            frame[mask == 1] * 0.3 + np.array(self.COLORS["bg_dark"]) * 0.7
        ).astype(np.uint8)

        # 发光边框
        glow_intensity = 0.5 + 0.2 * math.sin(self._pulse_phase)
        glow_color = tuple(
            int(c * glow_intensity) for c in self.COLORS["primary_light"]
        )

        # 外层光晕
        cv2.rectangle(
            frame,
            (x1 - 2, y1 - 2),
            (x2 + 2, y2 + 2),
            self.COLORS["primary_dark"],
            2,
            cv2.LINE_AA,
        )
        # 主边框
        cv2.rectangle(frame, (x1, y1), (x2, y2), glow_color, 2, cv2.LINE_AA)

        # 角落装饰 - 更精致
        corner_len = 25
        corner_color = self.COLORS["primary"]
        thickness = 2

        corners = [
            ((x1, y1), (1, 1)),  # 左上
            ((x2, y1), (-1, 1)),  # 右上
            ((x1, y2), (1, -1)),  # 左下
            ((x2, y2), (-1, -1)),  # 右下
        ]

        for (cx, cy), (dx, dy) in corners:
            # L形角落
            cv2.line(
                frame,
                (cx, cy),
                (cx + corner_len * dx, cy),
                corner_color,
                thickness,
                cv2.LINE_AA,
            )
            cv2.line(
                frame,
                (cx, cy),
                (cx, cy + corner_len * dy),
                corner_color,
                thickness,
                cv2.LINE_AA,
            )
            # 角点圆
            cv2.circle(
                frame, (cx, cy), 4, self.COLORS["primary_light"], -1, cv2.LINE_AA
            )

        return frame

    def _draw_cursor(
        self,
        frame: np.ndarray,
        pos: Tuple[int, int],
        gesture: Optional[Gesture] = None,
    ):
        """绘制现代光标"""
        cx, cy = pos

        # 根据手势选择颜色
        if gesture:
            color_key = self.GESTURE_COLORS.get(gesture.type, "warning")
            color = self.COLORS[color_key]
        else:
            color = self.COLORS["warning"]

        # 动态大小
        pulse = 1.0 + 0.1 * math.sin(self._pulse_phase * 2)

        # 外圈（发光）
        outer_radius = int(22 * pulse)
        cv2.circle(frame, (cx, cy), outer_radius, self.COLORS["shadow"], 3, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), outer_radius, color, 2, cv2.LINE_AA)

        # 中圈
        cv2.circle(frame, (cx, cy), 12, self.COLORS["text_primary"], 2, cv2.LINE_AA)

        # 内圈
        cv2.circle(frame, (cx, cy), 5, color, -1, cv2.LINE_AA)

        # 十字准心
        cross_size = 6
        cv2.line(
            frame,
            (cx - cross_size, cy),
            (cx + cross_size, cy),
            self.COLORS["text_primary"],
            1,
            cv2.LINE_AA,
        )
        cv2.line(
            frame,
            (cx, cy - cross_size),
            (cx, cy + cross_size),
            self.COLORS["text_primary"],
            1,
            cv2.LINE_AA,
        )

    def _draw_status_bar(
        self, frame: np.ndarray, gesture: Optional[Gesture]
    ) -> np.ndarray:
        """绘制顶部状态栏"""
        h, w = frame.shape[:2]
        bar_height = 48

        # 毛玻璃背景
        frame = self._draw_glass_panel(
            frame, (0, 0), (w, bar_height), alpha=0.85, radius=0
        )

        # 底部边线 - 渐变效果
        cv2.line(
            frame, (0, bar_height - 1), (w, bar_height - 1), self.COLORS["divider"], 1
        )

        # Logo / 应用名
        self._draw_text(
            frame,
            "LyraPointer",
            (16, 32),
            font_scale=0.6,
            color=self.COLORS["text_primary"],
            thickness=2,
        )

        # FPS 显示
        if self.show_fps:
            fps = self._fps_counter.update()
            fps_color = (
                self.COLORS["success"]
                if fps >= 25
                else self.COLORS["warning"]
                if fps >= 15
                else self.COLORS["danger"]
            )

            # FPS 标签
            fps_x = 140
            self._draw_text(
                frame,
                "FPS",
                (fps_x, 20),
                font_scale=0.35,
                color=self.COLORS["text_muted"],
            )
            self._draw_text(
                frame,
                f"{fps:.0f}",
                (fps_x, 36),
                font_scale=0.55,
                color=fps_color,
                thickness=2,
            )

        # 帮助按钮
        self._help_btn_rect = self._draw_help_button(frame, w)

        # 设置按钮
        self._settings_btn_rect = self._draw_settings_button(frame, w)

        # 状态指示器
        status_x = w - 160
        status_text = t("status.paused") if self._is_paused else t("status.running")
        status_color = (
            self.COLORS["danger"] if self._is_paused else self.COLORS["success"]
        )

        # 状态点（带发光）
        if not self._is_paused:
            glow = int(6 + 2 * math.sin(self._pulse_phase * 2))
            cv2.circle(
                frame, (status_x, 24), glow, (*status_color[:3],), -1, cv2.LINE_AA
            )
        cv2.circle(frame, (status_x, 24), 5, status_color, -1, cv2.LINE_AA)
        cv2.circle(
            frame, (status_x, 24), 5, self.COLORS["text_primary"], 1, cv2.LINE_AA
        )

        self._draw_text(
            frame, status_text, (status_x + 14, 30), font_scale=0.45, color=status_color
        )

        return frame

    def _draw_settings_button(
        self, frame: np.ndarray, frame_width: int
    ) -> Tuple[int, int, int, int]:
        """绘制设置按钮"""
        btn_size = 32
        btn_x = frame_width - btn_size - 12
        btn_y = 8
        center_x = btn_x + btn_size // 2
        center_y = btn_y + btn_size // 2

        # 按钮背景
        self._draw_rounded_rect(
            frame,
            (btn_x, btn_y),
            (btn_x + btn_size, btn_y + btn_size),
            self.COLORS["bg_light"],
            radius=8,
        )

        # 边框
        self._draw_rounded_rect(
            frame,
            (btn_x, btn_y),
            (btn_x + btn_size, btn_y + btn_size),
            self.COLORS["border"],
            radius=8,
            thickness=1,
        )

        # 齿轮图标
        gear_color = self.COLORS["text_secondary"]

        # 外圈
        cv2.circle(frame, (center_x, center_y), 9, gear_color, 2, cv2.LINE_AA)
        # 内圈
        cv2.circle(frame, (center_x, center_y), 4, gear_color, -1, cv2.LINE_AA)

        # 齿轮齿
        for i in range(6):
            angle = i * math.pi / 3
            x1 = int(center_x + 7 * math.cos(angle))
            y1 = int(center_y + 7 * math.sin(angle))
            x2 = int(center_x + 11 * math.cos(angle))
            y2 = int(center_y + 11 * math.sin(angle))
            cv2.line(frame, (x1, y1), (x2, y2), gear_color, 3, cv2.LINE_AA)

        return (btn_x, btn_y, btn_x + btn_size, btn_y + btn_size)

    def _draw_help_button(
        self, frame: np.ndarray, frame_width: int
    ) -> Tuple[int, int, int, int]:
        """绘制帮助按钮"""
        btn_size = 32
        btn_x = frame_width - btn_size * 2 - 20  # 在设置按钮左边
        btn_y = 8
        center_x = btn_x + btn_size // 2
        center_y = btn_y + btn_size // 2

        # 按钮背景
        self._draw_rounded_rect(
            frame,
            (btn_x, btn_y),
            (btn_x + btn_size, btn_y + btn_size),
            self.COLORS["bg_light"],
            radius=8,
        )

        # 边框
        self._draw_rounded_rect(
            frame,
            (btn_x, btn_y),
            (btn_x + btn_size, btn_y + btn_size),
            self.COLORS["border"],
            radius=8,
            thickness=1,
        )

        # 问号图标
        self._draw_text(
            frame,
            "?",
            (center_x - 5, center_y + 6),
            font_scale=0.7,
            color=self.COLORS["text_secondary"],
            thickness=2,
        )

        return (btn_x, btn_y, btn_x + btn_size, btn_y + btn_size)

    def _draw_info_panel(
        self, frame: np.ndarray, gesture: Optional[Gesture]
    ) -> np.ndarray:
        """绘制底部信息面板"""
        h, w = frame.shape[:2]
        panel_height = 80
        panel_y = h - panel_height

        # 毛玻璃背景
        frame = self._draw_glass_panel(
            frame, (0, panel_y), (w, h), alpha=0.85, radius=0
        )

        # 顶部边线
        cv2.line(frame, (0, panel_y), (w, panel_y), self.COLORS["divider"], 1)

        # 手势信息
        gesture_name = t("gesture.no_hand")
        gesture_color = self.COLORS["text_muted"]

        if gesture:
            gesture_name = self._get_gesture_text(gesture.type)
            color_key = self.GESTURE_COLORS.get(gesture.type, "text_muted")
            gesture_color = self.COLORS[color_key]

        # 手势图标
        icon_x = 24
        icon_y = panel_y + 20
        self._draw_gesture_icon(frame, gesture, (icon_x, icon_y), size=40)

        # 手势名称
        self._draw_text(
            frame,
            gesture_name,
            (icon_x + 55, panel_y + 48),
            font_scale=0.7,
            color=gesture_color,
            thickness=2,
        )

        # 快捷键提示
        hints = [("Q", "Quit"), ("P", "Pause"), ("V", "Toggle")]
        hint_x = w - 24

        for key, desc in reversed(hints):
            # 计算位置
            hint_x -= 70

            # 按键背景
            self._draw_rounded_rect(
                frame,
                (hint_x, panel_y + 25),
                (hint_x + 24, panel_y + 47),
                self.COLORS["bg_light"],
                radius=4,
            )

            # 按键文字
            self._draw_text(
                frame,
                key,
                (hint_x + 7, panel_y + 42),
                font_scale=0.45,
                color=self.COLORS["text_primary"],
            )

            # 描述
            self._draw_text(
                frame,
                desc,
                (hint_x + 28, panel_y + 42),
                font_scale=0.35,
                color=self.COLORS["text_muted"],
            )

        return frame

    def _draw_gesture_icon(
        self,
        frame: np.ndarray,
        gesture: Optional[Gesture],
        position: Tuple[int, int],
        size: int = 40,
    ):
        """绘制手势图标"""
        x, y = position
        center_x = x + size // 2
        center_y = y + size // 2

        # 图标背景
        self._draw_rounded_rect(
            frame,
            (x, y),
            (x + size, y + size),
            self.COLORS["bg_medium"],
            radius=10,
        )

        if gesture is None:
            # 空状态 - 问号
            cv2.circle(
                frame,
                (center_x, center_y),
                size // 3,
                self.COLORS["text_muted"],
                2,
                cv2.LINE_AA,
            )
            self._draw_text(
                frame,
                "?",
                (center_x - 5, center_y + 6),
                font_scale=0.6,
                color=self.COLORS["text_muted"],
            )
            return

        color_key = self.GESTURE_COLORS.get(gesture.type, "text_muted")
        color = self.COLORS[color_key]

        if gesture.type == GestureType.POINTER:
            # 指针 - 箭头
            pts = np.array(
                [
                    [center_x, center_y - 12],
                    [center_x - 8, center_y + 8],
                    [center_x, center_y + 2],
                    [center_x + 8, center_y + 8],
                ],
                np.int32,
            )
            cv2.fillPoly(frame, [pts], color, cv2.LINE_AA)

        elif gesture.type in [GestureType.CLICK, GestureType.DOUBLE_CLICK]:
            # 点击 - 圆
            cv2.circle(frame, (center_x, center_y), 10, color, -1, cv2.LINE_AA)
            cv2.circle(
                frame,
                (center_x, center_y),
                10,
                self.COLORS["text_primary"],
                1,
                cv2.LINE_AA,
            )
            if gesture.type == GestureType.DOUBLE_CLICK:
                cv2.circle(
                    frame,
                    (center_x, center_y),
                    14,
                    self.COLORS["text_primary"],
                    1,
                    cv2.LINE_AA,
                )

        elif gesture.type == GestureType.RIGHT_CLICK:
            # 右键
            cv2.circle(frame, (center_x, center_y), 10, color, -1, cv2.LINE_AA)
            self._draw_text(
                frame,
                "R",
                (center_x - 5, center_y + 5),
                font_scale=0.45,
                color=self.COLORS["text_primary"],
            )

        elif gesture.type == GestureType.CLICK_HOLD:
            # 拖拽
            cv2.circle(frame, (center_x, center_y), 10, color, 2, cv2.LINE_AA)
            cv2.arrowedLine(
                frame,
                (center_x - 6, center_y),
                (center_x + 6, center_y),
                color,
                2,
                cv2.LINE_AA,
                tipLength=0.5,
            )

        elif gesture.type in [
            GestureType.SCROLL,
            GestureType.SCROLL_UP,
            GestureType.SCROLL_DOWN,
        ]:
            # 滚动 - 双箭头
            cv2.arrowedLine(
                frame,
                (center_x, center_y + 6),
                (center_x, center_y - 10),
                color,
                2,
                cv2.LINE_AA,
                tipLength=0.4,
            )
            cv2.arrowedLine(
                frame,
                (center_x, center_y - 6),
                (center_x, center_y + 10),
                color,
                2,
                cv2.LINE_AA,
                tipLength=0.4,
            )

        elif gesture.type == GestureType.PALM:
            # 手掌
            cv2.circle(frame, (center_x, center_y), 10, color, 2, cv2.LINE_AA)
            for i in range(5):
                angle = -90 + i * 36 - 36
                rad = angle * math.pi / 180
                fx = int(center_x + 14 * math.cos(rad))
                fy = int(center_y + 14 * math.sin(rad))
                cv2.circle(frame, (fx, fy), 3, color, -1, cv2.LINE_AA)

        elif gesture.type == GestureType.FIST:
            # 握拳
            cv2.circle(
                frame,
                (center_x, center_y),
                12,
                self.COLORS["text_muted"],
                -1,
                cv2.LINE_AA,
            )

    def _draw_pause_overlay(self, frame: np.ndarray) -> np.ndarray:
        """绘制暂停覆盖层"""
        h, w = frame.shape[:2]

        # 半透明覆盖
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), self.COLORS["bg_dark"], -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # 中心面板
        panel_w, panel_h = 240, 140
        panel_x = (w - panel_w) // 2
        panel_y = (h - panel_h) // 2

        self._draw_glass_panel(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_w, panel_y + panel_h),
            alpha=0.9,
            radius=16,
        )

        # 边框
        self._draw_rounded_rect(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_w, panel_y + panel_h),
            self.COLORS["border"],
            radius=16,
            thickness=1,
        )

        center_x = w // 2
        center_y = panel_y + 50

        # 暂停图标
        bar_w, bar_h = 12, 40
        gap = 14
        cv2.rectangle(
            frame,
            (center_x - gap - bar_w, center_y - bar_h // 2),
            (center_x - gap, center_y + bar_h // 2),
            self.COLORS["text_primary"],
            -1,
        )
        cv2.rectangle(
            frame,
            (center_x + gap - bar_w, center_y - bar_h // 2),
            (center_x + gap, center_y + bar_h // 2),
            self.COLORS["text_primary"],
            -1,
        )

        # 暂停文字
        pause_text = t("status.paused")
        self._draw_text(
            frame,
            pause_text,
            (center_x - 40, panel_y + 105),
            font_scale=0.7,
            color=self.COLORS["text_primary"],
            thickness=2,
        )

        # 提示
        self._draw_text(
            frame,
            "Press P to resume",
            (center_x - 60, panel_y + 125),
            font_scale=0.4,
            color=self.COLORS["text_muted"],
        )

        return frame

    def _draw_tutorial_overlay(self, frame: np.ndarray) -> np.ndarray:
        """绘制新手教程覆盖层"""
        h, w = frame.shape[:2]

        # 半透明背景
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), self.COLORS["bg_dark"], -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # 教程面板
        panel_w, panel_h = min(500, w - 40), min(400, h - 40)
        panel_x = (w - panel_w) // 2
        panel_y = (h - panel_h) // 2

        # 面板背景
        self._draw_glass_panel(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_w, panel_y + panel_h),
            alpha=0.95,
            radius=16,
        )

        # 边框
        self._draw_rounded_rect(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_w, panel_y + panel_h),
            self.COLORS["primary"],
            radius=16,
            thickness=2,
        )

        # 标题
        title = "Welcome to LyraPointer"
        self._draw_text(
            frame,
            title,
            (panel_x + 20, panel_y + 40),
            font_scale=0.8,
            color=self.COLORS["text_primary"],
            thickness=2,
        )

        # 手势说明
        gestures = [
            ("☝️", "Index finger up", "Move cursor"),
            ("👌", "Pinch (index+thumb)", "Left click"),
            ("✌️", "Two fingers pinch", "Right click"),
            ("🤏", "Pinch and hold", "Drag"),
            ("✌️↕", "Two fingers up/down", "Scroll"),
            ("🖐️", "Open palm", "Pause control"),
            ("✊", "Fist", "Stop / Reset"),
        ]

        y_offset = panel_y + 80
        for emoji, gesture, action in gestures:
            # 手势
            self._draw_text(
                frame,
                f"{gesture}",
                (panel_x + 30, y_offset),
                font_scale=0.5,
                color=self.COLORS["warning"],
            )
            # 动作
            self._draw_text(
                frame,
                f"→ {action}",
                (panel_x + 200, y_offset),
                font_scale=0.5,
                color=self.COLORS["text_secondary"],
            )
            y_offset += 35

        # 快捷键提示
        y_offset += 15
        cv2.line(
            frame,
            (panel_x + 20, y_offset),
            (panel_x + panel_w - 20, y_offset),
            self.COLORS["divider"],
            1,
        )
        y_offset += 25

        shortcuts = [
            ("P", "Pause/Resume"),
            ("Q", "Quit"),
            ("V", "Show/Hide window"),
        ]

        for key, desc in shortcuts:
            self._draw_text(
                frame,
                f"[{key}] {desc}",
                (panel_x + 30, y_offset),
                font_scale=0.45,
                color=self.COLORS["text_muted"],
            )
            y_offset += 28

        # 关闭按钮
        close_text = "Click anywhere or press any key to start"
        text_w = len(close_text) * 8
        self._draw_text(
            frame,
            close_text,
            (panel_x + (panel_w - text_w) // 2, panel_y + panel_h - 25),
            font_scale=0.45,
            color=self.COLORS["primary_light"],
        )

        return frame

    def _get_gesture_text(self, gesture_type: GestureType) -> str:
        """获取手势的本地化文本"""
        gesture_keys = {
            GestureType.NONE: "gesture.none",
            GestureType.POINTER: "gesture.pointer",
            GestureType.CLICK: "gesture.click",
            GestureType.DOUBLE_CLICK: "gesture.double_click",
            GestureType.CLICK_HOLD: "gesture.dragging",
            GestureType.RIGHT_CLICK: "gesture.right_click",
            GestureType.SCROLL: "gesture.scroll",
            GestureType.SCROLL_UP: "gesture.scroll_up",
            GestureType.SCROLL_DOWN: "gesture.scroll_down",
            GestureType.PALM: "gesture.palm",
            GestureType.FIST: "gesture.fist",
        }
        key = gesture_keys.get(gesture_type, "gesture.none")
        return t(key)

    def _draw_text(
        self,
        frame: np.ndarray,
        text: str,
        position: Tuple[int, int],
        font_scale: float = 0.6,
        color: Tuple[int, int, int] = (255, 255, 255),
        thickness: int = 1,
    ):
        """绘制文字（带阴影）"""
        x, y = position

        # 阴影
        cv2.putText(
            frame,
            text,
            (x + 1, y + 1),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            self.COLORS["shadow"],
            thickness + 1,
            cv2.LINE_AA,
        )

        # 主文字
        cv2.putText(
            frame,
            text,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA,
        )

    def show(self, frame: np.ndarray) -> int:
        """显示画面"""
        if not self._window_created:
            self.create_window()

        cv2.imshow(self.WINDOW_NAME, frame)
        return cv2.waitKey(1) & 0xFF

    def set_paused(self, paused: bool):
        """设置暂停状态"""
        self._is_paused = paused

    def set_mouse_callback(self, callback):
        """设置鼠标回调"""
        if not self._window_created:
            self.create_window()
        cv2.setMouseCallback(self.WINDOW_NAME, callback)

    def check_click(self, x: int, y: int, frame_width: int) -> Optional[str]:
        """检查点击位置"""
        # 如果教程显示中，任意点击关闭教程
        if self._show_tutorial:
            self._show_tutorial = False
            return "close_tutorial"

        # 检查帮助按钮
        if hasattr(self, "_help_btn_rect") and self._help_btn_rect:
            bx1, by1, bx2, by2 = self._help_btn_rect
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                self._show_tutorial = True
                return "help"

        # 检查设置按钮
        if hasattr(self, "_settings_btn_rect") and self._settings_btn_rect:
            bx1, by1, bx2, by2 = self._settings_btn_rect
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                return "settings"

        return None

    def close_tutorial(self):
        """关闭教程"""
        self._show_tutorial = False

    def show_tutorial(self):
        """显示教程"""
        self._show_tutorial = True


class FPSCounter:
    """FPS 计数器"""

    def __init__(self, avg_frames: int = 20):
        self._times: list[float] = []
        self._avg_frames = avg_frames
        self._last_fps = 0.0

    def update(self) -> float:
        """更新并返回 FPS"""
        now = time.perf_counter()
        self._times.append(now)

        if len(self._times) > self._avg_frames:
            self._times = self._times[-self._avg_frames :]

        if len(self._times) < 2:
            return self._last_fps

        elapsed = self._times[-1] - self._times[0]
        if elapsed <= 0:
            return self._last_fps

        self._last_fps = (len(self._times) - 1) / elapsed
        return self._last_fps

    def reset(self):
        """重置"""
        self._times.clear()
        self._last_fps = 0.0
