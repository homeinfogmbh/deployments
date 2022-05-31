"""Common functions."""

from collections import defaultdict
from typing import Union

from his import Account
from hwdb import Deployment
from mdb import Address, Customer
from wsgilib import JSONMessage


__all__ = [
    'all_deployments',
    'can_be_modified',
    'get_address',
    'get_deployment'
]


def all_deployments() -> dict[int, list[dict]]:
    """Yields a JSON-ish dict of all deployments."""

    deployments = defaultdict(list)

    for deployment in Deployment.select(cascade=True).where(True):
        deployments[deployment.customer.id].append(
            deployment.to_json(systems=True, skip=['customer'], cascade=2)
        )

    return deployments


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


def get_deployment(ident: int, customer: Union[Customer, int]) -> Deployment:
    """Returns the respective deployment."""

    return Deployment.select(cascade=True).where(
        (Deployment.id == ident)
        & (Deployment.customer == customer)
    ).get()
