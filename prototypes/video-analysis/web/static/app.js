const state = { projectId: localStorage.getItem("yujiProjectId"), project: null, timer: null };
const $ = (selector) => document.querySelector(selector);

function formatTime(seconds) {
  const value = Number(seconds || 0);
  const minutes = Math.floor(value / 60);
  const rest = (value % 60).toFixed(3).padStart(6, "0");
  return `${String(minutes).padStart(2, "0")}:${rest}`;
}

async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let message = `请求失败（${response.status}）`;
    try { message = (await response.json()).detail || message; } catch (_) {}
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

function showWorkspace(show) {
  $("#uploadSection").classList.toggle("hidden", show);
  $("#workspace").classList.toggle("hidden", !show);
}

async function loadProject() {
  if (!state.projectId) return;
  try {
    const project = await api(`/api/projects/${state.projectId}`);
    state.project = project;
    renderProject(project);
    if (["queued", "processing"].includes(project.status)) schedulePoll();
    if (project.status === "review") await loadReview();
  } catch (error) {
    localStorage.removeItem("yujiProjectId");
    state.projectId = null;
    showWorkspace(false);
  }
}

function renderProject(project) {
  showWorkspace(true);
  $("#projectName").textContent = project.filename;
  $("#stageText").textContent = project.stage;
  $("#progressText").textContent = `${project.progress || 0}%`;
  $("#progressBar").style.width = `${project.progress || 0}%`;
  $("#statusHint").textContent = project.error || (project.status === "review" ? "算法候选已生成，请逐个确认真实边界。" : "处理在本机后台运行，可以保持页面打开。当前一次只处理一个视频。");
  $("#retryButton").classList.toggle("hidden", project.status !== "failed");
  $("#reviewArea").classList.toggle("hidden", project.status !== "review");
}

function schedulePoll() {
  clearTimeout(state.timer);
  state.timer = setTimeout(async () => {
    await loadProject();
  }, 2000);
}

async function loadReview() {
  const [candidates, rallies] = await Promise.all([
    api(`/api/projects/${state.projectId}/candidates`),
    api(`/api/projects/${state.projectId}/rallies`),
  ]);
  const player = $("#player");
  if (player.src !== new URL(state.project.marked_video_url, location.href).href) {
    player.src = state.project.marked_video_url;
  }
  $("#sourceLink").href = state.project.source_url;
  const warnings = state.project.warnings || [];
  $("#warnings").classList.toggle("hidden", warnings.length === 0);
  $("#warnings").textContent = warnings.join("；");
  renderCandidates(candidates.filter((item) => !item.is_complete_rally));
  renderRallies(rallies);
}

function candidatePayload(card) {
  const landing = card.querySelector(".landing-time").value;
  const shotCount = null;
  return {
    serve_time: Number(card.querySelector(".serve-time").value),
    landing_time: landing === "" ? null : Number(landing),
    landing_evidence: card.querySelector(".evidence").value.trim(),
    shot_count: shotCount,
    shot_count_status: "无法计拍",
  };
}

function renderCandidates(candidates) {
  const list = $("#candidateList");
  list.innerHTML = "";
  $("#candidateCount").textContent = candidates.length;
  const template = $("#candidateTemplate");
  candidates.forEach((candidate) => {
    const card = template.content.firstElementChild.cloneNode(true);
    card.dataset.id = candidate.id;
    const preview = card.querySelector(".candidate-preview");
    preview.textContent = `候选 ${String(candidate.id).padStart(2, "0")} · ${formatTime(candidate.candidate_start)}—${formatTime(candidate.candidate_end)}`;
    card.querySelector(".serve-time").value = candidate.serve_time ?? candidate.candidate_start;
    card.querySelector(".landing-time").value = candidate.landing_time ?? "";
    card.querySelector(".evidence").value = candidate.landing_evidence || "";
    preview.addEventListener("click", () => {
      $("#player").currentTime = candidate.candidate_start;
      $("#player").play();
    });
    card.querySelector(".serve-current").addEventListener("click", () => {
      card.querySelector(".serve-time").value = $("#player").currentTime.toFixed(2);
    });
    card.querySelector(".landing-current").addEventListener("click", () => {
      card.querySelector(".landing-time").value = $("#player").currentTime.toFixed(2);
    });
    card.querySelector(".save-candidate").addEventListener("click", () => saveCandidate(card));
    card.querySelector(".confirm-candidate").addEventListener("click", () => confirmCandidate(card));
    card.querySelector(".delete-candidate").addEventListener("click", () => deleteCandidate(card));
    list.appendChild(card);
  });
  if (!candidates.length) list.innerHTML = '<p class="rule">没有待确认候选。</p>';
}

async function saveCandidate(card) {
  const message = card.querySelector(".card-message");
  try {
    await api(`/api/projects/${state.projectId}/candidates/${card.dataset.id}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(candidatePayload(card)),
    });
    message.textContent = "边界已保存";
  } catch (error) {
    message.textContent = error.message;
    throw error;
  }
}

async function confirmCandidate(card) {
  const message = card.querySelector(".card-message");
  try {
    await saveCandidate(card);
    await api(`/api/projects/${state.projectId}/candidates/${card.dataset.id}/confirm`, { method: "POST" });
    await loadReview();
  } catch (error) { message.textContent = error.message; }
}

async function deleteCandidate(card) {
  if (!confirm("删除这个误识别候选？")) return;
  await api(`/api/projects/${state.projectId}/candidates/${card.dataset.id}`, { method: "DELETE" });
  await loadReview();
}

function renderRallies(rallies) {
  const section = $("#rallySection");
  const list = $("#rallyList");
  section.classList.toggle("hidden", rallies.length === 0);
  $("#rallyCount").textContent = rallies.length;
  list.innerHTML = rallies.map((rally) => `
    <article class="rally-card">
      <strong>严格回合 ${String(rally.rally_id).padStart(3, "0")}</strong>
      <p>${formatTime(rally.serve_time)} → ${formatTime(rally.landing_time)}</p>
      <p>${rally.landing_evidence}</p>
      <div class="downloads">
        <a class="text-link" href="${rally.marked_video_url}" target="_blank">标记版</a>
        <a class="text-link" href="${rally.original_video_url}" target="_blank">原画质版</a>
      </div>
    </article>`).join("");
}

$("#videoInput").addEventListener("change", (event) => {
  $("#fileLabel").textContent = event.target.files[0]?.name || "选择 MP4、MOV 或手机视频";
});

$("#uploadForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = $("#videoInput").files[0];
  if (!file) return;
  const body = new FormData(); body.append("video", file);
  $("#fileLabel").textContent = "正在复制视频到本机项目目录…";
  try {
    const project = await api("/api/projects", { method: "POST", body });
    state.projectId = project.id;
    localStorage.setItem("yujiProjectId", project.id);
    await loadProject();
  } catch (error) { $("#fileLabel").textContent = error.message; }
});

$("#newProject").addEventListener("click", () => {
  clearTimeout(state.timer); localStorage.removeItem("yujiProjectId"); location.reload();
});
$("#retryButton").addEventListener("click", async () => {
  await api(`/api/projects/${state.projectId}/retry`, { method: "POST" }); await loadProject();
});
$("#player").addEventListener("timeupdate", () => { $("#currentTime").textContent = formatTime($("#player").currentTime); });
document.querySelectorAll("[data-step]").forEach((button) => button.addEventListener("click", () => {
  $("#player").currentTime = Math.max(0, $("#player").currentTime + Number(button.dataset.step));
}));
$("#playbackRate").addEventListener("change", (event) => { $("#player").playbackRate = Number(event.target.value); });

loadProject();
