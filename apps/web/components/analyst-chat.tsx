'use client';

/**
 * Ask SmartInv — conversational analyst chat (CV5.E2.S4).
 *
 * Read-only governed Q&A over the JSON `POST /agents/run` endpoint. Renders the
 * grounded answer with its evidence strip; fails visibly (never silently) when
 * an answer is withheld (fail-closed) or the analyst is unconfigured (503).
 * Streaming the run trace is CV5.E2.S3; conversation persistence is S5.
 *
 * The same component powers the full `/analyst` page and the topbar slide-over,
 * so it holds its own local conversation state and takes only a layout variant.
 */

import { analystErrorMessage, groundingLabel, toEvidenceItems } from '@/lib/analyst';
import { type AgentAnswer, AnalystError, askSmartInv } from '@/lib/api';
import { EvidenceStrip } from '@smartinv/ui-web';
import { useMutation } from '@tanstack/react-query';
import { type FormEvent, useRef, useState } from 'react';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  text: string;
  answer?: AgentAnswer;
  error?: boolean;
}

const EXAMPLES = [
  'How many critical spares and what is the total downtime exposure?',
  'Give me an inventory health overview.',
  'How many items are at obsolescence risk?',
];

export function AnalystChat({ variant = 'page' }: { variant?: 'page' | 'panel' }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const nextId = useRef(1);
  const scrollRef = useRef<HTMLDivElement>(null);

  const ask = useMutation({
    mutationFn: (question: string) => askSmartInv(question),
    onSuccess: (answer) => {
      pushAssistant({ text: answer.answer, answer });
    },
    onError: (err) => {
      const status = err instanceof AnalystError ? err.status : 0;
      pushAssistant({ text: analystErrorMessage(status), error: true });
    },
  });

  function pushAssistant(partial: Omit<Message, 'id' | 'role'>) {
    setMessages((m) => [...m, { id: nextId.current++, role: 'assistant', ...partial }]);
    queueMicrotask(() => scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight }));
  }

  function submit(question: string) {
    const q = question.trim();
    if (!q || ask.isPending) return;
    setMessages((m) => [...m, { id: nextId.current++, role: 'user', text: q }]);
    setInput('');
    ask.mutate(q);
    queueMicrotask(() =>
      scrollRef.current?.scrollTo({ top: scrollRef.current?.scrollHeight ?? 0 }),
    );
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    submit(input);
  }

  // Both variants fill their parent, which is responsible for a definite height
  // (the page wraps this in a flex-1 min-h-0 column; the launcher in a
  // full-height aside). The composer sits outside the scroll area so it is
  // always pinned and visible.
  return (
    <div className={`flex flex-col h-full min-h-0 ${variant === 'page' ? 'min-h-[440px]' : ''}`}>
      <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-4 pr-1">
        {messages.length === 0 ? (
          <EmptyState onPick={submit} />
        ) : (
          messages.map((m) =>
            m.role === 'user' ? (
              <UserBubble key={m.id} text={m.text} />
            ) : (
              <AssistantBubble key={m.id} message={m} />
            ),
          )
        )}
        {ask.isPending ? <ThinkingBubble /> : null}
      </div>

      <form onSubmit={onSubmit} className="mt-3 flex items-end gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              submit(input);
            }
          }}
          rows={1}
          placeholder="Ask about inventory health, critical spares, risk…"
          className="flex-1 resize-none bg-card border border-line rounded-md px-md py-2 text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-ai"
        />
        <button
          type="submit"
          disabled={ask.isPending || !input.trim()}
          className="rounded-md bg-ai text-white px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          Ask
        </button>
      </form>
    </div>
  );
}

function EmptyState({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="m-auto max-w-md text-center flex flex-col gap-3">
      <div className="inline-flex mx-auto items-center gap-1.5 rounded-pill bg-ai-soft text-ai px-2.5 py-1 text-xs font-medium">
        AI · governed answers only
      </div>
      <p className="text-sm text-ink-2">
        Ask about your inventory, health, and operational risk. Every answer carries its evidence
        and is withheld if a figure can't be traced to a governed source.
      </p>
      <div className="flex flex-col gap-1.5">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            type="button"
            onClick={() => onPick(ex)}
            className="text-left text-sm text-ink-2 rounded-md border border-line bg-card px-md py-2 hover:border-ai hover:text-ink"
          >
            {ex}
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

function ThinkingBubble() {
  return (
    <div className="self-start rounded-lg border border-ai/30 bg-ai-soft/40 px-md py-2.5 text-sm text-ink-3">
      Analyzing governed data…
    </div>
  );
}
