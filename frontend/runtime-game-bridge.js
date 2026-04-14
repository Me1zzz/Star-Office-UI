(function () {
  const state = {
    runtimeOverview: [],
    selectedRuntimeKey: '',
    runtimeTooltip: null,
  };

  function fetchRuntimeOverviewForGame() {
    return fetch('/runtime/overview?t=' + Date.now(), { cache: 'no-store' })
      .then(response => response.json())
      .then(data => {
        if (!data || !data.ok || !Array.isArray(data.items)) return [];
        state.runtimeOverview = data.items;
        return state.runtimeOverview;
      })
      .catch(error => {
        console.error('拉取 runtime overview 失败:', error);
        return [];
      });
  }

  function getRuntimeItem(agentId) {
    const selectedOfficeId = window.__starRuntimeInspectorState ? (window.__starRuntimeInspectorState.selectedOfficeId || '') : '';
    const items = selectedOfficeId
      ? state.runtimeOverview.filter(item => item && item.officeId === selectedOfficeId)
      : state.runtimeOverview;
    return items.find(item => item && item.agentId === agentId) || null;
  }

  function getSelectedRuntimeKey() {
    return state.selectedRuntimeKey;
  }

  function showRuntimeTooltip(game, agent, runtimeItem, x, y) {
    if (!game) return;
    if (state.runtimeTooltip) {
      state.runtimeTooltip.destroy();
      state.runtimeTooltip = null;
    }
    const title = (agent.name || 'Agent') + ' · ' + ((runtimeItem && runtimeItem.status) || agent.state || 'idle');
    const detail = (runtimeItem && (runtimeItem.headline || runtimeItem.detail)) || agent.detail || '暂无运行态摘要';
    const width = Math.min(420, Math.max(title.length, detail.length) * 9 + 28);
    const bg = game.add.rectangle(x, y - 76, width, 46, 0x0f172a, 0.96);
    bg.setStrokeStyle(2, 0x22c55e, 1);
    const txt = game.add.text(x, y - 76, `${title}\n${detail}`, {
      fontFamily: 'ArkPixel, monospace',
      fontSize: '11px',
      fill: '#e5e7eb',
      align: 'center',
      wordWrap: { width: width - 14 }
    }).setOrigin(0.5);
    state.runtimeTooltip = game.add.container(0, 0, [bg, txt]);
    state.runtimeTooltip.setDepth(1800);
  }

  function selectRuntime(agentId, selectionKey) {
    state.selectedRuntimeKey = selectionKey || agentId || '';
    if (typeof window.selectRuntimeByAgent === 'function' && agentId) {
      window.selectRuntimeByAgent(agentId);
    }
  }

  window.StarRuntimeGameBridge = {
    fetchRuntimeOverviewForGame,
    getRuntimeItem,
    getSelectedRuntimeKey,
    showRuntimeTooltip,
    selectRuntime,
  };
})();
