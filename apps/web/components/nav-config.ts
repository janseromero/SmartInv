/**
 * Single source of truth for the sidebar + every screen's page-head.
 *
 * Adding a route is one edit here: a new entry creates the sidebar item,
 * the page metadata, and the type-safe lookup.
 */
import type { IconName } from './icons';

export interface RouteMeta {
  /** URL path under the (app) route group. `/` for the overview. */
  href: string;
  /** Sidebar label. */
  label: string;
  /** Page-head crumb (small uppercase line). */
  crumb: string;
  /** Page-head H1. */
  title: string;
  /** Page-head sub-line. */
  sub: string;
  /** Sidebar icon. */
  icon: IconName;
  /** Optional sidebar pill (count or 'AI' badge). */
  pill?: { value: string; tone: 'crit' | 'ai' };
  /** Optional pointer to the CV that ships real content. */
  shipsIn?: string;
  /**
   * Hide from the sidebar without removing the route. The page, URL, and
   * page-head lookup stay intact (still reachable directly); it just isn't
   * listed in the nav. Used to park deferred Phase-2 placeholders.
   */
  hidden?: boolean;
}

export interface RouteGroup {
  label: string;
  routes: RouteMeta[];
}

export const ROUTE_GROUPS: RouteGroup[] = [
  {
    label: 'Overview',
    routes: [
      {
        href: '/',
        label: 'Executive Overview',
        crumb: 'Overview · All sites',
        title: 'Executive Overview',
        sub: 'Working capital, risk and opportunity across plants — every figure traceable to source records.',
        icon: 'grid',
      },
    ],
  },
  {
    label: 'Operate',
    routes: [
      {
        href: '/health',
        label: 'Inventory Health',
        crumb: 'Operate · Inventory visibility & health',
        title: 'Inventory Health',
        sub: 'Stock position, health scoring and item-master quality across every site and storeroom.',
        icon: 'activity',
        shipsIn: 'CV2',
      },
      {
        href: '/duplicates',
        label: 'Duplicate Detection',
        crumb: 'Operate · Item-master duplicate detection',
        title: 'Duplicate Detection',
        sub: 'Probable item-master duplicates surfaced for review — every pair scored, explained, and merged only through approval.',
        icon: 'database',
        shipsIn: 'CV2.E4',
      },
      {
        href: '/forecast',
        label: 'Demand Forecasting',
        crumb: 'Operate · Demand forecasting',
        title: 'Demand Forecasting',
        sub: 'Probabilistic forecasts built for intermittent MRO demand — with confidence bands on every horizon.',
        icon: 'trend',
      },
      {
        href: '/optimize',
        label: 'Optimization',
        crumb: 'Operate · Inventory optimization',
        title: 'Optimization Recommendations',
        sub: 'Min/max, safety stock and action recommendations — every one explainable, simulated and reversible.',
        icon: 'shuffle',
        pill: { value: '14', tone: 'crit' },
        shipsIn: 'CV3',
      },
      {
        href: '/risk',
        label: 'Risk & Criticality',
        crumb: 'Operate · Criticality & operational risk',
        title: 'Risk & Criticality',
        sub: 'Where missing parts hurt: downtime exposure, critical-spare coverage and supply concentration.',
        icon: 'triangleAlert',
        shipsIn: 'CV4',
      },
      {
        href: '/procure',
        label: 'Procurement',
        crumb: 'Operate · Procurement & supplier intelligence',
        title: 'Procurement & Suppliers',
        sub: 'Act earlier on late POs, negotiate with price evidence, and reduce supply-side uncertainty.',
        icon: 'cart',
        shipsIn: 'CV9',
        hidden: true,
      },
    ],
  },
  {
    label: 'Intelligence',
    routes: [
      {
        href: '/analyst',
        label: 'Ask SmartInv',
        crumb: 'Intelligence · Conversational analyst',
        title: 'Ask SmartInv',
        sub: 'Natural language over governed inventory, usage, work-order and procurement data — answers carry their evidence.',
        icon: 'clock',
        pill: { value: 'AI', tone: 'ai' },
      },
      {
        href: '/agents',
        label: 'Agent Console',
        crumb: 'Intelligence · Agentic orchestration',
        title: 'Agent Console',
        sub: 'Specialized agents under human governance — scoped tools, full audit, no direct writes to source systems.',
        icon: 'agent',
        shipsIn: 'CV11',
        hidden: true,
      },
      {
        href: '/reports',
        label: 'Reports & Stories',
        crumb: 'Intelligence · Visualization, reporting & storytelling',
        title: 'Reports & Stories',
        sub: 'Board-ready narratives and operational reviews — generated from governed metrics, linked back to source records.',
        icon: 'document',
        shipsIn: 'CV10',
        hidden: true,
      },
    ],
  },
  {
    label: 'Govern',
    routes: [
      {
        href: '/approvals',
        label: 'Approvals',
        crumb: 'Govern · Human-in-the-loop workflows',
        title: 'Approvals',
        sub: 'High-risk actions require explicit approval. Low-risk actions can be semi-automated within policy limits.',
        icon: 'shield',
        pill: { value: '6', tone: 'crit' },
        shipsIn: 'CV6',
      },
      {
        href: '/quality',
        label: 'Data Quality',
        crumb: 'Govern · Data quality intelligence',
        title: 'Data Quality',
        sub: 'Is the data good enough to trust the recommendations? Confidence limits are surfaced, never hidden.',
        icon: 'database',
        shipsIn: 'CV7',
      },
      {
        href: '/settings',
        label: 'Admin & Governance',
        crumb: 'Govern · Administration',
        title: 'Admin & Governance',
        sub: 'Connectors, identity, model registry and audit — the controls under everything else.',
        icon: 'cog',
        shipsIn: 'CV1.E6 + CV15',
      },
    ],
  },
];

export const ROUTES: RouteMeta[] = ROUTE_GROUPS.flatMap((g) => g.routes);

export const ROUTE_BY_HREF: Map<string, RouteMeta> = new Map(ROUTES.map((r) => [r.href, r]));
