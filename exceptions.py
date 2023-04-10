class IsNot200Error(Exception):
    """Ответ сервер не 200."""


class EmptyDictorListError(Exception):
    """Пустой словарь или список."""


class StatusResponceError(Exception):
    """Ошибка статуса документа."""


class ApiError(Exception):
    """Ошибка в запросе API"""


class JSONDecoderError(Exception):
    """Ошибка с Json файлом"""