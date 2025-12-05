"""
默认配置

定义所有配置项的默认值。
"""

DEFAULT_CONFIG = {
    "version": "1.0",
    
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
            "threshold": 0.05,
            "action": "left_click",
            "hold_frames": 3,
        },
        "right_click": {
            "description": "右键 - 拇指中指捏合",
            "type": "pinch",
            "fingers": ["thumb", "middle"],
            "threshold": 0.05,
            "action": "right_click",
            "hold_frames": 3,
        },
        "scroll": {
            "description": "滚动模式 - 上下移动滚动",
            "fingers": {
                "index": True,
                "middle": True,
                "ring": False,
                "pinky": False,
            },
            "action": "scroll_mode",
        },
        "pause": {
            "description": "暂停/恢复控制",
            "fingers": {
                "thumb": True,
                "index": True,
                "middle": True,
                "ring": True,
                "pinky": True,
            },
            "action": "toggle_pause",
            "hold_frames": 10,
        },
        "fist": {
            "description": "休息状态 - 无操作",
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
        "sensitivity": 1.5,
        "smoothing": 0.7,
        "double_click_interval": 300,
        "scroll_speed": 5,
        "control_zone": {
            "x_min": 0.15,
            "x_max": 0.85,
            "y_min": 0.15,
            "y_max": 0.85,
        },
        "camera": {
            "index": 0,
            "width": 640,
            "height": 480,
            "fps": 30,
        },
        "performance": {
            "process_interval": 1,
            "model_complexity": 0,
            "detection_confidence": 0.7,
            "tracking_confidence": 0.5,
        },
    },
    
    # UI 设置
    "ui": {
        "show_visualizer": True,
        "show_skeleton": True,
        "show_gesture_info": True,
        "show_control_zone": True,
        "show_fps": True,
    },
}
