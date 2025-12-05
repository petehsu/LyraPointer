"""
LyraPointer 手势录制器

录制和回放手势序列，用于宏录制和自动化操作。
"""

import json
import threading
import time
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .gestures import Gesture, GestureType


class RecordingState(Enum):
    """录制状态"""

    IDLE = auto()  # 空闲
    RECORDING = auto()  # 录制中
    PAUSED = auto()  # 暂停
    PLAYING = auto()  # 回放中


@dataclass
class GestureFrame:
    """手势帧数据"""

    timestamp: float  # 相对时间戳（秒）
    gesture_type: str  # 手势类型名称
    position: Optional[Tuple[float, float]] = None  # 归一化坐标 (0-1)
    screen_position: Optional[Tuple[int, int]] = None  # 屏幕像素坐标
    data: Dict[str, Any] = field(default_factory=dict)  # 附加数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "gesture_type": self.gesture_type,
            "position": self.position,
            "screen_position": self.screen_position,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GestureFrame":
        """从字典创建"""
        return cls(
            timestamp=data["timestamp"],
            gesture_type=data["gesture_type"],
            position=tuple(data["position"]) if data.get("position") else None,
            screen_position=(
                tuple(data["screen_position"]) if data.get("screen_position") else None
            ),
            data=data.get("data", {}),
        )


@dataclass
class GestureRecording:
    """手势录制数据"""

    name: str = "Untitled Recording"
    description: str = ""
    created_at: float = field(default_factory=time.time)
    duration: float = 0.0
    frames: List[GestureFrame] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "duration": self.duration,
            "frames": [f.to_dict() for f in self.frames],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GestureRecording":
        """从字典创建"""
        return cls(
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            created_at=data.get("created_at", time.time()),
            duration=data.get("duration", 0.0),
            frames=[GestureFrame.from_dict(f) for f in data.get("frames", [])],
            metadata=data.get("metadata", {}),
        )

    def save(self, path: Path):
        """
        保存录制到文件

        Args:
            path: 文件路径
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Path) -> "GestureRecording":
        """
        从文件加载录制

        Args:
            path: 文件路径

        Returns:
            录制数据
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @property
    def frame_count(self) -> int:
        """帧数"""
        return len(self.frames)

    def get_frame_at(self, time_offset: float) -> Optional[GestureFrame]:
        """
        获取指定时间的帧

        Args:
            time_offset: 时间偏移（秒）

        Returns:
            手势帧，如果没有则返回 None
        """
        if not self.frames:
            return None

        # 二分查找
        left, right = 0, len(self.frames) - 1
        while left < right:
            mid = (left + right + 1) // 2
            if self.frames[mid].timestamp <= time_offset:
                left = mid
            else:
                right = mid - 1

        return self.frames[left] if self.frames[left].timestamp <= time_offset else None


# 回调类型
OnRecordCallback = Callable[[GestureFrame], None]
OnPlaybackCallback = Callable[[GestureFrame, float], None]  # (frame, progress)
OnStateChangeCallback = Callable[[RecordingState], None]


class GestureRecorder:
    """
    手势录制器

    支持录制手势序列并回放。

    Example:
        >>> recorder = GestureRecorder()
        >>> recorder.start_recording("My Gesture")
        >>> # ... 进行手势操作 ...
        >>> recorder.record_frame(gesture, position)
        >>> recording = recorder.stop_recording()
        >>> recording.save("my_gesture.json")
        >>>
        >>> # 回放
        >>> recorder.play(recording, on_frame=handle_frame)
    """

    def __init__(self):
        self._state = RecordingState.IDLE
        self._recording: Optional[GestureRecording] = None
        self._start_time: float = 0.0
        self._pause_time: float = 0.0
        self._total_pause_duration: float = 0.0

        # 回放相关
        self._playback_thread: Optional[threading.Thread] = None
        self._playback_stop_event = threading.Event()
        self._playback_speed: float = 1.0

        # 回调
        self._on_record_callbacks: List[OnRecordCallback] = []
        self._on_playback_callbacks: List[OnPlaybackCallback] = []
        self._on_state_change_callbacks: List[OnStateChangeCallback] = []

        # 过滤设置
        self._min_frame_interval: float = 0.016  # 最小帧间隔（约60fps）
        self._last_frame_time: float = 0.0
        self._record_idle: bool = False  # 是否录制空闲手势

    @property
    def state(self) -> RecordingState:
        """获取当前状态"""
        return self._state

    @property
    def is_recording(self) -> bool:
        """是否正在录制"""
        return self._state == RecordingState.RECORDING

    @property
    def is_playing(self) -> bool:
        """是否正在回放"""
        return self._state == RecordingState.PLAYING

    @property
    def current_recording(self) -> Optional[GestureRecording]:
        """获取当前录制"""
        return self._recording

    @property
    def elapsed_time(self) -> float:
        """获取已录制时间（秒）"""
        if self._state == RecordingState.IDLE:
            return 0.0
        elif self._state == RecordingState.PAUSED:
            return self._pause_time - self._start_time - self._total_pause_duration
        else:
            return time.time() - self._start_time - self._total_pause_duration

    def _set_state(self, state: RecordingState):
        """设置状态并触发回调"""
        if self._state != state:
            self._state = state
            for callback in self._on_state_change_callbacks:
                try:
                    callback(state)
                except Exception:
                    pass

    def start_recording(
        self,
        name: str = "Untitled Recording",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        开始录制

        Args:
            name: 录制名称
            description: 描述
            metadata: 附加元数据
        """
        if self._state != RecordingState.IDLE:
            self.stop_recording()

        self._recording = GestureRecording(
            name=name,
            description=description,
            metadata=metadata or {},
        )
        self._start_time = time.time()
        self._pause_time = 0.0
        self._total_pause_duration = 0.0
        self._last_frame_time = 0.0

        self._set_state(RecordingState.RECORDING)

    def stop_recording(self) -> Optional[GestureRecording]:
        """
        停止录制

        Returns:
            录制数据
        """
        if self._state == RecordingState.IDLE:
            return None

        recording = self._recording
        if recording:
            recording.duration = self.elapsed_time

        self._recording = None
        self._set_state(RecordingState.IDLE)

        return recording

    def pause_recording(self):
        """暂停录制"""
        if self._state == RecordingState.RECORDING:
            self._pause_time = time.time()
            self._set_state(RecordingState.PAUSED)

    def resume_recording(self):
        """恢复录制"""
        if self._state == RecordingState.PAUSED:
            self._total_pause_duration += time.time() - self._pause_time
            self._set_state(RecordingState.RECORDING)

    def record_frame(
        self,
        gesture: Gesture,
        position: Optional[Tuple[float, float]] = None,
        screen_position: Optional[Tuple[int, int]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        录制一帧

        Args:
            gesture: 手势对象
            position: 归一化坐标
            screen_position: 屏幕坐标
            data: 附加数据

        Returns:
            是否成功录制
        """
        if self._state != RecordingState.RECORDING or self._recording is None:
            return False

        # 过滤空闲手势
        if not self._record_idle and gesture.type in (
            GestureType.NONE,
            GestureType.FIST,
        ):
            return False

        # 帧率限制
        current_time = time.time()
        if current_time - self._last_frame_time < self._min_frame_interval:
            return False
        self._last_frame_time = current_time

        # 计算相对时间戳
        timestamp = self.elapsed_time

        # 创建帧
        frame = GestureFrame(
            timestamp=timestamp,
            gesture_type=gesture.type.name,
            position=position,
            screen_position=screen_position,
            data=data or {},
        )

        # 添加到录制
        self._recording.frames.append(frame)

        # 触发回调
        for callback in self._on_record_callbacks:
            try:
                callback(frame)
            except Exception:
                pass

        return True

    def play(
        self,
        recording: GestureRecording,
        speed: float = 1.0,
        on_frame: Optional[OnPlaybackCallback] = None,
        on_complete: Optional[Callable[[], None]] = None,
        loop: bool = False,
    ):
        """
        播放录制

        Args:
            recording: 要播放的录制
            speed: 播放速度（1.0 = 正常速度）
            on_frame: 帧回调
            on_complete: 完成回调
            loop: 是否循环播放
        """
        if self._state == RecordingState.PLAYING:
            self.stop_playback()

        self._playback_speed = max(0.1, min(10.0, speed))
        self._playback_stop_event.clear()

        def playback_loop():
            self._set_state(RecordingState.PLAYING)

            while not self._playback_stop_event.is_set():
                start_time = time.time()

                for i, frame in enumerate(recording.frames):
                    if self._playback_stop_event.is_set():
                        break

                    # 计算等待时间
                    target_time = frame.timestamp / self._playback_speed
                    elapsed = time.time() - start_time
                    wait_time = target_time - elapsed

                    if wait_time > 0:
                        # 使用小间隔检查停止事件
                        while wait_time > 0 and not self._playback_stop_event.is_set():
                            sleep_time = min(wait_time, 0.01)
                            time.sleep(sleep_time)
                            wait_time -= sleep_time

                    if self._playback_stop_event.is_set():
                        break

                    # 计算进度
                    progress = (i + 1) / len(recording.frames)

                    # 触发回调
                    if on_frame:
                        try:
                            on_frame(frame, progress)
                        except Exception:
                            pass

                    for callback in self._on_playback_callbacks:
                        try:
                            callback(frame, progress)
                        except Exception:
                            pass

                if not loop:
                    break

            self._set_state(RecordingState.IDLE)

            if on_complete and not self._playback_stop_event.is_set():
                try:
                    on_complete()
                except Exception:
                    pass

        self._playback_thread = threading.Thread(target=playback_loop, daemon=True)
        self._playback_thread.start()

    def stop_playback(self):
        """停止回放"""
        self._playback_stop_event.set()

        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=1.0)

        self._playback_thread = None
        self._set_state(RecordingState.IDLE)

    def on_record(self, callback: OnRecordCallback):
        """
        注册录制帧回调

        Args:
            callback: 回调函数
        """
        self._on_record_callbacks.append(callback)

    def on_playback(self, callback: OnPlaybackCallback):
        """
        注册回放帧回调

        Args:
            callback: 回调函数
        """
        self._on_playback_callbacks.append(callback)

    def on_state_change(self, callback: OnStateChangeCallback):
        """
        注册状态变化回调

        Args:
            callback: 回调函数
        """
        self._on_state_change_callbacks.append(callback)

    def set_min_frame_interval(self, interval: float):
        """
        设置最小帧间隔

        Args:
            interval: 间隔时间（秒）
        """
        self._min_frame_interval = max(0.001, interval)

    def set_record_idle(self, record: bool):
        """
        设置是否录制空闲手势

        Args:
            record: 是否录制
        """
        self._record_idle = record

    def clear_callbacks(self):
        """清除所有回调"""
        self._on_record_callbacks.clear()
        self._on_playback_callbacks.clear()
        self._on_state_change_callbacks.clear()


class RecordingManager:
    """
    录制管理器

    管理多个录制文件的保存和加载。
    """

    def __init__(self, recordings_dir: Optional[Path] = None):
        """
        初始化录制管理器

        Args:
            recordings_dir: 录制文件目录
        """
        if recordings_dir is None:
            recordings_dir = (
                Path.home() / ".local" / "share" / "lyrapointer" / "recordings"
            )

        self._recordings_dir = Path(recordings_dir)
        self._recordings_dir.mkdir(parents=True, exist_ok=True)

    @property
    def recordings_dir(self) -> Path:
        """获取录制目录"""
        return self._recordings_dir

    def save_recording(
        self, recording: GestureRecording, filename: Optional[str] = None
    ) -> Path:
        """
        保存录制

        Args:
            recording: 录制数据
            filename: 文件名（不含扩展名）

        Returns:
            保存的文件路径
        """
        if filename is None:
            # 使用时间戳生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in recording.name if c.isalnum() or c in " _-")
            filename = f"{timestamp}_{safe_name[:30]}"

        filename = filename.replace(" ", "_")
        if not filename.endswith(".json"):
            filename += ".json"

        path = self._recordings_dir / filename
        recording.save(path)

        return path

    def load_recording(self, filename: str) -> GestureRecording:
        """
        加载录制

        Args:
            filename: 文件名

        Returns:
            录制数据
        """
        if not filename.endswith(".json"):
            filename += ".json"

        path = self._recordings_dir / filename
        return GestureRecording.load(path)

    def list_recordings(self) -> List[Tuple[str, GestureRecording]]:
        """
        列出所有录制

        Returns:
            [(文件名, 录制数据), ...]
        """
        recordings = []

        for path in sorted(self._recordings_dir.glob("*.json")):
            try:
                recording = GestureRecording.load(path)
                recordings.append((path.name, recording))
            except Exception:
                pass

        return recordings

    def delete_recording(self, filename: str) -> bool:
        """
        删除录制

        Args:
            filename: 文件名

        Returns:
            是否成功
        """
        if not filename.endswith(".json"):
            filename += ".json"

        path = self._recordings_dir / filename

        if path.exists():
            path.unlink()
            return True

        return False

    def get_recording_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        获取录制信息（不加载完整数据）

        Args:
            filename: 文件名

        Returns:
            录制信息
        """
        try:
            recording = self.load_recording(filename)
            return {
                "name": recording.name,
                "description": recording.description,
                "created_at": recording.created_at,
                "duration": recording.duration,
                "frame_count": recording.frame_count,
            }
        except Exception:
            return None


# 全局录制器实例
_global_recorder: Optional[GestureRecorder] = None


def get_gesture_recorder() -> GestureRecorder:
    """获取全局录制器实例"""
    global _global_recorder
    if _global_recorder is None:
        _global_recorder = GestureRecorder()
    return _global_recorder
