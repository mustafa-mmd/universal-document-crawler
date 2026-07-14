import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return <main className="flex min-h-screen flex-col items-center justify-center bg-background p-6 text-center"><div className="font-mono text-sm text-primary">404</div><h1 className="mt-3 text-3xl font-semibold">Page not found</h1><p className="mt-2 text-sm text-muted-foreground">The requested UDC Pro page does not exist.</p><Link href="/dashboard" className={`${buttonVariants()} mt-6`}>Return to overview</Link></main>;
}
