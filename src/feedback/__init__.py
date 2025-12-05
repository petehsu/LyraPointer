"""
反馈模块

提供声音、视觉等反馈功能。
"""

from .audio import AudioFeedback, get_audio_feedback

__all__ = [
    "AudioFeedback",
    "get_audio_feedback",
]
