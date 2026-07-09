(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const NS = "http://www.w3.org/2000/svg";

  const fmtMoney = (v) => Math.round(v).toLocaleString("fr-FR") + " FCFA";
  const fmtMoneyCompact = (v) => {
    const abs = Math.abs(v);
    if (abs >= 1000) return (v / 1000).toFixed(0) + "k";
    return String(Math.round(v));
  };
  const fmtDate = (iso) => new Date(iso + "T00:00:00").toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" });
  const fmtDateShort = (iso) => new Date(iso + "T00:00:00").toLocaleDateString("fr-FR", { day: "numeric", month: "short" });

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function svgEl(tag, attrs) {
    const el = document.createElementNS(NS, tag);
    for (const k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  }

  // ---------------------------------------------------------------
  // Session state — rebuilt every time new simulation data arrives
  // (initial load, or after a "Lancer une nouvelle simulation" run).
  // ---------------------------------------------------------------
  let S = null;

  function makeChart(svg, { series, yDomain, yTicks, height, area, yTickFormat }) {
    yTickFormat = yTickFormat || ((v) => v);
    const { days, maxDay } = S;
    const W = 960, H = height, M = { l: 40, r: 10, t: 10, b: 26 };
    const innerW = W - M.l - M.r, innerH = H - M.t - M.b;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.innerHTML = "";

    const x = (d) => M.l + (d / maxDay) * innerW;
    const y = (v) => M.t + innerH - ((v - yDomain[0]) / (yDomain[1] - yDomain[0])) * innerH;

    yTicks.forEach((t) => {
      svg.appendChild(svgEl("line", { x1: M.l, x2: W - M.r, y1: y(t), y2: y(t), stroke: "var(--grid)", "stroke-width": 1 }));
      const label = svgEl("text", { x: M.l - 8, y: y(t) + 3, "text-anchor": "end" });
      label.setAttribute("style", "font-size:10px;fill:var(--ink-muted)");
      label.textContent = yTickFormat(t);
      svg.appendChild(label);
    });
    svg.appendChild(svgEl("line", { x1: M.l, x2: W - M.r, y1: y(yDomain[0]), y2: y(yDomain[0]), stroke: "var(--line)", "stroke-width": 1 }));

    let lastMonth = null;
    days.forEach((d, i) => {
      const m = d.date.slice(0, 7);
      if (m !== lastMonth) {
        lastMonth = m;
        const lx = x(i);
        const lbl = svgEl("text", { x: lx, y: H - 6, "text-anchor": "start" });
        lbl.setAttribute("style", "font-size:10px;fill:var(--ink-muted)");
        lbl.textContent = new Date(d.date + "T00:00:00").toLocaleDateString("fr-FR", { month: "short" });
        svg.appendChild(lbl);
        svg.appendChild(svgEl("line", { x1: lx, x2: lx, y1: M.t, y2: H - M.b, stroke: "var(--grid)", "stroke-width": 1 }));
      }
    });

    const chartSeries = series.map((s) => {
      const pts = days.map((d, i) => [x(i), y(s.get(d))]);
      const g = svgEl("g", {});
      let areaPath = null;
      if (area) {
        areaPath = svgEl("path", { fill: s.color, opacity: 0.10 });
        g.appendChild(areaPath);
      }
      const pastPath = svgEl("path", { fill: "none", stroke: s.color, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" });
      const futurePath = svgEl("path", { fill: "none", stroke: s.color, "stroke-width": 2, opacity: 0.25, "stroke-linejoin": "round", "stroke-linecap": "round" });
      g.appendChild(futurePath);
      g.appendChild(pastPath);
      const dot = svgEl("circle", { r: 4.5, fill: s.color, stroke: "var(--surface-1)", "stroke-width": 2 });
      g.appendChild(dot);
      svg.appendChild(g);
      return { ...s, pts, pastPath, futurePath, areaPath, dot };
    });

    const playhead = svgEl("line", { x1: M.l, x2: M.l, y1: M.t, y2: H - M.b, stroke: "var(--ink-muted)", "stroke-width": 1, "stroke-dasharray": "3,3" });
    svg.appendChild(playhead);

    const hitRect = svgEl("rect", { x: M.l, y: M.t, width: innerW, height: innerH, fill: "transparent", cursor: "crosshair" });
    svg.appendChild(hitRect);

    function pathFrom(pts) {
      if (!pts.length) return "";
      return "M" + pts.map((p) => p[0].toFixed(1) + "," + p[1].toFixed(1)).join("L");
    }

    function update(dayIndex) {
      const px = x(dayIndex);
      playhead.setAttribute("x1", px);
      playhead.setAttribute("x2", px);
      chartSeries.forEach((s) => {
        const past = s.pts.slice(0, dayIndex + 1);
        const future = s.pts.slice(dayIndex);
        s.pastPath.setAttribute("d", pathFrom(past));
        s.futurePath.setAttribute("d", pathFrom(future));
        if (s.areaPath) {
          if (past.length) {
            const base = y(yDomain[0]);
            s.areaPath.setAttribute("d", pathFrom(past) + `L${past[past.length - 1][0].toFixed(1)},${base}L${past[0][0].toFixed(1)},${base}Z`);
          } else {
            s.areaPath.setAttribute("d", "");
          }
        }
        const cur = s.pts[dayIndex];
        s.dot.setAttribute("cx", cur[0]);
        s.dot.setAttribute("cy", cur[1]);
      });
    }

    return { x, y, innerX0: M.l, innerX1: W - M.r, hitRect, series: chartSeries, update };
  }

  function attachHover(chart, svg, tooltipEl, container) {
    let dragging = false;
    function dayFromEvent(evt) {
      const rect = svg.getBoundingClientRect();
      const scaleX = 960 / rect.width;
      const px = (evt.clientX - rect.left) * scaleX;
      const ratio = (px - chart.innerX0) / (chart.innerX1 - chart.innerX0);
      return Math.max(0, Math.min(S.maxDay, Math.round(ratio * S.maxDay)));
    }
    function showTooltip(dayIndex) {
      const d = S.days[dayIndex];
      const rows = chart.series.map((s) => `<div class="tt-row"><span class="tt-key" style="background:${s.color}"></span><span class="tt-val">${s.fmt ? s.fmt(s.get(d)) : s.get(d)}</span><span class="tt-label">${s.label}</span></div>`).join("");
      tooltipEl.innerHTML = `<span class="tt-date">${fmtDate(d.date)}</span>${rows}`;
      const wrapRect = container.getBoundingClientRect();
      const svgRect = svg.getBoundingClientRect();
      const relX = svgRect.left - wrapRect.left + (chart.x(dayIndex) / 960) * svgRect.width;
      tooltipEl.style.left = relX + "px";
      tooltipEl.style.top = (svgRect.top - wrapRect.top) + "px";
      tooltipEl.classList.add("visible");
    }
    svg.addEventListener("pointermove", (evt) => {
      const d = dayFromEvent(evt);
      showTooltip(d);
      if (dragging) setDay(d);
    });
    svg.addEventListener("pointerleave", () => tooltipEl.classList.remove("visible"));
    svg.addEventListener("pointerdown", (evt) => { dragging = true; pause(); setDay(dayFromEvent(evt)); });
    window.addEventListener("pointerup", () => { dragging = false; });
  }

  // ---------------------------------------------------------------
  // Rendering for the current day
  // ---------------------------------------------------------------
  function renderNow(d) {
    $("date-readout").textContent = fmtDate(d.date);
    $("day-readout").textContent = `Jour ${d.d} / ${S.maxDay}`;
    $("now-action").textContent = d.action_label || "—";
    $("now-desire").textContent = d.desire_label ? `Motivé par : ${d.desire_label}` : "";

    const tiles = [
      { label: "Argent", value: fmtMoney(d.money) },
      { label: "Santé", value: d.health.toFixed(0) },
      { label: "Stress", value: d.stress.toFixed(0) },
      { label: "Fatigue", value: d.fatigue.toFixed(0) },
      { label: "Moral", value: d.moral.toFixed(0) },
      { label: "Faim", value: d.hunger.toFixed(0) },
      { label: "Dette de sommeil", value: d.sleep_debt.toFixed(1) + " h" },
      { label: "Emploi", value: d.job_status === "employed" ? "En poste" : "Sans emploi", jobClass: d.job_status !== "employed" ? "job-unemployed" : "" },
    ];
    $("stat-grid").innerHTML = tiles.map((t) => `<div class="stat-tile"><div class="st-label">${t.label}</div><div class="st-value ${t.jobClass || ""}">${t.value}</div></div>`).join("");
    $("money-note").textContent = fmtMoney(d.money);
  }

  function renderEventList(dayIndex) {
    const visible = S.DATA.events.filter((e) => e.d <= dayIndex);
    $("event-list").innerHTML = visible.slice(-40).reverse().map((e) => `<li><span class="ev-dot sev-${e.severity}"></span><span class="ev-body"><span class="ev-date">${fmtDateShort(S.days[e.d].date)}</span><span class="ev-desc">${escapeHtml(e.description)}</span></span></li>`).join("");
  }

  function renderExamList(dayIndex) {
    $("exam-list").innerHTML = S.DATA.exams.map((x) => {
      const revealed = x.d <= dayIndex;
      const chip = !revealed ? `<span class="exam-chip pending">à venir</span>` : (x.passed ? `<span class="exam-chip pass">réussi</span>` : `<span class="exam-chip fail">échoué</span>`);
      const cls = revealed ? "" : "exam-pending";
      const scoreText = revealed ? `score ${x.score.toFixed(1)}` : "en attente";
      return `<li class="${cls}"><span class="ev-body"><span class="ev-date">${fmtDateShort(x.date)} — ${escapeHtml(x.subject)}</span><span class="ev-desc">${scoreText}${chip}</span></span></li>`;
    }).join("");
  }

  function renderAllocation(dayIndex) {
    const totals = {};
    let grand = 0;
    S.DATA.meta.categories.forEach((c) => (totals[c.key] = 0));
    for (let i = 0; i <= dayIndex; i++) {
      const h = S.days[i].hours;
      S.DATA.meta.categories.forEach((c) => { totals[c.key] += h[c.key] || 0; grand += h[c.key] || 0; });
    }
    S.allocationBar.querySelectorAll(".allocation-seg").forEach((seg) => {
      const pct = grand > 0 ? (totals[seg.dataset.key] / grand) * 100 : 0;
      seg.style.width = pct + "%";
    });
    $("allocation-total").textContent = Math.round(grand) + " h cumulées";
  }

  function setDay(dayIndex) {
    S.currentDay = Math.max(0, Math.min(S.maxDay, dayIndex));
    const d = S.days[S.currentDay];
    S.scrubber.value = String(S.currentDay);
    renderNow(d);
    renderEventList(S.currentDay);
    renderExamList(S.currentDay);
    renderAllocation(S.currentDay);
    S.moneyChart.update(S.currentDay);
    S.vitalsChart.update(S.currentDay);
    S.academicChart.update(S.currentDay);
  }

  function play() {
    if (!S) return;
    if (S.currentDay >= S.maxDay) setDay(0);
    $("play-icon").style.display = "none";
    $("pause-icon").style.display = "";
    $("play-btn").setAttribute("aria-label", "Pause");
    const speed = Number($("speed").value);
    S.timer = setInterval(() => {
      if (S.currentDay >= S.maxDay) { pause(); return; }
      setDay(S.currentDay + 1);
    }, speed);
  }
  function pause() {
    if (!S) return;
    if (S.timer) clearInterval(S.timer);
    S.timer = null;
    $("play-icon").style.display = "";
    $("pause-icon").style.display = "none";
    $("play-btn").setAttribute("aria-label", "Lecture");
  }

  // ---------------------------------------------------------------
  // (Re)build the whole dashboard from a fresh data payload.
  // ---------------------------------------------------------------
  function initApp(DATA) {
    pause();

    const days = DATA.days;
    const maxDay = days.length - 1;
    S = { DATA, days, maxDay, currentDay: 0, timer: null, scrubber: $("scrubber"), allocationBar: $("allocation-bar") };

    ["vitals-legend", "academic-legend", "allocation-legend", "event-track", "event-list", "exam-list"].forEach((id) => ($(id).innerHTML = ""));
    S.allocationBar.innerHTML = "";
    S.scrubber.max = String(maxDay);
    S.scrubber.value = "0";

    const moneyValues = days.map((d) => d.money);
    const moneyMin = Math.min(0, ...moneyValues), moneyMax = Math.max(...moneyValues);
    const moneyPad = (moneyMax - moneyMin) * 0.12 || 1000;
    const moneyDomain = [Math.floor((moneyMin - moneyPad) / 5000) * 5000, Math.ceil((moneyMax + moneyPad) / 5000) * 5000];
    const moneyTicks = [];
    for (let t = moneyDomain[0]; t <= moneyDomain[1]; t += (moneyDomain[1] - moneyDomain[0]) / 4) moneyTicks.push(Math.round(t / 1000) * 1000);

    S.moneyChart = makeChart($("money-chart"), {
      height: 220, area: true, yDomain: moneyDomain, yTicks: moneyTicks, yTickFormat: fmtMoneyCompact,
      series: [{ key: "money", color: "var(--s-blue)", label: "Argent", get: (d) => d.money, fmt: fmtMoneyCompact }],
    });

    const VITALS = [
      { key: "health", color: "var(--s-aqua)", label: "Santé", get: (d) => d.health },
      { key: "stress", color: "var(--s-red)", label: "Stress", get: (d) => d.stress },
      { key: "fatigue", color: "var(--s-violet)", label: "Fatigue", get: (d) => d.fatigue },
      { key: "moral", color: "var(--s-green)", label: "Moral", get: (d) => d.moral },
      { key: "hunger", color: "var(--s-yellow)", label: "Faim", get: (d) => d.hunger },
    ];
    S.vitalsChart = makeChart($("vitals-chart"), { height: 260, area: false, yDomain: [0, 100], yTicks: [0, 25, 50, 75, 100], series: VITALS });
    $("vitals-legend").innerHTML = VITALS.map((s) => `<span class="legend-item"><span class="legend-key" style="background:${s.color}"></span>${s.label}</span>`).join("");

    const SUBJECT_COLORS = ["var(--s-blue)", "var(--s-aqua)", "var(--s-yellow)", "var(--s-magenta)", "var(--s-orange)"];
    const ACADEMIC = DATA.meta.subjects.map((subj, i) => ({ key: subj, color: SUBJECT_COLORS[i % SUBJECT_COLORS.length], label: subj, get: (d) => d.academic[subj] ?? 0 }));
    S.academicChart = makeChart($("academic-chart"), { height: 200, area: false, yDomain: [0, 100], yTicks: [0, 50, 100], series: ACADEMIC });
    $("academic-legend").innerHTML = ACADEMIC.map((s) => `<span class="legend-item"><span class="legend-key" style="background:${s.color}"></span>${escapeHtml(s.label)}</span>`).join("");

    attachHover(S.moneyChart, $("money-chart"), $("money-tooltip"), $("money-chart").parentElement);
    attachHover(S.vitalsChart, $("vitals-chart"), $("vitals-tooltip"), $("vitals-chart").parentElement);
    attachHover(S.academicChart, $("academic-chart"), $("academic-tooltip"), $("academic-chart").parentElement);

    const CAT_COLORS = { travail: "var(--s-blue)", etude: "var(--s-aqua)", sommeil: "var(--s-violet)", loisir: "var(--s-yellow)", autre: "var(--ink-muted)" };
    $("allocation-legend").innerHTML = DATA.meta.categories.map((c) => `<span class="legend-item"><span class="legend-dot" style="background:${CAT_COLORS[c.key]}"></span>${c.label}</span>`).join("");
    DATA.meta.categories.forEach((c) => {
      const seg = document.createElement("div");
      seg.className = "allocation-seg";
      seg.dataset.key = c.key;
      seg.style.background = CAT_COLORS[c.key];
      seg.style.width = "0%";
      seg.title = c.label;
      S.allocationBar.appendChild(seg);
    });

    const track = $("event-track");
    DATA.events.forEach((e) => {
      const dot = document.createElement("button");
      dot.className = "event-tick sev-" + e.severity;
      dot.style.left = (e.d / maxDay * 100) + "%";
      dot.title = `${fmtDateShort(days[e.d].date)} — ${e.label} : ${e.description}`;
      dot.setAttribute("aria-label", dot.title);
      dot.addEventListener("click", () => { pause(); setDay(e.d); });
      track.appendChild(dot);
    });

    const summary = DATA.summary;
    const finalTiles = [
      { label: "Argent final", value: fmtMoney(summary.final_money) },
      { label: "Santé", value: summary.final_health.toFixed(0) },
      { label: "Moral", value: summary.final_moral.toFixed(0) },
      { label: "Réussite examens", value: isNaN(summary.exam_success_rate) ? "—" : Math.round(summary.exam_success_rate * 100) + "%" },
      { label: "Maladies", value: summary.n_illness_episodes },
    ];
    $("final-strip").innerHTML = finalTiles.map((t) => `<div class="final-tile"><div class="ft-label">${t.label}</div><div class="ft-value">${t.value}</div></div>`).join("");
    $("period-label").textContent = `${fmtDate(DATA.meta.start_date)} → ${fmtDate(DATA.meta.end_date)}`;

    setDay(0);
  }

  // ---------------------------------------------------------------
  // Static controls (wired once — they persist across re-runs)
  // ---------------------------------------------------------------
  $("play-btn").addEventListener("click", () => (S && S.timer ? pause() : play()));
  $("scrubber").addEventListener("input", (e) => { if (!S) return; pause(); setDay(Number(e.target.value)); });
  $("end-btn").addEventListener("click", () => { if (!S) return; pause(); setDay(S.maxDay); });
  $("speed").addEventListener("change", () => { if (S && S.timer) { pause(); play(); } });

  function setRunStatus(message, busy, isError) {
    const el = $("run-status");
    el.classList.toggle("is-error", !!isError);
    el.innerHTML = busy ? `<span class="run-spinner"></span>${escapeHtml(message)}` : escapeHtml(message);
    $("run-btn").disabled = !!busy;
    $("play-btn").disabled = !!busy;
  }

  function runSimulation() {
    const seed = Number($("seed-input").value);
    const duration = Number($("duration-input").value);
    if (!Number.isFinite(seed) || !Number.isFinite(duration)) {
      setRunStatus("Graine et durée doivent être des nombres.", false, true);
      return;
    }
    pause();
    setRunStatus("Simulation en cours…", true);
    fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seed, duration_days: duration }),
    })
      .then(async (r) => {
        const body = await r.json();
        if (!r.ok) throw new Error(body.error || "Échec de la simulation");
        return body;
      })
      .then((data) => { initApp(data); setRunStatus(`Terminé — ${data.days.length} jours simulés.`, false); })
      .catch((err) => setRunStatus(err.message, false, true));
  }
  $("run-btn").addEventListener("click", runSimulation);

  // ---------------------------------------------------------------
  // Initial load
  // ---------------------------------------------------------------
  setRunStatus("Chargement de la simulation…", true);
  fetch("/api/data")
    .then((r) => r.json())
    .then((data) => { initApp(data); setRunStatus("", false); })
    .catch(() => setRunStatus("Impossible de charger la simulation.", false, true));
})();
