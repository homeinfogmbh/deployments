"""Meta data listing."""

from his import ACCOUNT, authenticated, authorized
from hwdb import HardwareModel
from wsgilib import JSON

from deployments.authorization import is_admin
from deployments.functions import get_customers, get_deployments


__all__ = ["ROUTES"]


@authenticated
@authorized("deployments")
def list_customers() -> JSON:
    """Lists customers."""

    return JSON([customer.to_json(company=True) for customer in get_customers(ACCOUNT)])


@authenticated
@authorized("deployments")
def list_deployments() -> JSON:
    """Lists deployments."""

    return JSON(
        [dep.to_json(address=True, customer=True) for dep in get_deployments(ACCOUNT)]
    )


@authenticated
@authorized("deployments")
def list_hw_models() -> JSON:
    """Lists hardware models."""

    return JSON({model.name: model.value for model in HardwareModel})


@authenticated
@authorized("deployments")
def is_admin_() -> JSON:
    """Returns whether the customer is an admin."""

    return JSON(is_admin(ACCOUNT))


ROUTES = [
    ("GET", "/customers", list_customers),
    ("GET", "/deployments", list_deployments),
    ("GET", "/hw-models", list_hw_models),
    ("GET", "/is-admin", is_admin_),
]
