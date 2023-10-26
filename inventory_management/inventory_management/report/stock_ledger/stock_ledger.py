# Copyright (c) 2023, Tanmoy Sarkar and contributors
# For license information, please see license.txt
from pypika import Criterion
from pypika.terms import AnalyticFunction as an

import frappe
from frappe import _
from frappe.query_builder import functions as fn

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


def execute(filters=None):
    if not filters:
        filters = {}
    subquery_filters = []
    main_query_filter = []
    stock_ledger_entry = frappe.qb.DocType('Stock Ledger Entry')

    if filters.get('item', ''):
        subquery_filters.append(stock_ledger_entry.item == filters.get('item', ''))
    if filters.get('warehouse', ''):
        subquery_filters.append(stock_ledger_entry.warehouse == filters.get('warehouse', ''))
    if filters.get('posting_date', ''):
        subquery_filters.append(stock_ledger_entry.posting_date >= filters.get('posting_date', ''))
    if filters.get('posting_time', ''):
        subquery_filters.append(stock_ledger_entry.posting_time >= filters.get('posting_time', ''))

    if filters.get('type', '') == 'Receive':
        subquery_filters.append(stock_ledger_entry.qty_change > 0)
    elif filters.get('type', '') == 'Consume':
        subquery_filters.append(stock_ledger_entry.qty_change < 0)

    if filters.get('stock_entry', ''):
        subquery_filters.append(stock_ledger_entry.stock_entry == filters.get('stock_entry', ''))

    item_warehouse_subquery = (
        frappe.qb.from_(stock_ledger_entry)
        .select(
            stock_ledger_entry.item,
            stock_ledger_entry.warehouse,
            stock_ledger_entry.qty_change,
            stock_ledger_entry.in_out_rate,
            stock_ledger_entry.valuation_rate,
            stock_ledger_entry.posting_date,
            stock_ledger_entry.posting_time,
            (stock_ledger_entry.qty_change * stock_ledger_entry.valuation_rate).as_('value_change'),
            an("SUM", stock_ledger_entry.qty_change).over(stock_ledger_entry.item,
                                                          stock_ledger_entry.warehouse).orderby(
                stock_ledger_entry.posting_date, stock_ledger_entry.posting_time).as_('balance_qty'),
            an("SUM", stock_ledger_entry.qty_change * stock_ledger_entry.valuation_rate).over(stock_ledger_entry.item,
                                                                                              stock_ledger_entry.warehouse).orderby(
                stock_ledger_entry.posting_date, stock_ledger_entry.posting_time).as_('balance_value'),
            stock_ledger_entry.stock_entry
        ).where(Criterion.all(subquery_filters))
    )
    stock_entry_with_calculations = (frappe.qb.from_(item_warehouse_subquery)
                                     .select('*',
                                             (item_warehouse_subquery.value_change + fn.Coalesce(
                                                 an('LAG', item_warehouse_subquery.balance_value, 1)
                                                 .over(item_warehouse_subquery.item, item_warehouse_subquery.warehouse)
                                                 .orderby(item_warehouse_subquery.posting_date,
                                                          item_warehouse_subquery.posting_time), 0)
                                              ).as_('updated_balance_value')))
    data = (
        frappe.qb.from_(stock_entry_with_calculations)
        .select('*',
                fn.Round(stock_entry_with_calculations.updated_balance_value, 2).as_('balance_value'),
                fn.Round(stock_entry_with_calculations.valuation_rate, 2).as_('valuation_rate'),
                fn.Round(stock_entry_with_calculations.value_change, 2).as_('value_change'))
        .where(Criterion.all(main_query_filter))
    )
    result = data.run(as_dict=True)
    return stock_ledger_report_columns, result
