"""WSGI interfaces to manage deployments."""

from his import Application
from hwdb import Deployment
from wsgilib import JSONMessage

from deployments.wsgi import administration, checklist, common, metadata


__all__ = ['APPLICATION']


APPLICATION = Application('Deployments', debug=True)
ROUTES = (
    *administration.ROUTES, *checklist.ROUTES, *common.ROUTES,
    *metadata.ROUTES
)
APPLICATION.add_routes(ROUTES)


@APPLICATION.errorhandler(KeyError)
def handle_key_error(error: KeyError) -> JSONMessage:
    """Handles key errors."""

    return JSONMessage('Missing JSON key.', key=str(error), status=400)


@APPLICATION.errorhandler(ValueError)
def handle_value_error(error: ValueError) -> JSONMessage:
    """Handles value errors."""

    return JSONMessage('Invalid value.', value=str(error), status=400)


@APPLICATION.errorhandler(Deployment.DoesNotExist)
def handle_no_such_deployment(_: Deployment.DoesNotExist) -> JSONMessage:
    """Handles non-existent deployments."""

    return JSONMessage('No such deployment.', status=404)
