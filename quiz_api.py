import logging
import re
from random import choice

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


def get_question_id(user_id, prefix):
    """Возвращает id вопроса пользователя."""
    return bd_redis.get(f'{prefix}_{user_id}')


def set_question_id(user_id, qa_id, prefix):
    """Устанавливает id вопроса пользователя."""
    return bd_redis.set(f'{prefix}_{user_id}', qa_id)


def delete_question_id(user_id, prefix):
    """Удаляет текущий id вопроса пользователя."""
    bd_redis.delete(f'{prefix}_{user_id}')


def get_random_question_id(question_ids):
    """Возвращает случайны id вопроса."""
    return choice(question_ids)


def fetch_questions():
    """Возвращает id всех вопросов"""
    return bd_redis.keys('QA_*')


def get_question_text(question_id):
    """Возвращает текст вопроса."""
    qa_context = bd_redis.json().get(question_id)
    return qa_context.get('question')


def get_answer_text(question_id) -> str:
    """Возвращает текст ответа."""
    answer_text = bd_redis.json().get(question_id).get('answer')

    if answer_text := re.split(r'[\.|(]', answer_text):
        answer_text = answer_text[0].lower()

    return answer_text.strip()  # type: ignore


logger = logging.getLogger('quiz-bot')
bd_redis = create_redis()
