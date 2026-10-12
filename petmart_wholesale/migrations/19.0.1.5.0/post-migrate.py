def migrate(cr, version):
    """No overselling: customers cannot order more than is in stock. New products
    get this from the field default; switch it on for the ones that already exist."""
    cr.execute("UPDATE product_template SET allow_out_of_stock_order = false WHERE allow_out_of_stock_order IS NOT false")
    cr.execute("""
        DELETE FROM ir_default
         WHERE field_id IN (SELECT id FROM ir_model_fields
                             WHERE model = 'product.template' AND name = 'allow_out_of_stock_order')
    """)
    # Pricing tiers: customers approved before tiers existed were all given the Wholesale price list.
    cr.execute("""
        UPDATE res_partner SET wholesale_pricing_tier = 'wholesale'
         WHERE wholesale_state = 'approved' AND wholesale_pricing_tier IS NULL
    """)
