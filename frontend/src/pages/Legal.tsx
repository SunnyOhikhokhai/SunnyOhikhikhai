import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { Markdown } from "@/components/shared/Markdown";
import { PageHeader } from "@/components/shared/PageHeader";
import { Seo } from "@/components/shared/Seo";

// Draft policy texts. They should be reviewed by qualified counsel for
// compliance with the Nigeria Data Protection Act 2023 before launch.
const LAST_UPDATED = "September 2026";

const DOCS = {
  privacy: {
    title: "Privacy Policy",
    description: "What information NIPAM collects, why, how it is used, and who can access it.",
    body: `
NIPAM ("we") respects your privacy. This policy explains what we collect when you use the NIPAM platform, why we collect it, how we use it and the choices you have. We process personal data in line with the **Nigeria Data Protection Act 2023**.

## What we collect

| Information | Why we collect it |
|---|---|
| Full name | To identify your account and, if you choose, show your name on community posts |
| Email address | To sign you in, verify your account and send the messages you choose |
| Phone number (optional) | For verification and SMS alerts you opt into |
| Password | Stored only as a one-way cryptographic hash (Argon2id) — we can never see it |
| Area Council, ward and community (ward and community optional) | To personalise updates and events for where you live |
| Communication preferences and consent records | To respect your choices and show when consent was given |
| Content you post | Discussions, comments, reactions and reports you submit |
| Security logs | Sign-in times, IP address and device type, to protect accounts and investigate abuse |

We do **not** ask for, or infer, your ethnicity, tribe, religion, indigene status or political opinions, and we do not target messages based on sensitive characteristics.

Your Area Council is **self-declared**. It is not proof of, and is not used to determine, electoral eligibility or voting location.

## How we use your information

- To run your account and keep it secure (including one-time codes and suspicious sign-in protection)
- To show you updates, events and records relevant to your Area Council
- To send **account and security messages** (essential and always sent)
- To send **event notifications and announcements** only through the channels you opt into
- To moderate the community and enforce our Community Guidelines
- To produce **aggregate statistics** (for example, the number of members per Area Council). Analytics do not track individual members' reading activity.

## Who can access it

- **The public** sees only what you publish in the community, shown with your name or display name. Your email address and phone number are **never** shown publicly.
- **Administrators** access member data only as their role requires. Roles include Super Admin, Content Admin, Area Council Admin, Moderator and Analyst. Every administrative action is recorded in an audit log.
- **Service providers** that deliver email, SMS and hosting process data on our behalf under contract.
- We do not sell your personal data.

## Communications

Account messages are essential. Everything else — event notifications, announcements and community updates — is **opt-in** and can be changed at any time under **Settings → Notifications**. Administrators may record an opt-out on your behalf but cannot opt you in.

## Cookies

We use only **strictly necessary cookies**:

- \`nipam_session\` — keeps you signed in (HTTP-only, secure)
- \`nipam_csrf\` — protects forms against cross-site request forgery

We do not use advertising or third-party tracking cookies. The installable app may store selected public content on your device so it can be read offline.

## Your rights

You can view and update your details in **Settings**, change your communication preferences, and **delete your account** at any time. Deleting your account removes your contact details and anonymises your posts as "Former member". You may also contact us to request a copy of your data or raise a concern, and you may complain to the Nigeria Data Protection Commission.

## Retention and security

We keep account data while your account is active. Security logs are retained for a limited period to protect the platform. Data is encrypted in transit (HTTPS), passwords are hashed, and access is restricted by role.

## Contact

For privacy questions or requests, use the [contact form](/contact) and choose "Privacy / data request".

_Last updated: ${LAST_UPDATED}_
`,
  },
  terms: {
    title: "Terms of Use",
    description: "The rules for using the NIPAM platform.",
    body: `
By creating an account or using the NIPAM platform you agree to these terms.

## Membership

- Membership is **voluntary and free**. You may leave at any time by deleting your account.
- You must provide accurate information and keep your password and one-time codes private.
- One person, one account. Do not impersonate anyone or create accounts on someone else's behalf.
- Selecting an Area Council does not establish electoral eligibility, voting location or any legal status.

## Content on the platform

NIPAM distinguishes between **verified information**, **announcements**, **historical records**, **opinion** and **user-generated content**. Labels and verification statuses are shown on each item. Unverified information must not be relied on as established fact. Items marked **Sample** are demonstration content and are not verified information.

## Your contributions

You keep ownership of what you post, and grant NIPAM permission to display it on the platform. You are responsible for your posts and must follow the [Community Guidelines](/community-guidelines). We may remove content or suspend accounts that break these terms or the guidelines.

## Acceptable use

Do not attempt to disrupt, overload, scrape or gain unauthorised access to the platform, other accounts or member data. Automated access is permitted only through the documented API with your own credentials.

## Liability

The platform is provided "as is". We work to keep information accurate and corrections are welcome, but we cannot guarantee that all content is complete or current.

## Changes

We may update these terms. Significant changes will be announced on the platform.

_Last updated: ${LAST_UPDATED}_
`,
  },
  guidelines: {
    title: "Community Guidelines",
    description: "How we keep NIPAM discussions respectful, safe and constructive.",
    body: `
The NIPAM community is a space for constructive conversation among residents of the FCT. These guidelines apply to all discussions, comments and reactions.

## Be constructive

- Discuss ideas, not individuals. Disagree respectfully.
- Stay on topic and choose the right category and Area Council.
- Share sources when you make factual claims.

## Not permitted

- **Hate speech** — attacking people on the basis of ethnicity, tribe, religion, state of origin, indigene status, gender, disability or similar characteristics
- **Threats** or incitement to violence
- **Harassment** or bullying
- **Impersonation** of any person, official or organisation
- **False claims presented as verified facts**
- **Doxxing** — revealing someone's private details
- **Personal information** — posting phone numbers, addresses or email addresses (yours or anyone else's)
- **Spam**, repetitive posting, or misleading links

## Moderation

- Anyone can use the **Report** button. Reports are confidential.
- Content that receives several independent reports may be hidden automatically while a moderator reviews it.
- Moderators may remove content, close discussions, or suspend accounts. Serious or repeated violations lead to suspension.
- New accounts must verify their email before posting, and posting is rate-limited to prevent spam.

## Labels

Community posts are **user-generated content** and represent their authors' views — not verified information from NIPAM.

_Last updated: ${LAST_UPDATED}_
`,
  },
};

export default function Legal({ doc }: { doc: keyof typeof DOCS }) {
  const d = DOCS[doc];
  const { hash } = useLocation();
  useEffect(() => {
    if (hash) document.getElementById(hash.slice(1))?.scrollIntoView();
  }, [hash]);
  return (
    <>
      <Seo title={d.title} description={d.description} />
      <PageHeader eyebrow="Policies" title={d.title} description={d.description} crumbs={[{ to: "/", label: "Home" }, { label: d.title }]} />
      <div className="container max-w-3xl py-12">
        <Markdown className="[&_table]:my-6 [&_table]:w-full [&_table]:text-sm [&_td]:border-t [&_td]:border-border [&_td]:py-2.5 [&_td]:pr-4 [&_td]:align-top [&_th]:pb-2 [&_th]:pr-4 [&_th]:text-left [&_th]:font-semibold [&_th]:text-navy">
          {d.body}
        </Markdown>
      </div>
    </>
  );
}
