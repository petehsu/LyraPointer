"""手势识别模块"""

from .detector import GestureDetector
from .gestures import ActionType, Gesture, GestureType
from .mapper import GestureMapper
from .recorder import (
    GestureFrame,
    GestureRecorder,
    GestureRecording,
    RecordingManager,
    RecordingState,
    get_gesture_recorder,
)

__all__ = [
    # Core classes
    "GestureDetector",
    "Gesture",
    "GestureType",
    "ActionType",
    "GestureMapper",
    # Recorder classes
    "GestureRecorder",
    "GestureRecording",
    "GestureFrame",
    "RecordingManager",
    "RecordingState",
    "get_gesture_recorder",
]
