from frappe.tests.utils import FrappeTestCase
from inventory_management.inventory_management.doctype.item.test_item import create_item
from inventory_management.inventory_management.doctype.stock_entry.test_stock_entry import new_stock_entry
from inventory_management.inventory_management.doctype.stock_settings.test_stock_settings import update_valuation_method
from inventory_management.inventory_management.doctype.warehouse.test_warehouse import create_warehouse

from inventory_management.inventory_management.report.stock_ledger.stock_ledger import execute as stock_ledger_execute


class TestStockLedgerReport(FrappeTestCase):
	def test_report(self):
		# switch to FIFO
		update_valuation_method("FIFO")

		# create ann item and warehouse
		warehouse = create_warehouse("Test Warehouse")
		item = create_item("Test Item", warehouse.name, 5, 500)

		# create a stock entry
		new_stock_entry("Consume", item.name, 2, warehouse.name, "", 500).save().submit()
		new_stock_entry("Receive", item.name, 2, "", warehouse.name, 1000).save().submit()
		# query report
		report = stock_ledger_execute(filters={
			"item": item.name,
			"warehouse": warehouse.name
		})
		# check report values
		report = report[1]
		# Run checks
		self.assertEqual(len(report), 3)
		# Check first ledger entry -- while adding stock
		first_entry = report[0]
		self.assertEqual(first_entry.qty_change, 5)
		self.assertEqual(int(first_entry.balance_qty), 5)
		self.assertEqual(int(first_entry.in_out_rate), 500)
		self.assertEqual(int(first_entry.valuation_rate), 500)
		self.assertEqual(int(first_entry.value_change), 2500)
		self.assertEqual(int(first_entry.updated_balance_value), 2500)
		# Check second ledger entry -- while consuming stock
		second_entry = report[1]
		self.assertEqual(second_entry.qty_change, -2)
		self.assertEqual(int(second_entry.balance_qty), 3)
		self.assertEqual(int(second_entry.in_out_rate), 500)
		self.assertEqual(int(second_entry.valuation_rate), 500)
		self.assertEqual(int(second_entry.value_change), -1000)
		self.assertEqual(int(second_entry.updated_balance_value), 1500)
		# Check third ledger entry -- while receiving stock
		third_entry = report[2]
		self.assertEqual(third_entry.qty_change, 2)
		self.assertEqual(int(third_entry.balance_qty), 5)
		self.assertEqual(int(third_entry.in_out_rate), 1000)
		self.assertEqual(int(third_entry.valuation_rate), 700)
		self.assertEqual(int(third_entry.value_change), 1400)
		self.assertEqual(int(third_entry.updated_balance_value), 2900)
