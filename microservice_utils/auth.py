from flask import request
from flask.wrappers import Request
from functools import wraps
from microservice_utils.settings import logger
from typing import Callable


def authorization_wrap(token_callback: Callable[[Request, str], None]):
    
    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get("Authorization", None)
            if token is None:
                logger.error("Authorization header missing")
                return {"error": "Authorization header missing"}, 401

            try:
                token_callback(request, token)

            except Exception as e:
                logger.error(str(e))
                return {"error": str(e)}, 401

            return f(*args, **kwargs)

        return decorated

    return token_required
