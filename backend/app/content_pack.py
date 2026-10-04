"""NIPAM Master Content Pack v1.0 (research date 4 October 2026).

Imports the controlled content pack as structured CMS data: the profile of
Senator Philip Tanimu Aduda, his political timeline, legislative records,
constituency project records, election records, seed news articles and a
reusable source registry.

Editorial rules applied here (from the content pack):
- nothing is invented: every value below is taken from the pack;
- verification is never upgraded: Verified only where the pack says so
  (INEC, National Assembly, FCTA records), otherwise Reported or Self-reported;
- "ongoing" stays "ongoing" and a bill is never shown as law without an
  official enactment record;
- projects are "reported as constituency projects facilitated/attracted during
  Senator Aduda's representation", never "personally funded".

The import is idempotent. Records that already exist (matched by slug) are
left alone so administrators' edits are kept.

    python -m app.seed --content-pack
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    AreaCouncil,
    ContentSource,
    ElectionRecord,
    LegislativeRecord,
    News,
    NewsCategory,
    PrincipalProfile,
    Project,
    ProjectCategory,
    ProjectSource,
    Source,
    utcnow,
)
from .utils import slugify

RESEARCH_DATE = date(2026, 10, 4)
FACILITATED = "Reported as a constituency project facilitated/attracted during Senator Aduda's representation."
PENDING_INFO = "Information pending verification."

# ---------------------------------------------------------------------------
# Source registry (one entry per URL)
# ---------------------------------------------------------------------------

SOURCES: dict[str, dict] = {
    "inec_2027": {
        "name": "Independent National Electoral Commission (INEC)",
        "title": "2027 Senate final list of candidates",
        "source_type": "inec",
        "reliability_level": "official",
        "url": "https://www.inecnigeria.org/documents/press/2027%20SENATE%20FINAL%20LIST%20OF%20CANDIDATES.pdf",
        "notes": "Lists FCT / Federal Capital Territory / Tanimu Philip Aduda / APC. Records his qualification as \"Diploma in Social Work\".",
    },
    "inec_calendar": {
        "name": "Independent National Electoral Commission (INEC)",
        "title": "Election calendar",
        "source_type": "inec",
        "reliability_level": "official",
        "url": "https://inecnigeria.org/elections/calendar",
        "notes": "National Assembly election scheduled for 16 January 2027.",
    },
    "inec_2019": {
        "name": "Independent National Electoral Commission (INEC)",
        "title": "2019 General Elections: updated list of elected candidates to the Senate",
        "source_type": "inec",
        "reliability_level": "official",
        "url": "https://www.inecnigeria.org/wp-content/uploads/2019/05/2019-GENERAL-ELECTIONS-UPDATED-LIST-OF-ELECTED-CANDIDATES-TO-THE-SENATE_may28.pdf",
        "notes": "Confirms Tanimu Philip Aduda (PDP) as the elected FCT senator in 2019.",
    },
    "inec_2023": {
        "name": "Independent National Electoral Commission (INEC)",
        "title": "Final list of candidates for national elections (2023)",
        "source_type": "inec",
        "reliability_level": "official",
        "url": "https://wp1.inecnigeria.org/wp-content/uploads/2022/09/Final-List-of-Candidates-for-National-Elections-1.pdf",
        "notes": "Records Tanimu Philip Aduda as the PDP candidate for the FCT Senate election in 2023.",
    },
    "nass_157": {
        "name": "National Assembly of Nigeria",
        "title": "FCT Area Councils Administrative & Political Structure Bill: second reading",
        "source_type": "national_assembly",
        "reliability_level": "official",
        "url": "https://www.nass.gov.ng/news/item/157",
        "notes": "Documents the bill's second reading (2015).",
    },
    "nass_589": {
        "name": "National Assembly of Nigeria",
        "title": "FCT University of Science & Technology, Abaji Bill (S.B. 59)",
        "source_type": "national_assembly",
        "reliability_level": "official",
        "url": "https://www.nass.gov.ng/news/item/589",
        "notes": "Records the bill as referred to the Senate Committee on Tertiary Education and TETFUND for report (2017).",
    },
    "nass_home": {
        "name": "National Assembly of Nigeria",
        "title": "National Assembly of the Federal Republic of Nigeria",
        "source_type": "national_assembly",
        "reliability_level": "official",
        "url": "https://www.nass.gov.ng/",
    },
    "constitution": {
        "name": "Constitution of the Federal Republic of Nigeria, 1999 (as amended)",
        "title": "Sections 48 and 299",
        "source_type": "legal",
        "reliability_level": "official",
        "url": None,
        "notes": "Section 48: the Senate consists of three senators from each state and one from the FCT. "
        "Section 299: the National Assembly exercises legislative powers for the FCT.",
    },
    "fcta_survey": {
        "name": "Federal Capital Territory Administration (FCTA)",
        "title": "Survey and Mapping",
        "source_type": "fcta",
        "reliability_level": "official",
        "url": "https://www.fcta.gov.ng/ova_dep/survey-and-mapping/",
        "notes": "Source for the six FCT Area Councils.",
    },
    "fcta_home": {
        "name": "Federal Capital Territory Administration (FCTA)",
        "title": "FCTA official website",
        "source_type": "fcta",
        "reliability_level": "official",
        "url": "https://www.fcta.gov.ng/",
    },
    "official_home": {
        "name": "Senator Philip Aduda Official Website",
        "title": "Home page",
        "source_type": "official_site",
        "reliability_level": "self",
        "url": "https://senatoraduda.com.ng/",
        "notes": "Self-reported figures: 140+ Infrastructural Development, 160+ Community Engagement, "
        "1,000+ Constituency Projects, 50+ Policy Advocacy.",
    },
    "official_about": {
        "name": "Senator Philip Aduda Official Website",
        "title": "About",
        "source_type": "official_site",
        "reliability_level": "self",
        "url": "https://senatoraduda.com.ng/about/",
        "notes": "Official portrait; MFR (2010) and CON; bills listed with the site's own status wording.",
    },
    "apc_profile": {
        "name": "All Progressives Congress (APC)",
        "title": "Candidate profile: Tanimu Philip Aduda (Sen.)",
        "source_type": "party",
        "reliability_level": "party",
        "url": "https://www.vote.apc.com.ng/tanimu-philip-aduda-sen",
        "notes": "Official APC candidate biography. Records a Higher Diploma in Public Administration and his 1996 election as councillor for Karu Ward.",
    },
    "gazette": {
        "name": "Gazette Nigeria",
        "title": "Defeated FCT senator Aduda unveils N2.8 billion constituency projects to knock off criticisms",
        "source_type": "news",
        "reliability_level": "news",
        "url": "https://gazettengr.com/defeated-fct-senator-aduda-unveils-n2-8-billion-constituency-projects-to-knock-off-criticisms/",
    },
    "vanguard_mar23": {
        "name": "Vanguard",
        "title": "I'm dragging INEC, Kingibe, others to court over FCT senatorial election — Aduda",
        "source_type": "news",
        "reliability_level": "news",
        "url": "https://www.vanguardngr.com/2023/03/im-dragging-inec-kingibe-others-to-court-over-fct-senatorial-election-aduda/",
    },
    "vanguard_apr23": {
        "name": "Vanguard",
        "title": "Kuje Area Council: improvisation in Kuje as school management converts health centre to classrooms",
        "source_type": "news",
        "reliability_level": "news",
        "url": "https://www.vanguardngr.com/2023/04/kuje-area-council-improvisation-in-kuje-as-school-management-converts-health-centre-to-classrooms/",
    },
    "tribune": {
        "name": "Nigerian Tribune",
        "title": "Senate President lauds Aduda's constituency projects in FCT",
        "source_type": "news",
        "reliability_level": "news",
        "url": "https://tribuneonlineng.com/senate-president-lauds-adudas-constituency-projects-in-fct/",
    },
    "peoples_gss": {
        "name": "Peoples Daily",
        "title": "Constituency project: Aduda to build classrooms in GSS Gwagwalada",
        "source_type": "news",
        "reliability_level": "news",
        "url": "https://peoplesdaily.ng/constituency-project-aduda-to-build-classrooms-in-gss-gwagwalada/",
    },
    "peoples_water": {
        "name": "Peoples Daily",
        "title": "Aduda commissions water projects, promises better deal",
        "source_type": "news",
        "reliability_level": "news",
        "url": "https://peoplesdaily.ng/aduda-commissions-water-projects-promises-better-deal/",
    },
    "dailytrust_scholarship": {
        "name": "Daily Trust",
        "title": "Aduda disburses N80m scholarships to students",
        "source_type": "news",
        "reliability_level": "news",
        "url": "https://dailytrust.com/aduda-disburses-n80m-scholarships-to-students/",
    },
    "thisday_2019": {
        "name": "ThisDay",
        "title": "PDP's Aduda emerges winner of FCT senatorial election",
        "source_type": "news",
        "reliability_level": "news",
        "url": "https://www.thisdaylive.com/2019/02/25/pdps-aduda-emerges-winner-of-fct-senatorial-election/",
        "publication_date": "2019-02-25",
        "notes": "Reported vote total: 263,055.",
    },
    "premium_times": {
        "name": "Premium Times",
        "title": "Ex-FCT senator dumps PDP for APC",
        "source_type": "news",
        "reliability_level": "news",
        "url": "https://www.premiumtimesng.com/regional/north-central/864842-ex-fct-senator-dumps-pdp-for-apc.html",
        "notes": "Reports his resignation from the PDP (17 March 2026), citing persistent party crises, and move to the APC.",
    },
    "blueprint": {
        "name": "Blueprint",
        "title": "2027: FCT — the odds increasingly favour Aduda",
        "source_type": "news",
        "reliability_level": "news",
        "url": "https://blueprint.ng/2027-fct-the-odds-increasingly-favour-aduda/",
        "notes": "Cited only for bill numbers SB 58, SB 175 and SB 419.",
    },
}


def upsert_source(db: Session, data: dict) -> Source:
    """Find a registry entry by URL (or by name when there is no URL), creating it if needed."""
    url = data.get("url")
    stmt = select(Source).where(Source.url == url) if url else select(Source).where(Source.url.is_(None), Source.name == data["name"])
    s = db.scalar(stmt)
    if s:
        return s
    s = Source(
        name=data["name"],
        title=data.get("title"),
        source_type=data.get("source_type", "news"),
        reliability_level=data.get("reliability_level", "news"),
        url=url,
        notes=data.get("notes"),
        accessed_date=RESEARCH_DATE,
    )
    if data.get("publication_date"):
        s.publication_date = date.fromisoformat(data["publication_date"])
    db.add(s)
    db.flush()
    return s


def link_sources(db: Session, content_type: str, content_id: int, refs: list) -> None:
    for i, ref in enumerate(refs):
        key, note = (ref, None) if isinstance(ref, str) else ref
        src = upsert_source(db, SOURCES[key])
        exists = db.scalar(
            select(ContentSource.id).where(
                ContentSource.content_type == content_type,
                ContentSource.content_id == content_id,
                ContentSource.source_id == src.id,
            )
        )
        if not exists:
            db.add(ContentSource(content_type=content_type, content_id=content_id, source_id=src.id, note=note, sort_order=i))


# ---------------------------------------------------------------------------
# Constituency projects (section 7–9 of the pack)
# ---------------------------------------------------------------------------

ONGOING_2023 = "Reported ongoing in 2023."


def _p(code, title, council, category, label, location, status, note, source, **extra):
    return {
        "code": code,
        "title": title,
        "council": council,
        "category": category,
        "category_label": label,
        "location": location,
        "project_status": status,
        "status_note": note,
        "sources": [source] if isinstance(source, str) else source,
        **extra,
    }


PROJECTS: list[dict] = [
    # AMAC
    _p("AMAC-01", "Nyanya road / Nyanya-Hospital road network", "amac", "roads", "Roads / Drainage", "Nyanya, AMAC",
       "reported", "Reported project; exact completion status requires current verification.", "gazette",
       reported_cost="approximately ₦1.4 billion",
       description="Network of roads including drainage/culvert works around Nyanya.", featured=True),
    _p("AMAC-02", "VIO–Police Station–Hospital Road", "amac", "roads", "Roads", "Nyanya, AMAC", "ongoing", ONGOING_2023, "vanguard_mar23"),
    _p("AMAC-03", "Agwan Dadi Road", "amac", "roads", "Roads", "Nyanya, AMAC", "ongoing", ONGOING_2023, "vanguard_mar23"),
    _p("AMAC-04", "Gbagalape Road", "amac", "roads", "Roads", "Nyanya, AMAC", "ongoing", ONGOING_2023, "vanguard_mar23"),
    _p("AMAC-05", "Kurudu Road", "amac", "roads", "Roads", "AMAC", "ongoing", ONGOING_2023, "vanguard_mar23"),
    _p("AMAC-06", "Jikwoyi Road", "amac", "roads", "Roads", "AMAC", "ongoing", ONGOING_2023, "vanguard_mar23"),
    _p("AMAC-07", "Youth & Sports Centre, Jikwoyi", "amac", "sports", "Sports / Youth", "Jikwoyi, AMAC", "ongoing", ONGOING_2023, "vanguard_mar23"),
    _p("AMAC-08", "Karu Town Hall", "amac", "infrastructure", "Community Infrastructure", "Karu, AMAC", "commissioned",
       "Reported project; later reporting describes it among commissioned projects.", "tribune"),
    _p("AMAC-09", "Nyanya Mini Stadium / Sports Centre", "amac", "sports", "Sports", "Nyanya, AMAC", "commissioned",
       "Reported/commissioned project.", "tribune"),
    # Bwari
    _p("BWARI-01", "Global Suite Road, Sabon Gari", "bwari", "roads", "Roads", "Sabon Gari, Bwari", "reported",
       "Reported project; verify present condition.", "gazette",
       reported_cost="₦1.4 billion", reported_length="6 km", featured=True),
    _p("BWARI-02", "GSS Kuduru Road", "bwari", "roads", "Roads / Street Lighting", "Kuduru, Bwari", "reported",
       "Reported project with street lighting.", "gazette", reported_length="1.5 km"),
    _p("BWARI-03", "Kuduru Multipurpose Town Hall", "bwari", "infrastructure", "Community Infrastructure", "Kuduru Ward, Bwari",
       "reported", "Reported project.", "gazette"),
    _p("BWARI-04", "Gbazango Internal Road", "bwari", "roads", "Roads", "Gbazango, Kubwa Ward, Bwari", "reported",
       "Reported project.", "gazette", reported_length="2.2 km"),
    _p("BWARI-05", "Byazhin/Byhazin Across Road", "bwari", "roads", "Roads", "Byazhin Ward, Bwari", "reported",
       "Reported project.", "gazette"),
    _p("BWARI-06", "Sabon Gari–Technology Village Road", "bwari", "roads", "Roads", "Bwari", "ongoing", ONGOING_2023, "vanguard_mar23"),
    _p("BWARI-07", "Kubwa Guinness Junction Road Rehabilitation", "bwari", "roads", "Roads", "Kubwa, Bwari", "reported",
       "Reported rehabilitation.", "vanguard_mar23"),
    _p("BWARI-08", "Bwari Town Hall", "bwari", "infrastructure", "Community Infrastructure", "Bwari", "reported",
       "Reported project.", "vanguard_mar23"),
    # Kuje
    _p("KUJE-01", "Shadadi Road", "kuje", "roads", "Roads", "Kuje", "ongoing", ONGOING_2023, "vanguard_mar23"),
    _p("KUJE-02", "Lanto Road", "kuje", "roads", "Roads / Solar Lighting", "Kuje", "reported", "Reported project.",
       "vanguard_apr23", reported_length="6 km"),
    _p("KUJE-03", "Government Secondary School, Jedda Classroom Block", "kuje", "education", "Education", "Jedda, Kuje",
       "nearing_completion", "Reported nearing completion in source; current status requires verification.", "vanguard_apr23",
       description="Six-classroom block reported as nearing completion in 2023.", featured=True),
    _p("KUJE-04", "Primary Health Care Centre, Jedda", "kuje", "healthcare", "Health", "Jedda, Kuje", "reported",
       "Reported project.", "vanguard_apr23"),
    # Gwagwalada
    _p("GWAG-01", "Gwagwalada Sports & Civic Centre", "gwagwalada", "sports", "Sports / Civic", "Kaida, Gwagwalada", "reported",
       "Reported project.", "vanguard_mar23"),
    _p("GWAG-02", "Agwan Dodo Road", "gwagwalada", "roads", "Roads", "Gwagwalada", "ongoing", ONGOING_2023, "vanguard_mar23"),
    _p("GWAG-03", "Tunga Maje Township Road", "gwagwalada", "roads", "Roads", "Gwagwalada", "reported", "Reported project.",
       "vanguard_apr23", reported_length="4 km"),
    _p("GWAG-04", "Paikon Kore Primary Health Centre", "gwagwalada", "healthcare", "Health", "Paikon Kore, Gwagwalada", "reported",
       "Reported.", "vanguard_apr23",
       description="Reported functional PHC with inverter-supported electricity.", featured=True),
    _p("GWAG-05", "Government Secondary School Gwagwalada Classroom Block", "gwagwalada", "education", "Education", "Gwagwalada",
       "reported", "Reported.", "peoples_gss", description="Reported 3-classroom block project."),
    # Kwali
    _p("KWALI-01", "Pai Road", "kwali", "roads", "Roads", "Kwali", "ongoing", ONGOING_2023, "vanguard_mar23"),
    _p("KWALI-02", "Kilankwa Road", "kwali", "roads", "Roads", "Kwali", "ongoing", ONGOING_2023, "vanguard_mar23"),
    # Abaji
    _p("ABAJI-01", "Yaba Community Road", "abaji", "roads", "Roads", "Yaba, Abaji", "ongoing", ONGOING_2023, "vanguard_mar23"),
    _p("ABAJI-02", "Abaji Town Road", "abaji", "roads", "Roads", "Abaji", "reported", "Reported project.", "vanguard_mar23"),
    # FCT-wide programmes
    _p("EDU-2018", "Scholarship Programme — 2018/2019", None, "education", "Education", "All six FCT Area Councils", "reported",
       "Reported by Daily Trust.", "dailytrust_scholarship", featured=True,
       reported_cost="₦80 million",
       summary="Reported ₦80 million scholarship round covering all six FCT Area Councils: about 3,000 applications and "
       "1,300 successful applicants in the 2018/2019 round.",
       description="Daily Trust reported the following for the **2018/2019 scholarship round**:\n\n"
       "- Reported value: ₦80 million\n"
       "- Reported applications: about 3,000\n"
       "- Reported successful applicants: 1,300 (this round only — not a historical total)\n"
       "- Coverage: all six FCT Area Councils\n"
       "- Previous round: 600 beneficiaries reported"),
    _p("WATER-2018", "Rural Water Projects — 2018", None, "water-rural-development", "Water / Rural Development",
       "Takushara, Karshi, Karu, Dakibiyu, Waru and other locations", "reported",
       "Rural water projects commissioned/reported in 2018.", "peoples_water", year=2018, featured=True,
       summary="Rural water projects reported in 2018 at Takushara, Karshi, Karu, Dakibiyu, Waru and other locations.",
       description="Rural water projects commissioned/reported in 2018. Locations reported:\n\n"
       "- Takushara\n- Karshi\n- Karu\n- Dakibiyu\n- Waru\n- other locations\n\n"
       "The same report attributes projects across the six Area Councils in these **reported portfolio categories**: "
       "scholarships, boreholes, rural electrification, clinics, schools and rural roads. "
       "These are categories only, not a verified count of projects."),
]

PROJECT_STATUS_WORDS = {
    "ongoing": "Ongoing (as reported)",
    "nearing_completion": "Nearing completion (as reported)",
    "commissioned": "Commissioned (as reported)",
    "reported": "Reported — current status not confirmed",
}


def _project_description(r: dict) -> str:
    lines = [f"**{FACILITATED}**", ""]
    if r.get("description"):
        lines += [r["description"], ""]
    lines += [
        f"- **Location:** {r['location']}",
        f"- **Category:** {r['category_label']}",
    ]
    if r.get("reported_cost"):
        lines.append(f"- **Reported value:** {r['reported_cost']}")
    if r.get("reported_length"):
        lines.append(f"- **Reported length:** {r['reported_length']}")
    lines.append(f"- **Status (source wording):** {r['status_note']}")
    lines += [
        "",
        "Details the source does not state — such as start or completion dates, contractor, "
        f"funding breakdown or present condition — are not shown. {PENDING_INFO}",
    ]
    return "\n".join(lines)


def _project_summary(r: dict) -> str:
    if r.get("summary"):
        return r["summary"]
    bits = [f"{FACILITATED[:-1]}, in {r['location']}."]
    if r.get("reported_length"):
        bits.append(f"Reported length: {r['reported_length']}.")
    if r.get("reported_cost"):
        bits.append(f"Reported value: {r['reported_cost']}.")
    bits.append(r["status_note"])
    return " ".join(bits)[:400]


def project_slug(r: dict) -> str:
    return slugify(f"{r['code']} {r['title']}")[:160]


# Records from the earlier research seed and the sample records they replace.
RETIRED_PROJECT_SLUGS = [
    "global-suites-sabon-gari-road-bwari",
    "nyanya-township-road-amac",
    "karu-town-hall-amac",
    "shadadi-road-kuje",
    "kubwa-internal-roads-gbazango-byazhin",
    "jikwoyi-nyanya-youth-sports-centres",
    "amac-medical-centres",
    "amac-school-renovations",
    "kwali-abaji-empowerment-2019",
    "fct-area-councils-administration-bill-2015",
    "fct-university-science-technology-abaji-bill",
    "fct-magistrates-welfare-bill",
]

# ---------------------------------------------------------------------------
# Legislative record (section 6)
# ---------------------------------------------------------------------------

SPONSOR = "Senator Philip Tanimu Aduda"
CONFIRM = "Confirm final legislative status."
SELF_PASSED = "Self-reported as passed until matched to an official enactment/assent record."

LEGISLATION: list[dict] = [
    {
        "code": "A", "title": "FCT Area Councils Administrative & Political Structure Bill", "category": "Governance",
        "year": 2015, "stage": "second_reading", "verification": "verified",
        "official_status": "Second reading documented by the National Assembly.",
        "description": "Bill seeking a legal framework for administration and political structures of FCT Area Councils.",
        "note": "Verified for the second-reading stage only. Not shown as law: no official enactment/assent record has been supplied.",
        "sources": ["nass_157"], "featured": True,
    },
    {
        "code": "B", "title": "Federal Capital Territory University of Science & Technology, Abaji Bill", "category": "Education",
        "bill_number": "S.B. 59", "year": 2017, "stage": "committee_stage", "verification": "verified",
        "official_status": "Referred to the Senate Committee on Tertiary Education and TETFUND for report.",
        "description": "Bill to establish a Federal Capital Territory University of Science & Technology at Abaji.",
        "note": "Verified for this legislative stage (committee referral).",
        "sources": ["nass_589"], "featured": True,
    },
    {
        "code": "C", "title": "FCT College of Education, Zuba", "category": "Education",
        "stage": "self_reported_passed", "verification": "self_reported",
        "official_status": "Official-site status: \"Passed.\"",
        "description": "Proposal for establishment of an FCT College of Education at Zuba.",
        "note": SELF_PASSED, "sources": ["official_about"],
    },
    {
        "code": "D", "title": "FCT Health Insurance Agency Bill", "category": "Health", "bill_number": "SB 668",
        "stage": "self_reported_passed", "verification": "self_reported",
        "official_status": "Official-site status: \"Passed.\"",
        "description": "Legislative proposal concerning health insurance administration in the FCT.",
        "note": SELF_PASSED, "sources": ["official_about"], "featured": True,
    },
    {
        "code": "E", "title": "FCT Primary Health Care Board Bill", "category": "Health", "bill_number": "SB 669",
        "stage": "pending", "verification": "self_reported",
        "official_status": None,
        "description": "Proposal concerning primary healthcare administration in the FCT.",
        "note": "Reported / self-reported. Confirm final legislative status before publishing as law.",
        "sources": ["official_about"],
    },
    {
        "code": "F", "title": "FCT Water Board Bill", "category": "Infrastructure / Water",
        "stage": "self_reported_passed", "verification": "self_reported",
        "official_status": "Official-site status: \"Passed.\"",
        "description": "Proposal concerning the FCT water utility.",
        "note": "Self-reported until independently matched to an official enactment record.", "sources": ["official_about"],
    },
    {
        "code": "G", "title": "FCT Civil Service Commission Bill", "category": "Governance", "bill_number": "SB 177",
        "stage": "self_reported_passed", "verification": "self_reported",
        "official_status": "Official-site status: \"Passed.\"",
        "description": "Proposal for a dedicated FCT civil service commission.",
        "note": "Self-reported until independently verified.", "sources": ["official_about"],
    },
    {
        "code": "H", "title": "Abuja Metropolitan Management Council Bill", "category": "Governance / Urban Management",
        "bill_number": "SB 58", "stage": "pending", "verification": "reported",
        "description": "Proposal concerning management of metropolitan Abuja.",
        "note": CONFIRM, "sources": ["blueprint"],
    },
    {
        "code": "I", "title": "FCT Transport Authority Bill", "category": "Transport", "bill_number": "SB 175",
        "stage": "pending", "verification": "reported",
        "description": "Proposal concerning transport administration in the FCT.",
        "note": CONFIRM, "sources": ["blueprint"],
    },
    {
        "code": "J", "title": "FCT Magistrates Salaries/Allowances Bill", "category": "Justice", "bill_number": "SB 419",
        "stage": "pending", "verification": "reported",
        "description": "Proposal concerning salaries, allowances and benefits of FCT magistrates.",
        "note": CONFIRM, "sources": ["blueprint"],
    },
    {
        "code": "K", "title": "Federal Polytechnic, Orozo Bill", "category": "Education / Technical Education",
        "stage": "pending", "verification": "self_reported",
        "description": "Proposal to establish a federal polytechnic in Orozo.",
        "note": "Self-reported / reported. Confirm official status.", "sources": ["official_about"],
    },
    {
        "code": "L", "title": "FCT College of Agriculture, Rubochi", "category": "Education / Agriculture",
        "stage": "pending", "verification": "reported",
        "description": "Proposal for an FCT College of Agriculture at Rubochi.",
        "note": CONFIRM, "sources": ["vanguard_mar23"],
    },
    {
        "code": "M", "title": "FCT College of Health, Kwali", "category": "Health / Education",
        "stage": "pending", "verification": "reported",
        "description": "Proposal for an FCT College of Health in Kwali.",
        "note": CONFIRM, "sources": ["vanguard_mar23"],
    },
]


def legislation_slug(r: dict) -> str:
    return slugify(r["title"])[:160]


# ---------------------------------------------------------------------------
# Election records (sections 4, 11, 12, 14)
# ---------------------------------------------------------------------------

ELECTIONS: list[dict] = [
    {
        "slug": "2019-fct-senatorial-election", "year": 2019, "title": "2019 FCT Senatorial Election",
        "constituency": "Federal Capital Territory", "candidate": "Tanimu Philip Aduda", "party": "PDP",
        "outcome": "Elected", "votes": 263055, "votes_note": "Vote total reported by ThisDay.",
        "verification": "verified",
        "note": "INEC's official elected-candidates record confirms him as the elected FCT senator. The vote total is reported, not taken from an INEC document.",
        "summary": "INEC's official list of elected candidates to the Senate confirms Tanimu Philip Aduda (PDP) as the elected senator for the FCT in 2019. ThisDay reported a total of 263,055 votes.",
        "sources": [("inec_2019", "Confirms the election result"), ("thisday_2019", "Reported vote total")],
    },
    {
        "slug": "2023-fct-senatorial-election", "year": 2023, "title": "2023 FCT Senatorial Election",
        "constituency": "Federal Capital Territory", "candidate": "Tanimu Philip Aduda", "party": "PDP",
        "outcome": "Not elected — Ireti Kingibe was declared winner.",
        "verification": "reported",
        "note": "The candidacy is verified against INEC's 2023 final candidate list. The declared result is reported (Vanguard); add INEC's declaration as a source to verify it.",
        "summary": "INEC's 2023 final candidate list records Tanimu Philip Aduda as the PDP candidate for the FCT Senate election. Ireti Kingibe was declared winner.",
        "sources": [("inec_2023", "Confirms the candidacy"), ("vanguard_mar23", "Reports the declared result")],
    },
    {
        "slug": "2027-fct-senatorial-election", "year": 2027, "title": "2027 FCT Senatorial Election",
        "constituency": "Federal Capital Territory", "candidate": "Tanimu Philip Aduda", "party": "APC",
        "outcome": "Candidate — election scheduled for 16 January 2027.", "election_date": "2027-01-16",
        "verification": "verified", "current": True,
        "note": "Official INEC record. INEC's final list of candidates records: FCT / Federal Capital Territory / Tanimu Philip Aduda / APC.",
        "summary": "INEC's final list of candidates for the January 2027 senatorial election lists Tanimu Philip Aduda as the APC candidate for the Federal Capital Territory senatorial district. INEC's election calendar schedules the National Assembly election for 16 January 2027.",
        "sources": [("inec_2027", "Final list of candidates"), ("inec_calendar", "Election date")],
    },
]

# ---------------------------------------------------------------------------
# Profile (sections 2–5, 10)
# ---------------------------------------------------------------------------

def _src(key: str) -> dict:
    s = SOURCES[key]
    return {"source_name": s["name"], "source_url": s["url"] or ""}


PROFILE = {
    "name": "Senator Philip Tanimu Aduda, CON",
    "title": "Former FCT Senator (2011–2023)",
    "tagline": "APC Candidate — FCT Senatorial District, 2027",
    "summary": (
        "Senator Philip Tanimu Aduda, CON, represented the Federal Capital Territory in the Senate from 2011 to 2023, "
        "after serving in the House of Representatives from 2003 to 2011. INEC's final list of candidates for the 2027 "
        "senatorial election lists him as the APC candidate for the FCT senatorial district. INEC has scheduled the "
        "National Assembly election for 16 January 2027."
    ),
    "biography": (
        "## Background\n\n"
        "Philip Tanimu Aduda was born on 13 June 1969 in Karu, Federal Capital Territory. He attended Government "
        "Secondary School, Gwagwalada; Kaduna Polytechnic; the University of Jos; and the Federal Polytechnic, Bida.\n\n"
        "Sources describe his qualification differently, so both are shown as each source records it: the APC candidate "
        "biography gives a **Higher Diploma in Public Administration**, and INEC's 2027 final candidate list records a "
        "**Diploma in Social Work**.\n\n"
        "## Public service\n\n"
        "According to the APC's candidate biography, he was elected councillor for Karu Ward in 1996. He represented the "
        "AMAC/Bwari Federal Constituency in the House of Representatives from 2003 to 2011, and was elected Senator for "
        "the FCT in 2011, then re-elected in 2015 and 2019. He was appointed Senate Minority Whip in 2015 and became "
        "Senate Minority Leader in 2022.\n\n"
        "In 2023 he lost the FCT Senate election to Ireti Kingibe. In March 2026 he resigned from the PDP and joined the "
        "APC, and INEC's final list for the 2027 election lists him as the APC candidate for the FCT senatorial district.\n\n"
        "## National honours\n\n"
        "- **CON** — 2023, reported by his official website and in 2023 national honours reporting.\n"
        "- **MFR** — 2010, as stated on his official website (self-reported; not yet matched to an official government record).\n\n"
        "## How to read this page\n\n"
        "Each fact on this page shows its source and a verification label: **Verified** (official INEC, National Assembly "
        "or FCTA record), **Reported** (credible news reporting), **Self-reported** (published by Senator Aduda, his "
        "official website or his party) or **Pending verification**."
    ),
    "photo_caption": "Official portrait — Senator Philip Aduda Official Website",
    "photo_alt": "Official portrait of Senator Philip Tanimu Aduda",
    "photo_source_name": "Senator Philip Aduda Official Website",
    "photo_source_url": "https://senatoraduda.com.ng/about/",
    "photo_usage": "Primary profile portrait",
    "photo_rights_status": (
        "Pending: the image file has not yet been obtained. Upload it here once it has been obtained from the official "
        "website or his media team with permission to use it."
    ),
    "badges": [
        {"label": "Former FCT Senator (2011–2023)", "verification": "self_reported", **_src("apc_profile")},
        {"label": "APC Candidate — FCT Senatorial District, 2027", "verification": "verified", **_src("inec_2027")},
    ],
    "facts": [
        {"label": "Date of birth", "value": "13 June 1969", "verification": "self_reported", **_src("apc_profile")},
        {"label": "Place of birth", "value": "Karu, Federal Capital Territory, Nigeria", "verification": "self_reported", **_src("apc_profile")},
        {
            "label": "Education", "verification": "self_reported", **_src("apc_profile"),
            "value": "Government Secondary School, Gwagwalada; Kaduna Polytechnic; University of Jos; Federal Polytechnic, Bida",
        },
        {"label": "Qualification (APC candidate biography)", "value": "Higher Diploma in Public Administration", "verification": "self_reported", **_src("apc_profile")},
        {
            "label": "Qualification (INEC 2027 final candidate list)", "value": "Diploma in Social Work", "verification": "verified",
            **_src("inec_2027"), "note": "As recorded on INEC's list. The two sources describe the qualification differently; both are kept.",
        },
        {
            "label": "National honour", "value": "CON (2023)", "verification": "reported", **_src("official_about"),
            "note": "Reported by the official site and 2023 national honours reporting.",
        },
        {
            "label": "National honour", "value": "MFR (2010)", "verification": "self_reported", **_src("official_about"),
            "note": "Stated on his official website; verify before presenting as an official government record.",
        },
        {"label": "Party", "value": "APC (joined March 2026)", "verification": "reported", **_src("premium_times")},
        {"label": "2027 candidacy", "value": "APC candidate, Federal Capital Territory senatorial district", "verification": "verified", **_src("inec_2027")},
    ],
    "metrics": [
        {"value": "140+", "label": "Infrastructural Development"},
        {"value": "160+", "label": "Community Engagement"},
        {"value": "1,000+", "label": "Constituency Projects"},
        {"value": "50+", "label": "Policy Advocacy"},
    ],
    "metrics_note": "Self-reported figures published by Senator Aduda's official platform.",
    "metrics_source_url": "https://senatoraduda.com.ng/",
    "timeline": [
        {"year": "1996", "title": "Elected councillor, Karu Ward", "description": "Grassroots political entry; elected councillor representing Karu Ward.", "verification": "self_reported", "src": "apc_profile"},
        {"year": "2003", "title": "Elected to the House of Representatives", "description": "Elected to the House of Representatives representing AMAC/Bwari Federal Constituency.", "verification": "self_reported", "src": "apc_profile"},
        {"year": "2007", "title": "Re-elected to the House of Representatives", "description": "", "verification": "self_reported", "src": "apc_profile"},
        {"year": "2011", "title": "Elected Senator for the FCT", "description": "Elected Senator representing the Federal Capital Territory.", "verification": "self_reported", "src": "apc_profile"},
        {"year": "2015", "title": "Re-elected Senator; Senate Minority Whip", "description": "Re-elected Senator and appointed Senate Minority Whip.", "verification": "self_reported", "src": "apc_profile"},
        {"year": "2019", "title": "Re-elected Senator for the FCT", "description": "INEC's list of elected candidates confirms the result.", "verification": "verified", "src": "inec_2019"},
        {"year": "2022", "title": "Senate Minority Leader", "description": "Became Senate Minority Leader.", "verification": "self_reported", "src": "apc_profile"},
        {"year": "2023", "title": "2023 FCT Senate election", "description": "Lost the FCT Senate election to Ireti Kingibe.", "verification": "reported", "src": "vanguard_mar23"},
        {"year": "2023", "title": "National honour: CON", "description": "Received/was listed for the national honour CON.", "verification": "reported", "src": "official_about"},
        {"year": "March 2026", "title": "Left the PDP and joined the APC", "description": "Resigned from the PDP on 17 March 2026 and subsequently joined the APC.", "verification": "reported", "src": "premium_times"},
        {"year": "2026", "title": "APC candidate for the FCT Senate seat", "description": "Listed by INEC as the APC candidate for the FCT senatorial district for the 2027 election.", "verification": "verified", "src": "inec_2027"},
        {"year": "2027", "title": "Election day: 16 January 2027", "description": "INEC scheduled the National Assembly election for 16 January 2027.", "verification": "verified", "src": "inec_calendar"},
    ],
    "links": [
        {"label": "Official website", "url": "https://senatoraduda.com.ng/"},
        {"label": "APC candidate profile", "url": "https://www.vote.apc.com.ng/tanimu-philip-aduda-sen"},
        {"label": "INEC 2027 final list of Senate candidates", "url": SOURCES["inec_2027"]["url"]},
    ],
}


def profile_timeline() -> list[dict]:
    out = []
    for t in PROFILE["timeline"]:
        s = SOURCES[t["src"]]
        out.append(
            {
                "year": t["year"],
                "title": t["title"],
                "description": t["description"],
                "source": s["url"] or "",
                "source_name": s["name"],
                "verification": t["verification"],
            }
        )
    return out


# ---------------------------------------------------------------------------
# News (section 16)
# ---------------------------------------------------------------------------

NEWS: list[dict] = [
    {
        "title": "Who Is Senator Philip Tanimu Aduda?",
        "category": "profile", "label": "historical_record", "verification": "self_reported",
        "excerpt": "A sourced profile of Senator Philip Tanimu Aduda, CON: background, public service, national honours and his 2027 candidacy.",
        "body": (
            "Senator Philip Tanimu Aduda, CON, represented the Federal Capital Territory (FCT) in the Senate from 2011 to "
            "2023. INEC's final list of candidates for the 2027 senatorial election lists him, as Tanimu Philip Aduda, as the "
            "All Progressives Congress (APC) candidate for the Federal Capital Territory senatorial district.\n\n"
            "## Background\n\n"
            "- **Date of birth:** 13 June 1969\n"
            "- **Place of birth:** Karu, Federal Capital Territory\n"
            "- **Education:** Government Secondary School, Gwagwalada; Kaduna Polytechnic; University of Jos; Federal Polytechnic, Bida\n\n"
            "Sources describe his qualification differently. The APC candidate biography gives a Higher Diploma in Public "
            "Administration; INEC's 2027 final candidate list records a Diploma in Social Work.\n\n"
            "## Public service\n\n"
            "- 1996: elected councillor representing Karu Ward (APC candidate biography)\n"
            "- 2003–2011: Member, House of Representatives, AMAC/Bwari Federal Constituency\n"
            "- 2011–2023: Senator representing the FCT (elected 2011; re-elected 2015 and 2019)\n"
            "- 2015: appointed Senate Minority Whip\n"
            "- 2022: became Senate Minority Leader\n\n"
            "## National honours\n\n"
            "- CON (2023), reported by his official website and in 2023 national honours reporting\n"
            "- MFR (2010), as stated on his official website (self-reported)\n\n"
            "## 2027\n\n"
            "In March 2026 he resigned from the PDP and joined the APC. INEC's final list records him as the APC candidate "
            "for the FCT senatorial district, and INEC has scheduled the National Assembly election for 16 January 2027.\n\n"
            "*Verification: biographical details come from the APC candidate biography and his official website "
            "(self-reported). The 2027 candidacy is verified against INEC's final list.*"
        ),
        "sources": ["apc_profile", "official_about", "inec_2027"],
    },
    {
        "title": "Aduda's Legislative Journey: From Grassroots Politics to the Senate",
        "category": "profile", "label": "historical_record", "verification": "self_reported",
        "excerpt": "From councillor for Karu Ward in 1996 to three Senate terms for the FCT: the milestones of Senator Aduda's political career, with sources.",
        "body": (
            "This timeline sets out the milestones of Senator Philip Tanimu Aduda's political career as recorded by the "
            "sources listed below.\n\n"
            "| Year | Milestone | Verification |\n|---|---|---|\n"
            "| 1996 | Elected councillor representing Karu Ward | Self-reported (APC candidate biography) |\n"
            "| 2003 | Elected to the House of Representatives, AMAC/Bwari Federal Constituency | Self-reported (APC candidate biography) |\n"
            "| 2007 | Re-elected to the House of Representatives | Self-reported (APC candidate biography) |\n"
            "| 2011 | Elected Senator representing the FCT | Self-reported (APC candidate biography) |\n"
            "| 2015 | Re-elected Senator; appointed Senate Minority Whip | Self-reported (APC candidate biography) |\n"
            "| 2019 | Re-elected Senator for the FCT | Verified (INEC) |\n"
            "| 2022 | Became Senate Minority Leader | Self-reported (APC candidate biography) |\n"
            "| 2023 | Lost the FCT Senate election to Ireti Kingibe | Reported |\n"
            "| March 2026 | Resigned from the PDP and joined the APC | Reported (Premium Times) |\n"
            "| 2026 | APC candidate for the FCT Senate seat for 2027 | Verified (INEC) |\n\n"
            "INEC has scheduled the National Assembly election for 16 January 2027."
        ),
        "sources": ["apc_profile", "inec_2019", "vanguard_mar23", "premium_times", "inec_2027"],
    },
    {
        "title": "FCT Area Councils: Understanding the Six Councils",
        "category": "public-information", "label": "historical_record", "verification": "verified",
        "excerpt": "The Federal Capital Territory has six Area Councils: AMAC, Bwari, Gwagwalada, Kuje, Kwali and Abaji.",
        "body": (
            "The Federal Capital Territory (FCT) is made up of six Area Councils, as listed by the Federal Capital Territory "
            "Administration (FCTA):\n\n"
            "1. Abuja Municipal Area Council (AMAC)\n"
            "2. Bwari Area Council\n"
            "3. Gwagwalada Area Council\n"
            "4. Kuje Area Council\n"
            "5. Kwali Area Council\n"
            "6. Abaji Area Council\n\n"
            "NIPAM uses the six councils to organise its community pages, records, news and events, so members can follow "
            "what is happening where they live.\n\n"
            "Ward counts, boundaries, population figures and polling units are not shown here. They will be added only from "
            "authoritative current sources. Choosing an Area Council on NIPAM does not indicate where anyone votes."
        ),
        "sources": ["fcta_survey"],
    },
    {
        "title": "A Look at Aduda's FCT Legislative Record",
        "category": "legislation", "label": "historical_record", "verification": "self_reported",
        "excerpt": "Thirteen bills and proposals associated with Senator Aduda, each shown at the stage its source documents — not collapsed into \"passed\".",
        "body": (
            "NIPAM lists each bill associated with Senator Philip Tanimu Aduda as a separate record, showing the legislative "
            "stage its source documents. A bill is not shown as law unless an official enactment or assent record is supplied.\n\n"
            "## Verified stages (National Assembly records)\n\n"
            "- **FCT Area Councils Administrative & Political Structure Bill** (2015): second reading documented by the National Assembly.\n"
            "- **FCT University of Science & Technology, Abaji Bill** (S.B. 59, 2017): referred to the Senate Committee on "
            "Tertiary Education and TETFUND for report.\n\n"
            "## Self-reported as passed (official website)\n\n"
            "His official website lists these with the status \"Passed\". They remain self-reported until matched to an "
            "official enactment/assent record:\n\n"
            "- FCT College of Education, Zuba\n- FCT Health Insurance Agency Bill (SB 668)\n- FCT Water Board Bill\n"
            "- FCT Civil Service Commission Bill (SB 177)\n\n"
            "## Status pending verification\n\n"
            "- FCT Primary Health Care Board Bill (SB 669) — official website\n"
            "- Federal Polytechnic, Orozo Bill — official website\n"
            "- Abuja Metropolitan Management Council Bill (SB 58) — reported by Blueprint\n"
            "- FCT Transport Authority Bill (SB 175) — reported by Blueprint\n"
            "- FCT Magistrates Salaries/Allowances Bill (SB 419) — reported by Blueprint\n"
            "- FCT College of Agriculture, Rubochi — reported by Vanguard\n"
            "- FCT College of Health, Kwali — reported by Vanguard\n\n"
            "See the [Legislation](/legislation) page for each record with its source."
        ),
        "sources": ["nass_157", "nass_589", "official_about", "blueprint", "vanguard_mar23"],
    },
    {
        "title": "Documented Constituency Projects Reported Across the FCT",
        "category": "projects", "label": "historical_record", "verification": "reported",
        "excerpt": "Roads, town halls, sports centres, classrooms and health centres reported across all six Area Councils as constituency projects during Senator Aduda's representation.",
        "body": (
            "News reports describe constituency projects facilitated or attracted during Senator Aduda's representation "
            "across the six Area Councils. They are reported projects, not projects personally funded by him. Where a "
            "report says a project was ongoing, NIPAM shows it as ongoing.\n\n"
            "- **AMAC:** the Nyanya road / Nyanya-Hospital road network (reported value approximately ₦1.4 billion); the "
            "VIO–Police Station–Hospital, Agwan Dadi, Gbagalape, Kurudu and Jikwoyi roads (reported ongoing in 2023); a Youth "
            "& Sports Centre at Jikwoyi; Karu Town Hall; and the Nyanya Mini Stadium / Sports Centre.\n"
            "- **Bwari:** Global Suite Road, Sabon Gari (reported 6 km, ₦1.4 billion); GSS Kuduru Road (1.5 km, with street "
            "lighting); Kuduru Multipurpose Town Hall; Gbazango Internal Road (2.2 km); Byazhin Across Road; Sabon "
            "Gari–Technology Village Road; Kubwa Guinness Junction road rehabilitation; and Bwari Town Hall.\n"
            "- **Kuje:** Shadadi Road; Lanto Road (6 km, solar lighting); a six-classroom block at GSS Jedda (reported nearing "
            "completion in 2023); and the Primary Health Care Centre, Jedda.\n"
            "- **Gwagwalada:** Gwagwalada Sports & Civic Centre, Kaida; Agwan Dodo Road; Tunga Maje Township Road (4 km); "
            "Paikon Kore Primary Health Centre; and a 3-classroom block at GSS Gwagwalada.\n"
            "- **Kwali:** Pai Road and Kilankwa Road (reported ongoing in 2023).\n"
            "- **Abaji:** Yaba Community Road (reported ongoing in 2023) and Abaji Town Road.\n\n"
            "Each project has its own page in [Our Record](/our-record) with its source and current verification status."
        ),
        "sources": ["gazette", "vanguard_mar23", "vanguard_apr23", "tribune", "peoples_gss"],
    },
    {
        "title": "Aduda's 2018/2019 Scholarship Programme",
        "category": "projects", "label": "historical_record", "verification": "reported",
        "excerpt": "Daily Trust reported an ₦80 million scholarship round covering all six FCT Area Councils, with 1,300 successful applicants in 2018/2019.",
        "body": (
            "Daily Trust reported the following about the 2018/2019 scholarship round:\n\n"
            "- **Reported value:** ₦80 million\n"
            "- **Reported applications:** about 3,000\n"
            "- **Reported successful applicants:** 1,300 for the 2018/2019 round\n"
            "- **Coverage:** all six FCT Area Councils\n"
            "- **Previous round:** 600 beneficiaries reported\n\n"
            "The 1,300 figure refers to the 2018/2019 round only. It is not a total for all scholarship rounds."
        ),
        "sources": ["dailytrust_scholarship"],
    },
    {
        "title": "Rural Water Projects Reported Across the FCT",
        "category": "projects", "label": "historical_record", "verification": "reported",
        "excerpt": "Peoples Daily reported rural water projects in 2018 at Takushara, Karshi, Karu, Dakibiyu, Waru and other locations.",
        "body": (
            "Peoples Daily reported rural water projects commissioned in 2018 at the following locations:\n\n"
            "- Takushara\n- Karshi\n- Karu\n- Dakibiyu\n- Waru\n- other locations\n\n"
            "The same report attributes projects across the six Area Councils in these categories: scholarships, boreholes, "
            "rural electrification, clinics, schools and rural roads. These are reported portfolio categories, not a verified "
            "count of projects."
        ),
        "sources": ["peoples_water"],
    },
    {
        "title": "The 2019 FCT Senatorial Election",
        "category": "elections", "label": "verified_information", "verification": "verified",
        "excerpt": "INEC's official list of elected senators confirms Tanimu Philip Aduda (PDP) as the FCT senator elected in 2019.",
        "body": (
            "INEC's official list of elected candidates to the Senate for the 2019 general elections confirms Tanimu Philip "
            "Aduda of the Peoples Democratic Party (PDP) as the elected senator for the Federal Capital Territory.\n\n"
            "ThisDay reported that he received 263,055 votes. The vote total is reported by the newspaper; the election "
            "result itself is confirmed by INEC's record."
        ),
        "sources": ["inec_2019", "thisday_2019"],
        "source_note": "INEC 2019 list of elected senators; ThisDay (vote total).",
    },
    {
        "title": "The 2023 FCT Senatorial Election",
        "category": "elections", "label": "historical_record", "verification": "reported",
        "excerpt": "Senator Aduda contested the 2023 FCT Senate election as the PDP candidate. Ireti Kingibe was declared winner.",
        "body": (
            "INEC's final list of candidates for the 2023 national elections records Tanimu Philip Aduda as the Peoples "
            "Democratic Party (PDP) candidate for the FCT Senate election.\n\n"
            "Ireti Kingibe was declared winner of the election.\n\n"
            "NIPAM keeps this record as part of Senator Aduda's public history. *Verification: the candidacy is verified "
            "against INEC's final list; the declared result is reported.*"
        ),
        "sources": ["inec_2023", "vanguard_mar23"],
    },
    {
        "title": "Philip Aduda Resigns from PDP and Joins APC",
        "category": "elections", "label": "update", "verification": "reported",
        "excerpt": "On 17 March 2026, former FCT senator Philip Aduda resigned from the PDP, citing persistent party crises, and subsequently joined the APC.",
        "body": (
            "On 17 March 2026, Senator Philip Tanimu Aduda resigned from the Peoples Democratic Party (PDP). Premium Times "
            "reported that his resignation letter cited persistent crises in the party. He subsequently aligned with the All "
            "Progressives Congress (APC).\n\n"
            "INEC's final list of candidates for the 2027 senatorial election now lists him as the APC candidate for the "
            "Federal Capital Territory senatorial district, which officially confirms his current party candidacy."
        ),
        "sources": ["premium_times", "official_home", "inec_2027"],
        "event_date": "2026-03-17",
    },
    {
        "title": "INEC Final List: 2027 FCT Senatorial Candidates",
        "category": "elections", "label": "verified_information", "verification": "verified",
        "excerpt": "INEC's final list of candidates for the 2027 Senate election lists Tanimu Philip Aduda as the APC candidate for the FCT. The election is scheduled for 16 January 2027.",
        "body": (
            "INEC has published its final list of candidates for the January 2027 senatorial election. For the Federal "
            "Capital Territory, the list records:\n\n"
            "| State | Constituency | Candidate | Party |\n|---|---|---|---|\n"
            "| FCT | Federal Capital Territory | Tanimu Philip Aduda | APC |\n\n"
            "INEC's election calendar schedules the National Assembly election for **16 January 2027**.\n\n"
            "The full list of candidates for the FCT seat is in the INEC document linked below."
        ),
        "sources": ["inec_2027", "inec_calendar"],
        "source_note": "INEC 2027 Senate final list of candidates; INEC election calendar.",
        "featured": True,
    },
    {
        "title": "Understanding the Role of an FCT Senator",
        "category": "public-information", "label": "historical_record", "verification": "verified",
        "excerpt": "The FCT elects one senator to the Senate, and the National Assembly makes laws for the Territory. Here is what that means.",
        "body": (
            "The Senate is one of the two chambers of Nigeria's National Assembly. Under section 48 of the Constitution, it "
            "consists of three senators from each state and one from the Federal Capital Territory. The FCT senator is "
            "elected by voters across all six Area Councils.\n\n"
            "Section 299 of the Constitution gives the National Assembly the legislative powers for the FCT that a state "
            "House of Assembly has for a state. This is why bills about FCT institutions — such as a water board, a civil "
            "service commission or tertiary institutions — are introduced in the National Assembly, often by the FCT's own "
            "legislators.\n\n"
            "Like other senators, the FCT senator takes part in law-making, oversight of government agencies and the "
            "approval of the federal budget, and represents the concerns of constituents."
        ),
        "sources": ["constitution", "nass_home"],
    },
]


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------


def _published_at(i: int) -> datetime:
    """Seed articles carry the content pack's research date, newest first."""
    base = datetime(2026, 10, 4, 9, 0, tzinfo=UTC)
    return min(base, utcnow()) - timedelta(minutes=i)


def _retire(db: Session, now: datetime) -> int:
    retired = 0
    stmt = select(Project).where(
        Project.deleted_at.is_(None), (Project.slug.in_(RETIRED_PROJECT_SLUGS)) | (Project.is_demo.is_(True))
    )
    for p in db.scalars(stmt).unique().all():
        p.deleted_at, p.status, p.is_featured = now, "draft", False
        retired += 1
    for n in db.scalars(select(News).where(News.deleted_at.is_(None), News.is_demo.is_(True))).unique().all():
        n.deleted_at, n.status, n.is_featured = now, "draft", False
        retired += 1
    return retired


def apply_projects(db: Session, now: datetime) -> int:
    cats = {c.slug: c for c in db.scalars(select(ProjectCategory)).all()}
    councils = {c.slug: c for c in db.scalars(select(AreaCouncil)).all()}
    added = 0
    for r in PROJECTS:
        slug = project_slug(r)
        if db.scalar(select(Project.id).where(Project.slug == slug)):
            continue
        p = Project(
            slug=slug,
            title=r["title"],
            category_id=cats[r["category"]].id,
            category_label=r["category_label"],
            area_council_id=councils[r["council"]].id if r["council"] else None,
            location=r["location"],
            year=r.get("year"),
            summary=_project_summary(r),
            description=_project_description(r),
            verification_status="reported",
            verification_note="Reported by the cited news source; not independently verified against an official record.",
            project_status=r["project_status"],
            status_note=r["status_note"],
            reported_cost=r.get("reported_cost"),
            reported_length=r.get("reported_length"),
            status="published",
            is_featured=r.get("featured", False),
            published_at=now,
        )
        for key in r["sources"]:
            s = upsert_source(db, SOURCES[key])
            p.sources.append(ProjectSource(title=s.title or s.name, publisher=s.name, url=s.url, published_on=s.publication_date, notes=s.notes, source_id=s.id))
        db.add(p)
        added += 1
    return added


def apply_legislation(db: Session, now: datetime) -> int:
    added = 0
    for r in LEGISLATION:
        slug = legislation_slug(r)
        if db.scalar(select(LegislativeRecord.id).where(LegislativeRecord.slug == slug)):
            continue
        rec = LegislativeRecord(
            slug=slug,
            title=r["title"],
            bill_number=r.get("bill_number"),
            category=r["category"],
            year=r.get("year"),
            sponsor=SPONSOR,
            description=r["description"],
            legislative_stage=r["stage"],
            official_status=r.get("official_status"),
            verification_status=r["verification"],
            verification_note=r.get("note"),
            status="published",
            is_featured=r.get("featured", False),
            published_at=now,
        )
        db.add(rec)
        db.flush()
        link_sources(db, "legislation", rec.id, r["sources"])
        added += 1
    return added


def apply_elections(db: Session, now: datetime) -> int:
    added = 0
    for r in ELECTIONS:
        if db.scalar(select(ElectionRecord.id).where(ElectionRecord.slug == r["slug"])):
            continue
        rec = ElectionRecord(
            slug=r["slug"],
            year=r["year"],
            title=r["title"],
            constituency=r["constituency"],
            candidate=r["candidate"],
            party=r["party"],
            outcome=r["outcome"],
            votes=r.get("votes"),
            votes_note=r.get("votes_note"),
            election_date=date.fromisoformat(r["election_date"]) if r.get("election_date") else None,
            summary=r["summary"],
            verification_status=r["verification"],
            verification_note=r["note"],
            is_current=r.get("current", False),
            status="published",
            published_at=now,
        )
        db.add(rec)
        db.flush()
        link_sources(db, "election", rec.id, r["sources"])
        added += 1
    return added


def apply_news(db: Session) -> int:
    cats = {c.slug: c for c in db.scalars(select(NewsCategory)).all()}
    added = 0
    for i, r in enumerate(NEWS):
        slug = slugify(r["title"])[:160]
        if db.scalar(select(News.id).where(News.slug == slug)):
            continue
        names = list(dict.fromkeys(SOURCES[k]["name"] for k in r["sources"]))
        n = News(
            slug=slug,
            title=r["title"],
            excerpt=r["excerpt"],
            body=r["body"],
            category_id=cats[r["category"]].id,
            content_label=r["label"],
            source_note=r.get("source_note") or "Sources: " + "; ".join(names) + ".",
            verification_status=r["verification"],
            author_name="NIPAM Editorial Team",
            status="published",
            is_featured=r.get("featured", False),
            published_at=_published_at(i),
        )
        db.add(n)
        db.flush()
        link_sources(db, "news", n.id, r["sources"])
        added += 1
    return added


def apply_profile(db: Session, *, replace: bool = False) -> bool:
    """Fill the profile once (or when ``replace`` is set). A portrait or gallery
    an administrator has already uploaded is kept."""
    profile = db.scalar(select(PrincipalProfile).order_by(PrincipalProfile.id))
    if profile is None:
        profile = PrincipalProfile()
        db.add(profile)
    if profile.facts and not replace:
        return False
    for key in (
        "name", "title", "tagline", "summary", "biography", "photo_caption", "photo_source_name", "photo_source_url",
        "photo_usage", "badges", "facts", "metrics", "metrics_note", "metrics_source_url", "links",
    ):
        setattr(profile, key, PROFILE[key])
    profile.timeline = profile_timeline()
    if not profile.photo_url:
        profile.photo_alt = PROFILE["photo_alt"]
        profile.photo_rights_status = PROFILE["photo_rights_status"]
    profile.gallery = profile.gallery or []
    return True


def apply(db: Session, *, replace_profile: bool = False) -> dict:
    # Register every source first so the registry is complete even for sources
    # only cited by the profile.
    for data in SOURCES.values():
        upsert_source(db, data)
    now = utcnow()
    result = {
        "retired": _retire(db, now),
        "projects_added": apply_projects(db, now),
        "legislation_added": apply_legislation(db, now),
        "elections_added": apply_elections(db, now),
        "news_added": apply_news(db),
        "profile_updated": apply_profile(db, replace=replace_profile),
    }
    db.commit()
    return result
