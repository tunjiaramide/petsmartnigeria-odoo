from odoo import models

# Animals shown in the header mega menu, in this order (xml ids in data/categories.xml).
NAV_CATEGORIES = ('cat_dog', 'cat_cat', 'cat_bird', 'cat_fish', 'cat_small_pet', 'cat_reptile', 'cat_horse', 'cat_pharmacy')


class Website(models.Model):
    _inherit = 'website'

    def _petmart_category_url(self, name):
        """Shop URL of one of the theme's categories (e.g. 'cat_dog').

        Staff can delete a category in the back end; the header, footer and
        homepage must keep working, so a missing one falls back to the shop."""
        category = self.env.ref('petmart_theme.%s' % name, raise_if_not_found=False)
        if not category:
            return '/shop'
        return '/shop/category/%s' % self.env['ir.http']._slug(category.sudo())

    def _petmart_nav_categories(self):
        """Top-level categories of the header mega menu. Their groups and
        sub-categories are read from the category tree, so staff edits show up
        in the menu without a code change."""
        categories = self.env['product.public.category'].sudo()
        for name in NAV_CATEGORIES:
            category = self.env.ref('petmart_theme.%s' % name, raise_if_not_found=False)
            if category:
                categories |= category.sudo()
        return categories
