/*
  Google Flow Agent API demo: the API client (useapi.net). Every call the page makes goes through this file.

  Base URL: https://api.useapi.net/v1/google-flow. Every call sends the header Authorization: Bearer <your useapi.net API token>.
  The development API (https://api.useapi.net/v1-dev/google-flow) is used with ?api=dev (remembered in this tab, ?api=prod to go
  back), and by default on localhost:4000 (the docs site's local preview).

    Accounts
    GET    /accounts                                     the Google Flow accounts on this token (account picker)
    GET    /accounts/{email}                             one account: its Google profile name greets you on a new chat

    Agent chats (Flow's creative agent)
    GET    /agent/chats?email=                           the account's chats, newest first
    POST   /agent/chats                                  start a chat {email, message, referenceImage_1…} -> 202 {chatId, turn}
    GET    /agent/chats/{chatId}                         turns (your message, the agent's items, media with links), status,
                                                         pendingApproval, lastError
    PATCH  /agent/chats/{chatId}                         rename {title}
    DELETE /agent/chats/{chatId}                         delete (the media it made stay on the account)
    POST   /agent/chats/{chatId}/messages                the next message {message, referenceImage_1…} -> 202 {turn}
    POST   /agent/chats/{chatId}/approval                answer a request to spend credits {decision: approve | always | reject}
    GET    /agent/chats/{chatId}/stream                  the chat as Server-Sent Events; header Last-Event-ID resumes (sse.js)
    GET    /agent/settings?email=                        approval mode, instructions, default models
    PUT    /agent/settings                               change them {email, approval?, instructions?, imageDefaults?, videoDefaults?}

    References for a message (images, a video, voices, characters)
    GET    /assets/media/{email}?projectId=              a project's images and videos (reference ids, newest by createTime)
    GET    /assets/{referenceId}                         a fresh signed link to one image or video {url}
    POST   /assets/{email}                               upload an image: the raw bytes, Content-Type image/jpeg|png|webp, 20 MB
    DELETE /assets/{email}                               delete media {mediaGenerationIds: [referenceId], projectId?}
    GET    /characters?email=                            the account's characters
    GET    /voices?email=                                built-in and custom voices

  The send routes (POST /agent/chats, /messages, /approval) answer 202 once Google has accepted the turn: up to about 100 s.
  The client allows them 150 s.
*/
(() => {
  const FD = window.FlowDemo = window.FlowDemo || {};

  /* The API base: production by default. ?api=dev or ?api=prod picks one (remembered in this tab), and the docs site's local
     preview (localhost:4000) uses the development API unless told otherwise. */
  const API_BASES = { prod: 'https://api.useapi.net/v1/google-flow', dev: 'https://api.useapi.net/v1-dev/google-flow' };
  const API_MODE = (() => {
    let mode = '';
    try {
      const asked = new URLSearchParams(location.search).get('api');
      if (asked === 'dev' || asked === 'prod') sessionStorage.setItem('flow-agent-demo-api', asked);
      mode = asked === 'dev' || asked === 'prod' ? asked : sessionStorage.getItem('flow-agent-demo-api') || '';
    } catch (err) { /* storage blocked: the URL and the host decide */ }
    if (mode !== 'dev' && mode !== 'prod') mode = ['localhost:4000', '127.0.0.1:4000'].includes(location.host) ? 'dev' : 'prod';
    return mode;
  })();
  const API = API_BASES[API_MODE];

  const SEND_TIMEOUT_MS = 150000;
  const READ_TIMEOUT_MS = 90000;
  /* The images POST /assets accepts, and its size limit */
  const UPLOAD_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
  const UPLOAD_MAX_BYTES = 20 * 1024 * 1024;

  /* The token lives here (memory). app.js keeps it in sessionStorage too, only when Remember is ticked. */
  let token = '';
  const setToken = value => { token = value; };

  /* Every id that goes into a URL path passes through here. Browsers collapse "." and ".." path segments before sending, so an
     id like ".." would turn DELETE /agent/chats/.. into another route. Such ids (and ones with "/" or "\") are refused. */
  const pathId = value => {
    const raw = String(value === undefined || value === null ? '' : value);
    let decoded = raw;
    try { decoded = decodeURIComponent(raw); } catch (err) { /* not valid percent-encoding: the raw value counts */ }
    const bad = v => v === '' || v === '.' || v === '..' || /[\\/]/.test(v);
    if (bad(raw) || bad(decoded)) throw Object.assign(new Error(`Refused an unsafe id in the URL: "${raw}"`), { status: 400 });
    return encodeURIComponent(raw);
  };
  /* A query string from the params that have a value */
  const query = params => {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(params || {})) if (v !== undefined && v !== null && v !== '') q.set(k, v);
    const s = q.toString();
    return s ? `?${s}` : '';
  };

  /* An API error: the HTTP status (0 = the network or the browser refused, -1 = our own timeout), the API's text and its body.
     The API answers {error: "text", code}; a few upstream failures carry {error: {code, message}} instead. */
  const apiError = (status, data, fallback) => {
    const text = typeof data.error === 'string' ? data.error : (data.error && data.error.message) || data.message || fallback;
    return Object.assign(new Error(text), { status, data });
  };
  const readJson = async res => {
    const text = res.status === 204 ? '' : await res.text();
    let data = {};
    try { data = text ? JSON.parse(text) : {}; } catch (err) { data = { error: text.slice(0, 300) }; }
    if (!res.ok) throw apiError(res.status, data, res.statusText || `HTTP ${res.status}`);
    return data;
  };

  /* Every JSON call goes through here: method, path under the base URL, optional JSON body, a time limit. */
  const api = async (method, path, options) => {
    const o = options || {};
    if (!token) throw Object.assign(new Error('Enter your useapi.net API token and press Connect first.'), { status: 0 });
    const headers = { Authorization: `Bearer ${token}` };
    if (o.body !== undefined && !(o.body instanceof Blob)) headers['Content-Type'] = 'application/json';
    if (o.contentType) headers['Content-Type'] = o.contentType;
    const timeoutMs = o.timeoutMs || READ_TIMEOUT_MS;
    const signal = AbortSignal.timeout(timeoutMs);
    let res;
    try {
      res = await fetch(API + path + query(o.query), {
        method,
        headers,
        body: o.body === undefined ? undefined : o.body instanceof Blob ? o.body : JSON.stringify(o.body),
        signal,
      });
    } catch (err) {
      if (signal.aborted) throw Object.assign(new Error(`No answer within ${Math.round(timeoutMs / 1000)} s`), { status: -1, timeout: true, data: {} });
      throw Object.assign(new Error(`Could not reach the API (${err.message}). Check your connection.`), { status: 0, data: {} });
    }
    return readJson(res);
  };

  const chatPath = chatId => `/agent/chats/${pathId(chatId)}`;
  const SEND = { timeoutMs: SEND_TIMEOUT_MS };

  const client = {
    accounts: () => api('GET', '/accounts'),
    account: email => api('GET', `/accounts/${pathId(email)}`),
    listChats: email => api('GET', '/agent/chats', { query: { email } }),
    getChat: chatId => api('GET', chatPath(chatId)),
    createChat: body => api('POST', '/agent/chats', Object.assign({ body }, SEND)),
    sendMessage: (chatId, body) => api('POST', `${chatPath(chatId)}/messages`, Object.assign({ body }, SEND)),
    answerApproval: (chatId, decision) => api('POST', `${chatPath(chatId)}/approval`, Object.assign({ body: { decision } }, SEND)),
    renameChat: (chatId, title) => api('PATCH', chatPath(chatId), { body: { title } }),
    deleteChat: chatId => api('DELETE', chatPath(chatId)),
    getSettings: email => api('GET', '/agent/settings', { query: { email } }),
    putSettings: body => api('PUT', '/agent/settings', { body }),
    projectMedia: (email, projectId) => api('GET', `/assets/media/${pathId(email)}`, { query: { projectId } }),
    mediaUrl: referenceId => api('GET', `/assets/${pathId(referenceId)}`),
    deleteMedia: (email, referenceIds, projectId) => api('DELETE', `/assets/${pathId(email)}`, { body: Object.assign({ mediaGenerationIds: referenceIds }, projectId ? { projectId } : {}) }),
    characters: email => api('GET', '/characters', { query: { email } }),
    voices: email => api('GET', '/voices', { query: { email } }),
    streamUrl: chatId => API + `${chatPath(chatId)}/stream`,
    /* POST /assets/{email}: the raw image as the body and its MIME type as Content-Type. Answers
       {mediaGenerationId: {mediaGenerationId: <referenceId>}, width, height, email}. */
    upload: async (email, file) => {
      if (!UPLOAD_TYPES.includes(file.type)) throw new Error(`${file.name || 'This file'}: only JPEG, PNG and WebP images can be uploaded`);
      if (file.size > UPLOAD_MAX_BYTES) throw new Error(`${file.name || 'This image'} is larger than 20 MB`);
      const data = await api('POST', `/assets/${pathId(email)}`, { body: file, contentType: file.type, timeoutMs: SEND_TIMEOUT_MS });
      const referenceId = data.mediaGenerationId && data.mediaGenerationId.mediaGenerationId;
      if (!referenceId) throw new Error('The upload answered without a reference id. Check the Library before uploading again.');
      return Object.assign({ referenceId }, data);
    },
  };

  /* Save an image or video: Google's signed link (no token needed, CORS open) read as a Blob, then a temporary link named after
     the file. A link expires about 6 hours after it was issued: then GET /assets/{referenceId} gives a fresh one, and onFresh()
     lets the page update its previews. */
  const download = async (media, onFresh) => {
    const get = async url => {
      const res = await fetch(url);
      if (!res.ok) throw Object.assign(new Error(`HTTP ${res.status}`), { status: res.status });
      return res.blob();
    };
    let blob;
    try {
      if (!media.url) throw new Error('no link yet');
      blob = await get(media.url);
    } catch (err) {
      if (!media.referenceId) throw err;
      const fresh = await client.mediaUrl(media.referenceId);
      if (onFresh) onFresh(fresh.url);
      blob = await get(fresh.url);
    }
    const ext = (blob.type.split('/')[1] || (media.type === 'video' ? 'mp4' : 'jpg')).replace('jpeg', 'jpg').replace(/[^a-z0-9]/g, '');
    const name = `flow-${media.type || 'media'}-${String(media.mediaId || 'file').slice(0, 8)}.${ext}`;
    const href = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = href;
    link.download = name;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(href), 10000);
  };

  FD.config = { API, API_MODE, UPLOAD_TYPES, UPLOAD_MAX_BYTES };
  FD.api = Object.assign({ setToken, pathId, download }, client);
})();
