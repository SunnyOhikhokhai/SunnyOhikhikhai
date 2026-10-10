# FINPLAN

**Plan Smarter. Grow Further.**

FINPLAN is a simple financial planning and modelling web application built with
Python and Django. It brings four guided financial models into one workspace:

| Model | What it answers |
|-------|-----------------|
| **Business** | Revenue, costs, gross/operating/net profit, margins, break-even sales and a 12-month forecast |
| **Startup** | Launch costs, monthly cash forecast, cash burn, cash runway, break-even month and extra funding needed |
| **Real estate** | Acquisition/development/total cost, sales and rental income, profit, ROI, break-even price, yields, land subdivision and a cash-flow timeline |
| **Investment** | Capital invested, income, expenses, net profit, simple ROI, annualised return, NPV, IRR and payback |

Every model has conservative / expected / optimistic scenarios, saved projects
(open, edit, recalculate, duplicate, delete), charts, a printable report and a
PDF download.

> This folder is self-contained. The rest of the repository (the NIPAM
> platform) is a separate project and is not affected by FINPLAN.

---

## 1. Set up on Windows (VS Code + PowerShell)

Requirements: **Python 3.11 or newer** (3.12/3.13 recommended) from python.org.
During installation, tick "Add python.exe to PATH".

Open the repository in VS Code, then open a terminal (**Terminal → New Terminal**,
which is PowerShell by default) and run:

```powershell
# 1. Go into the FINPLAN folder
cd finplan

# 2. Create an isolated Python environment for this project
python -m venv .venv

# 3. Activate it (your prompt will start with "(.venv)")
.\.venv\Scripts\Activate.ps1
#   If PowerShell refuses with "running scripts is disabled", run this once and try again:
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 4. Install the dependencies listed in requirements.txt
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Create your local settings file (development mode)
Copy-Item .env.example .env

# 6. Create the database tables (SQLite file db.sqlite3)
python manage.py migrate

# 7. (Optional) Create an admin account for /admin/
python manage.py createsuperuser

# 8. Start the development server
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser, click **Start Planning** and
create an account. Stop the server with **Ctrl + C**.

In VS Code, pick the interpreter with **Ctrl + Shift + P → "Python: Select
Interpreter" → .venv** so the editor understands the project.

macOS/Linux: identical, except activate with `source .venv/bin/activate` and
copy with `cp .env.example .env`.

## 2. Run the automated tests

```powershell
python manage.py test tests
```

There are 97 tests. They cover every calculation against hand-checked
examples (for example, NPV at 10% of −1,000 then 500 a year for three years is
243.43, and IRR is 23.38%). They also cover form validation, zero and missing
values, saving drafts, editing and recalculating, duplicating, deleting, PDF
generation, CSRF protection, and checks that one user can never open another
user's project.

## 3. How to verify it works (manual checklist)

1. Open the landing page and click **Start Planning**, then create an account.
2. The dashboard shows "Your financial workspace starts here." No figures are invented.
3. Click **Create New Financial Model**, then **Business**. Step through the form
   with **Continue**. Add a custom expense row under "More expense categories".
4. Click **Calculate and save**. You see key results, charts, scenarios and assumptions.
5. Click **Edit and recalculate**, change monthly sales and save. The results update.
6. Click **Duplicate**, then **Delete** on the copy. Deletion asks you to confirm first.
7. Click **Download PDF** and **Print view**.
8. Start a Startup model, fill in one step and click **Save draft**. It appears
   under "Continue where you left off" on the dashboard.
9. Make the browser narrow, or use a phone. The menu collapses behind the ☰ button.

## 4. Project structure

```
finplan/
├── manage.py
├── requirements.txt
├── .env.example            # copy to .env – never commit .env
├── config/                 # settings, URLs, WSGI
├── accounts/               # sign up / sign in / sign out (Django auth)
├── dashboard/              # landing page and dashboard
├── projects/               # Project model + list/detail/duplicate/delete
├── financial_models/
│   ├── registry.py         # the list of the four models
│   ├── views.py            # guided workspace (new, edit, draft, calculate)
│   ├── common/             # shared engine
│   │   ├── money.py        #   Decimal helpers, safe division, currency formatting
│   │   ├── finance.py      #   NPV, IRR, annuity (loan) payment, CAGR
│   │   ├── inputs.py       #   reading saved inputs (never inventing zeros)
│   │   ├── scenarios.py    #   scenario adjustments
│   │   ├── forms.py        #   form base class, steps, custom line items
│   │   ├── report.py       #   Report structure shared by page, print and PDF
│   │   └── charts.py       #   server-side SVG charts (no JS library/CDN)
│   ├── business/           # calculations.py, forms.py, report.py
│   ├── startup/
│   ├── real_estate/
│   └── investment/
├── reports/                # printable page + ReportLab PDF
├── templates/              # Django templates
├── static/
│   ├── css/finplan.css     # the design system (brand colours as variables)
│   ├── js/finplan.js       # small vanilla-JS enhancements
│   └── images/             # logo files (see images/README.md)
└── tests/                  # automated tests
```

Each model follows the same three-file pattern:

* **`calculations.py`**: pure Python with `Decimal`. It holds an inputs
  dataclass, a `calculate()` function and the documented formulas at the top
  of the file. It does no HTML and no database access, so it is easy to test.
* **`forms.py`**: the guided form, with fields, steps, validation rules and
  the scenario lever.
* **`report.py`**: turns results into headline cards, sections, charts,
  tables, assumptions, explanations and limitations.

## 5. Important design decisions

* **Inputs are saved and results are recalculated.** A project stores only
  the user's inputs as JSON, with numbers kept as text so no precision is lost.
  Results are recalculated each time they are viewed, so they are always
  reproducible and always match the current calculation logic.
* **Money uses `Decimal`.** It is never `float`, and rounding happens only
  when a figure is displayed.
* **Divisions cannot crash.** `safe_divide` returns "not available" instead of
  failing. The page then explains why, for example "Enter revenue above zero
  to estimate break-even sales".
* **Missing required values are never treated as zero.** Optional cost lines
  left blank are listed in the report's assumptions as "not included".
* **Startup runway uses the month-by-month cash forecast.** It is not a
  single "cash ÷ burn" division, so growth and loan repayments are respected.
* **Investment returns are kept separate.** Simple ROI, annualised return and
  IRR are shown separately with explanations. Annualised return is hidden when
  money is added over time, because IRR is the right measure then.
* **Currencies are never converted.** Each project has one currency: NGN
  (the default), USD or GBP. No exchange rates are invented.
* **Ownership is enforced on every query.** Every project lookup filters by
  the signed-in owner, so changing an ID in the URL returns "not found".
* **Charts are drawn on the server as SVG.** They come from the real
  calculated data, need no JavaScript library or CDN, and print correctly.
* **The app works without JavaScript.** JavaScript only adds the step-by-step
  navigation, adding rows, the live currency symbol and the mobile menu.

## 6. Logo

The approved FINPLAN logo was not available when this version was built. The
files in `static/images/` are **clearly labelled placeholders**. Replace
`finplan-logo.png` (full logo) and `finplan-icon.png` (square icon) with the
approved artwork, keeping the same file names. See `static/images/README.md`.

## 7. Production notes

* Set `FINPLAN_DEBUG=False` and a long random `FINPLAN_SECRET_KEY`.
* Set `FINPLAN_ALLOWED_HOSTS` and `FINPLAN_CSRF_TRUSTED_ORIGINS`.
* Behind HTTPS, set `FINPLAN_SECURE_COOKIES=True` and `FINPLAN_SSL_REDIRECT=True`.
* For PostgreSQL, run `pip install "psycopg[binary]"` and set the `FINPLAN_DB_*` variables.
* Run `python manage.py collectstatic`. WhiteNoise then serves CSS, JS and images.
* Run with a WSGI server such as `waitress` on Windows or `gunicorn` on Linux, using `config.wsgi:application`.

## 8. Known limitations (version 1)

* Business figures are typical monthly amounts. Seasonality, loan interest and
  depreciation are not modelled.
* The startup model assumes customers pay in the month of sale. It has no tax,
  VAT or inflation.
* Real estate timing is simplified: costs and income are spread evenly. It is
  a feasibility estimate, not a valuation.
* Investment cash flows are yearly. Tax on the exit gain is not included.
* There is no password-reset email yet, because no email service is configured.
  An admin can reset passwords in `/admin/`.
* All results are estimates based on user assumptions, not financial advice.
