/*
  Google Flow Agent API demo: building the page's pieces. Pure DOM helpers with no API calls: elements, Markdown, the agent's
  steps (thinking and tool calls), media previews, result figures and media cards.

  Safety: text from the API is always set with textContent, never innerHTML. Markdown is built as DOM nodes, and only http and
  https links become links.
*/
(() => {
  const FD = window.FlowDemo = window.FlowDemo || {};

  /* Build an element: props are attributes ("text" is textContent, "on…" are listeners), children are nodes or plain strings. */
  const el = (tag, props, children) => {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(props || {})) {
      if (value === undefined || value === null || value === false) continue;
      if (key === 'text') node.textContent = value;
      else if (key === 'class') node.className = value;
      else if (key === 'value') node.value = value;
      else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
      else node.setAttribute(key, value === true ? '' : value);
    }
    for (const child of [].concat(children === undefined ? [] : children)) if (child !== null && child !== undefined && child !== false) node.append(child);
    return node;
  };

  /* Account emails are shown masked ("ada…ace@gmail.com"). The real email stays in the picker's value and in every API call. */
  const maskEmail = email => {
    const at = email.lastIndexOf('@');
    const name = at > 0 ? email.slice(0, at) : email;
    const masked = name.length <= 6 ? `${name[0] || ''}…` : `${name.slice(0, 3)}…${name.slice(-3)}`;
    return at > 0 ? masked + email.slice(at) : masked;
  };
  const fmtClock = ms => new Date(ms).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  /* Compact date for lists: the time today, "Oct 11" this year, "Oct 11, 2025" before. */
  const fmtShort = iso => {
    if (!iso) return '';
    const d = new Date(iso);
    const now = new Date();
    if (d.toDateString() === now.toDateString()) return fmtClock(d);
    return d.toLocaleDateString([], d.getFullYear() === now.getFullYear() ? { month: 'short', day: 'numeric' } : { month: 'short', day: 'numeric', year: 'numeric' });
  };
  const STATUS_LABELS = { idle: 'Done', running: 'Working', waiting_approval: 'Waiting for approval', failed: 'Failed', queued: 'Queued', pending: 'In progress', completed: 'Done', success: 'Done', error: 'Failed' };
  const statusLabel = s => STATUS_LABELS[s] || String(s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

  /* **bold**, *italic*, `code` and [links](https://…) inside one line */
  const inlineMarkdown = (node, text) => {
    const re = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\(https?:[^)\s]+\)|(?<![\w*])\*[^*\n]+\*(?![\w*]))/g;
    let at = 0;
    let m;
    while ((m = re.exec(text))) {
      node.append(text.slice(at, m.index));
      const t = m[0];
      if (t.startsWith('**')) node.append(el('strong', { text: t.slice(2, -2) }));
      else if (t.startsWith('`')) node.append(el('code', { text: t.slice(1, -1) }));
      else if (t.startsWith('[')) {
        const link = /^\[([^\]]+)\]\((.+)\)$/.exec(t);
        node.append(el('a', { href: link[2], text: link[1], target: '_blank', rel: 'noopener noreferrer' }));
      } else node.append(el('em', { text: t.slice(1, -1) }));
      at = m.index + t.length;
    }
    node.append(text.slice(at));
    return node;
  };
  /* A small Markdown subset (paragraphs, headings, lists, code blocks, inline marks) built as DOM nodes. */
  const renderMarkdown = (box, text) => {
    box.textContent = '';
    let list = null;
    let para = null;
    let code = null;
    for (const line of String(text).split('\n')) {
      if (line.trim().startsWith('```')) {
        if (code) code = null;
        else {
          list = null;
          para = null;
          code = el('code');
          box.append(el('pre', {}, code));
        }
        continue;
      }
      if (code) { code.append(line + '\n'); continue; }
      if (!line.trim()) { list = null; para = null; continue; }
      const heading = /^#{1,6}\s+(.*)$/.exec(line);
      const item = /^\s*(?:[-*•]|\d+[.)])\s+(.*)$/.exec(line);
      if (heading) {
        list = null;
        para = null;
        box.append(inlineMarkdown(el('div', { class: 'gf-h' }), heading[1]));
      } else if (item) {
        para = null;
        if (!list) { list = el(/^\s*\d/.test(line) ? 'ol' : 'ul'); box.append(list); }
        list.append(inlineMarkdown(el('li'), item[1]));
      } else {
        list = null;
        if (para) para.append(el('br'));
        else { para = el('p'); box.append(para); }
        inlineMarkdown(para, line);
      }
    }
    return box;
  };

  /* "10 credits for 1 video" from an approval {cost, images, videos} */
  const approvalSummary = a => {
    const parts = [];
    if (a.images) parts.push(plural(a.images, 'image'));
    if (a.videos) parts.push(plural(a.videos, 'video'));
    const cost = typeof a.cost === 'number' ? plural(a.cost, 'credit') : 'credits';
    return `${cost}${parts.length ? ` for ${parts.join(' and ')}` : ''}`;
  };

  /* One step inside the collapsed "Steps" of an answer: the agent's thinking, a tool call or a tool result. */
  const argsSummary = args => {
    if (!args || typeof args !== 'object') return '';
    if (typeof args.prompt === 'string') return `"${args.prompt.length > 90 ? `${args.prompt.slice(0, 90)}…` : args.prompt}"`;
    return Object.entries(args).filter(([k, v]) => !k.startsWith('_') && ['string', 'number', 'boolean'].includes(typeof v))
      .slice(0, 4).map(([k, v]) => `${k}: ${String(v).slice(0, 40)}`).join(', ');
  };
  const renderStep = item => {
    if (item.kind === 'thinking') {
      const title = (/\*\*([^*]+)\*\*/.exec(item.text) || [])[1];
      const box = el('div', { class: 'gf-step' }, title ? el('div', { class: 'gf-step-title', text: title }) : null);
      box.append(renderMarkdown(el('div', { class: 'gf-text' }), item.text.replace(/^\s*\*\*[^*]+\*\*\s*/, '')));
      return box;
    }
    const call = item.kind === 'tool_call';
    const data = call ? item.args : item.result;
    const r = data || {};
    const failed = !call && (r.status === 'error' || !!r.error_code);
    const detail = call
      ? item.tool === 'ask_for_permission' ? approvalSummary({ cost: r.total_cost, images: r.num_images, videos: r.num_videos }) : argsSummary(r)
      : [r.status, r.error_code, r.display_name].filter(Boolean).join(' · ');
    return el('details', { class: `gf-step${failed ? ' gf-step-failed' : ''}` }, [
      el('summary', {}, [el('span', { class: 'gf-step-tool', text: `${call ? '→' : '←'} ${item.tool}` }), detail ? ` ${detail}` : '']),
      el('pre', { text: JSON.stringify(data, null, 2) }),
    ]);
  };

  /* A preview: an image, a video's first frame with a play mark, or a waiting / failed box. A click calls onOpen. A link that no
     longer loads (expired after ~6 h) calls onBroken once, so the page can fetch a fresh one. */
  const isDone = s => s === 'completed' || s === 'success';
  const isFailed = s => s === 'failed' || s === 'error';
  const preview = (media, { onOpen, onBroken } = {}) => {
    if (isFailed(media.status))
      return el('div', { class: 'gf-preview gf-preview-failed', text: media.error || (media.failureReasons || []).join(', ') || 'This one failed' });
    if (!media.url)
      return el('div', { class: 'gf-preview gf-preview-wait gf-loading' }, [el('span', { class: 'gf-spinner' }), el('span', { text: `${media.type === 'video' ? 'Video' : 'Image'} ${isDone(media.status) ? 'loading' : statusLabel(media.status || 'pending').toLowerCase()}…` })]);
    const label = `Open ${media.type === 'video' ? 'the video' : 'the image'} ${media.displayName || ''}`.trim();
    const broken = () => { if (onBroken) onBroken(media); };
    const inner = media.type === 'video'
      ? [el('video', { src: `${media.url}#t=0.1`, preload: 'metadata', muted: true, playsinline: true, onerror: broken }), el('span', { class: 'gf-play', 'aria-hidden': 'true' })]
      : [el('img', { src: media.url, alt: media.displayName || 'Generated image', loading: 'lazy', onerror: broken })];
    return el('button', { type: 'button', class: 'gf-preview', 'aria-label': label, title: 'Open', onclick: () => onOpen && onOpen(media) }, inner);
  };

  /* A result inside the conversation: the preview, its name and status, Download and Use in next message. */
  const resultFigure = (media, actions) => {
    const msg = el('span', { class: 'gf-item-msg', role: 'status' });
    const status = isDone(media.status) ? '' : el('span', { class: `gf-pill gf-pill-${isFailed(media.status) ? 'failed' : media.status || 'pending'}`, text: statusLabel(media.status || 'pending') });
    return el('figure', { class: 'gf-figure', 'data-media': media.mediaId }, [
      preview(media, actions),
      el('figcaption', { class: 'gf-figcap' }, [
        el('span', { text: media.displayName || (media.type === 'video' ? 'Video' : 'Image'), title: media.displayName || '' }),
        status,
      ]),
      isDone(media.status) && media.referenceId ? el('div', { class: 'gf-actions' }, [
        el('button', { type: 'button', class: 'gf-btn gf-btn-sm', text: 'Download', onclick: ev => actions.onDownload(media, ev.currentTarget, msg) }),
        el('button', { type: 'button', class: 'gf-btn gf-btn-sm', text: 'Use in next message', title: 'Attach it to your next message', onclick: () => actions.onUse(media) }),
      ]) : null,
      msg,
    ]);
  };

  /* A media card for the chat's media panel and the Library: preview, name, details, the referenceId with Copy, and actions. */
  const mediaCard = (media, actions, extra) => {
    const msg = el('div', { class: 'gf-item-msg', role: 'status' });
    const meta = [media.type, media.durationSec && `${media.durationSec} s`, media.turn && `turn ${media.turn}`, media.likelyUpload && 'upload', media.createTime && fmtShort(media.createTime), media.model].filter(Boolean).join(' · ');
    const done = isDone(media.status);
    return el('div', { class: 'gf-file', role: 'listitem', 'data-media': media.mediaId || media.referenceId }, [
      preview(media, actions),
      media.displayName ? el('div', { class: 'gf-file-name', title: media.displayName, text: media.displayName }) : null,
      el('div', { class: 'gf-file-meta' }, [
        done ? null : el('span', { class: `gf-pill gf-pill-${isFailed(media.status) ? 'failed' : media.status || 'pending'}`, text: statusLabel(media.status || 'pending') }),
        done ? meta : ` ${meta}`,
      ]),
      media.referenceId ? el('div', { class: 'gf-ref' }, [
        el('code', { title: media.referenceId, text: media.referenceId }),
        el('button', { type: 'button', class: 'gf-btn gf-btn-sm', text: 'Copy id', title: 'Copy the referenceId: it works in /images, /videos and the next message', onclick: () => actions.onCopy(media.referenceId, msg) }),
      ]) : null,
      el('div', { class: 'gf-actions' }, [
        done && media.referenceId ? el('button', { type: 'button', class: 'gf-btn gf-btn-sm', text: 'Download', onclick: ev => actions.onDownload(media, ev.currentTarget, msg) }) : null,
        done && media.referenceId ? el('button', { type: 'button', class: 'gf-btn gf-btn-sm', text: 'Use in next message', onclick: () => actions.onUse(media) }) : null,
      ].concat(extra ? extra(msg) : [])),
      msg,
    ]);
  };

  /* --- The new-chat screen's starter cards. Flow's agent shows 3 of these 14 labels at random under "Hi <name> / What would
     you like to create?", and a click sends the label as the first message. Each card gets a small drawing of our own:
     a hue and its shapes, every shape [svg tag, attributes] in a 72x52 box, stroked in the card's color ('f' = filled). --- */
  const STARTERS = [
    ['Brainstorm with me', 45, [['circle', { cx: 36, cy: 22, r: 10 }], ['path', { d: 'M31 33h10M32 38h8M36 4v3M20 10l2 2M52 10l-2 2M16 22h3M53 22h3' }]]],
    ['Turn a concept into prompts', 210, [['path', { d: 'M12 16h22M12 24h28M12 32h16M12 40h24' }], ['path', { d: 'M54 14l2 6 6 2-6 2-2 6-2-6-6-2 6-2z', class: 'f' }]]],
    ['Develop a storyboard', 260, [['rect', { x: 6, y: 12, width: 17, height: 13, rx: 2 }], ['rect', { x: 27.5, y: 12, width: 17, height: 13, rx: 2 }], ['rect', { x: 49, y: 12, width: 17, height: 13, rx: 2 }], ['path', { d: 'M6 32h17M6 37h11M27.5 32h17M27.5 37h11M49 32h17M49 37h11' }]]],
    ['Build a visual moodboard', 330, [['rect', { x: 10, y: 6, width: 24, height: 20, rx: 3, class: 'f' }], ['rect', { x: 38, y: 6, width: 24, height: 12, rx: 3 }], ['rect', { x: 38, y: 22, width: 24, height: 24, rx: 3 }], ['rect', { x: 10, y: 30, width: 24, height: 16, rx: 3 }]]],
    ['Generate concept art', 20, [['rect', { x: 10, y: 6, width: 52, height: 40, rx: 4 }], ['path', { d: 'M12 42l13-15 9 10 7-7 19 12' }], ['circle', { cx: 49, cy: 17, r: 5, class: 'f' }]]],
    ['Edit an image', 180, [['rect', { x: 8, y: 8, width: 40, height: 32, rx: 4 }], ['path', { d: 'M10 36l10-11 7 8 6-5 13 9' }], ['path', { d: 'M44 44l15-15 5 5-15 15-6 1z', class: 'f' }]]],
    ['Create a few versions of an image', 290, [['rect', { x: 24, y: 4, width: 36, height: 26, rx: 4 }], ['rect', { x: 18, y: 11, width: 36, height: 26, rx: 4 }], ['rect', { x: 12, y: 18, width: 36, height: 26, rx: 4, class: 'f' }]]],
    ['Edit a video with Omni', 0, [['rect', { x: 8, y: 10, width: 44, height: 32, rx: 4 }], ['path', { d: 'M14 10v32M46 10v32' }], ['path', { d: 'M26 19l10 7-10 7z', class: 'f' }], ['path', { d: 'M58 12l2 5 5 2-5 2-2 5-2-5-5-2 5-2z', class: 'f' }]]],
    ['How do I get started?', 140, [['path', { d: 'M24 46V8' }], ['path', { d: 'M24 10h24l-6 8 6 8H24', class: 'f' }], ['path', { d: 'M16 46h16' }]]],
    ['Rename my assets', 95, [['path', { d: 'M10 16h28l12 10-12 10H10z' }], ['circle', { cx: 17, cy: 26, r: 3, class: 'f' }], ['path', { d: 'M60 12v28M56 12h8M56 40h8' }]]],
    ['Organize my grid into collections', 230, [['rect', { x: 6, y: 12, width: 10, height: 10, rx: 2 }], ['rect', { x: 19, y: 12, width: 10, height: 10, rx: 2 }], ['rect', { x: 6, y: 25, width: 10, height: 10, rx: 2 }], ['rect', { x: 19, y: 25, width: 10, height: 10, rx: 2 }], ['path', { d: 'M33 24h7M37 21l3 3-3 3' }], ['path', { d: 'M44 15h8l3 4h11v20H44z', class: 'f' }]]],
    ['Teach me about what you can do', 50, [['path', { d: 'M10 10h42v24H26l-9 8v-8h-7z' }], ['path', { d: 'M18 19h26M18 26h16' }], ['path', { d: 'M60 30l2 5 5 2-5 2-2 5-2-5-5-2 5-2z', class: 'f' }]]],
    ['Show me the keyboard shortcuts', 200, [['rect', { x: 6, y: 12, width: 60, height: 30, rx: 5 }], ['path', { d: 'M13 20h4M22 20h4M31 20h4M40 20h4M49 20h4M58 20h1M13 27h4M22 27h4M31 27h4M40 27h4M49 27h4M22 34h28' }]]],
    ['Learn about generation costs', 35, [['ellipse', { cx: 30, cy: 38, rx: 16, ry: 5 }], ['path', { d: 'M14 26v12M46 26v12' }], ['ellipse', { cx: 30, cy: 32, rx: 16, ry: 5 }], ['ellipse', { cx: 30, cy: 26, rx: 16, ry: 5, class: 'f' }], ['path', { d: 'M58 8l2 5 5 2-5 2-2 5-2-5-5-2 5-2z', class: 'f' }]]],
  ].map(([label, hue, shapes]) => ({ label, hue, shapes }));
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const starterArt = s => {
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 72 52');
    svg.setAttribute('class', 'gf-starter-art');
    svg.setAttribute('aria-hidden', 'true');
    svg.style.setProperty('--h', String(s.hue));
    for (const [tag, attrs] of s.shapes) {
      const node = document.createElementNS(SVG_NS, tag);
      for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, String(v));
      svg.append(node);
    }
    return svg;
  };
  /* count labels at random (a new pick for every new chat): a Fisher-Yates shuffle */
  const pickStarters = count => {
    const pool = STARTERS.slice();
    for (let i = pool.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [pool[i], pool[j]] = [pool[j], pool[i]];
    }
    return pool.slice(0, count);
  };
  const starterCard = (s, onPick) => el('button', { type: 'button', class: 'gf-starter', onclick: () => onPick(s.label) }, [starterArt(s), el('span', { text: s.label })]);

  FD.render = { pickStarters, starterCard, el, maskEmail, fmtClock, fmtShort, statusLabel, plural, renderMarkdown, approvalSummary, renderStep, preview, resultFigure, mediaCard, isDone, isFailed };
})();
