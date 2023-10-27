# Copyright (c) 2023, Tanmoy Sarkar and Contributors
# See license.txt
import datetime
import math
from datetime import timedelta

import frappe
from frappe.tests.utils import FrappeTestCase
from inventory_management.inventory_management.doctype.item.test_item import create_item
from inventory_management.inventory_management.doctype.warehouse.test_warehouse import create_warehouse
from inventory_management.inventory_management.doctype.stock_settings.test_stock_settings import update_valuation_method
from inventory_management.inventory_management.doctype.stock_entry.stock_entry import calculate_valuation


def add_minutes(time: datetime.time, minutes: int) -> datetime.time:
	return (datetime.datetime.combine(datetime.date.today(), time) + timedelta(minutes=minutes)).time()


def new_stock_entry(type: str, item: str, qty: int, source_warehouse: str, target_warehouse: str,
					rate: int):
	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.type = type
	stock_entry.date = frappe.utils.nowdate()
	stock_entry.time = frappe.utils.nowtime()
	stock_entry_transaction = stock_entry.append("items")
	stock_entry_transaction.item = item
	stock_entry_transaction.qty = qty
	stock_entry_transaction.source_warehouse = source_warehouse
	stock_entry_transaction.target_warehouse = target_warehouse
	stock_entry_transaction.rate = rate
	stock_entry.save()
	return stock_entry


class TestStockEntry(FrappeTestCase):
	def setUp(self):
		update_valuation_method("FIFO")
		self.warehouse = create_warehouse("Test Warehouse")
		self.warehouse2 = create_warehouse("Test Warehouse 2")
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
		self.assertRaises(frappe.exceptions.ValidationError, stock_entry.save,
						  "Check if validation failed for consuming more than available quantity")
		stock_entry_transaction.qty = 2

		# Check if validation failed for setting a date in the future
		stock_entry.date = frappe.utils.add_days(frappe.utils.nowdate(), 1)
		self.assertRaises(frappe.exceptions.ValidationError, stock_entry.save,
						  "Check  if validation failed for setting a date in the future")
		stock_entry.date = frappe.utils.nowdate()

		# Check if validation failed for setting a time in the future
		stock_entry.time = add_minutes(frappe.utils.get_time(frappe.utils.nowtime()), 5)
		self.assertRaises(frappe.exceptions.ValidationError, stock_entry.save,
						  "Check if validation failed for setting a time in the future")

	def test_submit_for_consuming_items(self):
		# Create a new stock entry
		stock_entry = new_stock_entry("Consume", self.item.name, 2, self.warehouse.name, "", 500)
		stock_entry.submit()

		# Check if the stock entry has been submitted
		self.assertEquals(stock_entry.docstatus, 1, "Check if the stock entry has been submitted")

		# Check if the stock ledger entry has been created
		ledger_entry_id = frappe.db.get_value("Stock Ledger Entry", {"stock_entry": stock_entry.name})
		ledger_entry = frappe.get_doc("Stock Ledger Entry", ledger_entry_id)
		self.assertTrue(ledger_entry, "Check if the stock ledger entry has been created")

		# Check if the stock ledger entry has correct quantity
		self.assertEquals(ledger_entry.qty_change, -stock_entry.items[0].qty, "Check if the stock ledger entry has ")

		# Check if the stock ledger entry has correct in/out rate
		self.assertEquals(ledger_entry.in_out_rate, stock_entry.items[0].rate, "Check if the stock ledger entry has ")

		# Check if the stock ledger entry has correct valuation rate
		valuation = calculate_valuation(self.item.name, self.warehouse.name)
		self.assertEquals(ledger_entry.valuation_rate, valuation, "Check if the stock ledger entry has ")

	def test_submit_for_receiving_items(self):
		# Create a new stock entry
		stock_entry = new_stock_entry("Receive", self.item.name, 2, "", self.warehouse.name, 500)
		stock_entry.submit()

		# Check if the stock entry has been submitted
		self.assertEquals(stock_entry.docstatus, 1, "Check if the stock entry has been submitted")

		# Check if the stock ledger entry has been created
		ledger_entry_id = frappe.db.get_value("Stock Ledger Entry", {"stock_entry": stock_entry.name})
		ledger_entry = frappe.get_doc("Stock Ledger Entry", ledger_entry_id)
		self.assertTrue(ledger_entry, "Check if the stock ledger entry has been created")

		# Check if the stock ledger entry has correct quantity
		self.assertEquals(ledger_entry.qty_change, stock_entry.items[0].qty, "Check if the stock ledger entry has ")

		# Check if the stock ledger entry has correct in/out rate
		self.assertEquals(ledger_entry.in_out_rate, stock_entry.items[0].rate, "Check if the stock ledger entry has ")

		# Check if the stock ledger entry has correct valuation rate
		valuation = calculate_valuation(self.item.name, self.warehouse.name)
		self.assertEquals(ledger_entry.valuation_rate, valuation, "Check if the stock ledger entry has ")

	def test_submit_for_transferring_items(self):
		# Create a new stock entry
		stock_entry = new_stock_entry("Transfer", self.item.name, 2, self.warehouse.name, self.warehouse2.name, 500)
		stock_entry.submit()

		# Check if the stock entry has been submitted
		self.assertEquals(stock_entry.docstatus, 1, "Check if the stock entry has been submitted")

		### Check if the stock ledger entry has been created for source warehouse
		ledger_entry_id = frappe.db.get_value("Stock Ledger Entry",
											  {"stock_entry": stock_entry.name, "warehouse": self.warehouse.name})
		ledger_entry = frappe.get_doc("Stock Ledger Entry", ledger_entry_id)
		self.assertTrue(ledger_entry, "Check if the stock ledger entry has been created")

		# Check if the stock ledger entry has correct quantity
		self.assertEquals(ledger_entry.qty_change, -stock_entry.items[0].qty, "Check if the stock ledger entry has ")

		# Check if the stock ledger entry has correct in/out rate
		self.assertEquals(ledger_entry.in_out_rate, stock_entry.items[0].rate, "Check if the stock ledger entry has ")

		# Check if the stock ledger entry has correct valuation rate
		valuation = calculate_valuation(self.item.name, self.warehouse.name)
		self.assertEquals(ledger_entry.valuation_rate, valuation, "Check if the stock ledger entry has ")

		### Check if the stock ledger entry has been created for target warehouse
		ledger_entry_id = frappe.db.get_value("Stock Ledger Entry",
											  {"stock_entry": stock_entry.name, "warehouse": self.warehouse2.name})
		ledger_entry = frappe.get_doc("Stock Ledger Entry", ledger_entry_id)
		self.assertTrue(ledger_entry, "Check if the stock ledger entry has been created")

		# Check if the stock ledger entry has correct quantity
		self.assertEquals(ledger_entry.qty_change, stock_entry.items[0].qty, "Check if the stock ledger entry has ")

		# Check if the stock ledger entry has correct in/out rate
		self.assertEquals(ledger_entry.in_out_rate, stock_entry.items[0].rate, "Check if the stock ledger entry has ")

		# Check if the stock ledger entry has correct valuation rate
		valuation = calculate_valuation(self.item.name, self.warehouse2.name)
		self.assertEquals(ledger_entry.valuation_rate, valuation, "Check if the stock ledger entry has ")

	def test_cancel_for_consuming_items(self):
		# Create a new stock entry
		stock_entry = new_stock_entry("Consume", self.item.name, 2, self.warehouse.name, "", 500)
		stock_entry.submit()

		# Fetch the latest stock ledger entry
		ledger_entry_on_submit_id = frappe.db.get_value("Stock Ledger Entry", {"stock_entry": stock_entry.name},
														order_by="posting_date desc, posting_time desc")

		# cancel the stock entry
		stock_entry.cancel()

		# Check if the stock entry has been cancelled
		self.assertEquals(stock_entry.docstatus, 2, "Check if the stock entry has been cancelled")

		# Fetch latest stock ledger entry
		ledger_entry_on_cancel_id = frappe.db.get_value("Stock Ledger Entry", {"stock_entry": stock_entry.name},
														order_by="posting_date desc, posting_time desc")

		# Check if the stock ledger entry has been reversed
		self._check_ledger_entry_reversal(ledger_entry_on_submit_id, ledger_entry_on_cancel_id)

	def test_cancel_for_receiving_items(self):
		# Create a new stock entry
		stock_entry = new_stock_entry("Receive", self.item.name, 2, "", self.warehouse.name, 500)
		stock_entry.submit()

		# Fetch the latest stock ledger entry
		ledger_entry_on_submit_id = frappe.db.get_value("Stock Ledger Entry", {"stock_entry": stock_entry.name},
														order_by="posting_date desc, posting_time desc")

		# cancel the stock entry
		stock_entry.cancel()

		# Check if the stock entry has been cancelled
		self.assertEquals(stock_entry.docstatus, 2, "Check if the stock entry has been cancelled")

		# Fetch latest stock ledger entry
		ledger_entry_on_cancel_id = frappe.db.get_value("Stock Ledger Entry", {"stock_entry": stock_entry.name},
														order_by="posting_date desc, posting_time desc")

		# Check if the stock ledger entry has been reversed
		self._check_ledger_entry_reversal(ledger_entry_on_submit_id, ledger_entry_on_cancel_id)

	def test_cancel_for_transferring_items(self):
		# Create a new stock entry
		stock_entry = new_stock_entry("Transfer", self.item.name, 2, self.warehouse.name, self.warehouse2.name, 500)
		stock_entry.submit()

		# Fetch the latest stock ledger entries
		ledger_entry_on_submit_type_receive_id = frappe.db.get_value("Stock Ledger Entry",
																	 {"stock_entry": stock_entry.name,
																	  "qty_change": ['>=', 0]},
																	 order_by="posting_date desc, posting_time desc")

		ledger_entry_on_submit_type_consume_id = frappe.db.get_value("Stock Ledger Entry",
																	 {"stock_entry": stock_entry.name,
																	  "qty_change": ['<', 0]},
																	 order_by="posting_date desc, posting_time desc")

		# cancel the stock entry
		stock_entry.cancel()

		# Check if the stock entry has been cancelled
		self.assertEquals(stock_entry.docstatus, 2, "Check if the stock entry has been cancelled")

		# Fetch latest stock ledger entries
		ledger_entry_on_cancel_type_receive_id = frappe.db.get_value("Stock Ledger Entry",
																	 {"stock_entry": stock_entry.name,
																	  "qty_change": ['>=', 0]},
																	 order_by="posting_date desc, posting_time desc")

		ledger_entry_on_cancel_type_consume_id = frappe.db.get_value("Stock Ledger Entry",
																	 {"stock_entry": stock_entry.name,
																	  "qty_change": ['<', 0]},
																	 order_by="posting_date desc, posting_time desc")

		# Check if the stock ledger entry has been reversed
		self._check_ledger_entry_reversal(ledger_entry_on_submit_type_receive_id, ledger_entry_on_cancel_type_consume_id)
		self._check_ledger_entry_reversal(ledger_entry_on_submit_type_consume_id, ledger_entry_on_cancel_type_receive_id)

	def test_valuation_method_fifo(self):
		# switch to FIFO
		update_valuation_method("FIFO")
		# create a item
		item = create_item("Test Item", self.warehouse.name, 5, 500)
		# create a stock entry
		new_stock_entry("Consume", item.name, 2, self.warehouse.name, "", 500).save().submit()
		new_stock_entry("Receive", item.name, 2, "", self.warehouse.name, 1000).save().submit()

		# Get valuation rate
		valuation = calculate_valuation(item.name, self.warehouse.name)
		self.assertEquals(valuation, 700, "Check if valuation rate is correct")

	def test_valuation_method_moving_average(self):
		# switch to `Moving Average`
		update_valuation_method("Moving Average")
		# create a item
		item = create_item("Test Item", self.warehouse.name, 5, 500)
		# create a stock entry
		new_stock_entry("Consume", item.name, 2, self.warehouse.name, "", 500).save().submit()
		new_stock_entry("Receive", item.name, 2, "", self.warehouse.name, 1000).save().submit()

		# Get valuation rate
		valuation = calculate_valuation(item.name, self.warehouse.name)
		self.assertEquals(math.ceil(valuation), 667, "Check if valuation rate is correct")

	def _check_ledger_entry_reversal(self, ledger_entry_on_submit_id: str, ledger_entry_on_cancel_id: str):
		ledger_entry_on_submit = frappe.get_doc("Stock Ledger Entry", ledger_entry_on_submit_id)
		ledger_entry_on_cancel = frappe.get_doc("Stock Ledger Entry", ledger_entry_on_cancel_id)

		# Check if the stock ledger entry has been reversed
		self.assertEquals(ledger_entry_on_submit.qty_change, -ledger_entry_on_cancel.qty_change,
						  "Check if quantity has been reversed")
		self.assertEquals(ledger_entry_on_submit.in_out_rate, ledger_entry_on_cancel.in_out_rate,
						  "Check if in/out rate is same")
		self.assertEquals(ledger_entry_on_submit.warehouse, ledger_entry_on_cancel.warehouse,
						  "Check if warehouse is same")
