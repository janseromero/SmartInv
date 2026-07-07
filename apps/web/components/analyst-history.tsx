'use client';

/**
 * Conversation history rail for the Ask SmartInv page (CV5.E2.S5).
 *
 * Lists the current user's past conversations (newest first) and offers a
 * "New chat" reset. Selecting one loads its transcript into the chat.
 */

import { fetchConversations } from '@/lib/api';
import { useQuery } from '@tanstack/react-query';

export function AnalystHistory({
  activeId,
  onSelect,
  onNew,
}: {
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}) {
  const conversations = useQuery({ queryKey: ['conversations'], queryFn: fetchConversations });

  return (
    <div className="flex flex-col h-full min-h-0 rounded-md border border-line bg-card">
      <div className="p-2 border-b border-line flex-none">
        <button
          type="button"
          onClick={onNew}
          className="w-full rounded-md bg-ai-soft text-ai text-sm font-medium px-md py-1.5 hover:bg-ai hover:text-white transition-colors"
        >
          + New chat
        </button>
      </div>
      <div className="flex-1 min-h-0 overflow-y-auto p-1.5 flex flex-col gap-1">
        {conversations.data?.length === 0 ? (
          <p className="text-xs text-ink-3 p-2">No conversations yet.</p>
        ) : null}
        {conversations.data?.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => onSelect(c.id)}
            className={`text-left rounded-md px-md py-2 text-sm ${
              c.id === activeId
                ? 'bg-surface text-ink border border-line'
                : 'text-ink-2 hover:bg-surface'
            }`}
          >
            <span className="block truncate">{c.title}</span>
            <span className="block text-[11px] text-ink-3">{c.turns} turns</span>
          </button>
        ))}
        {conversations.isLoading ? <p className="text-xs text-ink-3 p-2">Loading…</p> : null}
      </div>
    </div>
  );
}
