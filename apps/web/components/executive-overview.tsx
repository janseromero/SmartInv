'use client';

/**
 * Executive Overview (CV2 + CV4 + CV6).
 *
 * The landing screen: working capital, operational risk, and where a human
 * needs to act — every figure aggregated from the same governed summary
 * endpoints the detail screens use, and every tile links to the screen that
 * owns the underlying records. No new backend: this is a read-only roll-up.
 */

import {
  type ExposureCell,
  fetchAnomalySummary,
  fetchApprovals,
  fetchDuplicateSummary,
  fetchInventorySummary,
  fetchRecommendationSummary,
  fetchRiskExposure,
  fetchRiskSummary,
} from '@/lib/api';
import { capitalAtRisk, opportunityValue, rollUpPlantExposure } from '@/lib/overview';
import { KpiCard } from '@smartinv/ui-web';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';

const currency = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
  notation: 'compact',
});
const integer = new Intl.NumberFormat('en-US');

type Tone = 'ok' | 'warn' | 'crit';

// --- distribution legends (keys match the API summaries) --------------------
const HEALTH_DIST = [
  { key: 'healthy', label: 'Healthy', cls: 'bg-ok' },
  { key: 'excess_slow', label: 'Excess / slow', cls: 'bg-warn' },
  { key: 'obsolete_risk', label: 'Obsolete / risk', cls: 'bg-crit' },
  { key: 'dq_risk', label: 'DQ risk', cls: 'bg-ink-3' },
] as const;

const RISK_DIST = [
  { key: 'critical', label: 'Critical', cls: 'bg-crit' },
  { key: 'high', label: 'High', cls: 'bg-crit-soft' },
  { key: 'moderate', label: 'Moderate', cls: 'bg-warn' },
  { key: 'low', label: 'Low', cls: 'bg-ok' },
] as const;

export function ExecutiveOverview() {
  const inventory = useQuery({ queryKey: ['inv-summary'], queryFn: () => fetchInventorySummary() });
  const risk = useQuery({ queryKey: ['risk-summary'], queryFn: fetchRiskSummary });
  const recs = useQuery({ queryKey: ['rec-summary'], queryFn: fetchRecommendationSummary });
  const approvals = useQuery({
    queryKey: ['approvals', 'my_queue'],
    queryFn: () => fetchApprovals('my_queue'),
  });
  const anomalies = useQuery({ queryKey: ['anomaly-summary'], queryFn: fetchAnomalySummary });
  const duplicates = useQuery({ queryKey: ['dup-summary'], queryFn: fetchDuplicateSummary });
  const exposure = useQuery({ queryKey: ['risk-exposure'], queryFn: fetchRiskExposure });

  const inv = inventory.data;
  const rk = risk.data;
  const rc = recs.data;

  const capital = inv ? capitalAtRisk(inv.excess_value, inv.dead_stock_value) : null;
  const opportunity = rc ? opportunityValue(rc.capital_delta) : null;

  const actions: Array<{
    href: string;
    label: string;
    value: number | undefined;
    caption: string;
    tone: Tone;
  }> = [
    {
      href: '/approvals',
      label: 'Awaiting your approval',
      value: approvals.data?.total,
      caption: 'high-risk actions in your queue',
      tone: 'crit',
    },
    {
      href: '/optimize',
      label: 'Actionable recommendations',
      value: rc?.actionable,
      caption: 'explained, ready to review',
      tone: 'warn',
    },
    {
      href: '/risk',
      label: 'Critical spares exposed',
      value: rk?.critical_spares,
      caption: `${rk ? rk.critical_spare_coverage : '—'}% coverage`,
      tone: 'crit',
    },
    {
      href: '/health',
      label: 'Open anomalies',
      value: anomalies.data?.open,
      caption: `${anomalies.data?.crit ?? '—'} critical`,
      tone: 'warn',
    },
    {
      href: '/duplicates',
      label: 'Duplicate candidates',
      value: duplicates.data?.open,
      caption: `${duplicates.data?.probable ?? '—'} probable`,
      tone: 'warn',
    },
  ];

  return (
    <div className="flex flex-col gap-5">
      {/* Money + risk headline */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard
          label="Inventory value"
          value={inv ? currency.format(inv.inventory_value) : '—'}
          delta={inv ? `${integer.format(inv.total_items)} items` : undefined}
          loading={inventory.isLoading}
        />
        <KpiCard
          label="Capital at risk"
          value={capital !== null ? currency.format(capital) : '—'}
          delta={inv ? `${currency.format(inv.dead_stock_value)} dead stock` : undefined}
          status={capital ? (capital > 0 ? 'warn' : 'ok') : undefined}
          loading={inventory.isLoading}
        />
        <KpiCard
          label="Downtime exposure"
          value={rk ? currency.format(rk.downtime_exposure) : '—'}
          delta={rk ? `${integer.format(rk.single_source_items)} single-source items` : undefined}
          status={rk && rk.downtime_exposure > 0 ? 'crit' : 'ok'}
          loading={risk.isLoading}
        />
        <KpiCard
          label="Opportunity identified"
          value={opportunity !== null ? currency.format(opportunity) : '—'}
          delta={rc ? `across ${integer.format(rc.actionable)} actions` : undefined}
          status={opportunity ? 'ok' : undefined}
          loading={recs.isLoading}
        />
      </div>

      {/* Where a human needs to act */}
      <section className="rounded-md border border-line bg-card shadow-card overflow-hidden">
        <div className="flex items-center gap-2 px-md py-2.5 border-b border-line">
          <h3 className="font-display text-sm text-ink">Needs a decision</h3>
          <span className="text-xs text-ink-3">agents propose · your team disposes</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 divide-x divide-line">
          {actions.map((a) => (
            <ActionTile key={a.href} {...a} />
          ))}
        </div>
      </section>

      {/* Portfolio composition */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DistributionCard
          title="Inventory health"
          caption="share of catalog by health class"
          legend={HEALTH_DIST}
          distribution={inv?.health_distribution}
          footer={inv ? `${inv.completeness_pct}% item-master completeness` : undefined}
          href="/health"
        />
        <DistributionCard
          title="Operational risk"
          caption="share of scored items by risk class"
          legend={RISK_DIST}
          distribution={rk?.risk_distribution}
          footer={
            rk ? `${integer.format(rk.obsolescence_candidates)} obsolescence candidates` : undefined
          }
          href="/risk"
        />
      </div>

      {/* Plant exposure roll-up */}
      <PlantExposure cells={exposure.data ?? []} />
    </div>
  );
}

const TONE_TEXT: Record<Tone, string> = {
  ok: 'text-ok',
  warn: 'text-warn',
  crit: 'text-crit',
};

function ActionTile({
  href,
  label,
  value,
  caption,
  tone,
}: { href: string; label: string; value: number | undefined; caption: string; tone: Tone }) {
  return (
    <Link
      href={href}
      className="group p-md flex flex-col gap-1 hover:bg-surface transition-colors focus:outline-none focus:bg-surface"
    >
      <span className="font-mono text-[11px] uppercase tracking-wide text-ink-3">{label}</span>
      <span className={`font-display text-2xl ${value ? TONE_TEXT[tone] : 'text-ink-3'}`}>
        {value === undefined ? '—' : integer.format(value)}
      </span>
      <span className="text-xs text-ink-3">{caption}</span>
    </Link>
  );
}

function DistributionCard({
  title,
  caption,
  legend,
  distribution,
  footer,
  href,
}: {
  title: string;
  caption: string;
  legend: ReadonlyArray<{ key: string; label: string; cls: string }>;
  distribution: Record<string, number> | undefined;
  footer: string | undefined;
  href: string;
}) {
  const total = distribution ? Object.values(distribution).reduce((a, b) => a + b, 0) : 0;

  return (
    <section className="rounded-md border border-line bg-card shadow-card overflow-hidden">
      <div className="flex items-center justify-between gap-2 px-md py-2.5 border-b border-line">
        <div className="flex items-center gap-2">
          <h3 className="font-display text-sm text-ink">{title}</h3>
          <span className="text-xs text-ink-3">{caption}</span>
        </div>
        <Link href={href} className="text-xs text-ai hover:underline">
          View →
        </Link>
      </div>
      <div className="p-md flex flex-col gap-3">
        <div className="flex h-2.5 w-full overflow-hidden rounded-pill bg-surface">
          {total > 0
            ? legend.map((seg) => {
                const v = distribution?.[seg.key] ?? 0;
                if (v === 0) return null;
                return (
                  <span
                    key={seg.key}
                    className={seg.cls}
                    style={{ width: `${(v / total) * 100}%` }}
                    title={`${seg.label}: ${integer.format(v)}`}
                  />
                );
              })
            : null}
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          {legend.map((seg) => (
            <div key={seg.key} className="flex items-center gap-1.5 text-xs text-ink-2">
              <span className={`w-2 h-2 rounded-pill ${seg.cls}`} />
              {seg.label}
              <span className="font-mono text-ink-3">
                {integer.format(distribution?.[seg.key] ?? 0)}
              </span>
            </div>
          ))}
        </div>
        {footer ? <p className="text-xs text-ink-3 border-t border-line pt-2">{footer}</p> : null}
      </div>
    </section>
  );
}

function PlantExposure({ cells }: { cells: ExposureCell[] }) {
  const rows = rollUpPlantExposure(cells).slice(0, 6);
  const max = Math.max(1, ...rows.map((r) => r.exposure));

  return (
    <section className="rounded-md border border-line bg-card shadow-card overflow-hidden">
      <div className="flex items-center justify-between gap-2 px-md py-2.5 border-b border-line">
        <div className="flex items-center gap-2">
          <h3 className="font-display text-sm text-ink">Downtime exposure by plant</h3>
          <span className="text-xs text-ink-3">where missing parts hurt most</span>
        </div>
        <Link href="/risk" className="text-xs text-ai hover:underline">
          Risk & criticality →
        </Link>
      </div>
      <div className="p-md flex flex-col gap-2.5">
        {rows.map((r) => (
          <div key={r.plant} className="grid grid-cols-[120px_1fr_auto] items-center gap-3">
            <span className="font-mono text-xs text-ink-2 truncate">{r.plant}</span>
            <span className="h-2 rounded-pill bg-surface overflow-hidden">
              <span
                className="block h-full bg-crit"
                style={{ width: `${(r.exposure / max) * 100}%` }}
              />
            </span>
            <span className="font-mono text-xs text-ink text-right w-20">
              {currency.format(r.exposure)}
            </span>
          </div>
        ))}
        {rows.length === 0 ? (
          <p className="text-sm text-ink-3">No risk scores yet — run `make risk`.</p>
        ) : null}
      </div>
    </section>
  );
}
