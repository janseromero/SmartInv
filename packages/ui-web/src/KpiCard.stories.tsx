import { KpiCard } from './KpiCard.js';

export const Default = () => <KpiCard label="Inventory Value" value="$4.2M" />;

export const WithDelta = () => (
  <KpiCard label="Excess Capital" value="$812K" delta="6.4% vs last month" trend="down" />
);

export const Statuses = () => (
  <div className="flex gap-3">
    <KpiCard label="Service Level" value="98%" status="ok" />
    <KpiCard label="Stockout Risk" value="12" unit="items" status="warn" />
    <KpiCard label="Critical Gaps" value="3" status="crit" trend="up" delta="+2" />
  </div>
);

export const Loading = () => <KpiCard label="Inventory Value" value="" loading />;

export const Dense = () => <KpiCard label="Turns" value="4.1" dense />;
