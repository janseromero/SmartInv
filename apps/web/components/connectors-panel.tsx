'use client';

import { type Connector, fetchConnectors, triggerFixtureSync } from '@/lib/api';
import { useCallback, useEffect, useState } from 'react';

const STATUS_TONE: Record<string, string> = {
  success: 'bg-ok-soft text-ok',
  active: 'bg-ok-soft text-ok',
  partial: 'bg-warn-soft text-warn',
  running: 'bg-surface text-ink-2',
  failed: 'bg-crit-soft text-crit',
};

function StatusBadge({ status }: { status: string }) {
  const tone = STATUS_TONE[status] ?? 'bg-surface text-ink-2';
  return (
    <span className={`inline-flex rounded-pill px-2 py-0.5 text-xs font-medium ${tone}`}>
      {status}
    </span>
  );
}

/**
 * Read-only connector governance panel (CV2.E1). Lists source connectors and
 * their recent sync runs. No credentials are entered here — Maximo credentials
 * live in the secret manager (ADR-024).
 */
export function ConnectorsPanel() {
  const [connectors, setConnectors] = useState<Connector[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  const load = useCallback(async () => {
    try {
      setConnectors(await fetchConnectors());
      setError(null);
    } catch {
      setError('Could not load connectors (admin role required).');
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onSync(): Promise<void> {
    setSyncing(true);
    try {
      await triggerFixtureSync();
      await load();
    } catch {
      setError('Sync failed (admin role required).');
    } finally {
      setSyncing(false);
    }
  }

  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-base text-ink">Source Connectors</h2>
        <button
          type="button"
          onClick={onSync}
          disabled={syncing}
          className="rounded-md bg-teal px-md py-1.5 text-sm text-card hover:bg-teal-dark disabled:opacity-60"
        >
          {syncing ? 'Syncing…' : 'Run fixture sync'}
        </button>
      </div>

      {error ? <p className="text-sm text-crit">{error}</p> : null}

      {connectors?.length === 0 ? (
        <p className="text-sm text-ink-3">No connectors yet. Run a fixture sync to create one.</p>
      ) : null}

      {connectors?.map((connector) => (
        <div key={connector.id} className="rounded-md border border-line bg-card p-md shadow-card">
          <div className="flex items-center gap-2">
            <span className="font-medium text-ink">{connector.name}</span>
            <span className="font-mono text-xs text-ink-3">{connector.source_system}</span>
            <StatusBadge status={connector.status} />
          </div>
          {connector.runs.length > 0 ? (
            <table className="mt-3 w-full text-sm">
              <thead>
                <tr className="text-left text-ink-3">
                  <th className="font-normal py-1">Entity</th>
                  <th className="font-normal py-1">Status</th>
                  <th className="font-normal py-1 text-right">Upserted</th>
                  <th className="font-normal py-1 text-right">Failed</th>
                </tr>
              </thead>
              <tbody>
                {connector.runs.map((run) => (
                  <tr
                    key={`${run.object_type}-${run.finished_at}`}
                    className="border-t border-line"
                  >
                    <td className="py-1 font-mono text-ink-2">{run.object_type}</td>
                    <td className="py-1">
                      <StatusBadge status={run.status} />
                    </td>
                    <td className="py-1 text-right text-ink">{run.records_upserted}</td>
                    <td className="py-1 text-right text-ink-2">{run.records_failed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="mt-2 text-sm text-ink-3">No sync runs yet.</p>
          )}
        </div>
      ))}
    </section>
  );
}
