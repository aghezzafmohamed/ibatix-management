# -*- coding: utf-8 -*-
{
    'name': "ItriSol Base",
    'description': """
        Adding specific tools to Odoo project
    """,
    'author': "ItriSol",
    'website': "http://www.itrisol.com",
    'category': 'Services/Project',
    'version': '18.0.1.0.0',
    'depends': ['base', 'project', 'account', 'sale', 'sale_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_views.xml',
        'wizard/sale_add_task_wizard.xml',
        'views/sale_views.xml',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'reports/invoice_report_views.xml',
    ],
    'license': 'LGPL-3',
}
