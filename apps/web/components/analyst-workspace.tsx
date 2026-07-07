'use client';

/**
 * Ask SmartInv page workspace (CV5.E2.S5): history rail + chat, wired together.
 *
 * `loadId` (paired with `chatKey`) only changes on an explicit New-chat / select,
 * remounting the chat so it cleanly loads that conversation. `activeId` tracks
 * the highlighted conversation and is updated when a turn creates/continues one,
 * without remounting (so an in-progress conversation is never clobbered).
 */

import { AnalystChat } from '@/components/analyst-chat';
import { AnalystHistory } from '@/components/analyst-history';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

export function AnalystWorkspace() {
  const queryClient = useQueryClient();
  const [loadId, setLoadId] = useState<string | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [chatKey, setChatKey] = useState(0);

  function newChat() {
    setLoadId(null);
    setActiveId(null);
    setChatKey((k) => k + 1);
  }

  function selectConversation(id: string) {
    setLoadId(id);
    setActiveId(id);
    setChatKey((k) => k + 1);
  }

  function onConversationChanged(id: string) {
    setActiveId(id);
    void queryClient.invalidateQueries({ queryKey: ['conversations'] });
  }

  return (
    <div className="flex-1 min-h-0 flex gap-4">
      <aside className="w-[240px] flex-none hidden md:block">
        <AnalystHistory activeId={activeId} onSelect={selectConversation} onNew={newChat} />
      </aside>
      <div className="flex-1 min-h-0">
        <AnalystChat
          key={chatKey}
          conversationId={loadId}
          onConversationChanged={onConversationChanged}
        />
      </div>
    </div>
  );
}
