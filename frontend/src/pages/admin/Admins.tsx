import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { UserMinus, UserPlus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useConfirm } from "@/components/ui/confirm";
import { Input, Select } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { useMeta } from "@/hooks/useMeta";
import { api, getData } from "@/lib/api";
import type { CouncilRef } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { FormSection } from "./editor-kit";
import { AdminTitle, DataTable } from "./shared";

interface Role { code: string; name: string; description: string; scoped: boolean; permissions: string[] }
interface AdminRow { user_id: number; name: string; email: string; role: string; role_name: string; area_council: CouncilRef | null; since: string }

export default function Admins() {
  const { user } = useAuth();
  const meta = useMeta();
  const qc = useQueryClient();
  const confirm = useConfirm();
  const roles = useQuery({ queryKey: ["admin", "roles"], queryFn: () => getData<Role[]>("/api/admin/roles") });
  const admins = useQuery({ queryKey: ["admin", "admins"], queryFn: () => getData<AdminRow[]>("/api/admin/admins") });
  const [f, setF] = useState({ email: "", role: "content_admin", area_council: "" });
  const scoped = roles.data?.find((r) => r.code === f.role)?.scoped;
  const assign = useMutation({
    mutationFn: () => api.post("/api/admin/admins", { ...f, area_council: scoped ? f.area_council : null }),
    onSuccess: () => { toast.success("Role assigned"); setF({ ...f, email: "" }); qc.invalidateQueries({ queryKey: ["admin", "admins"] }); },
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <>
      <AdminTitle title="Admins & roles" description="Role-based access control. Assign roles to verified member accounts." />
      <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
        <DataTable
          rows={admins.data?.map((a) => ({ ...a, id: a.user_id }))}
          loading={admins.isLoading}
          error={admins.error}
          columns={[
            { header: "Name", cell: (a) => <span className="font-semibold text-navy">{a.name}</span> },
            { header: "Email", cell: (a) => a.email },
            { header: "Role", cell: (a) => <Badge variant={a.role === "super_admin" ? "navy" : "default"}>{a.role_name}{a.area_council ? ` · ${a.area_council.short_name}` : ""}</Badge> },
            { header: "Since", cell: (a) => formatDate(a.since) },
            {
              header: "",
              className: "text-right",
              cell: (a) => a.user_id !== user?.id && (
                <Button size="sm" variant="ghost" className="text-red-600" onClick={async () => {
                  if (await confirm({ title: `Remove ${a.name}'s admin role?`, confirmLabel: "Remove role", destructive: true })) {
                    await api.del(`/api/admin/admins/${a.user_id}`);
                    qc.invalidateQueries({ queryKey: ["admin", "admins"] });
                    toast.success("Role removed");
                  }
                }}><UserMinus /> Revoke</Button>
              ),
            },
          ]}
        />
        <div className="space-y-6">
          <FormSection title="Assign a role" description="The person must already have a verified NIPAM account.">
            <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); assign.mutate(); }}>
              <Field id="ad-email" label="Member email"><Input type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} required /></Field>
              <Field id="ad-role" label="Role"><Select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}>{roles.data?.map((r) => <option key={r.code} value={r.code}>{r.name}</option>)}</Select></Field>
              {scoped && <Field id="ad-council" label="Assigned Area Council"><Select value={f.area_council} onChange={(e) => setF({ ...f, area_council: e.target.value })} required><option value="">Choose…</option>{meta.data?.area_councils.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}</Select></Field>}
              <Button type="submit" loading={assign.isPending}><UserPlus /> Assign role</Button>
            </form>
          </FormSection>
          <FormSection title="Role permissions">
            <ul className="space-y-4">
              {roles.data?.map((r) => (
                <li key={r.code}>
                  <p className="text-sm font-bold text-navy">{r.name}</p>
                  <p className="text-xs text-muted-foreground">{r.description}</p>
                  <div className="mt-1.5 flex flex-wrap gap-1">{r.permissions.map((p) => <code key={p} className="rounded bg-surface px-1.5 py-0.5 text-[11px] text-slate-600 ring-1 ring-border">{p}</code>)}</div>
                </li>
              ))}
            </ul>
          </FormSection>
        </div>
      </div>
    </>
  );
}
