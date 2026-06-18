'use client';

import {
  type DuplicateCandidate,
  type DuplicateDecision,
  type DuplicateItemSide,
  fetchDuplicateDetail,
  fetchDuplicateSummary,
  fetchDuplicates,
  reviewDuplicate,
} from '@/lib/api';
import { Badge, ConfidenceMeter, KpiCard } from '@smartinv/ui-web';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

const PAGE_SIZE = 25;
const integer = new Intl.NumberFormat('en-US');
const currency = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

const BANDS = [
  { value: '', label: 'All bands' },
  { value: 'probable', label: 'Probable' },
  { value: 'possible', label: 'Possible' },
];

const STATUSES = [
  { value: 'open', label: 'Open' },
  { value: 'merged', label: 'Merged' },
  { value: 'not_duplicate', label: 'Not duplicate' },
  { value: 'hold', label: 'On hold' },
];

const FEATURE_LABELS: Record<string, string> = {
  description: 'Description',
  manufacturer: 'Manufacturer part',
  uom: 'Unit of measure',
  item_type: 'Item type',
  unit_cost: 'Unit cost',
};

function bandTone(band: string): 'crit' | 'warn' {
  return band === 'probable' ? 'crit' : 'warn';
}

export function DuplicateQueue() {
  const [band, setBand] = useState('');
  const [status, setStatus] = useState('open');
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<string | null>(null);

  const summary = useQuery({ queryKey: ['dup-summary'], queryFn: fetchDuplicateSummary });
  const candidates = useQuery({
    queryKey: ['duplicates', { band, status, page }],
    queryFn: () =>
      fetchDuplicates({
        page,
        page_size: PAGE_SIZE,
        band: band || undefined,
        candidate_status: status || undefined,
      }),
  });

  const totalPages = candidates.data
    ? Math.max(1, Math.ceil(candidates.data.total / PAGE_SIZE))
    : 1;
  const s = summary.data;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard label="Open candidates" value={s ? integer.format(s.open) : '—'} />
        <KpiCard
          label="Probable"
          value={s ? integer.format(s.probable) : '—'}
          status={s && s.probable > 0 ? 'crit' : 'ok'}
        />
        <KpiCard
          label="Possible"
          value={s ? integer.format(s.possible) : '—'}
          status={s && s.possible > 0 ? 'warn' : 'ok'}
        />
        <KpiCard label="Resolved" value={s ? integer.format(s.resolved) : '—'} />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Badge label="AI · model-generated" variant="ai" />
        <span className="text-xs text-ink-3">
          Pairs are scored by the deterministic dedup engine. A merge is only a proposal — it routes
          through approval, never a direct merge.
        </span>
        <span className="flex-1" />
        <select
          value={band}
          onChange={(e) => {
            setBand(e.target.value);
            setPage(1);
          }}
          className="bg-card border border-line rounded-md px-md py-1.5 text-sm text-ink"
        >
          {BANDS.map((b) => (
            <option key={b.value} value={b.value}>
              {b.label}
            </option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
          className="bg-card border border-line rounded-md px-md py-1.5 text-sm text-ink"
        >
          {STATUSES.map((st) => (
            <option key={st.value} value={st.value}>
              {st.label}
            </option>
          ))}
        </select>
      </div>

      <div className="rounded-md border border-line bg-card shadow-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-ink-3 border-b border-line">
              <th className="font-normal px-md py-2">Item A</th>
              <th className="font-normal px-md py-2">Item B</th>
              <th className="font-normal px-md py-2">Band</th>
              <th className="font-normal px-md py-2 text-right">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {candidates.data?.candidates.map((c: DuplicateCandidate) => (
              <tr
                key={c.id}
                onClick={() => setSelected(c.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') setSelected(c.id);
                }}
                tabIndex={0}
                className="border-b border-line hover:bg-surface cursor-pointer"
              >
                <td className="px-md py-2">
                  <div className="font-mono text-ink">{c.item_a.item_number}</div>
                  <div className="text-ink-3 truncate max-w-[260px]">
                    {c.item_a.description ?? '—'}
                  </div>
                </td>
                <td className="px-md py-2">
                  <div className="font-mono text-ink">{c.item_b.item_number}</div>
                  <div className="text-ink-3 truncate max-w-[260px]">
                    {c.item_b.description ?? '—'}
                  </div>
                </td>
                <td className="px-md py-2">
                  <Badge label={c.band} variant="status" tone={bandTone(c.band)} />
                </td>
                <td className="px-md py-2 text-right font-mono text-ai">
                  {Math.round(c.confidence * 100)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {candidates.isLoading ? <div className="p-md text-sm text-ink-3">Loading…</div> : null}
        {candidates.data && candidates.data.candidates.length === 0 ? (
          <div className="p-md text-sm text-ink-3">No candidates match these filters.</div>
        ) : null}
      </div>

      <div className="flex items-center justify-between text-sm text-ink-2">
        <span>{candidates.data ? `${integer.format(candidates.data.total)} candidates` : ''}</span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="rounded-md border border-line px-md py-1 disabled:opacity-50"
          >
            Prev
          </button>
          <span>
            Page {page} / {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="rounded-md border border-line px-md py-1 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>

      {selected ? <CompareDrawer candidateId={selected} onClose={() => setSelected(null)} /> : null}
    </div>
  );
}

function SideColumn({ item, label }: { item: DuplicateItemSide; label: string }) {
  return (
    <div className="flex-1 rounded-md border border-line p-md">
      <div className="text-[10px] uppercase tracking-wide text-ink-3">{label}</div>
      <div className="font-mono text-ink">{item.item_number}</div>
      <div className="text-sm text-ink-2">{item.description ?? '—'}</div>
      <dl className="mt-2 text-xs text-ink-3 flex flex-col gap-1">
        <div className="flex justify-between">
          <dt>Type</dt>
          <dd className="text-ink-2">{item.item_type ?? '—'}</dd>
        </div>
        <div className="flex justify-between">
          <dt>UoM</dt>
          <dd className="text-ink-2">{item.uom ?? '—'}</dd>
        </div>
        <div className="flex justify-between">
          <dt>Unit cost</dt>
          <dd className="text-ink-2">
            {item.unit_cost !== null ? currency.format(item.unit_cost) : '—'}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt>Health</dt>
          <dd className="text-ink-2">{item.health_score ?? '—'}</dd>
        </div>
      </dl>
    </div>
  );
}

function CompareDrawer({ candidateId, onClose }: { candidateId: string; onClose: () => void }) {
  const queryClient = useQueryClient();
  const detail = useQuery({
    queryKey: ['duplicate', candidateId],
    queryFn: () => fetchDuplicateDetail(candidateId),
  });
  const [error, setError] = useState<string | null>(null);

  const review = useMutation({
    mutationFn: ({ decision, keepItemId }: { decision: DuplicateDecision; keepItemId?: string }) =>
      reviewDuplicate(candidateId, decision, keepItemId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['duplicates'] });
      void queryClient.invalidateQueries({ queryKey: ['dup-summary'] });
      onClose();
    },
    onError: () => setError('Review failed (planner or admin role required).'),
  });

  const d = detail.data;
  const open = d?.status === 'open';

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button type="button" aria-label="Close" onClick={onClose} className="flex-1 bg-ink/[0.25]" />
      <aside className="w-[560px] max-w-full h-full bg-card border-l border-line overflow-y-auto p-lg flex flex-col gap-4">
        {!d ? (
          <p className="text-sm text-ink-3">Loading…</p>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <div className="font-display text-lg text-ink">Compare pair</div>
              <Badge label={`AI · ${d.model_version}`} variant="ai" />
            </div>

            <ConfidenceMeter
              value={d.confidence}
              label={`Match confidence (${d.band})`}
              showBands
            />

            <div className="flex gap-3">
              <SideColumn item={d.item_a} label="Item A" />
              <SideColumn item={d.item_b} label="Item B" />
            </div>

            <div>
              <h3 className="text-sm font-medium text-ink-2 mb-1">Why this match</h3>
              <div className="flex flex-col gap-1">
                {Object.entries(d.features)
                  .sort(([, a], [, b]) => b - a)
                  .map(([k, v]) => (
                    <div key={k} className="flex items-center gap-2 text-xs">
                      <span className="w-32 text-ink-3">{FEATURE_LABELS[k] ?? k}</span>
                      <span className="flex-1 h-1.5 rounded-pill bg-line overflow-hidden">
                        <span
                          className="block h-full bg-ai"
                          style={{ width: `${Math.round(v * 100)}%` }}
                        />
                      </span>
                      <span className="w-10 text-right font-mono text-ink-2">
                        {Math.round(v * 100)}%
                      </span>
                    </div>
                  ))}
              </div>
            </div>

            {error ? <p className="text-sm text-crit">{error}</p> : null}

            {open ? (
              <div className="mt-auto flex flex-col gap-2">
                <div className="text-xs text-ink-3">
                  Merging proposes an approval action — it never edits source records directly.
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={review.isPending}
                    onClick={() => review.mutate({ decision: 'merge', keepItemId: d.item_a.id })}
                    className="flex-1 rounded-md bg-ai text-white px-md py-1.5 text-sm disabled:opacity-50"
                  >
                    Merge → keep A
                  </button>
                  <button
                    type="button"
                    disabled={review.isPending}
                    onClick={() => review.mutate({ decision: 'merge', keepItemId: d.item_b.id })}
                    className="flex-1 rounded-md bg-ai text-white px-md py-1.5 text-sm disabled:opacity-50"
                  >
                    Merge → keep B
                  </button>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={review.isPending}
                    onClick={() => review.mutate({ decision: 'not_duplicate' })}
                    className="flex-1 rounded-md border border-line px-md py-1.5 text-sm text-ink-2 disabled:opacity-50"
                  >
                    Not a duplicate
                  </button>
                  <button
                    type="button"
                    disabled={review.isPending}
                    onClick={() => review.mutate({ decision: 'hold' })}
                    className="flex-1 rounded-md border border-line px-md py-1.5 text-sm text-ink-2 disabled:opacity-50"
                  >
                    Hold
                  </button>
                </div>
              </div>
            ) : (
              <div className="mt-auto rounded-md border border-line p-md text-sm text-ink-2">
                This pair was resolved as <span className="font-medium">{d.status}</span>.
              </div>
            )}

            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-line px-md py-1.5 text-sm text-ink-2"
            >
              Close
            </button>
          </>
        )}
      </aside>
    </div>
  );
}
