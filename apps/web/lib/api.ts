/**
 * Minimal API client (CV1.E6).
 *
 * Attaches the bearer token to requests. The full typed SDK (generated from
 * OpenAPI) arrives with the data screens; this is the smallest thing that
 * proves the authenticated path end-to-end.
 */

import { clearToken, getToken } from '@/lib/auth';

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

/**
 * Handle an expired or otherwise invalid session: drop the dead token and send
 * the user back to sign-in. Without this, a stale token in localStorage passes
 * the (presence-only) route guard but 401s every request, leaving the page
 * silently empty.
 */
function handleUnauthorized(): void {
  clearToken();
  if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
    window.location.assign('/login');
  }
}

export interface Me {
  sub: string;
  tenant_id: string;
  email: string | null;
  roles: string[];
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (response.status === 401) {
    handleUnauthorized();
    throw new Error('Session expired — please sign in again.');
  }
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function devLogin(tenantSlug: string, roles: string[]): Promise<string> {
  const response = await fetch(`${API_URL}/auth/dev-login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tenant_slug: tenantSlug, roles }),
  });
  if (!response.ok) {
    throw new Error(`Dev login failed: ${response.status}`);
  }
  const data = (await response.json()) as { access_token: string };
  return data.access_token;
}

export function fetchMe(): Promise<Me> {
  return apiFetch<Me>('/me');
}

// --- Connectors (CV2.E1) -------------------------------------------------

export interface SyncRun {
  object_type: string;
  status: string;
  records_read: number;
  records_upserted: number;
  records_failed: number;
  finished_at: string | null;
}

export interface Connector {
  id: string;
  source_system: string;
  name: string;
  status: string;
  runs: SyncRun[];
}

export function fetchConnectors(): Promise<Connector[]> {
  return apiFetch<Connector[]>('/admin/connectors');
}

export function triggerFixtureSync(): Promise<Record<string, Record<string, number>>> {
  return apiFetch<Record<string, Record<string, number>>>('/admin/connectors/sync', {
    method: 'POST',
  });
}

// --- Inventory catalog (CV2.E2) ------------------------------------------

export interface ItemRow {
  id: string;
  item_number: string;
  description: string | null;
  uom: string | null;
  item_type: string | null;
  status: string | null;
  unit_cost: number | null;
  on_hand: number;
  inventory_value: number;
  locations: number;
  health_score: number | null;
  health_class: string | null;
  badges: string[];
}

export interface ItemsPage {
  items: ItemRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface InventorySummary {
  total_items: number;
  inventory_value: number;
  excess_value: number;
  dead_stock_value: number;
  disposal_candidates: number;
  completeness_pct: number;
  health_distribution: Record<string, number>;
}

export interface LocationRow {
  id: string;
  location_code: string;
  name: string | null;
}

export interface BalanceRow {
  location_code: string;
  on_hand: number;
  min_level: number | null;
  max_level: number | null;
  as_of: string | null;
}

export interface TransactionRow {
  type: string;
  quantity: number;
  txn_date: string | null;
  location_code: string | null;
}

export interface ItemDetail {
  id: string;
  item_number: string;
  description: string | null;
  uom: string | null;
  item_type: string | null;
  status: string | null;
  unit_cost: number | null;
  health_score: number | null;
  health_class: string | null;
  badges: string[];
  dimensions: Record<string, number>;
  balances: BalanceRow[];
  recent_transactions: TransactionRow[];
}

export interface ItemQuery {
  page?: number;
  page_size?: number;
  search?: string;
  item_type?: string;
  location_id?: string;
  missing_data?: boolean;
  health_class?: string;
  sort?: 'item_number' | 'value' | 'on_hand';
}

function queryString(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : '';
}

export function fetchInventorySummary(locationId?: string): Promise<InventorySummary> {
  return apiFetch<InventorySummary>(
    `/inventory/summary${queryString({ location_id: locationId })}`,
  );
}

export function fetchItems(query: ItemQuery): Promise<ItemsPage> {
  return apiFetch<ItemsPage>(`/inventory/items${queryString({ ...query })}`);
}

export function fetchLocations(): Promise<LocationRow[]> {
  return apiFetch<LocationRow[]>('/inventory/locations');
}

export function fetchItemDetail(id: string): Promise<ItemDetail> {
  return apiFetch<ItemDetail>(`/inventory/items/${id}`);
}

// --- Duplicate detection (CV2.E4) ----------------------------------------

export interface DuplicateItemSide {
  id: string;
  item_number: string;
  description: string | null;
  uom: string | null;
  item_type: string | null;
  status: string | null;
  unit_cost: number | null;
  health_score: number | null;
}

export interface DuplicateCandidate {
  id: string;
  confidence: number;
  band: string;
  status: string;
  model_version: string;
  item_a: DuplicateItemSide;
  item_b: DuplicateItemSide;
}

export interface DuplicateCandidateDetail extends DuplicateCandidate {
  features: Record<string, number>;
}

export interface DuplicatePage {
  candidates: DuplicateCandidate[];
  total: number;
  page: number;
  page_size: number;
}

export interface DuplicateSummary {
  open: number;
  probable: number;
  possible: number;
  resolved: number;
}

export type DuplicateDecision = 'merge' | 'not_duplicate' | 'hold';

export interface DuplicateReviewResult {
  id: string;
  status: string;
  recommendation_id: string | null;
}

export interface DuplicateQuery {
  page?: number;
  page_size?: number;
  band?: string;
  candidate_status?: string;
}

export function fetchDuplicateSummary(): Promise<DuplicateSummary> {
  return apiFetch<DuplicateSummary>('/duplicates/summary');
}

export function fetchDuplicates(query: DuplicateQuery): Promise<DuplicatePage> {
  return apiFetch<DuplicatePage>(`/duplicates${queryString({ ...query })}`);
}

export function fetchDuplicateDetail(id: string): Promise<DuplicateCandidateDetail> {
  return apiFetch<DuplicateCandidateDetail>(`/duplicates/${id}`);
}

export function reviewDuplicate(
  id: string,
  decision: DuplicateDecision,
  keepItemId?: string,
): Promise<DuplicateReviewResult> {
  return apiFetch<DuplicateReviewResult>(`/duplicates/${id}/review`, {
    method: 'POST',
    body: JSON.stringify({ decision, keep_item_id: keepItemId ?? null }),
  });
}

// --- Anomaly detection (CV2.E5) ------------------------------------------

export interface AnomalyRow {
  id: string;
  type: string;
  target_type: string;
  target_id: string;
  source_record_id: string | null;
  score: number;
  severity: string;
  status: string;
  detected_for: string | null;
  model_version: string;
  cause: string | null;
}

export interface AnomalyTransactionRef {
  source_id: string;
  item_number: string | null;
  description: string | null;
  location_code: string | null;
  quantity: number;
  unit_cost: number | null;
  txn_date: string | null;
}

export interface AnomalyDetail extends AnomalyRow {
  evidence: Record<string, number | string>;
  transaction: AnomalyTransactionRef | null;
}

export interface AnomalyPage {
  anomalies: AnomalyRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface AnomalySummary {
  open: number;
  crit: number;
  last_7_days: number;
  by_type: Record<string, number>;
}

export type AnomalyDecision = 'acknowledge' | 'dismiss';

export interface AnomalyQuery {
  page?: number;
  page_size?: number;
  type?: string;
  severity?: string;
  anomaly_status?: string;
  window_days?: number;
}

export function fetchAnomalySummary(): Promise<AnomalySummary> {
  return apiFetch<AnomalySummary>('/anomalies/summary');
}

export function fetchAnomalies(query: AnomalyQuery): Promise<AnomalyPage> {
  return apiFetch<AnomalyPage>(`/anomalies${queryString({ ...query })}`);
}

export function fetchAnomalyDetail(id: string): Promise<AnomalyDetail> {
  return apiFetch<AnomalyDetail>(`/anomalies/${id}`);
}

export function reviewAnomaly(id: string, decision: AnomalyDecision): Promise<AnomalyRow> {
  return apiFetch<AnomalyRow>(`/anomalies/${id}/review`, {
    method: 'POST',
    body: JSON.stringify({ decision }),
  });
}

// --- Recommendations (CV3) -----------------------------------------------

export interface RecommendationRow {
  id: string;
  type: string;
  target_id: string;
  item_number: string | null;
  description: string | null;
  claim: string;
  confidence: number | null;
  recommended_action: string | null;
  capital_delta: number | null;
  status: string;
  model_version: string | null;
}

export interface ParetoPoint {
  service_level: number;
  capital: number;
  stockout_prob: number;
}

export interface RecommendationEnvelope extends RecommendationRow {
  payload: Record<string, number | string | null>;
  evidence: Record<string, unknown>;
  assumptions: Record<string, unknown>;
  approval_path: string | null;
}

export interface RecommendationPage {
  recommendations: RecommendationRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface RecommendationSummary {
  proposed: number;
  actionable: number;
  capital_delta: number;
  avg_confidence: number;
  by_action: Record<string, number>;
}

export interface AcceptanceRateRow {
  model_version: string;
  total: number;
  accepted: number;
  adjusted: number;
  overridden: number;
  acceptance_rate: number;
}

export interface RegimeSignalRow {
  id: string;
  item_id: string;
  item_number: string | null;
  dimension: string;
  override_count: number;
  last_reason_note: string | null;
  status: string;
  is_regime_change: boolean;
}

export const OVERRIDE_REASONS = [
  { value: 'asset_retirement', label: 'Asset retirement' },
  { value: 'strategy_shift', label: 'Strategy shift' },
  { value: 'supply_change', label: 'Supply change' },
  { value: 'demand_change', label: 'Demand change' },
  { value: 'other', label: 'Other' },
] as const;

export interface RecommendationQuery {
  page?: number;
  page_size?: number;
  rec_status?: string;
  action?: string;
}

export function fetchRecommendationSummary(): Promise<RecommendationSummary> {
  return apiFetch<RecommendationSummary>('/recommendations/summary');
}

export function fetchRecommendations(query: RecommendationQuery): Promise<RecommendationPage> {
  return apiFetch<RecommendationPage>(`/recommendations${queryString({ ...query })}`);
}

export function fetchRecommendationDetail(id: string): Promise<RecommendationEnvelope> {
  return apiFetch<RecommendationEnvelope>(`/recommendations/${id}`);
}

export function acceptRecommendation(id: string): Promise<{ id: string; status: string }> {
  return apiFetch(`/recommendations/${id}/accept`, { method: 'POST' });
}

export function overrideRecommendation(
  id: string,
  reasonCode: string,
  note?: string,
): Promise<{ id: string; status: string }> {
  return apiFetch(`/recommendations/${id}/override`, {
    method: 'POST',
    body: JSON.stringify({ decision: 'override', reason_code: reasonCode, reason_note: note }),
  });
}

export function fetchAcceptanceRate(): Promise<AcceptanceRateRow[]> {
  return apiFetch<AcceptanceRateRow[]>('/recommendations/acceptance-rate');
}

export function fetchRegimeSignals(): Promise<RegimeSignalRow[]> {
  return apiFetch<RegimeSignalRow[]>('/recommendations/regime-signals');
}

// --- Conversational analyst: Ask SmartInv (CV5.E2) ------------------------

export interface AgentToolCall {
  name: string;
  version: string;
  source: string;
}

export interface AgentEvidence {
  metric: string;
  label: string;
  value: number;
  source: string;
}

export interface AgentAnswer {
  answer: string;
  grounded: boolean;
  confidence: number;
  model: string;
  tool_calls: AgentToolCall[];
  evidence: AgentEvidence[];
}

/** Error carrying the HTTP status so the UI can distinguish 503 (unconfigured). */
export class AnalystError extends Error {
  constructor(public readonly status: number) {
    super(`Ask SmartInv failed: ${status}`);
    this.name = 'AnalystError';
  }
}

export async function askSmartInv(question: string): Promise<AgentAnswer> {
  const headers = new Headers({ 'Content-Type': 'application/json' });
  const token = getToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  const response = await fetch(`${API_URL}/agents/run`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ question }),
  });
  if (response.status === 401) {
    handleUnauthorized();
    throw new AnalystError(401);
  }
  if (!response.ok) {
    throw new AnalystError(response.status);
  }
  return (await response.json()) as AgentAnswer;
}

// --- Demand forecasting (CV3.E1) -----------------------------------------

export interface ForecastItemRow {
  id: string;
  item_number: string;
  description: string | null;
  method: string;
  rate: number;
  p50: number;
  p80: number;
  p95: number;
  cv: number;
  demand_events: number;
  model_version: string;
}

export interface ForecastItemsPage {
  items: ForecastItemRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface ForecastSummary {
  forecasted: number;
  total_items: number;
  coverage_pct: number;
  obsolescence_trending: number;
  avg_cv: number;
  by_method: Record<string, number>;
  model_version: string;
}

export interface ForecastItemDetail extends ForecastItemRow {
  horizon: number;
  period_days: number;
  history: number[];
  diagnostics: Record<string, number>;
  predicted_at: string | null;
  input_fingerprint: string | null;
}

export interface ForecastQuery {
  page?: number;
  page_size?: number;
  method?: string;
}

export function fetchForecastSummary(): Promise<ForecastSummary> {
  return apiFetch<ForecastSummary>('/forecast/summary');
}

export function fetchForecastItems(query: ForecastQuery): Promise<ForecastItemsPage> {
  return apiFetch<ForecastItemsPage>(`/forecast/items${queryString({ ...query })}`);
}

export function fetchForecastItemDetail(id: string): Promise<ForecastItemDetail> {
  return apiFetch<ForecastItemDetail>(`/forecast/items/${id}`);
}

// --- Operational risk (CV4) ----------------------------------------------

export interface RiskItemRow {
  id: string;
  item_number: string;
  description: string | null;
  criticality: number | null;
  risk_score: number | null;
  risk_class: string | null;
  downtime_exposure: number;
  is_critical_spare: boolean;
  single_source: boolean;
  supplier_on_time_rate: number | null;
}

export interface RiskItemDetail extends RiskItemRow {
  breakdown: Record<string, number>;
  narrative: string;
  has_mitigation_policy: boolean;
}

export interface RiskItemsPage {
  items: RiskItemRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface RiskSummary {
  downtime_exposure: number;
  critical_spares: number;
  critical_spare_coverage: number;
  single_source_items: number;
  obsolescence_candidates: number;
  risk_distribution: Record<string, number>;
}

export interface HeatmapRow {
  location_code: string;
  scores: Record<string, number>;
}

export interface ExposureCell {
  location_code: string;
  risk_class: string;
  count: number;
  exposure: number;
}

export interface RiskQuery {
  page?: number;
  page_size?: number;
  risk_class?: string;
  critical_only?: boolean;
}

export function fetchRiskSummary(): Promise<RiskSummary> {
  return apiFetch<RiskSummary>('/risk/summary');
}

export function fetchRiskHeatmap(): Promise<HeatmapRow[]> {
  return apiFetch<HeatmapRow[]>('/risk/heatmap');
}

export function fetchRiskExposure(): Promise<ExposureCell[]> {
  return apiFetch<ExposureCell[]>('/risk/exposure');
}

export function fetchRiskItems(query: RiskQuery): Promise<RiskItemsPage> {
  return apiFetch<RiskItemsPage>(`/risk/items${queryString({ ...query })}`);
}

export function fetchRiskItemDetail(id: string): Promise<RiskItemDetail> {
  return apiFetch<RiskItemDetail>(`/risk/items/${id}`);
}

export function mitigateRisk(id: string): Promise<{ recommendation_id: string; status: string }> {
  return apiFetch(`/risk/items/${id}/mitigate`, { method: 'POST' });
}

// --- Approval queue (CV6.E2) ---------------------------------------------

export type ApprovalBucket = 'my_queue' | 'semi' | 'completed' | 'overrides' | 'all';
export type ApprovalUiState = 'pending' | 'active' | 'approved' | 'rejected';

export interface ApprovalStepRow {
  state: string;
  reviewer_type: 'role' | 'user';
  reviewer: string;
  ui_state: ApprovalUiState;
}

export interface ApprovalRow {
  id: string;
  workflow_type: string;
  state: string;
  current_reviewer_type: string | null;
  current_reviewer: string | null;
  current_actor: string | null;
  created_at: string;
  updated_at: string;
  recommendation_id: string | null;
  claim: string;
  target_label: string;
  confidence: number | null;
  model_version: string | null;
  evidence: Array<{ metric: string; value: string; sourceHref?: string }>;
  impact: Record<string, string>;
  steps: ApprovalStepRow[];
}

export interface ApprovalPage {
  approvals: ApprovalRow[];
  total: number;
}

export interface ApprovalPolicyRow {
  id: string;
  workflow_type: string;
  min_value: number | null;
  max_value: number | null;
  min_criticality: number | null;
  required_path: Array<{ state: string; reviewer_type: 'role' | 'user'; reviewer: string }>;
  priority: number;
  status: string;
}

export function fetchApprovals(bucket: ApprovalBucket): Promise<ApprovalPage> {
  return apiFetch<ApprovalPage>(`/approvals${queryString({ bucket })}`);
}

export function transitionApproval(
  id: string,
  action: 'approve' | 'request_changes' | 'reject',
  reasonCode?: string,
  reasonNote?: string,
): Promise<{ id: string; state: string }> {
  return apiFetch(`/approvals/${id}/actions`, {
    method: 'POST',
    body: JSON.stringify({
      action,
      reason_code: reasonCode,
      reason_note: reasonNote,
      idempotency_key: `${action}-${id}-${Date.now()}`,
    }),
  });
}

export function fetchApprovalPolicies(): Promise<ApprovalPolicyRow[]> {
  return apiFetch<ApprovalPolicyRow[]>('/approvals/policies');
}

// --- Audit trail (CV6.E3) ------------------------------------------------

export interface AuditEventRow {
  id: number;
  actor: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  payload: Record<string, unknown>;
  occurred_at: string;
}

export interface AuditPage {
  events: AuditEventRow[];
  total: number;
}

export interface AuditQuery {
  actor?: string;
  action?: string;
  resource_type?: string;
  limit?: number;
}

export function fetchAuditEvents(query: AuditQuery = {}): Promise<AuditPage> {
  return apiFetch<AuditPage>(`/audit/events${queryString({ ...query })}`);
}

export async function exportAuditCsv(query: AuditQuery = {}): Promise<string> {
  const headers = new Headers();
  const token = getToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  const response = await fetch(`${API_URL}/audit/events.csv${queryString({ ...query })}`, {
    headers,
  });
  if (!response.ok) {
    throw new Error(`Audit CSV export failed: ${response.status}`);
  }
  return response.text();
}

// --- Source-system write dispatch (CV6.E4) -------------------------------

export interface SourceWriteRow {
  id: string;
  recommendation_id: string | null;
  target_system: string;
  operation: string;
  status: string;
  attempts: number;
  max_attempts: number;
  last_error: string | null;
  receipt: Record<string, unknown>;
  updated_at: string;
}

export function fetchSourceWrites(status?: string): Promise<SourceWriteRow[]> {
  return apiFetch<SourceWriteRow[]>(`/approvals/dispatch${queryString({ status })}`);
}
