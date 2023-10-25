import frappe
from frappe.query_builder import functions as fn

@frappe.whitelist()
def fetch_rate_of_item(item_code, warehouse_id, type):
    valuation_rate = 0
    doctype = frappe.qb.DocType("Stock Ledger Entry")
    if type == "FIFO":
        rate = (frappe.qb.from_(doctype)
                .select(fn.Sum(doctype.qty_change * doctype.in_out_rate) / fn.Sum(doctype.qty_change))
                .where(doctype.item == item_code)
                .where(doctype.warehouse == warehouse_id)
                .groupby(doctype.item, doctype.warehouse)
                .run(as_list=True))
        if len(rate) > 0 and len(rate[0]) > 0:
            valuation_rate = max(rate[0][0], 0)
    elif type == "Moving Average":
        rate = (frappe.qb.from_(doctype)
                .select(fn.Avg(doctype.in_out_rate))
                .where(doctype.item == item_code)
                .where(doctype.warehouse == warehouse_id)
                .groupby(doctype.item, doctype.warehouse)
                .run(as_list=True))
        if len(rate) > 0 and len(rate[0]) > 0:
            valuation_rate = rate[0][0]

    return valuation_rate
