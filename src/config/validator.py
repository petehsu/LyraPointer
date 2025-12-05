"""
LyraPointer 配置验证器

验证配置文件的有效性，确保所有配置项都在有效范围内。
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union


@dataclass
class ValidationError:
    """验证错误"""

    key: str
    message: str
    value: Any
    severity: str = "error"  # "error", "warning", "info"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message} (value: {self.value})"


@dataclass
class ValidationRule:
    """验证规则"""

    key: str
    description: str = ""
    required: bool = False
    value_type: Optional[Type] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None  # 正则表达式
    custom_validator: Optional[Callable[[Any], Optional[str]]] = None
    default: Any = None
    nested_rules: Optional[Dict[str, "ValidationRule"]] = None


# 默认验证规则定义
DEFAULT_RULES: Dict[str, ValidationRule] = {
    # 手势配置
    "gestures": ValidationRule(
        key="gestures",
        description="手势配置",
        value_type=dict,
    ),
    # 设置
    "settings.sensitivity": ValidationRule(
        key="settings.sensitivity",
        description="鼠标灵敏度",
        required=True,
        value_type=(int, float),
        min_value=0.1,
        max_value=5.0,
        default=1.5,
    ),
    "settings.smoothing": ValidationRule(
        key="settings.smoothing",
        description="平滑系数",
        required=True,
        value_type=(int, float),
        min_value=0.0,
        max_value=0.99,
        default=0.7,
    ),
    "settings.double_click_interval": ValidationRule(
        key="settings.double_click_interval",
        description="双击间隔（毫秒）",
        value_type=(int, float),
        min_value=100,
        max_value=1000,
        default=300,
    ),
    "settings.scroll_speed": ValidationRule(
        key="settings.scroll_speed",
        description="滚动速度",
        value_type=int,
        min_value=1,
        max_value=20,
        default=5,
    ),
    # 控制区域
    "settings.control_zone.x_min": ValidationRule(
        key="settings.control_zone.x_min",
        description="控制区域 X 最小值",
        value_type=(int, float),
        min_value=0.0,
        max_value=0.5,
        default=0.15,
    ),
    "settings.control_zone.x_max": ValidationRule(
        key="settings.control_zone.x_max",
        description="控制区域 X 最大值",
        value_type=(int, float),
        min_value=0.5,
        max_value=1.0,
        default=0.85,
    ),
    "settings.control_zone.y_min": ValidationRule(
        key="settings.control_zone.y_min",
        description="控制区域 Y 最小值",
        value_type=(int, float),
        min_value=0.0,
        max_value=0.5,
        default=0.15,
    ),
    "settings.control_zone.y_max": ValidationRule(
        key="settings.control_zone.y_max",
        description="控制区域 Y 最大值",
        value_type=(int, float),
        min_value=0.5,
        max_value=1.0,
        default=0.85,
    ),
    # 摄像头设置
    "settings.camera.index": ValidationRule(
        key="settings.camera.index",
        description="摄像头索引",
        value_type=int,
        min_value=0,
        max_value=10,
        default=0,
    ),
    "settings.camera.width": ValidationRule(
        key="settings.camera.width",
        description="摄像头宽度",
        value_type=int,
        min_value=320,
        max_value=1920,
        default=640,
    ),
    "settings.camera.height": ValidationRule(
        key="settings.camera.height",
        description="摄像头高度",
        value_type=int,
        min_value=240,
        max_value=1080,
        default=480,
    ),
    "settings.camera.fps": ValidationRule(
        key="settings.camera.fps",
        description="摄像头帧率",
        value_type=int,
        min_value=10,
        max_value=120,
        default=30,
    ),
    "settings.camera.flip_x": ValidationRule(
        key="settings.camera.flip_x",
        description="水平镜像",
        value_type=bool,
        default=True,
    ),
    "settings.camera.flip_y": ValidationRule(
        key="settings.camera.flip_y",
        description="垂直镜像",
        value_type=bool,
        default=False,
    ),
    # 性能设置
    "settings.performance.process_interval": ValidationRule(
        key="settings.performance.process_interval",
        description="处理间隔帧数",
        value_type=int,
        min_value=1,
        max_value=5,
        default=1,
    ),
    "settings.performance.model_complexity": ValidationRule(
        key="settings.performance.model_complexity",
        description="模型复杂度",
        value_type=int,
        allowed_values=[0, 1],
        default=0,
    ),
    "settings.performance.detection_confidence": ValidationRule(
        key="settings.performance.detection_confidence",
        description="检测置信度",
        value_type=(int, float),
        min_value=0.1,
        max_value=1.0,
        default=0.7,
    ),
    "settings.performance.tracking_confidence": ValidationRule(
        key="settings.performance.tracking_confidence",
        description="追踪置信度",
        value_type=(int, float),
        min_value=0.1,
        max_value=1.0,
        default=0.5,
    ),
    # UI 设置
    "ui.show_visualizer": ValidationRule(
        key="ui.show_visualizer",
        description="显示可视化窗口",
        value_type=bool,
        default=True,
    ),
    "ui.show_skeleton": ValidationRule(
        key="ui.show_skeleton",
        description="显示手部骨架",
        value_type=bool,
        default=True,
    ),
    "ui.show_gesture_info": ValidationRule(
        key="ui.show_gesture_info",
        description="显示手势信息",
        value_type=bool,
        default=True,
    ),
    "ui.show_control_zone": ValidationRule(
        key="ui.show_control_zone",
        description="显示控制区域",
        value_type=bool,
        default=True,
    ),
    "ui.show_fps": ValidationRule(
        key="ui.show_fps",
        description="显示 FPS",
        value_type=bool,
        default=True,
    ),
}


class ConfigValidator:
    """
    配置验证器

    验证配置文件的有效性，确保所有配置项都在有效范围内。

    Example:
        >>> validator = ConfigValidator()
        >>> errors = validator.validate(config)
        >>> if errors:
        ...     for error in errors:
        ...         print(error)
    """

    def __init__(
        self,
        rules: Optional[Dict[str, ValidationRule]] = None,
        strict: bool = False,
    ):
        """
        初始化配置验证器

        Args:
            rules: 自定义验证规则，如果为 None 则使用默认规则
            strict: 是否严格模式（未知的配置项也会报错）
        """
        self.rules = rules or DEFAULT_RULES.copy()
        self.strict = strict

    def validate(self, config: Dict[str, Any]) -> List[ValidationError]:
        """
        验证配置

        Args:
            config: 配置字典

        Returns:
            验证错误列表，如果为空则验证通过
        """
        errors: List[ValidationError] = []

        # 验证每个规则
        for key, rule in self.rules.items():
            value = self._get_nested_value(config, key)
            rule_errors = self._validate_rule(rule, value)
            errors.extend(rule_errors)

        # 额外的跨字段验证
        cross_errors = self._validate_cross_field(config)
        errors.extend(cross_errors)

        return errors

    def _get_nested_value(self, config: Dict[str, Any], key: str) -> Any:
        """
        获取嵌套的配置值

        Args:
            config: 配置字典
            key: 点分隔的键路径

        Returns:
            配置值，如果不存在则返回 None
        """
        keys = key.split(".")
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None

        return value

    def _validate_rule(self, rule: ValidationRule, value: Any) -> List[ValidationError]:
        """
        验证单个规则

        Args:
            rule: 验证规则
            value: 配置值

        Returns:
            验证错误列表
        """
        errors: List[ValidationError] = []

        # 检查必填项
        if value is None:
            if rule.required:
                errors.append(
                    ValidationError(
                        key=rule.key,
                        message=f"必填项 '{rule.description}' 缺失",
                        value=value,
                    )
                )
            return errors

        # 检查类型
        if rule.value_type is not None:
            if isinstance(rule.value_type, tuple):
                if not isinstance(value, rule.value_type):
                    expected = " 或 ".join(t.__name__ for t in rule.value_type)
                    errors.append(
                        ValidationError(
                            key=rule.key,
                            message=f"类型错误，期望 {expected}，实际为 {type(value).__name__}",
                            value=value,
                        )
                    )
                    return errors
            elif not isinstance(value, rule.value_type):
                errors.append(
                    ValidationError(
                        key=rule.key,
                        message=f"类型错误，期望 {rule.value_type.__name__}，实际为 {type(value).__name__}",
                        value=value,
                    )
                )
                return errors

        # 检查最小值
        if rule.min_value is not None and isinstance(value, (int, float)):
            if value < rule.min_value:
                errors.append(
                    ValidationError(
                        key=rule.key,
                        message=f"值 {value} 小于最小值 {rule.min_value}",
                        value=value,
                    )
                )

        # 检查最大值
        if rule.max_value is not None and isinstance(value, (int, float)):
            if value > rule.max_value:
                errors.append(
                    ValidationError(
                        key=rule.key,
                        message=f"值 {value} 大于最大值 {rule.max_value}",
                        value=value,
                    )
                )

        # 检查允许的值
        if rule.allowed_values is not None:
            if value not in rule.allowed_values:
                allowed = ", ".join(str(v) for v in rule.allowed_values)
                errors.append(
                    ValidationError(
                        key=rule.key,
                        message=f"值 {value} 不在允许的范围内 [{allowed}]",
                        value=value,
                    )
                )

        # 检查正则表达式
        if rule.pattern is not None and isinstance(value, str):
            import re

            if not re.match(rule.pattern, value):
                errors.append(
                    ValidationError(
                        key=rule.key,
                        message=f"值 '{value}' 不匹配模式 {rule.pattern}",
                        value=value,
                    )
                )

        # 自定义验证器
        if rule.custom_validator is not None:
            error_msg = rule.custom_validator(value)
            if error_msg:
                errors.append(
                    ValidationError(
                        key=rule.key,
                        message=error_msg,
                        value=value,
                    )
                )

        return errors

    def _validate_cross_field(self, config: Dict[str, Any]) -> List[ValidationError]:
        """
        跨字段验证

        Args:
            config: 配置字典

        Returns:
            验证错误列表
        """
        errors: List[ValidationError] = []

        # 验证控制区域
        x_min = self._get_nested_value(config, "settings.control_zone.x_min")
        x_max = self._get_nested_value(config, "settings.control_zone.x_max")
        y_min = self._get_nested_value(config, "settings.control_zone.y_min")
        y_max = self._get_nested_value(config, "settings.control_zone.y_max")

        if x_min is not None and x_max is not None:
            if x_min >= x_max:
                errors.append(
                    ValidationError(
                        key="settings.control_zone",
                        message=f"x_min ({x_min}) 必须小于 x_max ({x_max})",
                        value={"x_min": x_min, "x_max": x_max},
                    )
                )

        if y_min is not None and y_max is not None:
            if y_min >= y_max:
                errors.append(
                    ValidationError(
                        key="settings.control_zone",
                        message=f"y_min ({y_min}) 必须小于 y_max ({y_max})",
                        value={"y_min": y_min, "y_max": y_max},
                    )
                )

        # 验证检测置信度 <= 追踪置信度的合理性（通常检测需要更高置信度）
        detection_conf = self._get_nested_value(
            config, "settings.performance.detection_confidence"
        )
        tracking_conf = self._get_nested_value(
            config, "settings.performance.tracking_confidence"
        )

        if detection_conf is not None and tracking_conf is not None:
            if detection_conf < tracking_conf:
                errors.append(
                    ValidationError(
                        key="settings.performance",
                        message=f"检测置信度 ({detection_conf}) 通常应大于等于追踪置信度 ({tracking_conf})",
                        value={
                            "detection_confidence": detection_conf,
                            "tracking_confidence": tracking_conf,
                        },
                        severity="warning",
                    )
                )

        return errors

    def add_rule(self, rule: ValidationRule):
        """
        添加验证规则

        Args:
            rule: 验证规则
        """
        self.rules[rule.key] = rule

    def remove_rule(self, key: str):
        """
        移除验证规则

        Args:
            key: 规则键
        """
        if key in self.rules:
            del self.rules[key]

    def get_defaults(self) -> Dict[str, Any]:
        """
        获取所有默认值

        Returns:
            默认值字典
        """
        defaults = {}

        for key, rule in self.rules.items():
            if rule.default is not None:
                self._set_nested_value(defaults, key, rule.default)

        return defaults

    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        """
        设置嵌套的配置值

        Args:
            config: 配置字典
            key: 点分隔的键路径
            value: 要设置的值
        """
        keys = key.split(".")
        current = config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def fix_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        尝试修复配置中的错误

        Args:
            config: 配置字典

        Returns:
            修复后的配置
        """
        import copy

        fixed = copy.deepcopy(config)

        for key, rule in self.rules.items():
            value = self._get_nested_value(fixed, key)

            # 如果值缺失或无效，使用默认值
            if value is None and rule.default is not None:
                self._set_nested_value(fixed, key, rule.default)
                continue

            # 修复超出范围的值
            if isinstance(value, (int, float)):
                if rule.min_value is not None and value < rule.min_value:
                    self._set_nested_value(fixed, key, rule.min_value)
                elif rule.max_value is not None and value > rule.max_value:
                    self._set_nested_value(fixed, key, rule.max_value)

        return fixed


def validate_config(config: Dict[str, Any]) -> List[ValidationError]:
    """
    便捷函数：验证配置

    Args:
        config: 配置字典

    Returns:
        验证错误列表
    """
    validator = ConfigValidator()
    return validator.validate(config)


def fix_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    便捷函数：修复配置

    Args:
        config: 配置字典

    Returns:
        修复后的配置
    """
    validator = ConfigValidator()
    return validator.fix_config(config)
