import { cn } from "@/lib/utils";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
      <h1 className={cn("text-4xl font-semibold tracking-tight text-brand")}>
        Sheepper
      </h1>
      <p className="text-lg text-muted">L&apos;app è in costruzione.</p>
    </main>
  );
}
