import logging
import re

import redis
from environs import Env

logger = logging.getLogger('quiz-bot')


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


def get_question_text(bd_redis, question_id):
    """Возвращает текст вопроса."""
    qa_context = bd_redis.json().get(question_id)
    return qa_context.get('question')


def get_answer_text(bd_redis, question_id) -> str:
    """Возвращает текст ответа."""
    answer_text = bd_redis.json().get(question_id).get('answer')

    if answer_text := re.split(r'[\.|(]', answer_text):
        answer_text = answer_text[0].lower()

    return answer_text.strip()  # type: ignore
