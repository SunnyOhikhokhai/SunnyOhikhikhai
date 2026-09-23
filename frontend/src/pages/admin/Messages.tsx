import { useState } from "react";
import { formatDateTime } from "@/lib/utils";
import { AdminTitle, DataTable, useAdminList } from "./shared";

interface Msg { id: number; name: string; email: string; subject: string; message: string; status: string; created_at: string }

export default function Messages() {
  const [page, setPage] = useState(1);
  const { data, isLoading, error, refetch } = useAdminList<Msg>("messages", "/api/admin/contact-messages", { page });
  return (
    <>
      <AdminTitle title="Contact inbox" description="Messages sent through the public contact form." />
      <DataTable
        rows={data?.data}
        loading={isLoading}
        error={error}
        onRetry={() => refetch()}
        page={page}
        totalPages={data?.meta.total_pages}
        onPage={setPage}
        empty="No messages yet"
        columns={[
          { header: "Received", cell: (m) => <span className="whitespace-nowrap">{formatDateTime(m.created_at)}</span> },
          { header: "From", cell: (m) => <span><span className="font-semibold text-navy">{m.name}</span><br /><a href={`mailto:${m.email}`} className="text-xs text-green-600">{m.email}</a></span> },
          { header: "Subject", cell: (m) => m.subject },
          { header: "Message", cell: (m) => <p className="max-w-md whitespace-pre-line text-sm text-slate-600">{m.message}</p> },
        ]}
      />
    </>
  );
}
