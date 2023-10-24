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

frappe.query_reports["Stock Balance"] = {
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
        }
	],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname === "in_qty") {
            return format_cell(data.in_qty);
        } else if (column.fieldname === "in_value") {
            return format_cell(data.in_value);
        } else if (column.fieldname === "out_qty") {
            return format_cell(data.out_qty);
        }
        else if (column.fieldname === "out_value") {
            return format_cell(data.out_value);
        }
        return value;
    }
};
