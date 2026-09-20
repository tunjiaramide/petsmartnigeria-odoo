# PETSMART NIGERIA – Odoo.sh deployment guide

Follow the parts **in order**: 0 (create the Odoo.sh project) → A (production base) → B (publish the code) → C (products and go-live).
Never skip the test steps. This guide was written without access to your Odoo.sh dashboard: menu names
are from Odoo's documentation and may differ slightly – where a step says **(verify)**, confirm it on screen
before relying on it.

---

## 0. How it fits together

| lives in… | what |
|---|---|
| **Git (GitHub)** | the two modules `petmart_wholesale` and `petmart_theme` – all code, design and rules |
| **The production database** | company, users, products, pictures, stock, wholesale prices, Flutterwave keys, settings |

- Code is pushed with git. Data is entered in Odoo (or imported). **Uploading products never goes through git.**
- Branch flow: `development` (throw-away test build) → `staging` (copy of real data) → `production` (live).
- **Test emails and payments do not go out from development/staging builds (verify)** – Odoo.sh captures
  mail in the branch's *Mails* tab, so approval emails are checked there, not in an inbox.
- `petmart_catalog` (sample products) is git-ignored on purpose. It never goes to Odoo.sh.

### What you need before starting
- [ ] Odoo.sh project (Enterprise subscription) on **Odoo 19.0**
- [ ] A private GitHub repository, connected to the Odoo.sh project
- [ ] Your domain name, and access to its DNS settings (e.g. `shop.yourdomain.com.ng`)
- [ ] Company logo (PNG), company address, phone, email, RC / Tax ID
- [ ] Flutterwave account with **live** and **test** API keys
- [ ] An outgoing email account (SMTP) or a decision to use Odoo.sh's mail service
- [ ] Your real product list as a spreadsheet, with photos

---

## PART 0 – Create the Odoo.sh project (one time)  ← start here

**Odoo Online and Odoo.sh are different products.** A database at `something.odoo.com` opened from
odoo.com → *My Databases* may be an **Odoo Online** trial. Odoo Online **cannot run custom modules or Git** –
our code only works on **Odoo.sh**. Never try to install `petmart_wholesale` / `petmart_theme` on an Odoo Online database.

1. Log in at **odoo.com → My Account → Subscriptions**. The subscription must be **active** (not a trial),
   on the **Custom** plan, with **hosting = Odoo.sh**. If it is still a trial or a quote: the customer (who pays)
   must confirm the order, or contact Odoo sales/support to convert it.
2. Open **https://www.odoo.sh** and sign in with the **same Odoo.com account** that owns the subscription
   (if the client owns it, they create the project or invite you as a collaborator).
3. Click **Deploy your platform / Create project (verify wording)** and fill in:
   - the subscription to use
   - project name (this becomes the address, e.g. `petsmart-nigeria.odoo.com`)
   - your **GitHub** account and the repository (private)
   - **Odoo version: 19.0 (stable)** – our code was built and tested on 19.0. Do **not** pick a `saas~` intermediate
     version unless you have re-tested every feature on it. *(verify the list on screen)*
4. The project opens with **Branches / Builds / Logs / Backups / Settings** tabs – that confirms it is Odoo.sh.
   The first branch is `production`; you will add `staging` and `development` next.
5. Only now continue with Part A.

---

## PART A – Prepare the production base (no custom code yet)

### A1. Make sure the production database is Nigeria / Naira  ← most important step
The company currency **cannot be changed after the first accounting entry**.
1. Open the production database → **Settings → Companies** → your company.
2. **Country = Nigeria** and **Currency = NGN (₦)**. Nothing else is acceptable.
3. If it says USD/EUR:
   - **No accounting entries yet** (fresh database): change it now, before installing any app.
   - **Entries already exist**: STOP. Do not fix by hand. Create a new production database
     (Odoo.sh support / project settings) with Nigeria selected and **demo data unticked**.
4. Avatar (top right) → **My Preferences** → Timezone `Africa/Lagos`, Language English.

### A2. Company identity
Settings → Companies: company name (PETSMART NIGERIA), logo, address, phone, email, RC / Tax ID.

### A3. Install the standard apps – in this order (Apps menu)
1. **Nigeria – Accounting** (`l10n_ng`) – chart of accounts and VAT
2. **eCommerce** (`website_sale`)
3. **Inventory** (`stock`) and **Expiration Dates** (`product_expiry`)
4. **Sales** (`sale_management`), **Contacts**, **Dashboards**
5. eCommerce extras: **Wishlist**, **Loyalty** (`website_sale_loyalty`), **Stock** on website (`website_sale_stock`)
6. **Flutterwave** payment provider (`payment_flutterwave`)
7. **Two-factor authentication** (`auth_totp`) for staff

(If you skip one, `petmart_wholesale` in Part B pulls in what it depends on, but installing them yourself first,
in this order, lets you check the Nigerian accounting loaded before anything else.)

### A4. Address, HTTPS and mail
1. **Domain (verify):** Odoo.sh project → Settings → custom domains → add `shop.yourdomain.com.ng`.
   At your DNS provider add the record Odoo.sh shows (normally a CNAME to your `*.odoo.com` address).
   Odoo.sh issues the HTTPS certificate itself.
2. In Odoo (developer mode: add `?debug=1` to the URL): **Settings → Technical → System Parameters**
   - `web.base.url` = `https://shop.yourdomain.com.ng`
   - add `web.base.url.freeze` = `True`
   Then leave developer mode (remove `?debug=1`).
3. **Outgoing mail:** Settings → Technical → Outgoing Mail Servers → add your SMTP → **Test Connection**.
   Also set the sender address / alias domain to your own domain (so mail is not marked as spam).
   Without working mail, approval, order-confirmation and password-reset emails fail.

### A5. Staff and roles
1. Settings → Users → create a user for each person who uploads products or approves customers.
2. Approvers: **Sales → Administrator** (only Sales Managers see the *Approve wholesale* button).
   Product uploaders: **Inventory → User** and **Website → Editor** (verify exact role names).
3. Everyone: turn on two-factor (avatar → My Preferences → Account Security).
4. Staff home page: My Preferences → **Home Action** → Dashboards (per user; needs developer mode to show).

At the end of Part A a user can already log in and create ordinary products. **Wait for Part B before loading
your real catalogue** – the Brand and Low-stock fields, the wholesale pricelist and the rules only exist once
`petmart_wholesale` is installed.

---

## PART B – Push your local work online (theme + all functions)

### B1. One-time repo setup on your PC
The repo folder is `C:\Odoo\custom-addons` (already prepared: `.gitignore`, `README.md`, and this guide).
It ships only `petmart_wholesale` and `petmart_theme`.

```powershell
cd C:\Odoo\custom-addons
git status                      # check: only the 2 modules, .gitignore, README.md, this guide. NO petmart_catalog, NO CLAUDE.md
git add .gitignore README.md ODOO_SH_DEPLOY.md petmart_wholesale petmart_theme
git status                      # everything listed should be "new file"
git commit -m "PETSMART wholesale + theme"
git remote add origin <your GitHub repository URL>
git push -u origin development
```
(The local repo is already initialised on branch `development`; nothing is committed yet. The commit and push
are yours to run – they publish code.)

### B2. Test build on `development`
1. Odoo.sh → **Branches → development** → a build starts automatically on every push. Wait for it to turn green.
   If it is **red**, open the build → **Logs** tab; the last ERROR lines say what failed – send them to me.
2. In the branch **Settings → Modules installation (verify)**: choose to install a list of modules:
   `petmart_wholesale, petmart_theme`. (Their dependencies install automatically.)
   Rebuild if needed (**Rebuild** / push an empty commit).
3. Open the build → **Connect** (log in as admin). Run the **Go-live test** (section 5) here.
4. Check outgoing emails in the branch's **Mails** tab.

### B3. Staging (real data, safe rehearsal)
1. Merge `development` into `staging` (drag the branch in Odoo.sh, or `git checkout staging; git merge development; git push`).
2. Staging is a **copy of production data** – so this is where you prove the upgrade works on real records.
3. Repeat the go-live test. Only continue if everything passes.

### B4. Production
1. Merge `staging` (or `development`) into the **production** branch and push. Production keeps its database –
   only the server code updates and the server restarts.
2. In production Odoo: **Apps → Update Apps List**, remove the *Apps* filter, search **PETSMART**.
3. Install **PETSMART Wholesale (B2B)**, then **PETSMART Nigeria Theme**. Wait for each to finish.
4. What installing does automatically:
   - shop becomes **login-only** (visitors never see prices)
   - lots / expiry dates switched on
   - **Wholesale (NGN)** pricelist, **2% online discount** program, back-in-stock job created
   - the ₦ sign is placed **before** the amount
   - public categories (Dog, Cat, Bird, Fish, Small Pet, Reptiles, Dog Food, …) created
5. Open your domain – you should see the blue PETSMART homepage.

### B5. Later releases (every change, same routine)
1. Edit locally → test on your PC (port 8071 test instance) → `git commit`.
2. `git push` to `development` → green build → test.
3. Merge to `staging` → test with real data → merge to `production`.
4. In production: **Apps → PETSMART … → Upgrade** for each changed module. Odoo.sh may or may not upgrade
   modules by itself on a production push **(verify in Odoo.sh docs / the build log)** – if a new field or view is
   missing after a push, the upgrade did not run: do it manually.
5. Raise `version` in the module's `__manifest__.py` for each release (e.g. `19.0.1.0.1`).
6. Take a manual backup (Odoo.sh → Backups → *Create*) **before** each production release.

---

## PART C – Products, prices, stock and go-live

### C1. Website settings (Website app → Configuration)
- Website name: PETSMART NIGERIA · Domain: your domain
- Check **Shop** access = *Logged-in users only* (`petmart_wholesale` sets this; confirm it stuck)
- Sign-up: *Free sign up* is correct (accounts stay **pending** until approved)

### C2. Business rules (Settings → Technical → System Parameters, developer mode)
| key | default | meaning |
|---|---|---|
| `petmart.min_order_amount` | 50000 | minimum wholesale order value, ₦, before tax |
| `petmart.new_arrival_days` | 30 | days a product keeps the NEW ARRIVAL tag |

Low-stock level is set **per product** (product form → *Low-stock threshold*, default 50 units).
The 2% online discount: Website / Sales → **Discount & Loyalty programs** → *Online order discount (2%)*.

### C3. Upload products
1. Prepare a spreadsheet with columns: **Name, Sales Price (retail), Product Type = Goods, Track Inventory = yes,
   Website Categories, Brand, Published**. For food: tick **Track by Lots** and **Expiration Date**.
2. Website → Products (or Inventory → Products) → list view → **Favorites (☰) → Import records** → upload, map
   columns, **Test** first, then **Import**.
3. Photos: open each product → click the picture box top-right → upload (or import via image URL column).
4. **Never tick "Show available quantity on website"** – customers must only ever see
   AVAILABLE / LOW STOCK / OUT OF STOCK.

### C4. Wholesale prices
Sales → Configuration → Pricelists → **Wholesale (NGN)** → add a line per product
(Applied on *Product*, Computation *Fixed Price*). A product with no line sells to approved customers at the
retail price.

### C5. Opening stock
Inventory → Operations → **Physical Inventory** → set the counted quantity → **Apply**.
For lot-tracked food: enter lot number + expiry date. Set the real warehouse name/address under
Inventory → Configuration → Warehouses.

### C6. Payments (Flutterwave)
1. Invoicing/Accounting → Configuration → **Payment Providers → Flutterwave**.
2. Enter the public key, secret key and webhook secret. State = **Test** first.
3. In the Flutterwave dashboard set the webhook URL to the address shown on the provider form in Odoo
   **(verify the exact path there)**.
4. Place a small test order. When it works: **State → Enabled**.
5. Paystack is not in stock Odoo 19 – a third-party/custom module is needed later.

### C7. Customers
Contacts → filter **Wholesale: pending approval** → open → **Approve wholesale**.
That assigns the wholesale pricelist and unlocks the shop for that customer.

---

## 4. Replace the placeholder content before real customers

These are text in the theme code. Change them locally, push, release (B5):
- Footer / header phone **0700-PET-SHOP**; footer "Chat now" link
- "Free nationwide delivery on qualifying wholesale orders over ₦150,000" – text only, **not enforced**;
  configure real delivery rules in Website → Configuration → Shipping if you offer this
- "Terms · Privacy · Returns" links (`/privacy` etc.) – create those pages first
- Menu items *Other Animals, Services, Brands, Deals* currently point to the shop / contact page
- "Wholesale Bestsellers" shows the first 5 published products (not a real sales ranking)
- Social icons / About / Careers pages do not exist yet

Files: `petmart_theme/views/layout.xml` (header + footer), `petmart_theme/views/homepage.xml` (homepage).

---

## 5. Go-live test (private browser window, do every line)

1. `/` loads with the PETSMART design and **no prices** anywhere; the *Wholesale Bestsellers* cards say
   "Sign in to see price".
2. `/shop` and `/shop/cart` send you to the login page.
3. `/web/signup` asks for business name + phone. Register a test business → "application under review".
4. Staff: Contacts → approve the test business. The test business logs in → prices appear as **₦85,000.00**
   (₦ on the left) and are the wholesale price.
5. Add items **below** the minimum → checkout is blocked with a message; above it → checkout works.
6. The order shows the **2% discount** line.
7. Product tiles say AVAILABLE / LOW STOCK / OUT OF STOCK – **never a number**. Staff see exact numbers in Inventory.
8. Flutterwave test payment completes; the order confirms; the email arrives (check *Mails* tab on dev/staging).
9. Delete or archive the test customer and test orders.
10. Create a manual backup and confirm it appears in Odoo.sh → Backups.

---

## 6. Security checklist (Odoo.sh)

- [ ] Production branch **protected** on GitHub (require pull request; nobody pushes straight to it)
- [ ] Only the people who need it have access to the GitHub repo and the Odoo.sh project
- [ ] **Two-factor** on for every staff user, GitHub account and Odoo.sh account
- [ ] Strong unique passwords in a password manager; no shared admin account
- [ ] **No secrets in git** – API keys and passwords are typed into Odoo only
- [ ] No demo data and no test users left in production
- [ ] Developer mode off for day-to-day users
- [ ] Only trusted people have *Settings / Administration* rights (Users → Access Rights)
- [ ] HTTPS working on your domain (padlock), `web.base.url` set to `https://…`
- [ ] Flutterwave: live keys only on production; webhook secret set
- [ ] Odoo.sh scheduled backups visible; **manual backup before every release**; restore tested once on a staging copy
- [ ] Keep Odoo.sh on the latest 19.0 and read its release notes; always rehearse upgrades on staging

Not applicable on Odoo.sh (Odoo.sh handles them): editing `odoo.conf`, database manager / master password,
firewall and reverse proxy, server patching.

---

## 7. Backups and rollback
- Odoo.sh keeps scheduled backups for production **(verify retention in the Backups tab)** and lets you create
  manual ones and restore to a chosen branch. **Restore a backup into staging to test it – not into production.**
- If a release breaks the live site: Odoo.sh → Backups → restore the pre-release backup, and revert the
  git merge (`git revert <merge commit>` then push). Data entered after the backup time is lost, so keep releases
  small and do them outside trading hours.

---

## 8. Troubleshooting

| symptom | what to do |
|---|---|
| Build is red | Build → **Logs** tab → the last `ERROR` / `Traceback` lines. Send them to me. |
| PETSMART modules missing from Apps | Apps → **Update Apps List**, remove the *Apps* filter and search "PETSMART". Check the build was green and the module folders are at the **repo root**. |
| Homepage looks like default Odoo | The theme is not installed/upgraded: Apps → PETSMART Nigeria Theme → Install / Upgrade. |
| Homepage changes don't show after a push | Upgrade `petmart_theme`. If someone edited the homepage in the drag-and-drop editor, that copy overrides the theme: Website → Pages → Home → reset / delete that customised copy. |
| Prices show `$` or amounts after the symbol | Company currency is not NGN, or `petmart_wholesale` was not installed. Recheck A1; upgrade `petmart_wholesale`. |
| Shop visible to everyone / prices exposed | Website settings → shop access must be *Logged-in users only*; upgrade `petmart_wholesale`. |
| Approval email not received | Production: check outgoing mail server test. Dev/staging: emails are captured in the *Mails* tab, not sent. |
| Approve button missing | User needs **Sales → Administrator**. |
| New products have no Brand field | `petmart_wholesale` not installed/upgraded. |

---

## 9. Local development reminder (your PC)
- Local database `demopetmartnigeria` on http://localhost:8069 is for building and testing only. **Its data is
  never sent to production** – only the code in git is.
- Test-instance command and dev notes are in `CLAUDE.md` (kept only on your PC, git-ignored).
