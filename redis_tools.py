import logging
import redis


def create_redis():
    """
    Create a new redis instance.
    """
    redis_host = ''
    redis_port = ''
    redis_username = ''
    redis_password = ''

    return redis.Redis(
        host=redis_host,
        port=redis_port,
        username=redis_username,
        password=redis_password
    )


def delete_all_qa():
    """Удаляет все вопросы и ответы с БД."""
    qa_keys = r.keys(pattern='QA_*')
    r.delete(*qa_keys)


def delete_all_user_data():
    """Удаляет все данные пользователей."""
    user_keys = r.keys(pattern='TG_*')
    r.delete(*user_keys)

    user_keys = r.keys(pattern='VK_*')
    r.delete(*user_keys)



r = redis.Redis()
