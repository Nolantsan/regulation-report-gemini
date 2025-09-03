"""
智能法律法规追踪系统 - 装饰器模块
提供系统中使用的各种装饰器
"""

import functools
import time
import asyncio
from typing import Any, Callable, Dict, Optional, Type, Union, List
import threading
from concurrent.futures import ThreadPoolExecutor
import inspect

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .logger import get_logger


def timing_decorator(operation_name: str = None):
    """性能计时装饰器"""
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        op_name = operation_name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    logger.performance(op_name, duration)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"{op_name} failed after {duration:.3f}s: {e}")
                    raise
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    logger.performance(op_name, duration)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"{op_name} failed after {duration:.3f}s: {e}")
                    raise
            return sync_wrapper
    return decorator


def error_handler(
    exceptions: Union[Type[Exception], tuple] = Exception,
    default_return: Any = None,
    log_errors: bool = True,
    reraise: bool = True
):
    """通用错误处理装饰器"""
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if log_errors:
                        logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                    
                    if reraise:
                        raise
                    return default_return
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if log_errors:
                        logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                    
                    if reraise:
                        raise
                    return default_return
            return sync_wrapper
    return decorator


def validate_args(**validators):
    """参数验证装饰器"""
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数签名
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # 验证参数
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        error_msg = f"Validation failed for parameter '{param_name}' with value {value}"
                        logger.error(error_msg)
                        raise ValueError(error_msg)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def cache_result(ttl_seconds: int = 3600, key_func: Callable = None):
    """结果缓存装饰器"""
    cache = {}
    cache_times = {}
    lock = threading.Lock()
    
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            current_time = time.time()
            
            with lock:
                # 检查缓存
                if cache_key in cache:
                    if current_time - cache_times[cache_key] < ttl_seconds:
                        logger.debug(f"Cache hit for {func.__name__}")
                        return cache[cache_key]
                    else:
                        # 清理过期缓存
                        del cache[cache_key]
                        del cache_times[cache_key]
                
                # 执行函数并缓存结果
                logger.debug(f"Cache miss for {func.__name__}, executing function")
                result = func(*args, **kwargs)
                cache[cache_key] = result
                cache_times[cache_key] = current_time
                return result
        
        # 添加清理缓存的方法
        wrapper.clear_cache = lambda: cache.clear() or cache_times.clear()
        return wrapper
    return decorator


def rate_limit(max_calls: int, time_window: int = 60):
    """API调用频率限制装饰器"""
    calls = []
    lock = threading.Lock()
    
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                current_time = time.time()
                
                with lock:
                    # 清理过期的调用记录
                    calls[:] = [call_time for call_time in calls if current_time - call_time < time_window]
                    
                    if len(calls) >= max_calls:
                        logger.warning(f"Rate limit exceeded for {func.__name__}")
                        raise Exception(f"Rate limit exceeded: {max_calls} calls per {time_window} seconds")
                    
                    calls.append(current_time)
                
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                current_time = time.time()
                
                with lock:
                    # 清理过期的调用记录
                    calls[:] = [call_time for call_time in calls if current_time - call_time < time_window]
                    
                    if len(calls) >= max_calls:
                        logger.warning(f"Rate limit exceeded for {func.__name__}")
                        raise Exception(f"Rate limit exceeded: {max_calls} calls per {time_window} seconds")
                    
                    calls.append(current_time)
                
                return func(*args, **kwargs)
            return sync_wrapper
    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """异步重试装饰器"""
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            raise last_exception
        return wrapper
    return decorator


def singleton(cls):
    """单例模式装饰器"""
    instances = {}
    lock = threading.Lock()
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


def thread_safe(func: Callable) -> Callable:
    """线程安全装饰器"""
    lock = threading.Lock()
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with lock:
            return func(*args, **kwargs)
    return wrapper


def async_to_sync(func: Callable) -> Callable:
    """异步函数转同步函数装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # 如果事件循环已经在运行，使用线程池执行
            with ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, func(*args, **kwargs))
                return future.result()
        else:
            return loop.run_until_complete(func(*args, **kwargs))
    
    return wrapper


def deprecated(reason: str = "This function is deprecated"):
    """标记函数为已废弃"""
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.warning(f"Call to deprecated function {func.__name__}: {reason}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_calls(log_args: bool = True, log_result: bool = False):
    """函数调用日志装饰器"""
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            
            # 记录函数调用
            if log_args:
                logger.debug(f"Calling {func_name} with args={args}, kwargs={kwargs}")
            else:
                logger.debug(f"Calling {func_name}")
            
            try:
                result = func(*args, **kwargs)
                
                if log_result:
                    logger.debug(f"{func_name} returned: {result}")
                else:
                    logger.debug(f"{func_name} completed successfully")
                
                return result
            except Exception as e:
                logger.error(f"{func_name} raised exception: {e}")
                raise
        
        return wrapper
    return decorator


def require_config(*config_keys):
    """要求配置项存在的装饰器"""
    def decorator(func: Callable) -> Callable:
        from ..config.settings import get_settings
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            settings = get_settings()
            
            for key in config_keys:
                # 支持嵌套键，如 "ai.api_key"
                value = settings
                for key_part in key.split('.'):
                    if hasattr(value, key_part):
                        value = getattr(value, key_part)
                    else:
                        raise ValueError(f"Required configuration '{key}' is missing")
                
                if not value:
                    raise ValueError(f"Required configuration '{key}' is empty")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def background_task(executor: ThreadPoolExecutor = None):
    """后台任务装饰器"""
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        _executor = executor or ThreadPoolExecutor(max_workers=4)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"Starting background task: {func.__name__}")
            future = _executor.submit(func, *args, **kwargs)
            return future
        
        return wrapper
    return decorator


def conditional(condition: Callable[[Any], bool]):
    """条件执行装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if condition(*args, **kwargs):
                return func(*args, **kwargs)
            else:
                return None
        return wrapper
    return decorator


# 预配置的重试装饰器
network_retry = functools.partial(
    async_retry,
    max_attempts=3,
    delay=1.0,
    backoff=2.0,
    exceptions=(ConnectionError, TimeoutError)
)

api_retry = functools.partial(
    async_retry,
    max_attempts=5,
    delay=0.5,
    backoff=1.5,
    exceptions=(Exception,)
)

database_retry = functools.partial(
    async_retry,
    max_attempts=3,
    delay=0.1,
    backoff=2.0,
    exceptions=(Exception,)
)
