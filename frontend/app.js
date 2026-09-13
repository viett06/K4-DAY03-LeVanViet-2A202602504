const $ = (id) => document.getElementById(id);

let mode = "react";

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || res.statusText);
  }
  return res.json();
}

function setMode(next) {
  mode = next;
  document.querySelectorAll(".mode").forEach((btn) => {
    btn.classList.toggle("on", btn.dataset.mode === mode);
  });
  $("modeHint").textContent =
    mode === "react"
      ? "Cấp 3: Thought → Action → Observation qua MCP."
      : "Cấp 2: chỉ sinh text, không gọi Tool — để so sánh với Agent.";
  $("stageTitle").textContent =
    mode === "react" ? "ReAct Agent · Học vụ VinUni" : "Chatbot Baseline · không có Tool";
}

function renderTools(tools) {
  $("toolList").innerHTML = tools
    .map(
      (tool) =>
        `<li>${escapeHtml(tool.name)}<small>${escapeHtml(tool.description)}</small></li>`
    )
    .join("");
  $("pillTools").textContent = `${tools.length} tools`;
}

function renderTests(tests) {
  $("testList").innerHTML = tests
    .map(
      (tc) =>
        `<button class="test" type="button" data-q="${escapeHtml(tc.question)}" data-type="${escapeHtml(tc.type || "")}">
          <b>${escapeHtml(tc.id)} · ${escapeHtml(tc.type)}</b>
          <span>${escapeHtml(tc.question)}</span>
        </button>`
    )
    .join("");
  $("testList").querySelectorAll(".test").forEach((btn) => {
    btn.addEventListener("click", () => {
      const nextMode = btn.dataset.type === "direct_query" ? "chatbot" : "react";
      setMode(nextMode);
      $("chatInput").value = btn.dataset.q;
      $("chatInput").focus();
      sendMessage(btn.dataset.q);
    });
  });
}

function renderMemory(prompts) {
  if (!prompts || !prompts.length) {
    $("memoryList").innerHTML = `<li class="muted">Chưa có lịch sử.</li>`;
    $("pillMem").textContent = "0 prompt cũ";
    return;
  }
  $("pillMem").textContent = `${prompts.length} prompt cũ`;
  $("memoryList").innerHTML = prompts
    .map(
      (item, index) =>
        `<li>
          <span class="rid">#${index + 1} · ${escapeHtml((item.request_id || "").slice(0, 8))}</span>
          ${escapeHtml(item.prompt)}
        </li>`
    )
    .join("");
}

function renderStatus(status) {
  $("stProvider").textContent = status.provider;
  $("stModel").textContent = status.model || "—";
  $("stMcp").textContent = `${status.mcp_server} (${status.tool_count})`;
  $("stMemory").textContent = status.memory_backend;
  $("pillMem").textContent = `${status.old_prompts} prompt cũ`;
  const flag = $("liveFlag");
  if (status.is_mock) {
    flag.textContent = "Mock Offline — chưa có API thật";
    flag.className = "live-flag bad";
  } else {
    flag.textContent = "LLM API thật đang kết nối";
    flag.className = "live-flag ok";
  }
}

function hideEmpty() {
  const empty = $("emptyState");
  if (empty) empty.remove();
}

function addUserBubble(text) {
  hideEmpty();
  const wrap = document.createElement("div");
  wrap.className = "turn";
  wrap.innerHTML = `<div class="bubble user">${escapeHtml(text)}</div>`;
  $("transcript").appendChild(wrap);
  wrap.scrollIntoView({ behavior: "smooth", block: "end" });
  return wrap;
}

function renderTraceCard(payload) {
  const tools = (payload.used_tools || []).join(", ") || "không gọi tool";
  const steps = (payload.traces || [])
    .map((event) => {
      if (event.action_type === "TOOL_EXECUTION") {
        return `<div class="step">
            <div class="label">Action · ${escapeHtml(event.tool_name)} · ${event.latency_ms} ms</div>
            <pre>${escapeHtml(JSON.stringify(event.arguments || {}, null, 2))}</pre>
          </div>
          <div class="step obs">
            <div class="label">Observation MCP</div>
            <pre>${escapeHtml(JSON.stringify(event.observation || {}, null, 2))}</pre>
          </div>`;
      }
      if (event.action_type === "FINAL_ANSWER") {
        return `<div class="step final">
            <div class="label">Thought</div>
            <pre>${escapeHtml(event.thought || "")}</pre>
          </div>`;
      }
      return "";
    })
    .join("");

  return `<article class="waterfall">
      <div class="wf-head ${payload.mode === "chatbot" ? "chatbot" : ""}">
        <strong>${payload.mode === "react" ? "ReAct waterfall" : "Chatbot baseline"}</strong>
        <span>${escapeHtml(tools)}</span>
      </div>
      <div class="steps">${steps}</div>
      <div class="answer">${escapeHtml(payload.final_answer || "")}</div>
    </article>`;
}

async function refreshMemory() {
  try {
    const data = await fetchJson("/api/memory");
    renderMemory(data.prompts);
  } catch {
    /* ignore */
  }
}

async function sendMessage(text) {
  const query = (text || $("chatInput").value || "").trim();
  if (!query) return;
  $("chatInput").value = "";
  const turn = addUserBubble(query);
  $("sendBtn").disabled = true;

  const pending = document.createElement("div");
  pending.className = "waterfall";
  pending.innerHTML = `<div class="wf-head">Đang suy luận ReAct…</div>`;
  turn.appendChild(pending);

  try {
    const payload = await fetchJson("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: query, mode }),
    });
    pending.outerHTML = renderTraceCard(payload);
    await refreshMemory();
  } catch (err) {
    pending.innerHTML = `<div class="wf-head">Lỗi</div><div class="answer">${escapeHtml(err.message)}</div>`;
  } finally {
    $("sendBtn").disabled = false;
    turn.scrollIntoView({ behavior: "smooth", block: "end" });
  }
}

async function boot() {
  document.querySelectorAll(".mode").forEach((btn) => {
    btn.addEventListener("click", () => setMode(btn.dataset.mode));
  });
  $("chatForm").addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage();
  });
  $("chatInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });

  const [status, tools, tests, memory] = await Promise.all([
    fetchJson("/api/status"),
    fetchJson("/api/tools"),
    fetchJson("/api/tests"),
    fetchJson("/api/memory"),
  ]);
  renderStatus(status);
  renderTools(tools.tools || []);
  renderTests(tests.tests || []);
  renderMemory(memory.prompts);
}

boot().catch((err) => {
  $("liveFlag").textContent = `Không tải được API: ${err.message}`;
  $("liveFlag").className = "live-flag bad";
});
