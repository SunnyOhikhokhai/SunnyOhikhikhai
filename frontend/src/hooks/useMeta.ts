import { useQuery } from "@tanstack/react-query";
import { getData } from "@/lib/api";
import type { Meta } from "@/lib/types";

export function useMeta() {
  return useQuery({ queryKey: ["meta"], queryFn: () => getData<Meta>("/api/meta"), staleTime: 10 * 60_000 });
}
