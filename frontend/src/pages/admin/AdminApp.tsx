import {
  BarChart3,
  CalendarDays,
  ExternalLink,
  FileText,
  History,
  Inbox,
  LayoutDashboard,
  LogOut,
  MapPin,
  Megaphone,
  Menu,
  Newspaper,
  ShieldAlert,
  UserCog,
  Users,
} from "lucide-react";
import { lazy, Suspense, useState } from "react";
import { Link, NavLink, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { Logo } from "@/components/brand/Logo";
import { PageFallback } from "@/components/layout/PublicLayout";
import { Seo } from "@/components/shared/Seo";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { useAuth } from "@/hooks/useAuth";
import { cn, initials } from "@/lib/utils";

const Overview = lazy(() => import("./Overview"));
const Analytics = lazy(() => import("./Analytics"));
const Members = lazy(() => import("./Members"));
const Records = lazy(() => import("./Records"));
const NewsAdmin = lazy(() => import("./NewsAdmin"));
const EventsAdmin = lazy(() => import("./EventsAdmin"));
const Announcements = lazy(() => import("./Announcements"));
const Councils = lazy(() => import("./Councils"));
const Moderation = lazy(() => import("./Moderation"));
const Admins = lazy(() => import("./Admins"));
const Audit = lazy(() => import("./Audit"));
const Messages = lazy(() => import("./Messages"));

const NAV = [
  { to: "/admin", label: "Overview", icon: LayoutDashboard, perms: ["analytics.view", "members.view"], end: true },
  { to: "/admin/analytics", label: "Analytics", icon: BarChart3, perms: ["analytics.view"] },
  { to: "/admin/members", label: "Members", icon: Users, perms: ["members.view", "members.suspend"] },
  { to: "/admin/records", label: "Our Record", icon: FileText, perms: ["records.manage"], group: "Content" },
  { to: "/admin/news", label: "News", icon: Newspaper, perms: ["news.manage"], group: "Content" },
  { to: "/admin/events", label: "Events", icon: CalendarDays, perms: ["events.manage"], group: "Content" },
  { to: "/admin/announcements", label: "Announcements", icon: Megaphone, perms: ["announcements.manage"], group: "Content" },
  { to: "/admin/councils", label: "Area Councils", icon: MapPin, perms: ["councils.manage"], group: "Content" },
  { to: "/admin/moderation", label: "Moderation", icon: ShieldAlert, perms: ["moderation.manage"], group: "Community" },
  { to: "/admin/messages", label: "Contact inbox", icon: Inbox, perms: ["members.view"], group: "Community" },
  { to: "/admin/admins", label: "Admins & roles", icon: UserCog, perms: ["admins.manage"], group: "System" },
  { to: "/admin/audit", label: "Audit log", icon: History, perms: ["audit.view"], group: "System" },
];

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { user, can, logout } = useAuth();
  const navigate = useNavigate();
  const items = NAV.filter((n) => n.perms.some(can));
  let lastGroup: string | undefined;
  return (
    <div className="flex h-full flex-col bg-navy-900 text-navy-100">
      <div className="flex items-center gap-2 p-5">
        <Link to="/admin" onClick={onNavigate}><Logo tone="dark" /></Link>
        <span className="ml-auto rounded-md bg-green-600 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">Admin</span>
      </div>
      <nav aria-label="Admin" className="flex-1 space-y-0.5 overflow-y-auto px-3 pb-4">
        {items.map((n) => {
          const header = n.group && n.group !== lastGroup ? n.group : null;
          lastGroup = n.group;
          return (
            <div key={n.to}>
              {header && <p className="px-3 pb-1.5 pt-5 text-[10px] font-bold uppercase tracking-[0.16em] text-navy-300">{header}</p>}
              <NavLink
                to={n.to}
                end={n.end}
                onClick={onNavigate}
                className={({ isActive }) => cn("flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition", isActive ? "bg-white/10 text-white" : "text-navy-200 hover:bg-white/5 hover:text-white")}
              >
                {({ isActive }) => (
                  <>
                    <n.icon className={cn("size-[18px]", isActive ? "text-green-400" : "")} /> {n.label}
                  </>
                )}
              </NavLink>
            </div>
          );
        })}
      </nav>
      <div className="border-t border-white/10 p-4">
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-lg bg-green-600 text-sm font-bold text-white">{initials(user?.full_name)}</span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-white">{user?.full_name}</p>
            <p className="truncate text-xs text-navy-300">{user?.admin?.role_name}{user?.admin?.area_council ? ` · ${user.admin.area_council.short_name}` : ""}</p>
          </div>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <Link to="/" className="flex items-center justify-center gap-1.5 rounded-lg bg-white/5 py-2 text-xs font-semibold text-navy-100 hover:bg-white/10"><ExternalLink className="size-3.5" /> View site</Link>
          <button onClick={async () => { await logout(); navigate("/"); }} className="flex items-center justify-center gap-1.5 rounded-lg bg-white/5 py-2 text-xs font-semibold text-navy-100 hover:bg-white/10"><LogOut className="size-3.5" /> Log out</button>
        </div>
      </div>
    </div>
  );
}

function Home() {
  const { can } = useAuth();
  const first = NAV.find((n) => n.perms.some(can));
  if (!first) return <p className="p-8 text-muted-foreground">Your admin role has no sections assigned.</p>;
  if (first.to === "/admin") return <Overview />;
  return <Navigate to={first.to} replace />;
}

export default function AdminApp() {
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-dvh bg-surface lg:grid lg:grid-cols-[260px_1fr]">
      <Seo title="Admin" noindex />
      <a href="#admin-main" className="skip-link">Skip to content</a>
      <aside className="sticky top-0 hidden h-dvh lg:block"><Sidebar /></aside>
      <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-white px-4 lg:hidden">
        <button onClick={() => setOpen(true)} aria-label="Open admin menu" className="rounded-lg p-2 text-navy hover:bg-navy-50"><Menu className="size-5" /></button>
        <Logo />
        <span className="rounded-md bg-green-600 px-2 py-0.5 text-[10px] font-bold uppercase text-white">Admin</span>
      </header>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent side="left" className="p-0 [&>button]:text-white" aria-describedby={undefined}>
          <DialogTitle className="sr-only">Admin menu</DialogTitle>
          <Sidebar onNavigate={() => setOpen(false)} />
        </DialogContent>
      </Dialog>
      <main id="admin-main" className="min-w-0 p-4 sm:p-6 lg:p-8">
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route index element={<Home />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="members" element={<Members />} />
            <Route path="records/*" element={<Records />} />
            <Route path="news/*" element={<NewsAdmin />} />
            <Route path="events/*" element={<EventsAdmin />} />
            <Route path="announcements" element={<Announcements />} />
            <Route path="councils" element={<Councils />} />
            <Route path="moderation" element={<Moderation />} />
            <Route path="messages" element={<Messages />} />
            <Route path="admins" element={<Admins />} />
            <Route path="audit" element={<Audit />} />
            <Route path="*" element={<Navigate to="/admin" replace />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}
