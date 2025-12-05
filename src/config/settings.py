"""
配置管理

从 YAML 文件加载和保存配置。
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml

from .defaults import DEFAULT_CONFIG


class Settings:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为 config/gestures.yaml
        """
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "gestures.yaml"
        
        self.config_path = Path(config_path)
        self._config: dict = {}
        
        # 加载配置
        self.load()
    
    def load(self) -> dict:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        # 先使用默认配置
        self._config = self._deep_copy(DEFAULT_CONFIG)
        
        # 如果配置文件存在，合并用户配置
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f) or {}
                self._config = self._deep_merge(self._config, user_config)
            except Exception as e:
                print(f"Warning: Failed to load config file: {e}")
        
        return self._config
    
    def save(self):
        """保存配置到文件"""
        # 确保目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                self._config,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点分隔（如 "settings.sensitivity"）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split(".")
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def reset(self):
        """重置为默认配置"""
        self._config = self._deep_copy(DEFAULT_CONFIG)
    
    @property
    def config(self) -> dict:
        """获取完整配置"""
        return self._config
    
    # ===== 便捷属性 =====
    
    @property
    def sensitivity(self) -> float:
        return self.get("settings.sensitivity", 1.5)
    
    @sensitivity.setter
    def sensitivity(self, value: float):
        self.set("settings.sensitivity", value)
    
    @property
    def smoothing(self) -> float:
        return self.get("settings.smoothing", 0.7)
    
    @smoothing.setter
    def smoothing(self, value: float):
        self.set("settings.smoothing", value)
    
    @property
    def scroll_speed(self) -> int:
        return self.get("settings.scroll_speed", 5)
    
    @property
    def control_zone(self) -> dict:
        return self.get("settings.control_zone", {
            "x_min": 0.15, "x_max": 0.85,
            "y_min": 0.15, "y_max": 0.85,
        })
    
    @property
    def camera_index(self) -> int:
        return self.get("settings.camera.index", 0)
    
    @property
    def camera_width(self) -> int:
        return self.get("settings.camera.width", 640)
    
    @property
    def camera_height(self) -> int:
        return self.get("settings.camera.height", 480)
    
    @property
    def flip_x(self) -> bool:
        return self.get("settings.camera.flip_x", True)
    
    @flip_x.setter
    def flip_x(self, value: bool):
        self.set("settings.camera.flip_x", value)
        
    @property
    def flip_y(self) -> bool:
        return self.get("settings.camera.flip_y", False)
    
    @flip_y.setter
    def flip_y(self, value: bool):
        self.set("settings.camera.flip_y", value)
    
    @property
    def model_complexity(self) -> int:
        return self.get("settings.performance.model_complexity", 0)
    
    @property
    def detection_confidence(self) -> float:
        return self.get("settings.performance.detection_confidence", 0.7)
    
    @property
    def tracking_confidence(self) -> float:
        return self.get("settings.performance.tracking_confidence", 0.5)
    
    @property
    def show_visualizer(self) -> bool:
        return self.get("ui.show_visualizer", True)
    
    @property
    def show_skeleton(self) -> bool:
        return self.get("ui.show_skeleton", True)
    
    @property
    def show_fps(self) -> bool:
        return self.get("ui.show_fps", True)
    
    # ===== 辅助方法 =====
    
    def _deep_copy(self, obj: Any) -> Any:
        """深拷贝对象"""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._deep_copy(v) for v in obj]
        return obj
    
    def _deep_merge(self, base: dict, override: dict) -> dict:
        """深度合并字典"""
        result = self._deep_copy(base)
        
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = self._deep_copy(value)
        
        return result
