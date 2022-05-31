"""Functions decorators."""

from functools import wraps
from typing import Any, Callable

from his import ACCOUNT
from wsgilib import JSONMessage

from deployments.authorization import is_admin


__all__ = ['ddb_admin']


def ddb_admin(function: Callable[..., Any]) -> Callable[..., Any]:
    """Checks for admin privileges."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        if ACCOUNT.root or is_admin(ACCOUNT):
            return function(*args, **kwargs)

        return JSONMessage('Unauthorized.', status=403)

    return wrapper
