import { forwardPolicy } from "@/lib/public-api";

export const dynamic = "force-dynamic";
export function GET(request: Request) {
  return forwardPolicy(request, "health");
}
