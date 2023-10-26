# Copyright (c) 2023, Tanmoy Sarkar and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class StockEntryTransaction(Document):

	# This function will create a deep copy and reverse the transaction
	def reverse_transaction(self):
		# swap source and target warehouse
		self.source_warehouse, self.target_warehouse = self.target_warehouse, self.source_warehouse