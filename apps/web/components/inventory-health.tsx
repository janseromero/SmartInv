'use client';

import {
  type ItemRow,
  fetchInventorySummary,
  fetchItemDetail,
  fetchItems,
  fetchLocations,
} from '@/lib/api';
import { Badge, KpiCard } from '@smartinv/ui-web';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

const ITEM_TYPES = ['SPARE', 'CONSUMABLE', 'TOOL', 'LUBRICANT'];
const PAGE_SIZE = 25;

const currency = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
  notation: 'compact',
});
const integer = new Intl.NumberFormat('en-US');

function completenessStatus(pct: number): 'ok' | 'warn' | 'crit' {
  if (pct >= 90) return 'ok';
  if (pct >= 70) return 'warn';
  return 'crit';
}

export function InventoryHealth() {
  const [search, setSearch] = useState('');
  const [locationId, setLocationId] = useState('');
  const [itemType, setItemType] = useState('');
  const [missingData, setMissingData] = useState(false);
  const [sort, setSort] = useState<'item_number' | 'value' | 'on_hand'>('item_number');
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<string | null>(null);

  const locations = useQuery({ queryKey: ['locations'], queryFn: fetchLocations });
  const summary = useQuery({
    queryKey: ['summary', locationId],
    queryFn: () => fetchInventorySummary(locationId || undefined),
  });
  const items = useQuery({
    queryKey: ['items', { search, locationId, itemType, missingData, sort, page }],
    queryFn: () =>
      fetchItems({
        page,
        page_size: PAGE_SIZE,
        search: search || undefined,
        item_type: itemType || undefined,
        location_id: locationId || undefined,
        missing_data: missingData || undefined,
        sort,
      }),
  });

  const totalPages = items.data ? Math.max(1, Math.ceil(items.data.total / PAGE_SIZE)) : 1;
  const s = summary.data;

  return (
    <div className="flex flex-col gap-4">
      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard label="Items" value={s ? integer.format(s.total_items) : '—'} />
        <KpiCard label="Inventory Value" value={s ? currency.format(s.inventory_value) : '—'} />
        <KpiCard
          label="Excess Value"
          value={s ? currency.format(s.excess_value) : '—'}
          status={s && s.excess_value > 0 ? 'warn' : 'ok'}
        />
        <KpiCard
          label="Item-master Completeness"
          value={s ? `${s.completeness_pct}%` : '—'}
          status={s ? completenessStatus(s.completeness_pct) : undefined}
        />
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2">
        <input
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          placeholder="Search item number or description…"
          className="flex-1 min-w-[220px] bg-card border border-line rounded-md px-md py-1.5 text-sm text-ink"
        />
        <select
          value={locationId}
          onChange={(e) => {
            setLocationId(e.target.value);
            setPage(1);
          }}
          className="bg-card border border-line rounded-md px-md py-1.5 text-sm text-ink"
        >
          <option value="">All sites</option>
          {locations.data?.map((loc) => (
            <option key={loc.id} value={loc.id}>
              {loc.location_code}
            </option>
          ))}
        </select>
        <select
          value={itemType}
          onChange={(e) => {
            setItemType(e.target.value);
            setPage(1);
          }}
          className="bg-card border border-line rounded-md px-md py-1.5 text-sm text-ink"
        >
          <option value="">All types</option>
          {ITEM_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as 'item_number' | 'value' | 'on_hand')}
          className="bg-card border border-line rounded-md px-md py-1.5 text-sm text-ink"
        >
          <option value="item_number">Sort: Item #</option>
          <option value="value">Sort: Value</option>
          <option value="on_hand">Sort: On hand</option>
        </select>
        <label className="flex items-center gap-1 text-sm text-ink-2">
          <input
            type="checkbox"
            checked={missingData}
            onChange={(e) => {
              setMissingData(e.target.checked);
              setPage(1);
            }}
          />
          Missing data
        </label>
      </div>

      {/* Items table */}
      <div className="rounded-md border border-line bg-card shadow-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-ink-3 border-b border-line">
              <th className="font-normal px-md py-2">Item</th>
              <th className="font-normal px-md py-2">Type</th>
              <th className="font-normal px-md py-2 text-right">On hand</th>
              <th className="font-normal px-md py-2 text-right">Value</th>
              <th className="font-normal px-md py-2 text-right">Sites</th>
              <th className="font-normal px-md py-2">Flags</th>
            </tr>
          </thead>
          <tbody>
            {items.data?.items.map((item: ItemRow) => (
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
                  <div className="text-ink-3 truncate max-w-[280px]">{item.description ?? '—'}</div>
                </td>
                <td className="px-md py-2 text-ink-2">{item.item_type ?? '—'}</td>
                <td className="px-md py-2 text-right text-ink">{integer.format(item.on_hand)}</td>
                <td className="px-md py-2 text-right text-ink">
                  {currency.format(item.inventory_value)}
                </td>
                <td className="px-md py-2 text-right text-ink-2">{item.locations}</td>
                <td className="px-md py-2">
                  {item.description === null ? (
                    <Badge label="No description" variant="status" tone="warn" />
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.isLoading ? <div className="p-md text-sm text-ink-3">Loading…</div> : null}
        {items.data && items.data.items.length === 0 ? (
          <div className="p-md text-sm text-ink-3">No items match these filters.</div>
        ) : null}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-ink-2">
        <span>{items.data ? `${integer.format(items.data.total)} items` : ''}</span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="rounded-md border border-line px-md py-1 disabled:opacity-50"
          >
            Prev
          </button>
          <span>
            Page {page} / {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="rounded-md border border-line px-md py-1 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>

      {selected ? <ItemDrawer itemId={selected} onClose={() => setSelected(null)} /> : null}
    </div>
  );
}

function ItemDrawer({ itemId, onClose }: { itemId: string; onClose: () => void }) {
  const detail = useQuery({ queryKey: ['item', itemId], queryFn: () => fetchItemDetail(itemId) });
  const d = detail.data;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button type="button" aria-label="Close" onClick={onClose} className="flex-1 bg-ink/[0.25]" />
      <aside className="w-[440px] max-w-full h-full bg-card border-l border-line overflow-y-auto p-lg flex flex-col gap-4">
        {!d ? (
          <p className="text-sm text-ink-3">Loading…</p>
        ) : (
          <>
            <div>
              <div className="font-mono text-ink">{d.item_number}</div>
              <div className="font-display text-lg text-ink">{d.description ?? '—'}</div>
              <div className="text-sm text-ink-3">
                {d.item_type ?? '—'} · {d.uom ?? '—'} ·{' '}
                {d.unit_cost !== null ? currency.format(d.unit_cost) : 'no cost'}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-ink-2 mb-1">Balances by site</h3>
              <table className="w-full text-sm">
                <tbody>
                  {d.balances.map((b) => (
                    <tr key={b.location_code} className="border-t border-line">
                      <td className="py-1 font-mono text-ink-2">{b.location_code}</td>
                      <td className="py-1 text-right text-ink">{integer.format(b.on_hand)}</td>
                      <td className="py-1 text-right text-ink-3">
                        min {b.min_level ?? '—'} / max {b.max_level ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div>
              <h3 className="text-sm font-medium text-ink-2 mb-1">Recent transactions</h3>
              {d.recent_transactions.length === 0 ? (
                <p className="text-sm text-ink-3">No movement on record.</p>
              ) : (
                <table className="w-full text-sm">
                  <tbody>
                    {d.recent_transactions.map((t, i) => (
                      <tr key={`${t.txn_date}-${i}`} className="border-t border-line">
                        <td className="py-1 text-ink-2">{t.txn_date?.slice(0, 10) ?? '—'}</td>
                        <td className="py-1 text-ink-3">{t.type}</td>
                        <td className="py-1 text-right text-ink">{integer.format(t.quantity)}</td>
                        <td className="py-1 text-right font-mono text-ink-3">
                          {t.location_code ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <button
              type="button"
              onClick={onClose}
              className="mt-auto rounded-md border border-line px-md py-1.5 text-sm text-ink-2"
            >
              Close
            </button>
          </>
        )}
      </aside>
    </div>
  );
}
