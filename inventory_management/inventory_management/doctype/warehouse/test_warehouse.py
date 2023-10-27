# Copyright (c) 2023, Tanmoy Sarkar and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from inventory_management.inventory_management.doctype.warehouse.warehouse import Warehouse


class TestWarehouse(FrappeTestCase):
    pass


def create_warehouse(warehouse_name: str) -> Warehouse:
    warehouse = frappe.new_doc("Warehouse")
    warehouse.name1 = warehouse_name
    warehouse.save()
    return warehouse
