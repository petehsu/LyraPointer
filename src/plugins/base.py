"""
LyraPointer 插件系统基类

定义插件的基础接口和类型，用于扩展手势和动作。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

if TYPE_CHECKING:
    from ..gestures.gestures import Gesture
    from ..tracker.hand_tracker import HandLandmarks


class PluginType(Enum):
    """插件类型枚举"""

    GESTURE = auto()  # 手势插件
    ACTION = auto()  # 动作插件
    FILTER = auto()  # 过滤器插件
    VISUALIZER = auto()  # 可视化插件
    FEEDBACK = auto()  # 反馈插件


@dataclass
class PluginInfo:
    """插件信息"""

    name: str
    version: str = "1.0.0"
    author: str = "Unknown"
    description: str = ""
    plugin_type: PluginType = PluginType.GESTURE
    enabled: bool = True
    priority: int = 0  # 优先级，数字越大越先执行
    dependencies: List[str] = field(default_factory=list)
    config_schema: Optional[Dict] = None  # 配置项定义

    def __str__(self) -> str:
        return f"{self.name} v{self.version} by {self.author}"


class Plugin(ABC):
    """
    插件基类

    所有插件都应该继承此类并实现必要的方法。

    Example:
        >>> class MyPlugin(Plugin):
        ...     @property
        ...     def info(self) -> PluginInfo:
        ...         return PluginInfo(
        ...             name="MyPlugin",
        ...             description="A custom plugin"
        ...         )
        ...
        ...     def initialize(self):
        ...         print("Plugin initialized")
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._enabled = True
        self._initialized = False

    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """
        获取插件信息

        Returns:
            插件信息对象
        """
        pass

    @property
    def name(self) -> str:
        """获取插件名称"""
        return self.info.name

    @property
    def enabled(self) -> bool:
        """插件是否启用"""
        return self._enabled and self.info.enabled

    @enabled.setter
    def enabled(self, value: bool):
        """设置插件启用状态"""
        self._enabled = value

    @property
    def initialized(self) -> bool:
        """插件是否已初始化"""
        return self._initialized

    def initialize(self):
        """
        初始化插件

        在插件加载后调用，用于执行初始化操作。
        子类可以重写此方法。
        """
        self._initialized = True

    def shutdown(self):
        """
        关闭插件

        在插件卸载前调用，用于清理资源。
        子类可以重写此方法。
        """
        self._initialized = False

    def configure(self, config: Dict[str, Any]):
        """
        配置插件

        Args:
            config: 配置字典
        """
        self._config.update(config)
        self.on_config_changed(config)

    def on_config_changed(self, config: Dict[str, Any]):
        """
        配置变化回调

        Args:
            config: 新的配置
        """
        pass

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self._config.get(key, default)

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        验证配置

        Args:
            config: 要验证的配置

        Returns:
            错误消息列表，如果为空则验证通过
        """
        errors = []
        schema = self.info.config_schema

        if schema:
            for key, rules in schema.items():
                if rules.get("required") and key not in config:
                    errors.append(f"Missing required config: {key}")
                elif key in config:
                    value = config[key]
                    expected_type = rules.get("type")
                    if expected_type and not isinstance(value, expected_type):
                        errors.append(
                            f"Invalid type for {key}: "
                            f"expected {expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )
                    min_val = rules.get("min")
                    max_val = rules.get("max")
                    if min_val is not None and value < min_val:
                        errors.append(f"{key} must be >= {min_val}")
                    if max_val is not None and value > max_val:
                        errors.append(f"{key} must be <= {max_val}")

        return errors

    def __str__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"{self.info} ({status})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name!r}>"


class GesturePlugin(Plugin):
    """
    手势插件基类

    用于定义自定义手势检测逻辑。

    Example:
        >>> class ThreeFingerPinchPlugin(GesturePlugin):
        ...     @property
        ...     def info(self) -> PluginInfo:
        ...         return PluginInfo(
        ...             name="ThreeFingerPinch",
        ...             plugin_type=PluginType.GESTURE,
        ...             description="Detect three finger pinch gesture"
        ...         )
        ...
        ...     def detect(self, hand):
        ...         # 检测三指捏合
        ...         thumb = hand.get_finger_tip("thumb")
        ...         index = hand.get_finger_tip("index")
        ...         middle = hand.get_finger_tip("middle")
        ...         # ... 计算距离并判断
        ...         return None  # 或返回自定义 Gesture
    """

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name=self.__class__.__name__,
            plugin_type=PluginType.GESTURE,
            description="Gesture detection plugin",
        )

    @abstractmethod
    def detect(self, hand: "HandLandmarks") -> Optional["Gesture"]:
        """
        检测自定义手势

        Args:
            hand: 手部关键点数据

        Returns:
            检测到的手势，如果没有检测到则返回 None
        """
        pass

    def get_gesture_name(self) -> str:
        """
        获取手势名称

        Returns:
            手势名称
        """
        return self.name

    def get_gesture_description(self) -> str:
        """
        获取手势描述

        Returns:
            手势描述
        """
        return self.info.description


class ActionPlugin(Plugin):
    """
    动作插件基类

    用于定义自定义动作执行逻辑。

    Example:
        >>> class ScreenshotPlugin(ActionPlugin):
        ...     @property
        ...     def info(self) -> PluginInfo:
        ...         return PluginInfo(
        ...             name="Screenshot",
        ...             plugin_type=PluginType.ACTION,
        ...             description="Take screenshot on gesture"
        ...         )
        ...
        ...     def execute(self, gesture, context):
        ...         import pyautogui
        ...         pyautogui.hotkey('ctrl', 'shift', 's')
    """

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name=self.__class__.__name__,
            plugin_type=PluginType.ACTION,
            description="Action execution plugin",
        )

    @abstractmethod
    def execute(self, gesture: "Gesture", context: Dict[str, Any]) -> bool:
        """
        执行动作

        Args:
            gesture: 触发的手势
            context: 上下文信息（包含位置、状态等）

        Returns:
            是否成功执行
        """
        pass

    def can_execute(self, gesture: "Gesture", context: Dict[str, Any]) -> bool:
        """
        检查是否可以执行动作

        Args:
            gesture: 手势
            context: 上下文

        Returns:
            是否可以执行
        """
        return self.enabled


class FilterPlugin(Plugin):
    """
    过滤器插件基类

    用于对手势或坐标进行过滤/修改。
    """

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name=self.__class__.__name__,
            plugin_type=PluginType.FILTER,
            description="Filter plugin",
        )

    @abstractmethod
    def filter(self, data: Any, context: Dict[str, Any]) -> Any:
        """
        过滤/处理数据

        Args:
            data: 输入数据
            context: 上下文信息

        Returns:
            处理后的数据
        """
        pass


class VisualizerPlugin(Plugin):
    """
    可视化插件基类

    用于在界面上绘制自定义内容。
    """

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name=self.__class__.__name__,
            plugin_type=PluginType.VISUALIZER,
            description="Visualizer plugin",
        )

    @abstractmethod
    def draw(self, frame, context: Dict[str, Any]):
        """
        在帧上绘制内容

        Args:
            frame: 图像帧 (numpy array)
            context: 上下文信息

        Returns:
            处理后的帧
        """
        pass


class FeedbackPlugin(Plugin):
    """
    反馈插件基类

    用于提供声音、触觉等反馈。
    """

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name=self.__class__.__name__,
            plugin_type=PluginType.FEEDBACK,
            description="Feedback plugin",
        )

    @abstractmethod
    def trigger(self, event: str, context: Dict[str, Any]):
        """
        触发反馈

        Args:
            event: 事件名称 (如 "click", "scroll", "error")
            context: 上下文信息
        """
        pass
