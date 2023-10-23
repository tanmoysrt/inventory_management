// Copyright (c) 2023, Tanmoy Sarkar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stock Entry', {
    refresh: (frm) => update_on_change_type(frm),
    type: (frm, cdt, cdn) => update_on_change_type(frm),
});

frappe.ui.form.on('Stock Entry Transaction', {
    // items_add: function (frm, cdt, cdn) {
    //
    // },
    item: (frm, cdt, cdn) => fetch_item_rate(cdt, cdn),
    target_warehouse: (frm, cdt, cdn) => fetch_item_rate(cdt, cdn),
    source_warehouse: (frm, cdt, cdn) => fetch_item_rate(cdt, cdn),
});

function update_on_change_type(frm){
    if(frm.doc.type === 'Receive') {
        frm.fields_dict.items.grid.toggle_enable("source_warehouse", false)
        frm.fields_dict.items.grid.toggle_reqd("source_warehouse", false)
        frm.fields_dict.items.grid.toggle_enable("target_warehouse", true)
        frm.fields_dict.items.grid.toggle_reqd("target_warehouse", true)
        frm.fields_dict.items.grid.toggle_enable("rate", true)
    } else if(frm.doc.type === 'Consume') {
        frm.fields_dict.items.grid.toggle_enable("source_warehouse", true)
        frm.fields_dict.items.grid.toggle_reqd("source_warehouse", true)
        frm.fields_dict.items.grid.toggle_enable("target_warehouse", false)
        frm.fields_dict.items.grid.toggle_reqd("target_warehouse", false)
        frm.fields_dict.items.grid.toggle_enable("rate", false)
    } else if(frm.doc.type === 'Transfer') {
        frm.fields_dict.items.grid.toggle_enable("source_warehouse", true)
        frm.fields_dict.items.grid.toggle_reqd("source_warehouse", true)
        frm.fields_dict.items.grid.toggle_enable("target_warehouse", true)
        frm.fields_dict.items.grid.toggle_reqd("target_warehouse", true)
        frm.fields_dict.items.grid.toggle_enable("rate", true)
    }
}

function fetch_item_rate(cdt, cdn){
    let row = frappe.get_doc(cdt, cdn);
    const item_code = row.item;
    const target_warehouse = row.target_warehouse;
    const source_warehouse = row.source_warehouse;
    const type = cur_frm.fields_dict.type.value;
    if(item_code && type === "Consume" && source_warehouse){
        fetch_item_rate_helper(item_code, source_warehouse, cdt, cdn)
    }
    if(item_code && type === "Receive" && target_warehouse){
        fetch_item_rate_helper(item_code, target_warehouse, cdt, cdn)
    }
    if(item_code && type === "Transfer" && target_warehouse && source_warehouse){
        fetch_item_rate_helper(item_code, source_warehouse, cdt, cdn)
    }
    // TODO: implement for transfer
}

async function fetch_item_rate_helper(item_code, warehouse, cdt, cdn){
    frappe.call({
        method: "inventory_management.helpers.fetch_rate_of_item",
        args: {
            item_code: item_code,
            warehouse_id: warehouse,
            type: cur_frm.fields_dict.valuation_method.value
        },
        callback: function (r) {
            frappe.get_doc(cdt, cdn).rate = r.message
            if (r.message === 0) {
                cur_frm.fields_dict.items.grid.toggle_enable("rate", true)
            }
            cur_frm.refresh_field("items")
        }
    });
}