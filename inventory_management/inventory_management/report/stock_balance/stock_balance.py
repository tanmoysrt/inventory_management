# Copyright (c) 2023, Tanmoy Sarkar and contributors
# For license information, please see license.txt
import frappe
from frappe import _

# import frappe


stock_balance_report_columns = [
    {
        'fieldname': 'item',
        'label': _('Item'),
        'fieldtype': 'Link',
        'options': 'Item'
    },
    {
        'fieldname': 'warehouse',
        'label': _('Warehouse'),
        'fieldtype': 'Link',
        'options': 'Warehouse'
    },
    {
        'fieldname': 'balance_qty',
        'label': _('Balance Quantity'),
        'fieldtype': 'Int',
        'options': ''
    },
    {
        'fieldname': 'balance_value',
        'label': _('Balance Value'),
        'fieldtype': 'Float',
        'options': ''
    },
    {
        'fieldname': 'in_qty',
        'label': _('In Quantity'),
        'fieldtype': 'Int',
        'options': ''
    },
    {
        'fieldname': 'in_value',
        'label': _('In Value'),
        'fieldtype': 'Float',
        'options': ''
    },
    {
        'fieldname': 'out_qty',
        'label': _('Out Quantity'),
        'fieldtype': 'Int',
        'options': ''
    },
    {
        'fieldname': 'out_value',
        'label': _('Out Value'),
        'fieldtype': 'Float',
        'options': ''
    },
    {
        'fieldname': 'latest_valuation_rate',
        'label': _('Valuation Rate'),
        'fieldtype': 'Float',
        'options': ''
    },
]


def clean_filter_query(query):
    query = query.strip()
    if query.endswith("AND"):
        query = query[:-3]
    if query == "WHERE":
        query = ""
    return query


def execute(filters=None):
    if not filters:
        filters = {}
    mainQueryFilter = "WHERE "
    subQueryFilter = "AND "
    if "item" in filters:
        mainQueryFilter += f"item = '{filters['item']}' AND "
    if "warehouse" in filters:
        mainQueryFilter += f"warehouse = '{filters['warehouse']}' AND "
    if "from_date" in filters:
        mainQueryFilter += f"posting_date >= '{filters['from_date']}' AND "
        subQueryFilter += f"posting_date >= '{filters['from_date']}' AND "
    if "to_date" in filters:
        mainQueryFilter += f"posting_date <= '{filters['to_date']}' AND "
        subQueryFilter += f"posting_date <= '{filters['to_date']}' AND "

    mainQueryFilter = clean_filter_query(mainQueryFilter)
    subQueryFilter = clean_filter_query(subQueryFilter)

    data = frappe.db.sql(f"""
	SELECT 
		item,
		warehouse,
		SUM(qty_change) AS balance_qty,
		SUM(qty_change*in_out_rate) AS balance_value,
		SUM(
			CASE
				WHEN qty_change > 0 THEN qty_change
				ELSE 0
				END
		) AS in_qty,
		SUM(
			CASE
				WHEN qty_change > 0 THEN qty_change*in_out_rate
				ELSE 0
				END
		) AS in_value,
		SUM(
			CASE
				WHEN qty_change < 0 THEN qty_change
				ELSE 0
				END
		) AS out_qty,
		SUM(
			CASE
				WHEN qty_change < 0 THEN qty_change*in_out_rate
				ELSE 0
				END
		) AS out_value,
		(
			SELECT ROUND(sub.valuation_rate, 2)
			FROM `tabStock Ledger Entry` AS sub
			WHERE sub.item = main.item AND sub.warehouse = main.warehouse {subQueryFilter}
			ORDER BY sub.posting_date DESC, sub.posting_time DESC
			LIMIT 1
		) AS latest_valuation_rate
	FROM `tabStock Ledger Entry` AS main
	{mainQueryFilter}
	GROUP BY item, warehouse
	""")
    print(data)
    return stock_balance_report_columns, data
