(function () {
  function ensureState() {
    if (!window.__starRuntimeInspectorState) {
      window.__starRuntimeInspectorState = {
        runtimeOverview: [],
        selectedRuntimeKey: '',
        selectedRuntimeDetail: null,
        runtimeInspectorTab: 'summary',
        runtimeLoading: false,
        runtimeError: '',
        selectedOfficeId: ''
      };
    }
    return window.__starRuntimeInspectorState;
  }

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function getSelectedRuntimeKey() {
    return ensureState().selectedRuntimeKey;
  }

  function getRuntimeItemByAgentId(agentId) {
    const state = ensureState();
    const candidates = (state.runtimeOverview || []).filter(item => item && item.agentId === agentId);
    if (!state.selectedOfficeId) return candidates[0] || null;
    return candidates.find(item => item.officeId === state.selectedOfficeId) || candidates[0] || null;
  }

  function getOfficeOptions() {
    const state = ensureState();
    const offices = new Map();
    for (const item of state.runtimeOverview || []) {
      if (!item || !item.officeId) continue;
      if (!offices.has(item.officeId)) {
        offices.set(item.officeId, {
          officeId: item.officeId,
          label: item.agentName || item.rootSessionId || item.officeId,
        });
      }
    }
    return Array.from(offices.values());
  }

  function renderOfficeSelector() {
    const state = ensureState();
    const tabs = document.getElementById('runtime-inspector-tabs');
    if (!tabs) return;
    let selector = document.getElementById('runtime-office-selector');
    const options = getOfficeOptions();
    if (!selector) {
      selector = document.createElement('select');
      selector.id = 'runtime-office-selector';
      selector.className = 'runtime-tab-btn';
      selector.style.marginLeft = 'auto';
      selector.onchange = (e) => setSelectedOfficeId(e.target.value || '');
      tabs.parentNode.insertBefore(selector, tabs);
    }
    selector.innerHTML = ['<option value="">全部 Office</option>']
      .concat(options.map(opt => `<option value="${escapeHtml(opt.officeId)}" ${state.selectedOfficeId === opt.officeId ? 'selected' : ''}>${escapeHtml(opt.label)}</option>`))
      .join('');
  }

  function renderRuntimeInspectorTabs() {
    const state = ensureState();
    const tabs = document.getElementById('runtime-inspector-tabs');
    if (!tabs) return;
    const tabDefs = [
      { id: 'summary', label: 'Summary' },
      { id: 'thinking', label: 'Thinking' },
      { id: 'messages', label: 'Messages' },
      { id: 'tools', label: 'Tools' },
      { id: 'timeline', label: 'Timeline' },
      { id: 'raw', label: 'Raw JSON' },
    ];
    tabs.innerHTML = tabDefs.map(tab => `
      <button class="runtime-tab-btn ${state.runtimeInspectorTab === tab.id ? 'active' : ''}" onclick="setRuntimeInspectorTab('${tab.id}')">${tab.label}</button>
    `).join('');
    renderOfficeSelector();
  }

  function renderRuntimeInspector() {
    const state = ensureState();
    const subtitle = document.getElementById('runtime-inspector-subtitle');
    const body = document.getElementById('runtime-inspector-body');
    if (!subtitle || !body) return;

    renderRuntimeInspectorTabs();

    if (state.runtimeLoading) {
      subtitle.textContent = '正在加载运行态…';
      body.innerHTML = '<div class="runtime-loading">正在加载运行态…</div>';
      return;
    }
    if (state.runtimeError) {
      subtitle.textContent = '运行态加载失败';
      body.innerHTML = `<div class="runtime-error">${escapeHtml(state.runtimeError)}</div>`;
      return;
    }
    if (!state.selectedRuntimeDetail || !state.selectedRuntimeDetail.summary) {
      subtitle.textContent = '请选择一个 Agent 查看运行态';
      body.innerHTML = '<div class="runtime-empty">请选择一个 Agent 查看运行态</div>';
      return;
    }

    const summary = state.selectedRuntimeDetail.summary || {};
    subtitle.textContent = `${summary.agentName || 'Unknown'} · ${summary.status || 'idle'} · ${summary.phase || 'unknown'}`;

    if (state.runtimeInspectorTab === 'summary') {
      const edges = Array.isArray(state.selectedRuntimeDetail.edges) ? state.selectedRuntimeDetail.edges : [];
      const relationHtml = edges.length
        ? `<div class="runtime-summary-card"><div class="runtime-event-title">运行关系</div>${edges.map(edge => `<div class="runtime-summary-row"><span class="runtime-summary-label">${escapeHtml(edge.kind || 'edge')}</span><span>${escapeHtml(edge.label || '')} · ${escapeHtml(edge.toRunId || '-')}</span></div>`).join('')}</div>`
        : '';
      body.innerHTML = `
        <div class="runtime-summary-card">
          <div class="runtime-event-title">${escapeHtml(summary.headline || summary.detail || '暂无摘要')}</div>
          <div style="color:#cbd5e1; font-size:11px; margin-bottom:6px;">${escapeHtml(summary.detail || '暂无详情')}</div>
          <div class="runtime-summary-row"><span class="runtime-summary-label">Agent</span><span>${escapeHtml(summary.agentName || summary.agentId || '-')}</span></div>
          <div class="runtime-summary-row"><span class="runtime-summary-label">Identity</span><span>${escapeHtml(summary.identityType || (state.selectedRuntimeDetail.synthetic ? 'synthetic' : 'explicit'))}</span></div>
          <div class="runtime-summary-row"><span class="runtime-summary-label">Office</span><span>${escapeHtml(summary.officeId || state.selectedRuntimeDetail.officeId || '-')}</span></div>
          <div class="runtime-summary-row"><span class="runtime-summary-label">Root Session</span><span>${escapeHtml(summary.rootSessionId || state.selectedRuntimeDetail.rootSessionId || '-')}</span></div>
          <div class="runtime-summary-row"><span class="runtime-summary-label">Selection Key</span><span>${escapeHtml(summary.selectionKey || '-')}</span></div>
          <div class="runtime-summary-row"><span class="runtime-summary-label">Run ID</span><span>${escapeHtml(summary.runId || '-')}</span></div>
          <div class="runtime-summary-row"><span class="runtime-summary-label">Session</span><span>${escapeHtml((state.selectedRuntimeDetail.session && state.selectedRuntimeDetail.session.sessionId) || '-')}</span></div>
          <div class="runtime-summary-row"><span class="runtime-summary-label">Task</span><span>${escapeHtml((state.selectedRuntimeDetail.backgroundTask && state.selectedRuntimeDetail.backgroundTask.taskId) || '-')}</span></div>
          <div class="runtime-summary-row"><span class="runtime-summary-label">Updated</span><span>${escapeHtml(summary.updatedAt || '-')}</span></div>
        </div>
        ${relationHtml}
      `;
      return;
    }

    if (state.runtimeInspectorTab === 'timeline') {
      const events = Array.isArray(state.selectedRuntimeDetail.events) ? state.selectedRuntimeDetail.events : [];
      if (!events.length) {
        body.innerHTML = '<div class="runtime-empty">当前没有可展示的事件</div>';
        return;
      }
      body.innerHTML = events.map(event => `
        <div class="runtime-event-card">
          <div class="runtime-event-title">${escapeHtml(event.title || event.kind || '事件')}</div>
          <div class="runtime-event-meta">${escapeHtml(event.kind || 'message')} · ${escapeHtml(event.createdAt || '-')}</div>
          <div>${escapeHtml(event.text || '无内容')}</div>
        </div>
      `).join('');
      return;
    }

    if (state.runtimeInspectorTab === 'thinking' || state.runtimeInspectorTab === 'messages' || state.runtimeInspectorTab === 'tools') {
      const events = Array.isArray(state.selectedRuntimeDetail.events) ? state.selectedRuntimeDetail.events : [];
      const kindMap = {
        thinking: ['thinking'],
        messages: ['message', 'status', 'error'],
        tools: ['tool_call', 'tool_result'],
      };
      const filtered = events.filter(event => (kindMap[state.runtimeInspectorTab] || []).includes(event.kind));
      if (!filtered.length) {
        body.innerHTML = `<div class="runtime-empty">当前没有可展示的 ${escapeHtml(state.runtimeInspectorTab)} 数据</div>`;
        return;
      }
      body.innerHTML = filtered.map(event => `
        <details class="runtime-event-card">
          <summary class="runtime-event-title">${escapeHtml(event.title || event.kind || '事件')}</summary>
          <div class="runtime-event-meta">${escapeHtml(event.kind || 'message')} · ${escapeHtml(event.createdAt || '-')}</div>
          <div>${escapeHtml(event.text || '无内容')}</div>
        </details>
      `).join('');
      return;
    }

    body.innerHTML = `
      <div class="runtime-raw-card">
        <pre>${escapeHtml(JSON.stringify(state.selectedRuntimeDetail.raw || state.selectedRuntimeDetail, null, 2))}</pre>
      </div>
    `;
  }

  function setRuntimeInspectorTab(tab) {
    const state = ensureState();
    state.runtimeInspectorTab = tab || 'summary';
    renderRuntimeInspector();
  }

  async function fetchRuntimeOverview() {
    const state = ensureState();
    try {
      const response = await fetch('/runtime/overview?t=' + Date.now(), { cache: 'no-store' });
      const data = await response.json();
      state.runtimeOverview = (data && data.ok && Array.isArray(data.items)) ? data.items : [];
      if (state.selectedOfficeId) {
        const officeStillExists = state.runtimeOverview.some(item => item.officeId === state.selectedOfficeId);
        if (!officeStillExists) state.selectedOfficeId = '';
      }
      if (state.selectedRuntimeKey) {
        const stillExists = state.runtimeOverview.some(item => (!state.selectedOfficeId || item.officeId === state.selectedOfficeId) && (item.selectionKey === state.selectedRuntimeKey || item.agentId === state.selectedRuntimeKey || item.runId === state.selectedRuntimeKey));
        if (!stillExists) {
          state.selectedRuntimeKey = '';
          state.selectedRuntimeDetail = null;
        }
      }
      if (typeof window.renderGuestAgentList === 'function') window.renderGuestAgentList();
      renderRuntimeInspector();
    } catch (error) {
      console.error('拉取运行态总览失败:', error);
    }
  }

  async function fetchRuntimeDetail(selectionKey) {
    const state = ensureState();
    if (!selectionKey) return;
    state.runtimeLoading = true;
    state.runtimeError = '';
    renderRuntimeInspector();
    try {
      const response = await fetch('/runtime/agents/' + encodeURIComponent(selectionKey) + '?t=' + Date.now(), { cache: 'no-store' });
      const data = await response.json();
      if (!data || !data.ok || !data.item) {
        throw new Error((data && data.msg) || '运行态详情获取失败');
      }
      state.selectedRuntimeDetail = data.item;
      state.runtimeInspectorTab = state.runtimeInspectorTab || 'summary';
    } catch (error) {
      state.runtimeError = error && error.message ? error.message : String(error);
      state.selectedRuntimeDetail = null;
    } finally {
      state.runtimeLoading = false;
      renderRuntimeInspector();
      if (typeof window.renderGuestAgentList === 'function') window.renderGuestAgentList();
    }
  }

  function selectRuntimeByKey(selectionKey) {
    const state = ensureState();
    if (!selectionKey) return;
    state.selectedRuntimeKey = selectionKey;
    state.runtimeInspectorTab = 'summary';
    if (typeof window.renderGuestAgentList === 'function') window.renderGuestAgentList();
    fetchRuntimeDetail(selectionKey);
  }

  function selectRuntimeByAgent(agentId) {
    const state = ensureState();
    const runtimeItem = getRuntimeItemByAgentId(agentId);
    if (runtimeItem && runtimeItem.selectionKey) {
      selectRuntimeByKey(runtimeItem.selectionKey);
      return;
    }
    state.selectedRuntimeKey = agentId;
    state.runtimeInspectorTab = 'summary';
    fetchRuntimeDetail(agentId);
  }

  function setSelectedOfficeId(officeId) {
    const state = ensureState();
    state.selectedOfficeId = officeId || '';
    if (typeof window.renderGuestAgentList === 'function') window.renderGuestAgentList();
    renderRuntimeInspector();
  }

  window.escapeRuntimeHtml = escapeHtml;
  window.getRuntimeItemByAgentId = getRuntimeItemByAgentId;
  window.fetchRuntimeOverview = fetchRuntimeOverview;
  window.fetchRuntimeDetail = fetchRuntimeDetail;
  window.selectRuntimeByKey = selectRuntimeByKey;
  window.selectRuntimeByAgent = selectRuntimeByAgent;
  window.setRuntimeInspectorTab = setRuntimeInspectorTab;
  window.setSelectedOfficeId = setSelectedOfficeId;
  window.renderRuntimeInspector = renderRuntimeInspector;
  window.getSelectedRuntimeKey = getSelectedRuntimeKey;
})();
