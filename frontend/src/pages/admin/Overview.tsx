import { useQuery } from "@tanstack/react-query";
import { Activity, BadgeCheck, CalendarCheck, Eye, FileText, Flag, MessageSquare, UserPlus, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ErrorState } from "@/components/shared/states";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { getData } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { AdminTitle, CHART, StatCard } from "./shared";

export interface Stats {
  totals: Record<string, number>;
  by_council: { slug: string; name: string; members: number }[];
  registration_trend: { date: string; registrations: number }[];
  membership_growth: { month: string; members: number }[];
}

export function ChartCard({ title, description, children, className }: { title: string; description?: string; children: React.ReactNode; className?: string }) {
  return (
    <section className={`rounded-2xl border border-border bg-white p-5 shadow-card ${className ?? ""}`}>
      <h2 className="text-base font-bold">{title}</h2>
      {description && <p className="text-xs text-muted-foreground">{description}</p>}
      <div className="mt-4 h-64">{children}</div>
    </section>
  );
}

const tooltipStyle = { borderRadius: 12, border: "1px solid #E3E8EC", fontSize: 12, boxShadow: "0 8px 24px -8px rgba(6,59,102,.2)" };
export { tooltipStyle };

export default function Overview() {
  const { user } = useAuth();
  const { data, error, refetch } = useQuery({ queryKey: ["admin", "stats"], queryFn: () => getData<Stats>("/api/admin/stats") });
  if (error) return <ErrorState error={error} onRetry={() => refetch()} />;
  const t = data?.totals;
  const month = (m: string) => new Date(`${m}-01T12:00:00Z`).toLocaleDateString("en-NG", { month: "short" });

  return (
    <>
      <AdminTitle title={`Welcome, ${user?.first_name}`} description="Platform overview. Figures are aggregate; individual members' activity is not tracked." />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total members" value={t?.members} icon={Users} tone="navy" />
        <StatCard label="Verified members" value={t?.verified_members} hint={t ? `${t.members ? Math.round((t.verified_members / t.members) * 100) : 0}% of members` : undefined} icon={BadgeCheck} tone="green" />
        <StatCard label="New registrations" value={t?.new_registrations_30d} hint={t ? `${t.new_registrations_7d} in the last 7 days` : undefined} icon={UserPlus} />
        <StatCard label="Active users (30 days)" value={t?.active_users_30d} icon={Activity} />
        <StatCard label="Event registrations" value={t?.event_registrations} icon={CalendarCheck} />
        <StatCard label="News views" value={t?.news_views} icon={Eye} />
        <StatCard label="Record views" value={t?.record_views} icon={FileText} />
        <StatCard label="Discussions" value={t?.discussions} hint={t ? `${t.comments_30d} comments in 30 days` : undefined} icon={MessageSquare} />
      </div>
      {t && t.open_reports > 0 && (
        <Link to="/admin/moderation" className="mt-4 flex items-center gap-3 rounded-2xl bg-amber-50 p-4 text-sm text-amber-900 ring-1 ring-amber-200 hover:ring-amber-400">
          <Flag className="size-5 text-amber-600" /> <strong>{t.open_reports}</strong> open report{t.open_reports > 1 ? "s" : ""} awaiting moderation →
        </Link>
      )}
      {!data ? (
        <div className="mt-6 grid gap-6 lg:grid-cols-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-80" />)}</div>
      ) : (
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <ChartCard title="Membership growth" description="Total members, last 12 months">
            <ResponsiveContainer>
              <AreaChart data={data.membership_growth} margin={{ left: -16, right: 8, top: 8 }}>
                <defs>
                  <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={CHART.navy} stopOpacity={0.25} /><stop offset="1" stopColor={CHART.navy} stopOpacity={0} /></linearGradient>
                </defs>
                <CartesianGrid stroke={CHART.grid} vertical={false} />
                <XAxis dataKey="month" tickFormatter={month} tick={{ fontSize: 12, fill: "#5B6670" }} axisLine={false} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#5B6670" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} labelFormatter={(m) => month(String(m))} />
                <Area type="monotone" dataKey="members" name="Members" stroke={CHART.navy} strokeWidth={2.5} fill="url(#g1)" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
          <ChartCard title="Area Council distribution" description="Members by self-declared Area Council">
            <ResponsiveContainer>
              <BarChart data={data.by_council} margin={{ left: -16, right: 8, top: 8 }}>
                <CartesianGrid stroke={CHART.grid} vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#5B6670" }} axisLine={false} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#5B6670" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#F5F8F7" }} />
                <Bar dataKey="members" name="Members" radius={[8, 8, 0, 0]}>
                  {data.by_council.map((_, i) => <Cell key={i} fill={i % 2 ? CHART.green : CHART.navy} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
          <ChartCard title="Registration trends" description="New registrations per day, last 30 days" className="lg:col-span-2">
            <ResponsiveContainer>
              <LineChart data={data.registration_trend} margin={{ left: -16, right: 8, top: 8 }}>
                <CartesianGrid stroke={CHART.grid} vertical={false} />
                <XAxis dataKey="date" tickFormatter={(d) => formatDate(d, { day: "numeric", month: "short" })} tick={{ fontSize: 12, fill: "#5B6670" }} axisLine={false} tickLine={false} minTickGap={24} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#5B6670" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} labelFormatter={(d) => formatDate(String(d))} />
                <Line type="monotone" dataKey="registrations" name="Registrations" stroke={CHART.green} strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      )}
    </>
  );
}
