# -*- coding: utf-8 -*-
{
    'name': 'Extend expense',
    'version': '19.0.0.0',
    'summary': 'Extend expense',
    'description': 'Change name and remove somme fuetures',
    'category': '',
    'author': 'AGHEZZAF Mohamed',
    'website': "http://www.itrisol.com",
    'company': 'ItriSol',
    'support': 'itrisol.contact@gmail.com',
    'license': 'LGPL-3',
    'depends': ['hr_expense', 'web'],
    'data': [
        # Views
        'views/hide_menu_views.xml',
        'views/hr_expense_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'extend_expense/static/src/views/*.xml',
        ],
    },
    'auto_install': ['hr_expense'],
}