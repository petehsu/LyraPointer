"""
LyraPointer 状态机

管理手势控制的状态转换，提供清晰的状态管理。
"""

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Set, Tuple

from ..gestures.gestures import GestureType


class ControlState(Enum):
    """控制状态枚举"""

    IDLE = auto()  # 空闲状态（无手/握拳）
    POINTING = auto()  # 指针模式
    CLICKING = auto()  # 点击中
    DRAGGING = auto()  # 拖拽中
    SCROLLING = auto()  # 滚动模式
    PAUSED = auto()  # 暂停状态
    CALIBRATING = auto()  # 校准中
    TUTORIAL = auto()  # 教程模式


@dataclass
class StateTransition:
    """状态转换定义"""

    from_state: ControlState
    to_state: ControlState
    trigger: GestureType
    condition: Optional[Callable[[], bool]] = None  # 可选的转换条件
    action: Optional[Callable[[], None]] = None  # 转换时执行的动作


@dataclass
class StateInfo:
    """状态信息"""

    state: ControlState
    entered_at: float = field(default_factory=time.time)
    previous_state: Optional[ControlState] = None
    gesture: Optional[GestureType] = None
    data: Dict = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """当前状态持续时间（秒）"""
        return time.time() - self.entered_at


# 状态变化回调类型
StateChangeCallback = Callable[
    [ControlState, ControlState, Optional[GestureType]], None
]


class GestureStateMachine:
    """
    手势控制状态机

    管理控制状态的转换，确保状态转换的一致性和可预测性。

    Example:
        >>> sm = GestureStateMachine()
        >>> sm.on_state_change(lambda old, new, g: print(f"{old} -> {new}"))
        >>> sm.process_gesture(GestureType.POINTER)
        >>> print(sm.state)  # ControlState.POINTING
    """

    def __init__(self, initial_state: ControlState = ControlState.IDLE):
        self._state = initial_state
        self._previous_state: Optional[ControlState] = None
        self._entered_at = time.time()
        self._current_gesture: Optional[GestureType] = None
        self._state_data: Dict = {}

        # 状态变化回调
        self._callbacks: List[StateChangeCallback] = []

        # 状态进入/退出回调
        self._enter_callbacks: Dict[ControlState, List[Callable]] = {}
        self._exit_callbacks: Dict[ControlState, List[Callable]] = {}

        # 定义状态转换规则
        self._transitions: Dict[Tuple[ControlState, GestureType], ControlState] = {}
        self._setup_default_transitions()

        # 状态历史
        self._history: List[StateInfo] = []
        self._history_size = 50

    def _setup_default_transitions(self):
        """设置默认的状态转换规则"""
        # 从 IDLE 状态的转换
        self._transitions[(ControlState.IDLE, GestureType.POINTER)] = (
            ControlState.POINTING
        )
        self._transitions[(ControlState.IDLE, GestureType.PALM)] = ControlState.PAUSED
        self._transitions[(ControlState.IDLE, GestureType.SCROLL)] = (
            ControlState.SCROLLING
        )

        # 从 POINTING 状态的转换
        self._transitions[(ControlState.POINTING, GestureType.CLICK)] = (
            ControlState.CLICKING
        )
        self._transitions[(ControlState.POINTING, GestureType.RIGHT_CLICK)] = (
            ControlState.CLICKING
        )
        self._transitions[(ControlState.POINTING, GestureType.SCROLL)] = (
            ControlState.SCROLLING
        )
        self._transitions[(ControlState.POINTING, GestureType.FIST)] = ControlState.IDLE
        self._transitions[(ControlState.POINTING, GestureType.NONE)] = ControlState.IDLE
        self._transitions[(ControlState.POINTING, GestureType.PALM)] = (
            ControlState.PAUSED
        )

        # 从 CLICKING 状态的转换
        self._transitions[(ControlState.CLICKING, GestureType.CLICK_HOLD)] = (
            ControlState.DRAGGING
        )
        self._transitions[(ControlState.CLICKING, GestureType.POINTER)] = (
            ControlState.POINTING
        )
        self._transitions[(ControlState.CLICKING, GestureType.NONE)] = ControlState.IDLE
        self._transitions[(ControlState.CLICKING, GestureType.FIST)] = ControlState.IDLE

        # 从 DRAGGING 状态的转换
        self._transitions[(ControlState.DRAGGING, GestureType.POINTER)] = (
            ControlState.POINTING
        )
        self._transitions[(ControlState.DRAGGING, GestureType.NONE)] = ControlState.IDLE
        self._transitions[(ControlState.DRAGGING, GestureType.FIST)] = ControlState.IDLE

        # 从 SCROLLING 状态的转换
        self._transitions[(ControlState.SCROLLING, GestureType.POINTER)] = (
            ControlState.POINTING
        )
        self._transitions[(ControlState.SCROLLING, GestureType.NONE)] = (
            ControlState.IDLE
        )
        self._transitions[(ControlState.SCROLLING, GestureType.FIST)] = (
            ControlState.IDLE
        )
        self._transitions[(ControlState.SCROLLING, GestureType.PALM)] = (
            ControlState.PAUSED
        )

        # 从 PAUSED 状态的转换
        self._transitions[(ControlState.PAUSED, GestureType.PALM)] = ControlState.IDLE
        self._transitions[(ControlState.PAUSED, GestureType.POINTER)] = (
            ControlState.POINTING
        )
        self._transitions[(ControlState.PAUSED, GestureType.FIST)] = ControlState.IDLE

    @property
    def state(self) -> ControlState:
        """获取当前状态"""
        return self._state

    @property
    def previous_state(self) -> Optional[ControlState]:
        """获取前一个状态"""
        return self._previous_state

    @property
    def state_duration(self) -> float:
        """获取当前状态持续时间（秒）"""
        return time.time() - self._entered_at

    @property
    def current_gesture(self) -> Optional[GestureType]:
        """获取当前手势"""
        return self._current_gesture

    @property
    def state_info(self) -> StateInfo:
        """获取当前状态信息"""
        return StateInfo(
            state=self._state,
            entered_at=self._entered_at,
            previous_state=self._previous_state,
            gesture=self._current_gesture,
            data=self._state_data.copy(),
        )

    def process_gesture(
        self, gesture: GestureType
    ) -> Tuple[ControlState, ControlState]:
        """
        处理手势，执行状态转换

        Args:
            gesture: 检测到的手势类型

        Returns:
            (旧状态, 新状态)
        """
        old_state = self._state
        self._current_gesture = gesture

        # 查找转换规则
        key = (self._state, gesture)
        if key in self._transitions:
            new_state = self._transitions[key]
            self._do_transition(old_state, new_state, gesture)
        else:
            # 没有定义的转换，保持当前状态
            new_state = self._state

        return old_state, new_state

    def _do_transition(
        self,
        old_state: ControlState,
        new_state: ControlState,
        gesture: GestureType,
    ):
        """执行状态转换"""
        if old_state == new_state:
            return

        # 记录历史
        self._record_history()

        # 执行退出回调
        self._fire_exit_callbacks(old_state)

        # 更新状态
        self._previous_state = old_state
        self._state = new_state
        self._entered_at = time.time()
        self._state_data.clear()

        # 执行进入回调
        self._fire_enter_callbacks(new_state)

        # 执行状态变化回调
        for callback in self._callbacks:
            try:
                callback(old_state, new_state, gesture)
            except Exception:
                pass  # 忽略回调错误

    def force_state(self, state: ControlState, gesture: Optional[GestureType] = None):
        """
        强制设置状态（跳过转换规则）

        Args:
            state: 目标状态
            gesture: 关联的手势
        """
        old_state = self._state
        self._do_transition(old_state, state, gesture)

    def set_transition(
        self,
        from_state: ControlState,
        gesture: GestureType,
        to_state: ControlState,
    ):
        """
        设置/覆盖转换规则

        Args:
            from_state: 源状态
            gesture: 触发手势
            to_state: 目标状态
        """
        self._transitions[(from_state, gesture)] = to_state

    def remove_transition(self, from_state: ControlState, gesture: GestureType):
        """
        移除转换规则

        Args:
            from_state: 源状态
            gesture: 触发手势
        """
        key = (from_state, gesture)
        if key in self._transitions:
            del self._transitions[key]

    def on_state_change(self, callback: StateChangeCallback) -> Callable:
        """
        注册状态变化回调

        Args:
            callback: 回调函数 (old_state, new_state, gesture) -> None

        Returns:
            取消注册的函数
        """
        self._callbacks.append(callback)

        def unsubscribe():
            if callback in self._callbacks:
                self._callbacks.remove(callback)

        return unsubscribe

    def on_enter(self, state: ControlState, callback: Callable) -> Callable:
        """
        注册进入状态回调

        Args:
            state: 目标状态
            callback: 回调函数

        Returns:
            取消注册的函数
        """
        if state not in self._enter_callbacks:
            self._enter_callbacks[state] = []
        self._enter_callbacks[state].append(callback)

        def unsubscribe():
            if (
                state in self._enter_callbacks
                and callback in self._enter_callbacks[state]
            ):
                self._enter_callbacks[state].remove(callback)

        return unsubscribe

    def on_exit(self, state: ControlState, callback: Callable) -> Callable:
        """
        注册退出状态回调

        Args:
            state: 目标状态
            callback: 回调函数

        Returns:
            取消注册的函数
        """
        if state not in self._exit_callbacks:
            self._exit_callbacks[state] = []
        self._exit_callbacks[state].append(callback)

        def unsubscribe():
            if (
                state in self._exit_callbacks
                and callback in self._exit_callbacks[state]
            ):
                self._exit_callbacks[state].remove(callback)

        return unsubscribe

    def _fire_enter_callbacks(self, state: ControlState):
        """触发进入状态回调"""
        if state in self._enter_callbacks:
            for callback in self._enter_callbacks[state]:
                try:
                    callback()
                except Exception:
                    pass

    def _fire_exit_callbacks(self, state: ControlState):
        """触发退出状态回调"""
        if state in self._exit_callbacks:
            for callback in self._exit_callbacks[state]:
                try:
                    callback()
                except Exception:
                    pass

    def _record_history(self):
        """记录状态历史"""
        info = self.state_info
        self._history.append(info)
        if len(self._history) > self._history_size:
            self._history = self._history[-self._history_size :]

    def get_history(self, limit: int = 10) -> List[StateInfo]:
        """
        获取状态历史

        Args:
            limit: 返回数量限制

        Returns:
            状态历史列表（最新的在后）
        """
        return self._history[-limit:]

    def clear_history(self):
        """清除状态历史"""
        self._history.clear()

    def reset(self, initial_state: ControlState = ControlState.IDLE):
        """
        重置状态机

        Args:
            initial_state: 初始状态
        """
        self._previous_state = self._state
        self._state = initial_state
        self._entered_at = time.time()
        self._current_gesture = None
        self._state_data.clear()

    def set_state_data(self, key: str, value):
        """设置状态数据"""
        self._state_data[key] = value

    def get_state_data(self, key: str, default=None):
        """获取状态数据"""
        return self._state_data.get(key, default)

    def is_in_state(self, *states: ControlState) -> bool:
        """
        检查是否处于指定状态之一

        Args:
            *states: 要检查的状态

        Returns:
            是否处于指定状态之一
        """
        return self._state in states

    def can_transition_to(self, gesture: GestureType) -> bool:
        """
        检查是否可以通过指定手势进行转换

        Args:
            gesture: 手势类型

        Returns:
            是否可以转换
        """
        return (self._state, gesture) in self._transitions

    def get_possible_transitions(self) -> List[Tuple[GestureType, ControlState]]:
        """
        获取当前状态下所有可能的转换

        Returns:
            [(手势, 目标状态), ...]
        """
        result = []
        for (state, gesture), target in self._transitions.items():
            if state == self._state:
                result.append((gesture, target))
        return result

    def __str__(self) -> str:
        return f"GestureStateMachine(state={self._state.name}, duration={self.state_duration:.2f}s)"

    def __repr__(self) -> str:
        return (
            f"GestureStateMachine("
            f"state={self._state}, "
            f"previous={self._previous_state}, "
            f"gesture={self._current_gesture})"
        )
