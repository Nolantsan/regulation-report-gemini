"""
智能法律法规追踪系统 - 日志工具模块
使用loguru提供高性能日志记录功能
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
from rich.console import Console
from rich.logging import RichHandler
import pendulum

from ..config.settings import get_settings
from ..config.constants import LOG_LEVELS


class LoggerManager:
    """日志管理器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.console = Console()
        self._configured = False
        
    def setup_logger(self):
        """设置日志配置"""
        if self._configured:
            return

        # 移除默认处理器
        logger.remove()

        # 确保日志目录存在
        log_dir = Path(self.settings.logging.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        level_name = str(self.settings.logging.level).upper()
        log_level = LOG_LEVELS.get(level_name, LOG_LEVELS["INFO"])

        # 配置控制台输出
        if self.settings.logging.console_output:
            logger.add(
                sys.stderr,
                level=log_level,
                format=self._get_console_format(),
                colorize=True,
                backtrace=True,
                diagnose=True,
                enqueue=True
            )

        # 配置文件输出
        logger.add(
            self.settings.logging.file_path,
            level=log_level,
            format=self._get_file_format(),
            rotation=self.settings.logging.max_file_size,
            retention=self.settings.logging.backup_count,
            compression="zip",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )
        
        # 配置错误日志单独文件
        error_log_path = log_dir / "errors.log"
        logger.add(
            str(error_log_path),
            level="ERROR",
            format=self._get_file_format(),
            rotation="10 MB",
            retention=10,
            compression="zip",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )
        
        # 配置性能日志
        performance_log_path = log_dir / "performance.log"
        logger.add(
            str(performance_log_path),
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {module}:{function}:{line} | {message}",
            rotation="5 MB",
            retention=5,
            filter=lambda record: "PERFORMANCE" in record["extra"],
            enqueue=True
        )
        
        self._configured = True
        logger.info(f"日志系统初始化完成 - 级别: {level_name}")
    
    def _get_console_format(self) -> str:
        """获取控制台日志格式"""
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    def _get_file_format(self) -> str:
        """获取文件日志格式"""
        return (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{process}:{thread} | "
            "{name}:{function}:{line} | "
            "{message} | "
            "{extra}"
        )
    
    def get_logger(self, name: str = None) -> "LoggerProxy":
        """获取指定名称的日志器代理"""
        if not self._configured:
            self.setup_logger()
        
        return LoggerProxy(name or __name__)


class LoggerProxy:
    """日志器代理类，提供额外功能"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logger.bind(name=name)
    
    def trace(self, message: str, **kwargs):
        """跟踪级别日志"""
        self.logger.trace(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """调试级别日志"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """信息级别日志"""
        self.logger.info(message, **kwargs)
    
    def success(self, message: str, **kwargs):
        """成功级别日志"""
        self.logger.success(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """警告级别日志"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """错误级别日志"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """严重错误级别日志"""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """异常日志（自动捕获堆栈信息）"""
        self.logger.exception(message, **kwargs)
    
    def performance(self, operation: str, duration: float, **kwargs):
        """性能日志"""
        self.logger.bind(PERFORMANCE=True).info(
            f"Performance: {operation} completed in {duration:.3f}s",
            operation=operation,
            duration=duration,
            **kwargs
        )
    
    def audit(self, action: str, user: str = "system", **kwargs):
        """审计日志"""
        self.logger.bind(AUDIT=True).info(
            f"Audit: {user} performed {action}",
            action=action,
            user=user,
            timestamp=pendulum.now().isoformat(),
            **kwargs
        )
    
    def api_call(self, method: str, url: str, status_code: int, duration: float, **kwargs):
        """API调用日志"""
        level = "ERROR" if status_code >= 400 else "INFO"
        getattr(self.logger, level.lower())(
            f"API {method} {url} -> {status_code} ({duration:.3f}s)",
            method=method,
            url=url,
            status_code=status_code,
            duration=duration,
            **kwargs
        )
    
    def business_event(self, event_type: str, details: Dict[str, Any]):
        """业务事件日志"""
        self.logger.bind(BUSINESS=True).info(
            f"Business Event: {event_type}",
            event_type=event_type,
            details=details,
            timestamp=pendulum.now().isoformat()
        )
    
    def security_event(self, event_type: str, severity: str, details: Dict[str, Any]):
        """安全事件日志"""
        log_method = getattr(self.logger, severity.lower(), self.logger.warning)
        log_method(
            f"Security Event: {event_type}",
            event_type=event_type,
            severity=severity,
            details=details,
            timestamp=pendulum.now().isoformat(),
            SECURITY=True
        )


# 全局日志管理器实例
_logger_manager = LoggerManager()


def get_logger(name: str = None) -> LoggerProxy:
    """获取日志器实例"""
    return _logger_manager.get_logger(name)


def setup_logging():
    """设置日志系统"""
    _logger_manager.setup_logger()


# 便捷函数
def log_performance(operation: str):
    """性能监控装饰器"""
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger_proxy = get_logger(func.__module__)
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger_proxy.performance(operation, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger_proxy.performance(f"{operation} (failed)", duration)
                logger_proxy.error(f"Function {func.__name__} failed: {e}")
                raise
        return wrapper
    return decorator


def log_api_call(func):
    """API调用日志装饰器"""
    import functools
    import time
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger_proxy = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # 尝试从结果中提取状态码
            status_code = getattr(result, 'status_code', 200)
            url = kwargs.get('url', 'unknown')
            method = kwargs.get('method', 'GET')
            
            logger_proxy.api_call(method, url, status_code, duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger_proxy.api_call('ERROR', str(e), 500, duration)
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger_proxy = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # 尝试从结果中提取状态码
            status_code = getattr(result, 'status_code', 200)
            url = kwargs.get('url', 'unknown')
            method = kwargs.get('method', 'GET')
            
            logger_proxy.api_call(method, url, status_code, duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger_proxy.api_call('ERROR', str(e), 500, duration)
            raise
    
    # 检查是否为异步函数
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def log_business_event(event_type: str, details: Dict[str, Any] = None):
    """业务事件日志记录器"""
    logger_proxy = get_logger("business")
    logger_proxy.business_event(event_type, details or {})


def log_security_event(event_type: str, severity: str = "warning", details: Dict[str, Any] = None):
    """安全事件日志记录器"""
    logger_proxy = get_logger("security")
    logger_proxy.security_event(event_type, severity, details or {})


# 初始化日志系统
try:
    setup_logging()
except Exception as e:
    # 如果日志系统初始化失败，至少保证基本的日志功能
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.error(f"Failed to initialize logger system: {e}")