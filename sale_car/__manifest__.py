# 
{
    "name": "Sales Cars",
    "version": "15.0.2.0.0",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "category": "Sales Management",
    "license": "AGPL-3",
    "depends": [
        "sale_management","sale", "base", "hr", "fleet", "account",'stock','pdc_payment'
    ],
    "website": "",
    # "maintainers": ["pedrobaeza"],
    "data": [
        "security/ir.model.access.csv",
        "data/sale_car_data.xml",
        "views/sale_partner.xml",
        "views/sale_order_view.xml",
        "views/sale_config.xml",
        # "views/sale_target.xml",
        "views/sale_contract.xml",
        "views/sale_installment.xml",
        "views/product.xml",
    ],
    "installable": True,
}
