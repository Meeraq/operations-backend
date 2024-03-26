import logging
from .models import APILog

logger = logging.getLogger(__name__)


class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            user = request.user if request.user.is_authenticated else None
            log_entry = APILog(path=request.path, method=request.method, user=user)
            log_entry.save()
            logger.info(
                f"API Request: {request.path} | Type: {request.method} | User: {user.username}"
            )
        except:
            pass
        return response
