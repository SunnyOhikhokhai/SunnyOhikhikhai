import { useQuery } from "@tanstack/react-query";
import { CouncilCard } from "@/components/shared/cards";
import { FctMap } from "@/components/shared/FctMap";
import { PageHeader, SectionHeading } from "@/components/shared/PageHeader";
import { Seo } from "@/components/shared/Seo";
import { ErrorState } from "@/components/shared/states";
import { CardSkeleton, Skeleton } from "@/components/ui/skeleton";
import { getData } from "@/lib/api";
import type { Council } from "@/lib/types";

export default function AreaCouncils() {
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["councils"], queryFn: () => getData<Council[]>("/api/area-councils") });
  return (
    <>
      <Seo title="Area Councils" description="Explore the six Area Councils of the Federal Capital Territory: AMAC, Bwari, Gwagwalada, Kuje, Kwali and Abaji." />
      <PageHeader
        eyebrow="FCT Area Councils"
        title="The six Area Councils of the FCT"
        description="Select a council on the map or below to see its community updates, events, public information and records."
        crumbs={[{ to: "/", label: "Home" }, { label: "Area Councils" }]}
      />
      <section className="section">
        <div className="container">
          {error ? (
            <ErrorState error={error} onRetry={() => refetch()} />
          ) : isLoading || !data ? (
            <Skeleton className="h-[28rem]" />
          ) : (
            <FctMap councils={data} />
          )}
        </div>
      </section>
      <section className="section bg-surface pt-16">
        <div className="container">
          <SectionHeading eyebrow="All councils" title="Explore by Area Council" />
          {isLoading ? (
            <CardSkeleton count={6} />
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {data?.map((c, i) => <CouncilCard key={c.slug} council={c} index={i} />)}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
