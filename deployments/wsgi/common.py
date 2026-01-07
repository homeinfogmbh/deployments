"""User-oriented endpoints."""

from contextlib import suppress
from datetime import datetime

from flask import request

from his import ACCOUNT
from his import CUSTOMER
from his import authenticated
from his import authorized
from his import Account
from hwdb import Connection, DeploymentType,Deployment
from wsgilib import JSON, JSONMessage

from deployments.functions import can_be_modified
from deployments.functions import get_address
from deployments.functions import get_deployment
from deployments.functions import get_deployments


__all__ = ["ROUTES"]


@authenticated
@authorized("deployments")
def list_() -> JSON:
    """List deployments."""

    return JSON(
        [
            deployment.to_json(address=True, customer=True)
            for deployment in get_deployments(ACCOUNT)
        ]
    )


@authenticated
@authorized("deployments")
def get(ident: int) -> JSON:
    """List the given deployment."""

    return JSON(get_deployment(ident, ACCOUNT).to_json(address=True, customer=True))


@authenticated
@authorized("deployments")
def patch(ident: int) -> JSONMessage:
    """Modifies the respective deployment."""
    deployment=Deployment.select().where(Deployment.id==ident).get()
    if type_ := request.json.get("type"):
        try:
            deployment.type = DeploymentType(type_)
        except ValueError:
            return JSONMessage("Invalid type.", status=400)

    if connection := request.json.get("connection"):
        try:
            deployment.connection = Connection(connection)
        except ValueError:
            return JSONMessage("Invalid connection.", status=400)

    if address := request.json.get("address"):
        address = get_address(address)
        address.save()
        deployment.address = address

    if lpt_address := request.json.get("lptAddress"):
        lpt_address = get_address(lpt_address)
        lpt_address.save()
        deployment.lpt_address = lpt_address

    with suppress(KeyError):
        if (scheduled := request.json["scheduled"]) is not None:
            scheduled = datetime.fromisoformat(scheduled)

        deployment.scheduled = scheduled

    with suppress(KeyError):
        deployment.annotation = request.json["annotation"]

    with suppress(KeyError):
        deployment.testing = request.json["testing"]

    deployment.save()
    return JSONMessage("Deployment patched.", status=200)


ROUTES = [
    ("GET", "/", list_),
    ("GET", "/<int:ident>", get),
    ("PATCH", "/<int:ident>", patch),
]
