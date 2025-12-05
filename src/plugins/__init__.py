"""
插件系统模块

提供可扩展的插件架构，支持自定义手势和动作。
"""

from .base import ActionPlugin, GesturePlugin, Plugin, PluginInfo, PluginType
from .manager import PluginManager

__all__ = [
    "Plugin",
    "PluginInfo",
    "PluginType",
    "GesturePlugin",
    "ActionPlugin",
    "PluginManager",
]
