# Content pack import

The site's factual content comes from the **NIPAM Master Content Pack v1.0** (research date 4 October 2026), kept in [`NIPAM_MASTER_CONTENT_PACK.md`](NIPAM_MASTER_CONTENT_PACK.md). `backend/app/content_pack.py` turns it into database records:

| Content | Where it appears | Count |
|---|---|---|
| Profile: name, status badges, facts, timeline, self-reported figures, portrait record | `/philip-aduda`, homepage | 1 |
| Constituency projects (all six Area Councils, plus the 2018/2019 scholarship round and the 2018 rural water projects) | `/our-record` | 32 |
| Legislative records, one per bill | `/legislation` | 13 |
| Election records: 2019, 2023, 2027 | `/elections` | 3 |
| News articles | `/news` | 12 |
| Source registry, one entry per URL | Admin → Source registry | 23 |

Run it with `python -m app.seed --content-pack` (`START-NIPAM.bat` does this automatically). Running it again adds nothing: records are matched by their web address (slug), so changes made in the admin dashboard are kept. The first run also removes the earlier sample records and the September 2026 research records, which the content pack replaces.

## Verification labels

| Label | Meaning |
|---|---|
| **Verified** | Supported directly by an official INEC, National Assembly or FCTA record |
| **Reported** | Supported by credible news reporting, not yet matched to an official document |
| **Self-reported** | Published by Senator Aduda, his official website or his party |
| **Pending verification** | Not enough evidence; not to be read as fact |
| **Disputed** | Questioned and under review |

The server refuses to mark a project, bill, election record or article **Verified** without a source.

## What was kept exactly as the pack states

- Project status uses the source's own words (for example "Reported ongoing in 2023."). Nothing is shown as completed.
- Projects are described as "Reported as a constituency project facilitated/attracted during Senator Aduda's representation", never as personally funded.
- Bills show their documented stage. Only the two National Assembly records are Verified, at *second reading* and *committee stage*. The four bills the official website calls "Passed" are shown as **Self-reported as passed**. None is shown as law.
- The two descriptions of his qualification (APC: Higher Diploma in Public Administration; INEC: Diploma in Social Work) are stored as separate facts.
- The 1,300 scholarship figure is labelled as the 2018/2019 round only.
- The figures 140+, 160+, 1,000+ and 50+ always carry the label "Self-reported figures published by Senator Aduda's official platform."

## Still to do

- **Official portrait.** The build environment could not download it from https://senatoraduda.com.ng/about/. The profile stores the image record (source, URL, usage) and shows a placeholder. Once the image has been obtained with permission, upload it under **Admin → Senator profile → Official portrait**.
- **Sources for biographical details.** The pack lists his date and place of birth, education and 2003–2022 offices without a per-item source. They are attributed to the APC candidate profile and marked Self-reported. Confirm this, or link a better source, in the profile editor.
- **2023 result.** The candidacy is verified against INEC's list. The declared result is sourced to Vanguard and marked Reported until an INEC declaration is linked.
- **Source titles.** Article titles in the registry follow each article's web address. Check them against the live pages in **Admin → Source registry**.
