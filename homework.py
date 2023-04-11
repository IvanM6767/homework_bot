import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exception import RequestError, StatusCodeError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot, message):
    """Отправляет сообщениe в тг."""
    logging.debug(f'Сообщение готово к отправке: "{message}"')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        logging.error(
            f'Бот не смог отправить сообщение "{message}". {error}',
            exc_info=True
        )
    else:
        logging.debug(f'Сообщение не удалось отправить: {message}')


def get_api_answer(timestamp):
    """Получение API с Я.П."""
    logging.debug('Начало запроса к API')
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except requests.RequestException as error:
        raise RequestError(
            f'ENDPOINT {ENDPOINT} недоступен.'
            f'Параметры запроса:'
            f'HEADERS - {HEADERS}, params - {params}. {error}'
        )

    if response.status_code != HTTPStatus.OK:
        raise StatusCodeError(
            f'Запрос {response.url} дропнулся.'
            f'Код ответа API: {response.status_code}.'
            f'Текст ответа API: {response.text}.'
            f'Параметры запроса: HEADERS - {HEADERS}, params - {params}.'
        )

    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError(
            'В ответе API данные не соответствует ожиданиям:'
        )

    keys_response = {
        'homeworks': list,
        'current_date': int
    }
    for key, type_value in keys_response.items():
        value = response.get(key)
        if not key:
            raise KeyError(f'В ответе API нет ключа `{key}`.')
        if not isinstance(value, type_value):
            raise TypeError(
                f'В ответе API под ключом `{key}`'
                f'данные приходят не в виде {type_value}.'
            )


def parse_status(homework):
    """Извлекает статус работы."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        raise KeyError('В ответе API нет ключа `homework_name`')

    status = homework.get('status')
    if not status:
        raise KeyError('В ответе API нет ключа `status`')

    if status not in HOMEWORK_VERDICTS:
        raise ValueError(
            'API возвращает недокументированный'
            'статус домашней работы либо домашку без статуса'
        )

    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = (
            'Отсутствует обязательная переменная окружения.'
            'Программа принудительно остановлена.'
        )
        logging.critical(message)
        sys.exit(message)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)

            homeworks = response.get('homeworks')
            if not homeworks:
                message = 'Список работ за запрошенный период пустой.'
                logging.debug(message, exc_info=True)
            else:
                message = parse_status(homeworks[0])

            timestamp = response.get('current_date')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)

        if last_message != message:
            send_message(bot, message)
            last_message = message
        else:
            logging.debug('Новых статусов нет.')

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(message)s'
    )
    main()
