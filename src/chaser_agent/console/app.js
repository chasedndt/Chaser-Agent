// A small always-visible HUD for the agent. It reads the bearer token from its URL fragment,
// keeps it for this tab only and removes it from the address bar. Everything it shows comes
// from the session's event log. See docs/01_Product/Chaser-Agent-HUD.md.
(() => {
  const $ = (id) => document.getElementById(id);
  const TOKEN_KEY = 'chaser-agent-token';
  const COLLAPSED = { width: 420, height: 76 };
  const EXPANDED = { width: 420, height: 600 };
  const VIEWING = { width: 1000, height: 820 };
  const STALE_PLAN_STEPS = 8;
  const CORNER_SLACK = 8;
  const SIZE_SLACK = 4;
  const TONE = {
    queued: 'live', reasoning: 'live', running_tool: 'live', awaiting_human: 'human', awaiting_approval: 'human',
    finished: 'done', failed: 'blocked', budget_stopped: 'blocked', interrupted: 'blocked', cancelled: 'idle',
  };
  const STATUS_TEXT = {
    queued: 'Starting', reasoning: 'Thinking', running_tool: 'Working', awaiting_human: 'Needs your answer',
    awaiting_approval: 'Needs your yes', finished: 'Finished', failed: 'Stopped', cancelled: 'Cancelled',
    budget_stopped: 'Used its budget', interrupted: 'Interrupted',
  };
  const ACTIVE = new Set(['queued', 'reasoning', 'running_tool']);
  const TOOL_TEXT = {
    chaseos_open_loops: 'Checked what\'s waiting on you', graph_search: 'Searched the knowledge graph', graph_node: 'Read a graph record', graph_source_segments: 'Read a source from the graph',
    library_search: 'Searched the library', read_document: 'Read a document', web_fetch: 'Read a public page',
    workspace_write: 'Saved a working file', workspace_read: 'Opened a working file', workspace_list: 'Listed working files',
    recall_output: 'Re-read an earlier result', update_plan: 'Updated the plan', memory_search: 'Checked reviewed memory', memory_propose: 'Proposed a memory',
    mail_accounts: 'Checked mail identities', mail_outbox: 'Checked the outbox', mail_search: 'Searched mail', mail_read: 'Read an email', mail_create_draft: 'Prepared a mail draft, not sent',
    graph_record: 'Recorded this in the knowledge graph',
    procurement_scan_adverts: 'Scanned live adverts for this customer', procurement_read_notice: 'Read an advert', procurement_list_customers: 'Listed the customers',
    procurement_save_customer: 'Saved the customer\'s evidence', procurement_review_history: 'Checked earlier reviews', procurement_record_review: 'Recorded how the review went',
    procurement_open_case: 'Opened a contract review', procurement_retain_document: 'Kept an exact copy of a document',
    procurement_record_requirements: 'Checked requirements word for word', procurement_record_evidence: 'Recorded the customer\'s evidence',
    procurement_assess_fit: 'Compared requirements with evidence', procurement_build_brief: 'Built the contract review',
  };

  // Rows say what happened. A request hasn't happened yet.
  const ASK_TEXT = { graph_record: 'Record this in the knowledge graph', mail_create_draft: 'Prepare this mail draft', memory_propose: 'Propose this memory', procurement_save_customer: 'Save this as the customer\'s evidence', procurement_record_review: 'Record how this review went' };

  const hud = $('hud');
  const suggestionBox = $('suggestions');
  const emptyState = $('empty');
  let token = '';
  let current = null;
  let seen = 0;
  let open = false;
  let lastMotion = '';
  let lastThought = '';
  let lastStatus = '';
  let nowLine = '';
  let steps = new Map();
  let effects = {};
  let sized = '';
  let corner = null;
  let polling = false;
  let firstMessage = null;
  let stepsSincePlan = 0;
  let turnStartedAt = null;
  let startedAt = null;
  let endedAt = null;

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

  function report(error) { $('notice').textContent = error.message; }

  // --- Window size. The pill stays put at the bottom of the screen and the panel opens upward. ---

  function fit(size) {
    const key = `${size.width}x${size.height}`;
    if (key === sized) return;
    if (!window.outerWidth) return;  // A minimized window reports no size. Try again when it's shown.
    sized = key;
    // Already this size, as when first opened. Moving now could undo where the launcher just put it.
    if (Math.abs(window.innerWidth - size.width) <= SIZE_SLACK && Math.abs(window.innerHeight - size.height) <= SIZE_SLACK) return;
    const width = size.width + (window.outerWidth - window.innerWidth);
    const height = size.height + (window.outerHeight - window.innerHeight);
    // Keep the corner where it was. Measuring it afresh each time would creep a few pixels per open,
    // so it only changes when the window is further away than rounding explains: someone moved it.
    const bottom = window.screenY + window.outerHeight;
    const right = window.screenX + window.outerWidth;
    if (!corner || Math.abs(corner.right - right) > CORNER_SLACK || Math.abs(corner.bottom - bottom) > CORNER_SLACK) corner = { right, bottom };
    try {
      window.resizeTo(width, height);
      window.moveTo(Math.max(0, corner.right - width), Math.max(0, corner.bottom - height));
    } catch (_) { /* An ordinary browser tab can't be resized, and the layout still works there. */ }
  }

  function setOpen(value) {
    open = value;
    hud.classList.toggle('open', open);
    $('panel').hidden = !open;
    $('toggle').setAttribute('aria-expanded', String(open));
    $('drawer').hidden = true;
    fit(open ? EXPANDED : COLLAPSED);
    if (open) requestAnimationFrame(() => { const box = $('activity'); box.scrollTop = box.scrollHeight; });
  }

  // --- Character and state. ---

  function setMotion(name) {
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

  function clock(start, end) {
    const seconds = Math.max(0, Math.round(((end ? Date.parse(end) : Date.now()) - Date.parse(start)) / 1000));
    if (Number.isNaN(seconds)) return '';
    const minutes = Math.floor(seconds / 60);
    return minutes >= 60 ? `${Math.floor(minutes / 60)}h ${minutes % 60}m` : `${minutes}:${String(seconds % 60).padStart(2, '0')}`;
  }

  function setNow(text) {
    nowLine = text;
    $('now').textContent = text;
    $('now').title = text;
  }

  // --- Activity. Each row can be opened to see why, what it asked for and what came back. ---

  function summarise(args) {
    if (!args) return '';
    const value = args.query || args.q || args.url || args.reference || args.path || args.document_path || args.name || args.title || args.subject || args.source || '';
    if (typeof value !== 'string') return '';
    return value.replace(/^https:\/\/(www\.)?/, '');
  }

  function tagFor(tool, status) {
    if (status === 'denied') return ['REFUSED', 'refused'];
    if (status && status !== 'ok') return ['FAILED', 'failed'];
    if (/draft/.test(tool)) return ['DRAFT', 'draft'];
    if (!status) return ['RUNNING', 'run'];
    return (effects[tool] || 'read_only') === 'read_only' ? ['READ', 'read'] : ['SAVED', 'save'];
  }

  function setTag(node, tool, status) {
    const [text, kind] = tagFor(tool, status);
    node.className = `tag ${kind}`;
    node.textContent = text;
  }

  function appendRow(node) {
    const box = $('activity');
    const near = box.scrollHeight - box.scrollTop - box.clientHeight < 80;
    box.append(node);
    if (near) box.scrollTop = box.scrollHeight;
  }

  function inspect(row, data, thought) {
    const next = row.nextElementSibling;
    if (next && next.classList.contains('inspect')) {
      next.remove();
      row.setAttribute('aria-expanded', 'false');
      return;
    }
    row.setAttribute('aria-expanded', 'true');
    const box = el('div', 'inspect');
    if (thought) box.append(el('h4', '', 'Why'), el('p', '', thought));
    box.append(el('h4', '', 'What it asked for'), el('pre', '', JSON.stringify(data.args || {}, null, 1)));
    const result = el('pre', '', 'Loading…');
    box.append(el('h4', '', 'What came back'), result);
    row.after(box);
    api(`/v1/agent/sessions/${current}/outputs/${data.call_id}`).then((value) => {
      result.textContent = value.text + (value.total_chars > value.text.length ? `\n…${value.total_chars - value.text.length} more characters` : '');
    }).catch(() => { result.textContent = 'Nothing was recorded for this step.'; });
  }

  function addStep(data) {
    const row = el('button', 'row');
    row.type = 'button';
    row.setAttribute('aria-expanded', 'false');
    const tag = el('span');
    setTag(tag, data.tool);
    const what = el('span', 'what');
    const label = TOOL_TEXT[data.tool] || data.tool;
    const detail = summarise(data.args);
    what.append(document.createTextNode(label));
    if (detail) what.append(document.createTextNode(' '), el('em', '', detail));
    what.title = detail ? `${label}: ${detail}` : label;
    row.append(tag, what, el('small', '', ''));
    const thought = lastThought;
    row.addEventListener('click', () => inspect(row, data, thought));
    appendRow(row);
    steps.set(data.call_id, { row, tag, tool: data.tool });
    return detail ? `${label}: ${detail}` : label;
  }

  function finishStep(data) {
    const step = steps.get(data.call_id);
    if (!step) return;
    setTag(step.tag, step.tool, data.status);
    step.row.querySelector('small').textContent = data.seconds ? `${data.seconds.toFixed(1)}s` : '';
    if (data.injection_signals && data.injection_signals.length) {
      step.row.after(el('div', 'flag', 'This source tried to give instructions. Treated as data and not followed.'));
    }
  }

  function refusedRow(text) {
    const row = el('div', 'row quiet');
    row.append(el('span', 'tag refused', 'REFUSED'), el('span', 'what', text), el('small', '', ''));
    row.querySelector('.what').title = text;
    appendRow(row);
  }

  function renderEvent(event) {
    const data = event.data;
    switch (event.type) {
      case 'session_created':
        // The goal line above the list shows the latest message, so one message needs no row of its own.
        firstMessage = data.goal;
        break;
      case 'message':
        turnStartedAt = event.at;
        if (firstMessage !== null) { $('activity').prepend(el('div', 'said', firstMessage)); firstMessage = null; }
        appendRow(el('div', 'said', data.text));
        break;
      case 'reasoner_reply':
        lastThought = data.thought || '';
        if (lastThought) setNow(lastThought);
        break;
      case 'tool_started':
        // The plan has its own line above the list, so changing it isn't an action worth a row.
        if (data.tool === 'update_plan') {
          stepsSincePlan = 0;
        } else {
          stepsSincePlan += 1;
          setNow(addStep(data));
        }
        break;
      case 'tool_finished':
        finishStep(data);
        break;
      case 'tool_denied':
        refusedRow(`${TOOL_TEXT[data.tool] || data.tool}: ${data.message}`);
        break;
      case 'reply_rejected':
        refusedRow(`A reply outside the rules (${data.reason}). Nothing ran.`);
        break;
      case 'question_answered':
        appendRow(el('div', 'said', data.text));
        break;
      case 'approval_decided': {
        const row = el('div', 'row quiet');
        row.append(el('span', 'tag ask', data.decision === 'approve' ? 'YOU: YES' : 'YOU: NO'), el('span', 'what', data.decision === 'approve' ? 'Approved that exact request.' : 'Rejected that request.'), el('small', '', ''));
        appendRow(row);
        break;
      }
      case 'turn_finished':
        if (data.answer) appendRow(el('div', 'answer', data.answer));
        else if (data.error) appendRow(el('div', 'answer failed', data.error));
        break;
      default:
        break;
    }
  }

  // --- A question or approval stays pinned above the input, and opens the panel by itself. ---

  function renderPending(session) {
    const box = $('pending');
    const pending = session.pending;
    if (!pending) {
      box.hidden = true;
      box.replaceChildren();
      box.dataset.id = '';
      return;
    }
    if (box.dataset.id === pending.id) return;
    box.dataset.id = pending.id;
    box.hidden = false;
    box.replaceChildren();
    const body = el('div', 'pending-body');
    if (pending.kind === 'question') {
      body.append(el('h3', '', 'Chaser Agent needs something from you'), el('p', '', pending.question));
      const row = el('div', 'choices');
      for (const option of pending.options || []) {
        const choice = el('button', 'control', option);
        choice.type = 'button';
        choice.addEventListener('click', () => answer(pending.id, option));
        row.append(choice);
      }
      const input = el('textarea');
      input.rows = 2;
      input.placeholder = 'Your answer';
      input.setAttribute('aria-label', 'Your answer');
      const send = el('button', 'yes', 'Answer');
      send.type = 'button';
      send.addEventListener('click', () => input.value.trim() && answer(pending.id, input.value.trim()));
      row.prepend(send);
      box.append(body, input, row);
    } else {
      body.append(el('h3', '', 'Say yes to this exact action?'), el('p', '', ASK_TEXT[pending.tool] || TOOL_TEXT[pending.tool] || pending.tool));
      if (pending.args.title) body.append(el('strong', '', pending.args.title));
      if (pending.args.text) body.append(el('p', '', pending.args.text));
      const exact = el('details');
      exact.append(el('summary', '', 'See the exact request'), el('pre', '', JSON.stringify(pending.args, null, 1)));
      const row = el('div', 'choices');
      const yes = el('button', 'yes', 'Yes, do this');
      const no = el('button', 'control', 'No');
      yes.type = no.type = 'button';
      yes.addEventListener('click', () => decide(pending, 'approve'));
      no.addEventListener('click', () => decide(pending, 'reject'));
      row.append(yes, no);
      body.append(exact);
      box.append(body, row);
    }
  }

  function renderProgress(session) {
    const plan = session.plan || [];
    const box = $('progress');
    // A plan the agent left half-way says nothing once the work has stopped.
    box.hidden = !plan.length || !(ACTIVE.has(session.status) || session.pending);
    if (box.hidden) return;
    const doing = plan.findIndex((step) => step.status === 'active');
    const done = plan.filter((step) => step.status === 'done').length;
    const index = doing >= 0 ? doing : Math.min(done, plan.length - 1);
    if (stepsSincePlan > STALE_PLAN_STEPS) {
      box.replaceChildren(el('b', '', `Plan not updated for ${stepsSincePlan} steps.`), document.createTextNode(`  It last said step ${index + 1} of ${plan.length}.`));
    } else {
      box.replaceChildren(el('b', '', `Step ${index + 1} of ${plan.length}`), document.createTextNode(`  ${plan[index].text}`));
    }
    box.title = plan.map((step, at) => `${at + 1}. ${step.text}`).join('\n');
  }

  function renderMeta(session) {
    // Problems first: if the line is cut short, it's the clock that goes.
    const parts = [];
    if (session.denied_calls) parts.push(`${session.denied_calls} refused`);
    if (session.tool_failures) parts.push(`${session.tool_failures} failed`);
    const tools = Object.values(session.tool_counts || {}).reduce((sum, count) => sum + count, 0);
    if (tools) parts.push(`${tools} step${tools === 1 ? '' : 's'}`);
    if (startedAt) parts.push(clock(startedAt, endedAt));
    $('meta').textContent = parts.join(' · ');
    $('meta').title = parts.join(' · ');
  }

  async function refreshSession() {
    const id = current;
    if (!id) return;
    const session = await api(`/v1/agent/sessions/${id}`);
    const page = await api(`/v1/agent/sessions/${id}/events?after=${seen}`);
    if (id !== current) return;  // Another session was chosen while this was on its way.
    // Choosing a session refreshes straight away and the timer can land at the same moment, so skip what's already shown.
    for (const event of page.events) {
      if (event.seq <= seen) continue;
      seen = event.seq;
      renderEvent(event);
    }

    const active = ACTIVE.has(session.status);
    startedAt = turnStartedAt || session.created_at;
    endedAt = active || session.pending ? null : session.updated_at;
    hud.dataset.tone = TONE[session.status] || 'idle';
    $('state-text').textContent = STATUS_TEXT[session.status] || session.status;
    // The taskbar is all that's left of a minimized window, so a waiting question shows there.
    document.title = session.pending ? `${STATUS_TEXT[session.status]} · Chaser Agent` : 'Chaser Agent';
    setMotion(session.motion);
    $('goal').hidden = false;
    $('goal').textContent = session.goal;
    $('goal').title = session.goal;
    $('new-work').hidden = false;
    renderPending(session);
    renderProgress(session);
    renderMeta(session);
    $('stop').hidden = !(active || session.pending);
    $('input').placeholder = session.pending ? 'Answer in the box above' : 'Tell Chaser Agent what to do next';

    if (session.pending) setNow(session.pending.kind === 'question' ? session.pending.question : `${ASK_TEXT[session.pending.tool] || TOOL_TEXT[session.pending.tool] || session.pending.tool}?`);
    else if (session.status === 'finished' && session.final_answer) setNow(session.final_answer);
    else if (session.error && !active) setNow(session.error);
    else if (session.status === 'reasoning' && lastThought) setNow(lastThought);
    else if (!nowLine) setNow(STATUS_TEXT[session.status] || session.status);

    // Open by itself only when the state changes to something that needs reading.
    if (session.status !== lastStatus) {
      if (session.pending || session.status === 'finished' || session.status === 'failed' || session.status === 'budget_stopped') setOpen(true);
      lastStatus = session.status;
    }
    if (page.events.length) refreshFiles().catch(() => {});
  }

  async function refreshFiles() {
    const { artifacts } = await api(`/v1/agent/sessions/${current}/artifacts`);
    const button = $('files-button');
    button.hidden = !artifacts.length;
    button.textContent = `Files (${artifacts.length})`;
    return artifacts;
  }

  function showRoute(routes) {
    const box = $('route');
    // The bridge is always there to send to, but it only counts if something is answering it.
    const usable = (routes || []).filter((route) => route.available && route.connected !== false);
    box.hidden = usable.length > 0 || !routes || !routes.length;
    if (box.hidden) return;
    box.textContent = 'No AI model is connected, so Chaser Agent can\'t start work yet. Hover here to see why.';
    box.title = routes.map((route) => `${route.label}: ${route.reason || 'not available'}`).join('\n');
  }

  async function refreshStatus() {
    const status = await api('/v1/agent/status');
    effects = Object.fromEntries((status.tools || []).map((row) => [row.tool, row.side_effect]));
    showRoute(status.reasoners && status.reasoners.routes);
    const parent = $('parent');
    if (status.parent) {
      parent.href = status.parent.url;
      parent.textContent = `Open ${status.parent.label}`;
      parent.hidden = false;
    }
    if (!suggestionBox.childElementCount) {
      for (const example of (status.examples || []).slice(0, 3)) {
        const button = el('button', 'suggestion', example);
        button.type = 'button';
        button.addEventListener('click', () => { $('input').value = example; $('input').focus(); });
        suggestionBox.append(button);
      }
    }
    if (!current) {
      setMotion(status.motion);
      hud.dataset.tone = 'idle';
      $('state-text').textContent = 'Ready';
      setNow('Tell Chaser Agent what to do.');
      $('meta').textContent = '';
    }
    return status;
  }

  function reset() {
    seen = 0;
    steps = new Map();
    lastThought = '';
    lastStatus = '';
    nowLine = '';
    firstMessage = null;
    stepsSincePlan = 0;
    turnStartedAt = null;
    startedAt = endedAt = null;
    $('activity').replaceChildren();
    $('pending').hidden = true;
    $('pending').dataset.id = '';
    $('pending').replaceChildren();
    $('files-button').hidden = true;
    $('notice').textContent = '';
    $('drawer').hidden = true;
  }

  function select(id) {
    current = id;
    reset();
    if (!id) {
      $('activity').append(emptyState);
      $('goal').hidden = true;
      $('progress').hidden = true;
      $('stop').hidden = true;
      $('new-work').hidden = true;
      $('input').placeholder = 'Tell Chaser Agent what to do';
      lastMotion = '';
    }
    refreshStatus().catch(report);
    refreshSession().catch(report);
  }

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
        if (ACTIVE.has(session.status) || session.pending) { $('notice').textContent = 'Chaser Agent is mid-task. Answer above, or press Stop first.'; return; }
        await api(`/v1/agent/sessions/${current}/messages`, { message: text });
      } else {
        const session = await api('/v1/agent/sessions', { message: text });
        select(session.id);
      }
      box.value = '';
      box.style.height = '';
    } catch (error) { report(error); }
  }

  // --- Drawers and the file viewer. ---

  function toggleDrawer(build) {
    const box = $('drawer');
    if (!box.hidden && box.dataset.kind === build.name) { box.hidden = true; return; }
    box.dataset.kind = build.name;
    build(box).then(() => { box.hidden = false; }).catch(report);
  }

  async function recentDrawer(box) {
    const { sessions } = await api('/v1/agent/sessions');
    box.replaceChildren(...(sessions.length ? sessions.slice(0, 12).map((row) => {
      const button = el('button', `pick${row.id === current ? ' on' : ''}`);
      button.type = 'button';
      button.append(el('b', '', row.title), el('small', '', STATUS_TEXT[row.status] || row.status));
      button.addEventListener('click', () => select(row.id));
      return button;
    }) : [el('p', 'pick', 'Nothing yet.')]));
  }

  async function filesDrawer(box) {
    const artifacts = await refreshFiles();
    const rank = (row) => (/brief\.html$/.test(row.name) ? 0 : /\.html$/.test(row.name) ? 1 : 2);
    box.replaceChildren(...[...artifacts].sort((a, b) => rank(a) - rank(b)).slice(0, 40).map((row) => {
      const button = el('button', 'pick');
      button.type = 'button';
      button.append(el('b', '', row.name), el('small', '', `${Math.max(1, Math.round(row.bytes / 1024))} KB`));
      button.addEventListener('click', () => { box.hidden = true; openFile(row.name); });
      return button;
    }));
  }

  async function openFile(name) {
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
    fit(VIEWING);
    $('viewer').showModal();
  }

  async function tick() {
    if (polling) return;
    polling = true;
    try {
      await refreshSession();
      if ($('notice').textContent.startsWith('Lost')) $('notice').textContent = '';
    } catch (error) {
      hud.dataset.tone = 'blocked';
      $('state-text').textContent = 'Lost contact';
      setNow('The local service isn\'t answering.');
      $('notice').textContent = `Lost contact with the local service: ${error.message}`;
    } finally { polling = false; }
  }

  const flip = () => setOpen(!open);
  $('toggle').addEventListener('click', flip);
  $('toggle-text').addEventListener('click', flip);
  $('chevron').addEventListener('click', flip);
  $('send').addEventListener('click', send);
  $('stop').addEventListener('click', () => current && api(`/v1/agent/sessions/${current}/cancel`, {}).then(refreshSession).catch(report));
  $('new-work').addEventListener('click', () => { select(null); $('input').focus(); });
  $('recent-button').addEventListener('click', () => toggleDrawer(recentDrawer));
  $('files-button').addEventListener('click', () => toggleDrawer(filesDrawer));
  $('viewer-close').addEventListener('click', () => $('viewer').close());
  $('viewer').addEventListener('close', () => fit(open ? EXPANDED : COLLAPSED));
  $('input').addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); }
  });
  $('input').addEventListener('input', (event) => {
    event.target.style.height = 'auto';
    event.target.style.height = `${event.target.scrollHeight}px`;
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && open && !$('viewer').open) setOpen(false);
  });

  async function start() {
    token = readToken();
    if (!token) {
      setMotion('blocked');
      hud.dataset.tone = 'blocked';
      $('state-text').textContent = 'Not connected';
      setNow('Open this with: chaser-agent open');
      return;
    }
    $('motion').play().catch(() => {});
    setOpen(false);
    // A resize asked for while the page is still loading is ignored, so ask again once it has.
    const refit = () => setTimeout(() => { if (!$('viewer').open) { sized = ''; fit(open ? EXPANDED : COLLAPSED); } }, 200);
    window.addEventListener('load', refit);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) refit(); });
    select(null);
    // Pick up where things stand: something running or waiting comes back into view.
    try {
      const status = await refreshStatus();
      const resume = (status.waiting_for_operator || [])[0] || (status.active_sessions || [])[0];
      if (resume) select(resume);
    } catch (error) { report(error); }
    setInterval(tick, 1500);
    setInterval(() => refreshStatus().catch(() => {}), 8000);
  }

  start();
})();
