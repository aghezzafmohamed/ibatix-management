# -*- coding: utf-8 -*-

{
    'name': 'ItriSol Backend Theme',
    'version': '19.0.1.0.0',
    'category': 'Themes/Backend',
    'summary': 'ItriSol Backend Theme is an attractive theme for backend',
    'description': """Minimalist and elegant backend theme for Odoo 18, 
     Backend Theme, Theme""",
    'author': 'AGHEZZAF Mohamed',
    'website': "http://www.itrisol.com",
    'company': 'ItriSol',
    'support': 'itrisol.contact@gmail.com',
    'depends': ['web', 'mail'],
    'data': [
        'views/icons_views.xml',
        'views/layout_templates.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('before', 'web/static/src/scss/primary_variables.scss',
             'itrisol_theme/static/src/scss/theme.scss'),
        ],
        'web.assets_backend': {
            '/itrisol_theme/static/src/scss/itrieducat_theme.scss',
            '/itrisol_theme/static/src/js/chrome/sidebar_menu.js',
            '/itrisol_theme/static/src/xml/top_bar_templates.xml',
        },
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'pre_init_hook': 'test_pre_init_hook',
    'post_init_hook': 'test_post_init_hook',
    'installable': True,
    'auto_install': False,
    'application': False
}
