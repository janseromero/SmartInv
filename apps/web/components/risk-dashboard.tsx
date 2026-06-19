'use client';

import {
  type ExposureCell,
  type HeatmapRow,
  type RiskItemRow,
  fetchRiskExposure,
  fetchRiskHeatmap,
  fetchRiskItemDetail,
  fetchRiskItems,
  fetchRiskSummary,
  mitigateRisk,
} from '@/lib/api';
import { Badge, Button, KpiCard } from '@smartinv/ui-web';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Fragment, useState } from 'react';

const integer = new Intl.NumberFormat('en-US');
const currency = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
  notation: 'compact',
});

const RISK_CLASSES = ['critical', 'high', 'moderate', 'low'] as const;
const RISK_TONE: Record<string, 'ok' | 'warn' | 'crit'> = {
  critical: 'crit',
  high: 'crit',
  moderate: 'warn',
  low: 'ok',
};

export function RiskDashboard() {
  const [riskClass, setRiskClass] = useState('');
  const [criticalOnly, setCriticalOnly] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);

  const summary = useQuery({ queryKey: ['risk-summary'], queryFn: fetchRiskSummary });
  const heatmap = useQuery({ queryKey: ['risk-heatmap'], queryFn: fetchRiskHeatmap });
  const exposure = useQuery({ queryKey: ['risk-exposure'], queryFn: fetchRiskExposure });
  const items = useQuery({
    queryKey: ['risk-items', { riskClass, criticalOnly }],
    queryFn: () =>
      fetchRiskItems({
        risk_class: riskClass || undefined,
        critical_only: criticalOnly || undefined,
        page_size: 40,
      }),
  });

  const s = summary.data;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard
          label="Downtime exposure"
          value={s ? currency.format(s.downtime_exposure) : '—'}
          status={s && s.downtime_exposure > 0 ? 'crit' : 'ok'}
        />
        <KpiCard
          label="Critical-spare coverage"
          value={s ? `${s.critical_spare_coverage}%` : '—'}
          delta={s ? `${integer.format(s.critical_spares)} critical spares` : undefined}
          status={s ? (s.critical_spare_coverage >= 90 ? 'ok' : 'warn') : undefined}
        />
        <KpiCard
          label="Single-source items"
          value={s ? integer.format(s.single_source_items) : '—'}
          status={s && s.single_source_items > 0 ? 'warn' : 'ok'}
        />
        <KpiCard
          label="Obsolescence candidates"
          value={s ? integer.format(s.obsolescence_candidates) : '—'}
        />
      </div>

      <Heatmap rows={heatmap.data ?? []} />

      <ExposureTable cells={exposure.data ?? []} onSelectClass={setRiskClass} />

      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={riskClass}
            onChange={(e) => setRiskClass(e.target.value)}
            className="bg-card border border-line rounded-md px-md py-1.5 text-sm text-ink"
          >
            <option value="">All risk levels</option>
            {RISK_CLASSES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-1 text-sm text-ink-2">
            <input
              type="checkbox"
              checked={criticalOnly}
              onChange={(e) => setCriticalOnly(e.target.checked)}
            />
            Critical spares only
          </label>
        </div>

        <div className="rounded-md border border-line bg-card shadow-card overflow-hidden">
          <div className="flex items-center gap-2 px-md py-2.5 border-b border-line">
            <h3 className="font-display text-sm text-ink">Top critical-spare exposures</h3>
            <span className="text-xs text-ink-3">
              {items.data ? `${integer.format(items.data.total)} items` : ''}
            </span>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink-3 border-b border-line">
                <th className="font-normal px-md py-2">Item</th>
                <th className="font-normal px-md py-2">Crit.</th>
                <th className="font-normal px-md py-2">Risk</th>
                <th className="font-normal px-md py-2 text-right">Downtime $</th>
                <th className="font-normal px-md py-2">Flags</th>
              </tr>
            </thead>
            <tbody>
              {items.data?.items.map((item: RiskItemRow) => (
                <tr
                  key={item.id}
                  onClick={() => setSelected(item.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') setSelected(item.id);
                  }}
                  tabIndex={0}
                  className="border-b border-line hover:bg-surface cursor-pointer"
                >
                  <td className="px-md py-2">
                    <div className="font-mono text-ink">{item.item_number}</div>
                    <div className="text-ink-3 truncate max-w-[260px]">
                      {item.description ?? '—'}
                    </div>
                  </td>
                  <td className="px-md py-2 text-ink-2">{item.criticality ?? '—'}</td>
                  <td className="px-md py-2">
                    <Badge
                      label={`${item.risk_class ?? '—'} ${item.risk_score ?? ''}`}
                      variant="status"
                      tone={RISK_TONE[item.risk_class ?? 'low'] ?? 'warn'}
                    />
                  </td>
                  <td className="px-md py-2 text-right font-mono text-ink">
                    {currency.format(item.downtime_exposure)}
                  </td>
                  <td className="px-md py-2">
                    <div className="flex flex-wrap gap-1">
                      {item.is_critical_spare ? (
                        <Badge label="Critical spare" variant="status" tone="crit" />
                      ) : null}
                      {item.single_source ? (
                        <Badge label="Single source" variant="status" tone="warn" />
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {items.isLoading ? <div className="p-md text-sm text-ink-3">Loading…</div> : null}
          {items.data && items.data.items.length === 0 ? (
            <div className="p-md text-sm text-ink-3">No items match this filter.</div>
          ) : null}
        </div>
      </div>

      {selected ? <RiskDrawer itemId={selected} onClose={() => setSelected(null)} /> : null}
    </div>
  );
}

const HEATMAP_DIMENSIONS = [
  { key: 'stockout', label: 'Stockout' },
  { key: 'lead_time', label: 'Lead time' },
  { key: 'supplier', label: 'Supplier' },
  { key: 'criticality', label: 'Criticality' },
] as const;

function scoreCell(score: number): string {
  // 0–100 score banded to the soft status palette (reference cell colors).
  if (score >= 45) return 'bg-crit-soft text-crit font-bold';
  if (score >= 25) return 'bg-warn-soft text-warn-dark';
  return 'bg-ok-soft text-ok';
}

const EXPOSURE_CLASSES = ['critical', 'high', 'moderate', 'low'] as const;

function ExposureTable({
  cells,
  onSelectClass,
}: { cells: ExposureCell[]; onSelectClass: (c: string) => void }) {
  const plants = Array.from(new Set(cells.map((c) => c.location_code))).sort();
  const byKey = new Map(cells.map((c) => [`${c.location_code}|${c.risk_class}`, c]));
  const maxExposure = Math.max(1, ...cells.map((c) => c.exposure));
  const template = `120px repeat(${EXPOSURE_CLASSES.length}, minmax(0, 1fr))`;

  function cellTone(exposure: number): string {
    const intensity = exposure / maxExposure;
    if (intensity > 0.66) return 'bg-crit-soft text-crit font-bold';
    if (intensity > 0.33) return 'bg-warn-soft text-warn-dark';
    if (intensity > 0) return 'bg-ok-soft text-ok';
    return 'bg-surface text-ink-3';
  }

  return (
    <section className="rounded-md border border-line bg-card shadow-card overflow-hidden">
      <div className="flex items-center gap-2 px-md py-2.5 border-b border-line">
        <h3 className="font-display text-sm text-ink">Plant × risk exposure</h3>
        <span className="text-xs text-ink-3">item count · shade = downtime exposure</span>
      </div>
      <div className="p-md">
        <div className="grid gap-1.5 items-center" style={{ gridTemplateColumns: template }}>
          <div />
          {EXPOSURE_CLASSES.map((c) => (
            <div key={c} className="text-[11px] text-ink-3 text-center font-medium capitalize">
              {c}
            </div>
          ))}
          {plants.map((plant) => (
            <Fragment key={plant}>
              <div className="font-mono text-xs text-ink-2 truncate pr-2">{plant}</div>
              {EXPOSURE_CLASSES.map((c) => {
                const cell = byKey.get(`${plant}|${c}`);
                return (
                  <button
                    key={c}
                    type="button"
                    onClick={() => onSelectClass(c)}
                    className={`rounded-sm py-2 text-center text-sm font-mono ${cellTone(cell?.exposure ?? 0)}`}
                    title={
                      cell ? `${cell.count} items · ${currency.format(cell.exposure)}` : '0 items'
                    }
                  >
                    {cell?.count ?? 0}
                  </button>
                );
              })}
            </Fragment>
          ))}
          {plants.length === 0 ? (
            <div className="col-span-full text-sm text-ink-3 py-2">
              No risk scores yet — run `make risk`.
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function Heatmap({ rows }: { rows: HeatmapRow[] }) {
  const template = `120px repeat(${HEATMAP_DIMENSIONS.length}, minmax(0, 1fr))`;
  return (
    <section className="rounded-md border border-line bg-card shadow-card overflow-hidden">
      <div className="flex items-center gap-2 px-md py-2.5 border-b border-line">
        <h3 className="font-display text-sm text-ink">Stockout risk heatmap</h3>
        <span className="text-xs text-ink-3">Plant × risk dimension · score 0–100</span>
      </div>
      <div className="p-md">
        <div className="grid gap-1.5 items-center" style={{ gridTemplateColumns: template }}>
          <div />
          {HEATMAP_DIMENSIONS.map((d) => (
            <div key={d.key} className="text-[11px] text-ink-3 text-center font-medium">
              {d.label}
            </div>
          ))}
          {rows.map((row) => (
            <Fragment key={row.location_code}>
              <div className="font-mono text-xs text-ink-2 truncate pr-2">{row.location_code}</div>
              {HEATMAP_DIMENSIONS.map((d) => {
                const score = row.scores[d.key] ?? 0;
                return (
                  <div
                    key={d.key}
                    className={`rounded-sm py-2 text-center text-sm font-mono ${scoreCell(score)}`}
                    title={`${row.location_code} · ${d.label}: ${score}/100`}
                  >
                    {score}
                  </div>
                );
              })}
            </Fragment>
          ))}
          {rows.length === 0 ? (
            <div className="col-span-full text-sm text-ink-3 py-2">
              No risk scores yet — run `make risk`.
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function RiskDrawer({ itemId, onClose }: { itemId: string; onClose: () => void }) {
  const queryClient = useQueryClient();
  const detail = useQuery({
    queryKey: ['risk-item', itemId],
    queryFn: () => fetchRiskItemDetail(itemId),
  });
  const [message, setMessage] = useState<string | null>(null);

  const mitigate = useMutation({
    mutationFn: () => mitigateRisk(itemId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['risk-item', itemId] });
      setMessage('Mitigation staged → routed to the approval queue.');
    },
    onError: () => setMessage('Mitigation failed (planner/manager/admin role required).'),
  });

  const d = detail.data;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button type="button" aria-label="Close" onClick={onClose} className="flex-1 bg-ink/[0.25]" />
      <aside className="w-[460px] max-w-full h-full bg-card border-l border-line overflow-y-auto p-lg flex flex-col gap-4">
        {!d ? (
          <p className="text-sm text-ink-3">Loading…</p>
        ) : (
          <>
            <div>
              <div className="font-mono text-xs text-ink-3">{d.item_number}</div>
              <div className="font-display text-lg text-ink">{d.description ?? 'Item'}</div>
              <div className="mt-1 flex items-center gap-2">
                <Badge
                  label={`${d.risk_class ?? '—'} · ${d.risk_score ?? ''}`}
                  variant="status"
                  tone={RISK_TONE[d.risk_class ?? 'low'] ?? 'warn'}
                />
                {d.is_critical_spare ? (
                  <Badge label="Critical spare" variant="status" tone="crit" />
                ) : null}
                {d.single_source ? (
                  <Badge label="Single source" variant="status" tone="warn" />
                ) : null}
              </div>
            </div>

            <div className="rounded-md border border-line p-md text-sm text-ink-2">
              {d.narrative}
            </div>

            <div>
              <h3 className="text-sm font-medium text-ink-2 mb-1">Risk breakdown</h3>
              <div className="flex flex-col gap-1">
                {(['stockout', 'lead_time', 'supplier'] as const).map((k) => (
                  <div key={k} className="flex items-center gap-2 text-xs">
                    <span className="w-24 text-ink-3">{k}</span>
                    <span className="flex-1 h-1.5 rounded-pill bg-line overflow-hidden">
                      <span
                        className="block h-full bg-crit"
                        style={{ width: `${Math.round((d.breakdown[k] ?? 0) * 100)}%` }}
                      />
                    </span>
                    <span className="w-10 text-right font-mono text-ink-2">
                      {Math.round((d.breakdown[k] ?? 0) * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <dl className="text-xs flex flex-col gap-1">
              <div className="flex justify-between">
                <dt className="text-ink-3">Downtime exposure</dt>
                <dd className="font-mono text-ink">{currency.format(d.downtime_exposure)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-ink-3">Supplier on-time</dt>
                <dd className="font-mono text-ink-2">
                  {d.supplier_on_time_rate !== null
                    ? `${Math.round(d.supplier_on_time_rate * 100)}%`
                    : '—'}
                </dd>
              </div>
            </dl>

            {message ? <p className="text-sm text-ok">{message}</p> : null}

            <div className="mt-auto flex flex-col gap-2">
              <Button
                variant="primary"
                disabled={mitigate.isPending || !d.has_mitigation_policy}
                onClick={() => mitigate.mutate()}
              >
                {d.has_mitigation_policy
                  ? 'Mitigate → approval'
                  : 'No policy — run optimizer first'}
              </Button>
              <Button onClick={onClose}>Close</Button>
            </div>
          </>
        )}
      </aside>
    </div>
  );
}
