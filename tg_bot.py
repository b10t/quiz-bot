import re
import redis
import hashlib

data = {
    'scientific-name': 'Canis familiaris'
}


r = redis.Redis()

questions_answers = []

with open('21plus.txt', 'r', encoding='KOI8-R') as quiz_file:
    file_contents = quiz_file.readlines()

current = []
index = -1

while (True):
    try:
        index += 1

        if file_contents[index] == '\n':  # and file_contents[index + 1] == '\n'
            questions_answers.append(''.join(current))
            current = []

            continue

        current.append(file_contents[index])

    except IndexError:
        break

# asd = file_contents.splitlines()

# print(*questions_answers, sep='\n')

question_reg = r'^Вопрос \d+:'
answer_reg = r'^Ответ:'

question_text = ''
answer_text = ''

for line in questions_answers:
    # result = re.split(r'^Вопрос \d+:', line)
    # print(result)

    if re.match(question_reg, line):
        question_text = re.sub(question_reg, '', line).strip()
        print('Question:')
        print(question_text)

        print('hash: ', str(hashlib.md5(question_text.encode()).hexdigest()))

    if re.match(answer_reg, line):
        answer_text = re.sub(answer_reg, '', line).strip()
        print('Answer:')
        print(answer_text)

        if question_text:

            data = {
                'question': question_text,
                'answer': answer_text
            }

            # type: ignore
            md5 = f'QA_{hashlib.md5(question_text.encode()).hexdigest()}'

            # r.json().set(f'QA_{hash(question_text)}', '$', data)
            r.json().set(md5, '$', data)

        break

    # result = re.match(r'^Вопрос \d+:', line)
    # if result:
    #     print(result)
    # if line.startswith('Вопрос') or line.startswith('Ответ'):
    #     book_title, book_author = [text.strip()
    #                                for text in line.split(':')]
    #     # print(*line.split(':').strip())

    #     print(book_title, book_author)


asd = r.keys(pattern='QA_*')

# Удаляет все вопросы с ответами.
r.delete(*asd)

print(asd)
