import logging
import re
import sys
from enum import Enum, auto
from random import choice
from textwrap import dedent

from environs import Env
from telegram import (ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update)
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, RegexHandler, Updater)
from telegram.utils.helpers import escape_markdown

import redis_tools

logger = logging.getLogger('support-bot')

question_ids = []


class State(Enum):
    BUTTON_HANDLERS = auto()


def get_question_id(user_id):
    """Возвращает id вопроса пользователя."""
    return redis_tools.get_value(f'TG_{user_id}')


def set_question_id(user_id, qa_id):
    """Устанавливает id вопроса пользователя."""
    return redis_tools.set_value(f'TG_{user_id}', qa_id)


def delete_question_id(user_id):
    """Удаляет текущий id вопроса пользователя."""
    redis_tools.delete_key(f'TG_{user_id}')


def get_random_question_id():
    """Возвращает случайны id вопроса."""
    return choice(question_ids)


class BotLogsHandler(logging.Handler):
    def __init__(self, telegram_bot, telegram_chat_id) -> None:
        super().__init__()

        self.telegram_chat_id = telegram_chat_id
        self.telegram_bot = telegram_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.telegram_bot.send_message(
            chat_id=self.telegram_chat_id,
            text=dedent(log_entry)
        )


def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(
        msg='Exception while handling an update:',
        exc_info=context.error
    )


def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    user = update.effective_user

    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счёт']]
    reply_markup = ReplyKeyboardMarkup(
        custom_keyboard,  # type: ignore
        input_field_placeholder='',
        resize_keyboard=True,
    )

    update.message.reply_text(
        f'Добро пожаловать в викторину, {user.first_name}!',
        reply_markup=reply_markup
    )

    # context.user_data.get(States.START_OVER)
    # context.user_data[States.START_OVER] = False

    return State.BUTTON_HANDLERS


def process_buttons(update: Update, context: CallbackContext) -> None:
    """Handles button pressing."""
    user_id = update.effective_user.id
    message_text = update.message.text

    if message_text == 'Новый вопрос':
        question_id = get_random_question_id()
        logger.info(f'Получен вопрос с id: {question_id}')

        set_question_id(user_id, question_id)
        logger.info(f'Установка id вопроса пользователя: {user_id}')

        question_text = redis_tools.get_json_value(question_id).get('question')
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

    if message_text == 'Сдаться':
        update.message.reply_text(
            'Вот тебе правильный ответ: .... \nДля продолжения, нажми "Новый вопрос"')

        logger.info(f'Удаление id вопроса пользователя: {user_id}')
        delete_question_id(user_id)

    if message_text == 'Мой счёт':
        update.message.reply_text('Данная функция в разработке.')


def process_message(update: Update, context: CallbackContext) -> None:
    """Processes a message from the user."""
    user_id = update.effective_user.id
    message_text = update.message.text

    # google_project_id = env.str('GOOGLE_PROJECT_ID')

    # _, message_text = detect_intent_text(
    #     google_project_id,
    #     session_id,
    #     message_text
    # )

    update.message.reply_text(message_text)


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel and end the conversation."""

    update.message.reply_text(
        'Всего доброго!',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def create_and_start_bot(telegram_token, telegram_chat_id):
    """Creates and launches a telegram bot."""
    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    conversation = ConversationHandler(
        entry_points=[CommandHandler('start', start)],  # type: ignore
        states={
            # StateEnum.LOCATE: [MessageHandler((Filters.text | Filters.location) & ~Filters.command, get_locate)],
            State.BUTTON_HANDLERS: [MessageHandler(Filters.regex('^(Новый вопрос|Сдаться|Мой счёт)$') & ~Filters.command, process_buttons),
                                    MessageHandler(Filters.text & ~Filters.command, process_message)],
            # StateEnum.TYPE: [MessageHandler(Filters.text & ~Filters.command, get_type)],
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


if __name__ == '__main__':
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

    logger.info('Старт бота.')
    logger.info('Получение списка id вопросов...')

    question_ids = redis_tools.fetch_keys('QA_*')

    logger.info(
        dedent(
            f'''
            Размер списка вопросов в памяти: {sys.getsizeof(question_ids)}
            Кол-во вопросов викторины: {len(question_ids)}
            '''
        )
    )
