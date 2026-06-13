import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen grid place-items-center px-8 bg-surface text-ink">
      <div className="text-center">
        <p className="font-mono text-xs uppercase tracking-widest text-ink-3">404</p>
        <h1 className="font-display text-2xl font-semibold mt-2">Page not found</h1>
        <p className="text-sm text-ink-2 mt-2 max-w-sm mx-auto">
          The screen you were looking for does not exist in this build of SmartInv.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 mt-6 px-3 py-1.5 rounded-md bg-teal text-white text-sm font-semibold hover:bg-teal-dark"
        >
          Back to overview
        </Link>
      </div>
    </div>
  );
}
