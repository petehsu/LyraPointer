"""
LyraPointer 主程序

整合所有模块，实现完整的手势控制系统。
优化版本 - 改进性能和多语言支持。
"""

import argparse
import os
import sys
import time
from typing import Optional

import cv2

from .config import Settings
from .control import MouseController, ScreenManager
from .gestures import Gesture, GestureDetector, GestureType
from .tracker import HandTracker, Smoother
from .ui import SettingsWindow, SystemTray, Visualizer
from .utils.i18n import Language, get_i18n, t


class LyraPointer:
    """LyraPointer 手势控制系统"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化 LyraPointer

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.settings = Settings(config_path)

        # 初始化多语言
        self._init_i18n()

        # 初始化组件
        self._init_components()

        # 状态
        self._is_running = False
        self._is_paused = False
        self._show_window = True
        self._last_gesture: Optional[Gesture] = None
        self._is_dragging = False

        # 性能优化：帧跳过计数
        self._frame_count = 0
        self._process_interval = self.settings.get(
            "settings.performance.process_interval", 1
        )

        # 性能优化：上次处理时间
        self._last_process_time = 0.0
        self._min_process_interval = 0.016  # ~60fps 上限

    def _init_i18n(self):
        """初始化多语言支持"""
        i18n = get_i18n()

        # 尝试从配置加载语言设置
        saved_lang = self.settings.get("ui.language", None)
        if saved_lang:
            if not i18n.set_language_by_code(saved_lang):
                # 如果保存的语言无效，自动检测
                i18n.auto_detect_and_set()
        else:
            # 自动检测系统语言
            i18n.auto_detect_and_set()

    def _init_components(self):
        """初始化所有组件"""
        # 手部追踪器
        self.tracker = HandTracker(
            max_hands=1,
            model_complexity=self.settings.model_complexity,
            detection_confidence=self.settings.detection_confidence,
            tracking_confidence=self.settings.tracking_confidence,
        )

        # 轨迹平滑器
        smoothing = self.settings.smoothing
        # 调整 One Euro Filter 参数以获得更丝滑的体验
        # min_cutoff: 越小越平滑，延迟越高 (0.01 - 1.0)
        # beta: 速度系数，越小高速时越平滑 (0.0 - 1.0)

        # 优化的 One Euro Filter 参数
        # min_cutoff: 越小越平滑，延迟越高
        # beta: 速度系数，对快速移动更敏感
        min_cutoff = 0.1 + (1.0 - smoothing) * 0.4  # 范围 0.1 - 0.5
        beta = 0.005 + smoothing * 0.02  # 范围 0.005 - 0.025

        self.smoother = Smoother(min_cutoff=min_cutoff, beta=beta)

        # 手势检测器
        self.detector = GestureDetector(
            pinch_threshold=0.05,
            click_hold_frames=3,
            double_click_interval=0.3,
        )

        # 屏幕管理器
        self.screen = ScreenManager(
            control_zone=self.settings.control_zone,
            sensitivity=self.settings.sensitivity,
        )

        # 鼠标控制器
        self.mouse = MouseController()

        # 可视化器
        self.visualizer = Visualizer(
            show_skeleton=self.settings.show_skeleton,
            show_gesture_info=True,
            show_control_zone=True,
            show_fps=self.settings.show_fps,
        )
        self.visualizer.set_mouse_callback(self._on_mouse_click)

        # 设置窗口
        self.settings_window = SettingsWindow(
            settings=self.settings,
            on_save=self._on_settings_save,
            on_close=self._on_settings_close,
        )

        # 系统托盘
        self.tray = SystemTray(
            on_show=self._on_show_window,
            on_hide=self._on_hide_window,
            on_pause=self._on_toggle_pause,
            on_quit=self._on_quit,
        )

        # 摄像头
        self.cap: Optional[cv2.VideoCapture] = None

    def _init_camera(self) -> bool:
        """初始化摄像头"""
        self.cap = cv2.VideoCapture(self.settings.camera_index)

        if not self.cap.isOpened():
            print(f"Error: Cannot open camera {self.settings.camera_index}")
            return False

        # 设置分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.camera_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.camera_height)

        return True

    def _check_wayland(self) -> bool:
        """检查是否在 Wayland 下运行，如果是则显示警告"""
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        wayland_display = os.environ.get("WAYLAND_DISPLAY", "")

        if session_type == "wayland" or wayland_display:
            print("=" * 50)
            print("  ⚠️  检测到 Wayland 会话")
            print("=" * 50)
            print()
            print("PyAutoGUI 在 Wayland 下可能无法正常控制鼠标。")
            print()
            print("解决方案:")
            print("  1. 切换到 X11 会话登录")
            print("  2. 或设置环境变量运行:")
            print("     XDG_SESSION_TYPE=x11 python run.py")
            print()
            print("系统托盘功能也可能受限。")
            print("-" * 50)
            print()
            return True
        return False

    def run(self):
        """运行主循环"""
        # 检查 Wayland
        self._check_wayland()

        print("=" * 50)
        print(f"  {t('app.title')}")
        print("=" * 50)
        print()
        print(t("hotkey.quit"))
        print(t("hotkey.pause"))
        print(t("hotkey.toggle_window"))
        print()
        print(t("help.pointer"))
        print(t("help.click"))
        print(t("help.right_click"))
        print(t("help.scroll"))
        print(t("help.palm"))
        print(t("help.fist"))
        print()

        # 初始化摄像头
        if not self._init_camera():
            return

        # 启动系统托盘
        if self.tray.available:
            self.tray.start()
            print("System tray started")

        self._is_running = True

        try:
            self._main_loop()
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self._cleanup()

    def _main_loop(self):
        """主循环 - 性能优化版"""
        while self._is_running:
            # 性能优化：限制处理频率
            current_time = time.perf_counter()
            time_since_last = current_time - self._last_process_time

            if time_since_last < self._min_process_interval:
                # 跳过这一帧，但仍需读取以清空缓冲区
                self.cap.grab()
                continue

            self._last_process_time = current_time

            # 读取摄像头
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Cannot read frame")
                break

            # 帧跳过（用于低性能设备）
            self._frame_count += 1
            if self._frame_count % self._process_interval != 0:
                continue

            # 水平翻转（镜像）
            frame = cv2.flip(frame, 1)

            # 处理手势
            gesture = None
            cursor_pos = None

            if not self._is_paused:
                gesture, cursor_pos = self._process_frame(frame)

            # 可视化
            if self._show_window:
                # 绘制手部骨架
                if self.tracker._last_landmarks:
                    frame = self.tracker.draw_landmarks(
                        frame,
                        self.tracker._last_landmarks,
                    )

                # 获取控制区域
                h, w = frame.shape[:2]
                control_zone = self.screen.get_zone_rect(w, h)

                # 渲染界面
                display = self.visualizer.render(
                    frame,
                    gesture=gesture,
                    control_zone=control_zone,
                    cursor_pos=cursor_pos,
                )

                # 显示并处理按键
                key = self.visualizer.show(display)
                self._handle_key(key)
            else:
                # 后台模式，添加小延迟
                time.sleep(0.01)

    def _process_frame(
        self, frame
    ) -> tuple[Optional[Gesture], Optional[tuple[int, int]]]:
        """
        处理一帧图像

        Returns:
            (手势, 指针位置)
        """
        h, w = frame.shape[:2]

        # 手部追踪
        hands = self.tracker.process(frame)

        if not hands:
            # 没有检测到手，停止拖拽
            if self._is_dragging:
                self.mouse.mouse_up()
                self._is_dragging = False
            self.smoother.reset()
            self.detector.reset()
            return None, None

        hand = hands[0]  # 只处理第一只手

        # 检测手势
        gesture = self.detector.detect(hand)

        # 获取指针位置（食指尖端）
        index_tip = hand.get_finger_tip("index")

        # 检查是否在控制区域内
        if not self.screen.is_in_control_zone(index_tip.x, index_tip.y):
            return gesture, None

        # 平滑处理
        smooth_x, smooth_y = self.smoother.smooth(index_tip.x, index_tip.y)

        # 转换为屏幕坐标
        screen_x, screen_y = self.screen.camera_to_screen(smooth_x, smooth_y)

        # 在画面上的显示位置（镜像翻转后）
        cursor_pixel = (int((1 - smooth_x) * w), int(smooth_y * h))

        # 执行操作
        self._execute_gesture(gesture, screen_x, screen_y)

        return gesture, cursor_pixel

    def _execute_gesture(self, gesture: Gesture, x: int, y: int):
        """执行手势对应的操作"""
        gesture_type = gesture.type

        # 指针模式 - 移动鼠标
        if gesture_type == GestureType.POINTER:
            if self._is_dragging:
                # 拖拽模式下继续移动
                self.mouse.move_to(x, y)
            else:
                self.mouse.move_to(x, y)

        # 点击
        elif gesture_type == GestureType.CLICK:
            # 只在手势开始时点击（防止连续触发）
            if (
                self._last_gesture is None
                or self._last_gesture.type != GestureType.CLICK
            ):
                if gesture.frames >= 3:  # 需要保持几帧
                    self.mouse.move_to(x, y)
                    self.mouse.click()

        # 双击
        elif gesture_type == GestureType.DOUBLE_CLICK:
            self.mouse.move_to(x, y)
            self.mouse.double_click()

        # 拖拽开始
        elif gesture_type == GestureType.CLICK_HOLD:
            if not self._is_dragging:
                self.mouse.move_to(x, y)
                self.mouse.mouse_down()
                self._is_dragging = True
            else:
                self.mouse.move_to(x, y)

        # 右键
        elif gesture_type == GestureType.RIGHT_CLICK:
            if (
                self._last_gesture is None
                or self._last_gesture.type != GestureType.RIGHT_CLICK
            ):
                if gesture.frames >= 3:
                    self.mouse.move_to(x, y)
                    self.mouse.right_click()

        # 滚动
        elif gesture_type == GestureType.SCROLL_UP:
            self.mouse.scroll_up(self.settings.scroll_speed)

        elif gesture_type == GestureType.SCROLL_DOWN:
            self.mouse.scroll_down(self.settings.scroll_speed)

        # 暂停
        elif gesture_type == GestureType.PALM:
            if gesture.frames >= 10:  # 需要保持一段时间
                if (
                    self._last_gesture is None
                    or self._last_gesture.type != GestureType.PALM
                ):
                    self._toggle_pause()

        # 停止拖拽（当手势变为非捏合状态）
        if self._is_dragging and gesture_type not in [
            GestureType.CLICK_HOLD,
            GestureType.CLICK,
        ]:
            self.mouse.mouse_up()
            self._is_dragging = False

        self._last_gesture = gesture

    def _handle_key(self, key: int):
        """处理按键"""
        if key == ord("q") or key == ord("Q"):
            self._is_running = False
        elif key == ord("p") or key == ord("P"):
            self._toggle_pause()
        elif key == ord("v") or key == ord("V"):
            self._toggle_window()

    def _toggle_pause(self):
        """切换暂停状态"""
        self._is_paused = not self._is_paused
        self.visualizer.set_paused(self._is_paused)
        if self.tray.available:
            self.tray.update_status(self._is_paused)

        status = t("status.paused") if self._is_paused else t("status.running")
        print(f"Control: {status}")

        # 如果暂停时正在拖拽，停止拖拽
        if self._is_paused and self._is_dragging:
            self.mouse.mouse_up()
            self._is_dragging = False

    def _toggle_window(self):
        """切换窗口可见性"""
        self._show_window = not self._show_window
        if not self._show_window:
            self.visualizer.destroy_window()
        else:
            self.visualizer.create_window()

    def _on_mouse_click(self, event, x, y, flags, param):
        """鼠标点击回调"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # 检查点击了什么
            target = self.visualizer.check_click(x, y, self.settings.camera_width)

            if target == "settings":
                self._open_settings()

    def _open_settings(self):
        """打开设置窗口"""
        # 暂停处理以避免冲突
        was_paused = self._is_paused
        self._is_paused = True
        self.visualizer.set_paused(True)

        # 在主线程中显示（注意：OpenCV 的 waitKey 可能会阻塞 Tkinter，这里简单处理）
        # 更好的方式是使用多线程，但为保持简单，我们暂时阻塞主循环
        print("Opening settings...")
        self.settings_window.show()

        # 恢复状态
        if not was_paused:
            self._is_paused = False
            self.visualizer.set_paused(False)

    def _on_settings_save(self):
        """设置保存回调"""
        print("Settings saved, reloading...")
        # 重新应用设置
        self.screen.sensitivity = self.settings.sensitivity
        self.screen.flip_x = self.settings.flip_x
        self.screen.flip_y = self.settings.flip_y

        self.visualizer.show_skeleton = self.settings.show_skeleton
        self.visualizer.show_fps = self.settings.show_fps

        # 更新平滑参数
        smoothing = self.settings.smoothing
        min_cutoff = 0.05 + (1.0 - smoothing) * 0.5
        beta = 0.001 + smoothing * 0.01
        self.smoother.min_cutoff = min_cutoff
        self.smoother.beta = beta

    def _on_settings_close(self):
        """设置关闭回调"""
        pass

    def _on_show_window(self):
        """显示窗口回调"""
        self._show_window = True
        self.visualizer.create_window()

    def _on_hide_window(self):
        """隐藏窗口回调"""
        self._show_window = False
        self.visualizer.destroy_window()

    def _on_toggle_pause(self):
        """暂停回调"""
        self._toggle_pause()

    def _on_quit(self):
        """退出回调"""
        self._is_running = False

    def _cleanup(self):
        """清理资源"""
        print("\nCleaning up...")

        # 停止拖拽
        if self._is_dragging:
            self.mouse.mouse_up()

        # 释放资源
        if self.cap:
            self.cap.release()

        self.tracker.release()
        self.visualizer.destroy_window()
        self.tray.stop()

        cv2.destroyAllWindows()
        print(t("info.stopped"))


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="LyraPointer - 手势控制系统")
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="配置文件路径",
    )
    parser.add_argument(
        "--camera",
        "-cam",
        type=int,
        default=0,
        help="摄像头索引",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="无界面模式（仅托盘）",
    )

    args = parser.parse_args()

    # 创建应用
    app = LyraPointer(config_path=args.config)

    # 应用命令行参数
    if args.camera != 0:
        app.settings.set("settings.camera.index", args.camera)

    if args.no_gui:
        app._show_window = False

    # 运行
    app.run()


if __name__ == "__main__":
    main()
