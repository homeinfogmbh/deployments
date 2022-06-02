"""Checklist management."""

from datetime import datetime

from flask import request

from his import ACCOUNT, authenticated, authorized
from wsgilib import JSONMessage

from deployments.decorators import ddb_admin
from deployments.functions import get_deployment


__all__ = ['ROUTES']


@authenticated
@authorized('deployments')
@ddb_admin
def update_technician_annotation(ident: int) -> JSONMessage:
    """Update the annotation of a deployment."""

    deployment = get_deployment(ident, ACCOUNT)
    deployment.technician_annotation = request.json
    deployment.save()
    return JSONMessage('Technician annotation updated.', 200)


@authenticated
@authorized('deployments')
@ddb_admin
def set_construction_site_preparation(ident: int) -> JSONMessage:
    """Set the construction site preparation feedback flag."""

    deployment = get_deployment(ident, ACCOUNT)

    if request.json:
        deployment.construction_site_preparation_feedback = datetime.now()
    else:
        deployment.construction_site_preparation_feedback = None

    deployment.save()
    return JSONMessage(
        'Construction site preparation feedback updated.', status=200
    )


@authenticated
@authorized('deployments')
@ddb_admin
def set_internet_connection(ident: int) -> JSONMessage:
    """Set the internet connection flag."""

    deployment = get_deployment(ident, ACCOUNT)

    if request.json:
        deployment.internet_connection = datetime.now()
    else:
        deployment.internet_connection = None

    deployment.save()
    return JSONMessage('Internet connection set.', status=200)


@authenticated
@authorized('deployments')
@ddb_admin
def set_hardware_installation(ident: int) -> JSONMessage:
    """Set the hardware installation flag."""

    deployment = get_deployment(ident, ACCOUNT)

    if request.json:
        deployment.hardware_installation = datetime.now()
    else:
        deployment.hardware_installation = None

    deployment.save()
    return JSONMessage('Hardware installation set.', status=200)


ROUTES = [
    ('PATCH', '/<int:ident>/annotation', update_technician_annotation),
    (
        'POST',
        '/<int:ident>/construction-site-preparation',
        set_construction_site_preparation
    ),
    ('POST', '/<int:ident>/internet-connection', set_internet_connection),
    ('POST', '/<int:ident>/hardware-installation', set_hardware_installation)
]
