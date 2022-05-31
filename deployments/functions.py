"""Common functions."""

from his import Account
from hwdb import Deployment
from mdb import Address, Customer
from wsgilib import JSONMessage

from flask import Request
from peewee import Select

from deployments.authorization import can_administer
from deployments.authorization import get_administered_customers
from deployments.authorization import is_admin


__all__ = [
    'can_be_modified',
    'get_address',
    'get_customer',
    'get_customers',
    'get_deployment',
    'get_deployments'
]


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


def get_address(address: dict) -> Address:
    """Returns the respective address."""

    return Address.add(
        address['street'],
        address['houseNumber'],
        address['zipCode'],
        address['city']
    )


def get_customer(request: Request, account: Account) -> Customer:
    """Returns the target customer."""

    if (customer := request.json.pop('customer', None)) is None:
        return account.customer

    try:
        customer = Customer.select(cascade=True).where(
            Customer.id == customer
        ).get()
    except Customer.DoesNotExist:
        raise JSONMessage('No such customer.', status=404)

    if can_administer(account, customer):
        return customer

    raise JSONMessage('Cannot administer the given customer.', status=403)


def get_customers(account: Account) -> Select:
    """Lists available customers."""

    if account.root:
        return Customer.select(cascade=True)

    if is_admin(account):
        return Customer.select(cascade=True).where(
            (Customer.id << set(get_administered_customers(account)))
            | (Customer.id == account.customer)
        )

    return Customer.select(cascade=True).where(Customer.id == account.customer)


def get_deployment(ident: int, account: Account) -> Deployment:
    """Returns the selected order of the given customer."""

    return get_deployments(account).where(Deployment.id == ident).get()


def get_deployments(account: Account) -> Select:
    """Returns the selected deployments."""

    if account.root:
        return Deployment.select(cascade=True).where(True)

    if is_admin(account):
        return Deployment.select(cascade=True).where(
            (Deployment.customer << set(get_administered_customers(account)))
            | (Deployment.customer == account.customer)
        )

    return Deployment.select(cascade=True).where(
        Deployment.customer == account.customer
    )
