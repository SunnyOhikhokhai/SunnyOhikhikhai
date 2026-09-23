"""Sourced public information about Sen. Philip Aduda, compiled from news reports
and parliamentary records (September 2026).

Every record is published as ``pending_review``: the information comes from the
cited reports and must be confirmed by NIPAM administrators (ideally against
his office's own records) before being marked Verified.

    python -m app.seed --aduda
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AreaCouncil, PrincipalProfile, Project, ProjectCategory, ProjectSource, utcnow

LEADERSHIP = {
    "title": "Senate President Lauds Aduda's Constituency Projects In FCT",
    "publisher": "Leadership",
    "url": "https://leadership.ng/senate-president-lauds-adudas-constituency-projects-in-fct/",
}
TRIBUNE = {
    "title": "Senate President lauds Aduda's constituency projects in FCT",
    "publisher": "Nigerian Tribune",
    "url": "https://tribuneonlineng.com/senate-president-lauds-adudas-constituency-projects-in-fct/",
}
DAILY_TRUST = {
    "title": "Despite Losing Election, Aduda Embarks On Oversight Projects",
    "publisher": "Daily Trust",
    "url": "https://dailytrust.com/despite-losing-election-aduda-embarks-on-oversight-projects/",
}
VANGUARD = {
    "title": "Senator Aduda showcases multi-billion naira projects across FCT area councils",
    "publisher": "Vanguard",
    "url": "https://www.vanguardngr.com/2023/03/senator-aduda-showcases-multi-billion-naira-projects-across-fct-area-councils/",
}
THISDAY = {
    "title": "Despite Election Loss, FCT Senator Pledges to Complete N2.8bn Road Projects, Others",
    "publisher": "ThisDay",
    "url": "https://www.thisdaylive.com/index.php/2023/03/27/despite-election-loss-fct-senator-pledges-to-complete-n2-8bn-road-projects-others/",
    "published_on": "2023-03-27",
}
DAILY_NIGERIAN = {
    "title": "Senator Aduda unveils N2.8bn projects",
    "publisher": "Daily Nigerian",
    "url": "https://dailynigerian.com/senator-aduda-unveils/",
}
NASS_BILL = {
    "title": "FCT Area Council Administration, Political Structure Bill",
    "publisher": "National Assembly of Nigeria",
    "url": "https://www.nass.gov.ng/news/item/157",
    "notes": "Passed second reading in the Senate on 25 November 2015.",
}
ORDERPAPER = {
    "title": "FCT lawmakers sponsor 12 bills in three years | NASS Scorecard",
    "publisher": "OrderPaper Nigeria",
    "url": "https://orderpaper.ng/2023/01/20/senator-aduda-increases-bill-tally-by-3-the-national-assembly-scorecard/",
    "published_on": "2023-01-20",
}
GROKIPEDIA = {
    "title": "Philip Aduda",
    "publisher": "Grokipedia (secondary source)",
    "url": "https://grokipedia.com/page/Philip_Aduda",
    "notes": "Single secondary source. Confirm against the original news report or his office's records.",
}
WIKIPEDIA = {"title": "Philip Aduda", "publisher": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Philip_Aduda"}

REVIEW_NOTE = "Compiled from the news reports cited below. Confirm details (dates, lengths, costs) with his office before marking Verified."

# Each record: slug, title, category, council, location, summary, description, sources, featured (+ optional year, record_date, verification)
RECORDS: list[dict] = [
    {
        "slug": "global-suites-sabon-gari-road-bwari",
        "title": "Global Suites – Sabon Gari Road, Bwari",
        "category": "roads",
        "council": "bwari",
        "location": "Sabon Gari, Bwari Area Council",
        "summary": "Road with drainage in the Sabon Gari area of Bwari, reported to cost over ₦1.4 billion and commissioned with Senate President Ahmad Lawan.",
        "description": (
            "The Global Suites / Sabon Gari road in Bwari Area Council is among the constituency projects facilitated by "
            "Sen. Philip Aduda.\n\n"
            "- **According to Leadership and Nigerian Tribune**, it is a 4 km road and was commissioned with Senate President Ahmad Lawan, "
            "who commended the quality of the projects.\n"
            "- **According to Daily Trust**, the Global Suite Road in Sabon Gari cost ₦1.4 billion.\n"
            "- **According to Vanguard**, the road, with drainage and culverts, leads to the Mechanic Village around Sabon Gari and cost over ₦1.4 billion.\n\n"
            "_Reports differ on the length (4 km and 6 km have both been reported). Confirm before publishing figures._"
        ),
        "sources": [LEADERSHIP, TRIBUNE, DAILY_TRUST, VANGUARD],
        "featured": True,
    },
    {
        "slug": "nyanya-township-road-amac",
        "title": "Nyanya Township Road (VIO – Police Station – Hospital Road)",
        "category": "roads",
        "council": "amac",
        "location": "Nyanya, Abuja Municipal Area Council",
        "summary": "Township road in Nyanya passing the Divisional Police Headquarters and hospital, reported to cost over ₦1.4 billion.",
        "description": (
            "A road project through Nyanya in AMAC.\n\n"
            "- **According to Leadership and Nigerian Tribune**, the Nyanya Township Road was among the projects commissioned with "
            "Senate President Ahmad Lawan.\n"
            "- **According to Daily Trust**, the ₦1.4bn VIO–Police Station–Hospital Road in Nyanya was inspected by Sen. Aduda in March 2023.\n"
            "- **According to Vanguard**, the Nyanya–Hospital Road cost over ₦1.4 billion and includes drainage and culverts."
        ),
        "sources": [LEADERSHIP, TRIBUNE, DAILY_TRUST, VANGUARD],
        "featured": True,
    },
    {
        "slug": "karu-town-hall-amac",
        "title": "Karu Multipurpose Town Hall",
        "category": "community-development",
        "council": "amac",
        "location": "Karu, Abuja Municipal Area Council",
        "summary": "Multipurpose town hall in Karu, AMAC, commissioned among Sen. Aduda's constituency projects.",
        "description": (
            "- **According to Leadership and Nigerian Tribune**, the Karu Town Hall in AMAC was among the projects commissioned with "
            "Senate President Ahmad Lawan.\n"
            "- **Daily Trust** reported a multipurpose town hall among the projects Sen. Aduda inspected in March 2023."
        ),
        "sources": [LEADERSHIP, TRIBUNE, DAILY_TRUST],
        "featured": True,
    },
    {
        "slug": "shadadi-road-kuje",
        "title": "Shadadi Road, Kuje",
        "category": "roads",
        "council": "kuje",
        "location": "Shadadi, Kuje Area Council",
        "summary": "Road project in Shadadi, Kuje Area Council, commissioned among Sen. Aduda's constituency projects.",
        "description": (
            "**According to Leadership and Nigerian Tribune**, Shadadi road in Kuje Area Council was among the constituency projects "
            "commissioned with Senate President Ahmad Lawan, spread across the wards of the FCT Senatorial District."
        ),
        "sources": [LEADERSHIP, TRIBUNE],
        "featured": True,
    },
    {
        "slug": "kubwa-internal-roads-gbazango-byazhin",
        "title": "Internal Roads in Gbazango, Kubwa and Byazhin",
        "category": "roads",
        "council": "bwari",
        "location": "Kubwa, Bwari Area Council",
        "summary": "Internal community roads in Gbazango, Kubwa and Byazhin, inspected by Sen. Aduda in March 2023.",
        "description": "**According to Daily Trust**, Sen. Aduda inspected internal roads in Gbazango, Kubwa and Byazhin in Kubwa during his March 2023 project tour.",
        "sources": [DAILY_TRUST],
        "featured": False,
    },
    {
        "slug": "jikwoyi-nyanya-youth-sports-centres",
        "title": "Youth and Sports Centres, Jikwoyi and Nyanya",
        "category": "sports",
        "council": "amac",
        "location": "Jikwoyi and Nyanya, Abuja Municipal Area Council",
        "summary": "Sports centres built in Jikwoyi and Nyanya for talent discovery.",
        "description": (
            "- **According to Vanguard**, sports centres were built in Jikwoyi and Nyanya for talent discovery.\n"
            "- **Daily Trust** reported a youth and sports centre among the projects inspected in March 2023."
        ),
        "sources": [VANGUARD, DAILY_TRUST],
        "featured": True,
    },
    {
        "slug": "amac-medical-centres",
        "title": "Medical Centres in AMAC",
        "category": "healthcare",
        "council": "amac",
        "location": "Abuja Municipal Area Council",
        "summary": "Medical centres in AMAC inspected by Sen. Aduda during his March 2023 project tour.",
        "description": "**According to Vanguard**, medical centres in AMAC were among the projects Sen. Aduda inspected in March 2023. [SPECIFIC LOCATIONS TO BE ADDED]",
        "sources": [VANGUARD],
        "featured": False,
    },
    {
        "slug": "amac-school-renovations",
        "title": "School Renovations in AMAC",
        "category": "education",
        "council": "amac",
        "location": "Abuja Municipal Area Council",
        "summary": "Renovation of schools in AMAC, inspected by Sen. Aduda during his March 2023 project tour.",
        "description": "**According to Vanguard**, schools renovated in AMAC were among the projects Sen. Aduda inspected in March 2023. [SPECIFIC SCHOOLS TO BE ADDED]",
        "sources": [VANGUARD],
        "featured": False,
    },
    {
        "slug": "kwali-abaji-empowerment-2019",
        "title": "Empowerment Programme for Women and Youths, Kwali and Abaji",
        "category": "employment-economic-development",
        "council": "kwali",
        "location": "Kwali and Abaji Area Councils",
        "year": 2019,
        "summary": "Reported distribution of tricycles, sewing machines and grinding machines to 1,200 women and youths in Kwali and Abaji in July 2019.",
        "description": (
            "A secondary source reports that in July 2019 Sen. Aduda distributed empowerment items — tricycles, sewing machines and "
            "grinding machines — to 1,200 women and youths in Kwali and Abaji Area Councils.\n\n"
            "_Only one secondary source was found. Please confirm with the original report or his office before sharing._"
        ),
        "sources": [GROKIPEDIA],
        "verification": "unverified",
        "featured": False,
    },
    {
        "slug": "fct-area-councils-administration-bill-2015",
        "title": "Bill on the Administration and Political Structure of FCT Area Councils",
        "category": "legislative-activity",
        "council": None,
        "location": "FCT-wide",
        "year": 2015,
        "record_date": "2015-11-25",
        "summary": "Sponsored a bill to provide for the administration and political structure of the FCT Area Councils; it passed second reading on 25 November 2015.",
        "description": (
            "Sen. Aduda sponsored *A Bill for an Act to provide for the administration and political structure of Area Councils of the "
            "Federal Capital Territory and for related matters, 2015*.\n\n"
            "**According to the National Assembly**, the bill passed second reading in the Senate on 25 November 2015. Leading the debate, "
            "he argued that adequate laws had not been enacted for the administration of the FCT Area Councils, and that the bill would "
            "fulfil the requirements of the 1999 Constitution (as amended) on their creation, administration and political structure."
        ),
        "sources": [NASS_BILL],
        "featured": True,
    },
    {
        "slug": "fct-university-science-technology-abaji-bill",
        "title": "Bill to Establish the FCT University of Science and Technology, Abaji",
        "category": "legislative-activity",
        "council": "abaji",
        "location": "Abaji Area Council",
        "summary": "A bill for the establishment of a Federal Capital Territory University of Science and Technology in Abaji, listed among bills attributed to Sen. Aduda.",
        "description": (
            "A bill for the establishment of the Federal Capital Territory University of Science and Technology, Abaji, is listed "
            "among the bills attributed to Sen. Aduda in the Ninth National Assembly (2019–2023).\n\n"
            "**According to OrderPaper's National Assembly Scorecard**, he sponsored four bills in the first year of the Ninth Assembly and six by mid-term.\n\n"
            "[CONFIRM BILL NUMBER, DATE INTRODUCED AND STATUS]"
        ),
        "sources": [ORDERPAPER],
        "featured": False,
    },
    {
        "slug": "fct-magistrates-welfare-bill",
        "title": "Bill on the Magistrate Courts of the FCT",
        "category": "legislative-activity",
        "council": None,
        "location": "FCT-wide",
        "summary": "Legislation on the Magistrate Court of the FCT, aimed at improving magistrates' salaries and welfare, listed among bills attributed to Sen. Aduda.",
        "description": (
            "A bill relating to the Magistrate Court of the Federal Capital Territory, Abuja — aimed at improving the salaries and welfare "
            "of magistrates in the FCT judiciary — is listed among bills attributed to Sen. Aduda.\n\n"
            "[CONFIRM BILL NUMBER, DATE INTRODUCED AND STATUS]"
        ),
        "sources": [ORDERPAPER],
        "featured": False,
    },
]

PROFILE = {
    "name": "Sen. Philip Aduda",
    "title": "Former Senator for the Federal Capital Territory (2011–2023)",
    "summary": (
        "Sen. Philip Tanimu Aduda, CON, was born in Karu, FCT. He represented the Federal Capital Territory in the Senate for three "
        "terms, from 2011 to 2023, after two terms in the House of Representatives (2003–2011). His constituency projects span roads, "
        "town halls, sports centres, schools and health facilities across the FCT."
    ),
    "biography": (
        "## Early life and education\n\n"
        "Philip Tanimu Aduda was born in Karu, in the Federal Capital Territory. He attended Government Secondary School, Gwagwalada "
        "(1983–1987) and Kaduna Polytechnic (1987–1990), and earned a Diploma in Social Works and Social Development from the "
        "University of Jos (1990–1992).\n\n"
        "## Public service\n\n"
        "He served two terms in the House of Representatives (2003–2011). In the April 2011 elections he was elected Senator for the "
        "Federal Capital Territory, and he served in the 7th, 8th and 9th National Assemblies (2011–2023). In the 9th Senate he served "
        "in the minority leadership, as Senate Minority Whip and later as Senate Minority Leader.\n\n"
        "In the Senate he sponsored the bill on the administration and political structure of the FCT Area Councils (2015), and bills "
        "attributed to him include the proposed FCT University of Science and Technology, Abaji. See **Our Record** for his "
        "constituency projects across the Area Councils, each with its sources.\n\n"
        "## Honours\n\n"
        "He holds the national honour of Commander of the Order of the Niger (CON).\n\n"
        "## Today\n\n"
        "In 2026, Daily Trust reported that he won the All Progressives Congress (APC) ticket for the FCT Senate seat in the 2027 "
        "elections.\n\n"
        "_Compiled from public sources listed in the timeline. [OFFICIAL BIOGRAPHY FROM HIS OFFICE TO BE ADDED]_"
    ),
    "timeline": [
        {"year": "1990–1992", "title": "Diploma, University of Jos", "description": "Diploma in Social Works and Social Development, after Government Secondary School, Gwagwalada and Kaduna Polytechnic.", "source": "Wikipedia — Philip Aduda"},
        {"year": "2003–2011", "title": "Member, House of Representatives (two terms)", "description": "", "source": "Wikipedia — Philip Aduda"},
        {"year": "2011", "title": "Elected Senator for the Federal Capital Territory", "description": "Elected in the 9 April 2011 elections; served in the 7th Senate (2011–2015).", "source": "Wikipedia — Philip Aduda"},
        {"year": "2015", "title": "Re-elected; sponsored the FCT Area Councils bill", "description": "Served in the 8th Senate (2015–2019). His bill on the administration and political structure of the FCT Area Councils passed second reading on 25 November 2015.", "source": "Wikipedia; National Assembly (nass.gov.ng)"},
        {"year": "2019", "title": "Elected for a third Senate term", "description": "Served in the 9th Senate (2019–2023).", "source": "Wikipedia — 2019 Nigerian Senate election in the FCT"},
        {"year": "2019–2023", "title": "Senate minority leadership", "description": "Served as Senate Minority Whip, and was reported as Senate Minority Leader by March 2023.", "source": "Wikipedia; Vanguard (March 2023)"},
        {"year": "2019–2023", "title": "Constituency projects commissioned with the Senate President", "description": "Senate President Ahmad Lawan commissioned projects including the Global Suites/Sabon Gari road (Bwari), Nyanya Township Road and Karu Town Hall (AMAC) and Shadadi road (Kuje).", "source": "Leadership; Nigerian Tribune"},
        {"year": "2023", "title": "Project inspection tour across the FCT", "description": "Inspected road, health, school and sports projects in Bwari and AMAC, with visits planned to Gwagwalada, Kuje, Kwali and Abaji.", "source": "Daily Trust; Vanguard; ThisDay (27 March 2023)"},
        {"year": "2026", "title": "APC candidate for the FCT Senate seat (2027)", "description": "", "source": "Daily Trust"},
    ],
    "links": [
        {"label": "X (Twitter): @SenatorAduda", "url": "https://x.com/SenatorAduda"},
        {"label": "Instagram: @officialphilipaduda", "url": "https://www.instagram.com/officialphilipaduda/"},
    ],
}


def apply(db: Session, *, replace_profile: bool = False) -> dict:
    """Idempotently add the sourced records and fill the profile if it still
    holds the seeded placeholders (or when ``replace_profile`` is set)."""
    cats = {c.slug: c for c in db.scalars(select(ProjectCategory)).all()}
    councils = {c.slug: c for c in db.scalars(select(AreaCouncil)).all()}
    now = utcnow()
    added = 0
    for r in RECORDS:
        if db.scalar(select(Project.id).where(Project.slug == r["slug"])):
            continue
        p = Project(
            slug=r["slug"],
            title=r["title"],
            category_id=cats[r["category"]].id,
            area_council_id=councils[r["council"]].id if r.get("council") else None,
            location=r["location"],
            year=r.get("year"),
            summary=r["summary"],
            description=r["description"],
            verification_status=r.get("verification", "pending_review"),
            verification_note=REVIEW_NOTE,
            status="published",
            is_featured=r["featured"],
            is_demo=False,
            published_at=now,
        )
        if r.get("record_date"):
            p.record_date = date.fromisoformat(r["record_date"])
        for s in r["sources"]:
            src = ProjectSource(title=s["title"], publisher=s.get("publisher"), url=s.get("url"), notes=s.get("notes"))
            if s.get("published_on"):
                src.published_on = date.fromisoformat(s["published_on"])
            p.sources.append(src)
        db.add(p)
        added += 1
    # Real records take precedence over sample content in the homepage carousel.
    if added:
        for demo in db.scalars(select(Project).where(Project.is_demo.is_(True))).all():
            demo.is_featured = False

    profile = db.scalar(select(PrincipalProfile).order_by(PrincipalProfile.id))
    profile_updated = False
    if profile is None:
        profile = PrincipalProfile()
        db.add(profile)
    if replace_profile or not profile.title or profile.title.startswith("["):
        profile.name = PROFILE["name"]
        profile.title = PROFILE["title"]
        profile.summary = PROFILE["summary"]
        profile.biography = PROFILE["biography"]
        profile.timeline = PROFILE["timeline"]
        if not profile.links:
            profile.links = PROFILE["links"]
        profile_updated = True
    db.commit()
    return {"records_added": added, "profile_updated": profile_updated}
