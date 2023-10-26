from pypika import Order

import frappe

@frappe.whitelist()
def fetch_rate_of_item(item_code, warehouse_id):
    doctype = frappe.qb.DocType("Stock Ledger Entry")
    # fetch latest valuation_rate of item in warehouse
    rate = (
        frappe.qb.from_(doctype)
        .select(doctype.valuation_rate)
        .where(doctype.item == item_code)
        .where(doctype.warehouse == warehouse_id)
        .orderby(doctype.posting_date, order=Order.desc)
        .limit(1)
        .run(as_list=True)
    )
    if len(rate) > 0 and len(rate[0]) > 0:
        return rate[0][0]
    return 0
