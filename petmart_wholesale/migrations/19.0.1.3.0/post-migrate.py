from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Turn the brand text typed on products into brand records (matching the
    preloaded ones regardless of capitals), then drop the old text column."""
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'product_template' AND column_name = 'petmart_brand_legacy'
    """)
    if not cr.fetchone():
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    Brand = env['petmart.brand'].with_context(active_test=False)
    brands = {brand.name.strip().lower(): brand for brand in Brand.search([])}
    cr.execute("""
        SELECT id, btrim(petmart_brand_legacy) FROM product_template
         WHERE coalesce(btrim(petmart_brand_legacy), '') != ''
    """)
    for product_id, text in cr.fetchall():
        brand = brands.get(text.lower())
        if not brand:
            brand = brands[text.lower()] = Brand.create({'name': text})
        env['product.template'].browse(product_id).petmart_brand_id = brand
    env.flush_all()
    cr.execute("ALTER TABLE product_template DROP COLUMN petmart_brand_legacy")
