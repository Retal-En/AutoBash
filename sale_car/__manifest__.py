# 
{
    "name": "Sales Cars",
    "version": "15.0.2.0.0",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "category": "Sales Management",
    "license": "AGPL-3",
    "depends": [
        "sale","hr",
    ],
    "website": "",
    # "maintainers": ["pedrobaeza"],
    "data": [
        "security/ir.model.access.csv",
        "data/sale_car_data.xml",
        "views/sale_order_view.xml",
        "views/sale_contract.xml",
        "views/sale_installment.xml",
    ],
    "installable": True,
}
