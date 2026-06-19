'use client';

import { DatabaseIcon, TrendIcon, TriangleAlertIcon } from '@/components/icons';
import {
  type AnomalyDecision,
  type AnomalyRow,
  fetchAnomalies,
  fetchAnomalyDetail,
  fetchAnomalySummary,
  reviewAnomaly,
} from '@/lib/api';
import { Badge, Button } from '@smartinv/ui-web';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useState } from 'react';

const WINDOW_DAYS = 7;
const MAX_ROWS = 6;
const integer = new Intl.NumberFormat('en-US');

const TYPE_LABELS: Record<string, string> = {
  consumption_spike: 'Consumption spike',
  price_jump: 'Unit-price jump',
  negative_balance: 'Negative balance',
};

/** Icon + tint per anomaly nature (mirrors the reference UI's signal dots). */
type Sig = { icon: ReactNode; cls: string };
const DEFAULT_SIG: Sig = { icon: <DatabaseIcon />, cls: 'bg-surface text-ink-2' };
const SIG: Record<string, Sig> = {
  consumption_spike: { icon: <TrendIcon />, cls: 'bg-warn-soft text-warn' },
  price_jump: { icon: <TriangleAlertIcon />, cls: 'bg-crit-soft text-crit' },
  negative_balance: DEFAULT_SIG,
};

function formatDate(iso: string | null): string {
  return iso ? iso.slice(0, 10) : '—';
}

export function AnomaliesPanel() {
  const [selected, setSelected] = useState<string | null>(null);

  const summary = useQuery({ queryKey: ['anomaly-summary'], queryFn: fetchAnomalySummary });
  const anomalies = useQuery({
    queryKey: ['anomalies', { window: WINDOW_DAYS }],
    queryFn: () => fetchAnomalies({ window_days: WINDOW_DAYS, page_size: 50 }),
  });

  const s = summary.data;
  const rows = anomalies.data?.anomalies.slice(0, MAX_ROWS) ?? [];

  return (
    <section className="rounded-md border border-line bg-card shadow-card overflow-hidden">
      <header className="flex items-center gap-2 px-md py-2.5 border-b border-line">
        <h3 className="font-display text-sm text-ink">Anomalies — last 7 days</h3>
        <Badge label="AI" variant="ai" />
        <span className="flex-1" />
        {s ? (
          <span className="text-xs text-ink-3">{integer.format(s.last_7_days)} flagged</span>
        ) : null}
      </header>

      <div className="divide-y divide-line">
        {rows.map((a: AnomalyRow) => {
          const sig = SIG[a.type] ?? DEFAULT_SIG;
          return (
            <button
              key={a.id}
              type="button"
              onClick={() => setSelected(a.id)}
              className="w-full flex items-start gap-3 px-md py-2.5 text-left hover:bg-surface"
            >
              <span
                className={`mt-0.5 grid place-items-center w-7 h-7 rounded-md flex-none [&_svg]:w-3.5 [&_svg]:h-3.5 ${sig.cls}`}
              >
                {sig.icon}
              </span>
              <span className="min-w-0">
                <span className="block text-sm text-ink">{TYPE_LABELS[a.type] ?? a.type}</span>
                <span className="block text-xs text-ink-2 truncate">{a.cause ?? '—'}</span>
                <span className="block text-[11px] text-ink-3">
                  {formatDate(a.detected_for)} · severity {a.severity}
                </span>
              </span>
            </button>
          );
        })}
      </div>

      {anomalies.isLoading ? <div className="px-md py-3 text-sm text-ink-3">Loading…</div> : null}
      {anomalies.data && rows.length === 0 ? (
        <div className="px-md py-3 text-sm text-ink-3">No anomalies in the last 7 days.</div>
      ) : null}

      {selected ? <AnomalyDrawer anomalyId={selected} onClose={() => setSelected(null)} /> : null}
    </section>
  );
}

function AnomalyDrawer({ anomalyId, onClose }: { anomalyId: string; onClose: () => void }) {
  const queryClient = useQueryClient();
  const detail = useQuery({
    queryKey: ['anomaly', anomalyId],
    queryFn: () => fetchAnomalyDetail(anomalyId),
  });
  const [error, setError] = useState<string | null>(null);

  const review = useMutation({
    mutationFn: (decision: AnomalyDecision) => reviewAnomaly(anomalyId, decision),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['anomalies'] });
      void queryClient.invalidateQueries({ queryKey: ['anomaly-summary'] });
      onClose();
    },
    onError: () => setError('Review failed (planner or admin role required).'),
  });

  const d = detail.data;
  const txn = d?.transaction;
  const open = d?.status === 'open';

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button type="button" aria-label="Close" onClick={onClose} className="flex-1 bg-ink/[0.25]" />
      <aside className="w-[460px] max-w-full h-full bg-card border-l border-line overflow-y-auto p-lg flex flex-col gap-4">
        {!d ? (
          <p className="text-sm text-ink-3">Loading…</p>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <div className="font-display text-lg text-ink">{TYPE_LABELS[d.type] ?? d.type}</div>
              <Badge label={`AI · ${d.model_version}`} variant="ai" />
            </div>

            <div className="rounded-md border border-line p-md">
              <div className="text-sm text-ink">{d.cause ?? '—'}</div>
              <div className="mt-1 text-xs text-ink-3">
                Detected {formatDate(d.detected_for)} · severity {d.severity} · z/score{' '}
                <span className="font-mono text-ai">{d.score}</span>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-ink-2 mb-1">Evidence</h3>
              <dl className="text-xs flex flex-col gap-1">
                {Object.entries(d.evidence)
                  .filter(([k]) => k !== 'cause')
                  .map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <dt className="text-ink-3">{k}</dt>
                      <dd className="font-mono text-ink-2">{String(v)}</dd>
                    </div>
                  ))}
              </dl>
            </div>

            {txn ? (
              <div>
                <h3 className="text-sm font-medium text-ink-2 mb-1">Source transaction</h3>
                <div className="rounded-md border border-line p-md text-xs flex flex-col gap-1">
                  <div className="flex justify-between">
                    <span className="text-ink-3">Record</span>
                    <span className="font-mono text-ink">{txn.source_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-3">Item</span>
                    <span className="font-mono text-ink-2">{txn.item_number ?? '—'}</span>
                  </div>
                  <div className="text-ink-3">{txn.description ?? '—'}</div>
                  <div className="flex justify-between">
                    <span className="text-ink-3">Qty / cost</span>
                    <span className="text-ink-2">
                      {integer.format(txn.quantity)} ·{' '}
                      {txn.unit_cost !== null ? txn.unit_cost : '—'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-3">Date / site</span>
                    <span className="text-ink-2">
                      {formatDate(txn.txn_date)} · {txn.location_code ?? '—'}
                    </span>
                  </div>
                </div>
              </div>
            ) : null}

            {error ? <p className="text-sm text-crit">{error}</p> : null}

            {open ? (
              <div className="mt-auto flex gap-2">
                <Button
                  className="flex-1"
                  disabled={review.isPending}
                  onClick={() => review.mutate('acknowledge')}
                >
                  Acknowledge
                </Button>
                <Button
                  className="flex-1"
                  disabled={review.isPending}
                  onClick={() => review.mutate('dismiss')}
                >
                  Dismiss
                </Button>
              </div>
            ) : (
              <div className="mt-auto rounded-md border border-line p-md text-sm text-ink-2">
                Reviewed as <span className="font-medium">{d.status}</span>.
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
