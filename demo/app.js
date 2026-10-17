/*
  Google Flow Agent API demo: the app. It uses api.js (every API call), sse.js (the chat stream) and render.js (DOM pieces).

  How it works, in numbered sections:
     1 state                        2 helpers (messages, confirm bar, masking)      3 connect, account picker, tabs
     4 chat list                    5 one chat: turns, answers, steps, results, approval cards, media panel
     6 the stream                   7 sending, choices, approvals, error answers     8 attachments: upload, drop, paste, pickers
     9 lightbox and download       10 Library tab                                   11 Agent settings tab
    12 layout and boot (splitters, drawers, keyboard)

  Reproduce this in your app:
  - Send with POST /agent/chats (first message) or POST /agent/chats/{chatId}/messages. It answers 202 once Google accepted the
    turn (up to about 100 s): allow 150 s. 409 = a turn is running in that chat, 429 = wait (retryAfter), 504 = it may still
    start (read the chat before sending again), 502/503 = say what the API says.
  - Follow the chat with GET /agent/chats/{chatId}/stream (sse.js). Its ids are per turn: <turn>:<messageId>, <turn>:end,
    <turn>:approval, <turn>:m:<mediaId>. Opening a chat renders its finished turns from GET /agent/chats/{chatId} and starts the
    stream with Last-Event-ID: <last finished turn>:end, so the stream carries only what is new.
  - References: upload with POST /assets/{email} (raw bytes), or take reference ids from GET /assets/media/{email},
    /characters, /voices; send them as referenceImage_1..7, referenceVideo_1, referenceAudio_1..5, character_1..7 and name them
    in the text as @referenceImage_1 and so on.
  - The token lives in memory and, only when Remember is ticked, in sessionStorage under 'flow-agent-demo-token' (this tab only).
    On a server, keep the token on the server and proxy these calls instead.
*/
(() => {
  const FD = window.FlowDemo;
  const { api, sse, config } = FD;
  const { pickStarters, starterCard, el, maskEmail, fmtShort, fmtClock, statusLabel, renderMarkdown, approvalSummary, renderStep, resultFigure, mediaCard, isDone } = FD.render;

  /* ======================================================================
     1. State
     ====================================================================== */
  const TOKEN_KEY = 'flow-agent-demo-token';
  /* References per message (the same parameters and limits as POST /videos) */
  const SLOTS = { image: { param: 'referenceImage', max: 7 }, video: { param: 'referenceVideo', max: 1 }, audio: { param: 'referenceAudio', max: 5 }, character: { param: 'character', max: 7 } };
  /* The default-model choices when GET /agent/settings could not read the account's catalog from Google (models: null) */
  const IMAGE_MODELS = [['nano-banana-pro', 'Nano Banana Pro'], ['nano-banana-2', 'Nano Banana 2.1'], ['nano-banana-2-lite', 'Nano Banana 2 Lite']];
  const IMAGE_ASPECTS = ['1:1', '9:16', '16:9', '3:4', '4:3'];
  const VIDEO_MODELS = [['omni-flash', 'Omni 1.1 Flash'], ['veo-3.1-lite', 'Veo 3.1 - Lite'], ['veo-3.1-fast', 'Veo 3.1 - Fast'], ['veo-3.1-quality', 'Veo 3.1 - Quality'], ['veo-3.1-lite-low-priority', 'Veo 3.1 - Lite [Lower Priority]']];
  const VIDEO_ASPECTS = ['9:16', '16:9'];
  const COUNTS = ['1', '2', '3', '4'];
  const LIBRARY_PAGE = 48;

  /* One object per chat on screen: its turns (Map turn -> nodes), the stream ids already shown (seen), the turns drawn from
     GET /agent/chats/{chatId} (fromHistory: the stream skips them), its media (Map mediaId -> media) and the open approval. */
  const newChat = chatId => ({
    id: chatId, title: '', status: 'idle', runningSince: 0, turns: new Map(), seen: new Set(), fromHistory: new Set(),
    media: new Map(), approval: null, stream: null, refreshTimer: 0,
  });
  const state = {
    token: '', email: '', accounts: {}, chats: [], chatsAt: 0, chat: newChat(null),
    sending: null,            // {since, label} while a send waits for Google
    attachments: [],          // [{key, kind, param, referenceId | voice, label, thumb, status, error}]
    urls: new Map(),          // referenceId -> fresh signed url (Library, pickers, refreshed results)
    library: new Map(),       // `${email}|${projectId}` -> {media: [...], at}
    libraryShown: LIBRARY_PAGE,
    settings: null,           // the last GET /agent/settings answer for the account
    names: new Map(),         // email -> the Google account's first name (GET /accounts/{email}), for the greeting
    characters: null, voices: null,
    pick: 'media',
  };
  const $ = id => document.getElementById(id);

  /* ======================================================================
     2. Helpers
     ====================================================================== */
  /* Mask the token's account emails wherever they appear in a message (API errors can name the account). */
  const maskEmails = text => {
    let out = String(text || '');
    for (const email of Object.keys(state.accounts || {})) out = out.split(email).join(maskEmail(email));
    return out;
  };
  const showMsg = (node, text, kind) => {
    node.textContent = maskEmails(text);
    node.classList.toggle('gf-msg-error', kind === 'error');
    node.classList.toggle('gf-msg-ok', kind === 'ok');
  };
  const topMsg = (text, kind) => {
    $('gf-top-msg').hidden = !text;
    showMsg($('gf-top-msg'), text, kind);
  };
  const setBusy = (button, busy) => {
    button.disabled = busy;
    button.classList.toggle('gf-busy', busy);
    button.setAttribute('aria-busy', busy ? 'true' : 'false');
  };
  const sentence = text => /[.!?]$/.test(String(text).trim()) ? String(text).trim() : `${String(text).trim()}.`;
  const copyText = async (text, msg) => {
    try {
      await navigator.clipboard.writeText(text);
      if (msg) showMsg(msg, 'Copied.', 'ok');
    } catch (err) {
      if (msg) showMsg(msg, text);
    }
  };
  /* Ask for confirmation inside the page (no window.confirm): a small bar with the question, the action and Cancel. */
  const confirmInline = (host, question, yesLabel) => new Promise(resolve => {
    host.querySelectorAll(':scope > .gf-confirm').forEach(n => n.remove());
    const done = answer => { bar.remove(); resolve(answer); };
    const yes = el('button', { type: 'button', class: 'gf-btn gf-btn-sm gf-btn-danger', text: yesLabel, onclick: () => done(true) });
    const bar = el('div', { class: 'gf-confirm', role: 'alertdialog' }, [el('span', { text: question }), yes, el('button', { type: 'button', class: 'gf-btn gf-btn-sm', text: 'Cancel', onclick: () => done(false) })]);
    bar.addEventListener('keydown', e => { if (e.key === 'Escape') { e.stopPropagation(); done(false); } });
    host.append(bar);
    yes.focus();
  });
  /* Run once the node scrolls near the view, so a long list does not read every link at once */
  const whenVisible = (node, run) => {
    if (!('IntersectionObserver' in window)) return run();
    const io = new IntersectionObserver(entries => {
      if (entries.some(e => e.isIntersecting)) { io.disconnect(); run(); }
    }, { rootMargin: '200px' });
    io.observe(node);
  };
  /* A fresh signed link for a reference id (GET /assets/{referenceId}), at most 4 reads at a time, cached for the page */
  const linkQueue = { running: 0, waiting: [] };
  const freshUrl = referenceId => {
    if (state.urls.has(referenceId)) return state.urls.get(referenceId);
    const pending = new Promise((resolve, reject) => {
      const go = () => {
        linkQueue.running++;
        api.mediaUrl(referenceId).then(d => resolve(d.url), reject).finally(() => {
          linkQueue.running--;
          const next = linkQueue.waiting.shift();
          if (next) next();
        });
      };
      if (linkQueue.running < 4) go();
      else linkQueue.waiting.push(go);
    });
    pending.catch(() => state.urls.delete(referenceId));
    state.urls.set(referenceId, pending);
    return pending;
  };

  /* ======================================================================
     3. Connect, account picker, tabs
     ====================================================================== */
  const rememberToken = () => {
    try {
      if ($('gf-remember').checked && state.token) sessionStorage.setItem(TOKEN_KEY, state.token);
      else sessionStorage.removeItem(TOKEN_KEY);
    } catch (err) { /* storage blocked: the token lives in the field only */ }
  };
  /* GET /accounts: the Google Flow accounts on this token, keyed by email */
  const connect = async () => {
    state.token = $('gf-token').value.trim();
    api.setToken(state.token);
    if (!state.token) return topMsg('Enter your useapi.net API token first.', 'error');
    rememberToken();
    setBusy($('gf-connect'), true);
    topMsg('Loading accounts…');
    try {
      const accounts = await api.accounts();
      const emails = Object.keys(accounts).filter(k => k.includes('@'));
      state.accounts = accounts;
      const select = $('gf-account');
      select.textContent = '';
      for (const email of emails) {
        const health = accounts[email].health && accounts[email].health !== 'OK' ? ` · ${accounts[email].health}` : '';
        select.append(el('option', { value: email, text: maskEmail(email) + health, title: maskEmail(email) + health }));
      }
      select.disabled = !emails.length;
      if (!emails.length) return topMsg('This token has no Google Flow account yet. Add one with POST /accounts (see the Google Flow setup).', 'error');
      topMsg('');
      const keep = emails.includes(state.email) ? state.email : emails[0];
      select.value = keep;
      selectAccount(keep);
    } catch (err) {
      topMsg(err.status === 401 || err.status === 403 ? `${sentence(err.message)} Check the API token.` : err.message, 'error');
    } finally {
      setBusy($('gf-connect'), false);
    }
  };
  /* Everything below the top bar belongs to one account: switching accounts starts each tab fresh. */
  const selectAccount = email => {
    state.email = email;
    state.chats = [];
    state.chatsAt = 0;
    state.settings = null;
    settingsSnapshot = null;
    state.characters = null;
    state.voices = null;
    state.urls.clear();
    state.attachments = [];
    renderAttachments();
    startNewChat();
    loadName(email);
    loadChats();
    const tab = currentTab();
    if (tab === 'library') loadLibrary(false);
    if (tab === 'settings') loadSettings();
  };
  /* the settings form as last filled (Save sends only what changed); null until filled for this account */
  let settingsSnapshot = null;

  const TABS = ['chat', 'library', 'settings'];
  const currentTab = () => TABS.find(t => $(`gf-tab-${t}`).getAttribute('aria-selected') === 'true');
  const showTab = name => {
    for (const t of TABS) {
      const on = t === name;
      $(`gf-tab-${t}`).setAttribute('aria-selected', on ? 'true' : 'false');
      $(`gf-tab-${t}`).tabIndex = on ? 0 : -1;
      $(`gf-panel-${t}`).hidden = !on;
    }
    if (!state.email) return;
    if (name === 'library') loadLibrary(false);
    /* the form is filled once per account: from the settings the Library already read, or from GET /agent/settings */
    if (name === 'settings' && !settingsSnapshot) { if (state.settings) fillSettings(state.settings); else loadSettings(); }
  };

  /* ======================================================================
     4. Chat list: GET /agent/chats?email=, rename (PATCH), delete (DELETE)
     ====================================================================== */
  const loadChats = async () => {
    if (!state.email) return;
    const email = state.email;
    $('gf-chats-state').textContent = state.chats.length ? '' : 'Loading chats…';
    try {
      const data = await api.listChats(email);
      if (email !== state.email) return;
      state.chats = data.chats || [];
      state.chatsAt = Date.now();
      renderChats();
    } catch (err) {
      showMsg($('gf-chats-state'), err.message, 'error');
    }
  };
  const renderListAge = () => {
    $('gf-chats-caption').hidden = !state.chatsAt;
    $('gf-chats-age').textContent = state.chatsAt ? `Updated ${fmtClock(state.chatsAt)}` : '';
  };
  const renderChats = () => {
    renderListAge();
    const list = $('gf-chat-list');
    list.textContent = '';
    $('gf-chats-state').textContent = state.chats.length ? '' : 'No chats yet. Write a message to start one.';
    for (const c of state.chats) {
      const item = el('div', { class: `gf-chat-item${c.chatId === state.chat.id ? ' gf-current' : ''}`, role: 'listitem' });
      const running = c.chatId === state.chat.id ? state.chat.status : c.running ? 'running' : '';
      item.append(
        el('button', { type: 'button', class: 'gf-chat-open', onclick: () => openChat(c.chatId) }, [
          el('span', { class: 'gf-chat-title', text: c.title || 'New chat', title: c.title || '' }),
          el('span', { class: 'gf-chat-meta' }, [
            running && running !== 'idle' ? el('span', { class: `gf-pill gf-pill-${running}`, text: statusLabel(running) }) : null,
            el('span', { class: 'gf-chat-date', text: fmtShort(c.updated || c.created) }),
          ]),
        ]),
        el('span', { class: 'gf-chat-actions' }, [
          el('button', { type: 'button', class: 'gf-icon-btn', title: 'Rename', 'aria-label': `Rename ${c.title || 'chat'}`, text: '✎', onclick: () => renameChat(c, item) }),
          el('button', { type: 'button', class: 'gf-icon-btn', title: 'Delete', 'aria-label': `Delete ${c.title || 'chat'}`, text: '\u{1F5D1}', onclick: () => deleteChat(c, item) }),
        ]),
      );
      list.append(item);
    }
  };
  const listed = chatId => state.chats.find(c => c.chatId === chatId);
  const renameChat = (c, item) => {
    item.querySelectorAll(':scope > .gf-rename, :scope > .gf-item-msg').forEach(n => n.remove());
    const input = el('input', { type: 'text', value: c.title || '', 'aria-label': 'New title', maxlength: '200' });
    const msg = el('div', { class: 'gf-item-msg', role: 'status' });
    const save = el('button', { type: 'submit', class: 'gf-btn gf-btn-sm gf-btn-primary', text: 'Save' });
    const form = el('form', { class: 'gf-rename' }, [input, save, el('button', { type: 'button', class: 'gf-btn gf-btn-sm', text: 'Cancel', onclick: () => { form.remove(); msg.remove(); } })]);
    form.addEventListener('keydown', e => { if (e.key === 'Escape') { e.stopPropagation(); form.remove(); msg.remove(); } });
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const title = input.value.trim();
      if (!title || title === c.title) return form.remove();
      setBusy(save, true);
      try {
        const data = await api.renameChat(c.chatId, title);
        c.title = data.title || title;
        if (c.chatId === state.chat.id) setTitle(c.title);
        renderChats();
      } catch (err) {
        setBusy(save, false);
        showMsg(msg, err.status === 409 ? 'A turn is running in this chat. Rename it once the turn ends.' : err.message, 'error');
      }
    });
    item.append(form, msg);
    input.focus();
    input.select();
  };
  const deleteChat = async (c, item) => {
    if (!await confirmInline(item, 'Delete this chat? Its history goes, the images and videos stay on the account.', 'Delete')) return;
    try {
      await api.deleteChat(c.chatId);
      state.chats = state.chats.filter(x => x !== c);
      if (c.chatId === state.chat.id) startNewChat();
      renderChats();
    } catch (err) {
      item.append(el('div', { class: 'gf-item-msg gf-msg-error', role: 'status', text: maskEmails(err.status === 409 ? 'A turn is running in this chat. Delete it once the turn ends.' : err.message) }));
    }
  };

  /* ======================================================================
     5. One chat: turns, answers, steps, results, approval cards, the media panel
     ====================================================================== */
  const log = () => $('gf-log');
  const atBottom = () => log().scrollHeight - log().scrollTop - log().clientHeight < 140;
  const scrollDown = force => { if (force || atBottom()) requestAnimationFrame(() => { log().scrollTop = log().scrollHeight; }); };
  const msgs = () => log().querySelector('.gf-msgs') || log().appendChild(el('div', { class: 'gf-msgs' }));
  const workingLine = el('div', { class: 'gf-note-line', role: 'status' });

  /* The new-chat screen, like Flow's own: "Hi <first name>", "What would you like to create?" and 3 starter cards picked at random
     from Flow's 14 (a new pick for every new chat). A card sends its label as your first message, as Flow does. */
  const greeting = () => {
    const name = state.names.get(state.email);
    return name ? `Hi ${name}` : 'Hi';
  };
  const renderEmpty = () => {
    log().textContent = '';
    log().append(el('div', { class: 'gf-msgs' }, el('div', { class: 'gf-empty' }, [
      el('div', { class: 'gf-greeting' }, [el('h2', { id: 'gf-greeting', text: greeting() }), el('h2', { text: 'What would you like to create?' })]),
      el('div', { class: 'gf-starters' }, pickStarters(3).map(s => starterCard(s, label => sendText(label)))),
    ])));
  };
  /* GET /accounts/{email}: the account's Google profile name (sessionData.user.name), once per account, for "Hi <first name>" */
  const loadName = async email => {
    if (state.names.has(email)) return;
    state.names.set(email, '');
    try {
      const a = await api.account(email);
      const full = a && a.sessionData && a.sessionData.user && a.sessionData.user.name;
      state.names.set(email, full ? String(full).trim().split(/\s+/)[0] : '');
    } catch (err) { /* the greeting stays "Hi" */ }
    if (email === state.email && $('gf-greeting')) $('gf-greeting').textContent = greeting();
  };

  const setTitle = title => {
    if (!title) return;
    state.chat.title = title;
    $('gf-chat-title').textContent = title;
    const c = listed(state.chat.id);
    if (c && c.title !== title) { c.title = title; renderChats(); }
  };
  const setStatus = status => {
    const chat = state.chat;
    if (status === 'running' && chat.status !== 'running') chat.runningSince = Date.now();
    chat.status = status || 'idle';
    const pill = $('gf-chat-status');
    pill.hidden = !chat.id;
    pill.className = `gf-pill gf-pill-${chat.status}`;
    pill.textContent = statusLabel(chat.status);
    const c = listed(chat.id);
    if (c) { c.running = chat.status === 'running'; renderChats(); }
    renderActivity();
  };
  const setConn = (kind, text, detail) => {
    $('gf-conn').className = `gf-conn gf-conn-${kind}`;
    $('gf-conn-text').textContent = text;
    $('gf-conn').title = detail || '';
  };

  /* A turn's nodes: your message, the agent's answer bubble (steps, parts, results), its approval card and error line. */
  const turnOf = n => {
    const chat = state.chat;
    let t = chat.turns.get(n);
    if (t) return t;
    const box = msgs();
    box.querySelector('.gf-empty') && box.querySelector('.gf-empty').remove();
    const node = el('div', { class: 'gf-turn', 'data-turn': n });
    const next = [...box.querySelectorAll(':scope > .gf-turn')].find(x => Number(x.dataset.turn) > n);
    box.insertBefore(node, next || (workingLine.parentNode === box ? workingLine : null));
    t = { n, node, user: null, answer: null, approval: null, hasUser: false };
    chat.turns.set(n, t);
    return t;
  };
  const maxTurn = () => Math.max(0, ...state.chat.turns.keys());

  /* Your message: its text and the references it carried (chips) */
  const setUser = (n, message, pending) => {
    const t = turnOf(n);
    const KIND = { media: 'image or video', voice: 'voice', character: 'character' };
    const refs = (message.references || []).map(r => el('span', { class: 'gf-chip', title: r.id || r.referenceId || '', text: r.label || r.param || KIND[r.type] || 'reference' }));
    const node = el('div', { class: `gf-msg gf-user${pending ? ' gf-pending' : ''}` }, [
      el('div', { class: 'gf-role', text: 'You' }),
      el('div', { class: 'gf-text', text: message.text || '' }),
      refs.length ? el('div', { class: 'gf-chips' }, refs) : null,
    ]);
    if (t.user) t.user.replaceWith(node);
    else t.node.prepend(node);
    t.user = node;
    t.hasUser = !pending;
  };

  /* The agent's answer bubble of a turn, made on its first item */
  const answerOf = n => {
    const t = turnOf(n);
    if (t.answer) return t.answer;
    const stepsBody = el('div', { class: 'gf-steps-body' });
    const summary = el('summary', { text: 'Steps' });
    const steps = el('details', { class: 'gf-steps', hidden: true }, [summary, stepsBody]);
    const parts = el('div', { class: 'gf-parts' });
    const results = el('div', { class: 'gf-results' });
    const node = el('div', { class: 'gf-msg gf-assistant' }, [el('div', { class: 'gf-role', text: 'Flow agent' }), steps, parts, results]);
    t.node.insertBefore(node, t.approval || null);
    t.answer = { node, steps, summary, stepsBody, parts, results, counts: { thinking: 0, tools: 0 } };
    return t.answer;
  };

  /* Tool results that made an image or video: their media ids, status and names (images come back done, videos queued) */
  const mediaFromResult = (item, turn) => {
    const r = item.result || {};
    if (!r.media_id || !/^(generate|edit|extend)_/.test(item.tool)) return null;
    return {
      mediaId: r.media_id, type: item.tool === 'generate_image' ? 'image' : 'video', status: r.status === 'success' ? 'completed' : r.status || 'pending',
      displayName: r.display_name, model: r.model_key || r.model_usage_key, error: r.error_code, turn,
    };
  };

  /* The agent's items, in order: text (with choices) and errors in the bubble, thinking and tool calls in the collapsed Steps,
     images and videos as results under the text */
  const addItems = (n, items) => {
    if (!items || !items.length) return;
    const a = answerOf(n);
    for (const item of items) {
      if (item.kind === 'text') {
        if (item.text) a.parts.append(renderMarkdown(el('div', { class: 'gf-text' }), item.text));
        if (item.choices && item.choices.length)
          a.parts.append(el('div', { class: 'gf-choices' }, item.choices.map(c => el('button', {
            type: 'button', class: 'gf-btn gf-btn-sm', title: 'Send this as your next message', onclick: () => sendText(c.label),
          }, [el('span', { text: c.label }), c.description ? el('small', { text: c.description }) : null]))));
        if (item.choices && item.choices.length || item.text && item.text.length > 400) a.node.classList.add('gf-wide');
      } else if (item.kind === 'thinking' || item.kind === 'tool_call' || item.kind === 'tool_result') {
        a.stepsBody.append(renderStep(item));
        if (item.kind === 'thinking') a.counts.thinking++;
        else if (item.kind === 'tool_call') a.counts.tools++;
        a.steps.hidden = false;
        a.summary.textContent = ['Steps', a.counts.thinking ? 'thinking' : '', a.counts.tools ? `${a.counts.tools} tool call${a.counts.tools === 1 ? '' : 's'}` : ''].filter(Boolean).join(' · ');
        if (item.kind === 'tool_result') {
          const m = mediaFromResult(item, n);
          if (m) upsertMedia(m);
        }
      } else if (item.kind === 'error') a.parts.append(el('div', { class: 'gf-agent-error', text: `The agent reported an error (code ${item.code}).` }));
    }
    scrollDown();
  };

  /* A message from the stream: each id once; turns drawn from GET are skipped */
  const addStreamMessage = msg => {
    const chat = state.chat;
    if (chat.fromHistory.has(msg.turn) || chat.seen.has(msg.id)) return;
    chat.seen.add(msg.id);
    addItems(msg.turn, msg.items);
    if (chat.approval && msg.turn > chat.approval.turn) closeApproval('answered');
  };
  const turnError = (n, error) => {
    if (!error) return;
    const t = turnOf(n);
    t.node.querySelectorAll(':scope > .gf-turn-error').forEach(x => x.remove());
    const text = typeof error === 'string' ? error : error.message || JSON.stringify(error);
    t.node.append(el('div', { class: 'gf-turn-error', role: 'status', text: maskEmails(`This turn failed${error.code ? ` (${error.code})` : ''}: ${text}`) }));
  };

  /* --- Results: one media object per mediaId, drawn inline in its turn and as a card in the media panel --- */
  const mediaActions = {
    onOpen: m => openLightbox(m, chatMediaList()),
    onBroken: m => refreshLink(m),
    onDownload: (m, button, msg) => downloadMedia(m, button, msg),
    onUse: m => useMedia(m),
    onCopy: (text, msg) => copyText(text, msg),
  };
  const chatMediaList = () => [...state.chat.media.values()].filter(m => isDone(m.status) && m.url);
  const upsertMedia = m => {
    const chat = state.chat;
    const prev = chat.media.get(m.mediaId) || {};
    /* a known link is kept (a new signature would restart a playing video) unless it was renewed on purpose (forceUrl) */
    const next = Object.assign({}, prev, m, { url: prev.url && !m.forceUrl ? prev.url : m.url || prev.url, referenceId: m.referenceId || prev.referenceId, turn: m.turn || prev.turn, displayName: m.displayName || prev.displayName });
    if (prev.figure && prev.status === next.status && prev.url === next.url && prev.referenceId === next.referenceId) return;
    chat.media.set(m.mediaId, next);
    const figure = resultFigure(next, mediaActions);
    if (prev.figure && prev.figure.isConnected) prev.figure.replaceWith(figure);
    else if (next.turn) answerOf(next.turn).results.append(figure);
    next.figure = figure;
    renderMediaPanel();
    scrollDown();
  };
  /* A link that stopped loading (expired): GET /assets/{referenceId} once for a fresh one */
  const refreshLink = async m => {
    if (!m.referenceId || m.refreshed) return;
    m.refreshed = true;
    try {
      state.urls.delete(m.referenceId);
      const url = await freshUrl(m.referenceId);
      if (state.chat.media.get(m.mediaId) === m) upsertMedia({ mediaId: m.mediaId, url, forceUrl: true });
    } catch (err) { /* the preview keeps its broken image; Reload chat tries again */ }
  };
  const renderMediaPanel = () => {
    const list = $('gf-chat-media');
    const items = [...state.chat.media.values()].sort((x, y) => (y.turn || 0) - (x.turn || 0));
    $('gf-media-count').textContent = items.length ? String(items.length) : '';
    $('gf-chat-media-state').hidden = !!items.length;
    list.textContent = '';
    for (const m of items) list.append(mediaCard(m, mediaActions));
  };

  /* --- The approval card: the agent asks to spend credits (cost, images, videos) --- */
  const showApproval = a => {
    const chat = state.chat;
    if (chat.approval && chat.approval.turn === a.turn && chat.approval.card.isConnected) return;
    closeApproval();
    const t = turnOf(a.turn);
    const msg = el('div', { class: 'gf-item-msg', role: 'status' });
    const buttons = [['approve', 'Approve', 'gf-btn-primary'], ['always', 'Always approve', ''], ['reject', 'Reject', 'gf-btn-danger']]
      .map(([decision, label, cls]) => el('button', { type: 'button', class: `gf-btn gf-btn-sm ${cls}`, text: label, 'data-decision': decision, onclick: ev => answerApproval(decision, label, ev.currentTarget, msg) }));
    const card = el('div', { class: 'gf-approval', role: 'group', 'aria-label': 'Request to spend credits' }, [
      el('div', { class: 'gf-approval-title', text: 'The agent asks to spend credits' }),
      el('p', { text: `${sentence(approvalSummary(a))} Approve to let it generate. Always approve also stops it asking (sets approval to automatic in Agent settings).` }),
      el('div', { class: 'gf-actions' }, buttons),
      msg,
    ]);
    t.node.append(card);
    t.approval = card;
    chat.approval = Object.assign({}, a, { card, buttons, msg });
    scrollDown(true);
  };
  const closeApproval = (how, label) => {
    const a = state.chat.approval;
    if (!a) return;
    a.card.classList.add('gf-approval-done');
    for (const b of a.buttons) b.remove();
    if (how) showMsg(a.msg, label ? `You answered: ${label}.` : 'Answered.');
    else a.card.remove();
    state.chat.approval = null;
  };

  /* --- Opening a chat: GET /agent/chats/{chatId}, then the stream --- */
  /* Draw GET /agent/chats/{chatId}. On first load, turns 1..K come from it and the stream starts after turn K (K = every turn, or
     all but the last while a turn runs, so the stream replays the running one with its ids). Later (refresh): titles, your
     messages, media links and status; a turn with no answer yet takes the history's. */
  const applyChat = (data, initial) => {
    const chat = state.chat;
    setTitle(data.title);
    const turns = data.turns || [];
    const K = data.status === 'running' ? Math.max(0, turns.length - 1) : turns.length;
    for (const t of turns) {
      const view = turnOf(t.turn);
      /* your own wording stays when you sent it from this page (Google stores mentions as "@Image I") */
      if (t.message && (t.message.text || (t.message.references || []).length) && !view.hasUser) setUser(t.turn, t.message);
      const empty = !view.answer;
      const fromHistory = initial ? t.turn <= K : empty && (t.turn < turns.length || data.status !== 'running');
      if (fromHistory && !chat.fromHistory.has(t.turn)) {
        chat.fromHistory.add(t.turn);
        addItems(t.turn, t.agent || []);
      }
      for (const m of t.media || []) upsertMedia(Object.assign({}, m, { turn: t.turn }));
    }
    setStatus(data.status);
    if (data.status === 'waiting_approval' && data.pendingApproval) showApproval(data.pendingApproval);
    if (data.lastError && data.status === 'failed') turnError(data.lastError.turn, data.lastError);
    return K;
  };

  const openChat = async (chatId, opts) => {
    const o = opts || {};
    if (!state.email) return;
    stopStream();
    state.chat = newChat(chatId);
    log().textContent = '';
    msgs().append(el('div', { class: 'gf-state', text: 'Loading the chat…' }));
    const c = listed(chatId);
    $('gf-chat-title').textContent = (c && c.title) || 'New chat';
    $('gf-reload').disabled = false;
    renderMediaPanel();
    renderChats();
    showChatsDrawer(false);
    setStatus(o.turn ? 'running' : 'idle');
    let after;
    if (!o.skipRead) {
      try {
        const data = await api.getChat(chatId);
        if (state.chat.id !== chatId) return;
        log().textContent = '';
        const K = applyChat(data, true);
        after = K > 0 ? `${K}:end` : undefined;
      } catch (err) {
        if (state.chat.id !== chatId) return;
        log().textContent = '';
        msgs().append(el('div', { class: 'gf-turn-error', role: 'status', text: maskEmails(err.status === 404 ? 'This chat no longer exists in Google Flow.' : `Could not read the chat: ${err.message}`) }));
        if (err.status === 404 || err.status === 403 || err.status === 400) return;
      }
    } else {
      log().textContent = '';
      after = o.turn > 1 ? `${o.turn - 1}:end` : undefined;
    }
    if (o.user) setUser(o.turn, o.user);
    renderMediaPanel();
    startStream(after);
    scrollDown(true);
  };

  const startNewChat = () => {
    stopStream();
    state.chat = newChat(null);
    $('gf-chat-title').textContent = 'New chat';
    $('gf-reload').disabled = true;
    setConn('off', 'Offline');
    setStatus('idle');
    renderEmpty();
    renderMediaPanel();
    renderChats();
  };

  /* After a turn ends: read the chat again (your message as Google stored it, the title, media links), Google's history trails
     the stream by about a second */
  const refreshChatSoon = () => {
    const chat = state.chat;
    clearTimeout(chat.refreshTimer);
    chat.refreshTimer = setTimeout(async () => {
      if (state.chat !== chat) return;
      try {
        const data = await api.getChat(chat.id);
        if (state.chat === chat) applyChat(data, false);
      } catch (err) { /* the stream already showed the turn */ }
    }, 2000);
  };

  /* ======================================================================
     6. The stream: GET /agent/chats/{chatId}/stream (sse.js)
     ====================================================================== */
  const CONN = { connecting: ['connecting', 'Connecting…'], live: ['live', 'Live'], retry: ['retry', 'Reconnecting…'], idle: ['off', 'Paused'], error: ['error', 'Stream error'], off: ['off', 'Offline'] };
  const stopStream = () => {
    if (state.chat.stream) state.chat.stream.close();
    state.chat.stream = null;
  };
  const startStream = after => {
    const chat = state.chat;
    if (!chat.id) return;
    if (chat.stream) chat.stream.close();
    chat.stream = sse.followStream({
      url: api.streamUrl(chat.id),
      token: state.token,
      lastEventId: after,
      onEvent: ev => { if (state.chat === chat) onStreamEvent(ev); },
      onState: (s, detail) => {
        if (state.chat !== chat) return;
        const [kind, text] = CONN[s] || ['off', s];
        setConn(kind, text, s === 'idle' ? 'No activity for 10 minutes. It opens again when you send or press ↻.' : detail);
        if (s === 'error') turnError(maxTurn() || 1, `Live updates stopped: ${detail}`);
      },
    });
  };
  /* Reopen a stream the API closed (idle) or that failed, from the last event it delivered */
  const ensureStream = () => {
    const chat = state.chat;
    if (chat.stream && !chat.stream.closed) return;
    startStream(chat.stream && chat.stream.lastId ? chat.stream.lastId : maxTurn() > 1 ? `${maxTurn() - 1}:end` : undefined);
  };
  const onStreamEvent = ({ event, data }) => {
    const chat = state.chat;
    switch (event) {
      case 'chat':
        setTitle(data.title);
        if (!state.sending) setStatus(data.status);
        break;
      case 'message':
        addStreamMessage(data);
        break;
      case 'approval':
        if (data.turn >= maxTurn() && !chat.turns.has(data.turn + 1)) showApproval(data);
        break;
      case 'turn':
        setStatus(data.status === 'completed' ? 'idle' : data.status);
        if (data.status === 'failed') turnError(data.turn, data.error);
        refreshChatSoon();
        break;
      case 'media':
        upsertMedia(data);
        break;
      case 'error':
        turnError(maxTurn() || 1, data && data.message ? data.message : 'The stream reported an error');
        break;
      default: /* replayed, keepalive, idle, reconnect */
    }
  };

  /* ======================================================================
     7. Sending: POST /agent/chats (first message) or /messages, choices, approvals, and what each error answer means
     ====================================================================== */
  const renderActivity = () => {
    const chat = state.chat;
    let text = 'Ready';
    let busy = false;
    if (state.sending) {
      busy = true;
      text = `${state.sending.label}… ${Math.round((Date.now() - state.sending.since) / 1000)} s (Google can take up to ~100 s to accept a turn)`;
    } else if (chat.status === 'running') {
      busy = true;
      text = `The agent is working… ${Math.max(0, Math.round((Date.now() - chat.runningSince) / 1000))} s`;
    } else if (chat.status === 'waiting_approval') text = 'Waiting for your approval';
    else if (chat.status === 'failed') text = 'The last turn failed';
    $('gf-activity').textContent = text;
    $('gf-spinner').hidden = !busy;
    const box = msgs();
    if (chat.status === 'running' && !state.sending && chat.id) {
      workingLine.textContent = 'The agent is working…';
      if (workingLine.parentNode !== box || box.lastElementChild !== workingLine) box.append(workingLine);
    } else workingLine.remove();
  };
  setInterval(renderActivity, 1000);

  const setSending = label => {
    state.sending = label ? { label, since: Date.now() } : null;
    $('gf-send').disabled = !!label;
    if (state.chat.approval) for (const b of state.chat.approval.buttons) b.disabled = !!label;
    renderActivity();
  };

  /* What each error answer of a send means for the user */
  const sendError = (err, chatId) => {
    const d = err.data || {};
    if (err.status === 409) return `${sentence(err.message)} Watch the answer, then send again.`;
    if (err.status === 429) {
      const at = Date.parse(d.retryAfter || '');
      return `${sentence(err.message)}${Number.isFinite(at) ? ` Try again in ${Math.max(1, Math.round((at - Date.now()) / 1000))} s.` : ''}`;
    }
    if (err.status === 504 || err.timeout) {
      const target = d.chatId || chatId;
      if (target) setTimeout(() => { if (!state.chat.id || state.chat.id === target) openChat(target); }, 5000);
      else setTimeout(loadChats, 10000);
      return `${err.status === 504 ? sentence(err.message) : 'No answer within 150 s, but the turn may still start.'} The chat reloads in a few seconds: check it before sending again.`;
    }
    if (err.status === 502 || err.status === 503) return `${sentence(err.message)}${d.reason ? ` (${d.reason})` : ''}`;
    if (err.status === 400) return `${sentence(err.message)}`;
    return err.status > 0 ? `${sentence(err.message)} (HTTP ${err.status})` : err.message;
  };

  const sendText = async text => {
    const message = String(text || '').trim();
    const msg = $('gf-composer-msg');
    if (!state.email) return showMsg(msg, 'Connect and pick an account first.', 'error');
    if (state.sending) return showMsg(msg, 'Still sending the previous message.', 'error');
    if (!message) return;
    if (state.attachments.some(a => a.status === 'uploading')) return showMsg(msg, 'Wait for the uploads to finish.', 'error');
    const ready = state.attachments.filter(a => a.status === 'ready');
    const refs = Object.fromEntries(ready.map(a => [a.param, a.referenceId || a.voice]));
    const references = ready.map(a => ({ param: a.param, label: `@${a.param}`, id: a.referenceId || a.voice }));
    const chatId = state.chat.id;
    showMsg(msg, '');
    const pending = el('div', { class: 'gf-turn' });
    msgs().querySelector('.gf-empty') && msgs().querySelector('.gf-empty').remove();
    msgs().append(pending);
    pending.append(el('div', { class: 'gf-msg gf-user gf-pending' }, [el('div', { class: 'gf-role', text: 'You' }), el('div', { class: 'gf-text', text: message }),
      references.length ? el('div', { class: 'gf-chips' }, references.map(r => el('span', { class: 'gf-chip', text: r.label }))) : null]));
    scrollDown(true);
    setSending('Waiting for Google to accept the turn');
    try {
      const body = Object.assign({ message }, refs);
      const data = chatId ? await api.sendMessage(chatId, body) : await api.createChat(Object.assign({ email: state.email }, body));
      pending.remove();
      showMsg(msg, '');
      $('gf-input').value = '';
      autoGrow();
      state.attachments = [];
      renderAttachments();
      setSending(null);
      if (!chatId) {
        await openChat(data.chatId, { skipRead: true, turn: data.turn, user: { text: message, references } });
        setStatus('running');
        loadChats();
      } else if (state.chat.id === chatId) {
        closeApproval();
        setUser(data.turn, { text: message, references });
        setStatus('running');
        ensureStream();
        scrollDown(true);
      }
    } catch (err) {
      pending.remove();
      setSending(null);
      showMsg(msg, sendError(err, chatId), err.status === 409 || err.status === 429 || err.status === 504 || err.timeout ? '' : 'error');
    } finally {
      if (state.sending) setSending(null);
    }
  };
  const send = () => sendText($('gf-input').value);

  /* POST /agent/chats/{chatId}/approval {decision}: Approve, Always approve or Reject. It starts the next turn (202). */
  const answerApproval = async (decision, label, button, msg) => {
    const chat = state.chat;
    if (state.sending) return;
    setBusy(button, true);
    setSending(`${label}: waiting for Google to accept the turn`);
    try {
      const data = await api.answerApproval(chat.id, decision);
      setSending(null);
      if (state.chat !== chat) return;
      closeApproval('answered', label);
      setUser(data.turn, { text: label });
      setStatus('running');
      ensureStream();
    } catch (err) {
      setSending(null);
      setBusy(button, false);
      showMsg(msg, sendError(err, chat.id), 'error');
    }
  };

  const autoGrow = () => {
    const t = $('gf-input');
    t.style.height = 'auto';
    t.style.height = `${Math.min(180, t.scrollHeight + 2)}px`;
  };

  /* ======================================================================
     8. Attachments: upload (button, drop, paste), earlier media, characters, voices
     ====================================================================== */
  /* The next free slot of a kind: referenceImage_1..7, referenceVideo_1, referenceAudio_1..5, character_1..7. A removed chip
     frees its slot; the others keep theirs, so @-mentions already typed stay right. */
  const nextSlot = kind => {
    const used = new Set(state.attachments.map(a => a.param));
    const s = SLOTS[kind];
    for (let i = 1; i <= s.max; i++) if (!used.has(`${s.param}_${i}`)) return `${s.param}_${i}`;
    return '';
  };
  const addAttachment = item => {
    const msg = $('gf-composer-msg');
    const key = item.referenceId || item.voice;
    if (key && state.attachments.some(a => (a.referenceId || a.voice) === key)) { showMsg(msg, `${item.label} is already attached.`); return null; }
    const param = nextSlot(item.kind);
    if (!param) {
      const s = SLOTS[item.kind];
      showMsg(msg, `At most ${s.max} ${item.kind === 'audio' ? 'voice' : item.kind}${s.max === 1 ? '' : 's'} per message.`, 'error');
      return null;
    }
    const a = Object.assign({ key: `${Date.now()}-${Math.random()}`, status: 'ready', param }, item);
    state.attachments.push(a);
    renderAttachments();
    showMsg(msg, '');
    return a;
  };
  const removeAttachment = a => {
    state.attachments = state.attachments.filter(x => x !== a);
    if (a.localUrl) URL.revokeObjectURL(a.localUrl);
    renderAttachments();
  };
  const insertMention = param => {
    const ta = $('gf-input');
    const at = ta.selectionStart === undefined ? ta.value.length : ta.selectionStart;
    const before = ta.value.slice(0, at);
    const mention = `${before && !/\s$/.test(before) ? ' ' : ''}@${param} `;
    ta.value = before + mention + ta.value.slice(ta.selectionEnd === undefined ? at : ta.selectionEnd);
    ta.focus();
    ta.selectionStart = ta.selectionEnd = at + mention.length;
    autoGrow();
  };
  const renderAttachments = () => {
    const box = $('gf-attachments');
    box.textContent = '';
    for (const a of state.attachments) {
      const thumb = a.thumb ? el('img', { class: 'gf-chip-thumb', src: a.thumb, alt: '' }) : el('span', { class: 'gf-chip-thumb', 'aria-hidden': 'true', text: a.kind === 'audio' ? '♪' : a.kind === 'character' ? (a.label || '?')[0].toUpperCase() : a.kind === 'video' ? '▶' : '' });
      box.append(el('span', { class: `gf-chip${a.status === 'uploading' ? ' gf-chip-uploading' : ''}${a.status === 'error' ? ' gf-chip-error' : ''}`, title: a.error || a.referenceId || a.voice || '' }, [
        thumb,
        el('span', { class: 'gf-chip-label' }, [
          el('span', { text: a.status === 'uploading' ? `Uploading ${a.label}…` : a.status === 'error' ? `${a.label}: ${a.error}` : a.label }),
          a.status === 'ready' ? el('button', { type: 'button', class: 'gf-mention', text: `@${a.param}`, title: 'Insert the mention into your message', onclick: () => insertMention(a.param) }) : null,
        ]),
        el('button', { type: 'button', class: 'gf-icon-btn', 'aria-label': `Remove ${a.label}`, title: 'Remove', text: '✕', onclick: () => removeAttachment(a) }),
      ]));
    }
    if (state.attachments.length && !$('gf-composer-msg').textContent)
      showMsg($('gf-composer-msg'), 'Attached to your next message. Mention one by clicking its @ name, or just send.');
    else if (!state.attachments.length && /^Attached to your next message/.test($('gf-composer-msg').textContent)) showMsg($('gf-composer-msg'), '');
  };

  /* Upload images from disk, a drop or a paste: POST /assets/{email}; each shows as a chip and is attached when ready. */
  const uploadImages = files => {
    const msg = $('gf-composer-msg');
    if (!state.email) return showMsg(msg, 'Connect and pick an account first.', 'error');
    for (const file of files) {
      if (!config.UPLOAD_TYPES.includes(file.type)) { showMsg(msg, `${file.name || 'That file'}: only JPEG, PNG and WebP images can be attached.`, 'error'); continue; }
      const localUrl = URL.createObjectURL(file);
      const a = addAttachment({ kind: 'image', label: file.name || 'Pasted image', thumb: localUrl, localUrl, status: 'uploading' });
      if (!a) { URL.revokeObjectURL(localUrl); continue; }
      const email = state.email;
      api.upload(email, file).then(d => {
        a.referenceId = d.referenceId;
        a.status = 'ready';
        state.library.delete(`${email}|`);
      }, err => {
        a.status = 'error';
        a.error = maskEmails(err.message);
      }).finally(renderAttachments);
    }
  };
  /* "Use in next message" on a result, a Library card or the lightbox */
  const useMedia = m => {
    const a = addAttachment({ kind: m.type === 'video' ? 'video' : 'image', referenceId: m.referenceId, label: m.displayName || (m.type === 'video' ? 'Video' : 'Image'), thumb: m.type === 'video' ? '' : m.url });
    if (a) { showTab('chat'); showMsg($('gf-composer-msg'), `Attached as @${a.param}.`, 'ok'); $('gf-input').focus(); }
    return a;
  };

  /* The Attach menu */
  const menu = $('gf-attach-menu');
  const showMenu = open => {
    menu.hidden = !open;
    $('gf-attach').setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) menu.querySelector('button').focus();
  };
  const onMenu = what => {
    showMenu(false);
    if (what === 'upload') return $('gf-upload').click();
    openPicker(what);
  };

  /* The picker dialog: earlier images and videos (GET /assets/media/{email}), characters (GET /characters), voices (GET /voices) */
  const picker = $('gf-picker');
  const openPicker = what => {
    if (!state.email) return showMsg($('gf-composer-msg'), 'Connect and pick an account first.', 'error');
    if (!picker.open) picker.showModal();
    showPick(what);
  };
  const pickTabs = () => [...picker.querySelectorAll('[data-pick]')];
  const showPick = what => {
    state.pick = what;
    for (const b of pickTabs()) {
      const on = b.dataset.pick === what;
      b.setAttribute('aria-selected', on ? 'true' : 'false');
      b.tabIndex = on ? 0 : -1;
    }
    $('gf-picker-grid').textContent = '';
    $('gf-picker-more').hidden = true;
    $('gf-picker-tools').textContent = '';
    if (what === 'media') pickMedia();
    else if (what === 'characters') pickCharacters();
    else pickVoices();
  };
  const isAttached = id => state.attachments.some(a => (a.referenceId || a.voice) === id);
  const pickItem = (attrs, children, attach) => {
    const button = el('button', Object.assign({ type: 'button', class: 'gf-pick', role: 'listitem' }, attrs), children);
    button.addEventListener('click', () => {
      const id = attrs['data-id'];
      if (isAttached(id)) { const a = state.attachments.find(x => (x.referenceId || x.voice) === id); if (a) removeAttachment(a); }
      else attach();
      button.setAttribute('aria-pressed', isAttached(id) ? 'true' : 'false');
    });
    button.setAttribute('aria-pressed', isAttached(attrs['data-id']) ? 'true' : 'false');
    return button;
  };
  /* A thumbnail that reads its link once it scrolls into view */
  const lazyThumb = item => {
    const box = el('div', { class: 'gf-preview gf-loading' });
    whenVisible(box, async () => {
      try {
        const url = await freshUrl(item.referenceId);
        item.url = url;
        box.classList.remove('gf-loading');
        box.append(item.type === 'video' ? el('video', { src: `${url}#t=0.1`, preload: 'metadata', muted: true, playsinline: true }) : el('img', { src: url, alt: '', loading: 'lazy' }));
        if (item.type === 'video') box.append(el('span', { class: 'gf-play', 'aria-hidden': 'true' }));
      } catch (err) {
        box.classList.remove('gf-loading');
        box.append(el('span', { text: 'No preview' }));
      }
    });
    return box;
  };
  const pickMedia = async () => {
    const tools = $('gf-picker-tools');
    showMsg($('gf-picker-msg'), 'Reading the project…');
    await loadSettingsQuietly();
    if (state.pick !== 'media') return;
    const project = el('select', { 'aria-label': 'Project' }, projectOptions());
    project.value = $('gf-l-project').value;
    const type = el('select', { 'aria-label': 'Type' }, [el('option', { value: '', text: 'Images and videos' }), el('option', { value: 'IMAGE', text: 'Images' }), el('option', { value: 'VIDEO', text: 'Videos' })]);
    const draw = async () => {
      const grid = $('gf-picker-grid');
      grid.textContent = '';
      showMsg($('gf-picker-msg'), 'Reading the project (a large one takes a few seconds)…');
      try {
        const all = await libraryMedia(project.value, false);
        if (state.pick !== 'media' || !project.isConnected) return;
        const items = all.filter(m => !type.value || m.mediaType === type.value);
        let shown = 0;
        const more = () => {
          for (const m of items.slice(shown, shown + LIBRARY_PAGE)) {
            grid.append(pickItem({ 'data-id': m.referenceId, title: m.referenceId }, [
              lazyThumb(m),
              el('span', { class: 'gf-pick-name', text: `${m.type === 'video' ? 'Video' : 'Image'}${m.likelyUpload ? ' · upload' : ''}` }),
              el('span', { class: 'gf-pick-meta', text: fmtShort(m.createTime) }),
            ], () => addAttachment({ kind: m.type, referenceId: m.referenceId, label: `${m.type === 'video' ? 'Video' : 'Image'} ${fmtShort(m.createTime)}`, thumb: m.type === 'video' ? '' : m.url || '' })));
          }
          shown += LIBRARY_PAGE;
          $('gf-picker-more').hidden = shown >= items.length;
          $('gf-picker-more').onclick = more;
        };
        showMsg($('gf-picker-msg'), items.length ? `${items.length} in this project, newest first. Click to attach, click again to remove.` : 'Nothing here yet. Upload an image or let the agent make one.');
        more();
      } catch (err) {
        showMsg($('gf-picker-msg'), err.message, 'error');
      }
    };
    project.addEventListener('change', draw);
    type.addEventListener('change', draw);
    tools.append(el('label', {}, ['Project', project]), el('label', {}, ['Type', type]));
    draw();
  };
  const pickCharacters = async () => {
    showMsg($('gf-picker-msg'), 'Reading characters…');
    try {
      if (!state.characters) state.characters = (await api.characters(state.email)).characters || [];
      if (state.pick !== 'characters') return;
      const grid = $('gf-picker-grid');
      for (const c of state.characters) {
        const name = c.displayName || 'Character';
        grid.append(pickItem({ 'data-id': c.character, title: c.character }, [
          el('div', { class: 'gf-avatar', 'aria-hidden': 'true', text: name[0].toUpperCase() }),
          el('span', { class: 'gf-pick-name', text: name }),
          el('span', { class: 'gf-pick-meta', text: c.voice ? `voice ${c.voice.displayName || c.voice.voice}` : c.personalityNotes || '' }),
        ], () => addAttachment({ kind: 'character', referenceId: c.character, label: name })));
      }
      showMsg($('gf-picker-msg'), state.characters.length ? 'Click to attach a character, click again to remove.' : 'No characters on this account yet (POST /characters makes one).');
    } catch (err) {
      showMsg($('gf-picker-msg'), err.message, 'error');
    }
  };
  const pickVoices = async () => {
    showMsg($('gf-picker-msg'), 'Reading voices…');
    try {
      if (!state.voices) state.voices = (await api.voices(state.email)).voices || [];
      if (state.pick !== 'voices') return;
      const grid = $('gf-picker-grid');
      const own = state.voices.filter(v => v.source !== 'system');
      const builtIn = state.voices.filter(v => v.source === 'system');
      for (const v of own.concat(builtIn)) {
        const name = v.displayName || v.voice;
        const sample = v.sampleUrl ? el('audio', { src: v.sampleUrl, preload: 'none', controls: true, style: 'width:100%;height:28px' }) : null;
        if (sample) sample.addEventListener('click', e => e.stopPropagation());
        grid.append(pickItem({ 'data-id': v.voice, title: v.voice }, [
          el('span', { class: 'gf-pick-name', text: name }),
          el('span', { class: 'gf-pick-meta', text: v.source === 'system' ? 'built-in' : `your voice${v.baseVoice ? ` · from ${v.baseVoice}` : ''}` }),
          sample,
        ], () => addAttachment(v.source === 'system' ? { kind: 'audio', voice: v.voice, label: name } : { kind: 'audio', referenceId: v.voice, label: name })));
      }
      showMsg($('gf-picker-msg'), `${own.length} of your own and ${builtIn.length} built-in voices. Click to attach, click again to remove.`);
    } catch (err) {
      showMsg($('gf-picker-msg'), err.message, 'error');
    }
  };

  /* ======================================================================
     9. Lightbox and download
     ====================================================================== */
  const lb = { list: [], index: 0 };
  const lightbox = $('gf-lightbox');
  const openLightbox = (media, list) => {
    lb.list = list && list.length ? list : [media];
    lb.index = Math.max(0, lb.list.findIndex(m => m === media || (m.mediaId && m.mediaId === media.mediaId) || (m.referenceId && m.referenceId === media.referenceId)));
    if (!lightbox.open) lightbox.showModal();
    drawLightbox();
  };
  const drawLightbox = () => {
    const m = lb.list[lb.index];
    const stage = $('gf-lb-stage');
    stage.textContent = '';
    stage.classList.remove('gf-zoomed');
    $('gf-lb-msg').textContent = '';
    $('gf-lb-title').textContent = `${m.displayName || (m.type === 'video' ? 'Video' : 'Image')}${lb.list.length > 1 ? `  ·  ${lb.index + 1} of ${lb.list.length}` : ''}`;
    $('gf-lb-prev').disabled = lb.index === 0;
    $('gf-lb-next').disabled = lb.index >= lb.list.length - 1;
    $('gf-lb-use').disabled = !m.referenceId;
    const media = m.type === 'video'
      ? el('video', { src: m.url, controls: true, autoplay: true, playsinline: true })
      : el('img', { src: m.url, alt: m.displayName || 'Image', title: 'Click to zoom', onclick: () => stage.classList.toggle('gf-zoomed') });
    media.addEventListener('error', async () => {
      if (!m.referenceId || media.dataset.retried) return;
      media.dataset.retried = '1';
      try {
        state.urls.delete(m.referenceId);
        m.url = await freshUrl(m.referenceId);
        media.src = m.url;
      } catch (err) { $('gf-lb-msg').textContent = maskEmails(err.message); }
    });
    stage.append(media);
  };
  const stepLightbox = d => {
    const i = lb.index + d;
    if (i < 0 || i >= lb.list.length) return;
    lb.index = i;
    drawLightbox();
  };
  /* Download: the signed link read as a Blob and saved under a file name (api.js). An expired link is renewed first. */
  const downloadMedia = async (m, button, msg) => {
    setBusy(button, true);
    if (msg) showMsg(msg, '');
    try {
      await api.download(m, url => {
        m.url = url;
        if (m.mediaId && state.chat.media.get(m.mediaId) === m) upsertMedia({ mediaId: m.mediaId, url, forceUrl: true });
      });
    } catch (err) {
      if (msg) showMsg(msg, `Download failed: ${err.message}`, 'error');
    } finally {
      setBusy(button, false);
    }
  };

  /* ======================================================================
     10. Library tab: the account's images and videos (GET /assets/media/{email}), upload, delete
     ====================================================================== */
  const projectOptions = () => {
    const opts = [el('option', { value: '', text: 'Main project (API generations and uploads)' })];
    if (state.settings && state.settings.projectId) opts.push(el('option', { value: state.settings.projectId, text: 'Agent project (what the agent made)' }));
    return opts;
  };
  const fillProjects = () => {
    const sel = $('gf-l-project');
    const keep = sel.value;
    sel.textContent = '';
    for (const o of projectOptions()) sel.append(o);
    sel.value = [...sel.options].some(o => o.value === keep) ? keep : '';
  };
  /* GET /assets/media/{email}?projectId=: every image and video in the project, newest first (cached for the page) */
  const libraryMedia = async (projectId, force) => {
    const key = `${state.email}|${projectId || ''}`;
    if (!force && state.library.has(key)) return state.library.get(key);
    const pending = api.projectMedia(state.email, projectId || undefined).then(d => (d.media || [])
      .filter(m => m.mediaType === 'IMAGE' || m.mediaType === 'VIDEO')
      .sort((x, y) => String(y.createTime || '').localeCompare(String(x.createTime || '')))
      .map(m => ({ referenceId: m.mediaGenerationId, mediaId: m.mediaGenerationId.split(':').pop(), type: m.mediaType === 'VIDEO' ? 'video' : 'image', status: 'completed', createTime: m.createTime, likelyUpload: m.likelyUpload, mediaType: m.mediaType })));
    pending.catch(() => state.library.delete(key));
    state.library.set(key, pending);
    return pending;
  };
  const loadLibrary = async force => {
    if (!state.email) return;
    if (!state.settings) loadSettingsQuietly().then(fillProjects);
    fillProjects();
    const email = state.email;
    const grid = $('gf-l-grid');
    if (force) state.libraryShown = LIBRARY_PAGE;
    showMsg($('gf-l-state'), 'Reading the project (a large one takes a few seconds)…');
    try {
      const all = await libraryMedia($('gf-l-project').value, force);
      if (email !== state.email) return;
      const type = $('gf-l-type').value;
      const items = all.filter(m => (!type || m.mediaType === type) && (!$('gf-l-uploads').checked || m.likelyUpload));
      grid.textContent = '';
      for (const m of items.slice(0, state.libraryShown)) grid.append(libraryCard(m));
      showMsg($('gf-l-state'), items.length ? '' : 'Nothing here yet.');
      showMsg($('gf-l-msg'), items.length ? `${items.length} of ${all.length} in this project, newest first.` : '');
      $('gf-l-more').hidden = items.length <= state.libraryShown;
    } catch (err) {
      showMsg($('gf-l-state'), err.message, 'error');
    }
  };
  const libraryCard = m => {
    const actions = Object.assign({}, mediaActions, { onOpen: x => openLightbox(x, [x]) });
    const card = mediaCard(Object.assign(m, { url: m.url }), actions, msg => [
      el('button', { type: 'button', class: 'gf-btn gf-btn-sm gf-btn-danger', text: 'Delete', 'aria-label': 'Delete this file', onclick: () => deleteMedia(m, card, msg) }),
    ]);
    /* the card's preview reads its link once visible */
    const placeholder = card.querySelector('.gf-preview');
    whenVisible(card, async () => {
      try {
        m.url = await freshUrl(m.referenceId);
        const fresh = FD.render.preview(m, actions);
        if (placeholder.isConnected) placeholder.replaceWith(fresh);
      } catch (err) { /* keeps the waiting box */ }
    });
    return card;
  };
  /* DELETE /assets/{email} {mediaGenerationIds: [referenceId], projectId}: permanent, on the Google account */
  const deleteMedia = async (m, card, msg) => {
    if (!await confirmInline(card, 'Delete it from the Google Flow account? This cannot be undone.', 'Delete')) return;
    try {
      const projectId = $('gf-l-project').value || undefined;
      await api.deleteMedia(state.email, [m.referenceId], projectId);
      card.remove();
      const key = `${state.email}|${projectId || ''}`;
      const cached = state.library.get(key);
      if (cached) state.library.set(key, cached.then(list => list.filter(x => x !== m)));
    } catch (err) {
      showMsg(msg, err.message, 'error');
    }
  };
  const uploadToLibrary = async files => {
    const msg = $('gf-l-msg');
    for (const file of files) {
      showMsg(msg, `Uploading ${file.name}…`);
      try {
        const d = await api.upload(state.email, file);
        showMsg(msg, `Uploaded ${file.name}. It is in the Library and can be attached to a message.`, 'ok');
        state.library.clear();
        void d;
      } catch (err) {
        showMsg(msg, err.message, 'error');
        return;
      }
    }
    loadLibrary(true);
  };

  /* ======================================================================
     11. Agent settings tab: GET / PUT /agent/settings
     ====================================================================== */
  /* values: plain strings, or [value, text] pairs (the models) */
  const fillSelect = (select, values, current) => {
    select.textContent = '';
    select.append(el('option', { value: '', text: '(not set)' }));
    const pairs = values.map(v => Array.isArray(v) ? v : [v, v]);
    for (const [value, text] of pairs) select.append(el('option', { value, text }));
    /* a saved value the list does not have (a model this plan no longer offers) stays visible and selected */
    if (current !== undefined && current !== null && current !== '' && !pairs.some(([v]) => v === String(current))) select.append(el('option', { value: String(current), text: `${current} (current)` }));
    select.value = current === undefined || current === null ? '' : String(current);
  };
  const instructionBlock = (card, i) => el('div', { class: 'gf-instruction', 'data-id': card ? card.id : '' }, [
    el('div', { class: 'gf-instruction-head' }, [
      el('input', { type: 'text', 'data-f': 'title', placeholder: `Instruction ${i + 1} title (optional)`, value: card && card.title || '', maxlength: '200', 'aria-label': `Instruction ${i + 1} title` }),
      el('label', { class: 'gf-check' }, [el('input', { type: 'checkbox', 'data-f': 'enabled', checked: card ? card.enabled : true }), 'On']),
    ]),
    el('textarea', { rows: '2', 'data-f': 'text', placeholder: 'e.g. Keep answers short. Make videos 16:9.', maxlength: '5000', 'aria-label': `Instruction ${i + 1}` }, card ? card.text : ''),
    el('input', { type: 'text', 'data-f': 'refs', placeholder: 'Image referenceIds that go with it, comma separated (optional)', spellcheck: 'false', 'aria-label': `Instruction ${i + 1} image references` }),
    card && card.references && card.references.length ? el('div', { class: 'gf-item-msg', text: `${card.references.length} image(s) attached in Flow. Saving instructions from here replaces them with the referenceIds above.` }) : null,
  ]);
  const readSettingsForm = () => {
    const instructions = [...document.querySelectorAll('#gf-s-instructions .gf-instruction')].map(b => {
      const f = name => b.querySelector(`[data-f=${name}]`);
      return { id: b.dataset.id || undefined, title: f('title').value.trim() || undefined, text: f('text').value.trim(), enabled: f('enabled').checked, references: f('refs').value.split(',').map(s => s.trim()).filter(Boolean) };
    }).filter(c => c.text);
    const approval = (document.querySelector('input[name=gf-approval]:checked') || {}).value || 'ask';
    return {
      approval, instructions,
      imageDefaults: { model: $('gf-s-img-model').value, aspectRatio: $('gf-s-img-aspect').value, count: $('gf-s-img-count').value },
      videoDefaults: { model: $('gf-s-vid-model').value, aspectRatio: $('gf-s-vid-aspect').value, count: $('gf-s-vid-count').value },
    };
  };
  /* The models this account's Google plan has, from settings.models {image: [{model, label, credits?}], video: [...]}:
     "Veo 3.1 - Fast · 20 credits", "Nano Banana Pro · free", or just the label when the cost is not known. models: null (Google's
     catalog could not be read) falls back to the full list without costs. */
  const modelChoices = (list, fallback) => list ? list.map(m => [m.model, `${m.label || m.model}${typeof m.credits === 'number' ? m.credits === 0 ? ' · free' : ` · ${m.credits} credit${m.credits === 1 ? '' : 's'}` : ''}`]) : fallback;
  const fillSettings = s => {
    state.settings = s;
    $('gf-s-project').textContent = s.projectId ? `project ${s.projectId}` : 'no agent project yet';
    for (const r of document.querySelectorAll('input[name=gf-approval]')) r.checked = r.value === (s.approval || 'ask');
    $('gf-s-instructions').textContent = '';
    for (let i = 0; i < 3; i++) $('gf-s-instructions').append(instructionBlock((s.instructions || [])[i], i));
    const img = s.imageDefaults || {};
    const vid = s.videoDefaults || {};
    const models = s.models || null;
    fillSelect($('gf-s-img-model'), modelChoices(models && models.image, IMAGE_MODELS), img.model);
    fillSelect($('gf-s-img-aspect'), IMAGE_ASPECTS, img.aspectRatio);
    fillSelect($('gf-s-img-count'), COUNTS, img.count);
    fillSelect($('gf-s-vid-model'), modelChoices(models && models.video, VIDEO_MODELS), vid.model);
    $('gf-s-models-note').textContent = models ? 'The models your Google plan has, with what one generation costs.' : 'Google\'s model list for this account could not be read, so every model is listed: one your plan does not have is refused when you save.';
    fillSelect($('gf-s-vid-aspect'), VIDEO_ASPECTS, vid.aspectRatio);
    fillSelect($('gf-s-vid-count'), COUNTS, vid.count);
    settingsSnapshot = readSettingsForm();
    fillProjects();
  };
  const loadSettingsQuietly = async () => {
    try { if (!state.settings) state.settings = await api.getSettings(state.email); } catch (err) { /* the Library still works */ }
  };
  const loadSettings = async () => {
    if (!state.email) return;
    showMsg($('gf-s-msg'), 'Reading settings…');
    try {
      fillSettings(await api.getSettings(state.email));
      showMsg($('gf-s-msg'), '');
    } catch (err) {
      showMsg($('gf-s-msg'), err.message, 'error');
    }
  };
  const saveSettings = async () => {
    const now = readSettingsForm();
    const before = settingsSnapshot || {};
    const changed = k => JSON.stringify(now[k]) !== JSON.stringify(before[k]);
    const body = { email: state.email };
    if (changed('approval')) body.approval = now.approval;
    if (changed('instructions')) body.instructions = now.instructions;
    for (const k of ['imageDefaults', 'videoDefaults']) {
      if (!changed(k)) continue;
      const d = now[k];
      if (!d.model || !d.aspectRatio) return showMsg($('gf-s-msg'), `${k === 'imageDefaults' ? 'Image' : 'Video'} defaults need a model and an aspect ratio.`, 'error');
      body[k] = { model: d.model, aspectRatio: d.aspectRatio, count: Number(d.count || 1) };
    }
    if (Object.keys(body).length === 1) return showMsg($('gf-s-msg'), 'Nothing changed.');
    setBusy($('gf-s-save'), true);
    try {
      fillSettings(await api.putSettings(body));
      showMsg($('gf-s-msg'), 'Saved. New turns use these settings.', 'ok');
    } catch (err) {
      showMsg($('gf-s-msg'), err.message, 'error');
    } finally {
      setBusy($('gf-s-save'), false);
    }
  };

  /* ======================================================================
     12. Layout and boot: drawers, splitters, keyboard, drop and paste, the remembered token
     ====================================================================== */
  const isNarrow = () => $('gf-app').clientWidth <= 640;
  const showMediaPanel = open => {
    if (open && isNarrow()) showChatsDrawer(false);
    $('gf-cols').classList.toggle('gf-media-closed', !open);
    $('gf-media-toggle').setAttribute('aria-expanded', open ? 'true' : 'false');
  };
  const showChatsDrawer = open => {
    if (open && isNarrow()) showMediaPanel(false);
    $('gf-cols').classList.toggle('gf-chats-open', open);
    $('gf-chats-toggle').setAttribute('aria-expanded', open ? 'true' : 'false');
  };
  /* Draggable splitters (mouse, touch, or arrow keys; Shift for bigger steps) */
  const initSplitters = () => {
    const grid = $('gf-cols');
    for (const handle of grid.querySelectorAll('.gf-split')) {
      const left = handle.dataset.side === 'left';
      const pane = $(left ? 'gf-pane-chats' : 'gf-pane-media');
      const setWidth = px => {
        const other = $(left ? 'gf-pane-media' : 'gf-pane-chats').getBoundingClientRect().width;
        const max = Math.max(160, grid.clientWidth - other - 16 - 280);
        const width = Math.round(Math.max(160, Math.min(max, px)));
        grid.style.setProperty(left ? '--gf-left' : '--gf-right', `${width}px`);
        handle.setAttribute('aria-valuenow', String(width));
      };
      handle.addEventListener('pointerdown', e => {
        e.preventDefault();
        handle.setPointerCapture(e.pointerId);
        handle.classList.add('gf-dragging');
        const startX = e.clientX;
        const start = pane.getBoundingClientRect().width;
        const move = ev => setWidth(left ? start + ev.clientX - startX : start - (ev.clientX - startX));
        const up = () => {
          handle.classList.remove('gf-dragging');
          handle.removeEventListener('pointermove', move);
          handle.removeEventListener('pointerup', up);
          handle.removeEventListener('pointercancel', up);
        };
        handle.addEventListener('pointermove', move);
        handle.addEventListener('pointerup', up);
        handle.addEventListener('pointercancel', up);
      });
      handle.addEventListener('keydown', e => {
        const dir = e.key === 'ArrowLeft' ? -1 : e.key === 'ArrowRight' ? 1 : 0;
        if (!dir) return;
        e.preventDefault();
        setWidth(pane.getBoundingClientRect().width + (left ? dir : -dir) * (e.shiftKey ? 64 : 16));
      });
    }
  };
  /* Left and Right arrows move between tabs */
  const arrowTabs = (bar, buttons, current, show) => bar.addEventListener('keydown', e => {
    const step = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
    if (!step) return;
    e.preventDefault();
    const list = buttons();
    const i = list.indexOf(current());
    const next = list[(i + step + list.length) % list.length];
    show(next);
    next.focus();
  });

  const init = () => {
    try {
      const saved = sessionStorage.getItem(TOKEN_KEY);
      if (saved) { $('gf-token').value = saved; $('gf-remember').checked = true; }
    } catch (err) { /* no storage: nothing remembered */ }
    $('gf-dev-badge').hidden = config.API_MODE !== 'dev';
    $('gf-connect-form').addEventListener('submit', e => { e.preventDefault(); connect(); });
    $('gf-remember').addEventListener('change', () => { state.token = $('gf-token').value.trim(); rememberToken(); });
    $('gf-account').addEventListener('change', e => selectAccount(e.target.value));
    for (const t of TABS) $(`gf-tab-${t}`).addEventListener('click', () => showTab(t));
    arrowTabs(document.querySelector('.gf-top > .gf-tabs'), () => TABS.map(t => $(`gf-tab-${t}`)), () => $(`gf-tab-${currentTab()}`), b => showTab(b.id.replace('gf-tab-', '')));

    $('gf-chats-toggle').addEventListener('click', () => showChatsDrawer(!$('gf-cols').classList.contains('gf-chats-open')));
    $('gf-chats-close').addEventListener('click', () => showChatsDrawer(false));
    $('gf-media-close').addEventListener('click', () => showMediaPanel(false));
    $('gf-media-toggle').addEventListener('click', () => showMediaPanel($('gf-cols').classList.contains('gf-media-closed')));
    showMediaPanel($('gf-app').clientWidth >= 1000);
    /* a window that shrinks to phone width closes the drawers (they would cover the conversation) */
    let wasNarrow = isNarrow();
    window.addEventListener('resize', () => {
      const narrow = isNarrow();
      if (narrow && !wasNarrow) { showChatsDrawer(false); showMediaPanel(false); }
      wasNarrow = narrow;
    });
    $('gf-new-chat').addEventListener('click', () => { startNewChat(); showChatsDrawer(false); $('gf-input').focus(); });
    $('gf-refresh-chats').addEventListener('click', loadChats);
    $('gf-reload').addEventListener('click', () => state.chat.id && openChat(state.chat.id));

    $('gf-send').addEventListener('click', send);
    $('gf-input').addEventListener('input', autoGrow);
    $('gf-input').addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); }
    });
    $('gf-attach').addEventListener('click', () => showMenu(menu.hidden));
    menu.addEventListener('click', e => { const b = e.target.closest('[data-attach]'); if (b) onMenu(b.dataset.attach); });
    menu.addEventListener('keydown', e => {
      const items = [...menu.querySelectorAll('button')];
      const i = items.indexOf(document.activeElement);
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); items[(i + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length].focus(); }
      if (e.key === 'Escape') { e.stopPropagation(); showMenu(false); $('gf-attach').focus(); }
    });
    document.addEventListener('click', e => { if (!menu.hidden && !e.target.closest('.gf-attach-wrap')) showMenu(false); });
    $('gf-upload').addEventListener('change', e => { uploadImages([...e.target.files]); e.target.value = ''; });

    /* Drop images onto the conversation, or paste them into the page, to attach them */
    const convo = $('gf-convo');
    let dragDepth = 0;
    const hasFiles = e => e.dataTransfer && [...e.dataTransfer.types].includes('Files');
    convo.addEventListener('dragenter', e => { if (!hasFiles(e)) return; e.preventDefault(); dragDepth++; $('gf-drop').hidden = false; });
    convo.addEventListener('dragover', e => { if (hasFiles(e)) e.preventDefault(); });
    convo.addEventListener('dragleave', () => { dragDepth = Math.max(0, dragDepth - 1); if (!dragDepth) $('gf-drop').hidden = true; });
    convo.addEventListener('drop', e => {
      if (!hasFiles(e)) return;
      e.preventDefault();
      dragDepth = 0;
      $('gf-drop').hidden = true;
      uploadImages([...e.dataTransfer.files]);
    });
    document.addEventListener('paste', e => {
      if (currentTab() !== 'chat' || picker.open || lightbox.open) return;
      const files = [...(e.clipboardData ? e.clipboardData.files : [])].filter(f => f.type.startsWith('image/'));
      if (!files.length) return;
      e.preventDefault();
      uploadImages(files);
    });

    for (const b of pickTabs()) b.addEventListener('click', () => showPick(b.dataset.pick));
    arrowTabs(picker.querySelector('.gf-tabs'), pickTabs, () => pickTabs().find(b => b.dataset.pick === state.pick), b => showPick(b.dataset.pick));
    $('gf-picker-close').addEventListener('click', () => picker.close());
    picker.addEventListener('click', e => { if (e.target === picker) picker.close(); });

    $('gf-lb-close').addEventListener('click', () => lightbox.close());
    $('gf-lb-prev').addEventListener('click', () => stepLightbox(-1));
    $('gf-lb-next').addEventListener('click', () => stepLightbox(1));
    $('gf-lb-download').addEventListener('click', e => downloadMedia(lb.list[lb.index], e.currentTarget, $('gf-lb-msg')));
    $('gf-lb-use').addEventListener('click', () => { if (useMedia(lb.list[lb.index])) lightbox.close(); });
    lightbox.addEventListener('keydown', e => {
      if (e.key === 'ArrowLeft') { e.preventDefault(); stepLightbox(-1); }
      if (e.key === 'ArrowRight') { e.preventDefault(); stepLightbox(1); }
    });
    lightbox.addEventListener('close', () => { $('gf-lb-stage').textContent = ''; });

    $('gf-l-refresh').addEventListener('click', () => loadLibrary(true));
    $('gf-l-project').addEventListener('change', () => loadLibrary(false));
    $('gf-l-type').addEventListener('change', () => { state.libraryShown = LIBRARY_PAGE; loadLibrary(false); });
    $('gf-l-uploads').addEventListener('change', () => { state.libraryShown = LIBRARY_PAGE; loadLibrary(false); });
    $('gf-l-more').addEventListener('click', () => { state.libraryShown += LIBRARY_PAGE; loadLibrary(false); });
    $('gf-l-upload').addEventListener('change', e => { uploadToLibrary([...e.target.files]); e.target.value = ''; });

    $('gf-s-refresh').addEventListener('click', loadSettings);
    $('gf-s-save').addEventListener('click', saveSettings);

    /* Escape closes the phone drawers */
    document.addEventListener('keydown', e => {
      if (e.key !== 'Escape' || !isNarrow() || e.defaultPrevented) return;
      showChatsDrawer(false);
      showMediaPanel(false);
    });
    /* Back on the page: read the chat list again (at most every 30 s), and reopen a paused stream */
    const onReturn = () => {
      if (document.visibilityState !== 'visible' || !state.email) return;
      if (Date.now() - state.chatsAt > 30000) loadChats();
      if (state.chat.id && state.chat.status === 'running') ensureStream();
    };
    document.addEventListener('visibilitychange', onReturn);
    window.addEventListener('focus', onReturn);
    setInterval(renderListAge, 30000);

    initSplitters();
    startNewChat();
    if ($('gf-token').value) connect();
  };
  init();
})();
