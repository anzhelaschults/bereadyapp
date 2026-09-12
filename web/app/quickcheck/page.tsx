import { QuickCheck } from "../../components/QuickCheck";
export default async function QuickCheckPage({ searchParams }: { searchParams: Promise<{ trail?: string }> }) { const { trail } = await searchParams; return <QuickCheck initialTrail={trail} />; }
