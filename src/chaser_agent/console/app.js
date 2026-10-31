// The console reads the bearer token from its URL fragment, keeps it for this tab only and
// removes it from the address bar. Everything it shows comes from the session's event log.
(() => {
  const $ = (id) => document.getElementById(id);
  const TOKEN_KEY = 'chaser-agent-token';
  const TONE = { reasoning: 'live', running_tool: 'live', queued: 'live', awaiting_human: 'human', awaiting_approval: 'human', finished: 'done', failed: 'blocked', budget_stopped: 'blocked' };
  const STATUS_TEXT = {
    queued: 'Starting', reasoning: 'Thinking', running_tool: 'Working', awaiting_human: 'Waiting for your answer',
    awaiting_approval: 'Waiting for your approval', finished: 'Finished', failed: 'Stopped', cancelled: 'Cancelled',
    budget_stopped: 'Used its budget', interrupted: 'Interrupted',
  };
  const ACTIVE = new Set(['queued', 'reasoning', 'running_tool']);
  const TOOL_TEXT = {
    graph_search: 'Searched the knowledge graph', graph_node: 'Read a graph record', graph_source_segments: 'Read a source from the graph',
    library_search: 'Searched the library', read_document: 'Read a document', web_fetch: 'Read a public page',
    workspace_write: 'Saved a working file', workspace_read: 'Opened a working file', workspace_list: 'Listed working files',
    recall_output: 'Re-read an earlier result', update_plan: 'Updated the plan', memory_search: 'Checked reviewed memory', memory_propose: 'Proposed a memory',
    mail_accounts: 'Checked mail identities', mail_outbox: 'Checked the outbox', mail_search: 'Searched mail', mail_read: 'Read an email', mail_create_draft: 'Prepared a mail draft (not sent)',
    graph_record: 'Recorded this in the knowledge graph',
  };

  const suggestionBox = $('suggestions');
  let token = '';
  let current = null;
  let seen = 0;
  let lastMotion = '';
  let openSteps = new Map();
  let polling = false;

  function readToken() {
    const match = location.hash.match(/token=([0-9a-f]{64})/);
    if (match) {
      try { sessionStorage.setItem(TOKEN_KEY, match[1]); } catch (_) { /* Private mode keeps it in memory only. */ }
      history.replaceState(null, '', location.pathname);
      return match[1];
    }
    try { return sessionStorage.getItem(TOKEN_KEY) || ''; } catch (_) { return ''; }
  }

  async function api(path, body) {
    const options = { headers: { Authorization: `Bearer ${token}` } };
    if (body !== undefined) {
      options.method = 'POST';
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
    const response = await fetch(path, options);
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error((detail.error && detail.error.message) || `Request failed (${response.status})`);
    }
    return response.json();
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function setMotion(name, tone, label) {
    const box = $('companion');
    box.dataset.tone = tone || '';
    $('state-text').textContent = label;
    if (name === lastMotion) return;
    lastMotion = name;
    const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const video = $('motion');
    const image = $('motion-still');
    video.hidden = still;
    image.hidden = !still;
    image.src = `/assets/motion/${name}.png`;
    if (!still) {
      video.poster = `/assets/motion/${name}.png`;
      video.src = `/assets/motion/${name}.mp4`;
      video.play().catch(() => {});
    }
  }

  function scrollDown() {
    const box = $('timeline');
    if (box.scrollHeight - box.scrollTop - box.clientHeight < 240) box.scrollTop = box.scrollHeight;
  }

  function summarise(args) {
    if (!args) return '';
    const value = args.query || args.q || args.url || args.reference || args.path || args.name || args.title || args.subject || args.source || '';
    return typeof value === 'string' ? value : '';
  }

  function toggleOutput(button, callId) {
    const next = button.nextElementSibling;
    if (next && next.classList.contains('output')) { next.remove(); return; }
    const box = el('pre', 'output', 'Loading…');
    button.after(box);
    api(`/v1/agent/sessions/${current}/outputs/${callId}`).then((value) => {
      box.textContent = value.text + (value.total_chars > value.text.length ? `\n…${value.total_chars - value.text.length} more characters` : '');
    }).catch((error) => { box.textContent = error.message; });
  }

  function addStep(data) {
    const button = el('button', 'step running');
    button.type = 'button';
    button.append(el('span', 'glyph', '›'));
    const what = el('span', 'what');
    what.append(el('b', '', TOOL_TEXT[data.tool] || data.tool));
    const detail = summarise(data.args);
    if (detail) what.append(document.createTextNode(`  ${detail}`));
    button.append(what, el('small', '', ''));
    button.addEventListener('click', () => toggleOutput(button, data.call_id));
    $('timeline').append(button);
    openSteps.set(data.call_id, button);
  }

  function finishStep(data) {
    const button = openSteps.get(data.call_id);
    if (!button) return;
    button.classList.remove('running');
    const ok = data.status === 'ok';
    if (!ok) button.classList.add(data.status === 'denied' ? 'denied' : 'failed');
    button.querySelector('.glyph').textContent = ok ? '✓' : '×';
    button.querySelector('small').textContent = data.seconds ? `${data.seconds.toFixed(1)}s` : '';
    if (data.injection_signals && data.injection_signals.length) {
      button.after(el('div', 'flag', 'This source tried to give me instructions. I treated it as data and did not follow them.'));
    }
  }

  function renderEvent(event) {
    const data = event.data;
    const line = $('timeline');
    switch (event.type) {
      case 'session_created':
      case 'message':
        line.append(el('div', 'operator', data.goal || data.text));
        break;
      case 'reasoner_reply':
        line.append(el('p', 'thought', data.thought));
        break;
      case 'tool_started':
        addStep(data);
        break;
      case 'tool_finished':
        finishStep(data);
        break;
      case 'tool_denied': {
        const row = el('div', 'flag', `Refused: ${TOOL_TEXT[data.tool] || data.tool}. ${data.message}`);
        line.append(row);
        break;
      }
      case 'reply_rejected':
        line.append(el('div', 'flag', `A reply outside the rules was refused (${data.reason}). Nothing ran.`));
        break;
      case 'question_answered':
        line.append(el('div', 'operator', data.text));
        break;
      case 'approval_decided':
        line.append(el('p', 'muted', data.decision === 'approve' ? 'You approved that exact request.' : 'You rejected that request.'));
        break;
      case 'turn_finished':
        if (data.answer) line.append(el('div', 'answer', data.answer));
        else if (data.error) line.append(el('div', 'answer failed', data.error));
        break;
      default:
        break;
    }
    scrollDown();
  }

  function renderPending(session) {
    const existing = document.querySelector('.card');
    const pending = session.pending;
    if (existing && (!pending || existing.dataset.id !== pending.id)) existing.remove();
    if (!pending || document.querySelector(`.card[data-id="${pending.id}"]`)) return;
    const card = el('div', 'card');
    card.dataset.id = pending.id;
    if (pending.kind === 'question') {
      card.append(el('h3', '', 'I need something from you'), el('p', '', pending.question));
      const row = el('div', 'row');
      for (const option of pending.options || []) {
        const choice = el('button', 'quiet', option);
        choice.type = 'button';
        choice.addEventListener('click', () => answer(pending.id, option));
        row.append(choice);
      }
      const box = el('textarea');
      box.rows = 2;
      box.placeholder = 'Your answer';
      const send = el('button', 'primary', 'Answer');
      send.type = 'button';
      send.addEventListener('click', () => box.value.trim() && answer(pending.id, box.value.trim()));
      card.append(row, box, send);
    } else {
      card.append(el('h3', '', 'Approve this exact action?'), el('p', '', TOOL_TEXT[pending.tool] || pending.tool));
      if (pending.args.title) card.append(el('strong', '', pending.args.title));
      if (pending.args.text) card.append(el('p', 'summary-text', pending.args.text));
      const exact = el('details');
      exact.append(el('summary', '', 'See the exact request'), el('pre', '', JSON.stringify(pending.args, null, 2)));
      card.append(exact);
      const row = el('div', 'row');
      const approve = el('button', 'primary', 'Approve');
      const reject = el('button', 'quiet', 'Reject');
      approve.type = reject.type = 'button';
      approve.addEventListener('click', () => decide(pending, 'approve'));
      reject.addEventListener('click', () => decide(pending, 'reject'));
      row.append(approve, reject);
      card.append(row);
    }
    $('timeline').append(card);
    scrollDown();
  }

  function renderMeters(session) {
    const meters = $('meters');
    meters.replaceChildren();
    const add = (label, value, warn) => {
      const item = el('span', warn ? 'warn' : '');
      item.append(el('b', '', String(value)), document.createTextNode(` ${label}`));
      meters.append(item);
    };
    add('steps', session.steps_total);
    add('tool calls', Object.values(session.tool_counts).reduce((sum, count) => sum + count, 0));
    if (session.denied_calls) add('refused', session.denied_calls, true);
    if (session.tool_failures) add('failed', session.tool_failures, true);
  }

  function renderPlan(session) {
    $('plan-box').hidden = !session.plan.length;
    $('plan').replaceChildren(...session.plan.map((step) => el('li', step.status, step.text)));
  }

  async function renderArtifacts() {
    const { artifacts } = await api(`/v1/agent/sessions/${current}/artifacts`);
    const box = $('artifacts');
    if (!artifacts.length) { box.replaceChildren(el('p', 'muted', 'Nothing yet.')); return; }
    const rank = (row) => (/brief\.html$/.test(row.name) ? 0 : /\.html$/.test(row.name) ? 1 : 2);
    const rows = [...artifacts].sort((a, b) => rank(a) - rank(b));
    box.replaceChildren(...rows.slice(0, 40).map((row) => {
      const button = el('button', `artifact${rank(row) === 0 ? ' lead' : ''}`);
      button.type = 'button';
      button.append(el('b', '', row.name), el('small', '', `${Math.max(1, Math.round(row.bytes / 1024))} KB · ${row.sha256.slice(0, 10)}`));
      button.addEventListener('click', () => openArtifact(row.name));
      return button;
    }));
  }

  async function openArtifact(name) {
    const response = await fetch(`/v1/agent/sessions/${current}/artifacts/${name}`, { headers: { Authorization: `Bearer ${token}` } });
    if (!response.ok) { $('notice').textContent = 'That file could not be opened.'; return; }
    $('viewer-title').textContent = name;
    const frame = $('viewer-frame');
    const text = $('viewer-text');
    if (name.endsWith('.html')) {
      frame.src = URL.createObjectURL(await response.blob());
      frame.hidden = false;
      text.hidden = true;
    } else {
      text.textContent = await response.text();
      text.hidden = false;
      frame.hidden = true;
    }
    $('viewer').showModal();
  }

  function renderGrants(session) {
    $('grants').replaceChildren(...session.grants.map((id) => el('span', `chip${/write|draft|record|propose|retain|open_case|assess|build/.test(id) ? ' write' : ''}`, id)));
  }

  async function refreshSession() {
    if (!current) return;
    const session = await api(`/v1/agent/sessions/${current}`);
    const page = await api(`/v1/agent/sessions/${current}/events?after=${seen}`);
    for (const event of page.events) { seen = event.seq; renderEvent(event); }
    $('run-head').hidden = false;
    $('run-workflow').textContent = `${session.workflow_title} · ${session.reasoner}`;
    $('run-goal').textContent = session.goal;
    setMotion(session.motion, TONE[session.status], STATUS_TEXT[session.status] || session.status);
    renderPending(session);
    renderMeters(session);
    renderPlan(session);
    renderGrants(session);
    $('stop').hidden = !(ACTIVE.has(session.status) || session.pending);
    $('input').placeholder = session.pending ? 'Answer in the card above' : 'Tell Chaser what to do next';
    if (page.events.length) renderArtifacts().catch(() => {});
  }

  async function refreshSide() {
    const status = await api('/v1/agent/status');
    const routes = (status.reasoners.routes || []).map((route) => {
      const row = el('div', `route${route.available ? ' on' : ''}`);
      row.append(el('i'), el('span', '', route.label));
      if (route.reason) row.append(el('small', '', route.reason));
      return row;
    });
    $('routes').replaceChildren(...(routes.length ? routes : [el('p', 'muted', 'Checking…')]));
    const { sessions } = await api('/v1/agent/sessions');
    $('sessions').replaceChildren(...sessions.slice(0, 12).map((row) => {
      const button = el('button', `session${row.id === current ? ' on' : ''}`);
      button.type = 'button';
      button.dataset.id = row.id;
      button.append(el('b', '', row.title), el('small', '', STATUS_TEXT[row.status] || row.status));
      button.addEventListener('click', () => select(row.id));
      return button;
    }));
    if (!current) setMotion(status.motion, '', 'Ready');
    // Held directly: the empty state, and this box with it, leaves the page while a session is open.
    const box = suggestionBox;
    if (!box.childElementCount) {
      for (const example of status.examples || []) {
        const button = el('button', 'suggestion', example);
        button.type = 'button';
        button.addEventListener('click', () => { $('input').value = example; $('input').focus(); });
        box.append(button);
      }
    }
    return status;
  }

  function select(id) {
    current = id;
    seen = 0;
    openSteps = new Map();
    document.querySelectorAll('#timeline > *').forEach((node) => node.remove());
    $('shell').classList.toggle('no-tray', !id);
    $('tray').hidden = !id;
    if (!id) {
      $('timeline').append(emptyState);
      $('run-head').hidden = true;
      lastMotion = '';
      $('stop').hidden = true;
      $('input').placeholder = 'Tell Chaser what to do';
    }
    refreshSession().catch(report);
    refreshSide().catch(report);
  }

  function report(error) { $('notice').textContent = error.message; }

  async function answer(questionId, text) {
    try { await api(`/v1/agent/sessions/${current}/answers`, { question_id: questionId, answer: text }); await refreshSession(); } catch (error) { report(error); }
  }

  async function decide(pending, decision) {
    try { await api(`/v1/agent/sessions/${current}/approvals`, { approval_id: pending.id, digest: pending.digest, decision }); await refreshSession(); } catch (error) { report(error); }
  }

  async function send() {
    const box = $('input');
    const text = box.value.trim();
    if (!text) return;
    $('notice').textContent = '';
    try {
      if (current) {
        const session = await api(`/v1/agent/sessions/${current}`);
        if (ACTIVE.has(session.status) || session.pending) { $('notice').textContent = 'Chaser is mid-task. Answer the card or press Stop first.'; return; }
        await api(`/v1/agent/sessions/${current}/messages`, { message: text });
      } else {
        const session = await api('/v1/agent/sessions', { message: text });
        select(session.id);
      }
      box.value = '';
      box.style.height = '';
    } catch (error) { report(error); }
  }

  const emptyState = $('empty');

  async function tick() {
    if (polling || document.hidden) return;
    polling = true;
    try {
      await refreshSession();
      $('notice').textContent = $('notice').textContent.startsWith('Lost') ? '' : $('notice').textContent;
    } catch (error) {
      $('notice').textContent = `Lost contact with the local service: ${error.message}`;
    } finally { polling = false; }
  }

  $('send').addEventListener('click', send);
  $('stop').addEventListener('click', () => current && api(`/v1/agent/sessions/${current}/cancel`, {}).then(refreshSession).catch(report));
  $('new-work').addEventListener('click', () => select(null));
  $('viewer-close').addEventListener('click', () => $('viewer').close());
  $('input').addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); }
  });
  $('input').addEventListener('input', (event) => {
    event.target.style.height = 'auto';
    event.target.style.height = `${event.target.scrollHeight + 2}px`;
  });

  function start() {
    token = readToken();
    $('port').textContent = `Private to this computer · ${location.host}`;
    if (!token) {
      setMotion('blocked', 'blocked', 'Not connected');
      $('notice').textContent = 'Open this page with: chaser-agent open';
      return;
    }
    const video = $('motion');
    video.play().catch(() => {});
    select(null);
    setInterval(tick, 1500);
    setInterval(() => refreshSide().catch(() => {}), 8000);
  }

  start();
})();
