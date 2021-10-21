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


def all_deployments() -> Dict[int, List[dict]]:
    """Yields a JSON-ish dict of all deployments."""

    deployments = defaultdict(list)

    for deployment in Deployment.select(cascade=True).where(True):
        json = deployment.to_json(systems=True, skip=['customer'], cascade=2)
        deployments[deployment.customer.id].append(json)

    return deployments


def get_address(address: dict) -> Address:
    """Returns the respective address."""

    street = address['street']
    house_number = address['houseNumber']
    zip_code = address['zipCode']
    city = address['city']
    state = address.get('state')
    return Address.add(street, house_number, zip_code, city, state=state)


def get_deployment(ident: int) -> Deployment:
    """Returns the respective deployment."""

    condition = Deployment.customer == CUSTOMER.id
    condition &= Deployment.id == ident
    return Deployment.select(cascade=True).where(condition).get()


def check_modifyable(deployment: Deployment):
    """Checks whether the deployment may be modified."""

    if ACCOUNT.root:
        return True

    systems = [system.id for system in deployment.systems]

    if systems:
        raise JSONMessage('Systems have already been deployed here.',
                          systems=systems, status=403)

    return True


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

    type_ = DeploymentType(request.json['type'])
    connection = Connection(request.json['connection'])
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
        customer=CUSTOMER.id, type=type_, connection=connection,
        address=address, lpt_address=lpt_address, weather=weather,
        scheduled=scheduled, annotation=annotation, testing=testing)
    deployment.save()
    return JSONMessage('Deployment added.', id=deployment.id, status=201)


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
    return JSONMessage('Deployment patched.', status=200)


@APPLICATION.route('/<int:ident>', methods=['DELETE'], strict_slashes=False)
@authenticated
@authorized('deployments')
def delete(ident: int) -> Response:
    """Deletes the respective deployment."""

    deployment = get_deployment(ident)

    if check_modifyable(deployment):
        deployment.delete_instance()

    return JSONMessage('Deployment deleted.', status=200)


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
    """Handles non-existant deployments."""

    return JSONMessage('No such deployment.', status=404)
