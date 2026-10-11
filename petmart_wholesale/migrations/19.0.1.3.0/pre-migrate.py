def migrate(cr, version):
    """Brand used to be free text on the product. It becomes a pick-list
    (petmart.brand); keep the typed text aside so post-migrate can convert it."""
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'product_template' AND column_name = 'petmart_brand_id'
    """)
    if cr.fetchone():
        return  # already converted
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'product_template' AND column_name = 'petmart_brand'
    """)
    if cr.fetchone():
        cr.execute("ALTER TABLE product_template RENAME COLUMN petmart_brand TO petmart_brand_legacy")
