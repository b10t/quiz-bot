import logging
import sys
from textwrap import dedent

import vk_api
from environs import Env
from vk_api.exceptions import ApiError
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id

from quiz_api import (delete_question_id, fetch_questions, get_answer_text,
                      get_question_id, get_question_text,
                      get_random_question_id, set_question_id)

logger = logging.getLogger('support-bot')

question_ids = []
user_prefix = 'VK'


def get_keyboard_markup():
    """Возвращает разметку клавиатуры."""
    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.SECONDARY)

    return keyboard.get_keyboard()


def handle_new_question_request(event, vk_api) -> None:
    """Обработка кнопки 'Новый вопрос'."""
    user_id = event.user_id

    question_id = get_question_id(user_id, user_prefix)

    if not question_id:
        question_id = get_random_question_id(question_ids)

    logger.info(f'Получен вопрос с id: {question_id}')

    set_question_id(user_id, question_id, user_prefix)
    logger.info(f'Установка id вопроса пользователя: {user_id}')

    logger.info(f'Правильный ответ: {get_answer_text(question_id)}')

    question_text = get_question_text(question_id)

    message_text = dedent(
        f'''
            Вопрос:
            {question_text}
        '''
    )
    vk_api.messages.send(
        user_id=user_id,
        message=message_text,
        keyboard=get_keyboard_markup(),
        random_id=get_random_id()
    )


def handle_give_up(event, vk_api) -> None:
    """Обработка кнопки 'Сдаться'."""
    user_id = event.user_id

    if question_id := get_question_id(user_id, user_prefix):
        answer_text = get_answer_text(question_id)

        message_text = dedent(
            f'''
                Вот тебе правильный ответ:
                {answer_text}

                Для продолжения, нажми «Новый вопрос»
            '''
        )

        vk_api.messages.send(
            user_id=user_id,
            message=message_text,
            keyboard=get_keyboard_markup(),
            random_id=get_random_id()
        )

        logger.info(f'Удаление id вопроса пользователя: {user_id}')
        delete_question_id(user_id, user_prefix)


def handle_show_invoice(event, vk_api) -> None:
    """Обработка кнопки 'Мой счёт'."""
    user_id = event.user_id
    message_text = 'Данная функция в разработке.'

    vk_api.messages.send(
        user_id=user_id,
        message=message_text,
        keyboard=get_keyboard_markup(),
        random_id=get_random_id()
    )


def handle_solution_attempt(event, vk_api) -> None:
    """Обрабатывает ответ пользователя."""
    user_id = event.user_id
    user_response = event.text

    message_text = 'Неправильно… Попробуешь ещё раз?'

    if question_id := get_question_id(user_id, user_prefix):
        answer_text = get_answer_text(question_id)

        if answer_text == user_response.lower():
            message_text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'

            logger.info(f'Удаление id вопроса пользователя: {user_id}')
            delete_question_id(user_id, user_prefix)

        vk_api.messages.send(
            user_id=user_id,
            message=message_text,
            keyboard=get_keyboard_markup(),
            random_id=get_random_id()
        )
    else:
        vk_api.messages.send(
            user_id=user_id,
            message='Для продолжения, нажми «Новый вопрос»',
            keyboard=get_keyboard_markup(),
            random_id=get_random_id()
        )


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )

    logger.info('Старт бота викторины.')
    logger.info('Получение списка id вопросов...')

    question_ids = fetch_questions()

    logger.info(
        dedent(
            f'''
            Размер списка вопросов в памяти: {sys.getsizeof(question_ids)}
            Кол-во вопросов викторины: {len(question_ids)}
            '''
        )
    )

    env = Env()
    env.read_env()

    vk_group_token = env.str('VK_GROUP_TOKEN')

    vk_session = vk_api.VkApi(token=vk_group_token)
    vk_api = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            try:
                if event.text == 'Новый вопрос':
                    handle_new_question_request(event, vk_api)

                elif event.text == 'Сдаться':
                    handle_give_up(event, vk_api)

                elif event.text == 'Мой счёт':
                    handle_show_invoice(event, vk_api)

                else:
                    handle_solution_attempt(event, vk_api)
            except ApiError as api_error:
                error_code = api_error.error.get('error_code')
                error_msg = api_error.error.get('error_msg')

                logger.error(
                    f'[{error_code}]: {error_msg}'
                )
