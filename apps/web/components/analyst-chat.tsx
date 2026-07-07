'use client';

/**
 * Ask SmartInv — conversational analyst chat (CV5.E2.S4/S5/S6).
 *
 * Read-only governed Q&A over the JSON `POST /agents/run` endpoint. Renders the
 * grounded answer with its evidence strip; fails visibly (never silently) when
 * an answer is withheld (fail-closed) or the analyst is unconfigured (503).
 * Turns are persisted (S5): the component threads a `conversation_id` so
 * follow-ups continue the same conversation, and can load a past one.
 * Streaming the run trace is CV5.E2.S3.
 *
 * The same component powers the full `/analyst` page and the topbar slide-over,
 * so it holds its own local conversation state and takes only a layout variant.
 */

import { analystErrorMessage, groundingLabel, toEvidenceItems } from '@/lib/analyst';
import { type AgentAnswer, AnalystError, askSmartInvStream, fetchConversation } from '@/lib/api';
import { SUGGESTED_PROMPTS } from '@/lib/prompts';
import { EvidenceStrip } from '@smartinv/ui-web';
import { type FormEvent, useEffect, useRef, useState } from 'react';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  text: string;
  answer?: AgentAnswer;
  error?: boolean;
}

interface TraceState {
  phase: string;
  tools: string[];
}

// Human-readable label per streamed trace event (CV5.E2.S3).
const PHASE: Record<string, string> = {
  planning: 'Planning',
  tool_call: 'Querying governed data',
  composing: 'Composing answer',
  validating: 'Validating grounding',
};

function phaseLabel(event: string): string {
  return PHASE[event] ?? 'Working';
}

interface AnalystChatProps {
  variant?: 'page' | 'panel';
  /** Load this existing conversation on mount (null/undefined = fresh chat). */
  conversationId?: string | null;
  /** Called when a conversation is created or continued (to refresh history). */
  onConversationChanged?: (id: string) => void;
}

export function AnalystChat({
  variant = 'page',
  conversationId: initialConversationId = null,
  onConversationChanged,
}: AnalystChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(initialConversationId);
  const nextId = useRef(1);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Load a past conversation's turns into the transcript on mount / when the
  // selected conversation changes (the page remounts via key, so this runs once).
  useEffect(() => {
    if (!initialConversationId) return;
    let cancelled = false;
    fetchConversation(initialConversationId)
      .then((detail) => {
        if (cancelled) return;
        const loaded: Message[] = [];
        for (const turn of detail.turns) {
          loaded.push({ id: nextId.current++, role: 'user', text: turn.question });
          loaded.push({
            id: nextId.current++,
            role: 'assistant',
            text: turn.answer.answer,
            answer: turn.answer,
          });
        }
        setMessages(loaded);
        setConversationId(initialConversationId);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [initialConversationId]);

  const [pending, setPending] = useState(false);
  const [trace, setTrace] = useState<TraceState | null>(null);

  function scrollToBottom() {
    queueMicrotask(() =>
      scrollRef.current?.scrollTo({ top: scrollRef.current?.scrollHeight ?? 0 }),
    );
  }

  function pushAssistant(partial: Omit<Message, 'id' | 'role'>) {
    setMessages((m) => [...m, { id: nextId.current++, role: 'assistant', ...partial }]);
    scrollToBottom();
  }

  async function submit(question: string) {
    const q = question.trim();
    if (!q || pending) return;
    setMessages((m) => [...m, { id: nextId.current++, role: 'user', text: q }]);
    setInput('');
    setPending(true);
    setTrace({ phase: phaseLabel('planning'), tools: [] });
    scrollToBottom();
    try {
      const answer = await askSmartInvStream(q, conversationId ?? undefined, (update) => {
        setTrace((prev) => {
          const tools = prev?.tools ?? [];
          if (update.event === 'tool_call' && typeof update.data.name === 'string') {
            return { phase: phaseLabel('tool_call'), tools: [...tools, update.data.name] };
          }
          return { phase: PHASE[update.event] ?? prev?.phase ?? 'Working', tools };
        });
        scrollToBottom();
      });
      pushAssistant({ text: answer.answer, answer });
      setConversationId(answer.conversation_id);
      onConversationChanged?.(answer.conversation_id);
    } catch (err) {
      const status = err instanceof AnalystError ? err.status : 0;
      pushAssistant({ text: analystErrorMessage(status), error: true });
    } finally {
      setPending(false);
      setTrace(null);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void submit(input);
  }

  // Both variants fill their parent, which is responsible for a definite height
  // (the page wraps this in a flex-1 min-h-0 column; the launcher in a
  // full-height aside). The composer sits outside the scroll area so it is
  // always pinned and visible.
  return (
    <div className={`flex flex-col h-full min-h-0 ${variant === 'page' ? 'min-h-[440px]' : ''}`}>
      <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-4 pr-1">
        {messages.length === 0 ? (
          <EmptyState onPick={submit} compact={variant === 'panel'} />
        ) : (
          messages.map((m) =>
            m.role === 'user' ? (
              <UserBubble key={m.id} text={m.text} />
            ) : (
              <AssistantBubble key={m.id} message={m} />
            ),
          )
        )}
        {pending ? <ThinkingBubble trace={trace} /> : null}
      </div>

      <form onSubmit={onSubmit} className="mt-3 flex items-end gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              void submit(input);
            }
          }}
          rows={1}
          placeholder="Ask about inventory health, critical spares, risk…"
          className="flex-1 resize-none bg-card border border-line rounded-md px-md py-2 text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-ai"
        />
        <button
          type="submit"
          disabled={pending || !input.trim()}
          className="rounded-md bg-ai text-white px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          Ask
        </button>
      </form>
    </div>
  );
}

function EmptyState({ onPick, compact }: { onPick: (q: string) => void; compact?: boolean }) {
  return (
    <div className="m-auto max-w-md text-center flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <div className="inline-flex mx-auto items-center gap-1.5 rounded-pill bg-ai-soft text-ai px-2.5 py-1 text-xs font-medium">
          AI · governed answers only
        </div>
        <p className="text-sm text-ink-2">
          Ask about your inventory, health, and operational risk. Every answer carries its evidence
          and is withheld if a figure can't be traced to a governed source.
        </p>
      </div>

      {/* Suggested prompts panel (CV5.E2.S6) */}
      <div className="flex flex-col gap-1.5 text-left">
        <span className="text-[11px] uppercase tracking-wide text-ink-3 px-1">
          Suggested prompts
        </span>
        {SUGGESTED_PROMPTS.map((p) => (
          <button
            key={p.label}
            type="button"
            onClick={() => onPick(p.question)}
            className="rounded-md border border-line bg-card px-md py-2 hover:border-ai group"
          >
            <span className="block text-sm text-ink group-hover:text-ai">{p.label}</span>
            {compact ? null : (
              <span className="block text-xs text-ink-3 truncate">{p.question}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

function UserBubble({ text }: { text: string }) {
  return (
    <div className="self-end max-w-[80%] rounded-lg bg-surface border border-line px-md py-2 text-sm text-ink">
      {text}
    </div>
  );
}

function AssistantBubble({ message }: { message: Message }) {
  const { text, answer, error } = message;

  if (error) {
    return (
      <div className="self-start max-w-[85%] rounded-lg border border-warn/40 bg-warn-soft px-md py-2 text-sm text-warn-dark">
        {text}
      </div>
    );
  }

  const status = answer ? groundingLabel(answer) : null;

  return (
    <div className="self-start w-full max-w-[85%] flex flex-col gap-2">
      {/* violet AI marker — non-negotiable #8 */}
      <div className="rounded-lg border border-ai/30 bg-ai-soft/40 px-md py-2.5">
        <div className="flex items-center gap-1.5 mb-1">
          <span className="rounded-pill bg-ai text-white text-[10px] font-bold px-1.5 py-px">
            AI
          </span>
          <span className="text-[11px] text-ink-3">SmartInv analyst</span>
        </div>
        <p className="text-sm text-ink whitespace-pre-wrap">{text}</p>
      </div>

      {answer && answer.evidence.length > 0 ? (
        <EvidenceStrip
          items={toEvidenceItems(answer.evidence)}
          confidence={answer.confidence}
          modelVersion={answer.model}
        />
      ) : null}

      {status ? (
        <span className={`text-[11px] ${status.ok ? 'text-ok' : 'text-warn'}`}>
          {status.ok ? '✓ ' : '⚠ '}
          {status.text}
        </span>
      ) : null}
    </div>
  );
}

function ThinkingBubble({ trace }: { trace: TraceState | null }) {
  const phase = trace?.phase ?? 'Working';
  const tools = trace?.tools ?? [];
  return (
    <div className="self-start rounded-lg border border-ai/30 bg-ai-soft/40 px-md py-2.5 flex flex-col gap-1.5">
      <div className="flex items-center gap-2 text-sm text-ink-2">
        <span className="inline-block w-1.5 h-1.5 rounded-pill bg-ai animate-pulse" />
        {phase}…
      </div>
      {tools.length > 0 ? (
        <div className="flex flex-wrap gap-1">
          {tools.map((t) => (
            <span
              key={t}
              className="inline-flex items-center gap-1 rounded-md bg-surface border border-line px-2 py-0.5 font-mono text-[11px] text-ink-3"
            >
              {t}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
