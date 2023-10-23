# Copyright (c) 2023, Tanmoy Sarkar and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe


class StockEntry(Document):

	def validate(self):
		# check if there is any duplicate entry in items
		checked_items = set() # <item_code>__<source_warehouse>__<target_warehouse>
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
				total_qty = frappe.db.sql("""SELECT SUM(sle.qty_change) as qty
												FROM `tabStock Ledger Entry` as sle
												WHERE sle.item = %s AND sle.warehouse = %s
												GROUP BY sle.item, sle.warehouse""", (item, warehouse), as_list=True)
				if len(total_qty) > 0 and len(total_qty[0]) > 0:
					total_qty = total_qty[0][0]
				else:
					total_qty = 0
				# If total qty is less than qty to be transferred or consumed, throw error
				if total_qty < qty:
					frappe.throw("Not enough stock of item {} available in warehouse {}".format(item, warehouse))
		frappe.throw("Stock Entry is not allowed to be modified")

	def before_save(self):
		# 	Make sure qty is not negative or zero and rate is not negative or zero
		for item_transaction in self.items:
			if item_transaction.rate <= 0:
				frappe.throw("Rate must be greater than zero, Remove the item or set the rate")
			if item_transaction.qty <= 0:
				frappe.throw("Quantity must be greater than zero, Remove the item or set the quantity")

	def on_submit(self):
		for item_transaction in self.items:
			if self.type == "Transfer":
				# Insert ledger entry for source warehouse
				doc = frappe.new_doc("Stock Ledger Entry")
				doc.item = item_transaction.item
				doc.warehouse = item_transaction.source_warehouse
				doc.qty_change = -item_transaction.qty
				doc.in_out_rate = item_transaction.rate
				doc.valuation_rate = self._calculate_valuation_of_item(item_transaction, self.valuation_method, True)
				doc.posting_date = self.date
				doc.posting_time = self.time
				doc.stock_entry = self.name
				doc.insert()
				#  Insert ledger entry for target warehouse
				doc = frappe.new_doc("Stock Ledger Entry")
				doc.item = item_transaction.item
				doc.warehouse = item_transaction.target_warehouse
				doc.qty_change = item_transaction.qty
				doc.in_out_rate = item_transaction.rate
				doc.valuation_rate = self._calculate_valuation_of_item(item_transaction, self.valuation_method)
				doc.posting_date = self.date
				doc.posting_time = self.time
				doc.stock_entry = self.name
				doc.insert()
			else:
				valuation = self._calculate_valuation_of_item(item_transaction, self.valuation_method, self.type == "Consume")
				doc = frappe.new_doc("Stock Ledger Entry")
				doc.item = item_transaction.item
				doc.warehouse = item_transaction.target_warehouse or item_transaction.source_warehouse
				doc.qty_change = -item_transaction.qty if self.type == "Consume" else item_transaction.qty
				doc.in_out_rate = item_transaction.rate
				doc.valuation_rate = valuation
				doc.posting_date = self.date
				doc.posting_time = self.time
				doc.stock_entry = self.name
				doc.insert()

	def on_cancel(self):
		# 	Delete all stock ledger entries for this stock entry
		frappe.db.delete("Stock Ledger Entry", {"stock_entry": self.name})

	# Private method
	# If received, make qty_change positive, else negative
	def _calculate_valuation_of_item(self, item_transaction, valuation_method, is_consumed=False):
		print("Stock Entry _calculate_valuation_of_item")
		item = item_transaction.item
		if is_consumed:
			warehouse = item_transaction.source_warehouse
		else:
			warehouse = item_transaction.target_warehouse
		incoming_rate = item_transaction.rate
		incoming_qty = item_transaction.qty
		if is_consumed:
			incoming_qty = -incoming_qty

		valuation_rate = 0
		if valuation_method == "FIFO":
			rate = frappe.db.sql("""SELECT ((SUM(sle.qty_change*sle.in_out_rate)+%s)/(SUM(sle.qty_change)+%s)) as rate
										FROM `tabStock Ledger Entry` as sle
										WHERE sle.item = %s AND sle.warehouse = %s
										GROUP BY sle.item, sle.warehouse""", (incoming_rate*incoming_qty, incoming_qty, item, warehouse), as_list=True)
			if len(rate) > 0 and len(rate[0]) > 0:
				valuation_rate = max(rate[0][0], 0)
		elif valuation_method == "Moving Average":
			rate = frappe.db.sql("""SELECT ((SUM(sle.qty_change)+AVG(sle.in_out_rate))*(%s+%s)/(SUM(sle.qty_change)+%s)) as rate
		                            FROM `tabStock Ledger Entry` as sle
		                            WHERE sle.item = %s AND sle.warehouse = %s
		                            GROUP BY sle.item, sle.warehouse""", (incoming_qty, incoming_rate, incoming_qty, item, warehouse), as_list=True)
			if len(rate) > 0 and len(rate[0]) > 0:
				valuation_rate = rate[0][0]

		if valuation_rate == 0:
			valuation_rate = 0 if is_consumed else incoming_rate
		return valuation_rate