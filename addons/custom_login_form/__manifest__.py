# -*- encoding: utf-8 -*-
{
    'name': 'Custom Login Background',
    'version': '19.0.2.0.0',
    'category': 'website',
    'summary': "You can customise the login page (background image, color, form position).",
    'author': 'AGHEZZAF Mohamed',
    'website': "http://www.itrisol.com",
    'company': 'ItriSol',
    'support': 'itrisol.contact@gmail.com',
    'license': 'AGPL-3',
    'depends': ['base', 'base_setup', 'web', 'auth_signup'],
    'data': [
        'templates/login_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'custom_login_form/static/src/scss/web_login_style.scss',
        ],
    },
    'installable': True,
    'application': True,
}