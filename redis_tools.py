import logging
import redis

from environs import Env


def create_redis():
    """
    Create a new redis instance.
    """
    env = Env()
    env.read_env()

    redis_host = env.str('REDIS_HOST', 'localhost')
    redis_port = env.str('REDIS_PORT', 6379)
    redis_username = env.str('REDIS_USERNAME', '')
    redis_password = env.str('REDIS_PASSWORD', '')

    return redis.Redis(
        host=redis_host,
        port=redis_port,
        username=redis_username,
        password=redis_password
    )


def set_json_value(key, value):
    """Установить значение JSON по ключу."""
    return bd_redis.json().set(key, '$', value)


def get_json_value(key):
    """Получить значение JSON по ключу."""
    return bd_redis.json().get(key)


def set_value(key, value):
    """Установить значение по ключу."""
    return bd_redis.set(key, value)


def get_value(key):
    """Получить значение по ключу."""
    return bd_redis.get(key)


def fetch_keys(pattern='*'):
    """Получает список ключей по шаблону."""
    return bd_redis.keys(pattern)


def delete_key(key):
    """Удаляет запись по ключу."""
    bd_redis.delete(key)


def delete_all_keys(pattern='*'):
    """Удаляет все все ключи по шаблону."""
    if keys := bd_redis.keys(pattern=pattern):
        bd_redis.delete(*keys)


logger = logging.getLogger('quiz-bot')
bd_redis = create_redis()
