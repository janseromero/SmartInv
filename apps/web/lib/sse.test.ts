import { parseSSEBuffer } from '@/lib/sse';
import { describe, expect, it } from 'vitest';

describe('parseSSEBuffer', () => {
  it('parses complete event/data blocks', () => {
    const buf = 'event: planning\ndata: {}\n\nevent: tool_call\ndata: {"name":"risk.summary"}\n\n';
    const { messages, rest } = parseSSEBuffer(buf);
    expect(messages).toHaveLength(2);
    expect(messages[0]).toEqual({ event: 'planning', data: {} });
    expect(messages[1]).toEqual({ event: 'tool_call', data: { name: 'risk.summary' } });
    expect(rest).toBe('');
  });

  it('keeps a trailing partial block as rest', () => {
    const buf = 'event: planning\ndata: {}\n\nevent: tool_ca';
    const { messages, rest } = parseSSEBuffer(buf);
    expect(messages).toHaveLength(1);
    expect(rest).toBe('event: tool_ca');
  });

  it('defaults the event name and passes through non-JSON data', () => {
    const { messages } = parseSSEBuffer('data: hello\n\n');
    expect(messages[0]).toEqual({ event: 'message', data: 'hello' });
  });
});
