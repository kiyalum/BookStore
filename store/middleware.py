import logging


logger = logging.getLogger('store')


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_info = request.user if request.user.is_authenticated else "Anonymous"
        logger.info(f"Path: {request.path} | User: {user_info} | Method: {request.method}")

        response = self.get_response(request)
        return response
