/**
 * Minimal Server-Sent Events parser for the Ask SmartInv trace stream (CV5.E2.S3).
 *
 * We read the stream with `fetch` + `ReadableStream` (not `EventSource`) because
 * the request needs the bearer header. This pure helper turns a growing text
 * buffer into complete SSE messages plus any trailing partial block.
 */

export interface SSEMessage {
  event: string;
  data: unknown;
}

/** Parse all complete `event:/data:` blocks; return the leftover partial tail. */
export function parseSSEBuffer(buffer: string): { messages: SSEMessage[]; rest: string } {
  const blocks = buffer.split('\n\n');
  const rest = blocks.pop() ?? '';
  const messages: SSEMessage[] = [];

  for (const block of blocks) {
    if (!block.trim()) continue;
    let event = 'message';
    let dataStr = '';
    for (const line of block.split('\n')) {
      if (line.startsWith('event:')) {
        event = line.slice('event:'.length).trim();
      } else if (line.startsWith('data:')) {
        dataStr += line.slice('data:'.length).trim();
      }
    }
    let data: unknown = dataStr;
    try {
      data = JSON.parse(dataStr);
    } catch {
      // leave as the raw string if it is not JSON
    }
    messages.push({ event, data });
  }

  return { messages, rest };
}
