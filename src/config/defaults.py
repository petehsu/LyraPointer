"""
默认配置

定义所有配置项的默认值。
优化版本 - 更好的默认体验。
"""

DEFAULT_CONFIG = {
    "version": "1.1",
    # 手势配置
    "gestures": {
        "pointer": {
            "description": "指针模式 - 控制鼠标移动",
            "fingers": {
                "index": True,
                "middle": False,
                "ring": False,
                "pinky": False,
            },
            "action": "move_cursor",
        },
        "click": {
            "description": "点击 - 拇指食指捏合",
            "type": "pinch",
            "fingers": ["thumb", "index"],
            "threshold": 0.045,  # 稍微降低，更容易触发
            "action": "left_click",
            "hold_frames": 2,  # 减少，更快响应
        },
        "double_click": {
            "description": "双击 - 快速捏合两次",
            "type": "pinch",
            "fingers": ["thumb", "index"],
            "threshold": 0.045,
            "action": "double_click",
            "interval_ms": 400,  # 双击间隔
        },
        "right_click": {
            "description": "右键 - 拇指中指捏合",
            "type": "pinch",
            "fingers": ["thumb", "middle"],
            "threshold": 0.05,
            "action": "right_click",
            "hold_frames": 2,
        },
        "drag": {
            "description": "拖拽 - 捏合并保持",
            "type": "pinch_hold",
            "fingers": ["thumb", "index"],
            "threshold": 0.045,
            "hold_time_ms": 300,  # 保持 300ms 进入拖拽
            "action": "drag",
        },
        "scroll": {
            "description": "滚动模式 - 双指上下移动",
            "fingers": {
                "index": True,
                "middle": True,
                "ring": False,
                "pinky": False,
            },
            "action": "scroll_mode",
            "sensitivity": 1.0,  # 滚动灵敏度
        },
        "palm": {
            "description": "暂停控制 - 张开手掌",
            "fingers": {
                "thumb": True,
                "index": True,
                "middle": True,
                "ring": True,
                "pinky": True,
            },
            "action": "pause",
            "hold_frames": 8,
        },
        "fist": {
            "description": "休息状态 - 握拳",
            "fingers": {
                "thumb": False,
                "index": False,
                "middle": False,
                "ring": False,
                "pinky": False,
            },
            "action": "none",
        },
    },
    # 控制设置
    "settings": {
        # 鼠标控制
        "sensitivity": 1.2,  # 降低灵敏度，更易控制
        "smoothing": 0.4,  # 降低平滑度，更跟手 (0=最跟手, 1=最平滑)
        "smoothing_preset": "balanced",  # responsive, balanced, stable, custom
        # 点击设置
        "double_click_interval": 350,
        "click_debounce_ms": 100,  # 防抖
        # 滚动设置
        "scroll_speed": 5,
        "scroll_acceleration": True,  # 滚动加速
        # 控制区域 - 手在此区域内才控制鼠标
        "control_zone": {
            "x_min": 0.12,  # 稍微扩大区域
            "x_max": 0.88,
            "y_min": 0.10,
            "y_max": 0.90,
        },
        # 摄像头设置
        "camera": {
            "index": 0,
            "width": 640,
            "height": 480,
            "fps": 30,
            "flip_x": True,  # 水平镜像（默认开启，更直观）
            "flip_y": False,
            "auto_exposure": True,
        },
        # 性能设置
        "performance": {
            "process_interval": 1,  # 每帧处理
            "model_complexity": 0,  # 0=Lite快速, 1=Full精准
            "detection_confidence": 0.65,  # 稍微降低，更容易检测
            "tracking_confidence": 0.5,
            "max_hands": 1,  # 只追踪一只手
        },
    },
    # UI 设置
    "ui": {
        "show_visualizer": True,
        "show_skeleton": True,
        "show_gesture_info": True,
        "show_control_zone": True,
        "show_fps": True,
        "show_tutorial_on_start": True,  # 首次启动显示教程
        "language": "auto",  # auto, en, zh_CN, zh_TW, ja, ko
        "theme": "dark",
        "window_size": {
            "width": 960,
            "height": 720,
        },
    },
    # 高级设置
    "advanced": {
        # One Euro Filter 参数（仅自定义模式使用）
        "filter": {
            "min_cutoff": 0.8,  # 最小截止频率
            "beta": 0.4,  # 速度系数
            "d_cutoff": 1.0,  # 导数截止频率
        },
        # 抖动检测
        "jitter": {
            "threshold": 0.002,  # 小于此值视为抖动
            "extra_smoothing": True,  # 检测到抖动时额外平滑
        },
        # 手势检测
        "gesture_detection": {
            "finger_threshold": 0.6,  # 手指伸展判断阈值
            "pinch_release_threshold": 0.08,  # 捏合释放阈值
            "state_change_frames": 2,  # 状态变化确认帧数
        },
    },
}
