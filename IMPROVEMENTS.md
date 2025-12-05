# LyraPointer 改进建议

本文档整理了对 LyraPointer 项目的全面改进建议，涵盖架构、性能、功能、用户体验等方面。

---

## 目录

1. [立即可修复的问题](#1-立即可修复的问题)
2. [架构优化](#2-架构优化)
3. [性能优化](#3-性能优化)
4. [功能增强](#4-功能增强)
5. [用户体验改进](#5-用户体验改进)
6. [兼容性改进](#6-兼容性改进)
7. [代码质量](#7-代码质量)
8. [测试建议](#8-测试建议)
9. [文档完善](#9-文档完善)

---

## 1. 立即可修复的问题

### 1.1 ~~模块导出缺失~~ ✅ 已修复

`src/ui/__init__.py` 缺少 `SettingsWindow` 导出。

### 1.2 ~~Wayland 检测~~ ✅ 已修复

添加 Wayland 环境检测和用户提示。

### 1.3 系统托盘错误处理

当前托盘初始化失败时会打印异常堆栈，建议静默处理：

```python
# src/ui/tray.py
def start(self):
    if not HAS_TRAY:
        return
    
    try:
        # ... 初始化代码
        self._thread = threading.Thread(target=self._safe_run, daemon=True)
        self._thread.start()
    except Exception as e:
        print(f"System tray unavailable: {e}")

def _safe_run(self):
    """安全运行托盘（捕获所有异常）"""
    try:
        self._icon.run()
    except Exception:
        pass  # 静默失败
```

### 1.4 摄像头异常处理

摄像头可能在运行中断开，需要添加重连机制：

```python
def _main_loop(self):
    consecutive_failures = 0
    max_failures = 30  # 约 1 秒
    
    while self._is_running:
        ret, frame = self.cap.read()
        if not ret:
            consecutive_failures += 1
            if consecutive_failures > max_failures:
                print("Camera disconnected, attempting reconnect...")
                if self._reconnect_camera():
                    consecutive_failures = 0
                else:
                    break
            continue
        consecutive_failures = 0
        # ... 正常处理
```

---

## 2. 架构优化

### 2.1 引入事件系统

当前手势检测和动作执行耦合在 `main.py`，建议使用发布-订阅模式解耦：

```python
# src/core/events.py
from dataclasses import dataclass
from typing import Callable, Dict, List
from enum import Enum, auto

class EventType(Enum):
    GESTURE_DETECTED = auto()
    HAND_LOST = auto()
    PAUSE_TOGGLED = auto()
    SETTINGS_CHANGED = auto()

@dataclass
class Event:
    type: EventType
    data: dict = None

class EventBus:
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
    
    def subscribe(self, event_type: EventType, callback: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def publish(self, event: Event):
        for callback in self._subscribers.get(event.type, []):
            callback(event)
```

### 2.2 状态机模式

用状态机管理复杂的手势状态转换：

```python
# src/gestures/state_machine.py
from enum import Enum, auto

class ControlState(Enum):
    IDLE = auto()        # 无手/握拳
    POINTING = auto()    # 指针模式
    CLICKING = auto()    # 点击中
    DRAGGING = auto()    # 拖拽中
    SCROLLING = auto()   # 滚动模式
    PAUSED = auto()      # 暂停

class GestureStateMachine:
    def __init__(self):
        self.state = ControlState.IDLE
        self._transitions = {
            (ControlState.IDLE, GestureType.POINTER): ControlState.POINTING,
            (ControlState.POINTING, GestureType.CLICK): ControlState.CLICKING,
            (ControlState.CLICKING, GestureType.CLICK_HOLD): ControlState.DRAGGING,
            # ... 更多转换规则
        }
    
    def transition(self, gesture: GestureType) -> tuple[ControlState, ControlState]:
        """返回 (旧状态, 新状态)"""
        old_state = self.state
        new_state = self._transitions.get((self.state, gesture), self.state)
        self.state = new_state
        return old_state, new_state
```

### 2.3 插件系统

支持自定义手势和动作：

```python
# src/plugins/base.py
from abc import ABC, abstractmethod

class GesturePlugin(ABC):
    """手势插件基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass
    
    @abstractmethod
    def detect(self, hand: HandLandmarks) -> Optional[Gesture]:
        """检测自定义手势"""
        pass

class ActionPlugin(ABC):
    """动作插件基类"""
    
    @abstractmethod
    def execute(self, gesture: Gesture, context: dict):
        """执行自定义动作"""
        pass
```

---

## 3. 性能优化

### 3.1 帧处理优化

当前每帧都进行完整处理，可以优化：

```python
# 跳帧处理（在低端硬件上）
def _main_loop(self):
    frame_count = 0
    process_interval = self.settings.process_interval  # 1=每帧, 2=隔帧
    
    while self._is_running:
        ret, frame = self.cap.read()
        frame_count += 1
        
        # 跳帧处理
        if frame_count % process_interval != 0:
            continue
        
        # ... 正常处理
```

### 3.2 多线程优化

将耗时操作移到后台线程：

```python
import queue
import threading

class AsyncProcessor:
    def __init__(self):
        self._frame_queue = queue.Queue(maxsize=2)
        self._result_queue = queue.Queue(maxsize=2)
        self._running = False
    
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
    
    def _process_loop(self):
        while self._running:
            try:
                frame = self._frame_queue.get(timeout=0.1)
                result = self._heavy_processing(frame)
                self._result_queue.put(result)
            except queue.Empty:
                continue
```

### 3.3 减少内存分配

复用数组而不是每帧创建新的：

```python
class HandTracker:
    def __init__(self):
        # 预分配缓冲区
        self._landmarks_buffer = [Point3D(0, 0, 0) for _ in range(21)]
    
    def process(self, frame):
        # 复用缓冲区
        for i, lm in enumerate(hand_landmarks.landmark):
            self._landmarks_buffer[i].x = lm.x
            self._landmarks_buffer[i].y = lm.y
            self._landmarks_buffer[i].z = lm.z
```

### 3.4 GPU 加速选项

MediaPipe 支持 GPU 加速：

```python
# 配置文件新增选项
performance:
  use_gpu: true  # 启用 GPU 加速

# hand_tracker.py
import mediapipe as mp

self.hands = mp.solutions.hands.Hands(
    static_image_mode=False,
    max_num_hands=max_hands,
    model_complexity=model_complexity,
    min_detection_confidence=detection_confidence,
    min_tracking_confidence=tracking_confidence,
)

# 注：需要安装 mediapipe-gpu 或使用 CUDA 版本
```

---

## 4. 功能增强

### 4.1 多手支持

当前只支持单手，可扩展为双手：

```python
class MultiHandController:
    """双手控制器"""
    
    def process(self, hands: list[HandLandmarks]):
        if len(hands) == 0:
            return
        
        if len(hands) == 1:
            # 单手模式
            self._single_hand_mode(hands[0])
        else:
            # 双手模式
            left_hand = next((h for h in hands if h.handedness == "Left"), None)
            right_hand = next((h for h in hands if h.handedness == "Right"), None)
            self._dual_hand_mode(left_hand, right_hand)
    
    def _dual_hand_mode(self, left: HandLandmarks, right: HandLandmarks):
        """双手手势：缩放、旋转等"""
        if left and right:
            # 计算两手距离变化 -> 缩放
            # 计算两手角度变化 -> 旋转
            pass
```

### 4.2 手势录制与回放

```python
# src/gestures/recorder.py
import json
import time

class GestureRecorder:
    def __init__(self):
        self._recording = []
        self._is_recording = False
    
    def start_recording(self):
        self._recording = []
        self._is_recording = True
        self._start_time = time.time()
    
    def record(self, gesture: Gesture, position: tuple):
        if self._is_recording:
            self._recording.append({
                "time": time.time() - self._start_time,
                "gesture": gesture.type.name,
                "position": position,
            })
    
    def stop_recording(self) -> list:
        self._is_recording = False
        return self._recording
    
    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self._recording, f)
```

### 4.3 自定义手势绑定

支持用户自定义手势触发的操作：

```yaml
# config/gestures.yaml
custom_bindings:
  # 三指捏合 -> 截图
  three_finger_pinch:
    fingers: ["thumb", "index", "middle"]
    action: "hotkey"
    keys: ["ctrl", "shift", "s"]
  
  # 四指上滑 -> 显示桌面
  four_finger_swipe_up:
    fingers: ["index", "middle", "ring", "pinky"]
    direction: "up"
    action: "hotkey"
    keys: ["super", "d"]
```

### 4.4 应用程序特定配置

不同应用使用不同配置：

```yaml
# config/app_profiles.yaml
profiles:
  default:
    sensitivity: 1.5
    scroll_speed: 5
  
  browser:
    match: ["firefox", "chrome", "chromium"]
    sensitivity: 1.2
    scroll_speed: 8
  
  terminal:
    match: ["alacritty", "konsole", "gnome-terminal"]
    sensitivity: 1.0
    gestures:
      three_finger_tap: "paste"  # Ctrl+Shift+V
```

### 4.5 虚拟键盘集成

空中打字功能：

```python
class AirKeyboard:
    """虚拟键盘 - 在空中打字"""
    
    KEYBOARD_LAYOUT = [
        "QWERTYUIOP",
        "ASDFGHJKL",
        "ZXCVBNM",
    ]
    
    def __init__(self):
        self._active = False
        self._hover_key = None
        self._hover_start = None
    
    def detect_key_press(self, finger_pos: tuple) -> Optional[str]:
        """检测手指悬停在哪个键上"""
        # 将手指位置映射到键盘布局
        # 悬停一定时间触发按键
        pass
```

---

## 5. 用户体验改进

### 5.1 首次运行向导

```python
# src/ui/wizard.py
class SetupWizard:
    """首次运行设置向导"""
    
    def run(self):
        steps = [
            self._camera_setup,      # 选择摄像头
            self._calibration,       # 手势校准
            self._sensitivity_test,  # 灵敏度测试
            self._tutorial,          # 手势教程
        ]
        
        for step in steps:
            if not step():
                return False
        return True
    
    def _calibration(self):
        """校准手势阈值"""
        print("请做出捏合手势...")
        # 记录用户的自然捏合距离
        # 自动调整阈值
```

### 5.2 手势教程模式

```python
class GestureTutorial:
    """交互式手势教程"""
    
    LESSONS = [
        {"gesture": "pointer", "instruction": "伸出食指，移动手控制鼠标"},
        {"gesture": "click", "instruction": "将拇指和食指捏在一起进行点击"},
        {"gesture": "scroll", "instruction": "伸出食指和中指，上下移动进行滚动"},
    ]
    
    def start(self):
        for lesson in self.LESSONS:
            self._show_instruction(lesson["instruction"])
            self._wait_for_gesture(lesson["gesture"])
            self._show_success()
```

### 5.3 声音/触觉反馈

```python
# src/feedback/audio.py
import simpleaudio as sa  # 需要添加依赖

class AudioFeedback:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._sounds = {
            "click": self._load_sound("click.wav"),
            "scroll": self._load_sound("scroll.wav"),
        }
    
    def play(self, sound_name: str):
        if self.enabled and sound_name in self._sounds:
            self._sounds[sound_name].play()
```

### 5.4 可视化改进

```python
# 添加手势预测指示器
def _draw_gesture_prediction(self, frame, gesture, confidence):
    """显示手势预测和置信度"""
    # 圆形进度条显示置信度
    center = (100, 100)
    radius = 40
    angle = int(360 * confidence)
    cv2.ellipse(frame, center, (radius, radius), -90, 0, angle, (0, 255, 0), 3)
    
    # 手势图标
    self._draw_gesture_icon(frame, gesture, center)

# 添加轨迹显示
def _draw_cursor_trail(self, frame, positions: list):
    """显示鼠标轨迹"""
    if len(positions) < 2:
        return
    
    for i in range(1, len(positions)):
        alpha = i / len(positions)  # 渐变透明度
        color = (0, int(255 * alpha), int(255 * (1 - alpha)))
        cv2.line(frame, positions[i-1], positions[i], color, 2)
```

### 5.5 OSD 提示

在屏幕上显示操作提示（不在摄像头窗口）：

```python
# src/ui/osd.py
class OnScreenDisplay:
    """屏幕悬浮提示"""
    
    def show_notification(self, message: str, duration: float = 2.0):
        """显示通知"""
        # 使用 tkinter 创建透明悬浮窗口
        # 或使用 notify-send (Linux)
        pass
    
    def show_gesture_hint(self, gesture: str):
        """显示手势提示图标"""
        pass
```

---

## 6. 兼容性改进

### 6.1 Wayland 支持

使用 `ydotool` 替代 `pyautogui`：

```python
# src/control/wayland_mouse.py
import subprocess

class WaylandMouseController:
    """Wayland 下的鼠标控制器"""
    
    def __init__(self):
        # 检查 ydotool 是否可用
        self._has_ydotool = self._check_ydotool()
    
    def _check_ydotool(self) -> bool:
        try:
            subprocess.run(["ydotool", "--help"], capture_output=True)
            return True
        except FileNotFoundError:
            return False
    
    def move_to(self, x: int, y: int):
        if self._has_ydotool:
            subprocess.run(["ydotool", "mousemove", "-a", str(x), str(y)])
    
    def click(self):
        if self._has_ydotool:
            subprocess.run(["ydotool", "click", "0xC0"])  # 左键点击
```

### 6.2 自动选择后端

```python
# src/control/__init__.py
import os

def get_mouse_controller():
    """根据环境自动选择鼠标控制器"""
    session_type = os.environ.get("XDG_SESSION_TYPE", "x11")
    
    if session_type == "wayland":
        from .wayland_mouse import WaylandMouseController
        controller = WaylandMouseController()
        if controller.available:
            return controller
        print("Warning: ydotool not available, falling back to pyautogui")
    
    from .mouse import MouseController
    return MouseController()
```

### 6.3 跨平台系统托盘

```python
# src/ui/tray.py
import platform

def get_tray_backend():
    """选择最佳托盘后端"""
    system = platform.system()
    
    if system == "Linux":
        # 优先使用 AppIndicator (GNOME/KDE)
        try:
            import gi
            gi.require_version('AppIndicator3', '0.1')
            return "appindicator"
        except:
            pass
    
    return "pystray"  # 默认
```

---

## 7. 代码质量

### 7.1 类型注解完善

```python
# 使用更严格的类型注解
from typing import TypeAlias, Literal

Position: TypeAlias = tuple[float, float]
PixelPosition: TypeAlias = tuple[int, int]
GestureAction: TypeAlias = Literal["click", "scroll", "move", "none"]

def process_gesture(
    gesture: Gesture,
    position: Position,
) -> tuple[GestureAction, Optional[PixelPosition]]:
    ...
```

### 7.2 添加日志系统

```python
# src/utils/logging.py
import logging
from pathlib import Path

def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)
    
    # 文件处理器
    log_dir = Path.home() / ".local" / "share" / "lyrapointer" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "lyrapointer.log")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # 配置根日志器
    logger = logging.getLogger("lyrapointer")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
```

### 7.3 配置验证

```python
# src/config/validator.py
from dataclasses import dataclass
from typing import Any

@dataclass
class ValidationError:
    key: str
    message: str
    value: Any

def validate_config(config: dict) -> list[ValidationError]:
    """验证配置文件"""
    errors = []
    
    # 验证灵敏度范围
    sensitivity = config.get("settings", {}).get("sensitivity", 1.5)
    if not 0.1 <= sensitivity <= 5.0:
        errors.append(ValidationError(
            "settings.sensitivity",
            "灵敏度必须在 0.1-5.0 之间",
            sensitivity
        ))
    
    # 验证控制区域
    zone = config.get("settings", {}).get("control_zone", {})
    if zone.get("x_min", 0) >= zone.get("x_max", 1):
        errors.append(ValidationError(
            "settings.control_zone",
            "x_min 必须小于 x_max",
            zone
        ))
    
    return errors
```

### 7.4 异常处理改进

```python
# src/exceptions.py
class LyraPointerError(Exception):
    """基础异常类"""
    pass

class CameraError(LyraPointerError):
    """摄像头相关错误"""
    pass

class ConfigError(LyraPointerError):
    """配置相关错误"""
    pass

class GestureError(LyraPointerError):
    """手势识别错误"""
    pass

# 使用示例
def _init_camera(self) -> bool:
    try:
        self.cap = cv2.VideoCapture(self.settings.camera_index)
        if not self.cap.isOpened():
            raise CameraError(f"无法打开摄像头 {self.settings.camera_index}")
        return True
    except CameraError as e:
        self.logger.error(str(e))
        return False
```

---

## 8. 测试建议

### 8.1 单元测试

```python
# tests/test_gestures.py
import pytest
from src.gestures.detector import GestureDetector
from src.tracker.hand_tracker import HandLandmarks, Point3D

class TestGestureDetector:
    @pytest.fixture
    def detector(self):
        return GestureDetector()
    
    @pytest.fixture
    def mock_hand_pointing(self):
        """模拟食指指向手势"""
        landmarks = [Point3D(0.5, 0.5, 0) for _ in range(21)]
        # 设置食指伸出
        landmarks[8] = Point3D(0.5, 0.3, 0)  # INDEX_TIP
        landmarks[6] = Point3D(0.5, 0.4, 0)  # INDEX_PIP
        return HandLandmarks(landmarks=landmarks, handedness="Right", score=0.9)
    
    def test_pointer_detection(self, detector, mock_hand_pointing):
        gesture = detector.detect(mock_hand_pointing)
        assert gesture.type == GestureType.POINTER

# tests/test_smoother.py
class TestOneEuroFilter:
    def test_smooth_static_input(self):
        """静态输入应该返回相同值"""
        smoother = Smoother()
        for _ in range(10):
            x, y = smoother.smooth(0.5, 0.5)
        assert abs(x - 0.5) < 0.01
        assert abs(y - 0.5) < 0.01
    
    def test_smooth_jittery_input(self):
        """抖动输入应该被平滑"""
        smoother = Smoother(min_cutoff=0.1, beta=0.01)
        outputs = []
        for i in range(100):
            # 模拟抖动
            jitter = 0.01 * (i % 2 * 2 - 1)
            x, _ = smoother.smooth(0.5 + jitter, 0.5)
            outputs.append(x)
        
        # 输出方差应该小于输入方差
        import numpy as np
        assert np.var(outputs[-50:]) < 0.01 ** 2
```

### 8.2 集成测试

```python
# tests/test_integration.py
class TestLyraPointerIntegration:
    def test_full_pipeline(self, mock_camera, mock_display):
        """测试完整的处理流程"""
        app = LyraPointer()
        app.cap = mock_camera
        
        # 模拟一帧处理
        frame = mock_camera.read()[1]
        gesture, pos = app._process_frame(frame)
        
        assert gesture is not None or pos is None
```

### 8.3 性能测试

```python
# tests/test_performance.py
import time

class TestPerformance:
    def test_frame_processing_time(self):
        """单帧处理时间应该小于 33ms (30fps)"""
        tracker = HandTracker()
        frame = cv2.imread("test_frame.jpg")
        
        times = []
        for _ in range(100):
            start = time.perf_counter()
            tracker.process(frame)
            times.append(time.perf_counter() - start)
        
        avg_time = sum(times) / len(times)
        assert avg_time < 0.033, f"Average processing time: {avg_time*1000:.1f}ms"
```

---

## 9. 文档完善

### 9.1 API 文档

使用 Sphinx 或 MkDocs 生成 API 文档：

```python
# 改进 docstring 格式
class GestureDetector:
    """手势检测器
    
    根据手部关键点判断当前手势类型。
    
    Attributes:
        pinch_threshold: 捏合判定阈值（归一化距离）
        click_hold_frames: 点击需要保持的帧数
        
    Example:
        >>> detector = GestureDetector(pinch_threshold=0.05)
        >>> gesture = detector.detect(hand_landmarks)
        >>> print(gesture.type)
        GestureType.POINTER
    """
```

### 9.2 用户手册

创建 `docs/` 目录：

```
docs/
├── index.md           # 首页
├── installation.md    # 安装指南
├── quickstart.md      # 快速开始
├── gestures.md        # 手势说明（配图）
├── configuration.md   # 配置详解
├── troubleshooting.md # 故障排除
└── development.md     # 开发指南
```

### 9.3 CHANGELOG

```markdown
# Changelog

## [1.1.0] - 未发布

### Added
- Wayland 环境检测和提示
- 摄像头断开重连机制

### Fixed
- 修复 SettingsWindow 导出缺失问题
- 修复系统托盘在 Wayland 下的错误堆栈

### Changed
- 改进错误处理和日志输出
```

---

## 实施优先级

| 优先级 | 改进项 | 工作量 | 影响 |
|--------|--------|--------|------|
| 🔴 高 | 系统托盘错误处理 | 小 | 用户体验 |
| 🔴 高 | 摄像头重连机制 | 中 | 稳定性 |
| 🟡 中 | 日志系统 | 中 | 可维护性 |
| 🟡 中 | 配置验证 | 小 | 用户体验 |
| 🟡 中 | 单元测试 | 大 | 代码质量 |
| 🟢 低 | 事件系统重构 | 大 | 架构 |
| 🟢 低 | 多手支持 | 大 | 功能 |
| 🟢 低 | Wayland 原生支持 | 大 | 兼容性 |

---

## 总结

LyraPointer 是一个架构清晰、功能完善的项目。主要改进方向：

1. **稳定性**: 完善错误处理、添加重连机制
2. **兼容性**: 改进 Wayland 支持
3. **可维护性**: 添加日志、测试、文档
4. **功能扩展**: 多手支持、自定义手势、插件系统

建议按优先级逐步实施，每次发布一个稳定版本。