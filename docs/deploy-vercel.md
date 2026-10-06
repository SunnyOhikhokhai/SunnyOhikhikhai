# Putting NIMPA online with Vercel

The project is ready for Vercel: the website is built from `frontend/`, and the backend runs as a Python function (`api/index.py`). On the first visit the site creates its database tables and imports the content pack by itself. The sample content and the demo accounts are not created.

You need a free [Vercel](https://vercel.com) account; sign up **with GitHub**. It takes about 15 minutes.

## 1. Import the project

1. In Vercel, click **Add New… → Project**.
2. Find **SunnyOhikhikhai** in the list of GitHub repositories and click **Import**. If it isn't listed, click **Adjust GitHub App Permissions** and allow access to it.
3. Leave **Root Directory** as it is (the repository root). The build settings come from `vercel.json`.
4. Open **Environment Variables** and add:

   | Name | Value |
   |---|---|
   | `NIPAM_SECRET_KEY` | A long random value, at least 32 characters, that you keep secret. |
   | `NIPAM_SEED_ADMIN_EMAIL` | Your email address. It becomes the Super Admin account. |
   | `NIPAM_SEED_ADMIN_PASSWORD` | A strong password for that account. |
   | `NIPAM_ENV` | `staging` |

   With `staging`, one-time codes for registration and login are shown on screen, because email and SMS aren't connected yet. Switch it to `production` once an email provider is set up (see below).
5. Click **Deploy**. The first build takes 2–3 minutes. It finishes, but the site can't work yet: it still needs a database and file storage.

## 2. Add the database (Neon Postgres)

1. Open the project in Vercel, then **Storage → Create Database → Neon** (Postgres).
2. Choose the region **Frankfurt (eu-central-1)**. It's closest to Nigeria and to the site's servers, which are set to Frankfurt.
3. Connect it to the project for **all environments**. Vercel adds `DATABASE_URL` automatically.

## 3. Add file storage (Vercel Blob)

1. **Storage → Create → Blob**, then connect it to the project. Vercel adds `BLOB_READ_WRITE_TOKEN` automatically.
2. Photos uploaded in the admin dashboard (portrait, gallery, project images) are stored here.

## 4. Redeploy and open the site

1. **Deployments →** the latest deployment **→ ⋯ → Redeploy**.
2. Open the address Vercel shows, for example `https://sunnyohikhikhai.vercel.app`. The first page load takes a few seconds while the site sets up its database.
3. Log in with `NIPAM_SEED_ADMIN_EMAIL` and `NIPAM_SEED_ADMIN_PASSWORD`. You're Super Admin.
4. In the admin dashboard, upload the portrait and gallery photos again under **Senator profile**. Photos on your own PC aren't copied to the live site.

Every time a pull request is merged into `main`, Vercel publishes the new version automatically.

## Changing the address

**Settings → Domains** lets you rename the `.vercel.app` address (for example `nimpa.vercel.app` if it's free) or connect your own domain such as `nimpa.ng`.

## Later, before a public launch

- **Email:** set `NIPAM_EMAIL_PROVIDER=smtp` and the `NIPAM_SMTP_*` variables (see `backend/.env.example`), then change `NIPAM_ENV` to `production` and add `NIPAM_DEV_EXPOSE_OTP=false`.
- **SMS / WhatsApp:** see the README.
- **Plan:** Vercel's free Hobby plan is meant for personal, non-commercial projects. For a long-running organisation site, consider the Pro plan.

## If something goes wrong

- **The site shows "Something went wrong" or the API returns errors:** in Vercel, open **Deployments → the deployment → Logs**. A message such as *Set NIPAM_SECRET_KEY…* or *Set NIPAM_SEED_ADMIN_EMAIL…* names the missing setting. Add it under **Settings → Environment Variables**, then redeploy.
- **Uploads fail with "File storage is not configured":** connect the Blob store (step 3) and redeploy.
