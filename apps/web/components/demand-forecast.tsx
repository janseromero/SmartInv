'use client';

/**
 * Demand Forecasting (CV3.E1).
 *
 * Reads the persisted Croston/TSB forecasts: portfolio KPIs, a method-filtered
 * per-item table, and a drill-down that plots the item's bucketed demand
 * history alongside a flat forecast projection with a P80/P95 confidence band.
 * Read-only — forecasting produces no writes, so there is no approval action.
 */

import {
  type ForecastItemDetail,
  type ForecastItemRow,
  fetchForecastItemDetail,
  fetchForecastItems,
  fetchForecastSummary,
} from '@/lib/api';
import { DEFAULT_CHART_DIMS, forecastChartGeometry } from '@/lib/forecast';
import { Badge, KpiCard } from '@smartinv/ui-web';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

const integer = new Intl.NumberFormat('en-US');
const decimal = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 });

// Method is the story: TSB = obsolescence-trending, croston = active intermittent,
// naive = thin signal, empty = no history. Tones follow the status palette.
const METHOD_META: Record<string, { label: string; tone: 'ok' | 'warn' | 'crit' | 'neutral' }> = {
  croston: { label: 'Croston', tone: 'ok' },
  tsb: { label: 'TSB · decaying', tone: 'warn' },
  naive: { label: 'Naive · low signal', tone: 'neutral' },
  empty: { label: 'No history', tone: 'neutral' },
};

const METHOD_FILTERS = ['', 'croston', 'tsb', 'naive', 'empty'] as const;

function methodBadge(method: string) {
  const meta = METHOD_META[method] ?? { label: method, tone: 'neutral' as const };
  if (meta.tone === 'neutral') return <Badge label={meta.label} variant="neutral" />;
  return <Badge label={meta.label} variant="status" tone={meta.tone} />;
}

export function DemandForecast() {
  const [method, setMethod] = useState('');
  const [selected, setSelected] = useState<string | null>(null);

  const summary = useQuery({ queryKey: ['forecast-summary'], queryFn: fetchForecastSummary });
  const items = useQuery({
    queryKey: ['forecast-items', { method }],
    queryFn: () => fetchForecastItems({ method: method || undefined, page_size: 40 }),
  });

  const s = summary.data;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard
          label="Items forecasted"
          value={s ? integer.format(s.forecasted) : '—'}
          delta={s ? `${s.coverage_pct}% of catalog` : undefined}
          loading={summary.isLoading}
        />
        <KpiCard
          label="Obsolescence-trending"
          value={s ? integer.format(s.obsolescence_trending) : '—'}
          delta="TSB — demand decaying"
          status={s && s.obsolescence_trending > 0 ? 'warn' : 'ok'}
          loading={summary.isLoading}
        />
        <KpiCard
          label="Demand variability"
          value={s ? decimal.format(s.avg_cv) : '—'}
          delta="avg coefficient of variation"
          status={s ? (s.avg_cv > 1 ? 'warn' : 'ok') : undefined}
          loading={summary.isLoading}
        />
        <KpiCard
          label="Model"
          value={s ? 'Croston / TSB' : '—'}
          delta={s?.model_version}
          loading={summary.isLoading}
        />
      </div>

      {s ? <MethodBar byMethod={s.by_method} total={s.forecasted} /> : null}

      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="bg-card border border-line rounded-md px-md py-1.5 text-sm text-ink"
          >
            {METHOD_FILTERS.map((m) => (
              <option key={m || 'all'} value={m}>
                {m ? (METHOD_META[m]?.label ?? m) : 'All methods'}
              </option>
            ))}
          </select>
          <span className="text-xs text-ink-3">
            {items.data ? `${integer.format(items.data.total)} items` : ''}
          </span>
        </div>

        <div className="rounded-md border border-line bg-card shadow-card overflow-hidden">
          <div className="flex items-center gap-2 px-md py-2.5 border-b border-line">
            <h3 className="font-display text-sm text-ink">Per-item demand forecast</h3>
            <span className="text-xs text-ink-3">P50 rate/period · P80 · P95 band</span>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink-3 border-b border-line">
                <th className="font-normal px-md py-2">Item</th>
                <th className="font-normal px-md py-2">Method</th>
                <th className="font-normal px-md py-2 text-right">P50 / period</th>
                <th className="font-normal px-md py-2 text-right">P80</th>
                <th className="font-normal px-md py-2 text-right">P95</th>
                <th className="font-normal px-md py-2 text-right">CV</th>
              </tr>
            </thead>
            <tbody>
              {items.data?.items.map((item: ForecastItemRow) => (
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
                  <td className="px-md py-2">{methodBadge(item.method)}</td>
                  <td className="px-md py-2 text-right font-mono text-ink">
                    {decimal.format(item.p50)}
                  </td>
                  <td className="px-md py-2 text-right font-mono text-ink-2">
                    {decimal.format(item.p80)}
                  </td>
                  <td className="px-md py-2 text-right font-mono text-ink-2">
                    {decimal.format(item.p95)}
                  </td>
                  <td className="px-md py-2 text-right font-mono text-ink-3">
                    {decimal.format(item.cv)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {items.isLoading ? <div className="p-md text-sm text-ink-3">Loading…</div> : null}
          {items.data && items.data.items.length === 0 ? (
            <div className="p-md text-sm text-ink-3">
              No forecasts match this filter — run `make forecast`.
            </div>
          ) : null}
        </div>
      </div>

      {selected ? <ForecastDrawer itemId={selected} onClose={() => setSelected(null)} /> : null}
    </div>
  );
}

const METHOD_BAR = [
  { key: 'croston', label: 'Croston', cls: 'bg-ok' },
  { key: 'tsb', label: 'TSB', cls: 'bg-warn' },
  { key: 'naive', label: 'Naive', cls: 'bg-ink-3' },
  { key: 'empty', label: 'No history', cls: 'bg-surface' },
] as const;

function MethodBar({ byMethod, total }: { byMethod: Record<string, number>; total: number }) {
  const denom = total || 1;
  return (
    <section className="rounded-md border border-line bg-card shadow-card overflow-hidden">
      <div className="flex items-center gap-2 px-md py-2.5 border-b border-line">
        <h3 className="font-display text-sm text-ink">Forecast method mix</h3>
        <span className="text-xs text-ink-3">which model each item earned</span>
      </div>
      <div className="p-md flex flex-col gap-3">
        <div className="flex h-2.5 w-full overflow-hidden rounded-pill bg-surface">
          {METHOD_BAR.map((seg) => {
            const v = byMethod[seg.key] ?? 0;
            if (v === 0) return null;
            return (
              <span
                key={seg.key}
                className={seg.cls}
                style={{ width: `${(v / denom) * 100}%` }}
                title={`${seg.label}: ${integer.format(v)}`}
              />
            );
          })}
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          {METHOD_BAR.map((seg) => (
            <div key={seg.key} className="flex items-center gap-1.5 text-xs text-ink-2">
              <span className={`w-2 h-2 rounded-pill ${seg.cls}`} />
              {seg.label}
              <span className="font-mono text-ink-3">{integer.format(byMethod[seg.key] ?? 0)}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ForecastChart({ detail }: { detail: ForecastItemDetail }) {
  const dims = DEFAULT_CHART_DIMS;
  const g = forecastChartGeometry(
    detail.history,
    { p50: detail.p50, p80: detail.p80, p95: detail.p95 },
    detail.horizon,
    dims,
  );

  return (
    <svg
      viewBox={`0 0 ${dims.width} ${dims.height}`}
      className="w-full h-auto"
      role="img"
      aria-label={`Demand history and forecast for ${detail.item_number}`}
    >
      {/* baseline */}
      <line
        x1={0}
        y1={g.baselineY}
        x2={dims.width}
        y2={g.baselineY}
        className="stroke-line"
        strokeWidth={1}
      />

      {/* history bars */}
      {g.bars.map((bar) => (
        <rect
          key={`bar-${bar.x.toFixed(2)}`}
          x={bar.x}
          y={bar.y}
          width={bar.width}
          height={bar.height}
          className="fill-ink-3"
          rx={1}
        />
      ))}

      {/* forecast band: P95 (light) then P80 (stronger), then the P50 line */}
      <rect
        x={g.forecastX0}
        y={g.p95Y}
        width={g.forecastX1 - g.forecastX0}
        height={g.baselineY - g.p95Y}
        className="fill-ai/10"
      />
      <rect
        x={g.forecastX0}
        y={g.p80Y}
        width={g.forecastX1 - g.forecastX0}
        height={g.baselineY - g.p80Y}
        className="fill-ai/15"
      />
      <line
        x1={g.forecastX0}
        y1={g.p50Y}
        x2={g.forecastX1}
        y2={g.p50Y}
        className="stroke-ai"
        strokeWidth={2}
      />

      {/* "now" divider */}
      <line
        x1={g.nowX}
        y1={dims.padTop}
        x2={g.nowX}
        y2={g.baselineY}
        className="stroke-line"
        strokeWidth={1}
        strokeDasharray="3 3"
      />
    </svg>
  );
}

function ForecastDrawer({ itemId, onClose }: { itemId: string; onClose: () => void }) {
  const detail = useQuery({
    queryKey: ['forecast-item', itemId],
    queryFn: () => fetchForecastItemDetail(itemId),
  });
  const d = detail.data;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button type="button" aria-label="Close" onClick={onClose} className="flex-1 bg-ink/[0.25]" />
      <aside className="w-[520px] max-w-full h-full bg-card border-l border-line overflow-y-auto p-lg flex flex-col gap-4">
        {!d ? (
          <p className="text-sm text-ink-3">Loading…</p>
        ) : (
          <>
            <div>
              <div className="font-mono text-xs text-ink-3">{d.item_number}</div>
              <div className="font-display text-lg text-ink">{d.description ?? 'Item'}</div>
              <div className="mt-1 flex items-center gap-2">
                {methodBadge(d.method)}
                <span className="text-xs text-ink-3 font-mono">{d.model_version}</span>
              </div>
            </div>

            <div className="rounded-md border border-line p-md">
              <ForecastChart detail={d} />
              <div className="mt-2 flex items-center justify-between text-[11px] text-ink-3">
                <span>← {d.history.length} periods history</span>
                <span className="text-ai">forecast {d.horizon} periods →</span>
              </div>
            </div>

            <dl className="grid grid-cols-3 gap-2 text-center">
              {(
                [
                  ['P50', d.p50],
                  ['P80', d.p80],
                  ['P95', d.p95],
                ] as const
              ).map(([label, value]) => (
                <div key={label} className="rounded-md border border-line p-md">
                  <dt className="text-[11px] uppercase tracking-wide text-ink-3">{label}</dt>
                  <dd className="font-display text-lg text-ink">{decimal.format(value)}</dd>
                </div>
              ))}
            </dl>

            <div className="text-xs flex flex-col gap-1">
              <Row label="Demand events" value={integer.format(d.demand_events)} />
              <Row label="Coefficient of variation" value={decimal.format(d.cv)} />
              <Row label="Period length" value={`${d.period_days} days`} />
              {d.predicted_at ? (
                <Row label="Computed" value={new Date(d.predicted_at).toLocaleString()} />
              ) : null}
            </div>

            <p className="text-xs text-ink-3 border-t border-line pt-2">
              Croston/TSB projects a flat per-period rate; the band is the P80/P95 quantile from
              this item's demand variability. This forecast feeds the optimization recommendations.
            </p>
          </>
        )}
      </aside>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-ink-3">{label}</span>
      <span className="font-mono text-ink-2">{value}</span>
    </div>
  );
}
