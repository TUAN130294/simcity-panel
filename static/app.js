"use strict";
const $ = (id) => document.getElementById(id);
const jbody = (o) => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(o) });
let settings = {};
let curDir = "", openFilePath = null;
const changes = new Map();   // key `${path}:${line}` -> {path,line,value}

async function api(p, o) { const r = await fetch(p, o); return r.json().catch(() => ({ ok: false, error: "phản hồi lỗi" })); }
function toast(m, k) { const t = $("toast"); t.textContent = m; t.className = "toast " + (k || ""); clearTimeout(t._t); t._t = setTimeout(() => t.classList.add("hidden"), 4500); }
function setConn(s, t) { $("connDot").className = "dot " + s; $("connText").textContent = t; }

/* ---------- settings ---------- */
async function loadSettings() {
  settings = await api("/api/settings");
  ["host", "port", "user", "password", "simcity_path", "server_root", "client_dir", "client_config_ini", "vmx_path", "reload_cmd"]
    .forEach((k) => { const el = $("s_" + k); if (el) el.value = settings[k] ?? ""; });
  $("encoding").value = settings.encoding || "latin-1";
}
async function saveSettings() {
  const p = {}; ["host", "port", "user", "password", "simcity_path", "server_root", "client_dir", "client_config_ini", "vmx_path", "reload_cmd"]
    .forEach((k) => p[k] = $("s_" + k).value); p.encoding = $("encoding").value;
  settings = await api("/api/settings", jbody(p)); $("settingsMsg").textContent = "Đã lưu."; toast("Đã lưu cài đặt", "ok");
}
async function detectServer() {
  const btn = $("btnDetect"), msg = $("settingsMsg");
  btn.disabled = true; btn.textContent = "⏳ Đang dò...";
  msg.textContent = "Đang tìm máy chủ game (đọc config.ini của client, nếu không có thì quét mạng nội bộ — mất tới 30 giây)...";
  try {
    const r = await api("/api/detect", jbody({
      user: $("s_user").value, port: $("s_port").value,
      // mật khẩu chỉ gửi khi người dùng đã gõ thật (dấu ******** = giữ nguyên cái cũ)
      password: $("s_password").value === "********" ? "" : $("s_password").value,
    }));
    if (r.ok && r.found) {
      $("s_host").value = r.host; $("s_port").value = r.port || 22; $("s_user").value = r.user || "root";
      if (r.password) $("s_password").value = r.password;
      if (r.client_config_ini) $("s_client_config_ini").value = r.client_config_ini;
      if (r.client_dir) $("s_client_dir").value = r.client_dir;
      msg.textContent = `✅ Tìm thấy máy chủ ${r.host} (nguồn: ${r.source})` +
        (r.verified ? " — đã đăng nhập thử và thấy thư mục game." : " — CHƯA đăng nhập thử được, kiểm tra lại mật khẩu hoặc máy ảo đã bật chưa.");
      toast(r.verified ? "Đã dò ra server, bấm Lưu để dùng" : "Tìm thấy máy nhưng chưa đăng nhập được", r.verified ? "ok" : "err");
    } else {
      msg.textContent = "❌ " + (r.error || "Không tìm thấy máy chủ nào.");
      toast(r.error || "Không tìm thấy", "err");
    }
  } finally {
    btn.disabled = false; btn.textContent = "🔍 Tự dò server";
  }
}
async function importClientConfig() {
  const r = await api("/api/import-client-config", jbody({ ini_path: $("s_client_config_ini").value }));
  if (r.ok) { settings = r.settings; await loadSettings(); toast("Nhập config.ini OK", "ok"); }
  else toast(r.error, "err");
}
async function testConn() {
  setConn("off", "Đang test..."); const r = await api("/api/test", { method: "POST" });
  if (r.ok) { setConn("on", "Đã kết nối"); toast("Kết nối OK", "ok"); } else { setConn("err", "Lỗi kết nối"); toast(r.error, "err"); }
}
/* ---------- bật/tắt nguồn (máy ảo + game) ---------- */
let powerTimer = null;

function pwPaint(vm, game, note) {
  const setPill = (el, state, txt) => { el.className = "pw-state " + state; el.textContent = txt; };
  setPill($("pwVmState"), vm === true ? "on" : vm === false ? "off" : "unknown",
    vm === true ? "ĐANG BẬT" : vm === false ? "ĐANG TẮT" : "không rõ");
  setPill($("pwGameState"), game === true ? "on" : "off", game === true ? "ĐANG CHẠY" : "ĐANG TẮT");
  $("btnVmStart").disabled = vm === true;
  $("btnVmStop").disabled = vm === false;
  $("btnGameStart").disabled = vm === false || game === true;
  $("btnGameStop").disabled = vm === false || game === false;
  $("btnGameReload").disabled = vm === false;
  if (note) $("powerMsg").textContent = note;
}

async function pwRefresh() {
  const r = await api("/api/power");
  if (!r.ok) { $("powerMsg").textContent = r.error || "Không lấy được trạng thái."; return r; }
  pwPaint(r.vm, r.game, r.vm_note || "");
  // nhịp tim ở thanh trên cùng
  if (r.game) setConn("on", "Game đang chạy");
  else if (r.vm === true) setConn("err", "Máy ảo bật, game chưa chạy");
  else if (r.vm === false) setConn("off", "Máy ảo đang tắt");
  return r;
}

function pwWatch(want, label) {
  // theo dõi tới khi đạt trạng thái mong muốn: want(r) -> true là xong
  clearInterval(powerTimer);
  let tries = 0;
  powerTimer = setInterval(async () => {
    tries++;
    const r = await pwRefresh();
    if (r && r.ok && want(r)) {
      clearInterval(powerTimer); toast(`✅ ${label}`, "ok");
      if (r.game) loadAll();
    } else if (tries >= 40) {   // ~10 phút
      clearInterval(powerTimer);
      toast(`Chờ ${label.toLowerCase()} quá lâu — kiểm tra cửa sổ VMware.`, "err");
    }
  }, 15000);
}

async function vmPower(action) {
  const isStop = action === "stop";
  if (isStop && !confirm("Tắt MÁY ẢO? Toàn bộ server sẽ dừng, người chơi bị ngắt.\n\nApp dùng lệnh tắt sạch bên trong nên an toàn cho dữ liệu.")) return;
  if (!isStop && !confirm("Bật máy ảo? Mất 1–2 phút để hệ điều hành khởi động.")) return;
  $("powerMsg").textContent = isStop ? "Đang gửi lệnh tắt sạch..." : "Đang bật máy ảo...";
  const r = await api("/api/power/vm", jbody({ action }));
  if (!r.ok) { toast(r.error, "err"); $("powerMsg").textContent = "❌ " + r.error; return; }
  const cleared = (r.cleared_locks && r.cleared_locks.length)
    ? ` (đã dọn ${r.cleared_locks.length} khoá cũ do lần trước tắt không sạch)` : "";
  $("powerMsg").textContent = (r.message || "Đã gửi lệnh.") + cleared;
  toast(r.message || "Đã gửi lệnh.", "ok");
  await pwRefresh();
  if (!isStop) pwWatch((x) => x.vm === true, "Máy ảo đã bật — giờ có thể Bật game.");
  else pwWatch((x) => x.vm === false, "Máy ảo đã tắt hẳn.");
}

async function gamePower(action) {
  const label = { start: "Bật game", stop: "Tắt game", reload: "Khởi động lại game" }[action];
  const warn = action === "start" ? "Bật game server? Mất 2–4 phút."
    : action === "stop" ? "TẮT game server? Người chơi sẽ bị ngắt ngay."
      : "Khởi động lại game server? Người chơi bị ngắt vài phút.";
  if (!confirm(warn)) return;
  const r = await api("/api/power/game", jbody({ action }));
  if (!r.ok) { toast(r.error, "err"); $("powerMsg").textContent = "❌ " + r.error; return; }
  $("powerMsg").textContent = `⏳ Đã gửi lệnh "${label}" — đang chạy trong máy ảo, panel sẽ tự báo khi xong.`;
  toast(`⏳ ${label}: đã gửi lệnh, chờ 2–4 phút...`, "");
  if (action === "stop") pwWatch((x) => x.game === false, "Game đã tắt.");
  else pwWatch((x) => x.game === true, "Game đã chạy!");
}

/* ---------- change tracking ---------- */
function ckey(f) { return `${f.path}:${f.line}`; }
function updateChangeCount() {
  const n = changes.size, b = $("changeCount");
  b.textContent = n + " thay đổi"; b.classList.toggle("hidden", n === 0);
  $("btnSave").disabled = n === 0;
}
function markChange(f, row, newVal) {
  const orig = f.value == null ? "" : String(f.value);
  if (String(newVal) !== orig) { changes.set(ckey(f), { path: f.path, line: f.line, value: newVal, label: f.label || f.name || f.key }); row.classList.add("changed"); }
  else { changes.delete(ckey(f)); row.classList.remove("changed"); }
  updateChangeCount();
}

/* ---------- field renderer ---------- */
function makeField(f) {
  const row = document.createElement("div");
  row.className = "field";
  const orig = f.value == null ? "" : String(f.value);
  row.dataset.search = ((f.label || "") + " " + (f.name || f.key || "") + " " + (f.desc || "")).toLowerCase();

  const warn = f.found === false ? ' <span class="f-warn">(không thấy trong file)</span>' : "";
  const top = document.createElement("div"); top.className = "f-top";
  const lab = document.createElement("div"); lab.className = "f-label"; lab.innerHTML = (f.label || f.name) + warn;
  const ctrlWrap = document.createElement("div"); ctrlWrap.className = "f-ctrl";
  top.appendChild(lab); top.appendChild(ctrlWrap);

  const desc = document.createElement("div"); desc.className = "f-desc"; desc.textContent = f.desc || "";
  const meta = document.createElement("div"); meta.className = "f-meta";
  meta.innerHTML = `<code>${f.name || f.key}</code>` + (f.value != null ? ` <span class="f-cur">· hiện tại: ${f.value}</span>` : "");

  const disabled = f.found === false && f.line == null;
  if (f.widget === "toggle") {
    const on = orig !== "" && orig !== "0";
    const sw = document.createElement("label"); sw.className = "switch";
    const inp = document.createElement("input"); inp.type = "checkbox"; inp.checked = on; inp.disabled = disabled;
    const sl = document.createElement("span"); sl.className = "slider";
    const state = document.createElement("span"); state.className = "toggle-state"; state.textContent = on ? "BẬT" : "TẮT";
    sw.appendChild(inp); sw.appendChild(sl);
    inp.onchange = () => { state.textContent = inp.checked ? "BẬT" : "TẮT"; markChange(f, row, inp.checked ? "1" : "0"); };
    ctrlWrap.appendChild(state); ctrlWrap.appendChild(sw);
  } else if (f.widget === "number") {
    const step = f.step || 1;
    const box = document.createElement("div"); box.className = "stepper";
    const minus = document.createElement("button"); minus.textContent = "−";
    const inp = document.createElement("input"); inp.type = "text"; inp.inputMode = "decimal"; inp.value = orig; inp.disabled = disabled;
    const plus = document.createElement("button"); plus.textContent = "+";
    const clamp = (v) => { let n = parseFloat(v); if (isNaN(n)) return v; if (f.min != null) n = Math.max(f.min, n); if (f.max != null) n = Math.min(f.max, n); return String(n); };
    const bump = (d) => { let n = parseFloat(inp.value || "0"); if (isNaN(n)) n = 0; inp.value = clamp(n + d * step); markChange(f, row, inp.value); };
    minus.onclick = () => bump(-1); plus.onclick = () => bump(1);
    inp.oninput = () => markChange(f, row, inp.value);
    inp.onblur = () => { inp.value = clamp(inp.value); markChange(f, row, inp.value); };
    box.appendChild(minus); box.appendChild(inp); box.appendChild(plus);
    ctrlWrap.appendChild(box);
    if (f.unit) { const u = document.createElement("span"); u.className = "unit"; u.textContent = f.unit; ctrlWrap.appendChild(u); }
  } else {
    const inp = document.createElement("input"); inp.type = "text"; inp.value = orig; inp.disabled = disabled;
    inp.oninput = () => markChange(f, row, inp.value);
    ctrlWrap.appendChild(inp);
  }
  row.appendChild(top); row.appendChild(desc); row.appendChild(meta);
  return row;
}
function renderGroup(container, title, note, fields, fileTag) {
  const g = document.createElement("div"); g.className = "group";
  const h = document.createElement("div"); h.className = "group-head";
  h.innerHTML = `<span class="caret">▾</span><span class="group-title">${title}</span>` +
    `<span class="group-count">${fields.length}</span>` +
    (note ? `<span class="group-note">${note}</span>` : "") +
    (fileTag ? `<span class="file-tag">${fileTag}</span>` : "");
  const grid = document.createElement("div"); grid.className = "grid";
  fields.forEach((f) => grid.appendChild(makeField(f)));
  g.appendChild(h); g.appendChild(grid); container.appendChild(g);
  // Cụm gập/mở được: bấm tiêu đề để thu gọn/bung, nhớ trạng thái theo tên nhóm.
  const key = "collapse:" + title;
  const saved = localStorage.getItem(key);
  const defaultCollapsed = title.startsWith("🎪") || title.startsWith("🗂️"); // nhóm ít dùng gập sẵn
  if (saved === "1" || (saved === null && defaultCollapsed)) g.classList.add("collapsed");
  h.onclick = () => {
    g.classList.toggle("collapsed");
    localStorage.setItem(key, g.classList.contains("collapsed") ? "1" : "0");
  };
}

/* ---------- loaders ---------- */
async function loadPanel() {
  setConn("off", "Đang nạp...");
  const enc = $("encoding").value;
  const r = await api("/api/config?encoding=" + enc);
  if (!r.ok) { setConn("err", "Lỗi"); toast(r.error, "err"); return; }
  setConn("on", "Đã kết nối");
  changes.clear(); updateChangeCount();
  const body = $("panelBody"); body.innerHTML = "";
  r.groups.forEach((g) => renderGroup(body, g.title, g.note, g.fields));
  if (r.extras && r.extras.length) renderGroup(body, "🗂️ Khác (chưa gắn nhãn)", "Hằng số khác trong config.lua", r.extras);
  applySearch();
  toast("Đã nạp thông số config.lua", "ok");
}
async function loadServerCfg() {
  const r = await api("/api/server-config?encoding=" + $("encoding").value);
  const body = $("serverBody"); body.innerHTML = "";
  if (!r.ok) { body.innerHTML = `<div class="empty">${r.error}</div>`; return; }
  renderDroprate(body);
  renderSeasonalEvents(body);
  r.sources.forEach((src) => {
    if (src.error) { renderGroup(body, "⚠️ " + src.title, "Không đọc được: " + src.error, []); return; }
    const tag = src.path.split("/").pop();
    src.groups.forEach((g) => renderGroup(body, g.title, g.note, g.fields, tag));
    if (src.extras && src.extras.length) renderGroup(body, src.extras_title || "🗂️ Khác", "", src.extras, tag);
  });
  applySearch();
}

/* ---- hệ số rơi đồ ---- */
async function renderDroprate(container) {
  const wrap = document.createElement("div"); wrap.className = "group";
  wrap.innerHTML = `<div class="group-head"><span class="group-title">🎁 Tỉ lệ rơi đồ (toàn server)</span>
    <span class="group-note">x1 = nguyên bản, x2 = rơi gấp đôi... Áp dụng NGAY vào file, restart để có hiệu lực.</span></div>
    <div class="grid drop-grid"></div>`;
  container.appendChild(wrap);
  const grid = wrap.querySelector(".drop-grid");
  const r = await api("/api/droprate");
  if (!r.ok) { grid.innerHTML = `<div class="empty">${r.error}</div>`; return; }
  r.scopes.forEach((sc) => {
    const card = document.createElement("div"); card.className = "field";
    card.dataset.search = ("rơi đồ drop rate " + sc.title).toLowerCase();
    card.innerHTML = `<div class="f-top"><div class="f-label">${sc.title}</div>
      <div class="f-ctrl"><span class="drop-cur">đang: <b>x${sc.mult}</b></span>
        <input class="drop-inp" type="number" min="0.1" max="50" step="0.5" value="${sc.mult}">
        <button class="btn sm primary drop-apply">Áp dụng</button></div></div>
      <div class="f-desc">Gồm ${sc.files} file bảng rơi đồ. Nhập hệ số rồi bấm Áp dụng (0.5 = rơi ít nửa, 2 = gấp đôi, 1 = trả về gốc).</div>`;
    card.querySelector(".drop-apply").onclick = async () => {
      const mult = parseFloat(card.querySelector(".drop-inp").value);
      if (isNaN(mult)) { toast("Hệ số không hợp lệ", "err"); return; }
      if (!confirm(`Đặt rơi đồ "${sc.title}" thành x${mult}? (tự backup từng file, khôi phục được ở tab Backup)`)) return;
      const res = await api("/api/droprate", jbody({ scope: sc.id, mult }));
      if (res.ok) { toast(`✅ Đã đặt x${mult} — sửa ${res.changed.length} file. Restart server để áp dụng.`, "ok"); card.querySelector(".drop-cur").innerHTML = `đang: <b>x${mult}</b>`; }
      else toast(res.error, "err");
    };
    grid.appendChild(card);
  });
}
/* ---- Event theo mùa (activitysys 2010–2012) ---- */
async function renderSeasonalEvents(container) {
  const wrap = document.createElement("div"); wrap.className = "group";
  wrap.innerHTML = `<div class="group-head"><span class="group-title">🎪 Event theo mùa (2010–2012)</span>
    <span class="group-note">Event trọn gói của bản gốc: bật là có đủ nguồn rơi + NPC + quà (tự vá hạn dùng vật phẩm cũ khi bật).
    Khác với "Sự kiện cổ" ở dưới (chạy qua Túi nguyên liệu). Bật/tắt hay đổi thông số xong phải RESTART server.</span></div>
    <div class="grid se-grid"></div>`;
  container.appendChild(wrap);
  const grid = wrap.querySelector(".se-grid");
  // Máy chủ còn script gốc thì các ô event chưa có tác dụng — mời kích hoạt (panel tự vá, có backup)
  const ps = await api("/api/event-patch");
  if (ps.ok && !ps.ready) {
    const need = ps.files.filter((f) => f.state === "stock").length;
    const unk = ps.files.filter((f) => f.state === "unknown" || f.state === "missing").length;
    const banner = document.createElement("div"); banner.className = "field";
    banner.innerHTML = `<div class="f-top"><div class="f-label">⚙️ Máy chủ này chưa kích hoạt chỉnh event</div>
        <div class="f-ctrl"><button class="btn sm primary se-activate">Kích hoạt ngay</button></div></div>
      <div class="f-desc">Script gốc của game ghi cứng tỉ lệ rơi/thông số event nên panel chưa chỉnh được.
        Bấm Kích hoạt để panel tự sửa ${need} file script (mỗi file đều tự backup — khôi phục được ở tab Backup).${
        unk ? ` Có ${unk} file khác bản gốc sẽ được BỎ QUA để không phá script riêng của bạn.` : ""}
        Kích hoạt xong phải Restart server.</div>`;
    banner.querySelector(".se-activate").onclick = async () => {
      if (!confirm("Panel sẽ sửa các file script event trên máy chủ (tự backup từng file). Tiếp tục?")) return;
      const res = await api("/api/event-patch", jbody({}));
      if (!res.ok) { toast(res.error, "err"); return; }
      toast(`✅ Đã vá ${res.patched.length} file${res.skipped.length ? ", bỏ qua " + res.skipped.length : ""}. Restart server để áp dụng.`, "ok");
      loadServerCfg();  // nạp lại để các ô event hiện giá trị thật
    };
    grid.appendChild(banner);
  }
  const r = await api("/api/seasonal-events");
  if (!r.ok) { grid.innerHTML = `<div class="empty">${r.error}</div>`; return; }
  r.events.forEach((ev) => {
    const card = document.createElement("div"); card.className = "field";
    card.dataset.search = ("event mùa " + ev.name + " " + ev.desc).toLowerCase();
    const knobRows = ev.knobs.map((k) => `
      <div class="f-top se-knob" data-knob="${k.key}">
        <div class="f-label">${k.label}</div>
        <div class="f-ctrl"><input class="se-inp" type="number" min="${k.min}" max="${k.max}" step="${k.step}"
          value="${k.value ?? ""}"><span class="unit">${k.unit}</span>
          <button class="btn sm se-apply">Lưu</button></div>
      </div>
      <div class="f-desc">${k.desc}</div>`).join("");
    card.innerHTML = `<div class="f-top">
        <div class="f-label">${ev.name} <span class="se-state" style="font-weight:bold;color:${ev.active ? "#2e7d32" : "#8d6e63"}">${ev.active ? "ĐANG MỞ" : "ĐANG TẮT"}</span></div>
        <div class="f-ctrl"><button class="btn sm primary se-toggle">${ev.active ? "Tắt event" : "Mở event"}</button></div>
      </div>
      <div class="f-desc">${ev.desc}</div>${knobRows}`;
    let active = ev.active;
    const stateEl = card.querySelector(".se-state"), btn = card.querySelector(".se-toggle");
    btn.onclick = async () => {
      const next = !active;
      if (!confirm(`${next ? "MỞ" : "TẮT"} "${ev.name}"?\n(tự backup file — khôi phục được ở tab Backup; xong phải Restart server)`)) return;
      const res = await api("/api/seasonal-events/toggle", jbody({ key: ev.key, enable: next }));
      if (!res.ok) { toast(res.error, "err"); return; }
      active = next;
      stateEl.textContent = active ? "ĐANG MỞ" : "ĐANG TẮT";
      stateEl.style.color = active ? "#2e7d32" : "#8d6e63";
      btn.textContent = active ? "Tắt event" : "Mở event";
      toast(`✅ Đã ${active ? "mở" : "tắt"} ${ev.name}. Restart server để áp dụng.`, "ok");
    };
    card.querySelectorAll(".se-knob").forEach((row) => {
      row.querySelector(".se-apply").onclick = async () => {
        const val = row.querySelector(".se-inp").value;
        const res = await api("/api/seasonal-events/knob", jbody({ key: ev.key, knob: row.dataset.knob, value: val }));
        if (res.ok) toast(`✅ Đã lưu ${row.querySelector(".f-label").textContent} = ${res.value}. Restart để áp dụng.`, "ok");
        else toast(res.error, "err");
      };
    });
    grid.appendChild(card);
  });
}
async function loadAdvanced() {
  const r = await api("/api/scan");
  const body = $("advancedBody"); body.innerHTML = "";
  if (!r.ok) { body.innerHTML = `<div class="empty">${r.error}</div>`; return; }
  if (!r.groups.length) { body.innerHTML = `<div class="empty">Không tìm thấy hằng số global nào khác.</div>`; return; }
  r.groups.forEach((g) => renderGroup(body, "📄 " + g.file, "", g.fields, g.path.replace(settings.simcity_path, "…")));
  applySearch();
}
/* ---------- data lists ---------- */
async function loadLists() {
  const cat = await api("/api/lists");
  const body = $("listsBody"); body.innerHTML = "";
  if (!cat.ok) { body.innerHTML = `<div class="empty">${cat.error}</div>`; return; }
  // tải song song từng tốp 3 (nhanh hơn tuần tự, không dồn quá nhiều kết nối SSH)
  const metas = cat.lists, datas = [];
  for (let i = 0; i < metas.length; i += 3) {
    const rs = await Promise.all(metas.slice(i, i + 3).map((m) =>
      api("/api/list?id=" + m.id + "&encoding=" + $("encoding").value)));
    datas.push(...rs);
  }
  metas.forEach((meta, i) => body.appendChild(makeListCard(meta, datas[i])));
}
function makeListCard(meta, data) {
  const card = document.createElement("div"); card.className = "list-card"; card.dataset.id = meta.id;
  const items = data.ok ? data.items : [];
  const types = data.types || null;   // null = danh sách 1 cột kiểu cũ
  card.innerHTML = `<div class="list-head">
    <div><div class="list-title">${meta.title}</div><div class="list-desc">${meta.desc}</div></div>
    <span class="list-count">${items.length} dòng</span>
    <div class="list-actions">
      <button class="btn sm add">➕ Thêm dòng</button>
      <button class="btn primary sm save">💾 Lưu danh sách</button>
    </div></div>
    <div class="list-rows"></div>`;
  const rows = card.querySelector(".list-rows");
  if (!data.ok) rows.innerHTML = `<div class="empty">${data.error}</div>`;
  if (data.cols && data.cols.length > 1) {   // bảng nhiều cột: vẽ hàng tiêu đề cột
    const head = document.createElement("div"); head.className = "list-row cols-head";
    head.innerHTML = `<span class="idx"></span>` +
      data.cols.map((c, j) => `<span class="col-label${types[j] === "number" ? " num-col" : ""}">${c}</span>`).join("") +
      `<span class="del-ph"></span>`;
    rows.appendChild(head);
  }
  items.forEach((v) => rows.appendChild(makeListRow(v, types)));
  card.querySelector(".add").onclick = () => {
    const blank = types && types.length > 1 ? Array(types.length).fill("") : "";
    const r = makeListRow(blank, types);
    rows.appendChild(r); r.querySelector("input").focus(); r.classList.add("dirty"); refreshIdx(rows);
  };
  card.querySelector(".save").onclick = () => saveList(meta.id, rows, card);
  refreshIdx(rows);
  return card;
}
function makeListRow(val, types) {
  const row = document.createElement("div"); row.className = "list-row";
  const idx = document.createElement("span"); idx.className = "idx";
  row.appendChild(idx);
  const vals = Array.isArray(val) ? val : [val];
  vals.forEach((v, j) => {
    const inp = document.createElement("input"); inp.value = v;
    if (types && types[j] === "number") inp.classList.add("num-col");
    inp.oninput = () => row.classList.add("dirty");
    row.appendChild(inp);
  });
  const del = document.createElement("button"); del.className = "del"; del.textContent = "🗑"; del.title = "Xoá dòng";
  del.onclick = () => { const rows = row.parentElement; row.remove(); refreshIdx(rows); };
  row.appendChild(del);
  return row;
}
function refreshIdx(rows) { [...rows.querySelectorAll(".list-row:not(.cols-head)")].forEach((r, i) => r.querySelector(".idx").textContent = (i + 1)); }
async function saveList(id, rows, card) {
  const items = [...rows.querySelectorAll(".list-row:not(.cols-head)")].map((r) => {
    const vals = [...r.querySelectorAll("input")].map((i) => i.value);
    return vals.length > 1 ? vals : vals[0];
  }).filter((v) => Array.isArray(v) ? v.some((x) => x.trim() !== "") : (v || "").trim() !== "");
  if (!confirm(`Lưu danh sách này (${items.length} dòng) vào server?`)) return;
  const r = await api("/api/list", jbody({ id, items, encoding: $("encoding").value }));
  if (r.ok) { toast(`Đã lưu ${r.count} dòng (backup .bak)`, "ok"); card.querySelector(".list-count").textContent = r.count + " dòng"; rows.querySelectorAll(".list-row").forEach((x) => x.classList.remove("dirty")); }
  else toast(r.error, "err");
}

async function loadAll() { await loadPanel(); await loadServerCfg(); await loadAdvanced(); await loadLists(); }

async function saveAll() {
  if (!changes.size) { toast("Không có thay đổi", ""); return; }
  const list = Array.from(changes.values());
  if (!confirm(`Lưu ${list.length} thay đổi vào server?`)) return;
  const r = await api("/api/save", jbody({ encoding: $("encoding").value, changes: list }));
  if (r.ok) { toast(`Đã lưu ${r.total} thay đổi (đã backup .bak)`, "ok"); loadAll(); }
  else toast(r.error, "err");
}

/* ---------- guide (mini markdown) ---------- */
function esc(s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
function inlineMd(s) {
  return esc(s).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}
function renderMarkdown(md) {
  const lines = md.split("\n"); let html = ""; let i = 0;
  while (i < lines.length) {
    let ln = lines[i];
    if (ln.startsWith("```")) { let code = ""; i++; while (i < lines.length && !lines[i].startsWith("```")) { code += esc(lines[i]) + "\n"; i++; } i++; html += `<pre><code>${code}</code></pre>`; continue; }
    if (ln.startsWith("### ")) { html += `<h3>${inlineMd(ln.slice(4))}</h3>`; i++; continue; }
    if (ln.startsWith("## ")) { html += `<h2>${inlineMd(ln.slice(3))}</h2>`; i++; continue; }
    if (ln.startsWith("# ")) { html += `<h1>${inlineMd(ln.slice(2))}</h1>`; i++; continue; }
    if (ln.startsWith("> ")) { html += `<blockquote>${inlineMd(ln.slice(2))}</blockquote>`; i++; continue; }
    if (ln.trim().startsWith("|")) { // table
      const rows = []; while (i < lines.length && lines[i].trim().startsWith("|")) { rows.push(lines[i]); i++; }
      const cells = (r) => r.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
      let t = "<table>"; rows.forEach((r, ri) => {
        if (/^[\s|:-]+$/.test(r)) return;
        const tag = ri === 0 ? "th" : "td";
        t += "<tr>" + cells(r).map((c) => `<${tag}>${inlineMd(c)}</${tag}>`).join("") + "</tr>";
      }); t += "</table>"; html += t; continue;
    }
    if (/^\s*[-*] /.test(ln)) { html += "<ul>"; while (i < lines.length && /^\s*[-*] /.test(lines[i])) { html += `<li>${inlineMd(lines[i].replace(/^\s*[-*] /, ""))}</li>`; i++; } html += "</ul>"; continue; }
    if (/^\s*\d+\. /.test(ln)) { html += "<ol>"; while (i < lines.length && /^\s*\d+\. /.test(lines[i])) { html += `<li>${inlineMd(lines[i].replace(/^\s*\d+\. /, ""))}</li>`; i++; } html += "</ol>"; continue; }
    if (ln.trim() === "") { i++; continue; }
    html += `<p>${inlineMd(ln)}</p>`; i++;
  }
  return html;
}
async function loadGuide() {
  const r = await api("/api/guide");
  $("guideBody").innerHTML = r.ok ? renderMarkdown(r.md) : `<div class="empty">${r.error}</div>`;
}

/* ---------- backups ---------- */
async function loadBackups() {
  const body = $("backupsBody"); body.innerHTML = `<div class="empty">Đang tải lịch sử backup...</div>`;
  const r = await api("/api/backups");
  if (!r.ok) { body.innerHTML = `<div class="empty">${r.error}</div>`; return; }
  if (!r.backups.length) { body.innerHTML = `<div class="empty">Chưa có bản backup nào — sẽ tự xuất hiện sau lần Lưu đầu tiên.</div>`; return; }
  body.innerHTML = "";
  r.backups.forEach((b) => {
    const row = document.createElement("div"); row.className = "bk-row";
    const file = b.path.split("/").pop();
    row.innerHTML = `<div class="bk-time">${b.ts}</div>
      <div class="bk-main"><div class="bk-desc"></div><div class="bk-file">📄 ${file} <span class="bk-path">${b.path}</span></div></div>
      <button class="btn sm bk-restore">↩ Khôi phục</button>`;
    row.querySelector(".bk-desc").textContent = b.desc || "(không có mô tả)";
    row.querySelector(".bk-restore").onclick = async () => {
      if (!confirm(`Khôi phục "${file}" về bản lúc ${b.ts}?\n(${b.desc})\n\nBản hiện tại sẽ được tự chụp lại trước, không mất gì. Khôi phục xong cần Restart server.`)) return;
      const res = await api("/api/restore", jbody({ id: b.id }));
      if (res.ok) { toast(`✅ Đã khôi phục ${file} về bản ${b.ts} — bấm Restart server để áp dụng.`, "ok"); loadBackups(); }
      else toast(res.error, "err");
    };
    body.appendChild(row);
  });
}

/* ---------- search ---------- */
function applySearch() {
  const q = $("search").value.trim().toLowerCase();
  document.body.classList.toggle("searching", !!q); // đang tìm: tạm bung mọi cụm đã gập
  document.querySelectorAll(".field").forEach((el) => el.classList.toggle("hide", q && !el.dataset.search.includes(q)));
  // ẩn luôn cụm không có kết quả nào khi đang tìm
  document.querySelectorAll(".group").forEach((g) => {
    const any = g.querySelector(".field:not(.hide)");
    g.classList.toggle("hide", !!q && !any);
  });
}

/* ---------- raw editor ---------- */
async function openDir(path) {
  const r = await api("/api/tree" + (path ? "?path=" + encodeURIComponent(path) : ""));
  if (!r.ok) { toast(r.error, "err"); return; }
  setConn("on", "Đã kết nối"); curDir = r.path; $("curPath").textContent = r.path;
  const ul = $("treeList"); ul.innerHTML = "";
  r.entries.forEach((e) => { const li = document.createElement("li"); li.className = e.is_dir ? "is-dir" : "is-file";
    li.innerHTML = `<span>${e.is_dir ? "📁" : "📄"} ${e.name}</span>`; li.onclick = () => e.is_dir ? openDir(e.path) : openFile(e.path); ul.appendChild(li); });
}
const parentDir = (p) => { const i = p.replace(/\/+$/, "").lastIndexOf("/"); return i > 0 ? p.slice(0, i) : p; };
let openFileViet = false; // file đang mở có được chuyển TCVN3->Unicode không
async function openFile(path) {
  const viet = $("chkViet").checked ? "1" : "0";
  const r = await api("/api/file?path=" + encodeURIComponent(path) + "&encoding=" + $("encoding").value + "&viet=" + viet);
  if (!r.ok) { toast(r.error, "err"); return; }
  openFilePath = path; openFileViet = !!r.viet;
  $("openPath").textContent = path; $("code").value = r.content; $("btnSaveFile").disabled = false;
}
async function saveFile() {
  if (!openFilePath) return;
  const r = await api("/api/file", jbody({ path: openFilePath, content: $("code").value, encoding: $("encoding").value, viet: openFileViet }));
  toast(r.ok ? "Đã lưu (backup .bak)" : r.error, r.ok ? "ok" : "err");
}

/* ---------- tabs ---------- */
function switchTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".pane").forEach((p) => p.classList.toggle("active", p.id === "tab-" + name));
  const showTool = ["panel", "server", "advanced", "lists"].includes(name);
  document.querySelector(".toolbar").style.display = showTool ? "flex" : "none";
  if (name === "editor" && !curDir) openDir(settings.simcity_path);
  if (name === "backups") loadBackups();
  if (name === "guide" && !$("guideBody").dataset.loaded) { $("guideBody").dataset.loaded = "1"; loadGuide(); }
}

/* ---- kiểm tra bản mới trên GitHub ---- */
async function checkForUpdate() {
  try {
    const r = await api("/api/version");
    if (!r.ok || !r.update_available) return;
    if (sessionStorage.getItem("upd-dismissed") === r.latest) return; // đã bấm "Để sau" trong phiên này
    const ov = document.createElement("div");
    ov.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:9999;display:flex;align-items:center;justify-content:center";
    ov.innerHTML = `<div style="background:#f5ead3;color:#3a2c1a;border:2px solid #8d6e63;border-radius:10px;max-width:420px;padding:22px 26px;box-shadow:0 8px 30px rgba(0,0,0,.4);font-size:15px">
        <div style="font-size:17px;font-weight:bold;margin-bottom:10px">🔔 Đã có bản mới ${r.latest}</div>
        <div style="margin-bottom:16px">Bạn đang dùng bản ${r.current}. Cập nhật mất ~10 giây, panel sẽ tự khởi động lại, cài đặt kết nối được giữ nguyên.</div>
        <div style="display:flex;gap:10px;justify-content:flex-end">
          <button class="btn sm" id="updLater">Để sau</button>
          <button class="btn sm primary" id="updNow">Cập nhật ngay</button>
        </div></div>`;
    document.body.appendChild(ov);
    ov.querySelector("#updLater").onclick = () => { sessionStorage.setItem("upd-dismissed", r.latest); ov.remove(); };
    ov.querySelector("#updNow").onclick = async () => {
      const btn = ov.querySelector("#updNow");
      btn.disabled = true; btn.textContent = "Đang cập nhật…";
      const res = await api("/api/update", jbody({}));
      if (!res.ok) { toast(res.error, "err"); btn.disabled = false; btn.textContent = "Cập nhật ngay"; return; }
      btn.textContent = "Đang khởi động lại…";
      // panel thoát rồi tự mở lại — chờ nó lên rồi tải lại trang
      const t0 = Date.now();
      const poll = async () => {
        try {
          const chk = await fetch("/api/version", { cache: "no-store" });
          if (chk.ok) { location.reload(); return; }
        } catch (e) { /* chưa lên lại — thử tiếp */ }
        if (Date.now() - t0 < 90000) setTimeout(poll, 1500);
        else { btn.textContent = "Chưa thấy panel lên lại — thử bấm shortcut SimCity Panel"; }
      };
      setTimeout(poll, 5000);
    };
  } catch (e) { /* offline hoặc lỗi mạng: im lặng, không làm phiền */ }
}

window.addEventListener("DOMContentLoaded", async () => {
  await loadSettings();
  checkForUpdate();
  $("btnSettings").onclick = () => $("settingsModal").classList.remove("hidden");
  $("btnCloseSettings").onclick = () => $("settingsModal").classList.add("hidden");
  $("btnSaveSettings").onclick = saveSettings;
  $("btnDetect").onclick = detectServer;
  $("btnImport").onclick = importClientConfig;
  $("btnTest").onclick = testConn;
  $("btnPower").onclick = () => { $("powerModal").classList.remove("hidden"); pwRefresh(); };
  $("btnClosePower").onclick = () => { $("powerModal").classList.add("hidden"); clearInterval(powerTimer); };
  $("btnVmStart").onclick = () => vmPower("start");
  $("btnVmStop").onclick = () => vmPower("stop");
  $("btnGameStart").onclick = () => gamePower("start");
  $("btnGameStop").onclick = () => gamePower("stop");
  $("btnGameReload").onclick = () => gamePower("reload");
  $("btnLoad").onclick = loadAll;
  $("btnSave").onclick = saveAll;
  $("search").oninput = applySearch;
  $("btnUp").onclick = () => openDir(parentDir(curDir));
  $("btnHome").onclick = () => openDir(settings.simcity_path);
  $("btnSaveFile").onclick = saveFile;
  $("chkViet").onchange = () => { if (openFilePath) openFile(openFilePath); }; // nạp lại file theo chế độ hiển thị mới
  document.querySelectorAll(".tab").forEach((t) => (t.onclick = () => switchTab(t.dataset.tab)));
  $("code").addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); saveFile(); } });
  window.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "s" && !$("tab-editor").classList.contains("active")) { e.preventDefault(); saveAll(); } });

  // Chạy lần đầu (chưa có IP máy chủ): mở cài đặt và tự dò giúp người dùng.
  if (!settings.host) {
    $("settingsModal").classList.remove("hidden");
    setConn("off", "Chưa cài đặt");
    $("settingsMsg").textContent = "Chào mừng! Bấm 🔍 Tự dò server để app tìm máy chủ game giúp bạn.";
    detectServer();
    return;
  }
  loadAll();
});
