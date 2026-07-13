let currentRunId = null;
let ws = null;
let outputBuffer = [];

document.addEventListener('DOMContentLoaded', () => {
  loadRunHistory();
  setupEventListeners();
});

function setupEventListeners() {
  document.getElementById('run-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    await startRun();
  });

  document.getElementById('clear-output').addEventListener('click', clearOutput);
  document.getElementById('copy-output').addEventListener('click', copyOutput);
}

async function loadRunHistory() {
  try {
    const res = await fetch('/api/runs');
    const data = await res.json();
    renderRunHistory(data.runs || []);
  } catch (err) {
    console.error('Failed to load run history:', err);
  }
}

function renderRunHistory(runs) {
  const container = document.getElementById('run-history');
  container.innerHTML = '';

  if (!runs || runs.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="icon">&#128213;</div>
        <p>No runs yet. Start one above!</p>
      </div>
    `;
    return;
  }

  runs.forEach((run) => {
    const el = document.createElement('div');
    el.className = 'run-item';
    el.dataset.runId = run.run_id;
    el.innerHTML = `
      <div class="run-header">
        <span class="run-status ${run.status}">${run.status}</span>
      </div>
      <div class="run-task">${escapeHtml(run.task || 'No task')}</div>
      <div class="run-time">${formatTime(run.created_at)}</div>
    `;
    el.addEventListener('click', () => loadRun(run.run_id));
    container.appendChild(el);
  });
}

async function startRun() {
  const form = document.getElementById('run-form');
  const task = document.getElementById('task').value.trim();
  if (!task) return;

  const btn = document.getElementById('run-btn');
  btn.disabled = true;
  btn.innerHTML = '&#9889; Running...';

  clearOutput();
  appendLine('system', 'Starting agent run...');
  appendLine('system', `Task: ${escapeHtml(task)}`);
  appendLine('system', '');

  const payload = {
    task,
    max_steps: parseInt(document.getElementById('max-steps').value) || 15,
    repo_dir: document.getElementById('repo-dir').value || null,
    test_cmd: document.getElementById('test-cmd').value || null,
    lint_cmd: document.getElementById('lint-cmd').value || null,
  };

  try {
    const res = await fetch('/api/runs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    currentRunId = data.run_id;
    appendLine('info', `Run ID: ${currentRunId}`);
    appendLine('info', `Started at: ${data.created_at}`);
    appendLine('system', '');

    document.getElementById('status-dot').className = 'status-dot running';
    document.getElementById('status-text').textContent = 'Running';

    connectWebSocket(currentRunId);
  } catch (err) {
    appendLine('stderr', `Error: ${err.message}`);
    btn.disabled = false;
    btn.innerHTML = '&#9889; Run Agent';
  }
}

function connectWebSocket(runId) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/api/ws/${runId}`;

  ws = new WebSocket(wsUrl);

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    if (msg.type === 'ping') return;

    if (msg.type === 'stdout') {
      appendLine('stdout', msg.data);
    } else if (msg.type === 'stderr') {
      appendLine('stderr', msg.data);
    } else if (msg.type === 'info') {
      appendLine('info', msg.data);
    } else if (msg.type === 'done' || msg.type === 'done') {
      appendLine('success', 'Run completed successfully.');
      appendLine('system', '');
      finishRun();
    } else if (msg.type === 'error') {
      appendLine('stderr', `Error: ${msg.data}`);
      finishRun();
    }
  };

  ws.onerror = () => {
    appendLine('stderr', 'WebSocket connection error. The run may still be in progress.');
  };

  ws.onclose = () => {
    if (currentRunId) {
      checkRunStatus(currentRunId);
    }
  };
}

function checkRunStatus(runId) {
  fetch(`/api/runs/${runId}`)
    .then((res) => res.json())
    .then((data) => {
      if (data.transcript) {
        data.transcript.forEach((entry) => {
          if (entry.type !== 'task') {
            appendLine('system', `[${entry.type}]`);
          }
        });
        appendLine('success', 'Run finished. View transcript for full details.');
      }
      finishRun();
    })
    .catch(() => {
      finishRun();
    });
}

async function loadRun(runId) {
  document.getElementById('status-dot').className = 'status-dot idle';
  document.getElementById('status-text').textContent = 'Viewing Log';

  clearOutput();
  appendLine('system', `Loading run ${runId}...`);

  const res = await fetch(`/api/runs/${runId}`);
  if (!res.ok) {
    appendLine('stderr', 'Failed to load run.');
    return;
  }
  const data = await res.json();
  appendLine('system', `Run: ${runId}`);
  appendLine('system', `Status: ${data.status}`);
  appendLine('system', `Task: ${escapeHtml(data.task || 'N/A')}`);
  appendLine('system', `Created: ${data.created_at || 'N/A'}`);
  appendLine('system', '');

  if (data.transcript) {
    data.transcript.forEach((entry) => {
      appendLine('system', `[${entry.type}]`);
      if (typeof entry.content === 'string') {
        entry.content.split('\n').forEach((line) => {
          if (line.trim()) appendLine('stdout', line);
        });
      }
    });
  } else if (data.output) {
    data.output.split('\n').forEach((line) => {
      if (line.trim()) appendLine('stdout', line);
    });
  }
}

function finishRun() {
  currentRunId = null;
  ws = null;
  const btn = document.getElementById('run-btn');
  btn.disabled = false;
  btn.innerHTML = '&#9889; Run Agent';
  document.getElementById('status-dot').className = 'status-dot idle';
  document.getElementById('status-text').textContent = 'Idle';
  loadRunHistory();
}

function appendLine(type, text) {
  const output = document.getElementById('output');
  const lines = text.split('\n');

  lines.forEach((line) => {
    const div = document.createElement('div');
    div.className = `line ${type}`;
    div.textContent = line;
    output.appendChild(div);
  });

  output.scrollTop = output.scrollHeight;
}

function clearOutput() {
  const output = document.getElementById('output');
  output.innerHTML = '';
  outputBuffer = [];
}

function copyOutput() {
  const output = document.getElementById('output');
  const text = Array.from(output.querySelectorAll('.line'))
    .map((el) => el.textContent)
    .join('\n');

  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById('copy-output');
    const orig = btn.innerHTML;
    btn.innerHTML = '&#10003; Copied!';
    setTimeout(() => { btn.innerHTML = orig; }, 2000);
  });
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function formatTime(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleString();
  } catch {
    return iso;
  }
}
