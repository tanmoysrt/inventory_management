# Copyright (c) 2023, Tanmoy Sarkar and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from inventory_management.inventory_management.doctype.warehouse.test_warehouse import create_warehouse

def create_item(item_name, warehouse_name, qty, rate):
    item = frappe.new_doc("Item")
    item.name1 = item_name
    item.opening_warehouse = warehouse_name
    item.opening_qty = qty
    item.opening_valuation_rate = rate
    item.save()
    return item

class TestItem(FrappeTestCase):
    def setUp(self):
        # Create a warehouse
        self.warehouse = create_warehouse("Test Warehouse")

    def test_create_item(self):
        # Create a new item
        item = create_item("Test Item", self.warehouse.name, 10, 100)

        # Check if the item has been created
        self.assertTrue(frappe.db.exists("Item", item.name), "Check if the item has been created")

        # Check if the stock ledger entry has been created
        ledger_entry_id = frappe.db.get_value("Stock Ledger Entry",
                                              {"item": item.name, "warehouse": self.warehouse.name},
                                              order_by="posting_date desc, posting_time desc"
                                              )
        self.assertTrue(ledger_entry_id, "Check if the stock ledger entry has been created")

        ledger_entry = frappe.get_doc("Stock Ledger Entry", ledger_entry_id)

        # Check if it has a valid stock entry
        self.assertIsNotNone(ledger_entry.stock_entry, "Check if it has a valid stock entry")

        # Check if the stock ledger entry has been created
        self.assertEquals(ledger_entry.qty_change, item.opening_qty, "Check if the stock ledger entry has correct "
                                                                     "quantity")
        self.assertEquals(ledger_entry.in_out_rate, item.opening_valuation_rate, "Check if the stock Ledger Entry has "
                                                                                 "correct in/out rate")
        self.assertEquals(ledger_entry.valuation_rate, item.opening_valuation_rate, "Check if the stock Ledger Entry "
                                                                                    "has correct valuation rate")
