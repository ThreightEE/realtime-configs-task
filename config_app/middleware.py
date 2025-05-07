import logging
import os

logger = logging.getLogger(__name__)

class LogRequestPIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        pid = os.getpid()
        logger.info(f"MIDDLEWARE - PID {pid} - request {request.method} {request.path}")
        
        response = self.get_response(request)
        return response
    