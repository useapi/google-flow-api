/*
  Google Flow Agent API demo: the chat stream, GET /agent/chats/{chatId}/stream (Server-Sent Events).

  The browser's EventSource cannot send an Authorization header, so the stream is read with fetch() and a ReadableStream reader,
  and parsed here (https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream).

  followStream() keeps one chat's stream open:
  - every event with an id moves lastId forward; a reconnect sends it as Last-Event-ID and the API resumes right after it;
  - media event ids (<turn>:m:<mediaId>) are not used to resume, because the API replays the whole turn for them;
  - a dropped connection or a 5xx reconnects after 1, 2, 5, 10, then every 30 s;
  - a `reconnect` event (the API's 60-minute cap) reconnects at once;
  - an `idle` event (10 quiet minutes) ends it: the page opens it again when you send, reload or come back;
  - a 4xx answer (bad token, chat deleted) ends it with the API's message.
*/
(() => {
  const FD = window.FlowDemo = window.FlowDemo || {};
  const RETRY_DELAYS_MS = [1000, 2000, 5000, 10000, 30000];

  /* Read an SSE body and call emit({id, event, data}) per event; data is parsed as JSON when it is JSON. */
  const readEventStream = async (body, emit) => {
    const reader = body.pipeThrough(new TextDecoderStream()).getReader();
    let buffer = '';
    let event = { id: undefined, event: '', data: [] };
    const dispatch = () => {
      if (event.data.length) {
        const raw = event.data.join('\n');
        let data = raw;
        try { data = JSON.parse(raw); } catch (err) { /* plain text data */ }
        emit({ id: event.id, event: event.event || 'message', data });
      }
      event = { id: undefined, event: '', data: [] };
    };
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += value;
      let nl;
      while ((nl = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, nl).replace(/\r$/, '');
        buffer = buffer.slice(nl + 1);
        if (line === '') { dispatch(); continue; }
        if (line.startsWith(':')) continue;
        const colon = line.indexOf(':');
        const field = colon < 0 ? line : line.slice(0, colon);
        const value = colon < 0 ? '' : line.slice(colon + 1).replace(/^ /, '');
        if (field === 'data') event.data.push(value);
        else if (field === 'event') event.event = value;
        else if (field === 'id') event.id = value;
      }
    }
  };

  /* Follow one chat's stream until close(). onEvent gets every event; onState(state, detail) gets
     'connecting' | 'live' | 'retry' | 'idle' | 'error' | 'off'. */
  const followStream = ({ url, token, lastEventId, onEvent, onState }) => {
    const state = onState || (() => {});
    const abort = new AbortController();
    let lastId = lastEventId;
    let closed = false;
    const finish = (s, detail) => {
      closed = true;
      state(s, detail);
    };

    const run = async () => {
      let failures = 0;
      while (!abort.signal.aborted) {
        let stopAfterClose = false;
        let reconnectNow = false;
        try {
          state(failures ? 'retry' : 'connecting');
          const headers = { Authorization: `Bearer ${token}`, Accept: 'text/event-stream' };
          if (lastId) headers['Last-Event-ID'] = lastId;
          const res = await fetch(url, { headers, signal: abort.signal, cache: 'no-store' });
          if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            const message = typeof data.error === 'string' ? data.error : (data.error && data.error.message) || `HTTP ${res.status}`;
            if (res.status >= 400 && res.status < 500 && res.status !== 429) return finish('error', message);
            throw new Error(message);
          }
          state('live');
          failures = 0;
          await readEventStream(res.body, ev => {
            if (ev.id && !ev.id.includes(':m:')) lastId = ev.id;
            if (ev.event === 'idle') stopAfterClose = true;
            if (ev.event === 'reconnect') reconnectNow = true;
            onEvent(ev);
          });
        } catch (err) {
          if (abort.signal.aborted) break;
          failures++;
          state('retry', err.message);
        }
        if (abort.signal.aborted) break;
        if (stopAfterClose) return finish('idle');
        if (!reconnectNow) {
          const delay = RETRY_DELAYS_MS[Math.min(Math.max(failures, 1) - 1, RETRY_DELAYS_MS.length - 1)];
          state('retry', `reconnecting in ${delay / 1000} s`);
          await new Promise(r => setTimeout(r, delay));
        }
      }
      if (!closed) finish('off');
    };
    run();

    return {
      close: () => { if (!closed) { closed = true; abort.abort(); } },
      get closed() { return closed; },
      get lastId() { return lastId; },
    };
  };

  FD.sse = { readEventStream, followStream };
})();
