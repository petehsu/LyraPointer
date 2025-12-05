"""
LyraPointer 音频反馈系统

提供声音反馈功能，用于增强用户体验。
"""

import os
import threading
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Dict, Optional

# 尝试导入音频库
_AUDIO_BACKEND = None

try:
    import simpleaudio as sa

    _AUDIO_BACKEND = "simpleaudio"
except ImportError:
    pass

if _AUDIO_BACKEND is None:
    try:
        # 尝试使用 playsound 作为备选
        from playsound import playsound

        _AUDIO_BACKEND = "playsound"
    except ImportError:
        pass

if _AUDIO_BACKEND is None:
    try:
        # Linux 下可以使用系统命令
        import subprocess

        # 检查是否有 paplay (PulseAudio) 或 aplay (ALSA)
        for cmd in ["paplay", "aplay"]:
            try:
                subprocess.run(
                    [cmd, "--help"],
                    capture_output=True,
                    check=False,
                )
                _AUDIO_BACKEND = cmd
                break
            except FileNotFoundError:
                pass
    except Exception:
        pass


class SoundEvent(Enum):
    """声音事件类型"""

    CLICK = auto()  # 点击
    DOUBLE_CLICK = auto()  # 双击
    RIGHT_CLICK = auto()  # 右键
    DRAG_START = auto()  # 拖拽开始
    DRAG_END = auto()  # 拖拽结束
    SCROLL = auto()  # 滚动
    PAUSE = auto()  # 暂停
    RESUME = auto()  # 恢复
    ERROR = auto()  # 错误
    GESTURE_DETECTED = auto()  # 手势检测到
    HAND_LOST = auto()  # 手丢失
    STARTUP = auto()  # 启动
    SHUTDOWN = auto()  # 关闭


@dataclass
class SoundConfig:
    """声音配置"""

    file_path: Optional[str] = None  # 自定义声音文件路径
    frequency: int = 440  # 蜂鸣频率 (Hz)
    duration: float = 0.1  # 时长 (秒)
    volume: float = 0.5  # 音量 (0.0-1.0)
    enabled: bool = True


# 默认声音配置
DEFAULT_SOUNDS: Dict[SoundEvent, SoundConfig] = {
    SoundEvent.CLICK: SoundConfig(frequency=800, duration=0.05),
    SoundEvent.DOUBLE_CLICK: SoundConfig(frequency=1000, duration=0.08),
    SoundEvent.RIGHT_CLICK: SoundConfig(frequency=600, duration=0.05),
    SoundEvent.DRAG_START: SoundConfig(frequency=500, duration=0.1),
    SoundEvent.DRAG_END: SoundConfig(frequency=400, duration=0.1),
    SoundEvent.SCROLL: SoundConfig(frequency=300, duration=0.02),
    SoundEvent.PAUSE: SoundConfig(frequency=200, duration=0.2),
    SoundEvent.RESUME: SoundConfig(frequency=600, duration=0.2),
    SoundEvent.ERROR: SoundConfig(frequency=200, duration=0.3),
    SoundEvent.GESTURE_DETECTED: SoundConfig(frequency=700, duration=0.03),
    SoundEvent.HAND_LOST: SoundConfig(frequency=300, duration=0.15),
    SoundEvent.STARTUP: SoundConfig(frequency=880, duration=0.15),
    SoundEvent.SHUTDOWN: SoundConfig(frequency=440, duration=0.15),
}


class AudioFeedback:
    """
    音频反馈系统

    提供声音反馈功能，支持多种音频后端。

    Example:
        >>> audio = AudioFeedback()
        >>> audio.play(SoundEvent.CLICK)
        >>> audio.enabled = False  # 禁用
    """

    def __init__(
        self,
        enabled: bool = True,
        volume: float = 0.5,
        sounds_dir: Optional[Path] = None,
    ):
        """
        初始化音频反馈系统

        Args:
            enabled: 是否启用音频反馈
            volume: 全局音量 (0.0-1.0)
            sounds_dir: 声音文件目录
        """
        self._enabled = enabled
        self._volume = max(0.0, min(1.0, volume))
        self._sounds_dir = sounds_dir
        self._sounds: Dict[SoundEvent, SoundConfig] = DEFAULT_SOUNDS.copy()
        self._playing = False
        self._lock = threading.Lock()

        # 缓存加载的声音
        self._sound_cache: Dict[str, any] = {}

        # 检查可用的音频后端
        self._backend = _AUDIO_BACKEND

    @property
    def enabled(self) -> bool:
        """是否启用音频反馈"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """设置是否启用音频反馈"""
        self._enabled = value

    @property
    def volume(self) -> float:
        """获取音量"""
        return self._volume

    @volume.setter
    def volume(self, value: float):
        """设置音量 (0.0-1.0)"""
        self._volume = max(0.0, min(1.0, value))

    @property
    def available(self) -> bool:
        """音频系统是否可用"""
        return self._backend is not None

    @property
    def backend(self) -> Optional[str]:
        """获取当前使用的音频后端"""
        return self._backend

    def play(self, event: SoundEvent, async_play: bool = True):
        """
        播放声音

        Args:
            event: 声音事件类型
            async_play: 是否异步播放
        """
        if not self._enabled or not self.available:
            return

        config = self._sounds.get(event)
        if config is None or not config.enabled:
            return

        if async_play:
            thread = threading.Thread(
                target=self._play_sound, args=(event, config), daemon=True
            )
            thread.start()
        else:
            self._play_sound(event, config)

    def _play_sound(self, event: SoundEvent, config: SoundConfig):
        """
        实际播放声音

        Args:
            event: 声音事件
            config: 声音配置
        """
        with self._lock:
            if self._playing:
                return
            self._playing = True

        try:
            # 如果有自定义声音文件
            if config.file_path and os.path.exists(config.file_path):
                self._play_file(config.file_path)
            # 检查默认声音文件
            elif self._sounds_dir:
                sound_file = self._sounds_dir / f"{event.name.lower()}.wav"
                if sound_file.exists():
                    self._play_file(str(sound_file))
                else:
                    self._play_beep(config)
            else:
                self._play_beep(config)
        except Exception:
            pass  # 静默处理播放错误
        finally:
            with self._lock:
                self._playing = False

    def _play_file(self, file_path: str):
        """播放声音文件"""
        if self._backend == "simpleaudio":
            try:
                import simpleaudio as sa

                # 尝试从缓存获取
                if file_path in self._sound_cache:
                    wave_obj = self._sound_cache[file_path]
                else:
                    wave_obj = sa.WaveObject.from_wave_file(file_path)
                    self._sound_cache[file_path] = wave_obj

                play_obj = wave_obj.play()
                play_obj.wait_done()
            except Exception:
                pass

        elif self._backend == "playsound":
            try:
                from playsound import playsound

                playsound(file_path)
            except Exception:
                pass

        elif self._backend in ("paplay", "aplay"):
            try:
                import subprocess

                subprocess.run(
                    [self._backend, file_path],
                    capture_output=True,
                    timeout=2,
                )
            except Exception:
                pass

    def _play_beep(self, config: SoundConfig):
        """
        播放蜂鸣声

        Args:
            config: 声音配置
        """
        if self._backend == "simpleaudio":
            try:
                import numpy as np
                import simpleaudio as sa

                # 生成正弦波
                sample_rate = 44100
                duration = config.duration
                frequency = config.frequency
                volume = self._volume * config.volume

                t = np.linspace(0, duration, int(sample_rate * duration), False)
                wave = np.sin(frequency * t * 2 * np.pi)

                # 应用音量和淡入淡出
                fade_samples = int(sample_rate * 0.01)  # 10ms 淡入淡出
                if fade_samples > 0 and len(wave) > fade_samples * 2:
                    fade_in = np.linspace(0, 1, fade_samples)
                    fade_out = np.linspace(1, 0, fade_samples)
                    wave[:fade_samples] *= fade_in
                    wave[-fade_samples:] *= fade_out

                # 转换为 16 位整数
                audio = (wave * volume * 32767).astype(np.int16)

                # 播放
                play_obj = sa.play_buffer(audio, 1, 2, sample_rate)
                play_obj.wait_done()

            except ImportError:
                # numpy 不可用，跳过
                pass
            except Exception:
                pass

        elif self._backend in ("paplay", "aplay"):
            # 使用系统 beep（如果可用）
            try:
                import subprocess

                # 尝试使用 beep 命令
                freq = config.frequency
                duration_ms = int(config.duration * 1000)
                subprocess.run(
                    ["beep", "-f", str(freq), "-l", str(duration_ms)],
                    capture_output=True,
                    timeout=2,
                )
            except Exception:
                pass

    def set_sound(self, event: SoundEvent, config: SoundConfig):
        """
        设置声音配置

        Args:
            event: 声音事件
            config: 声音配置
        """
        self._sounds[event] = config

    def set_sound_file(self, event: SoundEvent, file_path: str):
        """
        设置声音文件

        Args:
            event: 声音事件
            file_path: 声音文件路径
        """
        if event in self._sounds:
            self._sounds[event].file_path = file_path
        else:
            self._sounds[event] = SoundConfig(file_path=file_path)

    def enable_sound(self, event: SoundEvent, enabled: bool = True):
        """
        启用/禁用特定声音

        Args:
            event: 声音事件
            enabled: 是否启用
        """
        if event in self._sounds:
            self._sounds[event].enabled = enabled

    def disable_sound(self, event: SoundEvent):
        """
        禁用特定声音

        Args:
            event: 声音事件
        """
        self.enable_sound(event, False)

    def play_click(self):
        """播放点击声音"""
        self.play(SoundEvent.CLICK)

    def play_scroll(self):
        """播放滚动声音"""
        self.play(SoundEvent.SCROLL)

    def play_error(self):
        """播放错误声音"""
        self.play(SoundEvent.ERROR)

    def test(self):
        """测试音频系统"""
        print(f"Audio backend: {self._backend}")
        print(f"Audio available: {self.available}")
        print(f"Audio enabled: {self._enabled}")

        if self.available:
            print("Playing test sound...")
            self.play(SoundEvent.STARTUP, async_play=False)
            print("Done.")
        else:
            print("No audio backend available.")


# 全局音频反馈实例
_global_audio: Optional[AudioFeedback] = None


def get_audio_feedback() -> AudioFeedback:
    """获取全局音频反馈实例"""
    global _global_audio
    if _global_audio is None:
        _global_audio = AudioFeedback()
    return _global_audio


def play_sound(event: SoundEvent):
    """便捷函数：播放声音"""
    get_audio_feedback().play(event)


def enable_audio(enabled: bool = True):
    """便捷函数：启用/禁用音频"""
    get_audio_feedback().enabled = enabled


def set_volume(volume: float):
    """便捷函数：设置音量"""
    get_audio_feedback().volume = volume
