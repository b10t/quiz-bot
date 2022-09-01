import glob
import hashlib
import logging
import os
import re

from quiz_api import create_redis

logger = logging.getLogger('quiz-bot')


def save_qa_to_redis(bd_redis, questions_answers):
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

                question_hash = hashlib.md5(
                    question_text.encode('utf-8')
                ).hexdigest()

                bd_redis.json().set(
                    f'QA_{question_hash}',
                    '$',
                    data
                )


def get_qa_from_file(quiz_content):
    """Получает из файла вопросы и ответы викторины."""
    questions_answers = []

    current_qa = []

    for text in quiz_content:
        if text == '\n':
            questions_answers.append(''.join(current_qa))
            current_qa = []
            continue

        current_qa.append(text)

    return questions_answers


def processing_quizzes_files(bd_redis, folder='quizzes_files'):
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

            save_qa_to_redis(bd_redis, questions_answers)


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )

    bd_redis = create_redis()

    if keys := bd_redis.keys('QA_*'):
        bd_redis.delete(*keys)

    processing_quizzes_files(bd_redis)


if __name__ == '__main__':
    main()
