"""Manage deployments."""

from contextlib import suppress
from datetime import datetime

from flask import request

from his import ACCOUNT
from his import CUSTOMER
from his import authenticated
from his import authorized
from his import root
from hwdb import Connection, Deployment, DeploymentType
from wsgilib import JSON, JSONMessage

from deployments.functions import all_deployments
from deployments.functions import can_be_modified
from deployments.functions import get_address
from deployments.functions import get_deployment


__all__ = ['all_', 'list_', 'add', 'patch', 'delete']


@authenticated
@root
def all_() -> JSON:
    """Lists all customers' deployments."""

    return JSON(all_deployments())


@authenticated
@authorized('deployments')
def list_() -> JSON:
    """Lists the customer's deployments."""

    return JSON([
        deployment.to_json(systems=True, skip=['customer'], cascade=2)
        for deployment in Deployment.select().where(
            Deployment.customer == CUSTOMER.id)
    ])


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

    if (scheduled := request.json.get('scheduled')) is not None:
        scheduled = datetime.fromisoformat(scheduled)

    annotation = request.json.get('annotation')
    testing = request.json.get('testing')
    deployment = Deployment(
        customer=CUSTOMER.id, type=type_, connection=connection,
        address=address, lpt_address=lpt_address, scheduled=scheduled,
        annotation=annotation, testing=testing
    )
    deployment.save()
    return JSONMessage('Deployment added.', id=deployment.id, status=201)


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
        if (scheduled := request.json['scheduled']) is not None:
            scheduled = datetime.fromisoformat(scheduled)

        deployment.scheduled = scheduled

    with suppress(KeyError):
        deployment.annotation = request.json['annotation']

    with suppress(KeyError):
        deployment.testing = request.json['testing']

    deployment.save()
    return JSONMessage('Deployment patched.', status=200)


@authenticated
@authorized('deployments')
def delete(ident: int) -> JSONMessage:
    """Deletes the respective deployment."""

    if can_be_modified(
            deployment := get_deployment(ident, CUSTOMER.id), ACCOUNT
    ):
        deployment.delete_instance()

    return JSONMessage('Deployment deleted.', status=200)
