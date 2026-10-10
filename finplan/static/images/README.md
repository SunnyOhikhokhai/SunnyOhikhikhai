# FINPLAN logo files

**The two PNG files in this folder are placeholders.** The approved FINPLAN logo
was not available when this version was built, so clearly labelled stand-ins
are used instead. Nothing here is the real brand mark.

Replace them with the approved artwork, keeping the same file names:

| File | Used for | Recommended format |
|------|----------|--------------------|
| `finplan-logo.png` | Full logo: public header, sign-in page, sidebar, printable report, PDF report | PNG with a transparent background, wide (about 4:1), at least 800 px wide |
| `finplan-icon.png` | Compact mark: mobile top bar and browser tab icon | Square PNG, at least 256 × 256 px, a clean crop of the approved logo |

The templates size images by height only, so the logo keeps its proportions
whatever its exact dimensions are. The PDF report also scales it to fit
without distortion.

After replacing the files, restart the development server. In production,
run `python manage.py collectstatic` again.
