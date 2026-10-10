from odoo import SUPERUSER_ID, api

# The 12 categories created by earlier versions, moved into the new tree
# (animal > group > sub-category). They are "noupdate" data, so the data file
# alone does not change them on databases where they already exist.
# xml id: (name, parent xml id, sequence)
LEGACY = {
    'cat_dog': ('Dog', None, 1),
    'cat_cat': ('Cat', None, 2),
    'cat_bird': ('Bird', None, 3),
    'cat_fish': ('Fish', None, 4),
    'cat_small_pet': ('Small Pet', None, 5),
    'cat_reptile': ('Reptile', None, 6),
    'cat_pharmacy': ('Pharmacy', None, 8),
    'cat_dog_food': ('Food', 'cat_dog', 1),
    'cat_dog_treats': ('Treats', 'cat_dog', 3),
    'cat_cat_food': ('Food', 'cat_cat', 1),
    'cat_cat_litter': ('Litters & Accessories', 'cat_cat', 2),
    'cat_grooming': ('Grooming', 'cat_dog_supplies', 11),
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for name, (label, parent_name, sequence) in LEGACY.items():
        category = env.ref('petmart_theme.%s' % name, raise_if_not_found=False)
        if not category:
            continue
        values = {'name': label, 'sequence': sequence, 'parent_id': False}
        if parent_name:
            parent = env.ref('petmart_theme.%s' % parent_name, raise_if_not_found=False)
            if not parent:
                continue
            values['parent_id'] = parent.id
        category.write(values)
