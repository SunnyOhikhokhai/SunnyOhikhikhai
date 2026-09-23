import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ErrorState } from "@/components/shared/states";
import { Select } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { getData } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { ChartCard, tooltipStyle } from "./Overview";
import { AdminTitle, CHART } from "./shared";

interface AnalyticsData {
  engagement: { date: string; project: number; news: number; event: number }[];
  community: { date: string; discussions: number; comments: number; event_registrations: number }[];
  popular_records: { title: string; slug: string; views: number }[];
  popular_news: { title: string; slug: string; views: number }[];
  top_events: { title: string; slug: string; registrations: number }[];
}

function TopList({ title, rows, to, unit }: { title: string; rows: { title: string; slug: string; n: number }[]; to: string; unit: string }) {
  const max = Math.max(1, ...rows.map((r) => r.n));
  return (
    <section className="rounded-2xl border border-border bg-white p-5 shadow-card">
      <h2 className="text-base font-bold">{title}</h2>
      {rows.length ? (
        <ol className="mt-4 space-y-3">
          {rows.map((r, i) => (
            <li key={r.slug}>
              <div className="flex justify-between gap-3 text-sm">
                <Link to={`${to}/${r.slug}`} className="truncate font-medium text-navy hover:text-green-600">{i + 1}. {r.title}</Link>
                <span className="shrink-0 text-slate-500">{r.n.toLocaleString()} {unit}</span>
              </div>
              <div className="mt-1.5 h-1.5 rounded-full bg-surface"><div className="h-full rounded-full bg-green-500" style={{ width: `${(r.n / max) * 100}%` }} /></div>
            </li>
          ))}
        </ol>
      ) : <p className="mt-4 text-sm text-muted-foreground">No data yet.</p>}
    </section>
  );
}

export default function Analytics() {
  const [days, setDays] = useState(30);
  const { data, error, refetch } = useQuery({ queryKey: ["admin", "analytics", days], queryFn: () => getData<AnalyticsData>("/api/admin/analytics", { days }) });
  const tick = (d: string) => formatDate(d, { day: "numeric", month: "short" });
  return (
    <>
      <AdminTitle
        title="Analytics"
        description="Aggregate engagement across content and community. No individual reading activity is recorded."
        actions={
          <Select value={days} onChange={(e) => setDays(Number(e.target.value))} className="h-10 w-40" aria-label="Period">
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last 12 months</option>
          </Select>
        }
      />
      {error ? <ErrorState error={error} onRetry={() => refetch()} /> : !data ? (
        <div className="grid gap-6 lg:grid-cols-2">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-80" />)}</div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <ChartCard title="Content engagement" description="Daily views by content type" className="lg:col-span-2">
            <ResponsiveContainer>
              <LineChart data={data.engagement} margin={{ left: -16, right: 8, top: 8 }}>
                <CartesianGrid stroke={CHART.grid} vertical={false} />
                <XAxis dataKey="date" tickFormatter={tick} tick={{ fontSize: 12, fill: "#5B6670" }} axisLine={false} tickLine={false} minTickGap={24} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#5B6670" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} labelFormatter={(d) => formatDate(String(d))} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line dataKey="project" name="Records" stroke={CHART.navy} strokeWidth={2.5} dot={false} />
                <Line dataKey="news" name="News" stroke={CHART.green} strokeWidth={2.5} dot={false} />
                <Line dataKey="event" name="Events" stroke={CHART.sky} strokeWidth={2.5} dot={false} strokeDasharray="5 4" />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
          <ChartCard title="Community activity" description="Discussions, comments and event registrations per day" className="lg:col-span-2">
            <ResponsiveContainer>
              <BarChart data={data.community} margin={{ left: -16, right: 8, top: 8 }}>
                <CartesianGrid stroke={CHART.grid} vertical={false} />
                <XAxis dataKey="date" tickFormatter={tick} tick={{ fontSize: 12, fill: "#5B6670" }} axisLine={false} tickLine={false} minTickGap={24} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#5B6670" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} labelFormatter={(d) => formatDate(String(d))} cursor={{ fill: "#F5F8F7" }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="discussions" name="Discussions" stackId="a" fill={CHART.navy} />
                <Bar dataKey="comments" name="Comments" stackId="a" fill={CHART.green} />
                <Bar dataKey="event_registrations" name="Event registrations" stackId="a" fill={CHART.silver} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
          <TopList title="Popular records" to="/our-record" unit="views" rows={data.popular_records.map((r) => ({ ...r, n: r.views }))} />
          <TopList title="Popular news" to="/news" unit="views" rows={data.popular_news.map((r) => ({ ...r, n: r.views }))} />
          <TopList title="Events by registrations" to="/events" unit="registered" rows={data.top_events.map((r) => ({ ...r, n: r.registrations }))} />
        </div>
      )}
    </>
  );
}
