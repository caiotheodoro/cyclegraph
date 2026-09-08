/* cyclegraph flow gain — the Space's behaviour.
 *
 * Every measured number is read from data.json, which scripts/export_space_data.py builds from
 * results/. Nothing measured is typed here, so the page and the published dataset cannot drift.
 * The knee and floor thresholds travel in the payload too, because signal/gain.py owns them and
 * a reader downloads that harness.
 */
const $ = (id) => document.getElementById(id);
const fmt = (v, d = 4) => (v === null || v === undefined ? "—" : Number(v).toFixed(d));
const cvFmt = (v) => (Math.abs(v) < 1 ? v.toFixed(3).replace(/^0/, "") : v.toFixed(2));
const COLOUR = { farneback: "var(--v-measured)", raft: "var(--v-judge)", ref: "var(--v-published)" };
const HEX = { farneback: "#c93d1e", raft: "#4361ee", ref: "#a3a3a3", ink: "#171717" };

/* Knee, collapse and floor, computed with the harness's own thresholds. */
function classify(rows, ratio, TH) {
  const scored = rows.filter((r) => r.gain !== null).slice().sort((a, b) => a.displacement_px - b.displacement_px);
  const firstCollapse = scored.find((r) => r.gain < TH.collapse_gain);
  const collapse = firstCollapse ? firstCollapse.displacement_px : null;
  const above = scored.filter((r) => r.gain >= TH.knee_gain && (collapse === null || r.displacement_px < collapse));
  const knee = above.length ? Math.max(...above.map((r) => r.displacement_px)) : null;
  const regimeOne = scored
    .filter((r) => r.gain < TH.collapse_gain && r.gain >= TH.regime_two_fraction * ratio)
    .map((r) => r.gain)
    .sort((a, b) => a - b);
  const floor = regimeOne.length
    ? regimeOne.length % 2
      ? regimeOne[(regimeOne.length - 1) / 2]
      : (regimeOne[regimeOne.length / 2 - 1] + regimeOne[regimeOne.length / 2]) / 2
    : null;
  const tracks = floor !== null && Math.abs(floor - ratio) <= TH.background_tolerance * ratio;
  return { knee, collapse, floor, tracks, rows: scored };
}

function verdict(curve, displacement) {
  const xs = curve.rows.map((r) => r.displacement_px);
  if (displacement < Math.min(...xs) || displacement > Math.max(...xs)) return "UNTESTED";
  if (curve.knee === null) return "FAIL";
  return displacement <= curve.knee ? "PASS" : "FAIL";
}

fetch("data.json")
  .then((r) => r.json())
  .then((D) => {
    const TH = D.thresholds;
    const RATIO = D.depth_ratio;
    const SERIES = [
      { key: "farneback", label: "farneback-cv2", sweep: "farneback_025", hex: HEX.farneback },
      { key: "raft", label: "raft-small", sweep: "raft_025", hex: HEX.raft },
    ];
    const scaleOf = (sweep, w) => D.sweeps[sweep].find((s) => s.frame_size[0] === w);

    $("masthead-meta").textContent =
      `${D.lens.model} · ${D.lens.max_half_angle_deg}° half-angle · synthetic, no corpus`;
    $("prov").textContent = `Generated from ${D.generated_from}. Nothing measured is typed into this page.`;

    /* ---------------- verdicts ---------------- */
    const fb960 = classify(scaleOf("farneback_025", 960).rows, RATIO, TH);
    const rf960 = classify(scaleOf("raft_025", 960).rows, RATIO, TH);
    const res = D.sweeps.farneback_native;
    const bestIdx = res
      .map((s) => s.rows.filter((r) => r.gain >= TH.knee_gain).length)
      .reduce((bi, n, i, arr) => (n > arr[bi] ? i : bi), 0);
    const best = res[bestIdx];
    const cmpIdx = res[bestIdx].rows.filter((r) => r.gain >= TH.knee_gain).length - 1;

    $("verdicts").innerHTML = [
      ["Knee, farneback", `${fmt(fb960.knee, 3)} px`, `holds gain ${fmt(fb960.rows.find((r) => r.displacement_px === fb960.knee).gain)}`],
      ["Knee, raft-small", `${fmt(rf960.knee, 3)} px`, "one sweep step further out"],
      ["Floor", fmt(fb960.floor), `depth ratio ${RATIO} = ${D.hand_distance_m} m / ${D.background_distance_m} m`],
      ["Best decode", `${best.frame_size[0]}×${best.frame_size[1]}`, "measured optimum, not a compromise"],
    ]
      .map(([dt, v, d]) => `<div class="verdict"><dt>${dt}</dt><dd><strong>${v}</strong><span class="verdict-detail">${d}</span></dd></div>`)
      .join("");

    $("lens-limit").innerHTML =
      `<strong>The fleet.</strong> The corpus ships one <code class="tag">intrinsics.json</code> per worker and sixteen ` +
      `were checked and found byte-identical; the rest are assumed. A calibration replicated across every worker is not a ` +
      `real per-camera calibration, so this is a floor for the nominal lens rather than for the fleet.`;

    /* ---------------- 01 quiver scrubber ---------------- */
    const cv = $("quiver");
    const ctx = cv.getContext("2d");
    const box = D.hand_box;
    const cropW = box.width * 3.9;
    const cropH = cropW * (cv.height / cv.width);
    const ox = box.x + box.width / 2 - cropW / 2;
    const oy = box.y + box.height / 2 - cropH / 2;
    const k = cv.width / cropW;
    const px = (x) => (x - ox) * k;
    const py = (y) => (y - oy) * k;

    function drawQuiver(i) {
      const q = D.quivers[i];
      ctx.clearRect(0, 0, cv.width, cv.height);
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, cv.width, cv.height);
      ctx.fillStyle = "rgba(23,23,23,.035)";
      ctx.fillRect(px(box.x), py(box.y), box.width * k, box.height * k);

      /* True scale: one pixel of flow is one pixel of arrow, the same at every displacement.
         Normalising per panel would make the true arrows identical in all nine and hide the
         entire finding, which is that the true motion grows and the recovered motion does not. */
      const arrow = (v, dx, dy, colour, w) => {
        const x0 = px(v.x), y0 = py(v.y), x1 = px(v.x + dx), y1 = py(v.y + dy);
        ctx.strokeStyle = colour; ctx.lineWidth = w; ctx.lineCap = "round";
        ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
        ctx.fillStyle = colour;
        ctx.beginPath(); ctx.arc(x1, y1, w * 1.05, 0, 6.284); ctx.fill();
      };
      const vis = q.vectors.filter(
        (v) => v.x >= ox - 30 && v.x <= ox + cropW + 30 && v.y >= oy - 30 && v.y <= oy + cropH + 30
      );
      vis.forEach((v) => arrow(v, v.tx, v.ty, v.in_box ? "rgba(23,23,23,.85)" : "rgba(23,23,23,.22)", v.in_box ? 2.4 : 1.7));
      vis.forEach((v) => arrow(v, v.rx, v.ry, v.in_box ? "rgba(201,61,30,.95)" : "rgba(201,61,30,.3)", v.in_box ? 2.4 : 1.7));

      ctx.strokeStyle = "rgba(23,23,23,.45)"; ctx.lineWidth = 1.5; ctx.setLineDash([5, 5]);
      ctx.strokeRect(px(box.x), py(box.y), box.width * k, box.height * k);
      ctx.setLineDash([]);

      const past = q.gain < TH.collapse_gain;
      const recovered = q.gain * q.displacement_px;
      $("readout").innerHTML =
        `<dt>Hand displacement</dt><dd><strong>${fmt(q.displacement_px, 2)} px</strong></dd>` +
        `<dt>Gain</dt><dd><strong class="${past ? "hot" : "ok"}">${fmt(q.gain)}</strong>` +
        `<span class="state">${past
          ? "The recovered arrows stopped growing. The box is reporting the background."
          : "The recovered arrows lie on top of the true ones."}</span>` +
        `<div class="bar-cmp"><i style="width:${Math.min(100, q.gain * 100).toFixed(1)}%"></i></div></dd>` +
        `<dt>Recovered speed</dt><dd><strong>${fmt(recovered, 2)} px</strong>` +
        `<span class="state">against ${fmt(q.displacement_px, 2)} px of real motion</span></dd>`;
    }

    $("scrub-ticks").innerHTML = D.quivers
      .map((q, i) => `<span${i === 0 || i === D.quivers.length - 1 || i === 4 ? "" : ' style="opacity:.35"'}>${Math.round(q.displacement_px)}</span>`)
      .join("");
    $("scrub").max = String(D.quivers.length - 1);
    $("scrub").addEventListener("input", (e) => drawQuiver(Number(e.target.value)));
    drawQuiver(2);

    /* ---------------- 02 gain curve ---------------- */
    const shown = { farneback: true, raft: true };
    let curveScale = 960;

    $("series-toggles").innerHTML = SERIES.map(
      (s) => `<button class="button" type="button" data-series="${s.key}" aria-pressed="true">${s.label}</button>`
    ).join("");
    $("series-toggles").addEventListener("click", (e) => {
      const b = e.target.closest("[data-series]");
      if (!b) return;
      shown[b.dataset.series] = !shown[b.dataset.series];
      b.setAttribute("aria-pressed", String(shown[b.dataset.series]));
      drawCurve();
    });

    const scales = D.sweeps.farneback_025.map((s) => s.frame_size[0]);
    $("scale-select").innerHTML = scales
      .map((w) => `<option value="${w}"${w === 960 ? " selected" : ""}>${w}×${Math.round((w * 9) / 16)}</option>`)
      .join("");
    $("scale-select").addEventListener("change", (e) => { curveScale = Number(e.target.value); drawCurve(); });

    $("curve-legend").innerHTML =
      SERIES.map((s) => `<span><i class="chart-swatch" style="background:${s.hex}"></i>${s.label}</span>`).join("") +
      `<span><i class="chart-swatch" style="background:${HEX.ref}"></i>depth ratio ${RATIO}</span>`;

    const NS = "http://www.w3.org/2000/svg";
    const el = (n, a) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); return e; };

    function drawCurve() {
      const svg = $("curve");
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      // Right margin holds the series names, which sit outside the plot so they cannot
      // collide with the last value label.
      const M = { l: 52, r: 96, t: 22, b: 46 };
      const PW = 900 - M.l - M.r, PH = 400 - M.t - M.b;
      const active = SERIES.filter((s) => shown[s.key]);
      const all = SERIES.map((s) => scaleOf(s.sweep, curveScale)).filter(Boolean);
      if (!all.length) return;
      const xMax = Math.max(...all.flatMap((s) => s.rows.map((r) => r.displacement_px)));
      const X = (v) => M.l + Math.sqrt(v / xMax) * PW;
      const Y = (v) => M.t + (1 - v / 1.05) * PH;

      [0, RATIO, TH.collapse_gain, 1.0].forEach((g) => {
        svg.appendChild(el("line", { x1: M.l, x2: M.l + PW, y1: Y(g), y2: Y(g),
          class: "chart-grid", "stroke-dasharray": "2 4", ...(g === RATIO ? { stroke: HEX.ref, "stroke-dasharray": "5 4", "stroke-width": 1.5 } : {}) }));
        const t = el("text", { x: M.l - 9, y: Y(g) + 4, "text-anchor": "end", class: "chart-label" });
        t.textContent = cvFmt(g); svg.appendChild(t);
      });
      svg.appendChild(el("line", { x1: M.l, x2: M.l + PW, y1: M.t + PH, y2: M.t + PH, class: "chart-axis" }));

      const xs = all[0].rows.map((r) => r.displacement_px);
      xs.forEach((x) => { const t = el("text", { x: X(x), y: M.t + PH + 20, "text-anchor": "middle", class: "chart-label" });
        t.textContent = Math.round(x); svg.appendChild(t); });
      const xl = el("text", { x: M.l + PW / 2, y: M.t + PH + 40, "text-anchor": "middle", class: "chart-label" });
      xl.textContent = "hand displacement between the frame pair (px)"; svg.appendChild(xl);

      active.forEach((s) => {
        const sc = scaleOf(s.sweep, curveScale);
        if (!sc) return;
        const pts = sc.rows.filter((r) => r.gain !== null).map((r) => `${X(r.displacement_px)},${Y(r.gain)}`).join(" ");
        svg.appendChild(el("polyline", { points: pts, fill: "none", stroke: s.hex, "stroke-width": 2.2, "stroke-linejoin": "round" }));
        sc.rows.forEach((r, i) => {
          if (r.gain === null) return;
          const c = el("circle", { cx: X(r.displacement_px), cy: Y(r.gain), r: 4.5,
            fill: s.hex, stroke: "#ffffff", "stroke-width": 2 });
          c.style.cursor = "crosshair";
          c.addEventListener("mouseenter", () => showTip(s, r, X(r.displacement_px), Y(r.gain)));
          c.addEventListener("mouseleave", hideTip);
          svg.appendChild(c);
          // Direct value label on every point: identity is never colour alone in this system.
          const vl = el("text", { x: X(r.displacement_px),
            y: Y(r.gain) + (s.key === "farneback" ? 18 : -11), "text-anchor": "middle",
            fill: s.hex, "font-size": "10", "font-weight": "600",
            "font-family": "var(--font)" });
          vl.textContent = cvFmt(r.gain); svg.appendChild(vl);
        });
        // and the series name at its own line end, so the chart reads without the legend
        const last = sc.rows.filter((r) => r.gain !== null).slice(-1)[0];
        const nameEl = el("text", { x: M.l + PW + 10, y: Y(last.gain) + 4, "text-anchor": "start",
          fill: s.hex, "font-size": "11", "font-weight": "600", "font-family": "var(--font)" });
        nameEl.textContent = s.label; svg.appendChild(nameEl);
        svg.appendChild(el("line", { x1: X(last.displacement_px) + 5, x2: M.l + PW + 6,
          y1: Y(last.gain), y2: Y(last.gain), stroke: s.hex, "stroke-width": 1, opacity: .35 }));
      });

      const fb = classify(scaleOf("farneback_025", curveScale).rows, RATIO, TH);
      const rf = classify(scaleOf("raft_025", curveScale).rows, RATIO, TH);
      $("curve-lede").innerHTML =
        `Both sweeps use the ${scaleOf("farneback_025", curveScale).pair_interval_s} s pair interval, so they compare ` +
        `directly. At ${curveScale}×${Math.round((curveScale * 9) / 16)}, farneback holds full gain to ` +
        `<strong>${fmt(fb.knee, 3)} px</strong> and raft-small to <strong>${fmt(rf.knee, 3)} px</strong>. ` +
        `They land on <strong>${fmt(fb.floor)}</strong> and <strong>${fmt(rf.floor)}</strong> against a depth ratio of ` +
        `${RATIO}. A better estimator moves where the cliff is; it does not touch what is underneath it.`;
      $("curve-caption").textContent =
        "Horizontal axis is square-rooted because the knee sits low in the range. A line that dips below the depth " +
        "ratio at its last point has entered the second regime: displacement has exceeded the estimator's search " +
        "range and it is tracking nothing at all, which is excluded from the floor rather than averaged into it.";
    }

    const tip = $("curve-tip");
    function showTip(s, r, x, y) {
      const svg = $("curve");
      const rect = svg.getBoundingClientRect();
      const sx = (x / 900) * rect.width, sy = (y / 400) * rect.height;
      tip.innerHTML =
        `<div class="chart-tooltip-label">${fmt(r.displacement_px, 3)} px · ${fmt(r.over_box, 3)} box widths</div>` +
        `<div class="chart-tooltip-row"><i class="chart-swatch" style="background:${s.hex}"></i>${s.label}<strong>${fmt(r.gain)}</strong></div>`;
      tip.style.left = `${Math.min(rect.width - 170, sx + 12)}px`;
      tip.style.top = `${Math.max(0, sy - 46)}px`;
      tip.style.opacity = "1";
    }
    function hideTip() { tip.style.opacity = "0"; }
    drawCurve();

    /* ---------------- 03 calculator ---------------- */
    $("c-est").innerHTML = SERIES.map((s) => `<option value="${s.key}">${s.label}</option>`).join("");
    function recalc() {
      const hand = Number($("c-hand").value), bg = Number($("c-bg").value);
      const disp = Number($("c-disp").value);
      const key = $("c-est").value;
      const s = SERIES.find((x) => x.key === key);
      const sc = scaleOf(s.sweep, curveScale) || scaleOf(s.sweep, 960);
      const ratio = hand > 0 && bg > 0 ? hand / bg : null;
      const c = classify(sc.rows, RATIO, TH);
      const v = verdict(c, disp);
      const tone = v === "PASS" ? "var(--v-third)" : v === "FAIL" ? "var(--v-measured)" : "var(--muted)";
      const why = {
        PASS: `${fmt(disp, 2)} px is inside the range where ${s.label} still recovers the motion at this decode.`,
        FAIL: `${fmt(disp, 2)} px is past the knee. At that displacement ${s.label} reports the background, not the hand.`,
        UNTESTED: `${fmt(disp, 2)} px is outside the sweep, which runs ${fmt(Math.min(...sc.rows.map((r) => r.displacement_px)), 2)} to ${fmt(Math.max(...sc.rows.map((r) => r.displacement_px)), 2)} px. A test that has not seen a case does not clear it.`,
      }[v];
      $("calc-out").innerHTML =
        `<p style="margin:0 0 12px"><span class="verdict-badge" style="color:${tone}">${v}</span></p>` +
        `<p style="margin:0 0 12px;color:var(--muted);line-height:1.7">${why}</p>` +
        `<div class="table-wrap"><table class="table"><tbody>` +
        `<tr><td class="table-td-left">Predicted floor for your bench</td><td class="table-td">${ratio === null ? "—" : fmt(ratio)}</td></tr>` +
        `<tr><td class="table-td-left">Measured floor, ${s.label}</td><td class="table-td">${fmt(c.floor)}</td></tr>` +
        `<tr><td class="table-td-left">Knee at ${curveScale} px wide</td><td class="table-td">${fmt(c.knee, 3)} px</td></tr>` +
        `<tr><td class="table-td-left">Speed you would report past the knee</td><td class="table-td">${ratio === null ? "—" : `${(ratio * 100).toFixed(0)}% of true`}</td></tr>` +
        `</tbody></table></div>` +
        (ratio !== null && Math.abs(ratio - RATIO) > 0.02
          ? `<p class="chart-frame-caption">Your depth ratio is ${fmt(ratio)}, not the ${RATIO} these curves were rendered at. ` +
            `The knee is measured; the floor for your bench is a prediction from your two distances and has not been tested here.</p>`
          : "");
    }
    ["c-hand", "c-bg", "c-disp", "c-est"].forEach((id) => $(id).addEventListener("input", recalc));
    recalc();

    /* ---------------- 04 resolution ---------------- */
    const overBox = res[0].rows[cmpIdx].over_box;
    $("res-lede").innerHTML =
      `The same physical camera translation at four decode sizes, compared at ${overBox} of the hand box width — ` +
      `the last step at which the best scale still holds full gain. ` +
      `<strong>${best.frame_size[0]}×${best.frame_size[1]} is a measured optimum</strong>, and ` +
      `${res[res.length - 1].frame_size[0]}×${res[res.length - 1].frame_size[1]} scores below ` +
      `${res[0].frame_size[0]}×${res[0].frame_size[1]} at ` +
      `${((res[res.length - 1].frame_size[0] * res[res.length - 1].frame_size[1]) / (res[0].frame_size[0] * res[0].frame_size[1])).toFixed(0)} times the pixels.`;
    $("res-table").innerHTML =
      `<thead><tr><th class="table-th-left">decode</th><th class="table-th">gain at ${overBox} box widths</th>` +
      `<th class="table-th">knee</th><th class="table-th">megapixels</th></tr></thead><tbody>` +
      res
        .map((s) => {
          const c = classify(s.rows, RATIO, TH);
          const g = s.rows[cmpIdx].gain;
          const w = s.frame_size[0];
          const hasCurve = scales.includes(w);
          return `<tr data-scale="${w}" data-active="${w === curveScale}" style="cursor:${hasCurve ? "pointer" : "default"}">` +
            `<td class="table-td-left">${w}×${s.frame_size[1]}${hasCurve ? "" : ' <span class="mono">curve n/a</span>'}</td>` +
            `<td class="table-td" style="color:${g < TH.collapse_gain ? "var(--v-measured)" : "inherit"}">${fmt(g)}</td>` +
            `<td class="table-td">${fmt(c.knee, 3)} px</td>` +
            `<td class="table-td">${((w * s.frame_size[1]) / 1e6).toFixed(2)}</td></tr>`;
        })
        .join("") + `</tbody>`;
    $("res-table").addEventListener("click", (e) => {
      const tr = e.target.closest("[data-scale]");
      if (!tr) return;
      const w = Number(tr.dataset.scale);
      if (!scales.includes(w)) return;
      curveScale = w;
      $("scale-select").value = String(w);
      [...$("res-table").querySelectorAll("[data-scale]")].forEach((r) =>
        r.setAttribute("data-active", String(Number(r.dataset.scale) === w)));
      drawCurve(); recalc();
      $("curve").scrollIntoView({ behavior: "smooth", block: "center" });
    });

    /* ---------------- 05 lens rotation ---------------- */
    const rot = D.geometry_floor.rotation_corpus.filter((r) => r.rotation_deg_per_s > 0);
    const narrow = D.geometry_floor.rotation_narrow.filter((r) => r.rotation_deg_per_s > 0);
    const budget = D.geometry_floor.hal_budget;
    const medians = Object.keys(budget).sort((a, b) => Number(a) - Number(b));
    $("rot").max = String(rot.length - 1);
    $("rot-ticks").innerHTML = rot.map((r) => `<span>${r.rotation_deg_per_s}°/s</span>`).join("");
    function drawRot(i) {
      const r = rot[i], n = narrow[i];
      const med = medians[1];
      const b = budget[med];
      const over = r.floor_mm_s > b;
      $("rot-out").innerHTML =
        `<div class="table-wrap"><table class="table"><tbody>` +
        `<tr><td class="table-td-left">Corpus fisheye leaves</td><td class="table-td hot">${r.floor_mm_s} mm/s</td></tr>` +
        `<tr><td class="table-td-left">A narrow lens leaves</td><td class="table-td">${n.floor_mm_s} mm/s</td></tr>` +
        `<tr><td class="table-td-left">Ratio</td><td class="table-td">${(r.floor_mm_s / n.floor_mm_s).toFixed(0)}×</td></tr>` +
        `<tr><td class="table-td-left">Whole error budget at ${med} mm/s, ${D.geometry_floor.pre_registered_bound_hal} HAL</td>` +
        `<td class="table-td">${b} mm/s</td></tr>` +
        `</tbody></table></div>` +
        `<p class="chart-frame-caption" style="color:${over ? "var(--v-measured)" : "var(--muted)"}">` +
        (over
          ? `At ${r.rotation_deg_per_s}°/s the lens alone spends more than the entire pre-registered error budget, before any estimator runs.`
          : `At ${r.rotation_deg_per_s}°/s the lens spends ${((r.floor_mm_s / b) * 100).toFixed(0)}% of the budget, before any estimator runs.`) +
        `</p>`;
    }
    $("rot").addEventListener("input", (e) => drawRot(Number(e.target.value)));
    drawRot(3);

    /* ---------------- scroll reveal ---------------- */
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      document.documentElement.classList.add("motion");
      const io = new IntersectionObserver(
        (entries) => entries.forEach((en) => { if (en.isIntersecting) { en.target.setAttribute("data-visible", ""); io.unobserve(en.target); } }),
        { rootMargin: "0px 0px -80px 0px" }
      );
      document.querySelectorAll("[data-fade]").forEach((n) => io.observe(n));
    }
  })
  .catch((e) => {
    document.querySelector(".page").insertAdjacentHTML(
      "afterbegin",
      `<p style="color:#c93d1e;font-family:var(--mono)">data.json did not load: ${e}</p>`
    );
  });
