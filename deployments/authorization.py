"""Authorization checks."""

from typing import Iterator, Union

from mdb import Company, Customer
from his import Account

from deployments.orm import Admin, CustomerAdmin


__all__ = ['is_admin', 'can_administer', 'get_administered_customers']


def is_admin(account: Account) -> Union[Admin, bool]:
    """Returns a condition that matches management accounts."""

    try:
        return Admin.select().where(Admin.account == account.id).get()
    except Admin.DoesNotExist:
        return False


def can_administer(
        account: Account,
        customer: Customer
) -> Union[CustomerAdmin, bool]:
    """Determines whether the account can administer the given customer."""

    if account.root:
        return True

    if not is_admin(account):
        return False

    try:
        return CustomerAdmin.select().where(
            (CustomerAdmin.account == account.id)
            & (CustomerAdmin.customer == customer.id)
        ).get()
    except CustomerAdmin.DoesNotExist:
        return False


def get_administered_customers(account: Account) -> Iterator[Customer]:
    """Selects customers which the account can administer."""

    if account.admin:
        yield account.customer

    for customer_admin in CustomerAdmin.select().join(Customer).join(
            Company).where(CustomerAdmin.account == account.id):
        yield customer_admin.customer
