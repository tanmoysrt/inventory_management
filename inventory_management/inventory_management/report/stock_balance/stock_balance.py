# Copyright (c) 2023, Tanmoy Sarkar and contributors
# For license information, please see license.txt
from pypika import Case, Criterion, Order, AliasedQuery

import frappe
from frappe import _

from frappe.query_builder import functions as fn

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


def execute(filters=None):
    if not filters:
        filters = {}

    main = frappe.qb.Table("tabStock Ledger Entry", alias="main")
    sub = frappe.qb.Table("tabStock Ledger Entry", alias="sub")

    main_query_filters = []
    sub_query_filters = []

    if "item" in filters:
        main_query_filters.append(main.item == filters.get("item"))
    if "warehouse" in filters:
        main_query_filters.append(main.warehouse == filters.get("warehouse"))
    if "from_date" in filters:
        main_query_filters.append(main.posting_date >= filters.get("from_date"))
        sub_query_filters.append(sub.posting_date >= filters.get("from_date"))
    if "to_date" in filters:
        main_query_filters.append(main.posting_date <= filters.get("to_date"))
        sub_query_filters.append(sub.posting_date <= filters.get("to_date"))

    sub_query = (frappe.qb.from_(sub)
                 .select(fn.Round(sub.valuation_rate, 2))
                 .where(sub.item == main.item)
                 .where(sub.warehouse == main.warehouse)
                 .where(Criterion.all(sub_query_filters))
                 .orderby(sub.posting_date, order=Order.desc)
                 .orderby(sub.posting_time, order=Order.desc).limit(1))

    data = (frappe.qb.from_(main).select(
        main.item,
        main.warehouse,
        fn.Sum(main.qty_change).as_('balance_qty'),
        fn.Sum(main.qty_change * main.in_out_rate).as_('balance_value'),
        fn.Sum(Case().when(main.qty_change > 0, main.qty_change).else_(0)).as_('in_qty'),
        fn.Sum(Case().when(main.qty_change > 0,
                           main.qty_change * main.in_out_rate).else_(0)).as_('in_value'),
        fn.Sum(Case().when(main.qty_change < 0, main.qty_change).else_(0)).as_('out_qty'),
        fn.Sum(Case().when(main.qty_change < 0,
                           main.qty_change * main.in_out_rate).else_(0)).as_('out_value'),
        sub_query.as_('latest_valuation_rate')
    ).where(Criterion.all(main_query_filters))
            .groupby(main.item, main.warehouse))

    result = data.run(as_dict=True)
    return stock_balance_report_columns, result
