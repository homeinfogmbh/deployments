"""Object-relational mappings."""

from __future__ import annotations

from peewee import ForeignKeyField, Select

from his import Account
from mdb import Company, Customer
from peeweeplus import JSONModel, MySQLDatabaseProxy


__all__ = ['Admin', 'CustomerAdmin']


DATABASE = MySQLDatabaseProxy('deployments')


class DeploymentModel(JSONModel):
    """Abstract base model."""

    class Meta:
        database = DATABASE
        schema = database.database


class Admin(DeploymentModel):
    """Accounts that are allowed to process orders."""

    account = ForeignKeyField(
        Account, column_name='account', on_delete='CASCADE'
    )

    @classmethod
    def select(cls, *args, cascade: bool = False) -> Select:
        """Select records."""
        if not cascade:
            return super().select(*args)

        args = {cls, *args, Account, Customer, Company}
        return super().select(*args).join(Account).join(Customer).join(Company)


class CustomerAdmin(DeploymentModel):
    """Mappings of accounts and customers which can be administered."""

    class Meta:
        table_name = 'customer_admin'

    account = ForeignKeyField(
        Account, column_name='account', on_delete='CASCADE'
    )
    customer = ForeignKeyField(
        Customer, column_name='customer', on_delete='CASCADE'
    )
