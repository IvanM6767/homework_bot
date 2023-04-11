class StatusCodeError(Exception):
    """Вызывается когда возвращается код отличный от 200."""

    pass


class RequestError(Exception):
    """Обрабатываются случайные сбои и ошибки при запросе к API."""

    pass