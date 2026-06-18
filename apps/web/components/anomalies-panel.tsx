'use client';

import {
  type AnomalyDecision,
  type AnomalyRow,
  fetchAnomalies,
  fetchAnomalyDetail,
  fetchAnomalySummary,
  reviewAnomaly,
} from '@/lib/api';
import { Badge } from '@smartinv/ui-web';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

const WINDOW_DAYS = 7;
const integer = new Intl.NumberFormat('en-US');

const TYPE_LABELS: Record<string, string> = {
  consumption_spike: 'Consumption spike',
  price_jump: 'Price jump',
  negative_balance: 'Negative balance',
};

const TYPES = [
  { value: '', label: 'All types' },
  { value: 'consumption_spike', label: 'Consumption spikes' },
  { value: 'price_jump', label: 'Price jumps' },
  { value: 'negative_balance', label: 'Negative balances' },
];

function severityTone(severity: string): 'crit' | 'warn' {
  return severity === 'crit' ? 'crit' : 'warn';
}

function formatDate(iso: string | null): string {
  return iso ? iso.slice(0, 10) : '—';
}

export function AnomaliesPanel() {
  const [type, setType] = useState('');
  const [selected, setSelected] = useState<string | null>(null);

  const summary = useQuery({ queryKey: ['anomaly-summary'], queryFn: fetchAnomalySummary });
  const anomalies = useQuery({
    queryKey: ['anomalies', { type }],
    queryFn: () =>
      fetchAnomalies({
        window_days: WINDOW_DAYS,
        type: type || undefined,
        page_size: 50,
      }),
  });

  const s = summary.data;

  return (
    <section className="rounded-md border border-line bg-card shadow-card p-md flex flex-col gap-3">
      <header className="flex flex-wrap items-center gap-2">
        <h2 className="font-display text-ink">Anomalies — last 7 days</h2>
        <Badge label="AI · model-generated" variant="ai" />
        {s ? (
          <span className="text-xs text-ink-3">
            {integer.format(s.open)} open · {integer.format(s.crit)} critical
          </span>
        ) : null}
        <span className="flex-1" />
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="bg-card border border-line rounded-md px-md py-1 text-sm text-ink"
        >
          {TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </header>

      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-ink-3 border-b border-line">
            <th className="font-normal py-1.5">Type</th>
            <th className="font-normal py-1.5">Likely cause</th>
            <th className="font-normal py-1.5">Severity</th>
            <th className="font-normal py-1.5 text-right">Detected</th>
          </tr>
        </thead>
        <tbody>
          {anomalies.data?.anomalies.map((a: AnomalyRow) => (
            <tr
              key={a.id}
              onClick={() => setSelected(a.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') setSelected(a.id);
              }}
              tabIndex={0}
              className="border-b border-line hover:bg-surface cursor-pointer"
            >
              <td className="py-1.5 text-ink">{TYPE_LABELS[a.type] ?? a.type}</td>
              <td className="py-1.5 text-ink-2 truncate max-w-[360px]">{a.cause ?? '—'}</td>
              <td className="py-1.5">
                <Badge label={a.severity} variant="status" tone={severityTone(a.severity)} />
              </td>
              <td className="py-1.5 text-right text-ink-3">{formatDate(a.detected_for)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {anomalies.isLoading ? <div className="text-sm text-ink-3">Loading…</div> : null}
      {anomalies.data && anomalies.data.anomalies.length === 0 ? (
        <div className="text-sm text-ink-3">No anomalies in the last 7 days.</div>
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
                <button
                  type="button"
                  disabled={review.isPending}
                  onClick={() => review.mutate('acknowledge')}
                  className="flex-1 rounded-md border border-line px-md py-1.5 text-sm text-ink-2 disabled:opacity-50"
                >
                  Acknowledge
                </button>
                <button
                  type="button"
                  disabled={review.isPending}
                  onClick={() => review.mutate('dismiss')}
                  className="flex-1 rounded-md border border-line px-md py-1.5 text-sm text-ink-2 disabled:opacity-50"
                >
                  Dismiss
                </button>
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
