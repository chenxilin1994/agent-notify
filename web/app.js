/**
 * AGENT NOTIFY - Terminal UI Controller
 * Version: 2.1 - Pagination & Data Management
 */

let latestState = null;
let paginationState = {
  page: 1,
  perPage: 20,
  total: 0,
  totalPages: 0,
};

let sortColumn = "timestamp";
let sortDirection = "desc";

// Response display state
let responseMode = "preview"; // "preview" or "raw"
let responseSize = "normal"; // "normal", "expanded", "collapsed"

// Utility Functions
function setStatus(message) {
  const el = document.getElementById("status-message");
  if (el) el.textContent = message || "";
}

// Simple Markdown to HTML converter
function markdownToHtml(text) {
  if (!text) return "";

  let html = text;

  // Escape HTML entities first (but preserve markdown)
  html = html.replace(/&/g, "&amp;");
  html = html.replace(/</g, "&lt;");
  html = html.replace(/>/g, "&gt;");

  // Code blocks (```code```)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, function(match, lang, code) {
    return '<pre class="md-code-block"><code class="language-' + lang + '">' + code.trim() + '</code></pre>';
  });

  // Inline code (`code`)
  html = html.replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>');

  // Tables: | header | header | format
  html = html.replace(/^\|(.+)\|\s*\n\|[-:\s|]+\|\s*\n((?:\|.+\|\s*\n?)+)/gm, function(match, headerRow, bodyRows) {
    // Parse header
    const headers = headerRow.split('|').map(function(h) { return h.trim(); }).filter(function(h) { return h; });
    let tableHtml = '<table class="md-table"><thead><tr>';
    headers.forEach(function(h) {
      tableHtml += '<th class="md-th">' + h + '</th>';
    });
    tableHtml += '</tr></thead><tbody>';

    // Parse body rows
    const rows = bodyRows.trim().split('\n');
    rows.forEach(function(row) {
      const cells = row.split('|').map(function(c) { return c.trim(); }).filter(function(c) { return c; });
      if (cells.length > 0) {
        tableHtml += '<tr class="md-tr">';
        cells.forEach(function(c) {
          tableHtml += '<td class="md-td">' + c + '</td>';
        });
        tableHtml += '</tr>';
      }
    });
    tableHtml += '</tbody></table>';
    return tableHtml;
  });

  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>');

  // Bold and italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Links [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a class="md-link" href="$2" target="_blank">$1</a>');

  // Bullet lists
  html = html.replace(/^- (.+)$/gm, '<li class="md-li">$1</li>');

  // Wrap consecutive list items in ul
  html = html.replace(/(<li class="md-li">.*<\/li>\n?)+/g, function(match) {
    return '<ul class="md-ul">' + match + '</ul>';
  });

  // Numbered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li class="md-li">$1</li>');

  // Paragraphs (wrap lines that aren't already wrapped)
  html = html.split('\n\n').map(function(para) {
    if (para.trim() && !para.startsWith('<')) {
      return '<p class="md-p">' + para.replace(/\n/g, '<br>') + '</p>';
    }
    return para;
  }).join('\n');

  return html;
}

// Toggle response mode (preview vs raw markdown)
function toggleResponseMode() {
  const btn = document.getElementById("toggle-mode");
  const summaryEl = document.getElementById("latest-summary");

  if (!latestState) return;

  if (responseMode === "preview") {
    responseMode = "raw";
    btn.classList.add("active");
    btn.textContent = "◉";
    if (summaryEl) {
      summaryEl.classList.add("raw-mode");
      summaryEl.textContent = latestState.summary || "";
    }
  } else {
    responseMode = "preview";
    btn.classList.remove("active");
    btn.textContent = "◈";
    if (summaryEl) {
      summaryEl.classList.remove("raw-mode");
      summaryEl.innerHTML = markdownToHtml(latestState.summary || "");
    }
  }
}

// Show response in large modal
function showResponseModal() {
  const modal = document.getElementById("response-view-modal");
  const content = document.getElementById("response-view-content");
  const titleEl = document.getElementById("response-view-title");
  const modalToggleBtn = document.getElementById("modal-toggle-mode");
  const mainToggleBtn = document.getElementById("toggle-mode");

  if (!latestState) return;

  titleEl.textContent = "AI 回复详情";

  // Sync modal toggle button state with main view
  if (responseMode === "raw") {
    modalToggleBtn.classList.add("active");
    modalToggleBtn.textContent = "◉";
    content.classList.add("raw-mode");
    content.textContent = latestState.summary || "";
  } else {
    modalToggleBtn.classList.remove("active");
    modalToggleBtn.textContent = "◈";
    content.classList.remove("raw-mode");
    content.innerHTML = markdownToHtml(latestState.summary || "");
  }

  modal.classList.remove("hidden");
}

// Toggle mode from modal (syncs with main view)
function toggleResponseModeFromModal() {
  toggleResponseMode();

  // Update modal content
  const content = document.getElementById("response-view-content");
  const modalToggleBtn = document.getElementById("modal-toggle-mode");

  if (!latestState) return;

  if (responseMode === "raw") {
    modalToggleBtn.classList.add("active");
    modalToggleBtn.textContent = "◉";
    content.classList.add("raw-mode");
    content.textContent = latestState.summary || "";
  } else {
    modalToggleBtn.classList.remove("active");
    modalToggleBtn.textContent = "◈";
    content.classList.remove("raw-mode");
    content.innerHTML = markdownToHtml(latestState.summary || "");
  }
}

// Close response view modal
function closeResponseModal() {
  const modal = document.getElementById("response-view-modal");
  modal.classList.add("hidden");
}

function formatTimestamp(ts) {
  if (!ts) return "--:--:--";
  try {
    const date = new Date(ts);
    return date.toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return ts;
  }
}

function formatDateShort(ts) {
  if (!ts) return "";
  try {
    const date = new Date(ts);
    return date.toLocaleDateString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
    });
  } catch {
    return "";
  }
}

function formatProjectName(cwd) {
  if (!cwd) return "unknown";
  const parts = cwd.split("/");
  return parts[parts.length - 1] || cwd;
}

function truncateText(text, maxLength) {
  maxLength = maxLength || 60;
  if (!text) return "--";
  return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
}

// Check if text is truncated
function isTruncated(text, maxLength) {
  maxLength = maxLength || 60;
  return text && text.length > maxLength;
}

// Time Display
function updateCurrentTime() {
  const el = document.getElementById("current-time");
  if (el) {
    el.textContent = new Date().toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }
}

setInterval(updateCurrentTime, 1000);
updateCurrentTime();

// Pagination
function renderPagination() {
  const el = document.getElementById("pagination-controls");
  if (!el) return;

  const page = paginationState.page;
  const totalPages = paginationState.totalPages;

  let html = "";
  html += '<button class="page-btn" data-page="' + (page - 1) + '" ' + (page <= 1 ? "disabled" : "") + '>上一页</button>';
  html += '<span class="page-info">第 ' + page + " 页 / 共 " + (totalPages || 1) + " 页</span>";
  html += '<input type="number" class="page-input" id="page-jump" min="1" max="' + totalPages + '" value="' + page + '" />';
  html += '<button class="page-btn" data-page="' + (page + 1) + '" ' + (page >= totalPages ? "disabled" : "") + '>下一页</button>';

  el.innerHTML = html;

  el.querySelectorAll(".page-btn").forEach(function(btn) {
    btn.addEventListener("click", function() {
      const targetPage = parseInt(btn.dataset.page);
      if (targetPage >= 1 && targetPage <= totalPages) {
        paginationState.page = targetPage;
        refreshHistory();
      }
    });
  });

  const pageJump = document.getElementById("page-jump");
  if (pageJump) {
    pageJump.addEventListener("change", function() {
      const targetPage = parseInt(pageJump.value);
      if (targetPage >= 1 && targetPage <= totalPages) {
        paginationState.page = targetPage;
        refreshHistory();
      }
    });
  }
}

// Sorting
function updateSortIndicators() {
  const headers = document.querySelectorAll("#history-table th[data-sort]");
  headers.forEach(function(th) {
    th.classList.remove("sort-asc", "sort-desc");
    if (th.dataset.sort === sortColumn) {
      th.classList.add(sortDirection === "asc" ? "sort-asc" : "sort-desc");
    }
  });
}

function handleSort(column) {
  if (sortColumn === column) {
    sortDirection = sortDirection === "asc" ? "desc" : "asc";
  } else {
    sortColumn = column;
    sortDirection = "desc";
  }
  updateSortIndicators();
  refreshHistory();
}

// Render Functions
function renderLatest() {
  if (!latestState) return;

  const agentBadge = document.getElementById("latest-agent");
  if (agentBadge) {
    agentBadge.textContent = latestState.agent || "未知";
    agentBadge.classList.remove("codex", "claude");
    if (latestState.agent) agentBadge.classList.add(latestState.agent.toLowerCase());
  }

  const modelBadge = document.getElementById("latest-model");
  if (modelBadge) modelBadge.textContent = latestState.model || "--";

  const tokenBadge = document.getElementById("latest-tokens");
  if (tokenBadge) {
    const inputTokens = latestState.input_tokens || 0;
    const outputTokens = latestState.output_tokens || 0;
    if (inputTokens > 0 || outputTokens > 0) {
      tokenBadge.textContent = "Token: " + inputTokens + "/" + outputTokens;
    } else {
      tokenBadge.textContent = "Token: --";
    }
  }

  const userInputEl = document.getElementById("latest-user-input");
  if (userInputEl) userInputEl.textContent = latestState.user_input || "(no input)";

  const summaryEl = document.getElementById("latest-summary");
  if (summaryEl) {
    // Apply current mode
    if (responseMode === "raw") {
      summaryEl.classList.add("raw-mode");
      summaryEl.textContent = latestState.summary || "(no response)";
    } else {
      summaryEl.classList.remove("raw-mode");
      summaryEl.innerHTML = markdownToHtml(latestState.summary || "(no response)");
    }
  }

  const timeEl = document.getElementById("latest-time");
  if (timeEl) timeEl.textContent = formatTimestamp(latestState.timestamp);

  const projectEl = document.getElementById("latest-project");
  if (projectEl) projectEl.textContent = latestState.cwd || "/unknown";

  const sessionEl = document.getElementById("latest-session");
  if (sessionEl) {
    const sid = latestState.session_id || "--";
    sessionEl.textContent = "session: " + sid.substring(0, 8) + "...";
  }
}

function renderTable(events) {
  const tbody = document.getElementById("history-body");
  const badge = document.getElementById("history-count");

  if (badge) badge.textContent = paginationState.total + " 条记录";

  if (!events || events.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><span class="loading-text">无记录</span></td></tr>';
    return;
  }

  let html = "";
  events.forEach(function(item, index) {
    const agentClass = (item.agent || "").toLowerCase();
    const time = formatTimestamp(item.timestamp);
    const date = formatDateShort(item.timestamp);
    const autoCategory = item.auto_category || "";

    // Get search term for highlighting
    const searchInput = document.getElementById("search-input");
    const searchTerm = searchInput ? searchInput.value.trim().toLowerCase() : "";

    html += "<tr>";
    html += '<td class="col-time">' + date + " " + time + "</td>";
    html += '<td class="col-agent ' + agentClass + '">' + (item.agent || "-") + "</td>";

    // Model column
    const model = item.model || "--";
    html += '<td class="col-model">' + model + "</td>";

    // Token column
    const inputTokens = item.input_tokens || 0;
    const outputTokens = item.output_tokens || 0;
    const tokenDisplay = inputTokens > 0 || outputTokens > 0 ? inputTokens + "/" + outputTokens : "--";
    html += '<td class="col-tokens">' + tokenDisplay + "</td>";

    // Category column
    const categoryClass = getCategoryClass(autoCategory);
    html += '<td class="col-category">';
    if (autoCategory) {
      html += '<span class="category-badge ' + categoryClass + '">' + autoCategory + '</span>';
    } else {
      html += "-";
    }
    html += "</td>";

    html += '<td class="col-project">' + formatProjectName(item.cwd) + "</td>";

    // User input cell - with copy button and highlight
    const userInputFull = item.user_input || "";
    const userInputDisplay = searchTerm ? highlightText(userInputFull, searchTerm) : truncateText(userInputFull, 50);
    const inputTruncatedClass = isTruncated(userInputFull, 50) ? " truncated-indicator" : "";
    html += '<td class="col-input cell-with-copy' + inputTruncatedClass + '" data-full-content="' + escapeHtml(userInputFull) + '" data-field-type="input" data-event-id="' + item.id + '">';
    html += '<div class="cell-content">' + userInputDisplay + '</div>';
    html += '<button class="cell-copy-btn" data-copy-content="' + escapeHtml(userInputFull) + '" title="复制">⎘</button>';
    html += "</td>";

    // Summary cell - with copy button and highlight
    const summaryFull = item.summary || "";
    const summaryDisplay = searchTerm ? highlightText(summaryFull, searchTerm) : truncateText(summaryFull, 50);
    const summaryTruncatedClass = isTruncated(summaryFull, 50) ? " truncated-indicator" : "";
    html += '<td class="col-summary cell-with-copy' + summaryTruncatedClass + '" data-full-content="' + escapeHtml(summaryFull) + '" data-field-type="summary" data-event-id="' + item.id + '">';
    html += '<div class="cell-content">' + summaryDisplay + '</div>';
    html += '<button class="cell-copy-btn" data-copy-content="' + escapeHtml(summaryFull) + '" title="复制">⎘</button>';
    html += "</td>";

    html += "</tr>";
  });
  tbody.innerHTML = html;

  // Add click handlers to cell content (not the copy button)
  tbody.querySelectorAll(".col-input, .col-summary").forEach(function(cell) {
    cell.querySelector(".cell-content").addEventListener("click", function() {
      showContentModal(cell);
    });
  });

  // Add click handlers to copy buttons
  tbody.querySelectorAll(".cell-copy-btn").forEach(function(btn) {
    btn.addEventListener("click", function(e) {
      e.stopPropagation();
      copyCellContent(btn);
    });
  });
}

// Get category class for styling
function getCategoryClass(category) {
  const categoryMap = {
    "调试": "cat-debug",
    "代码": "cat-code",
    "文档": "cat-docs",
    "阅读": "cat-read",
    "执行": "cat-exec",
    "探索": "cat-explore",
  };
  return categoryMap[category] || "";
}

// Highlight search term in text
function highlightText(text, searchTerm) {
  if (!searchTerm || !text) return truncateText(text, 50);

  const lowerText = text.toLowerCase();
  const lowerSearch = searchTerm.toLowerCase();

  if (!lowerText.includes(lowerSearch)) return truncateText(text, 50);

  // Find the position and show context around it
  const pos = lowerText.indexOf(lowerSearch);
  const start = Math.max(0, pos - 20);
  const end = Math.min(text.length, pos + searchTerm.length + 30);
  const context = text.substring(start, end);

  // Highlight the search term
  const regex = new RegExp("(" + escapeRegex(searchTerm) + ")", "gi");
  const highlighted = context.replace(regex, '<span class="highlight-search">$1</span>');

  return (start > 0 ? "..." : "") + highlighted + (end < text.length ? "..." : "");
}

// Escape regex special characters
function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Escape HTML for data attribute
function escapeHtml(text) {
  if (!text) return "";
  return text.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/'/g, "&#39;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Unescape HTML from data attribute
function unescapeHtml(text) {
  if (!text) return "";
  return text.replace(/&amp;/g, "&").replace(/&quot;/g, "\"").replace(/&#39;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">");
}

// Modal functions
function showContentModal(cell) {
  const fullContent = unescapeHtml(cell.getAttribute("data-full-content") || "");
  const fieldType = cell.getAttribute("data-field-type") || "input";

  if (!fullContent || !isTruncated(fullContent, 50)) {
    return; // Don't show modal if content is not truncated
  }

  const modal = document.getElementById("content-modal");
  const modalTitle = document.getElementById("modal-title");
  const modalLabel = document.getElementById("modal-label");
  const modalContent = document.getElementById("modal-content");

  // Set title based on field type
  if (fieldType === "input") {
    modalTitle.textContent = "用户输入详情";
    modalLabel.textContent = "⟩ 用户输入";
  } else {
    modalTitle.textContent = "回复详情";
    modalLabel.textContent = "⟨ 回复";
  }

  modalContent.textContent = fullContent;
  modal.classList.remove("hidden");

  // Clear status
  const modalStatus = document.getElementById("modal-status");
  modalStatus.textContent = "";
}

function closeModal() {
  const modal = document.getElementById("content-modal");
  modal.classList.add("hidden");
}

function copyModalContent() {
  const modalContent = document.getElementById("modal-content");
  const text = modalContent.textContent || "";

  if (!text) {
    const modalStatus = document.getElementById("modal-status");
    modalStatus.textContent = "NO CONTENT";
    return;
  }

  navigator.clipboard.writeText(text).then(function() {
    const modalStatus = document.getElementById("modal-status");
    modalStatus.textContent = "已复制 ✓";
    setTimeout(function() {
      modalStatus.textContent = "";
    }, 2000);
  }).catch(function(err) {
    const modalStatus = document.getElementById("modal-status");
    modalStatus.textContent = "复制失败";
  });
}

// Copy cell content function
function copyCellContent(btn) {
  const content = unescapeHtml(btn.getAttribute("data-copy-content") || "");

  if (!content) {
    showCopyFeedback(btn, "空");
    return;
  }

  navigator.clipboard.writeText(content).then(function() {
    showCopyFeedback(btn, "✓");
    setTimeout(function() {
      showCopyFeedback(btn, "⎘");
    }, 1500);
  }).catch(function(err) {
    showCopyFeedback(btn, "✕");
    setTimeout(function() {
      showCopyFeedback(btn, "⎘");
    }, 1500);
  });
}

function showCopyFeedback(btn, text) {
  btn.textContent = text;
  if (text === "✓") {
    btn.classList.add("copy-success");
  } else if (text === "✕") {
    btn.classList.add("copy-failed");
  } else {
    btn.classList.remove("copy-success", "copy-failed");
  }
}

// Copy latest card content
function copyLatestContent(type) {
  if (!latestState) {
    return;
  }

  const content = type === "user-input" ? latestState.user_input : latestState.summary;
  const btnId = type === "user-input" ? "copy-user-input" : "copy-response";
  const btn = document.getElementById(btnId);

  if (!content) {
    showCardCopyFeedback(btn, "空");
    setTimeout(function() { showCardCopyFeedback(btn, "⎘"); }, 1500);
    return;
  }

  navigator.clipboard.writeText(content).then(function() {
    showCardCopyFeedback(btn, "✓");
    setTimeout(function() { showCardCopyFeedback(btn, "⎘"); }, 1500);
  }).catch(function(err) {
    showCardCopyFeedback(btn, "✕");
    setTimeout(function() { showCardCopyFeedback(btn, "⎘"); }, 1500);
  });
}

function showCardCopyFeedback(btn, text) {
  btn.textContent = text;
  btn.classList.remove("copy-success");
  if (text === "✓") {
    btn.classList.add("copy-success");
  }
}

// Data Fetching
function fetchJson(url, options) {
  options = options || { method: "GET" };

  if (options.body && typeof options.body === "string") {
    options.headers = { "Content-Type": "application/json" };
  }

  return fetch(url, options).then(function(response) {
    if (!response.ok) {
      return response.json().then(function(data) {
        throw new Error(data.error || "Request failed: " + response.status);
      }).catch(function() {
        throw new Error("Request failed: " + response.status);
      });
    }
    return response.json();
  });
}

function refreshLatest() {
  fetchJson("/api/latest").then(function(data) {
    latestState = data;
    renderLatest();
  }).catch(function(err) {
    console.error("Failed to fetch latest:", err);
  });
}

function refreshHistory() {
  setStatus("加载中...");

  const searchInput = document.getElementById("search-input");
  const timeFilter = document.getElementById("time-filter");
  const agentFilter = document.getElementById("agent-filter");
  const projectFilter = document.getElementById("project-filter");
  const categoryFilter = document.getElementById("category-filter");
  const tagsFilter = document.getElementById("tags-filter");

  const search = searchInput ? searchInput.value.trim() : "";
  const timeDays = timeFilter ? timeFilter.value : "all";
  const agent = agentFilter ? agentFilter.value : "all";
  const project = projectFilter ? projectFilter.value : "all";
  const category = categoryFilter ? categoryFilter.value : "all";
  const tags = tagsFilter ? tagsFilter.value : "all";

  const params = new URLSearchParams({
    page: paginationState.page,
    per_page: paginationState.perPage,
    sort: sortColumn,
    dir: sortDirection,
  });

  if (search) params.set("search", search);
  if (timeDays !== "all") params.set("time_days", timeDays);
  if (agent !== "all") params.set("agent", agent);
  if (project !== "all") params.set("project", project);
  if (category !== "all") params.set("category", category);

  fetchJson("/api/history?" + params.toString()).then(function(data) {
    paginationState = {
      page: data.pagination.page,
      perPage: data.pagination.per_page,
      total: data.pagination.total,
      totalPages: data.pagination.total_pages,
    };
    renderTable(data.events);
    renderPagination();
    updateProjectFilter(data.projects || []);
    updateCategoryFilter(data.categories || []);
    setStatus("");
  }).catch(function(err) {
    console.error("Failed to fetch history:", err);
    setStatus("错误: " + err.message);
  });

  // Update tags filter separately
  refreshTagsFilter();
}

function refreshTagsFilter() {
  fetchJson("/api/tags").then(function(tags) {
    const tagsFilter = document.getElementById("tags-filter");
    if (!tagsFilter) return;

    const currentValue = tagsFilter.value;
    let html = '<option value="all">◈ 全部</option>';

    tags.forEach(function(tag) {
      const selected = tag.id === currentValue ? " selected" : "";
      html += '<option value="' + tag.id + '"' + selected + '>◈ ' + tag.name + ' (' + tag.usage_count + ')</option>';
    });

    tagsFilter.innerHTML = html;
  }).catch(function(err) {
    console.error("Failed to fetch tags:", err);
  });
}

function updateCategoryFilter(categories) {
  const categoryFilter = document.getElementById("category-filter");
  if (!categoryFilter) return;

  const currentValue = categoryFilter.value;
  let html = '<option value="all">◈ 全部</option>';

  categories.forEach(function(cat) {
    const selected = cat === currentValue ? " selected" : "";
    html += '<option value="' + cat + '"' + selected + '>◈ ' + cat + '</option>';
  });

  categoryFilter.innerHTML = html;
}

function updateProjectFilter(projects) {
  const projectFilter = document.getElementById("project-filter");
  if (!projectFilter) return;

  const currentValue = projectFilter.value;
  let html = '<option value="all">◈ 全部</option>';

  projects.forEach(function(project) {
    const selected = project === currentValue ? " selected" : "";
    html += '<option value="' + project + '"' + selected + '>◈ ' + project + '</option>';
  });

  projectFilter.innerHTML = html;
}

function refreshStats() {
  fetchJson("/api/stats").then(function(stats) {
    const el = document.getElementById("stats-info");
    if (el) {
      const agents = stats.agent_counts || {};
      el.textContent = stats.total_events + " events | Claude: " + (agents.claude || 0) + " | Codex: " + (agents.codex || 0);
    }
  }).catch(function(err) {
    console.error("Failed to fetch stats:", err);
  });
}

// Data Management
function toggleAdminPanel() {
  const panel = document.getElementById("admin-panel");
  panel.classList.toggle("hidden");
  if (!panel.classList.contains("hidden")) {
    refreshAdminStats();
  }
}

function refreshAdminStats() {
  fetchJson("/api/stats").then(function(stats) {
    const ds = stats.date_stats || {};
    document.getElementById("stat-7").textContent = ds.last_7_days || 0;
    document.getElementById("stat-30").textContent = ds.last_30_days || 0;
    document.getElementById("stat-90").textContent = ds.last_90_days || 0;
    document.getElementById("stat-365").textContent = ds.last_365_days || 0;
  }).catch(function(err) {
    console.error("Failed to fetch admin stats:", err);
  });
}

// Confirm Modal State
let pendingCleanupDays = null;

// Get time range text
function getCleanupRangeText(days) {
  if (days === "all") {
    return "全部数据";
  } else if (days === "7") {
    return "保留近7天";
  } else if (days === "30") {
    return "保留近30天";
  } else if (days === "90") {
    return "保留近90天";
  } else if (days === "365") {
    return "保留近一年";
  }
  return "保留近" + days + "天";
}

// Get action text
function getCleanupActionText(days) {
  if (days === "all") {
    return "清空全部";
  }
  return "清理旧数据";
}

// Calculate records to delete
function getRecordsToDelete(days) {
  return fetchJson("/api/stats").then(function(stats) {
    const ds = stats.date_stats || {};
    const total = stats.total_events || 0;

    if (days === "all") {
      return {
        toDelete: total,
        toKeep: 0,
        total: total
      };
    }

    // For retention, we keep the specified days
    const keepKey = "last_" + days + "_days";
    const toKeep = ds[keepKey] || 0;

    return {
      toDelete: total - toKeep,
      toKeep: toKeep,
      total: total
    };
  });
}

// Show confirm modal
function showConfirmModal(days) {
  pendingCleanupDays = days;

  const modal = document.getElementById("confirm-modal");
  const countEl = document.getElementById("confirm-count");
  const rangeEl = document.getElementById("confirm-range");
  const actionEl = document.getElementById("confirm-action");
  const warningEl = document.getElementById("confirm-warning-text");

  // Set range and action text
  rangeEl.textContent = getCleanupRangeText(days);
  actionEl.textContent = getCleanupActionText(days);

  // Calculate and show records to delete
  getRecordsToDelete(days).then(function(result) {
    countEl.textContent = result.toDelete + " 条";

    // Update warning text based on operation
    if (days === "all") {
      warningEl.textContent = "将删除全部 " + result.total + " 条记录，此操作不可撤销！";
    } else {
      warningEl.textContent = "将删除 " + result.toDelete + " 条旧记录，保留 " + result.toKeep + " 条近" + days + "天数据";
    }
  }).catch(function(err) {
    countEl.textContent = "--";
    warningEl.textContent = "删除后的数据将无法恢复，请确认是否继续";
  });

  modal.classList.remove("hidden");
}

// Close confirm modal
function closeConfirmModal() {
  const modal = document.getElementById("confirm-modal");
  modal.classList.add("hidden");
  pendingCleanupDays = null;
}

// Perform cleanup after confirmation
function performCleanupConfirmed() {
  if (!pendingCleanupDays) return;

  // Store days value before closing modal (which clears it)
  const daysToClean = pendingCleanupDays;

  const msgEl = document.getElementById("admin-message");
  msgEl.textContent = "处理中...";
  msgEl.className = "admin-message";

  closeConfirmModal();

  let url, options;

  if (daysToClean === "all") {
    url = "/api/clear-all";
    options = { method: "POST" };
  } else {
    url = "/api/cleanup";
    options = {
      method: "POST",
      body: JSON.stringify({ days: parseInt(daysToClean) }),
    };
  }

  fetchJson(url, options).then(function(result) {
    msgEl.textContent = "已删除 " + (result.deleted || 0) + " 条记录，剩余 " + (result.remaining || 0) + " 条";
    msgEl.className = "admin-message success";
    refreshHistory();
    refreshStats();
    refreshAdminStats();
  }).catch(function(err) {
    msgEl.textContent = "错误: " + err.message;
    msgEl.className = "admin-message error";
  });

  pendingCleanupDays = null;
}

// Modified performCleanup - shows confirm modal first
function performCleanup(days) {
  showConfirmModal(days);
}

// Modal event handlers
document.addEventListener("DOMContentLoaded", function() {
  // Filter event handlers
  document.getElementById("time-filter").addEventListener("change", function() {
    paginationState.page = 1;
    refreshHistory();
  });

  document.getElementById("agent-filter").addEventListener("change", function() {
    paginationState.page = 1;
    refreshHistory();
  });

  document.getElementById("project-filter").addEventListener("change", function() {
    paginationState.page = 1;
    refreshHistory();
  });

  document.getElementById("category-filter").addEventListener("change", function() {
    paginationState.page = 1;
    refreshHistory();
  });

  document.getElementById("tags-filter").addEventListener("change", function() {
    paginationState.page = 1;
    refreshHistory();
  });

  document.getElementById("search-input").addEventListener("input", function() {
    paginationState.page = 1;
    refreshHistory();
  });

  document.querySelectorAll("#history-table th[data-sort]").forEach(function(th) {
    th.addEventListener("click", function() {
      handleSort(th.dataset.sort);
    });
  });

  document.getElementById("toggle-admin").addEventListener("click", toggleAdminPanel);

  // Modal event handlers
  document.getElementById("modal-close").addEventListener("click", closeModal);
  document.getElementById("modal-copy").addEventListener("click", copyModalContent);

  // Close modal on overlay click
  document.getElementById("content-modal").addEventListener("click", function(e) {
    if (e.target.id === "content-modal") {
      closeModal();
    }
  });

  // Close modal on Escape key
  document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") {
      const modal = document.getElementById("content-modal");
      if (!modal.classList.contains("hidden")) {
        closeModal();
      }
      const adminPanel = document.getElementById("admin-panel");
      if (!adminPanel.classList.contains("hidden")) {
        toggleAdminPanel();
      }
    }
  });

  // Admin panel close button
  document.getElementById("admin-close").addEventListener("click", toggleAdminPanel);

  // Export panel handlers
  document.getElementById("export-btn").addEventListener("click", toggleExportPanel);
  document.getElementById("export-close").addEventListener("click", toggleExportPanel);
  document.getElementById("export-csv").addEventListener("click", exportCSV);
  document.getElementById("export-json").addEventListener("click", exportJSON);

  // Latest card copy buttons
  document.getElementById("copy-user-input").addEventListener("click", function() {
    copyLatestContent("user-input");
  });
  document.getElementById("copy-response").addEventListener("click", function() {
    copyLatestContent("response");
  });

  // Response toggle buttons
  document.getElementById("toggle-mode").addEventListener("click", toggleResponseMode);
  document.getElementById("toggle-expand").addEventListener("click", showResponseModal);

  // Response view modal handlers
  document.getElementById("response-view-close").addEventListener("click", closeResponseModal);
  document.getElementById("response-view-modal").addEventListener("click", function(e) {
    if (e.target.id === "response-view-modal") {
      closeResponseModal();
    }
  });

  // Modal mode toggle button
  document.getElementById("modal-toggle-mode").addEventListener("click", toggleResponseModeFromModal);

  // Response view copy button
  document.getElementById("response-view-copy").addEventListener("click", function() {
    const content = document.getElementById("response-view-content");
    const text = latestState ? latestState.summary : "";
    const statusEl = document.getElementById("response-view-status");

    if (!text) {
      statusEl.textContent = "无内容";
      setTimeout(function() { statusEl.textContent = ""; }, 2000);
      return;
    }

    navigator.clipboard.writeText(text).then(function() {
      statusEl.textContent = "已复制 ✓";
      setTimeout(function() { statusEl.textContent = ""; }, 2000);
    }).catch(function(err) {
      statusEl.textContent = "复制失败";
    });
  });

  document.querySelectorAll("[data-days]").forEach(function(btn) {
    btn.addEventListener("click", function() {
      performCleanup(btn.dataset.days);
    });
  });

  updateSortIndicators();
  refreshLatest();
  refreshHistory();
  refreshStats();

  // Tag modal event handlers
  document.getElementById("tag-modal-close").addEventListener("click", closeTagModal);
  document.getElementById("save-tags-btn").addEventListener("click", saveEventTags);
  document.getElementById("cancel-tags-btn").addEventListener("click", closeTagModal);
  document.getElementById("add-tag-btn").addEventListener("click", addNewTag);

  // Tag modal overlay click
  document.getElementById("tag-modal").addEventListener("click", function(e) {
    if (e.target.id === "tag-modal") {
      closeTagModal();
    }
  });

  // Add tag on Enter key
  document.getElementById("new-tag-input").addEventListener("keypress", function(e) {
    if (e.key === "Enter") {
      addNewTag();
    }
  });

  // Confirm modal event handlers
  document.getElementById("confirm-cancel").addEventListener("click", closeConfirmModal);
  document.getElementById("confirm-proceed").addEventListener("click", performCleanupConfirmed);

  // Confirm modal overlay click to close
  document.getElementById("confirm-modal").addEventListener("click", function(e) {
    if (e.target.id === "confirm-modal") {
      closeConfirmModal();
    }
  });

  // Escape key to close confirm modal
  document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") {
      const confirmModal = document.getElementById("confirm-modal");
      if (!confirmModal.classList.contains("hidden")) {
        closeConfirmModal();
      }
      const responseModal = document.getElementById("response-view-modal");
      if (!responseModal.classList.contains("hidden")) {
        closeResponseModal();
      }
    }
  });

  setInterval(refreshLatest, 30000);
  setInterval(refreshStats, 60000);
});

// =====================
// Tag Management
// =====================

let currentEventId = "";
let currentEventTags = [];

function openTagModal(eventId) {
  currentEventId = eventId;

  const modal = document.getElementById("tag-modal");
  modal.classList.remove("hidden");

  // Fetch current tags for this event
  fetchJson("/api/events/" + eventId + "/tags").then(function(tags) {
    currentEventTags = tags.map(function(t) { return t.id; });
    renderCurrentTags(tags);
  }).catch(function(err) {
    console.error("Failed to fetch event tags:", err);
    currentEventTags = [];
    renderCurrentTags([]);
  });

  // Fetch popular tags
  fetchJson("/api/tags").then(function(tags) {
    renderPopularTags(tags);
  }).catch(function(err) {
    console.error("Failed to fetch tags:", err);
  });
}

function closeTagModal() {
  const modal = document.getElementById("tag-modal");
  modal.classList.add("hidden");
  currentEventId = "";
  currentEventTags = [];
}

function renderCurrentTags(tags) {
  const container = document.getElementById("current-tags");
  if (!container) return;

  if (tags.length === 0) {
    container.innerHTML = '<span style="color: var(--text-muted);">无标签</span>';
    return;
  }

  let html = "";
  tags.forEach(function(tag) {
    html += '<span class="tag-item" data-tag-id="' + tag.id + '">';
    html += tag.name;
    html += '<span class="tag-remove" onclick="removeTag(\'' + tag.id + '\')">✕</span>';
    html += '</span>';
  });
  container.innerHTML = html;
}

function renderPopularTags(tags) {
  const container = document.getElementById("popular-tags");
  if (!container) return;

  // Show top 10 popular tags
  const popularTags = tags.slice(0, 10);

  let html = "";
  popularTags.forEach(function(tag) {
    const isAdded = currentEventTags.includes(tag.id);
    const addedClass = isAdded ? " added" : "";
    html += '<span class="tag-item popular-tag' + addedClass + '" data-tag-id="' + tag.id + '" onclick="togglePopularTag(\'' + tag.id + '\')">';
    html += tag.name + ' (' + tag.usage_count + ')';
    html += '</span>';
  });
  container.innerHTML = html;
}

function removeTag(tagId) {
  currentEventTags = currentEventTags.filter(function(id) { return id !== tagId; });

  // Re-render current tags
  fetchJson("/api/tags").then(function(allTags) {
    const currentTags = allTags.filter(function(t) { return currentEventTags.includes(t.id); });
    renderCurrentTags(currentTags);
    renderPopularTags(allTags);
  });
}

function togglePopularTag(tagId) {
  if (currentEventTags.includes(tagId)) {
    currentEventTags = currentEventTags.filter(function(id) { return id !== tagId; });
  } else {
    currentEventTags.push(tagId);
  }

  // Re-render
  fetchJson("/api/tags").then(function(allTags) {
    const currentTags = allTags.filter(function(t) { return currentEventTags.includes(t.id); });
    renderCurrentTags(currentTags);
    renderPopularTags(allTags);
  });
}

function addNewTag() {
  const input = document.getElementById("new-tag-input");
  const tagName = input.value.trim();

  if (!tagName) return;

  // Create new tag
  fetchJson("/api/tags", {
    method: "POST",
    body: JSON.stringify({ name: tagName, color: "#7b61ff" })
  }).then(function(newTag) {
    currentEventTags.push(newTag.id);
    input.value = "";

    // Refresh display
    fetchJson("/api/tags").then(function(allTags) {
      const currentTags = allTags.filter(function(t) { return currentEventTags.includes(t.id); });
      renderCurrentTags(currentTags);
      renderPopularTags(allTags);
      refreshTagsFilter();
    });
  }).catch(function(err) {
    console.error("Failed to create tag:", err);
    setStatus("创建标签失败");
  });
}

function saveEventTags() {
  if (!currentEventId) return;

  fetchJson("/api/events/" + currentEventId + "/tags", {
    method: "POST",
    body: JSON.stringify({ tag_ids: currentEventTags })
  }).then(function() {
    closeTagModal();
    refreshHistory();
  }).catch(function(err) {
    console.error("Failed to save tags:", err);
    setStatus("保存标签失败");
  });
}

// =====================
// Export Functions
// =====================

function toggleExportPanel() {
  const panel = document.getElementById("export-panel");
  panel.classList.toggle("hidden");
}

function getExportParams() {
  const timeFilter = document.getElementById("time-filter");
  const agentFilter = document.getElementById("agent-filter");
  const projectFilter = document.getElementById("project-filter");
  const categoryFilter = document.getElementById("category-filter");

  return {
    time_days: timeFilter ? timeFilter.value : "all",
    agent: agentFilter ? agentFilter.value : "all",
    project: projectFilter ? projectFilter.value : "all",
    category: categoryFilter ? categoryFilter.value : "all",
  };
}

function exportCSV() {
  const params = getExportParams();
  const url = new URL("http://localhost:8765/api/export/csv");

  Object.keys(params).forEach(function(key) {
    if (params[key] !== "all") {
      url.searchParams.set(key, params[key]);
    }
  });

  // Trigger download
  const a = document.createElement("a");
  a.href = url.toString();
  a.download = "agent_notify_export.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  const msgEl = document.getElementById("export-message");
  msgEl.textContent = "CSV 导出已开始";
  msgEl.className = "admin-message success";
  setTimeout(function() { msgEl.textContent = ""; }, 3000);
}

function exportJSON() {
  const params = getExportParams();
  const url = new URL("http://localhost:8765/api/export/json");

  Object.keys(params).forEach(function(key) {
    if (params[key] !== "all") {
      url.searchParams.set(key, params[key]);
    }
  });

  // Trigger download
  const a = document.createElement("a");
  a.href = url.toString();
  a.download = "agent_notify_export.json";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  const msgEl = document.getElementById("export-message");
  msgEl.textContent = "JSON 导出已开始";
  msgEl.className = "admin-message success";
  setTimeout(function() { msgEl.textContent = ""; }, 3000);
}