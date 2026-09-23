# NIPAM — Non-Indigenes for Philip Aduda Movement

The digital home of NIPAM, the support movement for **Sen. Philip Aduda**. It is a mobile-first platform that unites supporters across the six Area Councils of the Federal Capital Territory (FCT), Nigeria, shares his record, and spreads his message.

| Part | Stack |
|---|---|
| `frontend/` | React 18 + TypeScript, Vite, Tailwind CSS, shadcn-style components (Radix UI), TanStack Query, Recharts, installable PWA |
| `backend/` | Python 3.11, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL (SQLite for quick local dev), Argon2id |

## What's included

**Public site** — landing page (hero, rotating featured records, a "Meet Sen. Philip Aduda" section, About pillars, six Area Council cards, record highlights, news, events, community, join CTA), a **Sen. Philip Aduda profile page** (`/philip-aduda`: biography, public-service timeline with sources, gallery, official channels — edited from the admin dashboard), About, **Our Record** (grid/list views, filters by Area Council, category, year, verification status, search, sort), record detail (sources, documents, images, verification panel, related records, share), Area Councils with a schematic interactive map and a tabbed page per council (Overview, Community Updates, Events, Public Information, Projects/Records, Discussions, Announcements), News with categories, Events (upcoming, past, calendar, registration, add-to-calendar), moderated Community (discussions, replies, likes, reporting), global search (Ctrl/⌘ K), Contact, Privacy Policy, Terms of Use, Community Guidelines, and a 404 page.

**Members** — 4-step registration (personal info → Area Council → email/phone OTP verification → consent), password or one-time-code login, remember me, forgot/reset password, a dashboard, a notification centre, and settings (profile, verification, notification preferences per channel, change password, delete account).

**Admin (`/admin`)** — overview stats and charts, analytics, member management (search, filter, detail, suspend/reactivate, record opt-outs, CSV export of permitted data), CMS for records (with sources, images and PDFs), news, events (publish, cancel, archive), announcements (schedule, publish, expire) and Area Council profiles, a moderation queue, the **language filter word list**, the Sen. Aduda profile editor, role assignment, the audit log, and a contact inbox.

### Roles

| Role | Access |
|---|---|
| Super Admin | Everything |
| Content Admin | Records (including verification), news, events, announcements, council pages, analytics, uploads |
| Area Council Admin | News, events, announcements and the council page, **for their assigned council only** (enforced on the server) |
| Moderator | Reports, discussions, suspending members |
| Analyst | Analytics, read-only |

### Content principles, built into the product

- Every record has a verification status: **Unverified / Pending review / Verified / Disputed**. The server refuses to mark a record *Verified* unless at least one source is attached.
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
.venv/bin/python -m app.seed --create-tables --demo   # SQLite by default
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
cd backend && .venv/bin/pytest -q                          # 47 API tests (SQLite)
NIPAM_TEST_DATABASE_URL=postgresql+psycopg://… .venv/bin/pytest -q   # same tests against PostgreSQL
cd frontend && npm run typecheck && npm run build
BASE=http://localhost:5173 npm run e2e                     # 28-step browser test of member + admin flows
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
- **SMS:** `backend/app/services/sms.py` is an abstraction. Set `NIPAM_SMS_PROVIDER=http` for a generic JSON gateway, or add a `SmsProvider` subclass for an approved Nigerian SMS provider.
- **File storage:** `NIPAM_STORAGE_BACKEND=s3` for S3-compatible object storage. It requires `boto3`.
- **Rate limiting** is per process. With several instances, back `security.RateLimiter` with Redis.
- **Scheduled announcements** are dispatched by an in-process loop every minute.

CI (`.github/workflows/ci.yml`) runs lint, the API tests on SQLite and PostgreSQL, a check that migrations match the models, and the frontend typecheck and build.

## Before launch — to be supplied by NIPAM

- **Official logo:** the current mark in `frontend/src/components/brand/Logo.tsx` and `frontend/public/brand/*.svg` is a placeholder based on the brief. Replace it, then run `npm run icons` to regenerate the favicon, PWA icons, splash screens and Open Graph image.
- **Sen. Philip Aduda's profile:** add his official photo, title, biography, timeline (with sources) and official channels under **Admin → Sen. Aduda profile**. It currently shows clearly marked placeholders.
- **Verified content:** replace the sample records, events and news, or run the seed without `--demo`.
- **Social media links** in `SiteFooter.tsx`, and contact details.
- **Legal review:** have the Privacy Policy, Terms and Guidelines (`frontend/src/pages/Legal.tsx`) reviewed against the Nigeria Data Protection Act 2023.
- **Map:** the Area Council map is schematic and labelled as such. If official GIS boundaries are adopted, replace `REGIONS` in `FctMap.tsx` and cite the source.

> The repository root also contains an empty Django scaffold (`manage.py`, `SunnyOhikhokhai/`) from the initial commit. It is not used by the platform and can be removed.
