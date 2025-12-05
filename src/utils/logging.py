"""
LyraPointer 日志系统

提供统一的日志记录功能，支持控制台和文件输出。
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# 日志格式
CONSOLE_FORMAT = "%(levelname)s: %(message)s"
CONSOLE_FORMAT_DEBUG = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
FILE_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)

# 默认日志目录
DEFAULT_LOG_DIR = Path.home() / ".local" / "share" / "lyrapointer" / "logs"

# 全局日志器缓存
_loggers: dict[str, logging.Logger] = {}
_initialized = False


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""

    # ANSI 颜色代码
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, fmt: str = None, use_colors: bool = True):
        super().__init__(fmt)
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        if self.use_colors and record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )
        return super().format(record)


def setup_logging(
    debug: bool = False,
    log_dir: Optional[Path] = None,
    log_file: bool = True,
    max_file_size: int = 5 * 1024 * 1024,  # 5MB
    backup_count: int = 3,
    use_colors: bool = True,
) -> logging.Logger:
    """
    设置日志系统

    Args:
        debug: 是否启用调试模式
        log_dir: 日志文件目录
        log_file: 是否启用文件日志
        max_file_size: 单个日志文件最大大小（字节）
        backup_count: 保留的备份文件数量
        use_colors: 是否使用彩色输出

    Returns:
        根日志器
    """
    global _initialized

    if _initialized:
        return logging.getLogger("lyrapointer")

    # 设置日志级别
    level = logging.DEBUG if debug else logging.INFO

    # 创建根日志器
    root_logger = logging.getLogger("lyrapointer")
    root_logger.setLevel(logging.DEBUG)  # 根日志器始终捕获所有级别

    # 清除已有的处理器
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = CONSOLE_FORMAT_DEBUG if debug else CONSOLE_FORMAT
    console_formatter = ColoredFormatter(console_format, use_colors=use_colors)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        try:
            if log_dir is None:
                log_dir = DEFAULT_LOG_DIR
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)

            # 创建日志文件名（包含日期）
            log_filename = f"lyrapointer_{datetime.now().strftime('%Y%m%d')}.log"
            log_path = log_dir / log_filename

            # 使用 RotatingFileHandler 防止日志文件过大
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)  # 文件始终记录所有级别
            file_formatter = logging.Formatter(FILE_FORMAT)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

            root_logger.debug(f"日志文件: {log_path}")
        except Exception as e:
            root_logger.warning(f"无法创建日志文件: {e}")

    _initialized = True
    return root_logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志器

    Args:
        name: 日志器名称，如果为 None 则返回根日志器

    Returns:
        日志器实例

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello, world!")
    """
    global _initialized

    # 如果还没初始化，先初始化
    if not _initialized:
        setup_logging()

    if name is None:
        return logging.getLogger("lyrapointer")

    # 构建完整的日志器名称
    if name.startswith("lyrapointer."):
        full_name = name
    elif name.startswith("src."):
        full_name = f"lyrapointer.{name[4:]}"
    else:
        full_name = f"lyrapointer.{name}"

    # 缓存日志器
    if full_name not in _loggers:
        _loggers[full_name] = logging.getLogger(full_name)

    return _loggers[full_name]


def set_level(level: int | str):
    """
    设置日志级别

    Args:
        level: 日志级别（logging.DEBUG, logging.INFO 等或字符串）
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    root_logger = logging.getLogger("lyrapointer")
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, RotatingFileHandler
        ):
            handler.setLevel(level)


def disable_file_logging():
    """禁用文件日志"""
    root_logger = logging.getLogger("lyrapointer")
    for handler in root_logger.handlers[:]:
        if isinstance(handler, RotatingFileHandler):
            root_logger.removeHandler(handler)
            handler.close()


def get_log_files() -> list[Path]:
    """
    获取所有日志文件列表

    Returns:
        日志文件路径列表
    """
    log_dir = DEFAULT_LOG_DIR
    if not log_dir.exists():
        return []

    return sorted(log_dir.glob("lyrapointer_*.log*"))


def clear_old_logs(keep_days: int = 7):
    """
    清理旧日志文件

    Args:
        keep_days: 保留最近几天的日志
    """
    from datetime import timedelta

    cutoff = datetime.now() - timedelta(days=keep_days)
    log_files = get_log_files()

    for log_file in log_files:
        try:
            # 从文件名解析日期
            name = log_file.stem
            if name.startswith("lyrapointer_"):
                date_str = name.replace("lyrapointer_", "").split(".")[0]
                try:
                    file_date = datetime.strptime(date_str, "%Y%m%d")
                    if file_date < cutoff:
                        log_file.unlink()
                        print(f"Deleted old log: {log_file}")
                except ValueError:
                    pass
        except Exception:
            pass


class LoggerMixin:
    """
    日志器混入类

    为类提供便捷的日志功能。

    Example:
        >>> class MyClass(LoggerMixin):
        ...     def do_something(self):
        ...         self.logger.info("Doing something")
    """

    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__module__)
        return self._logger


# 便捷函数
def debug(msg: str, *args, **kwargs):
    """记录调试信息"""
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """记录普通信息"""
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """记录警告信息"""
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """记录错误信息"""
    get_logger().error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """记录严重错误"""
    get_logger().critical(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs):
    """记录异常信息（包含堆栈）"""
    get_logger().exception(msg, *args, **kwargs)
