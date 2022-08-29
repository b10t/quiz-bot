import glob
import hashlib
import logging
import os
import re

import redis_tools

logger = logging.getLogger('quiz-bot')


def get_qa_key(question):
    """Возвращает ключ для хранения вопросов в базе данных."""
    return 'QA_%s' % hashlib.md5(question.encode('utf-8')).hexdigest()


def save_qa_to_redis(questions_answers):
    """Сохраняет вопросы и ответы в БД redis."""
    question_reg = r'^Вопрос \d+:'
    answer_reg = r'^Ответ:'

    question_text = ''
    answer_text = ''

    for qa_text in questions_answers:
        if re.match(question_reg, qa_text):
            question_text = re.sub(question_reg, '', qa_text)

        if re.match(answer_reg, qa_text):
            answer_text = re.sub(answer_reg, '', qa_text)

            if question_text:
                data = {
                    'question': re.sub('^\s+|\n|\r|\t|\s+$', '', question_text),
                    'answer': re.sub('^\s+|\n|\r|\t|\s+$', '', answer_text),
                }

                redis_tools.set_json_value(
                    get_qa_key(question_text),
                    data
                )


def get_qa_from_file(quiz_content):
    """Получает из файла вопросы и ответы викторины."""
    questions_answers = []

    current_qa = []
    index = -1

    while (True):
        try:
            index += 1

            if quiz_content[index] == '\n':
                questions_answers.append(''.join(current_qa))
                current_qa = []
                continue

            current_qa.append(quiz_content[index])

        except IndexError:
            break

    return questions_answers


def processing_quizzes_files(folder='quizzes_files'):
    """Обрабатывает файлы с викторинами из папки."""
    if not os.path.isdir(folder):
        logger.error(f'The folder with quizzes was not found: {folder}')
        return

    for quiz_filename in glob.glob(os.path.join(folder, '*.txt')):
        logger.info(f'Found quiz file: {quiz_filename}')

        with open(quiz_filename, 'r', encoding='KOI8-R') as quiz_file:
            questions_answers = get_qa_from_file(
                quiz_file.readlines()
            )

            save_qa_to_redis(questions_answers)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )

    redis_tools.delete_all_keys('QA_*')

    processing_quizzes_files()
