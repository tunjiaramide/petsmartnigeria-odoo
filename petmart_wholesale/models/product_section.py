from odoo import fields, models

# offered by the "Add standard sections" button on the product form; staff can rename or add any other title
STANDARD_SECTIONS = ['Ingredients', 'Calorie Content', 'Feeding Guide', 'Guaranteed Analysis']


class PetmartProductSection(models.Model):
    """One dropdown in the product page's "details" area (Ingredients, Feeding Guide, ...)."""
    _name = 'petmart.product.section'
    _description = 'Product detail section'
    _order = 'sequence, id'

    product_tmpl_id = fields.Many2one('product.template', string='Product', required=True,
                                      ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Title', required=True, translate=True)
    content = fields.Html(string='Content', translate=True)
