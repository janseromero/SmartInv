/**
 * Placeholder home page.
 *
 * Intentionally minimal: no colors, no design tokens — those land in the
 * tokens / Tailwind / UI shell tasks (E1.2 → E1.3 → E1.4).
 */
export default function HomePage() {
  return (
    <main className="mx-auto max-w-3xl px-8 py-24">
      <h1 className="text-3xl font-bold tracking-tight">SmartInv</h1>
      <p className="mt-2 text-base">AI-Powered MRO Inventory Intelligence Platform.</p>
      <p className="mt-12 text-sm">Placeholder home. Real shell ships in task E1.4.</p>
    </main>
  );
}
