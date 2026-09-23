import { Compass } from "lucide-react";
import { Link } from "react-router-dom";
import { Seo } from "@/components/shared/Seo";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <section className="container flex min-h-[60vh] flex-col items-center justify-center py-20 text-center">
      <Seo title="Page not found" noindex />
      <div className="flex size-16 items-center justify-center rounded-2xl bg-navy-50 text-navy">
        <Compass className="size-8" />
      </div>
      <p className="eyebrow mt-6">Error 404</p>
      <h1 className="mt-2 text-4xl font-extrabold">We couldn't find that page</h1>
      <p className="mt-3 max-w-md text-muted-foreground">The link may be out of date, or the content may have been moved or unpublished.</p>
      <div className="mt-8 flex gap-3">
        <Button asChild><Link to="/">Back to home</Link></Button>
        <Button asChild variant="outline"><Link to="/search">Search NIPAM</Link></Button>
      </div>
    </section>
  );
}
