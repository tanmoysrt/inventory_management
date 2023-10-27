from frappe.tests.utils import FrappeTestCase
from inventory_management.inventory_management.doctype.item.test_item import create_item
from inventory_management.inventory_management.doctype.stock_entry.test_stock_entry import new_stock_entry
from inventory_management.inventory_management.doctype.stock_settings.test_stock_settings import update_valuation_method
from inventory_management.inventory_management.doctype.warehouse.test_warehouse import create_warehouse

from inventory_management.inventory_management.report.stock_balance.stock_balance import \
	execute as stock_balance_execute


class TestStockBalanceReport(FrappeTestCase):
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
		report = stock_balance_execute(filters={
			"item": item.name,
			"warehouse": warehouse.name
		})
		# check report values
		report = report[1]
		# Run checks
		self.assertEqual(len(report), 1)
		self.assertEqual(report[0].in_qty, 7)
		self.assertEqual(int(report[0].in_value), 4500)  # 500 * 5 + 1000 * 2
		self.assertEqual(-1*report[0].out_qty, 2)
		self.assertEqual(-1*int(report[0].out_value), 1000)  # 500 * 2
		self.assertEqual(report[0].balance_qty, 5)  # 5 -2 + 2
		self.assertEqual(report[0].balance_value, 3500)  # 500 * 5 + 1000 * 2 - 500 * 2
		self.assertEqual(report[0].latest_valuation_rate, 700)  # FIFO > (500 * 5 + 1000 * 2) / 5
