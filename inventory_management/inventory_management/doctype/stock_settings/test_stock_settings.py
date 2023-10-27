# Copyright (c) 2023, Tanmoy Sarkar and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestStockSettings(FrappeTestCase):
	pass


def update_valuation_method(method: str):
	frappe.db.set_value("Stock Settings", None, "valuation_method", method)
