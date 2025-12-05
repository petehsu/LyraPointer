"""
LyraPointer 插件管理器

负责插件的加载、卸载、管理和执行。
"""

import importlib
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union

from ..utils.logging import get_logger
from .base import (
    ActionPlugin,
    FeedbackPlugin,
    FilterPlugin,
    GesturePlugin,
    Plugin,
    PluginInfo,
    PluginType,
    VisualizerPlugin,
)

logger = get_logger(__name__)


@dataclass
class PluginEntry:
    """插件条目"""

    plugin: Plugin
    info: PluginInfo
    module_path: Optional[str] = None
    load_order: int = 0


class PluginManager:
    """
    插件管理器

    负责插件的加载、卸载和生命周期管理。

    Example:
        >>> manager = PluginManager()
        >>> manager.load_from_directory("plugins/")
        >>> manager.initialize_all()
        >>>
        >>> # 获取手势插件
        >>> for plugin in manager.get_gesture_plugins():
        ...     gesture = plugin.detect(hand)
        ...
        >>> manager.shutdown_all()
    """

    def __init__(self, plugin_dirs: Optional[List[Path]] = None):
        """
        初始化插件管理器

        Args:
            plugin_dirs: 插件目录列表
        """
        self._plugins: Dict[str, PluginEntry] = {}
        self._plugin_dirs: List[Path] = plugin_dirs or []
        self._load_counter = 0

        # 按类型分类的插件缓存
        self._gesture_plugins: List[GesturePlugin] = []
        self._action_plugins: List[ActionPlugin] = []
        self._filter_plugins: List[FilterPlugin] = []
        self._visualizer_plugins: List[VisualizerPlugin] = []
        self._feedback_plugins: List[FeedbackPlugin] = []

        # 插件事件回调
        self._on_load_callbacks: List[Callable[[Plugin], None]] = []
        self._on_unload_callbacks: List[Callable[[Plugin], None]] = []

    def register(self, plugin: Plugin) -> bool:
        """
        注册插件

        Args:
            plugin: 插件实例

        Returns:
            是否注册成功
        """
        info = plugin.info
        name = info.name

        if name in self._plugins:
            logger.warning(f"Plugin '{name}' already registered, skipping")
            return False

        # 检查依赖
        if not self._check_dependencies(info):
            logger.error(f"Plugin '{name}' has unmet dependencies: {info.dependencies}")
            return False

        # 注册插件
        self._load_counter += 1
        entry = PluginEntry(
            plugin=plugin,
            info=info,
            load_order=self._load_counter,
        )
        self._plugins[name] = entry

        # 添加到类型缓存
        self._add_to_type_cache(plugin, info.plugin_type)

        logger.info(f"Registered plugin: {info}")

        # 触发回调
        for callback in self._on_load_callbacks:
            try:
                callback(plugin)
            except Exception as e:
                logger.error(f"Error in plugin load callback: {e}")

        return True

    def unregister(self, name: str) -> bool:
        """
        注销插件

        Args:
            name: 插件名称

        Returns:
            是否注销成功
        """
        if name not in self._plugins:
            logger.warning(f"Plugin '{name}' not found")
            return False

        entry = self._plugins[name]
        plugin = entry.plugin

        # 关闭插件
        if plugin.initialized:
            try:
                plugin.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugin '{name}': {e}")

        # 从类型缓存移除
        self._remove_from_type_cache(plugin, entry.info.plugin_type)

        # 移除注册
        del self._plugins[name]

        logger.info(f"Unregistered plugin: {name}")

        # 触发回调
        for callback in self._on_unload_callbacks:
            try:
                callback(plugin)
            except Exception as e:
                logger.error(f"Error in plugin unload callback: {e}")

        return True

    def _add_to_type_cache(self, plugin: Plugin, plugin_type: PluginType):
        """添加到类型缓存"""
        if plugin_type == PluginType.GESTURE and isinstance(plugin, GesturePlugin):
            self._gesture_plugins.append(plugin)
            self._gesture_plugins.sort(key=lambda p: -p.info.priority)
        elif plugin_type == PluginType.ACTION and isinstance(plugin, ActionPlugin):
            self._action_plugins.append(plugin)
            self._action_plugins.sort(key=lambda p: -p.info.priority)
        elif plugin_type == PluginType.FILTER and isinstance(plugin, FilterPlugin):
            self._filter_plugins.append(plugin)
            self._filter_plugins.sort(key=lambda p: -p.info.priority)
        elif plugin_type == PluginType.VISUALIZER and isinstance(
            plugin, VisualizerPlugin
        ):
            self._visualizer_plugins.append(plugin)
            self._visualizer_plugins.sort(key=lambda p: -p.info.priority)
        elif plugin_type == PluginType.FEEDBACK and isinstance(plugin, FeedbackPlugin):
            self._feedback_plugins.append(plugin)
            self._feedback_plugins.sort(key=lambda p: -p.info.priority)

    def _remove_from_type_cache(self, plugin: Plugin, plugin_type: PluginType):
        """从类型缓存移除"""
        if plugin_type == PluginType.GESTURE:
            if plugin in self._gesture_plugins:
                self._gesture_plugins.remove(plugin)
        elif plugin_type == PluginType.ACTION:
            if plugin in self._action_plugins:
                self._action_plugins.remove(plugin)
        elif plugin_type == PluginType.FILTER:
            if plugin in self._filter_plugins:
                self._filter_plugins.remove(plugin)
        elif plugin_type == PluginType.VISUALIZER:
            if plugin in self._visualizer_plugins:
                self._visualizer_plugins.remove(plugin)
        elif plugin_type == PluginType.FEEDBACK:
            if plugin in self._feedback_plugins:
                self._feedback_plugins.remove(plugin)

    def _check_dependencies(self, info: PluginInfo) -> bool:
        """检查插件依赖"""
        for dep in info.dependencies:
            if dep not in self._plugins:
                return False
        return True

    def load_from_file(self, file_path: Union[str, Path]) -> Optional[Plugin]:
        """
        从文件加载插件

        Args:
            file_path: 插件文件路径

        Returns:
            加载的插件，如果失败则返回 None
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"Plugin file not found: {file_path}")
            return None

        if not file_path.suffix == ".py":
            logger.error(f"Invalid plugin file: {file_path}")
            return None

        try:
            # 动态加载模块
            module_name = f"lyrapointer_plugin_{file_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)

            if spec is None or spec.loader is None:
                logger.error(f"Failed to load plugin spec: {file_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # 查找插件类
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Plugin)
                    and attr is not Plugin
                    and attr
                    not in (
                        GesturePlugin,
                        ActionPlugin,
                        FilterPlugin,
                        VisualizerPlugin,
                        FeedbackPlugin,
                    )
                ):
                    plugin_class = attr
                    break

            if plugin_class is None:
                logger.error(f"No plugin class found in: {file_path}")
                return None

            # 实例化并注册
            plugin = plugin_class()

            if self.register(plugin):
                entry = self._plugins[plugin.name]
                entry.module_path = str(file_path)
                return plugin

            return None

        except Exception as e:
            logger.error(f"Error loading plugin from {file_path}: {e}")
            return None

    def load_from_directory(self, directory: Union[str, Path]) -> List[Plugin]:
        """
        从目录加载所有插件

        Args:
            directory: 插件目录路径

        Returns:
            加载的插件列表
        """
        directory = Path(directory)
        loaded = []

        if not directory.exists():
            logger.warning(f"Plugin directory not found: {directory}")
            return loaded

        if not directory.is_dir():
            logger.error(f"Not a directory: {directory}")
            return loaded

        # 加载所有 .py 文件
        for file_path in sorted(directory.glob("*.py")):
            if file_path.name.startswith("_"):
                continue

            plugin = self.load_from_file(file_path)
            if plugin:
                loaded.append(plugin)

        logger.info(f"Loaded {len(loaded)} plugins from {directory}")
        return loaded

    def load_from_class(self, plugin_class: Type[Plugin]) -> Optional[Plugin]:
        """
        从类加载插件

        Args:
            plugin_class: 插件类

        Returns:
            加载的插件实例
        """
        try:
            plugin = plugin_class()
            if self.register(plugin):
                return plugin
            return None
        except Exception as e:
            logger.error(f"Error instantiating plugin class {plugin_class}: {e}")
            return None

    def get(self, name: str) -> Optional[Plugin]:
        """
        获取插件

        Args:
            name: 插件名称

        Returns:
            插件实例，如果不存在则返回 None
        """
        entry = self._plugins.get(name)
        return entry.plugin if entry else None

    def get_all(self) -> List[Plugin]:
        """
        获取所有插件

        Returns:
            插件列表（按加载顺序）
        """
        entries = sorted(self._plugins.values(), key=lambda e: e.load_order)
        return [e.plugin for e in entries]

    def get_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """
        获取指定类型的所有插件

        Args:
            plugin_type: 插件类型

        Returns:
            插件列表
        """
        if plugin_type == PluginType.GESTURE:
            return list(self._gesture_plugins)
        elif plugin_type == PluginType.ACTION:
            return list(self._action_plugins)
        elif plugin_type == PluginType.FILTER:
            return list(self._filter_plugins)
        elif plugin_type == PluginType.VISUALIZER:
            return list(self._visualizer_plugins)
        elif plugin_type == PluginType.FEEDBACK:
            return list(self._feedback_plugins)
        return []

    def get_gesture_plugins(self) -> List[GesturePlugin]:
        """获取所有手势插件"""
        return [p for p in self._gesture_plugins if p.enabled]

    def get_action_plugins(self) -> List[ActionPlugin]:
        """获取所有动作插件"""
        return [p for p in self._action_plugins if p.enabled]

    def get_filter_plugins(self) -> List[FilterPlugin]:
        """获取所有过滤器插件"""
        return [p for p in self._filter_plugins if p.enabled]

    def get_visualizer_plugins(self) -> List[VisualizerPlugin]:
        """获取所有可视化插件"""
        return [p for p in self._visualizer_plugins if p.enabled]

    def get_feedback_plugins(self) -> List[FeedbackPlugin]:
        """获取所有反馈插件"""
        return [p for p in self._feedback_plugins if p.enabled]

    def initialize_all(self):
        """初始化所有已注册的插件"""
        for entry in sorted(self._plugins.values(), key=lambda e: e.load_order):
            plugin = entry.plugin
            if not plugin.initialized:
                try:
                    plugin.initialize()
                    logger.debug(f"Initialized plugin: {plugin.name}")
                except Exception as e:
                    logger.error(f"Error initializing plugin '{plugin.name}': {e}")

    def shutdown_all(self):
        """关闭所有插件"""
        # 按加载顺序的逆序关闭
        for entry in sorted(self._plugins.values(), key=lambda e: -e.load_order):
            plugin = entry.plugin
            if plugin.initialized:
                try:
                    plugin.shutdown()
                    logger.debug(f"Shutdown plugin: {plugin.name}")
                except Exception as e:
                    logger.error(f"Error shutting down plugin '{plugin.name}': {e}")

    def enable(self, name: str) -> bool:
        """
        启用插件

        Args:
            name: 插件名称

        Returns:
            是否成功
        """
        plugin = self.get(name)
        if plugin:
            plugin.enabled = True
            logger.info(f"Enabled plugin: {name}")
            return True
        return False

    def disable(self, name: str) -> bool:
        """
        禁用插件

        Args:
            name: 插件名称

        Returns:
            是否成功
        """
        plugin = self.get(name)
        if plugin:
            plugin.enabled = False
            logger.info(f"Disabled plugin: {name}")
            return True
        return False

    def configure(self, name: str, config: Dict[str, Any]) -> bool:
        """
        配置插件

        Args:
            name: 插件名称
            config: 配置字典

        Returns:
            是否成功
        """
        plugin = self.get(name)
        if plugin:
            # 验证配置
            errors = plugin.validate_config(config)
            if errors:
                for error in errors:
                    logger.error(f"Config validation error for '{name}': {error}")
                return False

            plugin.configure(config)
            logger.info(f"Configured plugin: {name}")
            return True
        return False

    def reload(self, name: str) -> bool:
        """
        重新加载插件

        Args:
            name: 插件名称

        Returns:
            是否成功
        """
        if name not in self._plugins:
            logger.warning(f"Plugin '{name}' not found")
            return False

        entry = self._plugins[name]
        module_path = entry.module_path

        if not module_path:
            logger.error(f"Cannot reload plugin '{name}': no module path")
            return False

        # 卸载
        self.unregister(name)

        # 重新加载
        plugin = self.load_from_file(module_path)
        if plugin:
            if not plugin.initialized:
                plugin.initialize()
            return True

        return False

    def on_load(self, callback: Callable[[Plugin], None]):
        """注册插件加载回调"""
        self._on_load_callbacks.append(callback)

    def on_unload(self, callback: Callable[[Plugin], None]):
        """注册插件卸载回调"""
        self._on_unload_callbacks.append(callback)

    def get_info(self, name: str) -> Optional[PluginInfo]:
        """
        获取插件信息

        Args:
            name: 插件名称

        Returns:
            插件信息
        """
        entry = self._plugins.get(name)
        return entry.info if entry else None

    def get_all_info(self) -> List[PluginInfo]:
        """获取所有插件信息"""
        return [e.info for e in self._plugins.values()]

    def __len__(self) -> int:
        """获取插件数量"""
        return len(self._plugins)

    def __contains__(self, name: str) -> bool:
        """检查插件是否存在"""
        return name in self._plugins

    def __iter__(self):
        """迭代所有插件"""
        return iter(self.get_all())

    def __str__(self) -> str:
        return f"PluginManager({len(self)} plugins)"

    def __repr__(self) -> str:
        plugins = ", ".join(self._plugins.keys())
        return f"PluginManager([{plugins}])"


# 全局插件管理器实例
_global_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器实例"""
    global _global_manager
    if _global_manager is None:
        _global_manager = PluginManager()
    return _global_manager


def register_plugin(plugin: Plugin) -> bool:
    """便捷函数：注册插件到全局管理器"""
    return get_plugin_manager().register(plugin)


def get_plugin(name: str) -> Optional[Plugin]:
    """便捷函数：从全局管理器获取插件"""
    return get_plugin_manager().get(name)
