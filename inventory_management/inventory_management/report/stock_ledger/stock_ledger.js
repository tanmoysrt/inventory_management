// Copyright (c) 2023, Tanmoy Sarkar and contributors
// For license information, please see license.txt


function format_cell(value) {
    if (value > 0) {
        return `<span style="color:green">+${value}</span>`;
    } else if (value < 0) {
        return `<span style="color:red">${value}</span>`;
    } else {
        return value;
    }
}

frappe.query_reports["Stock Ledger"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
        },
        {
            "fieldname": "item",
            "label": "Item",
            "fieldtype": "Link",
            "options": "Item",
        },
        {
            "fieldname": "warehouse",
            "label": "Warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
        },
        {
            "fieldname": "type",
            "label": "Type",
            "fieldtype": "Select",
            "options": [
                "Receive",
                "Consume"
            ]
        },
        {
            "fieldname": "stock_entry",
            "label": "Stock Entry",
            "fieldtype": "Link",
            "options": "Stock Entry"
        }
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        // if(value.id === "qty_change") {
        // 	// fetch value from columnDef
        // }
        if (column.fieldname === "qty_change") {
            return format_cell(data.qty_change);
        } else if (column.fieldname === "value_change") {
            return format_cell(data.value_change);
        }
        return value;
    }
};
