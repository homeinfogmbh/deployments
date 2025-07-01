"""WSGI interface."""

from datetime import datetime

from flask import request
import urllib.parse


from configlib import load_config
from his import ACCOUNT, authenticated, authorized
from hwdb import Connection, Deployment, DeploymentType,DeploymentTemp
from mdb import Address
from wsgilib import JSONMessage

from deployments.functions import get_customer, get_deployment,new_deployment_mail,password_decrypt

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
    deployment = DeploymentTemp(
        customer=get_customer(request, ACCOUNT),
        type=DeploymentType.DDB,
        connection=Connection[request.json["connection"]],
        address=address,
        annotation=request.json.get("annotation"),
        timestamp=datetime.now(),
    )
    deployment.save()
    #new_deployment_mail("mb@mieterinfo.tv",deployment)
    new_deployment_mail("reallyme@gmx.net", deployment)
    #new_deployment_mail("s.dissmer@support.homeinfo.de", deployment)
    return JSONMessage("Deployment added.", id=deployment.id, status=201)


@authenticated
@authorized("deployments")
def delete(ident: int) -> JSONMessage:
    """Removes a deployment."""

    if (deployment := get_deployment(ident, ACCOUNT)).systems:
        return JSONMessage("Systems are already deployed here.", status=400)

    deployment.delete_instance()
    return JSONMessage("Order cancelled.", status=200)


def confirm(id : str) -> JSONMessage:
    """Confirms a deployment"""
    password = load_config("sysmon.conf").get("mailing", "encryptionpassword")
    id = password_decrypt(urllib.parse.unquote_plus(id),password).decode()
    dep = DeploymentTemp.select(cascade=True).where(DeploymentTemp.id == id).get()
    deployment = Deployment(
        customer=dep.customer,
        type=dep.type,
        connection=dep.connection,
        address=dep.address,
        annotation=dep.annotation,
        timestamp=datetime.now(),
    )
    deployment.save()
    dep.delete_instance()
    return JSONMessage("Deployment confirmed.", id=deployment.id, status=201)

ROUTES = [("POST", "/", add), ("DELETE", "/<int:ident>", delete), ("GET", "/confirm/<string:id>", confirm)]
