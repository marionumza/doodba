# -*- coding: utf-8 -*-
from openerp import models, fields


class ProductProduct(models.Model):
    _inherit = "product.product"

    rapport_quota = fields.Float('Rapport quota')
