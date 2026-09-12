import { forwardPolicy } from "@/lib/public-api";

export const dynamic = "force-dynamic";
export function POST(request: Request) {
  return forwardPolicy(request, "plan");
}
