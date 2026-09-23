import { Mail, MapPin } from "lucide-react";
import { Link } from "react-router-dom";
import { Logo } from "@/components/brand/Logo";
import { FacebookIcon, WhatsAppIcon, XIcon } from "@/components/shared/Share";

function InstagramIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="17.5" cy="6.5" r="1" fill="currentColor" />
    </svg>
  );
}

// Official account URLs are configured here once confirmed.
const SOCIAL = [
  { label: "Facebook", href: "#", Icon: FacebookIcon },
  { label: "X (Twitter)", href: "#", Icon: XIcon },
  { label: "Instagram", href: "#", Icon: InstagramIcon },
  { label: "WhatsApp", href: "#", Icon: WhatsAppIcon },
];

const COLUMNS = [
  {
    title: "Explore",
    links: [
      ["About", "/about"],
      ["Our Record", "/our-record"],
      ["Area Councils", "/area-councils"],
      ["News", "/news"],
      ["Events", "/events"],
    ],
  },
  {
    title: "Participate",
    links: [
      ["Community", "/community"],
      ["Join NIPAM", "/join"],
      ["Member login", "/login"],
      ["Contact", "/contact"],
    ],
  },
  {
    title: "Policies",
    links: [
      ["Privacy Policy", "/privacy"],
      ["Terms of Use", "/terms"],
      ["Community Guidelines", "/community-guidelines"],
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="relative overflow-hidden bg-navy-900 text-navy-100">
      <div className="h-1 bg-gradient-to-r from-green-600 via-green-500 to-navy-500" />
      <div className="container grid gap-10 py-14 md:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div className="space-y-5">
          <Logo variant="with-name" tone="dark" />
          <p className="max-w-sm text-sm leading-relaxed text-navy-200">
            A digital community connecting residents, sharing information, documenting public records and facilitating constructive civic
            engagement across the Federal Capital Territory.
          </p>
          <ul className="space-y-2 text-sm text-navy-200">
            <li className="flex items-center gap-2">
              <MapPin className="size-4 text-green-400" /> Federal Capital Territory, Abuja, Nigeria
            </li>
            <li className="flex items-center gap-2">
              <Mail className="size-4 text-green-400" />
              <Link to="/contact" className="hover:text-white">
                Contact the NIPAM team
              </Link>
            </li>
          </ul>
          <div className="flex gap-2">
            {SOCIAL.map(({ label, href, Icon }) => (
              <a
                key={label}
                href={href}
                aria-label={`NIPAM on ${label}`}
                className="flex size-10 items-center justify-center rounded-xl bg-white/5 text-navy-100 ring-1 ring-white/10 transition hover:bg-green-600 hover:text-white [&_svg]:size-[18px]"
              >
                <Icon />
              </a>
            ))}
          </div>
        </div>
        {COLUMNS.map((col) => (
          <nav key={col.title} aria-label={col.title}>
            <h2 className="mb-4 font-display text-sm font-bold uppercase tracking-[0.14em] text-white">{col.title}</h2>
            <ul className="space-y-2.5">
              {col.links.map(([label, to]) => (
                <li key={to}>
                  <Link to={to} className="text-sm text-navy-200 transition hover:text-white">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </div>
      <div className="border-t border-white/10">
        <div className="container flex flex-col gap-2 py-6 text-xs text-navy-300 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} NIPAM — Non-Indigenes for Philip Aduda Movement. All rights reserved.</p>
          <p>Membership is voluntary. Area Council selection is not proof of electoral eligibility.</p>
        </div>
      </div>
    </footer>
  );
}
