'use client';

import { type AuditEventRow, exportAuditCsv, fetchAuditEvents } from '@/lib/api';
import { Badge, Button } from '@smartinv/ui-web';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useState } from 'react';

const ACTIONS = [
  '',
  'approval.approve',
  'approval.reject',
  'recommendation.accept',
  'recommendation.override',
  'duplicate.review',
  'anomaly.review',
  'risk.mitigate',
];

export function AuditTrail() {
  const [action, setAction] = useState('');
  const [actor, setActor] = useState('');
  const query = { action: action || undefined, actor: actor || undefined, limit: 100 };
  const events = useQuery({
    queryKey: ['audit-events', query],
    queryFn: () => fetchAuditEvents(query),
  });
  const csv = useMutation({
    mutationFn: () => exportAuditCsv(query),
    onSuccess: (content) => {
      const blob = new Blob([content], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'audit-events.csv';
      link.click();
      URL.revokeObjectURL(url);
    },
  });

  return (
    <section className="rounded-md border border-line bg-card shadow-card p-md flex flex-col gap-3">
      <div className="flex flex-wrap items-start gap-3">
        <div>
          <h2 className="font-medium text-ink">Audit Trail</h2>
          <p className="text-sm text-ink-3 mt-1">
            Append-only events for approvals, recommendations, reviews, and admin jobs.
          </p>
        </div>
        <span className="flex-1" />
        <Button size="sm" onClick={() => csv.mutate()} disabled={csv.isPending}>
          Export CSV
        </Button>
      </div>

      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={action}
          onChange={(event) => setAction(event.target.value)}
          className="rounded-md border border-line bg-card px-2 py-2 text-sm text-ink"
        >
          {ACTIONS.map((value) => (
            <option key={value || 'all'} value={value}>
              {value || 'All actions'}
            </option>
          ))}
        </select>
        <input
          value={actor}
          onChange={(event) => setActor(event.target.value)}
          placeholder="Filter actor"
          className="rounded-md border border-line bg-card px-2 py-2 text-sm text-ink"
        />
      </div>

      {events.isLoading ? <div className="text-sm text-ink-3">Loading audit events…</div> : null}
      {events.isError ? (
        <div className="text-sm text-crit">Audit trail requires admin or finance role.</div>
      ) : null}
      <div className="overflow-x-auto rounded-md border border-line">
        <table className="w-full text-sm">
          <thead className="bg-surface text-ink-3">
            <tr>
              <th className="text-left px-3 py-2 font-medium">Time</th>
              <th className="text-left px-3 py-2 font-medium">Action</th>
              <th className="text-left px-3 py-2 font-medium">Actor</th>
              <th className="text-left px-3 py-2 font-medium">Resource</th>
            </tr>
          </thead>
          <tbody>
            {(events.data?.events ?? []).map((event) => (
              <AuditRow key={event.id} event={event} />
            ))}
            {events.data && events.data.events.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-3 py-6 text-center text-ink-3">
                  No audit events match this filter.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function AuditRow({ event }: { event: AuditEventRow }) {
  return (
    <tr className="border-t border-line align-top">
      <td className="px-3 py-2 font-mono text-xs text-ink-3">
        {new Date(event.occurred_at).toLocaleString()}
      </td>
      <td className="px-3 py-2">
        <Badge label={event.action} variant="neutral" />
      </td>
      <td className="px-3 py-2 text-ink-2">{event.actor ?? 'system'}</td>
      <td className="px-3 py-2 text-ink-2">
        <span className="font-mono text-xs">{event.resource_type ?? '—'}</span>
        {event.resource_id ? (
          <div className="font-mono text-[10px] text-ink-3">{event.resource_id}</div>
        ) : null}
      </td>
    </tr>
  );
}
