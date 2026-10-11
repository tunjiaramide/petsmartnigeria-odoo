from odoo import fields, models


class PetmartBrand(models.Model):
    _name = 'petmart.brand'
    _description = 'Product brand'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    product_ids = fields.One2many('product.template', 'petmart_brand_id', string='Products')
    product_count = fields.Integer(compute='_compute_product_count')

    _name_uniq = models.Constraint('unique (name)', "This brand already exists.")

    def _compute_product_count(self):
        counts = dict(self.env['product.template']._read_group(
            [('petmart_brand_id', 'in', self.ids)], ['petmart_brand_id'], ['__count']))
        for brand in self:
            brand.product_count = counts.get(brand, 0)
