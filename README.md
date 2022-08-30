# Бот проведения викторины  

Чат-боты позволяют проводит викторину "Вопрос - Ответ", в Telegram и VK.  

Назначение программ:  
- tg_bot.py: чат-бот для Telegram.  
- vk_bot.py: чат-бот для VK.  
- uploading_quiz_data.py: программа для загрузки данных викторины (вопросы, ответы) на сервер Redis.  

### Как установить

Python3 должен быть уже установлен.
Затем используйте `pip` (или `pip3`, есть конфликт с Python2) для установки зависимостей:
```bash
pip install -r requirements.txt
```

### Первоначальная настройка

Создайте папку `quizzes_files` и скопируйте в неё файлы с вопросами и ответами викторин.  

Скопируйте файл `.env.Example` и переименуйте его в `.env`.  

Заполните переменные окружения в файле `.env`:  
`TELEGRAM_TOKEN` - токен телеграм бота.  
`TELEGRAM_CHAT_ID` - id телеграм чата (для вывода сообщений об ошибках чат-бота Telegram).  
`VK_GROUP_TOKEN` - токен группы VK.  
`REDIS_HOST` - адрес сервера Redis.  
`REDIS_PORT` - порт сервера Redis.  
`REDIS_USERNAME` - имя пользователя для сервера Redis.  
`REDIS_PASSWORD` - пароль пользователя для сервера Redis.  

### Как запускать

Для запуска чат-бота Telegram:  
```bash
python tg_bot.py
```

Для запуска чат-бота VK:  
```bash
python vk_bot.py
```

Для загрузки данных викторин в Redis:  
```bash
python uploading_quiz_data.py
```

## Пример использования бота
Пример результата для Telegram:  
![Sample](https://dvmn.org/filer/canonical/1569215494/324/)

Пример результата для ВКонтакте:  
![Sample](https://dvmn.org/filer/canonical/1569215498/325/)

## Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/modules/)
