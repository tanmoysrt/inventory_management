# Copyright (c) 2023, Tanmoy Sarkar and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from frappe.query_builder import functions as fn
import frappe


class StockEntry(Document):

    def validate(self):
        # check if date and time is not in future

        if frappe.utils.getdate(self.date) > frappe.utils.getdate(frappe.utils.nowdate()):
            frappe.throw("Date cannot be in future")
        if frappe.utils.getdate(self.date) == frappe.utils.getdate(frappe.utils.nowdate()) and frappe.utils.get_time(
                self.time) > frappe.utils.get_time(frappe.utils.nowtime()):
            frappe.throw("Time cannot be in future")
        # check if there is any duplicate entry in items
        checked_items = set()  # <item_code>__<source_warehouse>__<target_warehouse>
        for item_transaction in self.items:
            key = item_transaction.item
            if item_transaction.source_warehouse:
                key += "__" + item_transaction.source_warehouse
            if item_transaction.target_warehouse:
                key += "__" + item_transaction.target_warehouse
            if key in checked_items:
                frappe.throw("Duplicate entry found for item {}".format(item_transaction.item))
            checked_items.add(key)

        # check if there is enough stock in source warehouse to transfer or consume
        if self.type == "Transfer" or self.type == "Consume":
            for item_transaction in self.items:
                item = item_transaction.item
                warehouse = item_transaction.source_warehouse
                qty = item_transaction.qty
                # Fetch total qty of item in warehouse
                doctype = frappe.qb.DocType("Stock Ledger Entry")
                total_qty = (frappe.qb.from_(doctype)
                             .select(fn.Sum(doctype.qty_change))
                             .where(doctype.item == item)
                             .where(doctype.warehouse == warehouse)
                             .groupby(doctype.item, doctype.warehouse)
                             .run(as_list=True))
                if len(total_qty) > 0 and len(total_qty[0]) > 0:
                    total_qty = total_qty[0][0]
                else:
                    total_qty = 0
                # If total qty is less than qty to be transferred or consumed, throw error
                if total_qty < qty:
                    frappe.throw("Not enough stock of item {} available in warehouse {}".format(item, warehouse))

    def before_save(self):
        # 	Make sure qty is not negative or zero and rate is not negative or zero
        for item_transaction in self.items:
            if item_transaction.rate <= 0:
                frappe.throw("Rate must be greater than zero, Remove the item or set the rate")
            if item_transaction.qty <= 0:
                frappe.throw("Quantity must be greater than zero, Remove the item or set the quantity")

    def on_submit(self):
        # Create stock ledger entries
        self.create_stock_ledger_entries()

    def create_stock_ledger_entries(self, is_cancel=False):
        valuation_method = frappe.get_doc("Stock Settings").valuation_method
        for item_transaction in self.items:
            if self.type == "Transfer":
                # Insert ledger entry for source warehouse
                doc = frappe.new_doc("Stock Ledger Entry")
                doc.item = item_transaction.item
                doc.warehouse = item_transaction.source_warehouse
                doc.qty_change = -item_transaction.qty
                doc.in_out_rate = item_transaction.rate
                doc.valuation_rate = self._calculate_valuation_of_item(item_transaction, True)
                doc.posting_date = self.date if not is_cancel else frappe.utils.nowdate()
                doc.posting_time = self.time if not is_cancel else frappe.utils.nowtime()
                doc.stock_entry = self.name
                doc.insert()
                #  Insert ledger entry for target warehouse
                doc = frappe.new_doc("Stock Ledger Entry")
                doc.item = item_transaction.item
                doc.warehouse = item_transaction.target_warehouse
                doc.qty_change = item_transaction.qty
                doc.in_out_rate = item_transaction.rate
                doc.valuation_rate = self._calculate_valuation_of_item(item_transaction)
                doc.posting_date = self.date if not is_cancel else frappe.utils.nowdate()
                doc.posting_time = self.time if not is_cancel else frappe.utils.nowtime()
                doc.stock_entry = self.name
                doc.insert()
            else:
                valuation = self._calculate_valuation_of_item(item_transaction, self.type == "Consume")
                doc = frappe.new_doc("Stock Ledger Entry")
                doc.item = item_transaction.item
                doc.warehouse = item_transaction.target_warehouse or item_transaction.source_warehouse
                doc.qty_change = -item_transaction.qty if self.type == "Consume" else item_transaction.qty
                doc.in_out_rate = item_transaction.rate
                doc.valuation_rate = valuation
                doc.posting_date = self.date if not is_cancel else frappe.utils.nowdate()
                doc.posting_time = self.time if not is_cancel else frappe.utils.nowtime()
                doc.stock_entry = self.name
                doc.insert()

    def on_cancel(self):
        for item_transaction in self.items:
            item_transaction.reverse_transaction()
        # reverse type of stock entry if it's consume or receive
        if self.type == "Consume":
            self.type = "Receive"
        elif self.type == "Receive":
            self.type = "Consume"
        # Create reverse stock ledger entries
        self.create_stock_ledger_entries(is_cancel=True)
        ### Roll back the changes
        # reverse type of stock entry if it's consume or receive
        if self.type == "Consume":
            self.type = "Receive"
        elif self.type == "Receive":
            self.type = "Consume"
        # reverse item transactions
        for item_transaction in self.items:
            item_transaction.reverse_transaction()

    # Private method
    # If received, make qty_change positive, else negative
    def _calculate_valuation_of_item(self, item_transaction, is_consumed=False):
        item = item_transaction.item
        if is_consumed:
            warehouse = item_transaction.source_warehouse
        else:
            warehouse = item_transaction.target_warehouse
        incoming_rate = item_transaction.rate
        incoming_qty = item_transaction.qty
        if is_consumed:
            incoming_qty = -incoming_qty

        return calculate_valuation(item, warehouse, incoming_qty, incoming_rate, is_consumed)


def calculate_valuation(item: str, warehouse: str, incoming_qty: int = 0, incoming_rate: int = 0, is_consumed: bool = False):
    valuation_rate = 0
    valuation_method = frappe.get_doc("Stock Settings").valuation_method
    doctype = frappe.qb.DocType("Stock Ledger Entry")
    if valuation_method == "FIFO":
        rate = (frappe.qb.from_(doctype)
                .select((fn.Sum(doctype.qty_change * doctype.in_out_rate) + incoming_rate * incoming_qty) / (
                fn.Sum(doctype.qty_change) + incoming_qty))
                .where(doctype.item == item)
                .where(doctype.warehouse == warehouse)
                .groupby(doctype.item, doctype.warehouse)
                .run(as_list=True))
        if len(rate) > 0 and len(rate[0]) > 0:
            valuation_rate = max(rate[0][0], 0)
    elif valuation_method == "Moving Average":
        rate = (frappe.qb.from_(doctype)
                .select(
            (fn.Sum(doctype.qty_change) * fn.Avg(doctype.in_out_rate) + incoming_qty * incoming_rate) / (
                    fn.Sum(doctype.qty_change) + incoming_qty))
                .where(doctype.item == item)
                .where(doctype.warehouse == warehouse)
                .groupby(doctype.item, doctype.warehouse)
                .run(as_list=True))
        if len(rate) > 0 and len(rate[0]) > 0:
            valuation_rate = rate[0][0]

    if valuation_rate == 0:
        valuation_rate = 0 if is_consumed else incoming_rate
    return valuation_rate
