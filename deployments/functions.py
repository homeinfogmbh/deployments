"""Common functions."""

from his import Account
from hwdb import Deployment, DeploymentTemp
from mdb import Address, Customer
from wsgilib import JSONMessage
from emaillib import EMailsNotSent, Mailer, EMail
from configlib import load_config

from flask import Request
from peewee import Select
import urllib.parse
import secrets
from base64 import urlsafe_b64encode as b64e, urlsafe_b64decode as b64d
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from deployments.authorization import can_administer
from deployments.authorization import get_administered_customers
from deployments.authorization import is_admin


__all__ = [
    "can_be_modified",
    "get_address",
    "get_customer",
    "get_customers",
    "get_deployment",
    "get_deployments",
    "new_deployment_mail",
    "password_decrypt"
]

backend = default_backend()
iterations = 100_000

def new_deployment_mail(email, deployment: DeploymentTemp):
    sender = "service@dasdigitalebrett.de"
    password = load_config("sysmon.conf").get("mailing","encryptionpassword")
    message = str(deployment.id)
    encrypted_id = password_encrypt(message.encode(), password)
    mailbody = "Guten Tag,<br><br>Folgender Standort wurde angelegt und wartet auf Freischaltung:<br>"
    mailbody = mailbody+"Kunde: <b>"+str(deployment.customer.company)+"</b><br>"
    mailbody = mailbody+"Adresse: <b>"+str(deployment.address)+"</b><br>"
    mailbody = mailbody+"Freischalten: <a href='https://backend.homeinfo.de/deployments/"+urllib.parse.quote_plus(encrypted_id)+"'>Ja</a><br>"
    mail= EMail(subject="Homeinfo: Neuer Standort angelegt",sender=sender,recipient=email,html=mailbody)
    Mailer.from_config(load_config("sysmon.conf")).send([mail])


def can_be_modified(deployment: Deployment, account: Account) -> bool:
    """Checks whether the deployment may be modified."""

    if account.root:
        return True

    if systems := [system.id for system in deployment.systems]:
        raise JSONMessage(
            "Systems have already been deployed here.", systems=systems, status=403
        )

    return True


def get_address(address: dict) -> Address:
    """Returns the respective address."""

    return Address.add(
        address["street"], address["houseNumber"], address["zipCode"], address["city"]
    )


def get_customer(request: Request, account: Account) -> Customer:
    """Returns the target customer."""

    if (customer := request.json.pop("customer", None)) is None:
        return account.customer

    try:
        customer = Customer.select(cascade=True).where(Customer.id == customer).get()
    except Customer.DoesNotExist:
        raise JSONMessage("No such customer.", status=404)

    if can_administer(account, customer):
        return customer

    raise JSONMessage("Cannot administer the given customer.", status=403)


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
def _derive_key(password: bytes, salt: bytes, iterations: int = iterations) -> bytes:
    """Derive a secret key from a given password and salt"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt,
        iterations=iterations, backend=backend)
    return b64e(kdf.derive(password))

def password_encrypt(message: bytes, password: str, iterations: int = iterations) -> bytes:
    salt = secrets.token_bytes(16)
    key = _derive_key(password.encode(), salt, iterations)
    return b64e(
        b'%b%b%b' % (
            salt,
            iterations.to_bytes(4, 'big'),
            b64d(Fernet(key).encrypt(message)),
        )
    )

def password_decrypt(token: bytes, password: str) -> bytes:
    decoded = b64d(token)
    salt, iter, token = decoded[:16], decoded[16:20], b64e(decoded[20:])
    iterations = int.from_bytes(iter, 'big')
    key = _derive_key(password.encode(), salt, iterations)
    return Fernet(key).decrypt(token)
