import redis
import json
from typing import Optional, Any
from datetime import timedelta
import hashlib
from loguru import logger

# 从我们创建的config模块中导入settings实例
from ..config.settings import settings

class CacheManager:
    """智能缓存管理器，使用Redis进行数据缓存"""

    def __init__(self, redis_url: str = None):
        """初始化时，连接到Redis服务器"""
        # 优先使用传入的redis_url，否则从全局配置中获取
        url = redis_url or settings.redis_url
        try:
            self.redis_client = redis.from_url(url, decode_responses=True)
            # 测试连接是否成功
            self.redis_client.ping()
            logger.info(f"Successfully connected to Redis at {url}")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"无法连接到Redis at {url}。缓存功能将被禁用。错误: {e}")
            self.redis_client = None

    def _generate_key(self, prefix: str, data: Any) -> str:
        """根据前缀和数据内容生成一个确定的MD5哈希作为缓存键"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        hash_digest = hashlib.md5(data_str.encode()).hexdigest()
        return f"{prefix}:{hash_digest}"

    def get(self, key: str) -> Optional[Any]:
        """从缓存中获取数据"""
        if not self.redis_client:
            return None
        try:
            data = self.redis_client.get(key)
            if data:
                logger.debug(f"Cache HIT for key: {key}")
                return json.loads(data)
            else:
                logger.debug(f"Cache MISS for key: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_hours: int = 24
    ) -> bool:
        """向缓存中写入数据"""
        if not self.redis_client:
            return False
        try:
            ttl_seconds = int(timedelta(hours=ttl_hours).total_seconds())
            self.redis_client.setex(
                key,
                ttl_seconds,
                json.dumps(value, ensure_ascii=False)
            )
            logger.debug(f"Cache SET for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """根据模式批量失效缓存"""
        if not self.redis_client:
            return 0
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                logger.info(f"Invalidating {len(keys)} cache entries for pattern: {pattern}")
                return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache invalidation error for pattern {pattern}: {e}")
        return 0

# 创建一个全局可引用的缓存管理器实例
cache_manager = CacheManager()
