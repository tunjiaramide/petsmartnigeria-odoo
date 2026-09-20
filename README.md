# PETSMART NIGERIA – Odoo 19 wholesale (B2B) shop

Custom Odoo modules for the PETSMART NIGERIA wholesale website. Hosted on **Odoo.sh**.

| module | what it does |
|---|---|
| `petmart_wholesale` | Business rules: login-only prices, wholesale account approval, wholesale pricelist, minimum order, AVAILABLE / LOW STOCK / OUT OF STOCK (no quantities shown), 2% online-order discount, New Arrival / Back in stock tags, ₦ sign before the amount |
| `petmart_theme` | Homepage, header, footer, styling and site categories |

Install order: `petmart_wholesale` first, then `petmart_theme`.

`petmart_catalog` (sample products) exists only on the developer's machine and is deliberately
**not** in this repository – never install sample data on production.

## Branches (Odoo.sh)
`development` → test build  ·  `staging` → copy of production data  ·  `production` → live.
Never commit straight to `production`. Full procedure: **[ODOO_SH_DEPLOY.md](ODOO_SH_DEPLOY.md)**.

## Rules for changing code
- Edit the theme in `petmart_theme/views/*.xml` and `static/src/scss/petmart.scss`. Do **not** restyle the
  homepage with Odoo's drag-and-drop editor (it forks the page away from this code).
- Python changes need a module upgrade after deploy; XML/SCSS changes too.
- Never commit secrets (API keys, passwords). Flutterwave keys are entered in Odoo, not in code.
- Keep `version` in each `__manifest__.py` up to date when releasing.
