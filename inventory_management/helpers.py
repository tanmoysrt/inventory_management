import frappe

@frappe.whitelist()
def fetch_rate_of_item(item_code, warehouse_id, type):
    valuation_rate = 0
    if type == "FIFO":
        rate = frappe.db.sql("""SELECT (SUM(sle.qty_change*sle.in_out_rate)/SUM(sle.qty_change)) as rate
                                FROM `tabStock Ledger Entry` as sle
                                WHERE sle.item = %s AND sle.warehouse = %s
                                GROUP BY sle.item, sle.warehouse""", (item_code, warehouse_id), as_list=True)
        if len(rate) > 0 and len(rate[0]) > 0:
            valuation_rate = max(rate[0][0], 0)
    elif type == "Moving Average":
        rate = frappe.db.sql("""SELECT AVG(sle.in_out_rate) as rate
                                FROM `tabStock Ledger Entry` as sle
                                WHERE sle.item = %s AND sle.warehouse = %s
                                GROUP BY sle.item, sle.warehouse""", (item_code, warehouse_id), as_list=True)
        if len(rate) > 0 and len(rate[0]) > 0:
            valuation_rate = rate[0][0]

    return valuation_rate
