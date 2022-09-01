import logging
import re

from environs import Env

logger = logging.getLogger('quiz-bot')


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
