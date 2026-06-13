/**
 * Placeholder home page.
 *
 * Demonstrates that Tailwind reads from @smartinv/tokens — no raw hex,
 * only token-backed utility classes. The real UI shell ships in CV1.E3.
 */
export default function HomePage() {
  return (
    <main className="mx-auto max-w-3xl px-8 py-24 bg-surface text-ink font-body">
      <h1 className="text-3xl font-bold font-display tracking-tight text-ink">SmartInv</h1>
      <p className="mt-2 text-base text-ink-2">AI-Powered MRO Inventory Intelligence Platform.</p>
      <p className="mt-12 text-sm text-ink-3">Placeholder home. Real shell ships in CV1.E3.</p>
      <div className="mt-12 inline-flex items-center gap-2 rounded-md bg-ai-soft px-3 py-1 text-sm font-semibold text-ai">
        violet = AI-generated content
      </div>
    </main>
  );
}
