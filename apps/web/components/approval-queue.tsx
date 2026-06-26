'use client';

import {
  type ApprovalBucket,
  type ApprovalPolicyRow,
  type ApprovalRow,
  fetchApprovalPolicies,
  fetchApprovals,
  transitionApproval,
} from '@/lib/api';
import { ApprovalStep, Badge, Button, EvidenceStrip, KpiCard } from '@smartinv/ui-web';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

const integer = new Intl.NumberFormat('en-US');

const TABS: Array<{ value: ApprovalBucket; label: string }> = [
  { value: 'my_queue', label: 'My queue' },
  { value: 'semi', label: 'Semi-automated' },
  { value: 'completed', label: 'Completed' },
  { value: 'overrides', label: 'Overrides' },
];

const STATE_TONE: Record<string, 'ok' | 'warn' | 'crit'> = {
  approved: 'ok',
  rejected: 'crit',
  agent_proposed: 'warn',
  planner_review: 'warn',
  manager_review: 'warn',
  finance_review: 'warn',
};

const DEFAULT_REASON = 'missing_evidence';
const ACTION_REASONS = [
  { value: 'missing_evidence', label: 'Missing evidence' },
  { value: 'policy_exception', label: 'Policy exception' },
  { value: 'source_data_issue', label: 'Source data issue' },
  { value: 'business_context', label: 'Business context changed' },
];

export function ApprovalQueue() {
  const [bucket, setBucket] = useState<ApprovalBucket>('my_queue');
  const approvals = useQuery({
    queryKey: ['approvals', bucket],
    queryFn: () => fetchApprovals(bucket),
  });
  const policies = useQuery({ queryKey: ['approval-policies'], queryFn: fetchApprovalPolicies });

  const counts = useMemo(() => {
    const rows = approvals.data?.approvals ?? [];
    return {
      visible: rows.length,
      active: rows.filter((a) => !['approved', 'rejected'].includes(a.state)).length,
      completed: rows.filter((a) => ['approved', 'rejected'].includes(a.state)).length,
      finance: rows.filter((a) => a.current_reviewer === 'finance').length,
    };
  }, [approvals.data]);

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard label="Visible approvals" value={integer.format(counts.visible)} />
        <KpiCard label="Active" value={integer.format(counts.active)} status="warn" />
        <KpiCard label="Finance review" value={integer.format(counts.finance)} />
        <KpiCard label="Completed" value={integer.format(counts.completed)} status="ok" />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {TABS.map((tab) => (
          <button
            key={tab.value}
            type="button"
            onClick={() => setBucket(tab.value)}
            className={`rounded-md border px-md py-1.5 text-sm ${
              bucket === tab.value
                ? 'border-ink text-ink bg-surface'
                : 'border-line text-ink-2 hover:bg-surface'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-4 items-start">
        <div className="flex flex-col gap-3">
          {approvals.isLoading ? (
            <div className="text-sm text-ink-3">Loading approvals…</div>
          ) : null}
          {approvals.data?.approvals.map((approval) => (
            <ApprovalCard key={approval.id} approval={approval} />
          ))}
          {approvals.data && approvals.data.approvals.length === 0 ? (
            <div className="rounded-md border border-line bg-card p-md text-sm text-ink-3">
              No approvals in this queue. Generate recommendations and submit them to workflow.
            </div>
          ) : null}
          {approvals.isError ? (
            <div className="rounded-md border border-crit bg-card p-md text-sm text-crit">
              Could not load approvals. Check your role and API connection.
            </div>
          ) : null}
        </div>

        <PolicyPanel policies={policies.data ?? []} loading={policies.isLoading} />
      </div>
    </div>
  );
}

function ApprovalCard({ approval }: { approval: ApprovalRow }) {
  const queryClient = useQueryClient();
  const [reason, setReason] = useState(DEFAULT_REASON);
  const [note, setNote] = useState('');
  const [expanded, setExpanded] = useState(false);
  const terminal = ['approved', 'rejected'].includes(approval.state);

  const mutate = useMutation({
    mutationFn: (action: 'approve' | 'request_changes' | 'reject') =>
      transitionApproval(approval.id, action, reason, note),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['approvals'] });
      setExpanded(false);
      setNote('');
    },
  });

  return (
    <div className="rounded-md border border-line bg-card shadow-card p-md flex flex-col gap-3">
      <div className="flex items-start gap-2 flex-wrap">
        <div>
          <h3 className="font-medium text-ink">{approval.target_label}</h3>
          <p className="text-sm text-ink-2 mt-1">{approval.claim}</p>
        </div>
        <span className="flex-1" />
        <Badge
          label={approval.state.replaceAll('_', ' ')}
          variant="status"
          tone={STATE_TONE[approval.state] ?? 'warn'}
        />
        <Badge label={approval.workflow_type.replaceAll('_', ' ')} variant="ai" />
      </div>

      <EvidenceStrip
        items={approval.evidence}
        confidence={approval.confidence ?? undefined}
        modelVersion={approval.model_version ?? undefined}
      />

      {Object.keys(approval.impact).length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
          {Object.entries(approval.impact).map(([key, value]) => (
            <div key={key} className="rounded-md bg-surface border border-line p-2">
              <div className="text-ink-3">{key.replaceAll('_', ' ')}</div>
              <div className="font-mono text-ink">{value}</div>
            </div>
          ))}
        </div>
      ) : null}

      <div className="rounded-md border border-line p-md bg-surface/60">
        <div className="text-xs uppercase tracking-wide text-ink-3 mb-2">Approval path</div>
        <div className="flex flex-col md:flex-row gap-3 md:items-center md:flex-wrap">
          {approval.steps.map((step) => (
            <ApprovalStep
              key={`${approval.id}-${step.state}-${step.reviewer}`}
              label={step.state.replaceAll('_', ' ')}
              state={step.ui_state}
              actor={`${step.reviewer_type}: ${step.reviewer}`}
            />
          ))}
        </div>
      </div>

      {!terminal ? (
        <div className="flex flex-wrap gap-2 items-center">
          <Button
            variant="primary"
            size="sm"
            onClick={() => mutate.mutate('approve')}
            disabled={mutate.isPending}
          >
            Approve
          </Button>
          <Button variant="default" size="sm" onClick={() => setExpanded((v) => !v)}>
            Request changes
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => mutate.mutate('reject')}
            disabled={mutate.isPending}
          >
            Reject
          </Button>
          {mutate.isError ? <span className="text-xs text-crit">Action failed.</span> : null}
        </div>
      ) : null}

      {expanded ? (
        <div className="rounded-md border border-line bg-surface p-md flex flex-col gap-2">
          <label className="text-xs text-ink-3" htmlFor={`reason-${approval.id}`}>
            Reason
          </label>
          <select
            id={`reason-${approval.id}`}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            className="rounded-md border border-line bg-card px-2 py-2 text-sm text-ink"
          >
            {ACTION_REASONS.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
          <textarea
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Add context for the requester…"
            className="min-h-20 rounded-md border border-line bg-card px-2 py-2 text-sm text-ink"
          />
          <div>
            <Button
              variant="primary"
              size="sm"
              onClick={() => mutate.mutate('request_changes')}
              disabled={mutate.isPending}
            >
              Send request
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function PolicyPanel({ policies, loading }: { policies: ApprovalPolicyRow[]; loading: boolean }) {
  return (
    <aside className="rounded-md border border-line bg-card shadow-card p-md flex flex-col gap-3">
      <div>
        <h2 className="font-medium text-ink">Automation policy</h2>
        <p className="text-sm text-ink-3 mt-1">
          Read-only MVP view of the rules that choose approvers.
        </p>
      </div>
      {loading ? <div className="text-sm text-ink-3">Loading policies…</div> : null}
      {policies.length === 0 && !loading ? (
        <div className="text-sm text-ink-3">
          No configured policies yet. The engine falls back to planner review.
        </div>
      ) : null}
      <div className="flex flex-col gap-2">
        {policies.map((policy) => (
          <div key={policy.id} className="rounded-md border border-line p-3 bg-surface/60">
            <div className="flex items-center gap-2">
              <span className="font-medium text-sm text-ink">
                {policy.workflow_type.replaceAll('_', ' ')}
              </span>
              <Badge label={`P${policy.priority}`} variant="neutral" />
              <Badge
                label={policy.status}
                variant="status"
                tone={policy.status === 'active' ? 'ok' : 'warn'}
              />
            </div>
            <div className="mt-2 text-xs text-ink-3">
              {policy.min_value !== null ? (
                <span>value ≥ ${policy.min_value.toLocaleString()} · </span>
              ) : null}
              {policy.min_criticality !== null ? (
                <span>criticality ≥ {policy.min_criticality} · </span>
              ) : null}
              <span>{policy.required_path.length} step path</span>
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              {policy.required_path.map((step) => (
                <span
                  key={`${policy.id}-${step.state}-${step.reviewer}`}
                  className="rounded bg-card border border-line px-2 py-1 text-[11px] text-ink-2"
                >
                  {step.state.replaceAll('_', ' ')} · {step.reviewer_type}: {step.reviewer}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
