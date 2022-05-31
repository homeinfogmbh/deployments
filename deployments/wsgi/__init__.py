"""WSGI interfaces to manage deployments."""

from his import Application
from hwdb import Deployment
from wsgilib import JSONMessage

from deployments.wsgi.manage import all_, list_, add, patch, delete


__all__ = ['APPLICATION']


APPLICATION = Application('Deployments', debug=True)
APPLICATION.route('/all', methods=['GET'], strict_slashes=False)(all_)
APPLICATION.route('/', methods=['GET'], strict_slashes=False)(list_)
APPLICATION.route('/', methods=['POST'], strict_slashes=False)(add)
APPLICATION.route('/<int:ident>', methods=['PATCH'], strict_slashes=False)(
    patch
)
APPLICATION.route('/<int:ident>', methods=['DELETE'], strict_slashes=False)(
    delete
)


@APPLICATION.errorhandler(KeyError)
def handle_key_error(error: KeyError) -> JSONMessage:
    """Handles key errors."""

    return JSONMessage('Missing JSON key.', key=str(error))


@APPLICATION.errorhandler(ValueError)
def handle_value_error(error: ValueError) -> JSONMessage:
    """Handles value errors."""

    return JSONMessage('Invalid value.', value=str(error))


@APPLICATION.errorhandler(Deployment.DoesNotExist)
def handle_no_such_deployment(_: Deployment.DoesNotExist) -> JSONMessage:
    """Handles non-existent deployments."""

    return JSONMessage('No such deployment.', status=404)
