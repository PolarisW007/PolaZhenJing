(function () {
  const log = document.querySelector("[data-chat-log]");
  const form = document.querySelector("[data-chat-form]");
  const drawer = document.querySelector("[data-memory-drawer]");
  const stats = document.querySelector("[data-memory-stats]");
  const memoryTime = document.querySelector("[data-memory-time]");
  const newChat = document.querySelector("[data-new-chat]");
  const historyKey = "pola-agent-chat-history";
  let history = [];
  let typingTimer = null;

  function text(value, fallback) {
    return value && String(value).trim() ? String(value).trim() : fallback;
  }

  function formatNumber(value) {
    return Number(value || 0).toLocaleString("zh-CN");
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderInlineMarkdown(value) {
    return escapeHtml(value)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>")
      .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  }

  function renderMarkdown(content) {
    const source = String(content || "").replace(/\r\n/g, "\n");
    const blocks = [];
    let buffer = [];
    let inCode = false;
    let codeBuffer = [];

    function flushParagraph() {
      if (!buffer.length) return;
      const lines = buffer.splice(0);
      const first = lines[0] || "";
      const heading = first.match(/^(#{1,4})\s+(.+)$/);
      if (heading && lines.length === 1) {
        const level = Math.min(heading[1].length + 2, 6);
        blocks.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`);
        return;
      }
      if (lines.every((line) => /^[-*]\s+/.test(line))) {
        blocks.push(`<ul>${lines.map((line) => `<li>${renderInlineMarkdown(line.replace(/^[-*]\s+/, ""))}</li>`).join("")}</ul>`);
        return;
      }
      if (lines.every((line) => /^\d+\.\s+/.test(line))) {
        blocks.push(`<ol>${lines.map((line) => `<li>${renderInlineMarkdown(line.replace(/^\d+\.\s+/, ""))}</li>`).join("")}</ol>`);
        return;
      }
      if (lines.every((line) => /^>\s?/.test(line))) {
        blocks.push(`<blockquote>${lines.map((line) => renderInlineMarkdown(line.replace(/^>\s?/, ""))).join("<br>")}</blockquote>`);
        return;
      }
      blocks.push(`<p>${lines.map(renderInlineMarkdown).join("<br>")}</p>`);
    }

    source.split("\n").forEach((line) => {
      if (line.trim().startsWith("```")) {
        if (inCode) {
          blocks.push(`<pre><code>${escapeHtml(codeBuffer.join("\n"))}</code></pre>`);
          codeBuffer = [];
          inCode = false;
        } else {
          flushParagraph();
          inCode = true;
        }
        return;
      }
      if (inCode) {
        codeBuffer.push(line);
        return;
      }
      if (!line.trim()) {
        flushParagraph();
        return;
      }
      buffer.push(line);
    });

    if (inCode) blocks.push(`<pre><code>${escapeHtml(codeBuffer.join("\n"))}</code></pre>`);
    flushParagraph();
    return blocks.join("");
  }

  function splitTypingUnits(content) {
    const units = String(content || "").match(/[\s\S]{1,2}/g);
    return units || [];
  }

  function typeMessage(target, content, options = {}) {
    const units = splitTypingUnits(content);
    let index = 0;
    target.classList.add("typing");
    target.innerHTML = "";
    clearInterval(typingTimer);
    typingTimer = window.setInterval(() => {
      index += 1;
      target.innerHTML = renderMarkdown(units.slice(0, index).join(""));
      log.scrollTop = log.scrollHeight;
      if (index >= units.length) {
        clearInterval(typingTimer);
        typingTimer = null;
        target.innerHTML = renderMarkdown(content);
        target.classList.remove("typing");
        if (typeof options.onDone === "function") options.onDone();
      }
    }, options.delay || 22);
  }

  function appendMessage(role, content, options = {}) {
    const item = document.createElement("article");
    item.className = `message ${role}`;
    if (role === "assistant") {
      const image = document.createElement("img");
      image.src = "assets/agent-avatar.png";
      image.alt = "";
      item.appendChild(image);
    }
    const body = document.createElement("div");
    const speaker = document.createElement("span");
    speaker.textContent = role === "assistant" ? "超级小王" : "你";
    const contentNode = document.createElement("div");
    contentNode.className = "message-content";
    if (options.typing) {
      contentNode.classList.add("typing");
      contentNode.textContent = content;
    } else {
      contentNode.innerHTML = renderMarkdown(content);
    }
    body.append(speaker, contentNode);
    item.appendChild(body);
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
    return contentNode;
  }

  function persist() {
    localStorage.setItem(historyKey, JSON.stringify(history.slice(-16)));
  }

  function restore() {
    try {
      const saved = JSON.parse(localStorage.getItem(historyKey) || "[]");
      if (!Array.isArray(saved) || !saved.length) return;
      history = saved.filter((item) => item && item.role && item.content).slice(-16);
      history.forEach((item) => appendMessage(item.role, item.content));
    } catch {
      history = [];
    }
  }

  function renderMemories(memories) {
    if (!drawer) return;
    if (!Array.isArray(memories) || !memories.length) {
      drawer.hidden = true;
      drawer.textContent = "";
      return;
    }
    drawer.hidden = false;
    drawer.textContent = "";
    memories.slice(0, 4).forEach((memory) => {
      const item = document.createElement("article");
      const title = document.createElement("strong");
      title.textContent = text(memory.title, "Memory");
      const source = document.createElement("p");
      source.textContent = memory.path || "";
      item.append(title, source);
      drawer.appendChild(item);
    });
  }

  async function loadMemoryStatus() {
    try {
      const response = await fetch("/PolaZhenjing/admin/api/agent/memory/status", {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) return;
      const payload = await response.json();
      const s = payload.stats || {};
      if (stats) {
        const values = stats.querySelectorAll("dd");
        if (values[0]) values[0].textContent = formatNumber(s.notes);
        if (values[1]) values[1].textContent = formatNumber(s.chunks);
        if (values[2]) values[2].textContent = "Obsidian";
      }
      if (memoryTime) {
        const when = payload.generated_at ? new Date(payload.generated_at) : null;
        memoryTime.textContent = when && !Number.isNaN(when.getTime())
          ? `记忆更新于 ${when.toLocaleString("zh-CN")}`
          : "记忆已接入";
      }
    } catch {
      if (memoryTime) memoryTime.textContent = "记忆状态暂不可用";
    }
  }

  async function send(message) {
    const button = form.querySelector("button");
    button.disabled = true;
    appendMessage("user", message);
    history.push({ role: "user", content: message });
    persist();
    const thinking = "我正在检索长期记忆并组织回答...";
    appendMessage("assistant", thinking, { typing: true });
    try {
      const response = await fetch("/PolaZhenjing/admin/api/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ message, history: history.slice(0, -1) }),
      });
      const payload = await response.json();
      const last = log.querySelector(".message.assistant:last-child .message-content");
      if (!response.ok || !payload.ok) {
        last.innerHTML = renderMarkdown(payload.error || "Agent 暂时没有返回。");
        last.classList.remove("typing");
        button.disabled = false;
        return;
      }
      typeMessage(last, payload.answer, {
        onDone: () => {
          history.push({ role: "assistant", content: payload.answer });
          persist();
          button.disabled = false;
        },
      });
      renderMemories(payload.memories);
    } catch (error) {
      const last = log.querySelector(".message.assistant:last-child .message-content");
      last.innerHTML = renderMarkdown(`连接失败：${error.message}`);
      last.classList.remove("typing");
      button.disabled = false;
    }
  }

  if (form) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const input = form.elements.message;
      const message = input.value.trim();
      if (!message) return;
      input.value = "";
      send(message);
    });
  }

  if (newChat) {
    newChat.addEventListener("click", () => {
      history = [];
      localStorage.removeItem(historyKey);
      log.textContent = "";
      appendMessage("assistant", "新会话已开始。我会继续使用炽驹的部分记忆，但不会带入刚才的上下文。");
      renderMemories([]);
    });
  }

  restore();
  loadMemoryStatus();
})();
