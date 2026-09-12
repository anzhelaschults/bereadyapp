import type { Metadata } from "next";
import Link from "next/link";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "./globals.css";
export const metadata: Metadata = { title: "BeReady", description: "Practical trail preparation guidance." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body><nav aria-label="Main navigation"><Link className="brand" href="/quickcheck">BeReady</Link><div><Link href="/discover">Discover</Link><Link href="/workspace">Workspace</Link><Link href="/pricing">Pricing</Link></div></nav>{children}<footer><Link href="/privacy">Privacy</Link><span>Preparation guidance, not mountain-safety clearance.</span></footer></body></html>; }
