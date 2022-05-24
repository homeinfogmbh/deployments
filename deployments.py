"""HIS service to handle system deployments."""

from collections import defaultdict
from contextlib import suppress
from datetime import datetime
from typing import Union

from flask import request

from his import ACCOUNT
from his import CUSTOMER
from his import Account
from his import authenticated
from his import authorized
from his import root
from his import Application
from hwdb import Connection, Deployment, DeploymentType
from mdb import Address, Customer
from wsgilib import JSON, JSONMessage


__all__ = ['APPLICATION']


APPLICATION = Application('Deployments', debug=True)


def all_deployments() -> dict[int, list[dict]]:
    """Yields a JSON-ish dict of all deployments."""

    deployments = defaultdict(list)

    for deployment in Deployment.select(cascade=True).where(True):
        deployments[deployment.customer.id].append(
            deployment.to_json(systems=True, skip=['customer'], cascade=2)
        )

    return deployments


def get_address(address: dict) -> Address:
    """Returns the respective address."""

    return Address.add(
        address['street'],
        address['houseNumber'],
        address['zipCode'],
        address['city']
    )


def get_deployment(ident: int, customer: Union[Customer, int]) -> Deployment:
    """Returns the respective deployment."""

    return Deployment.select(cascade=True).where(
        (Deployment.id == ident)
        & (Deployment.customer == customer)
    ).get()


def can_be_modified(deployment: Deployment, account: Account) -> bool:
    """Checks whether the deployment may be modified."""

    if account.root:
        return True

    if systems := [system.id for system in deployment.systems]:
        raise JSONMessage(
            'Systems have already been deployed here.', systems=systems,
            status=403
        )

    return True


@APPLICATION.route('/', methods=['GET'], strict_slashes=False)
@authenticated
@authorized('deployments')
def list_() -> JSON:
    """Lists the customer's deployments."""

    return JSON([
        deployment.to_json(systems=True, skip=['customer'], cascade=2)
        for deployment in Deployment.select().where(
            Deployment.customer == CUSTOMER.id)
    ])


@APPLICATION.route('/all', methods=['GET'], strict_slashes=False)
@authenticated
@root
def all_() -> JSON:
    """Lists all customers' deployments."""

    return JSON(all_deployments())


@APPLICATION.route('/', methods=['POST'], strict_slashes=False)
@authenticated
@authorized('deployments')
def add() -> JSONMessage:
    """Adds a deployment."""

    type_ = DeploymentType(request.json['type'])
    connection = Connection(request.json['connection'])

    if not (address := request.json.get('address')):
        return JSONMessage('No address specified.', status=400)

    address = get_address(address)
    address.save()
    lpt_address = request.json.get('lptAddress')

    if lpt_address:
        lpt_address = get_address(lpt_address)
        lpt_address.save()
    else:
        lpt_address = None

    weather = request.json.get('weather')

    if (scheduled := request.json.get('scheduled')) is not None:
        scheduled = datetime.fromisoformat(scheduled)

    annotation = request.json.get('annotation')
    testing = request.json.get('testing')
    deployment = Deployment(
        customer=CUSTOMER.id, type=type_, connection=connection,
        address=address, lpt_address=lpt_address, weather=weather,
        scheduled=scheduled, annotation=annotation, testing=testing
    )
    deployment.save()
    return JSONMessage('Deployment added.', id=deployment.id, status=201)


@APPLICATION.route('/<int:ident>', methods=['PATCH'], strict_slashes=False)
@authenticated
@authorized('deployments')
def patch(ident: int) -> JSONMessage:
    """Modifies the respective deployment."""

    can_be_modified(deployment := get_deployment(ident, CUSTOMER.id), ACCOUNT)

    if type_ := request.json.get('type'):
        try:
            deployment.type = DeploymentType(type_)
        except ValueError:
            return JSONMessage('Invalid type.', status=400)

    if connection := request.json.get('connection'):
        try:
            deployment.connection = Connection(connection)
        except ValueError:
            return JSONMessage('Invalid connection.', status=400)

    if address := request.json.get('address'):
        address = get_address(address)
        address.save()
        deployment.address = address

    if lpt_address := request.json.get('lptAddress'):
        lpt_address = get_address(lpt_address)
        lpt_address.save()
        deployment.lpt_address = lpt_address

    with suppress(KeyError):
        deployment.weather = request.json['weather']

    with suppress(KeyError):
        if (scheduled := request.json['scheduled']) is not None:
            scheduled = datetime.fromisoformat(scheduled)

        deployment.scheduled = scheduled

    with suppress(KeyError):
        deployment.annotation = request.json['annotation']

    with suppress(KeyError):
        deployment.testing = request.json['testing']

    deployment.save()
    return JSONMessage('Deployment patched.', status=200)


@APPLICATION.route('/<int:ident>', methods=['DELETE'], strict_slashes=False)
@authenticated
@authorized('deployments')
def delete(ident: int) -> JSONMessage:
    """Deletes the respective deployment."""

    if can_be_modified(
            deployment := get_deployment(ident, CUSTOMER.id), ACCOUNT
    ):
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
    """Handles non-existent deployments."""

    return JSONMessage('No such deployment.', status=404)
