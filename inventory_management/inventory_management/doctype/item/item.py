# Copyright (c) 2023, Tanmoy Sarkar and contributors
# For license information, please see license.txt
from datetime import datetime

import frappe
# import frappe
from frappe.model.document import Document

class Item(Document):
	def before_save(self):
		self.code = self.name

	def after_insert(self):
		# Create stock entry with type "Receive" with rate = opening valuation rate and qty = opening qty for opening stock
		doc = frappe.new_doc("Stock Entry")
		doc.date = datetime.now().date()
		doc.time = datetime.now().time()
		doc.type = "Receive"
		doc.valuation_method = "Moving Average"
		doc.append("items", {
			"item": self.name,
			"qty": self.opening_qty,
			"rate": self.opening_valuation_rate,
			"target_warehouse": self.opening_warehouse
		})
		doc.insert()
		doc.submit()
