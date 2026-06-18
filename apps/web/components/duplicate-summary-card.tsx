'use client';

import { fetchDuplicateSummary, fetchDuplicates } from '@/lib/api';
import { Badge } from '@smartinv/ui-web';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';

const integer = new Intl.NumberFormat('en-US');

/**
 * Compact duplicate-detection summary for the Inventory Health sidebar
 * (mirrors the reference UI). The full review queue lives at /duplicates.
 */
export function DuplicateSummaryCard() {
  const summary = useQuery({ queryKey: ['dup-summary'], queryFn: fetchDuplicateSummary });
  const top = useQuery({
    queryKey: ['dup-top'],
    queryFn: () => fetchDuplicates({ page: 1, page_size: 1, band: 'probable' }),
  });

  const probable = summary.data?.probable;
  const pair = top.data?.candidates[0];

  return (
    <section className="rounded-md border border-line bg-card shadow-card overflow-hidden">
      <header className="flex items-center gap-2 px-md py-2.5 border-b border-line">
        <h3 className="font-display text-sm text-ink">Duplicate detection</h3>
        <Badge label="AI" variant="ai" />
      </header>

      <div className="p-md flex flex-col gap-3">
        <div className="flex items-baseline gap-2">
          <span className="font-display text-2xl text-ink">
            {probable !== undefined ? integer.format(probable) : '—'}
          </span>
          <span className="text-xs text-ink-2">probable duplicate pairs</span>
        </div>

        {pair ? (
          <div className="rounded-md border border-line p-md text-xs">
            <div className="flex items-center justify-between mb-1.5">
              <span className="font-mono text-ink">{pair.item_a.item_number}</span>
              <Badge label={`${Math.round(pair.confidence * 100)}% match`} variant="ai" />
            </div>
            <div className="text-ink-2 truncate">{pair.item_a.description ?? '—'}</div>
            <div className="text-ink-3 truncate">↔ {pair.item_b.description ?? '—'}</div>
          </div>
        ) : null}

        <Link
          href="/duplicates"
          className="rounded-md border border-line px-md py-1.5 text-sm text-ink-2 text-center hover:bg-surface"
        >
          Review in queue
        </Link>
      </div>
    </section>
  );
}
