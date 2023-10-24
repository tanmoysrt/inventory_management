# Copyright (c) 2023, Tanmoy Sarkar and contributors
# For license information, please see license.txt
import frappe
from frappe import _

# import frappe

stock_ledger_report_columns = [
    {
        'fieldname': 'posting_date',
        'label': _('Posting Date'),
        'fieldtype': 'Date',
        'options': ''
    },
    {
        'fieldname': 'posting_time',
        'label': _('Posting Time'),
        'fieldtype': 'Time',
        'options': ''
    },
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
        'fieldname': 'qty_change',
        'label': _('Quantity Change'),
        'fieldtype': 'Int',
        'options': ''
    },
    {
        'fieldname': 'balance_qty',
        'label': _('Balance Quantity'),
        'fieldtype': 'Int',
        'options': ''
    },
    {
        'fieldname': 'in_out_rate',
        'label': _('In/Out Rate'),
        'fieldtype': 'Float',
        'options': ''
    },
    {
        'fieldname': 'valuation_rate',
        'label': _('Valuation Rate'),
        'fieldtype': 'Float',
        'options': ''
    },
    {
        'fieldname': 'value_change',
        'label': _('Value Change'),
        'fieldtype': 'Float',
        'options': ''
    },
    {
        'fieldname': 'balance_value',
        'label': _('Balance Value'),
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
    generatedSubQueryFilter = "WHERE "
    if "item" in filters:
        generatedSubQueryFilter += f"item = '{filters['item']}' AND "
    if "warehouse" in filters:
        generatedSubQueryFilter += f"warehouse = '{filters['warehouse']}' AND "
    if "from_date" in filters:
        generatedSubQueryFilter += f"posting_date >= '{filters['from_date']}' AND "
    if "to_date" in filters:
        generatedSubQueryFilter += f"posting_date <= '{filters['to_date']}' AND "

    generatedSubQueryFilter = clean_filter_query(generatedSubQueryFilter)

    generatedFilter = "WHERE "
    if "type" in filters:
        if filters['type'] == "Receive":
            generatedFilter += f"qty_change > 0 AND "
        elif filters['type'] == "Consume":
            generatedFilter += f"qty_change < 0 AND "
    if "stock_entry" in filters:
        generatedFilter += f"stock_entry = '{filters['stock_entry']}' AND "

    generatedFilter = clean_filter_query(generatedFilter)


    data = frappe.db.sql(f"""
    WITH inventory_with_calculations AS (
      SELECT
        item,
        warehouse,
        qty_change,
        in_out_rate,
        valuation_rate,
        posting_date,
        posting_time,
        qty_change * valuation_rate AS value_change,
        SUM(qty_change) OVER (PARTITION BY item, warehouse ORDER BY posting_date, posting_time) AS balance_qty,
        SUM(qty_change * valuation_rate) OVER (PARTITION BY item, warehouse ORDER BY posting_date, posting_time) AS balance_value,
        stock_entry
      FROM `tabStock Ledger Entry`
      {generatedSubQueryFilter}
    ),
    stock_entry_with_calculations AS (
        SELECT
            *,
            COALESCE(LAG(value_change, 1) OVER (PARTITION BY item, warehouse ORDER BY posting_date, posting_time), 0) + value_change AS updated_balance_value
        FROM inventory_with_calculations
        ORDER BY posting_date ASC, posting_time ASC
    )
    SELECT 
        *,
        ROUND(updated_balance_value, 2) AS balance_value,
        ROUND(valuation_rate, 2) AS valuation_rate,
        ROUND(value_change, 2) AS value_change
    FROM stock_entry_with_calculations
    {generatedFilter}
    """, as_dict=True)
    return stock_ledger_report_columns, data
