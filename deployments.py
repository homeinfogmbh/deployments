"""HIS service to handle system deployments."""

from collections import defaultdict
from contextlib import suppress
from typing import Dict, List

from flask import Response, request

from his import ACCOUNT
from his import CUSTOMER
from his import authenticated
from his import authorized
from his import root
from his import Application
from hwdb import Connection, Deployment, DeploymentType
from mdb import Address
from timelib import strpdatetime
from wsgilib import Error, JSON, JSONMessage


__all__ = ['APPLICATION']


APPLICATION = Application('Deployments', debug=True)
MSG_NO_SUCH_DEPLOYMENT = JSONMessage('No such deployment.', status=404)
MSG_DEPLOYMENT_ADDED = JSONMessage('Deployment added.', status=201)
MSG_SYSTEMS_DEPLOYED = JSONMessage(
    'Systems have already been deployed here.', status=403)
MSG_DEPLOYMENT_PATCHED = JSONMessage('Deployment patched.', status=200)
MSG_DEPLOYMENT_DELETED = JSONMessage('Deployment deleted.', status=200)


def all_deployments() -> Dict[int, List[dict]]:
    """Yields a JSON-ish dict of all deployments."""

    deployments = defaultdict(list)

    for deployment in Deployment:
        json = deployment.to_json(systems=True, skip=['customer'], cascade=2)
        deployments[deployment.customer.id].append(json)

    return deployments


def get_address(address: dict) -> Address:
    """Returns the respective address."""

    try:
        street = address['street']
    except KeyError:
        raise Error('No street specified.') from None

    try:
        house_number = address['houseNumber']
    except KeyError:
        raise Error('No house number specified.') from None

    try:
        zip_code = address['zipCode']
    except KeyError:
        raise Error('No ZIP code specified.') from None

    try:
        city = address['city']
    except KeyError:
        raise Error('No city specified.') from None

    state = address.get('state')
    address = (street, house_number, zip_code, city)
    return Address.add_by_address(address, state=state)


def get_deployment(ident: int) -> Deployment:
    """Returns the respective deployment."""

    try:
        return Deployment.get(
            (Deployment.customer == CUSTOMER.id)
            & (Deployment.id == ident))
    except Deployment.DoesNotExist:
        raise MSG_NO_SUCH_DEPLOYMENT from None


def check_modifyable(deployment: Deployment):
    """Checks whether the deployment may be modified."""

    if ACCOUNT.root:
        return

    systems = [system.id for system in deployment.systems]

    if systems:
        raise MSG_SYSTEMS_DEPLOYED.update(systems=systems)


@APPLICATION.route('/', methods=['GET'], strict_slashes=False)
@authenticated
@authorized('deployments')
def list_() -> Response:
    """Lists the customer's deployments."""

    return JSON([
        deployment.to_json(systems=True, skip=['customer'], cascade=2)
        for deployment in Deployment.select().where(
            Deployment.customer == CUSTOMER.id)])


@APPLICATION.route('/all', methods=['GET'], strict_slashes=False)
@authenticated
@root
def all_() -> Response:
    """Lists all customers' deployments."""

    return JSON(all_deployments())


@APPLICATION.route('/', methods=['POST'], strict_slashes=False)
@authenticated
@authorized('deployments')
def add() -> Response:
    """Adds a deployment."""

    try:
        deployment_type = DeploymentType(request.json['type'])
    except KeyError:
        return ('No type specified.', 400)
    except ValueError:
        return ('Invalid type.', 400)

    try:
        connection = Connection(request.json['connection'])
    except KeyError:
        return ('No connection specified.', 400)
    except ValueError:
        return ('Invalid connection.', 400)

    address = request.json.get('address')

    if not address:
        return ('No address specified.', 400)

    address = get_address(address)
    address.save()
    lpt_address = request.json.get('lptAddress')

    if lpt_address:
        lpt_address = get_address(lpt_address)
        lpt_address.save()
    else:
        lpt_address = None

    weather = request.json.get('weather')
    scheduled = strpdatetime(request.json.get('scheduled'))
    annotation = request.json.get('annotation')
    testing = request.json.get('testing')
    deployment = Deployment(
        customer=CUSTOMER.id, type=deployment_type, connection=connection,
        address=address, lpt_address=lpt_address, weather=weather,
        scheduled=scheduled, annotation=annotation, testing=testing)
    deployment.save()
    return MSG_DEPLOYMENT_ADDED.update(id=deployment.id)


@APPLICATION.route('/<int:ident>', methods=['PATCH'], strict_slashes=False)
@authenticated
@authorized('deployments')
def patch(ident: int) -> Response:
    """Modifies the respective deployment."""

    deployment = get_deployment(ident)
    check_modifyable(deployment)

    try:
        with suppress(KeyError):
            deployment.type = DeploymentType(request.json['type'])
    except ValueError:
        return Error('Invalid type.')

    try:
        with suppress(KeyError):
            deployment.connection = Connection(request.json['connection'])
    except ValueError:
        return Error('Invalid connection.')

    address = request.json.get('address')

    if address:
        address = get_address(address)
        address.save()
        deployment.address = address

    lpt_address = request.json.get('lptAddress')

    if lpt_address:
        lpt_address = get_address(lpt_address)
        lpt_address.save()
        deployment.lpt_address = lpt_address

    with suppress(KeyError):
        deployment.weather = request.json['weather']

    try:
        with suppress(KeyError):
            deployment.scheduled = strpdatetime(request.json['scheduled'])
    except ValueError:
        return Error('Invalid connection.')

    with suppress(KeyError):
        deployment.annotation = request.json['annotation']

    with suppress(KeyError):
        deployment.testing = request.json['testing']

    deployment.save()
    return MSG_DEPLOYMENT_PATCHED


@APPLICATION.route('/<int:ident>', methods=['PATCH'], strict_slashes=False)
@authenticated
@authorized('deployments')
def delete(ident: int) -> Response:
    """Deletes the respective deployment."""

    deployment = get_deployment(ident)
    check_modifyable(deployment)
    deployment.delete_instance()
    return MSG_DEPLOYMENT_DELETED
