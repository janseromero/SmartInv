'use client';

import {
  OVERRIDE_REASONS,
  type ParetoPoint,
  type RecommendationEnvelope,
  type RecommendationRow,
  acceptRecommendation,
  fetchAcceptanceRate,
  fetchRecommendationDetail,
  fetchRecommendationSummary,
  fetchRecommendations,
  fetchRegimeSignals,
  overrideRecommendation,
} from '@/lib/api';
import { Badge, Button, ConfidenceMeter, EvidenceStrip, KpiCard } from '@smartinv/ui-web';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

const integer = new Intl.NumberFormat('en-US');
const currency = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
  notation: 'compact',
});
const pct = new Intl.NumberFormat('en-US', { style: 'percent', maximumFractionDigits: 0 });

const ACTION_LABELS: Record<string, string> = {
  buy: 'Buy',
  raise_min: 'Raise min',
  lower_max: 'Lower max',
  reduce_excess: 'Reduce excess',
  hold: 'Hold',
};
const ACTION_TONE: Record<string, 'ok' | 'warn' | 'crit'> = {
  buy: 'crit',
  raise_min: 'warn',
  lower_max: 'warn',
  reduce_excess: 'warn',
  hold: 'ok',
};
const ACTION_TABS = [
  { value: '', label: 'All' },
  { value: 'buy', label: 'Buy' },
  { value: 'reduce_excess', label: 'Reduce excess' },
  { value: 'lower_max', label: 'Lower max' },
  { value: 'raise_min', label: 'Raise min' },
];

export function Recommendations() {
  const [action, setAction] = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);

  const summary = useQuery({ queryKey: ['rec-summary'], queryFn: fetchRecommendationSummary });
  const recs = useQuery({
    queryKey: ['recs', { action }],
    queryFn: () => fetchRecommendations({ action: action || undefined, page_size: 50 }),
  });

  const s = summary.data;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard label="Proposed" value={s ? integer.format(s.proposed) : '—'} />
        <KpiCard
          label="Actionable"
          value={s ? integer.format(s.actionable) : '—'}
          status={s && s.actionable > 0 ? 'warn' : 'ok'}
        />
        <KpiCard
          label="Capital impact"
          value={s ? currency.format(s.capital_delta) : '—'}
          delta={s ? 'at recommended max levels' : undefined}
        />
        <KpiCard label="Avg confidence" value={s ? pct.format(s.avg_confidence) : '—'} />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {ACTION_TABS.map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => setAction(t.value)}
            className={`rounded-md border px-md py-1.5 text-sm ${
              action === t.value
                ? 'border-ink text-ink bg-surface'
                : 'border-line text-ink-2 hover:bg-surface'
            }`}
          >
            {t.label}
          </button>
        ))}
        <span className="flex-1" />
        <button
          type="button"
          onClick={() => setShowFeedback((v) => !v)}
          className="rounded-md border border-line px-md py-1.5 text-sm text-ink-2 hover:bg-surface"
        >
          {showFeedback ? 'Hide feedback loop' : 'Feedback loop'}
        </button>
      </div>

      {showFeedback ? <FeedbackPanel /> : null}

      <div className="flex flex-col gap-3">
        {recs.data?.recommendations.map((r: RecommendationRow) => (
          <RecommendationCard key={r.id} row={r} onOpen={() => setSelected(r.id)} />
        ))}
        {recs.isLoading ? <div className="text-sm text-ink-3">Loading…</div> : null}
        {recs.data && recs.data.recommendations.length === 0 ? (
          <div className="rounded-md border border-line bg-card p-md text-sm text-ink-3">
            No recommendations for this filter. Run the optimizer (`make optimize`).
          </div>
        ) : null}
      </div>

      {selected ? (
        <EnvelopeDrawer recommendationId={selected} onClose={() => setSelected(null)} />
      ) : null}
    </div>
  );
}

function RecommendationCard({ row, onOpen }: { row: RecommendationRow; onOpen: () => void }) {
  const action = row.recommended_action ?? 'hold';
  const reviewed = row.status !== 'proposed';
  return (
    <div className="rounded-md border border-line bg-card shadow-card p-md flex flex-col gap-2">
      <div className="flex items-start gap-2 flex-wrap">
        <span className="font-medium text-ink">
          {ACTION_LABELS[action] ?? action} — {row.description ?? row.item_number ?? 'Item'}
        </span>
        <Badge
          label={ACTION_LABELS[action] ?? action}
          variant="status"
          tone={ACTION_TONE[action] ?? 'warn'}
        />
        <span className="font-mono text-xs text-ink-3">{row.item_number}</span>
        <span className="flex-1" />
        {reviewed ? (
          <Badge label={row.status} variant="neutral" />
        ) : (
          <Button variant="primary" size="sm" onClick={onOpen}>
            Review
          </Button>
        )}
      </div>
      <p className="text-sm text-ink-2">{row.claim}</p>
      <div className="flex items-center gap-3 text-xs text-ink-3">
        {row.confidence !== null ? (
          <span className="w-40">
            <ConfidenceMeter value={row.confidence} label="Confidence" />
          </span>
        ) : null}
        <span className="font-mono text-[10px]">model {row.model_version}</span>
        {row.capital_delta !== null ? (
          <span>Δ capital {currency.format(row.capital_delta)}</span>
        ) : null}
      </div>
    </div>
  );
}

function ParetoChart({ points }: { points: ParetoPoint[] }) {
  if (points.length === 0) return null;
  const capitals = points.map((p) => p.capital);
  const maxCap = Math.max(...capitals, 1);
  return (
    <div className="rounded-md border border-line p-md">
      <h3 className="text-sm font-medium text-ink-2 mb-2">Cost ↔ risk frontier</h3>
      <div className="relative h-32 border-l border-b border-line">
        {points.map((p) => {
          const x = p.stockout_prob * 100 * 4; // 0..25% -> 0..100
          const y = (p.capital / maxCap) * 100;
          return (
            <span
              key={p.service_level}
              title={`SL ${pct.format(p.service_level)} · ${currency.format(p.capital)} · stockout ${pct.format(p.stockout_prob)}`}
              className="absolute w-2.5 h-2.5 rounded-full bg-ai -translate-x-1/2 translate-y-1/2"
              style={{ left: `${Math.min(100, x)}%`, bottom: `${y}%` }}
            />
          );
        })}
      </div>
      <div className="flex justify-between text-[10px] text-ink-3 mt-1">
        <span>capital ↑ / stockout →</span>
        <span>{points.length} service levels</span>
      </div>
    </div>
  );
}

function EnvelopeDrawer({
  recommendationId,
  onClose,
}: { recommendationId: string; onClose: () => void }) {
  const queryClient = useQueryClient();
  const detail = useQuery({
    queryKey: ['rec', recommendationId],
    queryFn: () => fetchRecommendationDetail(recommendationId),
  });
  const [error, setError] = useState<string | null>(null);
  const [overriding, setOverriding] = useState(false);
  const [reason, setReason] = useState<string>(OVERRIDE_REASONS[0].value);
  const [note, setNote] = useState('');

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['recs'] });
    void queryClient.invalidateQueries({ queryKey: ['rec-summary'] });
    onClose();
  };

  const accept = useMutation({
    mutationFn: () => acceptRecommendation(recommendationId),
    onSuccess: invalidate,
    onError: () => setError('Accept failed (planner or admin role required).'),
  });
  const override = useMutation({
    mutationFn: () => overrideRecommendation(recommendationId, reason, note || undefined),
    onSuccess: invalidate,
    onError: () => setError('Override failed (planner or admin role required).'),
  });

  const d: RecommendationEnvelope | undefined = detail.data;
  const pareto = (d?.evidence.pareto as ParetoPoint[] | undefined) ?? [];

  const evidenceItems = d
    ? [
        { metric: 'min/max', value: `${d.payload.min_level} / ${d.payload.max_level}` },
        { metric: 'reorder', value: String(d.payload.reorder_point) },
        { metric: 'safety stock', value: String(d.payload.safety_stock) },
        { metric: 'stockout', value: pct.format(Number(d.evidence.stockout_prob ?? 0)) },
        { metric: 'lead time', value: `${d.evidence.lead_time_days}d` },
        { metric: 'forecast', value: String(d.evidence.forecast_method ?? '—') },
      ]
    : [];

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button type="button" aria-label="Close" onClick={onClose} className="flex-1 bg-ink/[0.25]" />
      <aside className="w-[560px] max-w-full h-full bg-card border-l border-line overflow-y-auto p-lg flex flex-col gap-4">
        {!d ? (
          <p className="text-sm text-ink-3">Loading…</p>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-mono text-xs text-ink-3">{d.item_number}</div>
                <div className="font-display text-lg text-ink">{d.description ?? 'Item'}</div>
              </div>
              <Badge label={`AI · ${d.model_version}`} variant="ai" />
            </div>

            <p className="text-sm text-ink-2">{d.claim}</p>

            <EvidenceStrip
              items={evidenceItems}
              confidence={d.confidence ?? undefined}
              modelVersion={d.model_version ?? undefined}
            />

            <ParetoChart points={pareto} />

            <div>
              <h3 className="text-sm font-medium text-ink-2 mb-1">Assumptions</h3>
              <dl className="text-xs flex flex-col gap-1">
                {Object.entries(d.assumptions).map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <dt className="text-ink-3">{k}</dt>
                    <dd className="font-mono text-ink-2">{String(v)}</dd>
                  </div>
                ))}
              </dl>
            </div>

            <div className="text-xs text-ink-3">
              Approval path: <span className="font-mono">{d.approval_path}</span> — accepting routes
              to the approval queue, never a direct write.
            </div>

            {error ? <p className="text-sm text-crit">{error}</p> : null}

            {d.status !== 'proposed' ? (
              <div className="mt-auto rounded-md border border-line p-md text-sm text-ink-2">
                Actioned as <span className="font-medium">{d.status}</span>.
              </div>
            ) : overriding ? (
              <div className="mt-auto flex flex-col gap-2">
                <h3 className="text-sm font-medium text-ink-2">Override — reason</h3>
                <select
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="bg-card border border-line rounded-md px-md py-1.5 text-sm text-ink"
                >
                  {OVERRIDE_REASONS.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Optional note…"
                  className="bg-card border border-line rounded-md px-md py-1.5 text-sm text-ink min-h-[60px]"
                />
                <div className="flex gap-2">
                  <Button
                    variant="primary"
                    className="flex-1"
                    disabled={override.isPending}
                    onClick={() => override.mutate()}
                  >
                    Submit override
                  </Button>
                  <Button onClick={() => setOverriding(false)}>Cancel</Button>
                </div>
              </div>
            ) : (
              <div className="mt-auto flex gap-2">
                <Button
                  variant="primary"
                  className="flex-1"
                  disabled={accept.isPending}
                  onClick={() => accept.mutate()}
                >
                  Accept → approval
                </Button>
                <Button className="flex-1" onClick={() => setOverriding(true)}>
                  Override…
                </Button>
              </div>
            )}

            <Button onClick={onClose}>Close</Button>
          </>
        )}
      </aside>
    </div>
  );
}

function FeedbackPanel() {
  const rates = useQuery({ queryKey: ['acceptance-rate'], queryFn: fetchAcceptanceRate });
  const signals = useQuery({ queryKey: ['regime-signals'], queryFn: fetchRegimeSignals });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
      <section className="rounded-md border border-line bg-card shadow-card p-md">
        <h3 className="font-display text-sm text-ink mb-2">Acceptance rate by model</h3>
        {rates.data && rates.data.length > 0 ? (
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-ink-3 border-b border-line">
                <th className="font-normal py-1">Model</th>
                <th className="font-normal py-1 text-right">Accepted</th>
                <th className="font-normal py-1 text-right">Overridden</th>
                <th className="font-normal py-1 text-right">Rate</th>
              </tr>
            </thead>
            <tbody>
              {rates.data.map((r) => (
                <tr key={r.model_version} className="border-b border-line">
                  <td className="py-1 font-mono text-ink-2">{r.model_version}</td>
                  <td className="py-1 text-right text-ink">{r.accepted}</td>
                  <td className="py-1 text-right text-ink">{r.overridden}</td>
                  <td className="py-1 text-right font-mono text-ink">
                    {pct.format(r.acceptance_rate)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-xs text-ink-3">No feedback recorded yet.</p>
        )}
      </section>

      <section className="rounded-md border border-line bg-card shadow-card p-md">
        <h3 className="font-display text-sm text-ink mb-2">Regime-change signals</h3>
        {signals.data && signals.data.length > 0 ? (
          <div className="flex flex-col gap-1.5">
            {signals.data.map((sig) => (
              <div key={sig.id} className="flex items-center gap-2 text-xs">
                {sig.is_regime_change ? (
                  <Badge label="regime change" variant="status" tone="crit" />
                ) : (
                  <Badge label={`×${sig.override_count}`} variant="neutral" />
                )}
                <span className="font-mono text-ink-2">
                  {sig.item_number ?? sig.item_id.slice(0, 8)}
                </span>
                <span className="text-ink-3">{sig.dimension}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-ink-3">No recurring overrides yet.</p>
        )}
      </section>
    </div>
  );
}
