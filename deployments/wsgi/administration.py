"""WSGI interface."""

from datetime import datetime

from flask import request

from his import ACCOUNT, authenticated, authorized
from hwdb import Connection, Deployment, DeploymentType
from mdb import Address
from wsgilib import JSONMessage

from deployments.functions import get_customer, get_deployment,new_deployment_mail


__all__ = ["ROUTES"]


@authenticated
@authorized("deployments")
def add() -> JSONMessage:
    """Add a new deployment."""

    address = Address.add(
        request.json["address"]["street"],
        request.json["address"]["houseNumber"],
        request.json["address"]["zipCode"],
        request.json["address"]["city"],
    )
    address.save()
    deployment = Deployment(
        customer=get_customer(request, ACCOUNT),
        type=DeploymentType.DDB,
        connection=Connection[request.json["connection"]],
        address=address,
        annotation=request.json.get("annotation"),
        timestamp=datetime.now(),
    )
    deployment.save()
    new_deployment_mail("mb@mieterinfo.tv",deployment)
    new_deployment_mail("s.dissmer@support.homeinfo.de", deployment)
    return JSONMessage("Deployment added.", id=deployment.id, status=201)


@authenticated
@authorized("deployments")
def delete(ident: int) -> JSONMessage:
    """Removes a deployment."""

    if (deployment := get_deployment(ident, ACCOUNT)).systems:
        return JSONMessage("Systems are already deployed here.", status=400)

    deployment.delete_instance()
    return JSONMessage("Order cancelled.", status=200)


ROUTES = [("POST", "/", add), ("DELETE", "/<int:ident>", delete)]
