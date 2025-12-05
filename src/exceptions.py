"""
LyraPointer 自定义异常类

提供更精确的错误处理和调试信息。
"""


class LyraPointerError(Exception):
    """LyraPointer 基础异常类"""

    def __init__(self, message: str = "", details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


class CameraError(LyraPointerError):
    """摄像头相关错误"""

    pass


class CameraNotFoundError(CameraError):
    """摄像头未找到"""

    def __init__(self, camera_index: int = 0):
        super().__init__(
            f"无法找到摄像头 {camera_index}",
            {"camera_index": camera_index},
        )


class CameraOpenError(CameraError):
    """摄像头无法打开"""

    def __init__(self, camera_index: int = 0, reason: str = ""):
        message = f"无法打开摄像头 {camera_index}"
        if reason:
            message += f": {reason}"
        super().__init__(message, {"camera_index": camera_index, "reason": reason})


class CameraReadError(CameraError):
    """摄像头读取错误"""

    def __init__(self, camera_index: int = 0):
        super().__init__(
            f"无法从摄像头 {camera_index} 读取帧",
            {"camera_index": camera_index},
        )


class CameraDisconnectedError(CameraError):
    """摄像头断开连接"""

    def __init__(self, camera_index: int = 0):
        super().__init__(
            f"摄像头 {camera_index} 已断开连接",
            {"camera_index": camera_index},
        )


class ConfigError(LyraPointerError):
    """配置相关错误"""

    pass


class ConfigNotFoundError(ConfigError):
    """配置文件未找到"""

    def __init__(self, path: str):
        super().__init__(f"配置文件未找到: {path}", {"path": path})


class ConfigParseError(ConfigError):
    """配置文件解析错误"""

    def __init__(self, path: str, reason: str = ""):
        message = f"配置文件解析失败: {path}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"path": path, "reason": reason})


class ConfigValidationError(ConfigError):
    """配置验证错误"""

    def __init__(self, key: str, value, reason: str = ""):
        message = f"配置项 '{key}' 值无效: {value}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"key": key, "value": value, "reason": reason})


class GestureError(LyraPointerError):
    """手势识别相关错误"""

    pass


class GestureDetectionError(GestureError):
    """手势检测错误"""

    def __init__(self, reason: str = ""):
        super().__init__(f"手势检测失败: {reason}", {"reason": reason})


class GesturePluginError(GestureError):
    """手势插件错误"""

    def __init__(self, plugin_name: str, reason: str = ""):
        message = f"手势插件 '{plugin_name}' 错误"
        if reason:
            message += f": {reason}"
        super().__init__(message, {"plugin_name": plugin_name, "reason": reason})


class TrackerError(LyraPointerError):
    """追踪器相关错误"""

    pass


class TrackerInitError(TrackerError):
    """追踪器初始化错误"""

    def __init__(self, reason: str = ""):
        super().__init__(f"追踪器初始化失败: {reason}", {"reason": reason})


class HandNotDetectedError(TrackerError):
    """未检测到手"""

    def __init__(self):
        super().__init__("未检测到手部")


class ControlError(LyraPointerError):
    """系统控制相关错误"""

    pass


class MouseControlError(ControlError):
    """鼠标控制错误"""

    def __init__(self, action: str, reason: str = ""):
        message = f"鼠标操作 '{action}' 失败"
        if reason:
            message += f": {reason}"
        super().__init__(message, {"action": action, "reason": reason})


class KeyboardControlError(ControlError):
    """键盘控制错误"""

    def __init__(self, action: str, reason: str = ""):
        message = f"键盘操作 '{action}' 失败"
        if reason:
            message += f": {reason}"
        super().__init__(message, {"action": action, "reason": reason})


class ScreenError(ControlError):
    """屏幕相关错误"""

    def __init__(self, reason: str = ""):
        super().__init__(f"屏幕操作失败: {reason}", {"reason": reason})


class UIError(LyraPointerError):
    """用户界面相关错误"""

    pass


class WindowError(UIError):
    """窗口错误"""

    def __init__(self, window_name: str, reason: str = ""):
        message = f"窗口 '{window_name}' 错误"
        if reason:
            message += f": {reason}"
        super().__init__(message, {"window_name": window_name, "reason": reason})


class TrayError(UIError):
    """系统托盘错误"""

    def __init__(self, reason: str = ""):
        super().__init__(f"系统托盘错误: {reason}", {"reason": reason})


class PluginError(LyraPointerError):
    """插件系统错误"""

    pass


class PluginLoadError(PluginError):
    """插件加载错误"""

    def __init__(self, plugin_name: str, reason: str = ""):
        message = f"插件 '{plugin_name}' 加载失败"
        if reason:
            message += f": {reason}"
        super().__init__(message, {"plugin_name": plugin_name, "reason": reason})


class PluginExecutionError(PluginError):
    """插件执行错误"""

    def __init__(self, plugin_name: str, reason: str = ""):
        message = f"插件 '{plugin_name}' 执行失败"
        if reason:
            message += f": {reason}"
        super().__init__(message, {"plugin_name": plugin_name, "reason": reason})


class PlatformError(LyraPointerError):
    """平台兼容性错误"""

    pass


class WaylandError(PlatformError):
    """Wayland 相关错误"""

    def __init__(self, reason: str = ""):
        message = "Wayland 环境不支持此操作"
        if reason:
            message += f": {reason}"
        super().__init__(message, {"reason": reason})


class UnsupportedPlatformError(PlatformError):
    """不支持的平台"""

    def __init__(self, platform: str, feature: str = ""):
        message = f"平台 '{platform}' 不支持"
        if feature:
            message += f" '{feature}' 功能"
        super().__init__(message, {"platform": platform, "feature": feature})
