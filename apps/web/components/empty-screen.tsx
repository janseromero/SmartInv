interface EmptyScreenProps {
  shipsIn?: string;
}

/**
 * Placeholder body for every CV1.E3 screen — until the owning CV ships its
 * real content. Centered card with the CV pointer so the team knows where
 * to look.
 */
export function EmptyScreen({ shipsIn }: EmptyScreenProps) {
  return (
    <div className="rounded-md border border-line bg-card p-xl text-center shadow-card">
      <p className="text-sm text-ink-2">Placeholder screen — UI shell only.</p>
      {shipsIn ? (
        <p className="text-sm text-ink-3 mt-2">
          Real content ships in <span className="font-mono text-ink">{shipsIn}</span>.
        </p>
      ) : null}
    </div>
  );
}
