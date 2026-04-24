# -*- coding: utf-8 -*-

from io import BytesIO
from odoo import http
from odoo.tools.misc import file_open


class WebFavicon(http.Controller):

    @http.route('/web_favicon/favicon', type='http', auth="none")
    def icon(self):
        request = http.request
        # The image size must be 300*300 px
        with file_open('web_custome/static/src/img/favicon.png', 'rb') as f:
            icon_img = f.read()
        favicon = BytesIO(icon_img)
        return request.make_response(
            favicon.read(), [('Content-Type', 'image/png')])
