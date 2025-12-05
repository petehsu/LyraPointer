"""
LyraPointer 事件系统单元测试

测试事件总线、订阅、发布等功能。
"""

import threading
import time
from unittest.mock import MagicMock

import pytest

# conftest.py 已经设置了正确的导入路径
from src.core.events import (
    Event,
    EventBus,
    EventType,
    emit,
    get_event_bus,
    on,
    publish,
    subscribe,
)


class TestEventType:
    """测试事件类型枚举"""

    def test_event_types_exist(self):
        """确认所有预期的事件类型都存在"""
        expected_types = [
            "GESTURE_DETECTED",
            "GESTURE_CHANGED",
            "HAND_DETECTED",
            "HAND_LOST",
            "CURSOR_MOVED",
            "CLICK_PERFORMED",
            "STATE_CHANGED",
            "PAUSE_TOGGLED",
            "SETTINGS_CHANGED",
            "APP_STARTED",
            "APP_STOPPED",
            "ERROR_OCCURRED",
        ]
        for type_name in expected_types:
            assert hasattr(EventType, type_name), f"Missing EventType.{type_name}"

    def test_event_types_are_unique(self):
        """确认所有事件类型值唯一"""
        values = [e.value for e in EventType]
        assert len(values) == len(set(values))


class TestEvent:
    """测试 Event 数据类"""

    def test_event_creation(self):
        """测试事件创建"""
        event = Event(type=EventType.GESTURE_DETECTED)

        assert event.type == EventType.GESTURE_DETECTED
        assert event.data == {}
        assert event.timestamp > 0
        assert event.source is None
        assert event.cancelable is False
        assert event.cancelled is False

    def test_event_with_data(self):
        """测试带数据的事件"""
        event = Event(
            type=EventType.CURSOR_MOVED,
            data={"x": 100, "y": 200},
            source="mouse_controller",
        )

        assert event.data["x"] == 100
        assert event.data["y"] == 200
        assert event.source == "mouse_controller"

    def test_event_get_method(self):
        """测试 get 方法"""
        event = Event(
            type=EventType.CLICK_PERFORMED,
            data={"button": "left", "count": 2},
        )

        assert event.get("button") == "left"
        assert event.get("count") == 2
        assert event.get("nonexistent") is None
        assert event.get("nonexistent", "default") == "default"

    def test_event_getitem(self):
        """测试索引访问"""
        event = Event(
            type=EventType.STATE_CHANGED,
            data={"old_state": "idle", "new_state": "pointing"},
        )

        assert event["old_state"] == "idle"
        assert event["new_state"] == "pointing"

        with pytest.raises(KeyError):
            _ = event["nonexistent"]

    def test_event_contains(self):
        """测试 in 操作符"""
        event = Event(
            type=EventType.SETTINGS_CHANGED,
            data={"key": "sensitivity", "value": 1.5},
        )

        assert "key" in event
        assert "value" in event
        assert "nonexistent" not in event

    def test_event_cancel(self):
        """测试事件取消"""
        # 不可取消的事件
        event1 = Event(type=EventType.APP_STARTED, cancelable=False)
        event1.cancel()
        assert event1.cancelled is False

        # 可取消的事件
        event2 = Event(type=EventType.APP_STARTED, cancelable=True)
        event2.cancel()
        assert event2.cancelled is True


class TestEventBus:
    """测试 EventBus"""

    @pytest.fixture
    def bus(self):
        """创建新的事件总线实例"""
        return EventBus()

    def test_subscribe(self, bus):
        """测试订阅功能"""
        handler = MagicMock()

        unsubscribe = bus.subscribe(EventType.GESTURE_DETECTED, handler)

        assert callable(unsubscribe)
        assert bus.get_subscriber_count(EventType.GESTURE_DETECTED) == 1

    def test_unsubscribe(self, bus):
        """测试取消订阅"""
        handler = MagicMock()

        unsubscribe = bus.subscribe(EventType.GESTURE_DETECTED, handler)
        unsubscribe()

        assert bus.get_subscriber_count(EventType.GESTURE_DETECTED) == 0

    def test_publish_event(self, bus):
        """测试发布事件"""
        handler = MagicMock()
        bus.subscribe(EventType.CLICK_PERFORMED, handler)

        event = Event(type=EventType.CLICK_PERFORMED, data={"button": "left"})
        result = bus.publish(event)

        assert result is True
        handler.assert_called_once_with(event)

    def test_publish_to_multiple_subscribers(self, bus):
        """测试向多个订阅者发布"""
        handler1 = MagicMock()
        handler2 = MagicMock()
        handler3 = MagicMock()

        bus.subscribe(EventType.STATE_CHANGED, handler1)
        bus.subscribe(EventType.STATE_CHANGED, handler2)
        bus.subscribe(EventType.STATE_CHANGED, handler3)

        event = Event(type=EventType.STATE_CHANGED)
        bus.publish(event)

        handler1.assert_called_once()
        handler2.assert_called_once()
        handler3.assert_called_once()

    def test_emit_convenience_method(self, bus):
        """测试 emit 便捷方法"""
        handler = MagicMock()
        bus.subscribe(EventType.HAND_DETECTED, handler)

        bus.emit(EventType.HAND_DETECTED, hand_id=1, confidence=0.95)

        handler.assert_called_once()
        event = handler.call_args[0][0]
        assert event.type == EventType.HAND_DETECTED
        assert event.data["hand_id"] == 1
        assert event.data["confidence"] == 0.95

    def test_subscribe_once(self, bus):
        """测试一次性订阅"""
        handler = MagicMock()
        bus.subscribe_once(EventType.APP_STARTED, handler)

        # 第一次发布
        bus.emit(EventType.APP_STARTED)
        assert handler.call_count == 1

        # 第二次发布，不应该再调用
        bus.emit(EventType.APP_STARTED)
        assert handler.call_count == 1

    def test_subscriber_priority(self, bus):
        """测试订阅者优先级"""
        call_order = []

        def handler_low(event):
            call_order.append("low")

        def handler_high(event):
            call_order.append("high")

        def handler_medium(event):
            call_order.append("medium")

        bus.subscribe(EventType.GESTURE_CHANGED, handler_low, priority=0)
        bus.subscribe(EventType.GESTURE_CHANGED, handler_high, priority=10)
        bus.subscribe(EventType.GESTURE_CHANGED, handler_medium, priority=5)

        bus.emit(EventType.GESTURE_CHANGED)

        assert call_order == ["high", "medium", "low"]

    def test_cancelable_event(self, bus):
        """测试可取消事件"""
        call_order = []

        def handler_cancels(event):
            call_order.append("canceler")
            event.cancel()

        def handler_after(event):
            call_order.append("after")

        bus.subscribe(EventType.CLICK_PERFORMED, handler_cancels, priority=10)
        bus.subscribe(EventType.CLICK_PERFORMED, handler_after, priority=0)

        event = Event(type=EventType.CLICK_PERFORMED, cancelable=True)
        result = bus.publish(event)

        assert result is False  # 事件被取消
        assert call_order == ["canceler"]  # 第二个处理器不会被调用

    def test_handler_exception_doesnt_break_others(self, bus):
        """测试处理器异常不影响其他处理器"""
        handler1 = MagicMock(side_effect=Exception("Handler 1 failed"))
        handler2 = MagicMock()

        bus.subscribe(EventType.ERROR_OCCURRED, handler1, priority=10)
        bus.subscribe(EventType.ERROR_OCCURRED, handler2, priority=0)

        # 不应该抛出异常
        bus.emit(EventType.ERROR_OCCURRED)

        # 第二个处理器仍然应该被调用
        handler2.assert_called_once()

    def test_event_history(self, bus):
        """测试事件历史"""
        bus.emit(EventType.APP_STARTED)
        bus.emit(EventType.GESTURE_DETECTED, gesture="pointer")
        bus.emit(EventType.CLICK_PERFORMED, button="left")

        history = bus.get_history(limit=10)

        assert len(history) == 3
        # 最新的在前
        assert history[0].type == EventType.CLICK_PERFORMED
        assert history[1].type == EventType.GESTURE_DETECTED
        assert history[2].type == EventType.APP_STARTED

    def test_event_history_filter_by_type(self, bus):
        """测试按类型过滤事件历史"""
        bus.emit(EventType.APP_STARTED)
        bus.emit(EventType.GESTURE_DETECTED)
        bus.emit(EventType.GESTURE_DETECTED)
        bus.emit(EventType.CLICK_PERFORMED)

        history = bus.get_history(event_type=EventType.GESTURE_DETECTED)

        assert len(history) == 2
        assert all(e.type == EventType.GESTURE_DETECTED for e in history)

    def test_clear_history(self, bus):
        """测试清除历史"""
        bus.emit(EventType.APP_STARTED)
        bus.emit(EventType.GESTURE_DETECTED)

        bus.clear_history()

        assert len(bus.get_history()) == 0

    def test_clear_subscribers(self, bus):
        """测试清除订阅者"""
        bus.subscribe(EventType.APP_STARTED, MagicMock())
        bus.subscribe(EventType.GESTURE_DETECTED, MagicMock())

        bus.clear_subscribers(EventType.APP_STARTED)

        assert bus.get_subscriber_count(EventType.APP_STARTED) == 0
        assert bus.get_subscriber_count(EventType.GESTURE_DETECTED) == 1

        bus.clear_subscribers()  # 清除所有
        assert bus.get_subscriber_count() == 0

    def test_enable_disable(self, bus):
        """测试启用/禁用事件总线"""
        handler = MagicMock()
        bus.subscribe(EventType.CLICK_PERFORMED, handler)

        assert bus.enabled is True

        bus.disable()
        assert bus.enabled is False

        bus.emit(EventType.CLICK_PERFORMED)
        handler.assert_not_called()

        bus.enable()
        bus.emit(EventType.CLICK_PERFORMED)
        handler.assert_called_once()

    def test_get_subscriber_count(self, bus):
        """测试获取订阅者数量"""
        assert bus.get_subscriber_count() == 0

        bus.subscribe(EventType.APP_STARTED, MagicMock())
        bus.subscribe(EventType.APP_STARTED, MagicMock())
        bus.subscribe(EventType.GESTURE_DETECTED, MagicMock())

        assert bus.get_subscriber_count() == 3
        assert bus.get_subscriber_count(EventType.APP_STARTED) == 2
        assert bus.get_subscriber_count(EventType.GESTURE_DETECTED) == 1
        assert bus.get_subscriber_count(EventType.CLICK_PERFORMED) == 0


class TestAsyncPublish:
    """测试异步发布"""

    @pytest.fixture
    def bus(self):
        return EventBus()

    def test_publish_async(self, bus):
        """测试异步发布"""
        handler = MagicMock()
        bus.subscribe(EventType.GESTURE_DETECTED, handler)

        event = Event(type=EventType.GESTURE_DETECTED)
        completed = threading.Event()

        def callback(result):
            completed.set()

        bus.publish_async(event, callback=callback)

        # 等待异步完成
        assert completed.wait(timeout=1.0)
        handler.assert_called_once()

    def test_publish_async_without_callback(self, bus):
        """测试无回调的异步发布"""
        handler = MagicMock()
        bus.subscribe(EventType.APP_STARTED, handler)

        event = Event(type=EventType.APP_STARTED)
        bus.publish_async(event)

        # 等待一小段时间让异步执行完成
        time.sleep(0.1)
        handler.assert_called_once()


class TestGlobalEventBus:
    """测试全局事件总线"""

    def test_get_event_bus_singleton(self):
        """测试获取全局事件总线（单例）"""
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    def test_global_subscribe(self):
        """测试全局订阅函数"""
        handler = MagicMock()

        unsubscribe = subscribe(EventType.HAND_LOST, handler)

        emit(EventType.HAND_LOST)
        handler.assert_called_once()

        unsubscribe()

    def test_global_publish(self):
        """测试全局发布函数"""
        handler = MagicMock()
        bus = get_event_bus()
        bus.subscribe(EventType.CAMERA_CONNECTED, handler)

        event = Event(type=EventType.CAMERA_CONNECTED)
        publish(event)

        handler.assert_called_once()

    def test_global_emit(self):
        """测试全局 emit 函数"""
        handler = MagicMock()
        bus = get_event_bus()
        bus.subscribe(EventType.SCROLL_PERFORMED, handler)

        emit(EventType.SCROLL_PERFORMED, direction="up", amount=3)

        handler.assert_called_once()
        event = handler.call_args[0][0]
        assert event.data["direction"] == "up"


class TestEventDecorator:
    """测试事件装饰器"""

    def test_on_decorator(self):
        """测试 @on 装饰器"""
        call_count = [0]

        @on(EventType.PLUGIN_LOADED)
        def handle_plugin(event: Event):
            call_count[0] += 1

        emit(EventType.PLUGIN_LOADED, plugin_name="test_plugin")

        assert call_count[0] == 1

    def test_on_decorator_with_priority(self):
        """测试带优先级的 @on 装饰器"""
        results = []

        @on(EventType.WINDOW_SHOWN, priority=0)
        def low_priority(event):
            results.append("low")

        @on(EventType.WINDOW_SHOWN, priority=10)
        def high_priority(event):
            results.append("high")

        emit(EventType.WINDOW_SHOWN)

        assert results == ["high", "low"]


class TestThreadSafety:
    """测试线程安全性"""

    @pytest.fixture
    def bus(self):
        return EventBus()

    def test_concurrent_subscribe(self, bus):
        """测试并发订阅"""
        handlers_added = []

        def add_handler(idx):
            handler = MagicMock()
            bus.subscribe(EventType.GESTURE_DETECTED, handler)
            handlers_added.append(handler)

        threads = [threading.Thread(target=add_handler, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert bus.get_subscriber_count(EventType.GESTURE_DETECTED) == 10

    def test_concurrent_publish(self, bus):
        """测试并发发布"""
        call_count = [0]
        lock = threading.Lock()

        def handler(event):
            with lock:
                call_count[0] += 1

        bus.subscribe(EventType.CURSOR_MOVED, handler)

        def publish_events():
            for _ in range(100):
                bus.emit(EventType.CURSOR_MOVED)

        threads = [threading.Thread(target=publish_events) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert call_count[0] == 500


class TestEdgeCases:
    """测试边缘情况"""

    @pytest.fixture
    def bus(self):
        return EventBus()

    def test_publish_with_no_subscribers(self, bus):
        """测试无订阅者时发布"""
        result = bus.emit(EventType.APP_STOPPED)
        assert result is True  # 应该成功（只是没有处理器）

    def test_subscribe_same_handler_twice(self, bus):
        """测试同一处理器订阅两次"""
        handler = MagicMock()

        bus.subscribe(EventType.STATE_CHANGED, handler)
        bus.subscribe(EventType.STATE_CHANGED, handler)

        bus.emit(EventType.STATE_CHANGED)

        # 应该被调用两次
        assert handler.call_count == 2

    def test_unsubscribe_not_subscribed(self, bus):
        """测试取消未订阅的处理器"""
        handler = MagicMock()

        # 这不应该抛出异常
        bus._unsubscribe(EventType.APP_STARTED, handler)

    def test_empty_event_data(self, bus):
        """测试空数据事件"""
        handler = MagicMock()
        bus.subscribe(EventType.PAUSE_TOGGLED, handler)

        event = Event(type=EventType.PAUSE_TOGGLED, data={})
        bus.publish(event)

        handler.assert_called_once()
        assert handler.call_args[0][0].data == {}


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
