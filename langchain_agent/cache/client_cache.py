"""
Client 缓存管理器
支持按照用户+入口维度进行缓存，30分钟后自动释放
"""

import time
from threading import Lock
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict


class ClientCache:
    """客户端缓存管理器"""

    # 缓存过期时间（秒）- 30分钟
    CACHE_TTL = 30 * 60

    def __init__(self):
        """初始化缓存管理器"""
        self._cache: Dict[Tuple[str, str], Tuple[Any, float]] = OrderedDict()
        self._lock = Lock()

    def _generate_key(self, user_id: str, entry_point: str) -> Tuple[str, str]:
        """生成缓存键"""
        return (user_id, entry_point)

    def get(self, user_id: str, entry_point: str) -> Optional[Any]:
        """
        获取缓存的 client

        Args:
            user_id: 用户ID
            entry_point: 入口标识

        Returns:
            缓存的 client，如果不存在或已过期则返回 None
        """
        key = self._generate_key(user_id, entry_point)

        with self._lock:
            if key not in self._cache:
                return None

            client, timestamp = self._cache[key]
            current_time = time.time()

            # 检查是否过期
            if current_time - timestamp > self.CACHE_TTL:
                # 删除过期缓存
                del self._cache[key]
                return None

            # 更新访问顺序（LRU）
            self._cache.move_to_end(key)
            return client

    def set(self, user_id: str, entry_point: str, client: Any) -> None:
        """
        设置 client 缓存

        Args:
            user_id: 用户ID
            entry_point: 入口标识
            client: 要缓存的 client 对象
        """
        key = self._generate_key(user_id, entry_point)
        timestamp = time.time()

        with self._lock:
            self._cache[key] = (client, timestamp)
            self._cache.move_to_end(key)

    def delete(self, user_id: str, entry_point: str) -> bool:
        """
        删除指定的缓存

        Args:
            user_id: 用户ID
            entry_point: 入口标识

        Returns:
            是否成功删除
        """
        key = self._generate_key(user_id, entry_point)

        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear_expired(self) -> int:
        """
        清理所有过期的缓存

        Returns:
            清理的缓存数量
        """
        current_time = time.time()
        expired_keys = []

        with self._lock:
            for key, (_, timestamp) in self._cache.items():
                if current_time - timestamp > self.CACHE_TTL:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

        return len(expired_keys)

    def clear_all(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """获取当前缓存数量"""
        with self._lock:
            return len(self._cache)

    def stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            包含缓存统计信息的字典
        """
        current_time = time.time()

        with self._lock:
            valid_count = 0
            expired_count = 0
            oldest_age = 0

            for _, (_, timestamp) in self._cache.items():
                age = current_time - timestamp
                if age > self.CACHE_TTL:
                    expired_count += 1
                else:
                    valid_count += 1
                    if age > oldest_age:
                        oldest_age = age

            return {
                "total": len(self._cache),
                "valid": valid_count,
                "expired": expired_count,
                "oldest_age_seconds": round(oldest_age, 2),
                "cache_ttl_seconds": self.CACHE_TTL,
            }


# 全局缓存实例
_global_cache: Optional[ClientCache] = None
_cache_lock = Lock()


def get_global_cache() -> ClientCache:
    """
    获取全局缓存实例（单例模式）

    Returns:
        ClientCache 实例
    """
    global _global_cache

    with _cache_lock:
        if _global_cache is None:
            _global_cache = ClientCache()

        return _global_cache
