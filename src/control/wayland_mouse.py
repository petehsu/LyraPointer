"""
LyraPointer Wayland 鼠标控制器

使用 ydotool 在 Wayland 环境下控制鼠标。
ydotool 是一个通用的输入模拟工具，支持 X11 和 Wayland。

安装 ydotool:
    Arch Linux: sudo pacman -S ydotool
    Ubuntu/Debian: sudo apt install ydotool

注意: ydotool 需要 ydotoold 守护进程运行:
    sudo systemctl enable --now ydotool
    或者手动运行: sudo ydotoold
"""

import shutil
import subprocess
import time
from typing import Optional, Tuple

from ..utils.logging import get_logger

logger = get_logger(__name__)


class WaylandMouseController:
    """
    Wayland 环境下的鼠标控制器

    使用 ydotool 实现鼠标控制，作为 PyAutoGUI 的替代方案。

    Example:
        >>> controller = WaylandMouseController()
        >>> if controller.available:
        ...     controller.move_to(500, 300)
        ...     controller.click()
    """

    # ydotool 鼠标按钮代码
    BUTTON_LEFT = 0x110  # BTN_LEFT
    BUTTON_RIGHT = 0x111  # BTN_RIGHT
    BUTTON_MIDDLE = 0x112  # BTN_MIDDLE

    # 鼠标事件类型
    MOUSE_DOWN = "D"
    MOUSE_UP = "U"
    MOUSE_CLICK = "C"  # Down + Up

    def __init__(self, move_duration: float = 0.0):
        """
        初始化 Wayland 鼠标控制器

        Args:
            move_duration: 移动动画时长（秒），0 表示即时移动
        """
        self.move_duration = move_duration
        self._ydotool_path: Optional[str] = None
        self._available = False
        self._last_position: Tuple[int, int] = (0, 0)
        self._is_dragging = False

        # 检查 ydotool 可用性
        self._check_ydotool()

    def _check_ydotool(self) -> bool:
        """
        检查 ydotool 是否可用

        Returns:
            是否可用
        """
        # 查找 ydotool 可执行文件
        self._ydotool_path = shutil.which("ydotool")

        if self._ydotool_path is None:
            logger.warning("ydotool not found. Install it for Wayland support.")
            self._available = False
            return False

        # 测试 ydotool 是否可以运行
        try:
            result = subprocess.run(
                [self._ydotool_path, "--help"],
                capture_output=True,
                timeout=2,
            )
            self._available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
            logger.warning(f"ydotool test failed: {e}")
            self._available = False

        if self._available:
            logger.info("ydotool is available for Wayland mouse control")
        else:
            logger.warning(
                "ydotool is not working. "
                "Make sure ydotoold daemon is running: sudo systemctl start ydotool"
            )

        return self._available

    @property
    def available(self) -> bool:
        """ydotool 是否可用"""
        return self._available

    def _run_ydotool(self, *args) -> bool:
        """
        运行 ydotool 命令

        Args:
            *args: 命令参数

        Returns:
            是否成功
        """
        if not self._available:
            return False

        try:
            cmd = [self._ydotool_path] + list(args)
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=1,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
            logger.error(f"ydotool command failed: {e}")
            return False

    def move_to(self, x: int, y: int, duration: Optional[float] = None) -> bool:
        """
        移动鼠标到指定位置（绝对坐标）

        Args:
            x: x 坐标
            y: y 坐标
            duration: 移动时长（当前实现中被忽略）

        Returns:
            是否成功
        """
        # ydotool mousemove -a x y
        success = self._run_ydotool("mousemove", "-a", str(x), str(y))
        if success:
            self._last_position = (x, y)
        return success

    def move_relative(self, dx: int, dy: int, duration: Optional[float] = None) -> bool:
        """
        相对移动鼠标

        Args:
            dx: x 方向偏移
            dy: y 方向偏移
            duration: 移动时长（当前实现中被忽略）

        Returns:
            是否成功
        """
        # ydotool mousemove -- dx dy (不带 -a 表示相对移动)
        success = self._run_ydotool("mousemove", "--", str(dx), str(dy))
        if success:
            self._last_position = (
                self._last_position[0] + dx,
                self._last_position[1] + dy,
            )
        return success

    def click(self, button: str = "left", clicks: int = 1) -> bool:
        """
        点击鼠标

        Args:
            button: 按钮 ("left", "right", "middle")
            clicks: 点击次数

        Returns:
            是否成功
        """
        button_code = self._get_button_code(button)

        # ydotool click <button_code>
        # 对于多次点击，需要多次调用
        for _ in range(clicks):
            # 格式: 0xC0 表示点击 (down + up)，0x110 是左键代码
            # ydotool click 0xC0
            # 但更可靠的方式是使用 button 代码
            if not self._run_ydotool("click", hex(button_code)):
                return False
            if clicks > 1:
                time.sleep(0.05)  # 多次点击之间的间隔

        return True

    def double_click(self, button: str = "left") -> bool:
        """
        双击鼠标

        Args:
            button: 按钮

        Returns:
            是否成功
        """
        return self.click(button=button, clicks=2)

    def right_click(self) -> bool:
        """右键点击"""
        return self.click(button="right")

    def middle_click(self) -> bool:
        """中键点击"""
        return self.click(button="middle")

    def mouse_down(self, button: str = "left") -> bool:
        """
        按下鼠标按钮（不释放）

        Args:
            button: 按钮

        Returns:
            是否成功
        """
        button_code = self._get_button_code(button)

        # ydotool click -d <button_code>  # down only
        success = self._run_ydotool("click", "-d", hex(button_code))
        if success and button == "left":
            self._is_dragging = True
        return success

    def mouse_up(self, button: str = "left") -> bool:
        """
        释放鼠标按钮

        Args:
            button: 按钮

        Returns:
            是否成功
        """
        button_code = self._get_button_code(button)

        # ydotool click -u <button_code>  # up only
        success = self._run_ydotool("click", "-u", hex(button_code))
        if success and button == "left":
            self._is_dragging = False
        return success

    def scroll(self, amount: int, horizontal: bool = False) -> bool:
        """
        滚动

        Args:
            amount: 滚动量（正数向上/右，负数向下/左）
            horizontal: 是否水平滚动

        Returns:
            是否成功
        """
        # ydotool mousemove -w -- <amount>  # 垂直滚动
        # 对于水平滚动，ydotool 可能需要不同的参数

        if horizontal:
            # 水平滚动 (如果支持)
            return self._run_ydotool("mousemove", "-h", "--", str(amount))
        else:
            # 垂直滚动
            # 注意：ydotool 的滚动方向可能与预期相反，需要取反
            return self._run_ydotool("mousemove", "-w", "--", str(amount))

    def scroll_up(self, amount: int = 3) -> bool:
        """向上滚动"""
        return self.scroll(amount)

    def scroll_down(self, amount: int = 3) -> bool:
        """向下滚动"""
        return self.scroll(-amount)

    def _get_button_code(self, button: str) -> int:
        """
        获取按钮代码

        Args:
            button: 按钮名称

        Returns:
            按钮代码
        """
        button_map = {
            "left": self.BUTTON_LEFT,
            "right": self.BUTTON_RIGHT,
            "middle": self.BUTTON_MIDDLE,
        }
        return button_map.get(button.lower(), self.BUTTON_LEFT)

    @property
    def position(self) -> Tuple[int, int]:
        """
        获取最后已知的鼠标位置

        注意：这是缓存的位置，可能不准确
        """
        return self._last_position

    @property
    def is_dragging(self) -> bool:
        """是否正在拖拽"""
        return self._is_dragging

    def stop_drag(self):
        """停止拖拽"""
        if self._is_dragging:
            self.mouse_up()


def is_wayland() -> bool:
    """
    检测是否在 Wayland 环境下运行

    Returns:
        是否是 Wayland 环境
    """
    import os

    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "")

    return session_type == "wayland" or bool(wayland_display)


def get_mouse_controller():
    """
    获取适合当前环境的鼠标控制器

    在 Wayland 下优先使用 WaylandMouseController，
    如果不可用则回退到 PyAutoGUI。

    Returns:
        鼠标控制器实例
    """
    if is_wayland():
        wayland_controller = WaylandMouseController()
        if wayland_controller.available:
            logger.info("Using WaylandMouseController (ydotool)")
            return wayland_controller
        else:
            logger.warning(
                "WaylandMouseController not available, "
                "falling back to PyAutoGUI (may not work on Wayland)"
            )

    # 回退到 PyAutoGUI
    from .mouse import MouseController

    return MouseController()
