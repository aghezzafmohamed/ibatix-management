# -*- coding: utf-8 -*-
{
    'name': 'Thème Ibatix',
    'description': 'Thème personnalisé et ultra-rapide pour Ibatix',
    'category': 'Theme/Corporate',
    'version': '19.0.1.0.0',
    'depends': ['website', 'website_crm', 'website_sale'],
    'data': [
        'views/homepage.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_ibatix/static/src/css/style.css',
            'theme_ibatix/static/src/js/main.js',
        ],
    },
    'installable': True,
    'application': False,
}