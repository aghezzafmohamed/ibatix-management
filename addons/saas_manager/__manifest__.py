{
    'name': 'SaaS Manager (Coolify)',
    'version': '1.0',
    'category': 'Services/Project',
    'summary': 'Gérez vos instances Coolify liées aux Projets Odoo',
    'depends': ['base', 'project', 'mail', 'sale_management'],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/mail_template.xml',

        # Views
        'views/saas_license_type_views.xml',
        'views/project_views.xml',
        'views/saas_environment_views.xml',
        'views/saas_instance_views.xml',
        'views/saas_server_views.xml',
        'views/saas_coolify_views.xml',
        'views/saas_license_views.xml',
        'views/res_partner_views.xml',
        'views/menu.xml',
    ],
    'external_dependencies': {
        'python': ['paramiko', 'requests'],
    },
    'assets': {
        'web.assets_backend': [
            'saas_manager/static/src/css/console.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}