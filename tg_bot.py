import logging
import sys
from enum import Enum, auto
from functools import partial
from random import choice
from textwrap import dedent

from environs import Env
from telegram import (ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update)
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)
from telegram.utils.helpers import escape_markdown

from quiz_api import create_redis, get_answer_text, get_question_text

logger = logging.getLogger('support-bot')

user_prefix = 'TG'


class State(Enum):
    BUTTON_HANDLERS = auto()


class BotLogsHandler(logging.Handler):
    def __init__(self, telegram_bot, telegram_chat_id) -> None:
        super().__init__()

        self.telegram_chat_id = telegram_chat_id
        self.telegram_bot = telegram_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.telegram_bot.send_message(
            chat_id=self.telegram_chat_id,
            text=dedent(f'ℹ️ {log_entry}')
        )


def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(
        msg='Exception while handling an update:',
        exc_info=context.error
    )


def get_keyboard_markup():
    """Возвращает разметку клавиатуры."""
    custom_keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счёт']
    ]
    return ReplyKeyboardMarkup(
        custom_keyboard,  # type: ignore
        input_field_placeholder='',
        resize_keyboard=True,
    )


def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    user = update.effective_user

    update.message.reply_text(
        f'Добро пожаловать в викторину, {user.first_name}!',
        reply_markup=get_keyboard_markup()
    )

    return State.BUTTON_HANDLERS


def handle_new_question_request(update: Update, context: CallbackContext, bd_redis) -> None:
    """Обработка кнопки 'Новый вопрос'."""
    user_id = update.effective_user.id

    question_id = bd_redis.get(f'{user_prefix}_{user_id}')

    if not question_id:
        question_id = choice(bd_redis.keys('QA_*'))

    logger.info(f'Получен вопрос с id: {question_id}')

    bd_redis.set(f'{user_prefix}_{user_id}', question_id)
    logger.info(f'Установка id вопроса пользователя: {user_id}')

    logger.info(f'Правильный ответ: {get_answer_text(bd_redis, question_id)}')

    question_text = get_question_text(bd_redis, question_id)
    question_text = escape_markdown(question_text, 2)

    message_text = dedent(
        f'''
            *Вопрос:*
            `{question_text}`
        '''
    )
    update.message.reply_text(
        message_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )


def handle_give_up(update: Update, context: CallbackContext, bd_redis) -> None:
    """Обработка кнопки 'Сдаться'."""
    user_id = update.effective_user.id

    if question_id := bd_redis.get(f'{user_prefix}_{user_id}'):
        answer_text = get_answer_text(bd_redis, question_id)
        answer_text = escape_markdown(answer_text, 2)

        message_text = dedent(
            f'''
                *Вот тебе правильный ответ:*
                `{answer_text}`

                Для продолжения, нажми «*Новый вопрос*»
            '''
        )

        update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        logger.info(f'Удаление id вопроса пользователя: {user_id}')
        bd_redis.delete(f'{user_prefix}_{user_id}')


def handle_show_invoice(update: Update, context: CallbackContext) -> None:
    """Обработка кнопки 'Мой счёт'."""
    update.message.reply_text('Данная функция в разработке.')


def handle_solution_attempt(update: Update, context: CallbackContext, bd_redis) -> None:
    """Обрабатывает ответ пользователя."""
    user_id = update.effective_user.id
    user_response = update.message.text

    message_text = 'Неправильно… Попробуешь ещё раз?'

    if question_id := bd_redis.get(f'{user_prefix}_{user_id}'):
        answer_text = get_answer_text(bd_redis, question_id)

        if answer_text == user_response.lower():
            message_text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'

            logger.info(f'Удаление id вопроса пользователя: {user_id}')
            bd_redis.delete(f'{user_prefix}_{user_id}')

        update.message.reply_text(
            message_text,
            reply_markup=get_keyboard_markup()
        )
    else:
        update.message.reply_text(
            'Для продолжения, нажми «Новый вопрос»',
            reply_markup=get_keyboard_markup()
        )


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel and end the conversation."""

    update.message.reply_text(
        'Всего доброго!',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def create_and_start_bot(telegram_token, telegram_chat_id):
    """Creates and launches a telegram bot."""
    logger.info('Старт бота викторины.')
    logger.info('Получение списка id вопросов...')

    bd_redis = create_redis()
    question_ids = bd_redis.keys('QA_*')

    logger.info(
        dedent(
            f'''
            Размер списка вопросов в памяти: {sys.getsizeof(question_ids)}
            Кол-во вопросов викторины: {len(question_ids)}
            '''
        )
    )

    handle_new_question_request_partial = partial(
        handle_new_question_request,
        bd_redis=bd_redis
    )
    handle_give_up_partial = partial(
        handle_give_up,
        bd_redis=bd_redis
    )
    handle_solution_attempt_partial = partial(
        handle_solution_attempt,
        bd_redis=bd_redis
    )

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    conversation = ConversationHandler(
        entry_points=[CommandHandler('start', start)],  # type: ignore
        states={
            State.BUTTON_HANDLERS: [
                MessageHandler(Filters.regex('^Новый вопрос$')
                               & ~Filters.command, handle_new_question_request_partial),
                MessageHandler(Filters.regex('^Сдаться$')
                               & ~Filters.command, handle_give_up_partial),
                MessageHandler(Filters.regex('^Мой счёт$')
                               & ~Filters.command, handle_show_invoice),
                MessageHandler(Filters.text & ~Filters.command,
                               handle_solution_attempt_partial)
            ],
        },  # type: ignore
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('stop', cancel),
        ]  # type: ignore
    )

    dispatcher.add_handler(conversation)
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()

    return dispatcher.bot


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )

    env = Env()
    env.read_env()

    telegram_token = env.str('TELEGRAM_TOKEN')
    telegram_chat_id = env.int('TELEGRAM_CHAT_ID')

    telegram_bot = create_and_start_bot(telegram_token, telegram_chat_id)

    bot_logs_handler = BotLogsHandler(telegram_bot, telegram_chat_id)
    logger.addHandler(bot_logs_handler)


if __name__ == '__main__':
    main()
