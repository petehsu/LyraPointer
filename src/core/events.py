"""
LyraPointer 事件系统

实现发布-订阅模式，用于解耦手势检测和动作执行。
"""

import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional
from weakref import WeakSet


class EventType(Enum):
    """事件类型枚举"""

    # 手势相关事件
    GESTURE_DETECTED = auto()  # 检测到手势
    GESTURE_CHANGED = auto()  # 手势变化
    GESTURE_STARTED = auto()  # 手势开始
    GESTURE_ENDED = auto()  # 手势结束

    # 手部追踪事件
    HAND_DETECTED = auto()  # 检测到手
    HAND_LOST = auto()  # 手丢失
    HAND_MOVED = auto()  # 手移动

    # 控制相关事件
    CURSOR_MOVED = auto()  # 鼠标移动
    CLICK_PERFORMED = auto()  # 点击执行
    SCROLL_PERFORMED = auto()  # 滚动执行
    DRAG_STARTED = auto()  # 拖拽开始
    DRAG_ENDED = auto()  # 拖拽结束

    # 状态相关事件
    STATE_CHANGED = auto()  # 状态变化
    PAUSE_TOGGLED = auto()  # 暂停切换
    CONTROL_PAUSED = auto()  # 控制暂停
    CONTROL_RESUMED = auto()  # 控制恢复

    # 配置相关事件
    SETTINGS_CHANGED = auto()  # 设置变化
    SETTINGS_SAVED = auto()  # 设置保存
    SETTINGS_LOADED = auto()  # 设置加载

    # 系统相关事件
    APP_STARTED = auto()  # 应用启动
    APP_STOPPING = auto()  # 应用停止中
    APP_STOPPED = auto()  # 应用已停止
    CAMERA_CONNECTED = auto()  # 摄像头连接
    CAMERA_DISCONNECTED = auto()  # 摄像头断开
    CAMERA_RECONNECTING = auto()  # 摄像头重连中
    ERROR_OCCURRED = auto()  # 发生错误

    # UI 相关事件
    WINDOW_SHOWN = auto()  # 窗口显示
    WINDOW_HIDDEN = auto()  # 窗口隐藏
    TRAY_CLICKED = auto()  # 托盘点击

    # 插件相关事件
    PLUGIN_LOADED = auto()  # 插件加载
    PLUGIN_UNLOADED = auto()  # 插件卸载
    PLUGIN_ERROR = auto()  # 插件错误


@dataclass
class Event:
    """事件数据类"""

    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    source: Optional[str] = None  # 事件来源
    cancelable: bool = False  # 是否可取消
    _cancelled: bool = field(default=False, repr=False)

    def cancel(self):
        """取消事件（仅对可取消事件有效）"""
        if self.cancelable:
            self._cancelled = True

    @property
    def cancelled(self) -> bool:
        """事件是否已取消"""
        return self._cancelled

    def get(self, key: str, default: Any = None) -> Any:
        """获取事件数据"""
        return self.data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """通过索引获取事件数据"""
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        """检查是否包含某个数据键"""
        return key in self.data


# 事件处理器类型
EventHandler = Callable[[Event], None]


class EventBus:
    """
    事件总线

    实现发布-订阅模式，支持：
    - 同步和异步事件发布
    - 事件优先级
    - 一次性订阅
    - 弱引用订阅（防止内存泄漏）
    """

    def __init__(self):
        self._subscribers: Dict[EventType, List[tuple]] = {}
        self._once_subscribers: Dict[EventType, List[tuple]] = {}
        self._lock = threading.RLock()
        self._event_history: List[Event] = []
        self._history_size = 100  # 保留最近 100 个事件
        self._enabled = True

    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
        priority: int = 0,
    ) -> Callable:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 事件处理器
            priority: 优先级（数字越大越先执行）

        Returns:
            取消订阅的函数
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            entry = (priority, handler)
            self._subscribers[event_type].append(entry)
            # 按优先级排序（降序）
            self._subscribers[event_type].sort(key=lambda x: -x[0])

        def unsubscribe():
            self._unsubscribe(event_type, handler)

        return unsubscribe

    def subscribe_once(
        self,
        event_type: EventType,
        handler: EventHandler,
        priority: int = 0,
    ) -> Callable:
        """
        订阅一次性事件（触发后自动取消订阅）

        Args:
            event_type: 事件类型
            handler: 事件处理器
            priority: 优先级

        Returns:
            取消订阅的函数
        """
        with self._lock:
            if event_type not in self._once_subscribers:
                self._once_subscribers[event_type] = []

            entry = (priority, handler)
            self._once_subscribers[event_type].append(entry)
            self._once_subscribers[event_type].sort(key=lambda x: -x[0])

        def unsubscribe():
            self._unsubscribe_once(event_type, handler)

        return unsubscribe

    def _unsubscribe(self, event_type: EventType, handler: EventHandler):
        """取消订阅"""
        with self._lock:
            if event_type in self._subscribers:
                self._subscribers[event_type] = [
                    (p, h) for p, h in self._subscribers[event_type] if h != handler
                ]

    def _unsubscribe_once(self, event_type: EventType, handler: EventHandler):
        """取消一次性订阅"""
        with self._lock:
            if event_type in self._once_subscribers:
                self._once_subscribers[event_type] = [
                    (p, h)
                    for p, h in self._once_subscribers[event_type]
                    if h != handler
                ]

    def publish(self, event: Event) -> bool:
        """
        发布事件（同步）

        Args:
            event: 事件对象

        Returns:
            事件是否被处理（未被取消）
        """
        if not self._enabled:
            return False

        # 记录事件历史
        self._record_event(event)

        handlers_to_call = []

        with self._lock:
            # 收集常规订阅者
            if event.type in self._subscribers:
                handlers_to_call.extend(self._subscribers[event.type])

            # 收集一次性订阅者
            if event.type in self._once_subscribers:
                handlers_to_call.extend(self._once_subscribers[event.type])
                # 清空一次性订阅
                self._once_subscribers[event.type] = []

        # 按优先级排序
        handlers_to_call.sort(key=lambda x: -x[0])

        # 调用处理器
        for priority, handler in handlers_to_call:
            if event.cancelled:
                break
            try:
                handler(event)
            except Exception as e:
                # 记录错误但不中断其他处理器
                self._handle_error(event, handler, e)

        return not event.cancelled

    def publish_async(self, event: Event, callback: Callable[[bool], None] = None):
        """
        异步发布事件

        Args:
            event: 事件对象
            callback: 完成回调，参数为事件是否被处理
        """

        def _publish():
            result = self.publish(event)
            if callback:
                callback(result)

        thread = threading.Thread(target=_publish, daemon=True)
        thread.start()

    def emit(self, event_type: EventType, **data) -> bool:
        """
        便捷方法：发布事件

        Args:
            event_type: 事件类型
            **data: 事件数据

        Returns:
            事件是否被处理
        """
        event = Event(type=event_type, data=data)
        return self.publish(event)

    def _record_event(self, event: Event):
        """记录事件到历史"""
        with self._lock:
            self._event_history.append(event)
            # 限制历史大小
            if len(self._event_history) > self._history_size:
                self._event_history = self._event_history[-self._history_size :]

    def _handle_error(self, event: Event, handler: EventHandler, error: Exception):
        """处理事件处理器中的错误"""
        # 发布错误事件（避免递归）
        if event.type != EventType.ERROR_OCCURRED:
            error_event = Event(
                type=EventType.ERROR_OCCURRED,
                data={
                    "original_event": event,
                    "handler": str(handler),
                    "error": str(error),
                    "error_type": type(error).__name__,
                },
            )
            # 直接调用错误处理器，不通过 publish 防止递归
            with self._lock:
                if EventType.ERROR_OCCURRED in self._subscribers:
                    for priority, h in self._subscribers[EventType.ERROR_OCCURRED]:
                        try:
                            h(error_event)
                        except Exception:
                            pass  # 忽略错误处理器中的错误

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 10,
    ) -> List[Event]:
        """
        获取事件历史

        Args:
            event_type: 过滤特定类型的事件
            limit: 返回数量限制

        Returns:
            事件列表（最新的在前）
        """
        with self._lock:
            history = self._event_history.copy()

        if event_type:
            history = [e for e in history if e.type == event_type]

        return list(reversed(history[-limit:]))

    def clear_history(self):
        """清除事件历史"""
        with self._lock:
            self._event_history.clear()

    def clear_subscribers(self, event_type: Optional[EventType] = None):
        """
        清除订阅者

        Args:
            event_type: 要清除的事件类型，如果为 None 则清除所有
        """
        with self._lock:
            if event_type:
                self._subscribers.pop(event_type, None)
                self._once_subscribers.pop(event_type, None)
            else:
                self._subscribers.clear()
                self._once_subscribers.clear()

    def get_subscriber_count(self, event_type: Optional[EventType] = None) -> int:
        """
        获取订阅者数量

        Args:
            event_type: 事件类型，如果为 None 则返回总数

        Returns:
            订阅者数量
        """
        with self._lock:
            if event_type:
                regular = len(self._subscribers.get(event_type, []))
                once = len(self._once_subscribers.get(event_type, []))
                return regular + once
            else:
                total = sum(len(h) for h in self._subscribers.values())
                total += sum(len(h) for h in self._once_subscribers.values())
                return total

    def enable(self):
        """启用事件总线"""
        self._enabled = True

    def disable(self):
        """禁用事件总线"""
        self._enabled = False

    @property
    def enabled(self) -> bool:
        """事件总线是否启用"""
        return self._enabled


# 全局事件总线实例
_global_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus


def subscribe(
    event_type: EventType,
    handler: EventHandler,
    priority: int = 0,
) -> Callable:
    """便捷函数：订阅全局事件总线"""
    return get_event_bus().subscribe(event_type, handler, priority)


def publish(event: Event) -> bool:
    """便捷函数：发布到全局事件总线"""
    return get_event_bus().publish(event)


def emit(event_type: EventType, **data) -> bool:
    """便捷函数：发布事件到全局事件总线"""
    return get_event_bus().emit(event_type, **data)


# 装饰器
def on(event_type: EventType, priority: int = 0):
    """
    事件处理器装饰器

    Example:
        >>> @on(EventType.GESTURE_DETECTED)
        ... def handle_gesture(event: Event):
        ...     print(f"Detected: {event.data}")
    """

    def decorator(func: EventHandler) -> EventHandler:
        get_event_bus().subscribe(event_type, func, priority)
        return func

    return decorator
