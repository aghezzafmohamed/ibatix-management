# -*- coding: utf-8 -*-
{
    "name": "Customisation base",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "category": "Website",
    "summary": "Customisation favicon/title/user menu",
    'author': 'ItriSol',
    'company': 'ItriSol',
    'support': 'itrisol.contact@gmail.com',
    'website': "https://www.itrisol.com",
    "depends": [
        "base_setup",
        "mail",
        "web",
    ],
    "data": [
        'views/templates.xml',
        'views/res_users_views.xml',
        'views/res_config_setting_views.xml',
        'views/webclient_templates.xml',
        'data/res_partner_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            #'web_custome/static/src/js/web_window_title.js',
            # 'web_custome/static/src/js/user_menuitems.js',
        ],
    },
    "installable": True,
    'sequence': 3,
}
