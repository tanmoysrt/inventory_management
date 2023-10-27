# Copyright (c) 2023, Tanmoy Sarkar and Contributors
# See license.txt
import datetime
from datetime import timedelta

import frappe
from frappe.tests.utils import FrappeTestCase
from inventory_management.inventory_management.doctype.item.test_item import create_item
from inventory_management.inventory_management.doctype.warehouse.test_warehouse import create_warehouse
from inventory_management.inventory_management.doctype.stock_settings.test_stock_settings import update_valuation_method


def add_minutes(time: datetime.time, minutes: int) -> datetime.time:
	return (datetime.datetime.combine(datetime.date.today(), time) + timedelta(minutes=minutes)).time()

class TestStockEntry(FrappeTestCase):
	def setUp(self):
		update_valuation_method("FIFO")
		self.warehouse = create_warehouse("Test Warehouse")
		self.item = create_item("Test Item", self.warehouse.name, 5, 500)

	def test_validation(self):
		# Create a new stock entry
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.type = "Consume"
		stock_entry.date = frappe.utils.nowdate()
		stock_entry.time = frappe.utils.nowtime()
		# Create a new Stock Entry Transaction
		stock_entry_transaction = stock_entry.append("items")
		stock_entry_transaction.item = self.item.name
		stock_entry_transaction.qty = 500
		stock_entry_transaction.source_warehouse = self.warehouse.name
		stock_entry_transaction.target_warehouse = ""
		stock_entry_transaction.rate = 500

		# Check if validation failed for consuming more than available quantity
		self.assertRaises(frappe.exceptions.ValidationError, stock_entry.save, "Check if validation failed for consuming more than available quantity")
		stock_entry_transaction.qty = 2

		# Check if validation failed for setting a date in the future
		stock_entry.date = frappe.utils.add_days(frappe.utils.nowdate(), 1)
		self.assertRaises(frappe.exceptions.ValidationError, stock_entry.save, "Check  if validation failed for setting a date in the future")
		stock_entry.date = frappe.utils.nowdate()

		# Check if validation failed for setting a time in the future
		stock_entry.time = add_minutes(frappe.utils.get_time(frappe.utils.nowtime()), 5)
		self.assertRaises(frappe.exceptions.ValidationError, stock_entry.save, "Check if validation failed for setting a time in the future")

	def test_submit(self):
		pass

	def test_cancel(self):
		pass
