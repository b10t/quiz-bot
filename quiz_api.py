import re
from random import choice

import redis_tools


def get_question_id(user_id, prefix):
    """Возвращает id вопроса пользователя."""
    return redis_tools.get_value(f'{prefix}_{user_id}')


def set_question_id(user_id, qa_id, prefix):
    """Устанавливает id вопроса пользователя."""
    return redis_tools.set_value(f'{prefix}_{user_id}', qa_id)


def delete_question_id(user_id, prefix):
    """Удаляет текущий id вопроса пользователя."""
    redis_tools.delete_key(f'{prefix}_{user_id}')


def get_random_question_id(question_ids):
    """Возвращает случайны id вопроса."""
    return choice(question_ids)


def fetch_questions():
    """Возвращает id всех вопросов"""
    return redis_tools.fetch_keys('QA_*')


def get_question_text(question_id):
    """Возвращает текст вопроса."""
    qa_context = redis_tools.get_json_value(question_id)
    return qa_context.get('question')


def get_answer_text(question_id) -> str:
    """Возвращает текст ответа."""
    answer_text = redis_tools.get_json_value(question_id).get('answer')

    if answer_text := re.split(r'[\.|(]', answer_text):
        answer_text = answer_text[0].lower()

    return answer_text  # type: ignore
