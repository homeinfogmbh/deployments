"""HIS service to handle system deployments."""

from collections import defaultdict
from contextlib import suppress

from flask import request

from his import CUSTOMER, authenticated, authorized, root, Application
from mdb import Address
from terminallib import Connection, Deployment, Type
from timelib import strpdatetime
from wsgilib import Error, JSON


__all__ = ['APPLICATION']


APPLICATION = Application('Deployments', debug=True)


def _all_deployments():
    """Yields a JSON-ish dict of all deployments."""

    deployments = defaultdict(list)

    for deployment in Deployment:
        json = deployment.to_json(systems=True, skip='customer', cascade=2)
        deployments[deployment.customer.id].append(json)

    return deployments


def _get_address(address):
    """Returns the respective address."""

    try:
        street = address['street']
    except KeyError:
        raise Error('No street specified.')

    try:
        house_number = address['houseNumber']
    except KeyError:
        raise Error('No house number specified.')

    try:
        zip_code = address['zipCode']
    except KeyError:
        raise Error('No ZIP code specified.')

    try:
        city = address['city']
    except KeyError:
        raise Error('No city specified.')

    state = address.get('state')
    address = (street, house_number, zip_code, city)
    return Address.add_by_address(address, state=state)


def _get_deployment(ident):
    """Returns the respective deployment."""

    try:
        return Deployment.get(
            (Deployment.customer == CUSTOMER.id)
            & (Deployment.id == ident))
    except Deployment.DoesNotExist:
        raise Error('No such deployment.', status=404)


@authenticated
@authorized('deployments')
def list_():
    """Lists the customer's deployments."""

    return JSON([
        deployment.to_json(systems=True, skip='customer', cascade=2)
        for deployment in Deployment.select().where(
            Deployment.customer == CUSTOMER.id)])


@authenticated
@root
def all_():
    """Lists all customers' deployments."""

    return JSON(_all_deployments())


@authenticated
@authorized('deployments')
def add():
    """Adds a deployment."""

    try:
        type_ = Type(request.json['type'])
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

    address = _get_address(address)
    address.save()
    lpt_address = request.json.get('lptAddress')

    if lpt_address:
        lpt_address = _get_address(lpt_address)
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
    json = {'message': 'Deployment added.', 'id': deployment.id}
    return JSON(json, status=201)


def patch(ident):
    """Modifies the respective deployment."""

    deployment = _get_deployment(ident)

    try:
        deployment.type = Type(request.json['type'])
    except KeyError:
        pass
    except ValueError:
        raise Error('Invalid type.')

    try:
        deployment.connection = Connection(request.json['connection'])
    except KeyError:
        pass
    except ValueError:
        raise Error('Invalid connection.')

    address = request.json.get('address')

    if address:
        address = _get_address(address)
        address.save()
        deployment.address = address

    lpt_address = request.json.get('lptAddress')

    if lpt_address:
        lpt_address = _get_address(lpt_address)
        lpt_address.save()
        deployment.lpt_address = lpt_address

    with suppress(KeyError):
        deployment.weather = request.json['weather']

    try:
        scheduled = request.json['scheduled']
    except KeyError:
        pass
    else:
        deployment.scheduled = strpdatetime(scheduled)

    with suppress(KeyError):
        deployment.annotation = request.json['annotation']

    with suppress(KeyError):
        deployment.testing = request.json['testing']

    deployment.save()
    return 'Deployment patched.'


def delete(ident):
    """Deletes the respective deployment."""

    deployment = _get_deployment(ident)
    systems = [system.id for system in deployment.systems]

    if systems:
        json = {
            'message': 'Systems have already been deployed here.',
            'systems': systems}
        return JSON(json, status=403)

    deployment.delete_instance()
    return 'Deployment deleted.'


ROUTES = (
    ('GET', '/', list_),
    ('GET', '/all', all_),
    ('POST', '/', add),
    ('PATCH', '/<int:ident>', patch),
)
APPLICATION.add_routes(ROUTES)
