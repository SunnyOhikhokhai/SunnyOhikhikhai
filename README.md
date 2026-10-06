# NIMPA — Non-Indigenous Movement for Philip Aduda

> **Quick start on Windows (no commands needed)**
> 1. Install [Python](https://www.python.org/downloads/) (tick **"Add python.exe to PATH"**) and [Node.js LTS](https://nodejs.org).
> 2. Download the project ZIP, extract it to your Desktop, and rename the folder to `NIMPA`.
> 3. Double-click **`START-NIPAM.bat`** in that folder. It sets everything up and opens the site at http://localhost:5173.
> 4. To edit in VS Code: **File → Open Folder → Desktop → NIMPA**.
> 5. **Updates:** if the folder is linked to GitHub (a `.git` folder exists), `START-NIPAM.bat` downloads the latest version each time it starts. To link a folder that came from a ZIP, run these once in the folder: `git init`, `git remote add origin https://github.com/SunnyOhikhokhai/SunnyOhikhikhai.git`, `git fetch origin`, `git reset --hard origin/main`, `git branch -M main`, `git branch -u origin/main`. Your database and installed packages are kept.

The digital home of NIMPA, the support movement for **Sen. Philip Aduda**. It is a mobile-first platform that unites supporters across the six Area Councils of the Federal Capital Territory (FCT), Nigeria, shares his record, and spreads his message.

| Part | Stack |
|---|---|
| `frontend/` | React 18 + TypeScript, Vite, Tailwind CSS, shadcn-style components (Radix UI), TanStack Query, Recharts, installable PWA |
| `backend/` | Python 3.11, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL (SQLite for quick local dev), Argon2id |

## What's included

**Public site** — landing page (hero, rotating featured records, six featured sections, the Senator profile with self-reported figures, About pillars, six Area Council cards, record highlights, news, events, community, join CTA), a **Senator profile page** (`/philip-aduda`: status badges, sourced facts, 2027 election card, self-reported figures, biography, political timeline with a source and verification label on every item, gallery, official links), About, **Our Record** with three parts — **constituency projects** (filters by Area Council, category, project status and verification), **legislation** (`/legislation`, one record per bill, filters by category, year, legislative stage and verification) and **elections** (`/elections`, 2019, 2023 and the INEC-verified 2027 candidacy) — with detail pages that show Source, Verification and Last updated, Area Councils with a schematic interactive map and a tabbed page per council (Overview, Community Updates, Events, Public Information, Projects/Records, Discussions, Announcements), News with category, date and Area Council filters, a verification label and linked sources, Events (upcoming, past, calendar, registration, add-to-calendar), moderated Community (discussions, replies, likes, reporting), global search (Ctrl/⌘ K), Contact, Privacy Policy, Terms of Use, Community Guidelines, and a 404 page.

**Members** — 4-step registration (personal info → Area Council → email/phone OTP verification → consent), password or one-time-code login, remember me, forgot/reset password, a dashboard, a notification centre, and settings (profile, verification, notification preferences per channel, change password, delete account).

**Admin (`/admin`)** — overview stats and charts, analytics, member management (search, filter, detail, suspend/reactivate, record opt-outs, CSV export of permitted data), CMS for projects (with sources, images, PDFs, project status, reported cost and length), legislation, elections, a **source registry** (each URL stored once and reused), news (with verification and sources), events (publish, cancel, archive), announcements (schedule, publish, expire) and Area Council profiles, a moderation queue, the **language filter word list**, the Senator profile editor (badges, facts, figures, portrait record, timeline), role assignment, the audit log, and a contact inbox.

### Roles

| Role | Access |
|---|---|
| Super Admin | Everything |
| Content Admin | Records (including verification), news, events, announcements, council pages, analytics, uploads |
| Area Council Admin | News, events, announcements and the council page, **for their assigned council only** (enforced on the server) |
| Moderator | Reports, discussions, suspending members |
| Analyst | Analytics, read-only |

### Content principles, built into the product

- Every record has a verification status: **Verified** (official INEC, National Assembly or FCTA record), **Reported** (credible news), **Self-reported** (published by Senator Aduda or his party), **Pending verification** or **Disputed**. The server refuses to mark anything *Verified* without a source.
- Project status and legislative stage keep the source's own wording: "ongoing" is never upgraded to "completed", and a bill is never shown as law without an official enactment record.
- Content comes from the NIMPA Master Content Pack; see [`docs/content-pack.md`](docs/content-pack.md).
- News carries a content label: *Verified information*, *Announcement*, *Opinion*, *Historical record* or *Update*. *Verified information* requires a source note.
- Community posts are labelled as user-generated content.
- Demo content is flagged `is_demo` and shows a **Sample** badge. It contains placeholders such as **[VERIFIED PROJECT INFORMATION TO BE ADDED]**. No projects, figures, dates or achievements have been invented.
- An Area Council is self-declared and is stated everywhere **not** to indicate electoral eligibility or polling location. Nothing collects or infers ethnicity, religion, indigene status or political views.

### Language filter (hate speech and insults)

Every discussion, comment, registration name and public profile field is checked before it's saved (`backend/app/services/moderation.py`):

- **Block** terms (profanity, insults including Pidgin/local ones, hateful "go back to your village"-type phrases, threats) reject the post with a polite message.
- **Review** terms (borderline wording) publish the post hidden and put it in the moderation queue, where a moderator can **Approve & publish** or remove it.
- Disguised spellings are caught: capitals, leetspeak (`1d10t`), repeated letters (`iiidiot`), spaced or dotted letters (`f.u.c.k`, `s t u p i d`) and masked letters (`st*pid`). Whole-word matching avoids false positives such as "Scunthorpe".
- Five blocked attempts in 24 hours pause that member's posting for a day. Every blocked attempt is audit-logged.
- Moderators manage the list under **Admin → Moderation → Language filter**. Add local-language insults and tribal slurs there; no redeploy is needed.

### Security

Argon2id password hashing; server-side sessions in HTTP-only `SameSite=Lax` cookies (revocable, so logout, password change and suspension take effect immediately); bearer tokens for API clients (`POST /api/auth/token`); CSRF double-submit tokens; per-IP rate limits; account lockout after repeated failed logins; one-time codes stored as keyed hashes that expire and are single-use; responses that don't reveal whether an account exists; RBAC checked on every admin route; audit logging; uploads checked by magic bytes, size-limited and randomly renamed; Markdown rendered with raw HTML disabled (XSS); SQLAlchemy parameterised queries; security headers and a CSP; production start-up refuses weak secrets, insecure cookies or exposed OTPs. Member email addresses and phone numbers never appear in public API responses (tested).

## Running locally

```bash
# API
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m app.seed --create-tables --demo --content-pack   # SQLite by default; runs the migrations
.venv/bin/uvicorn app.main:app --reload --port 8000     # API docs: http://localhost:8000/api/docs

# Web (in another terminal)
cd frontend
npm install
npm run dev                                             # http://localhost:5173
```

Demo accounts (development seed only):

- Super admin: `admin@nipam.local` / `ChangeMe!Admin2026`
- Member: `member@nipam.local` / `Member!Demo2026`

With no email provider configured, codes are logged to the console. With `NIPAM_DEV_EXPOSE_OTP=true` (the development default), they are also shown in the UI in an amber "Development mode" box. Set `NIPAM_SMS_PROVIDER=console` to test phone verification.

To use PostgreSQL locally, set `NIPAM_DATABASE_URL=postgresql+psycopg://user:pass@localhost/nipam` and run `alembic upgrade head && python -m app.seed --demo`.

## Tests

```bash
cd backend && .venv/bin/pytest -q                          # 54 API tests (SQLite)
NIPAM_TEST_DATABASE_URL=postgresql+psycopg://… .venv/bin/pytest -q   # same tests against PostgreSQL
cd frontend && npm run typecheck && npm run build
BASE=http://localhost:5173 npm run e2e                     # 31-step browser test of member + admin flows
```

The end-to-end script covers registration → verification → consent → dashboard → logout/login → Area Council → records → news → event registration → calendar → community post/comment/like → notifications → settings → search → reporting, then admin login → members → record CMS with sources → news → events → moderation → analytics → audit log. It saves screenshots to `frontend/e2e-screens/`.

## Deployment

```bash
cp .env.example .env    # set real secrets, SMTP and admin credentials
docker compose up -d --build
```

This starts PostgreSQL, the API (runs migrations and seeds reference data on start) and nginx serving the SPA on port 8080, with `/api`, `/uploads` and `/sitemap.xml` proxied to the API. Put TLS in front of it (a load balancer, Caddy or Traefik). The API container is reachable only through nginx.

Production notes:
- **Email:** `NIPAM_EMAIL_PROVIDER=smtp` works with any SMTP transactional provider.
- **WhatsApp:** members can opt in to WhatsApp messages for announcements and events (off by default; needs a verified phone number). To switch it on, create a WhatsApp Business account in Meta Business Manager, get an approved message template (default name `nipam_update`) whose body has one `{{1}}` variable, for example "NIMPA update: {{1}}", then set `NIPAM_WHATSAPP_PROVIDER=cloud`, `NIPAM_WHATSAPP_TOKEN` and `NIPAM_WHATSAPP_PHONE_NUMBER_ID`. Use `NIPAM_WHATSAPP_PROVIDER=console` to test without sending.
- **SMS:** `backend/app/services/sms.py` is an abstraction. Set `NIPAM_SMS_PROVIDER=http` for a generic JSON gateway, or add a `SmsProvider` subclass for an approved Nigerian SMS provider.
- **File storage:** `NIPAM_STORAGE_BACKEND=s3` for S3-compatible object storage. It requires `boto3`.
- **Rate limiting** is per process. With several instances, back `security.RateLimiter` with Redis.
- **Scheduled announcements** are dispatched by an in-process loop every minute.

CI (`.github/workflows/ci.yml`) runs lint, the API tests on SQLite and PostgreSQL, a check that migrations match the models, and the frontend typecheck and build.

## Before launch — to be supplied by NIMPA

- **Logo:** the official NIMPA logo is in `frontend/brand-source/`. To replace it, save the new artwork there, run `node scripts/prepare-logo.mjs <file>` (it makes the transparent `public/brand/nimpa-logo.png` and the emblem `nimpa-mark.png`; adjust `EMBLEM` in the script if the layout differs), then `npm run icons` to rebuild the favicon, app icons, splash screens and share image.
- **Official portrait:** upload it under **Admin → Senator profile** once obtained with permission from his official website (see [`docs/content-pack.md`](docs/content-pack.md) for the other open items).
- **Sample events and discussions:** the content pack replaces the sample records and news; sample events and discussions remain until real ones are added (or run the seed without `--demo`).
- **Social media links** in `SiteFooter.tsx`, and contact details.
- **Legal review:** have the Privacy Policy, Terms and Guidelines (`frontend/src/pages/Legal.tsx`) reviewed against the Nigeria Data Protection Act 2023.
- **Map:** the Area Council map is schematic and labelled as such. If official GIS boundaries are adopted, replace `REGIONS` in `FctMap.tsx` and cite the source.

> The repository root also contains an empty Django scaffold (`manage.py`, `SunnyOhikhokhai/`) from the initial commit. It is not used by the platform and can be removed.
