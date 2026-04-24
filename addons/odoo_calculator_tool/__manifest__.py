# -*- coding: utf-8 -*-

{
    'name': "Odoo Calculator",
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Perform basic math calculations effortlessly within Odoo.""",
    'description': """This module makes it easy for you to carry out simple
    mathematical operations via the Odoo user interface.""",
    'author': 'AGHEZZAF Mohamed',
    'website': "http://www.itrisol.com",
    'company': 'ItriSol',
    'support': 'itrisol.contact@gmail.com',
    'depends': ['base'],
    'assets': {
        'web.assets_backend': {
            'odoo_calculator_tool/static/src/scss/calculator.scss',
            'odoo_calculator_tool/static/src/xml/calculator.xml',
            'odoo_calculator_tool/static/src/js/calculator.js',
        },
    },
    'images': ['static/description/banner.png'],
    'license': "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False
}
