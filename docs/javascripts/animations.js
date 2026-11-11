/* kDomainBench docs: page behaviour on top of Material for MkDocs.

   - the landing card: a looping run → estimate k → compare animation (GSAP),
     with a dot per step and a pause button
   - a border under the header once the page is scrolled
   - a reading-progress bar and a back-to-top button
   - a sliding marker for the active entry of the table of contents

   With prefers-reduced-motion the landing card shows one still frame and
   back-to-top jumps instead of scrolling. */

(function () {
  const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Run fn now, then at most once per frame while the page scrolls. */
  const onScroll = (fn) => {
    let queued = false;
    const run = () => { queued = false; fn(); };
    window.addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(run); } }, { passive: true });
    fn();
  };

  const stickyHeader = () => {
    const header = document.querySelector('.md-header');
    const setShadow = () => header.setAttribute('data-md-state', window.scrollY > 8 ? 'shadow' : '');
    if (window.__stickyWired) return setShadow();     // instant navigation re-runs init: one listener is enough
    window.__stickyWired = true;
    onScroll(setShadow);
  };

  /* Reading-progress bar: a slim bar along the top edge */
  const scrollProgress = () => {
    if (document.querySelector('.scroll-progress')) return;
    const bar = document.createElement('div');
    bar.className = 'scroll-progress';
    document.body.appendChild(bar);

    onScroll(() => {
      const h = document.documentElement;
      const total = h.scrollHeight - h.clientHeight;
      bar.style.width = (total > 0 ? (window.scrollY / total) * 100 : 0) + '%';
      bar.classList.toggle('is-scrolling', window.scrollY > 80);
    });
  };

  /* Back-to-top button, shown after 600px of scroll */
  const backToTop = () => {
    if (document.querySelector('.back-to-top')) return;
    const btn = document.createElement('button');
    btn.className = 'back-to-top';
    btn.setAttribute('aria-label', 'Back to top');
    btn.innerHTML = '↑';
    btn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: REDUCED_MOTION ? 'auto' : 'smooth' });
    });
    document.body.appendChild(btn);

    onScroll(() => btn.classList.toggle('is-visible', window.scrollY > 600));
  };

  /* ── shared SVG helpers for the task-flow ── */
  const TF_NS = 'http://www.w3.org/2000/svg';
  const mk = (tag, attrs) => { const e = document.createElementNS(TF_NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; };
  const tfScene = () => mk('g', { class: 'tf-scene', opacity: 0 });
  const label = (x, y, str, anchor, size, fill, weight) => {
    const t = mk('text', { x, y, 'text-anchor': anchor, 'font-size': size, fill, 'font-weight': weight });
    t.textContent = str;
    return t;
  };
  /* seeded PRNG (mulberry32): a scene drawn twice from one seed is identical,
     and every visit sees the same frame */
  const tfRng = (seed) => () => {
    seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };

  /* Still frame without GSAP: give every registered element of a scene its
     final 'to' state (opacity, SVG attributes, x/y as a translate). Morphs are
     applied in the order they were added, so the last value of a property wins. */
  const tfStill = (scene) => {
    const offsets = new Map();
    scene.morphs.forEach(({ el, to }) => {
      Object.keys(to).forEach((k) => {
        const v = to[k];
        if (k === 'attr') Object.keys(v).forEach((a) => el.setAttribute(a, v[a]));
        else if (k === 'opacity') el.setAttribute('opacity', v);
        else if (k === 'x' || k === 'y') {
          const o = offsets.get(el) || { x: 0, y: 0 };
          o[k] = v;
          offsets.set(el, o);
        }
      });
    });
    offsets.forEach((o, el) => el.setAttribute('transform', `translate(${o.x} ${o.y})`));
    scene.g.setAttribute('opacity', 1);
  };

  /* The landing card: three scenes (run → estimate k → compare) on one looping
     GSAP timeline. */
  const taskFlow = () => {
    const wrap = document.querySelector('.taskflow');
    /* Instant navigation re-runs this on every page. The loop and the observer of
       the page before must stop first: a loop on detached nodes would run forever,
       and a stale observer would pause the new page's loop. */
    if (window.__tfTl) { window.__tfTl.kill(); window.__tfTl = null; }
    if (window.__tfIO) { window.__tfIO.disconnect(); window.__tfIO = null; }
    if (!wrap) return;
    const scenesG = wrap.querySelector('.tf-scenes');
    const headNum = wrap.querySelector('.tf-num');
    const headTitle = wrap.querySelector('.tf-title');
    scenesG.innerHTML = '';

    const reg = (arr, el, from, to, dur, delay, ease) => arr.push({ el, from, to, dur, delay, ease });

    /* The three scenes tell one run: a method finds 7 domains (①), which is the K
       with the best score among the K it tried (②), and 7 is then compared with
       the reference k next to other methods (③).
       ① a method is picked and its result spreads over a grey Visium spot array;
       ② the same tissue is split into K = 2 … 10 domains while a score is drawn
          for each K; the tissue settles on the K with the best score;
       ③ each method's k̂ slides onto a k axis from the reference k, colored as in
          kdb.pl.plot_k_estimates, and the rows glide into order of |k̂ − k|. */
    const buildScenes = () => {
      const scenes = [];
      /* The card's colours are CSS variables (extra.css), read here when the scenes
         are drawn, so the light and dark themes each get their own palette. */
      const css = getComputedStyle(wrap);
      const cv = (name) => css.getPropertyValue(name).trim();
      const ACC = cv('--tf-accent'), ACC_SOFT = cv('--tf-accent-soft'), ON_ACC = cv('--tf-on-accent');
      const CHIP_BG = cv('--tf-chip'), INK_MUT = cv('--tf-muted'), GREY_SPOT = cv('--tf-spot');
      const UNDER = cv('--tf-under'), EXACT = cv('--tf-exact'), OVER = cv('--tf-over');
      const DOM = ['#4e79a7', '#f28e2b', '#59a14f', '#e15759', '#76b7b2',     // the logo's palette, continued
                   '#edc948', '#b07aa1', '#ff9da7', '#9c755f', '#bab0ac'];
      const K_HAT = 7;                                  // the k of the story
      const appear = (m, el, delay, dur) => { el.setAttribute('opacity', 0); reg(m, el, { opacity: 0 }, { opacity: 1 }, dur || 0.3, delay || 0, 'power2.out'); };

      /* The tissue panel is drawn twice from one lattice: ① colours it, and ② starts
         from that finished state and recolours it for every K. It does not move
         between the two scenes, so the hand-over is seamless. */
      const PANEL = { x: 250, y: 30, w: 186, h: 158 };
      const T_ARRIVE = 3.2;
      const spots = (() => {
        const cx = PANEL.x + PANEL.w / 2, cy = PANEL.y + PANEL.h / 2, rx = 80, ry = 66, p = 13, dy = p * Math.sqrt(3) / 2;
        const out = [];
        for (let j = -7; j <= 7; j++) {
          for (let i = -8; i <= 8; i++) {
            const x = cx + i * p + (j % 2 ? p / 2 : 0), y = cy + j * dy;
            const u = (x - cx) / rx, v = (y - cy) / ry;
            if (u * u + v * v > 1) continue;
            out.push({ x, y, d: v + 0.35 * u * u });           // depth: curved, cortex-like layers
          }
        }
        out.sort((a, b) => a.d - b.d).forEach((s, i) => { s.rank = i / out.length; });
        return out;
      })();
      const layer = (s, k) => Math.floor(s.rank * k);          // k layers of equal size
      const buildTissue = (m, entryY) => {
        const rnd = tfRng(7);
        const tis = mk('g', {});
        tis.appendChild(mk('rect', { x: PANEL.x, y: PANEL.y, width: PANEL.w, height: PANEL.h, rx: 8, fill: 'none', stroke: 'currentColor', 'stroke-opacity': 0.2, 'stroke-width': 1.4 }));
        tis.spots = spots.map((s) => {
          const done = DOM[layer(s, K_HAT)];
          if (!m) return tis.appendChild(mk('circle', { cx: s.x, cy: s.y, r: 4.3, fill: done, class: 'tf-spot' }));
          // grey spots fade in; the result then spreads from where the wire arrives
          const c = tis.appendChild(mk('circle', { cx: s.x, cy: s.y, r: 4.3, fill: GREY_SPOT, opacity: 0 }));
          const t = T_ARRIVE + 0.05 + 0.75 * Math.hypot(s.x - PANEL.x, s.y - entryY) / PANEL.w;
          reg(m, c, { opacity: 0, scale: 1, svgOrigin: s.x + ' ' + s.y, attr: { fill: GREY_SPOT } }, { opacity: 1 }, 0.35, 0.3 + rnd() * 0.5, 'power2.out');
          reg(m, c, {}, { scale: 0.72, attr: { fill: done } }, 0.12, t, 'power2.out');
          reg(m, c, {}, { scale: 1 }, 0.4, t + 0.12, 'back.out(2.5)');
          return c;
        });
        if (m) {
          const ping = mk('rect', { x: PANEL.x, y: PANEL.y, width: PANEL.w, height: PANEL.h, rx: 8, fill: 'none', stroke: ACC, 'stroke-width': 1.8, opacity: 0 });
          tis.appendChild(ping);
          reg(m, ping, { opacity: 0 }, { opacity: 0.9 }, 0.12, T_ARRIVE - 0.04, 'power2.out');
          reg(m, ping, {}, { opacity: 0 }, 0.5, T_ARRIVE + 0.1, 'power2.out');
        }
        return tis;
      };

      /* ① Run — pick a method from the list; it runs on the spot array */
      (() => {
        const g = tfScene(); const m = []; const ex = [];
        const defs = mk('defs', {});
        const blur = mk('filter', { id: 'tf-soft-k', x: '-30%', y: '-200%', width: '160%', height: '500%' });
        blur.appendChild(mk('feGaussianBlur', { stdDeviation: 2.2 }));
        defs.appendChild(blur); g.appendChild(defs);

        const list = mk('g', {});
        g.appendChild(list);
        list.appendChild(label(34, 40, '10 methods', 'start', 9, 'currentColor', '700'));
        const names = ['PRECAST', 'BayesSpace', 'CellCharter', 'DeepST', 'SpatialDE2', '+ 5 more'];
        const SEL = 2;                                  // the method that gets picked
        const rw = 108, rh = 19, rgap = 5, rx = 34, ry0 = 50;
        const rowY = (i) => ry0 + i * (rh + rgap);
        const selCY = rowY(SEL) + rh / 2, selCX = rx + rw / 2;
        const T_PICK = 1.6, T_LAND = 2.25, T_RUN = 2.5;

        const shadow = mk('ellipse', { cx: selCX, cy: rowY(SEL) + rh + 2.5, rx: rw * 0.4, ry: 3, fill: '#0f172a', filter: 'url(#tf-soft-k)', opacity: 0 });
        list.appendChild(shadow);
        reg(m, shadow, { opacity: 0, scaleX: 0.8, svgOrigin: selCX + ' ' + (rowY(SEL) + rh + 2.5) }, { opacity: 0.3, scaleX: 1.12 }, 0.33, T_PICK, 'power3.out');
        reg(m, shadow, {}, { opacity: 0, scaleX: 0.8 }, 0.25, T_LAND, 'power2.in');

        const tIn = [0.05, 0.16, 0.25, 0.32, 0.37, 0.40];
        let selRow = null;
        names.forEach((nm, i) => {
          const y = rowY(i), sel = (i === SEL);
          const row = mk('g', { opacity: 0 });
          const chip = mk('rect', { x: rx, y, width: rw, height: rh, rx: 4, fill: CHIP_BG });
          const txt = label(rx + 10, y + 13, nm, 'start', 9, INK_MUT, '500');
          row.appendChild(chip); row.appendChild(txt);
          if (!sel) list.appendChild(row); else selRow = row;
          const from = { opacity: 0, x: -10 };
          if (sel) { from.y = 0; from.scale = 1; from.svgOrigin = selCX + ' ' + selCY; }
          reg(m, row, from, { opacity: 1, x: 0 }, 0.4, tIn[i], 'power3.out');
          if (sel) {
            reg(m, chip, {}, { attr: { fill: ACC } }, 0.25, T_PICK, 'power2.out');
            reg(m, txt, {}, { attr: { fill: ON_ACC, 'font-weight': 700 } }, 0.25, T_PICK, 'power2.out');
            reg(m, row, {}, { y: -5, scale: 1.06 }, 0.33, T_PICK, 'power3.out');
            reg(m, row, {}, { y: 0, scale: 0.985 }, 0.25, T_LAND, 'power2.in');
            reg(m, row, {}, { scale: 1 }, 0.2, T_RUN, 'power3.out');
          } else {
            reg(m, row, {}, { opacity: 0.55 }, 0.3, T_PICK, 'power2.out');
          }
        });
        list.appendChild(selRow);

        const ring = mk('rect', { x: rx - 3, y: rowY(0) - 3, width: rw + 6, height: rh + 6, rx: 6, fill: 'none', stroke: ACC, 'stroke-width': 1.8, opacity: 0 });
        list.appendChild(ring);
        reg(m, ring, { opacity: 0, y: 0 }, { opacity: 1 }, 0.2, 0.8, 'power2.out');
        reg(m, ring, {}, { y: rowY(SEL) - rowY(0) }, 0.55, 0.95, 'power3.inOut');
        reg(m, ring, {}, { opacity: 0 }, 0.25, T_PICK, 'power2.out');

        const wx0 = rx + rw + 5, wx1 = PANEL.x - 3, wLen = wx1 - wx0;
        const wire = mk('line', { x1: wx0, y1: selCY, x2: wx1, y2: selCY, stroke: ACC, 'stroke-width': 1.8, 'stroke-linecap': 'round', 'stroke-dasharray': wLen, 'stroke-dashoffset': wLen, opacity: 0 });
        g.appendChild(wire);
        reg(m, wire, { opacity: 0, attr: { 'stroke-dashoffset': wLen } }, { opacity: 1 }, 0.05, T_RUN, 'none');
        reg(m, wire, {}, { attr: { 'stroke-dashoffset': 0 } }, T_ARRIVE - T_RUN, T_RUN, 'power2.inOut');
        reg(m, wire, {}, { opacity: 0.45 }, 0.5, T_ARRIVE + 0.1, 'power2.out');
        const head = mk('circle', { cx: wx0, cy: selCY, r: 3.2, fill: ACC, opacity: 0 });
        g.appendChild(head);
        reg(m, head, { opacity: 0, x: 0 }, { opacity: 1 }, 0.05, T_RUN, 'none');
        reg(m, head, {}, { x: wLen }, T_ARRIVE - T_RUN, T_RUN, 'power2.inOut');
        reg(m, head, {}, { opacity: 0 }, 0.12, T_ARRIVE, 'power2.out');

        const tis = buildTissue(m, selCY);
        tis.setAttribute('opacity', 0);
        g.appendChild(tis);
        reg(m, tis, { opacity: 0 }, { opacity: 1 }, 0.4, 0.3, 'power2.out');
        const cap = label(PANEL.x + PANEL.w / 2, 204, 'Spatial domains', 'middle', 9, 'currentColor', '600');
        cap.setAttribute('opacity', 0);
        g.appendChild(cap);
        reg(m, cap, { opacity: 0 }, { opacity: 1 }, 0.5, T_ARRIVE + 1.1, 'power2.out');

        // hand-over to ②: the list makes room for the score, the tissue stays
        [list, wire].forEach((el) => ex.push({ el, to: { opacity: 0, x: -10 }, dur: 0.3, delay: 0, ease: 'power2.out' }));
        ex.push({ el: cap, to: { opacity: 0 }, dur: 0.25, delay: 0, ease: 'power2.out' });
        scenes.push({ num: 1, title: 'Run a method', g, morphs: m, exits: ex, hold: 1.8 });
      })();

      /* ② Estimate k — the method tries every K: the tissue is split into K domains and
         each K gets a score; the K with the best score becomes k̂ */
      (() => {
        const g = tfScene(); const m = [];
        const tis = buildTissue(null);
        g.appendChild(tis);
        const cap = label(PANEL.x + PANEL.w / 2, 204, 'K = ' + K_HAT, 'middle', 9, 'currentColor', '600');
        g.appendChild(cap); appear(m, cap, 0.15);

        // axes: K = 2 … 10, score in [0, 1]
        const ax0 = 44, ax1 = 222, ay0 = 172, ay1 = 44;
        const Ks = [2, 3, 4, 5, 6, 7, 8, 9, 10];
        const SC = [0.30, 0.43, 0.56, 0.67, 0.78, 0.90, 0.74, 0.63, 0.55];
        const px = (k) => ax0 + 10 + (k - Ks[0]) * (ax1 - ax0 - 20) / (Ks.length - 1);
        const py = (v) => ay0 - v * (ay0 - ay1);

        const axes = mk('path', { d: `M ${ax0} ${ay1 - 6} V ${ay0} H ${ax1}`, fill: 'none', stroke: 'currentColor', 'stroke-opacity': 0.35, 'stroke-width': 1.2 });
        g.appendChild(axes); appear(m, axes, 0.1);
        const yl = label(ax0 - 6, ay1, 'score', 'end', 8, 'currentColor', '600');
        g.appendChild(yl); appear(m, yl, 0.15);
        [2, 4, 6, 8, 10].forEach((k, i) => {
          const t = label(px(k), ay0 + 12, String(k), 'middle', 8, INK_MUT, '500');
          g.appendChild(t); appear(m, t, 0.15 + i * 0.04);
        });
        const xl = label(ax1, ay0 + 26, 'K, the number of domains tried', 'end', 8, 'currentColor', '600');
        g.appendChild(xl); appear(m, xl, 0.3);

        const pts = SC.map((v, i) => [px(Ks[i]), py(v)]);
        const at = [0];                                         // length of the curve up to each point
        for (let i = 1; i < pts.length; i++) at.push(at[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
        const len = at[at.length - 1];
        const cursor = g.appendChild(mk('line', { x1: 0, y1: ay1 - 6, x2: 0, y2: ay0, stroke: ACC, 'stroke-width': 1.3, opacity: 0 }));
        const curve = g.appendChild(mk('polyline', { points: pts.map((p) => p.join(',')).join(' '), fill: 'none', stroke: ACC_SOFT, 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-dasharray': len, 'stroke-dashoffset': len }));
        const marks = pts.map((p) => g.appendChild(mk('circle', { cx: p[0], cy: p[1], r: 3, fill: ACC_SOFT, class: 'tf-pt' })));

        /* One sweep drives the cursor, the curve and the tissue. GSAP moves `k` (the K
           under the cursor) and `drawn` (how far the curve has got); paint() runs on
           every frame of the loop and shows that state, so a jump to any time of the
           scene shows the right picture. */
        const sweep = { k: K_HAT, drawn: 0 };
        let shown = 0;
        const paint = () => {
          const i = Math.min(Math.floor(sweep.drawn), pts.length - 2), k = Math.round(sweep.k);
          cursor.setAttribute('transform', `translate(${px(sweep.k)} 0)`);
          curve.setAttribute('stroke-dashoffset', len - at[i] - (sweep.drawn - i) * (at[i + 1] - at[i]));
          marks.forEach((c, j) => c.classList.toggle('is-on', sweep.drawn > 0 && j <= sweep.drawn));
          if (k === shown) return;
          shown = k;
          tis.spots.forEach((c, j) => { c.style.fill = DOM[layer(spots[j], k)]; });
          cap.textContent = 'K = ' + k;
        };
        const T_START = 0.5, T_SWEEP = 1.05, D_SWEEP = 2.6, T_BACK = T_SWEEP + D_SWEEP + 0.25, T_BEST = T_BACK + 0.55;
        reg(m, sweep, { k: K_HAT, drawn: 0 }, { k: Ks[0] }, 0.45, T_START, 'power2.inOut');       // start over, from K = 2
        reg(m, sweep, {}, { k: Ks[Ks.length - 1], drawn: Ks.length - 1 }, D_SWEEP, T_SWEEP, 'none');
        reg(m, sweep, {}, { k: K_HAT }, 0.55, T_BACK, 'power3.inOut');                             // back to the best K
        reg(m, cursor, { opacity: 0 }, { opacity: 0.5 }, 0.2, T_START, 'power2.out');
        reg(m, cursor, {}, { opacity: 0 }, 0.3, T_BEST + 0.1, 'power2.out');

        // the best K: drop line, deep-coloured point, k̂ label
        const [bx, by] = pts[Ks.indexOf(K_HAT)];
        const drop = mk('line', { x1: bx, y1: by + 5, x2: bx, y2: ay0, stroke: ACC, 'stroke-width': 1.3, 'stroke-dasharray': '3 2.5' });
        g.appendChild(drop); appear(m, drop, T_BEST + 0.15);
        const halo = mk('circle', { cx: bx, cy: by, r: 9, fill: ACC, opacity: 0 });
        g.appendChild(halo);
        reg(m, halo, { opacity: 0, scale: 0.4, svgOrigin: bx + ' ' + by }, { opacity: 0.15, scale: 1 }, 0.4, T_BEST, 'back.out(1.7)');
        const best = mk('circle', { cx: bx, cy: by, r: 4.6, fill: ACC });
        g.appendChild(best);
        reg(m, best, { opacity: 0, scale: 0.6, svgOrigin: bx + ' ' + by }, { opacity: 1, scale: 1 }, 0.35, T_BEST, 'back.out(2)');
        const kl = label(bx + 11, by - 7, 'k̂ = ' + K_HAT, 'start', 11, ACC, '700');
        g.appendChild(kl); appear(m, kl, T_BEST + 0.2, 0.35);
        scenes.push({ num: 2, title: 'Estimate k', g, morphs: m, hold: 2.4, cut: true, tick: paint });
      })();

      /* ③ Compare — each method's k̂ on a k axis next to the reference k; rows glide
         into order of |k̂ − k| and the closest method is outlined */
      (() => {
        const g = tfScene(); const m = [];
        const methods = ['Method 1', 'Method 2', 'Method 3', 'Method 4', 'Method 5'];
        const K_REF = K_HAT;                            // the method of the story finds the reference k
        const estimates = [4, K_REF, 10, 2, 6];
        const err = estimates.map((k) => Math.abs(k - K_REF));
        const order = err.map((_, i) => i).sort((a, b) => err[a] - err[b] || a - b);
        const rank = err.map((_, i) => order.indexOf(i));
        const BEST = order[0];
        const kx0 = 132, kx1 = 400, y0 = 62, ch = 25;
        const kx = (k) => kx0 + (k - 1) * (kx1 - kx0) / 11;   // k = 1 … 12
        const T_SLIDE = 0.6, T_SORT = 2.3, T_TRACE = 3.0, T_CLOSE = 3.9;

        const bx = 44, by = y0 - 12, bw = 380, bhh = 24, brx = 6;
        const band = mk('rect', { x: bx, y: by, width: bw, height: bhh, rx: brx, fill: ACC, opacity: 0 });
        g.appendChild(band);
        reg(m, band, { opacity: 0 }, { opacity: 0.08 }, 0.4, T_CLOSE, 'power2.out');

        // k axis with ticks, and the reference k as a dashed line
        const axY = y0 + methods.length * ch - 6;
        const axis = mk('line', { x1: kx0, y1: axY, x2: kx1, y2: axY, stroke: 'currentColor', 'stroke-opacity': 0.35, 'stroke-width': 1.2 });
        g.appendChild(axis); appear(m, axis, 0.05);
        [1, 3, 5, 7, 9, 11].forEach((k) => {
          const t = label(kx(k), axY + 12, String(k), 'middle', 8, INK_MUT, '500');
          g.appendChild(t); appear(m, t, 0.1);
        });
        const axl = label(kx1 + 8, axY + 3, 'k', 'start', 9, 'currentColor', '700');
        axl.setAttribute('font-style', 'italic');
        g.appendChild(axl); appear(m, axl, 0.1);
        const tl = mk('line', { x1: kx(K_REF), y1: 32, x2: kx(K_REF), y2: axY, stroke: 'currentColor', 'stroke-opacity': 0.55, 'stroke-width': 1.3, 'stroke-dasharray': '4 3' });
        g.appendChild(tl); appear(m, tl, 0.15);
        const tlab = label(kx(K_REF), 27, 'reference k = ' + K_REF, 'middle', 8.5, 'currentColor', '700');
        g.appendChild(tlab); appear(m, tlab, 0.15);

        const tRow = [0.2, 0.35, 0.47, 0.57, 0.65];
        methods.forEach((nm, i) => {
          const row = mk('g', {});
          const cy = y0 + i * ch, best = (i === BEST);
          // fewer domains than the reference, the reference k, or more: the colours of kdb.pl.plot_k_estimates
          const tone = estimates[i] < K_REF ? UNDER : estimates[i] > K_REF ? OVER : EXACT;
          const name = label(96, cy + 3, nm, 'end', 8, 'currentColor', '500');
          row.appendChild(name); appear(m, name, tRow[i]);
          // the error segment between k̂ and the reference k grows with the dot
          const seg = mk('line', { x1: kx(K_REF), y1: cy, x2: kx(K_REF), y2: cy, stroke: tone, 'stroke-width': 3, 'stroke-linecap': 'round', opacity: 0.35 });
          row.appendChild(seg);
          reg(m, seg, { attr: { x2: kx(K_REF) } }, { attr: { x2: kx(estimates[i]) } }, 0.7, T_SLIDE + tRow[i], 'power3.out');
          const dot = mk('circle', { cx: kx(K_REF), cy, r: 5.5, fill: GREY_SPOT });
          row.appendChild(dot);
          reg(m, dot, { opacity: 0, attr: { cx: kx(K_REF), fill: GREY_SPOT } }, { opacity: 1 }, 0.2, T_SLIDE + tRow[i], 'power2.out');
          reg(m, dot, {}, { attr: { cx: kx(estimates[i]), fill: tone } }, 0.7, T_SLIDE + tRow[i], 'power3.out');
          const val = label(kx(estimates[i]) + (estimates[i] < K_REF ? -10 : 10), cy + 3, String(estimates[i]), estimates[i] < K_REF ? 'end' : 'start', 8, INK_MUT, '600');
          row.appendChild(val); appear(m, val, T_SLIDE + tRow[i] + 0.6, 0.3);
          if (best) reg(m, name, {}, { attr: { 'font-weight': 700 } }, 0.2, T_CLOSE, 'power2.out');
          g.appendChild(row);
          if (rank[i] !== i) reg(m, row, { y: 0 }, { y: (rank[i] - i) * ch }, 0.6, T_SORT + i * 0.05, 'power2.inOut');
        });

        const P = 2 * (bw + bhh) - 8 * brx + 2 * Math.PI * brx, PEN = 0.05 * P;
        const outline = { x: bx, y: by, width: bw, height: bhh, rx: brx, fill: 'none', stroke: ACC, 'stroke-linecap': 'round' };
        const trace = mk('rect', Object.assign({ 'stroke-width': 1.6, 'stroke-dasharray': P, 'stroke-dashoffset': P, opacity: 0 }, outline));
        const pen = mk('rect', Object.assign({ 'stroke-width': 3, 'stroke-dasharray': PEN + ' ' + (P - PEN), 'stroke-dashoffset': PEN, opacity: 0 }, outline));
        g.appendChild(trace); g.appendChild(pen);
        reg(m, trace, { opacity: 0, attr: { 'stroke-dashoffset': P, 'stroke-width': 1.6 } }, { opacity: 1 }, 0.05, T_TRACE, 'none');
        reg(m, trace, {}, { attr: { 'stroke-dashoffset': 0 } }, T_CLOSE - T_TRACE, T_TRACE, 'power2.inOut');
        reg(m, trace, {}, { opacity: 0 }, 0.35, T_CLOSE + 0.3, 'power2.out');
        reg(m, pen, { opacity: 0, attr: { 'stroke-dashoffset': PEN } }, { opacity: 1 }, 0.05, T_TRACE, 'none');
        reg(m, pen, {}, { attr: { 'stroke-dashoffset': PEN - P } }, T_CLOSE - T_TRACE, T_TRACE, 'power2.inOut');
        reg(m, pen, {}, { opacity: 0 }, 0.08, T_CLOSE - 0.04, 'none');
        scenes.push({ num: 3, title: 'Compare with the reference k', g, morphs: m, hold: 3.2 });
      })();

      return scenes;
    };

    /* ── Draw the scenes and the controls below the card, and start the loop ── */
    const render = () => {
      const scenes = buildScenes();
      scenes.forEach((s) => scenesG.appendChild(s.g));

      const controls = wrap.querySelector('.tf-dots');
      controls.innerHTML = '';
      const dots = scenes.map((sc) => {
        const dot = document.createElement('button');
        dot.type = 'button';
        dot.className = 'tf-dot';
        dot.setAttribute('aria-label', 'Step ' + sc.num + ': ' + sc.title);
        return controls.appendChild(dot);
      });

      let step = -1;
      const setHead = (i) => {
        if (i === step) return;
        const first = step < 0;
        step = i;
        headNum.textContent = scenes[i].num;
        headTitle.textContent = scenes[i].title;
        dots.forEach((d, j) => d.classList.toggle('is-active', j === i));
        if (first || REDUCED_MOTION || !headTitle.animate) return;
        [headNum, headTitle].forEach((el) => el.animate(      // the new step's title rises into place
          [{ opacity: 0, transform: 'translateY(5px)' }, { opacity: 1, transform: 'none' }],
          { duration: 260, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' }));
      };

      const gsap = window.gsap;
      setHead(0);
      // No GSAP (its script did not load) or reduced motion: show the first scene as a still frame.
      if (!gsap || REDUCED_MOTION) { tfStill(scenes[0]); controls.hidden = true; return; }

      const frame = () => {                    // on every frame of the loop, and after every jump
        const t = master.time();
        let i = headAt.length - 1;
        while (i > 0 && t < headAt[i]) i--;
        setHead(i);
        const end = i + 1 < headAt.length ? headAt[i + 1] : master.duration();
        dots[i].style.setProperty('--tf-progress', ((t - headAt[i]) / (end - headAt[i])).toFixed(3));
        scenes.forEach((s) => s.tick && s.tick());
      };
      const master = gsap.timeline({ repeat: -1, onUpdate: frame });
      window.__tfTl = master;
      const startTimes = [];                   // where each scene begins on the master
      const builtAt = [];                      // where each scene's build-up has finished
      const headAt = [];                       // where the card's title turns to each scene
      scenes.forEach((s, idx) => {
        startTimes[idx] = master.duration();   // current end = this scene's start time
        if (headAt[idx] === undefined) headAt[idx] = startTimes[idx];
        const st = gsap.timeline();
        /* a scene slides in from the right and builds; one that takes over the
           tissue of the scene before (cut) is simply there */
        const lead = s.cut ? 0 : 0.35;
        st.set(s.g, s.cut ? { opacity: 1, x: 0 } : { opacity: 0, x: 14 }, 0);
        s.morphs.forEach((mo) => st.set(mo.el, mo.from, 0));
        if (!s.cut) st.to(s.g, { opacity: 1, x: 0, duration: 0.5, ease: 'power3.out' }, 0);
        let maxEnd = lead;
        s.morphs.forEach((mo) => {
          st.to(mo.el, Object.assign({ duration: mo.dur, ease: mo.ease, delay: mo.delay }, mo.to), lead);
          maxEnd = Math.max(maxEnd, lead + mo.delay + mo.dur);
        });
        /* the finished frame rests, then the scene either hands the tissue to the
           next one (exits) or leaves to the left as a whole */
        const tExit = maxEnd + s.hold;
        if (s.exits) {
          let exitEnd = tExit;
          headAt[idx + 1] = startTimes[idx] + tExit + 0.1;      // the hand-over already belongs to the next step
          s.exits.forEach((mo) => {
            st.to(mo.el, Object.assign({ duration: mo.dur, ease: mo.ease }, mo.to), tExit + mo.delay);
            exitEnd = Math.max(exitEnd, tExit + mo.delay + mo.dur);
          });
          st.set(s.g, { opacity: 0 }, exitEnd);
        } else {
          st.to(s.g, { opacity: 0, x: -14, duration: 0.3, ease: 'power2.out' }, tExit);
        }
        builtAt[idx] = startTimes[idx] + maxEnd;
        master.add(st);
      });

      /* Open the loop on the first scene's finished frame. seek() renders at
         once, without waiting for an animation frame, so the card has content
         in a headless render, a background tab or a paused timeline. The next
         loops play the first scene's build-up from the start. */
      const jump = (t) => { master.seek(t); frame(); };
      jump(builtAt[0]);

      /* The controls. A dot jumps to its scene: to its start while the loop plays,
         to its finished frame while it is paused. The button pauses the loop for
         readers who want to look at a frame (or do not want motion beside the text). */
      const paused = () => wrap.dataset.paused === '1';
      dots.forEach((dot, i) => {
        /* a hair past the scene's start: a scene that has never played does not
           render its first frame at exactly its own time 0 */
        dot.addEventListener('click', () => jump(paused() ? builtAt[i] : startTimes[i] + 0.001));
      });
      const toggle = controls.appendChild(document.createElement('button'));
      toggle.type = 'button';
      toggle.className = 'tf-toggle';
      const showState = () => {
        toggle.setAttribute('aria-label', paused() ? 'Play the animation' : 'Pause the animation');
        toggle.innerHTML = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="' +
          (paused() ? 'M3.5 2l6.5 4-6.5 4z' : 'M2.5 2h2.5v8H2.5zM7 2h2.5v8H7z') + '"/></svg>';
        paused() ? master.pause() : master.play();
      };
      toggle.addEventListener('click', () => { wrap.dataset.paused = paused() ? '' : '1'; showState(); });
      showState();
    };

    render();

    /* redraw in the other palette when the reader switches the theme */
    if (!window.__tfScheme) {
      window.__tfScheme = new MutationObserver(() => taskFlow());
      window.__tfScheme.observe(document.body, { attributes: true, attributeFilter: ['data-md-color-scheme'] });
    }

    /* Perf: pause the perpetual loop when the card is scrolled off-screen, so it
       isn't burning CPU/rAF the whole time you're reading further down the page.
       isConnected: an observer of a page left by instant navigation can still
       deliver a late record for its detached card, and must not touch this loop. */
    if ('IntersectionObserver' in window) {
      window.__tfIO = new IntersectionObserver((ents) => {
        ents.forEach((e) => {
          const tl = window.__tfTl;
          if (!e.target.isConnected || !tl) return;
          e.isIntersecting && wrap.dataset.paused !== '1' ? tl.play() : tl.pause();
        });
      }, { threshold: 0.01 });
      window.__tfIO.observe(wrap);
    }
  };

  /* Sliding TOC indicator — one vertical bar that animates to the active heading,
     instead of a border jumping between items.
     Tracks Material's `.md-nav__link--active`, which the scrollspy toggles. */
  const tocSlider = () => {
    const getCtx = () => {
      const list = document.querySelector('.md-sidebar--secondary .md-nav--secondary > .md-nav__list');
      if (!list) return null;
      let bar = list.querySelector(':scope > .toc-indicator');
      if (!bar) { bar = document.createElement('div'); bar.className = 'toc-indicator'; list.appendChild(bar); }
      return { list, bar };
    };
    const move = () => {
      const ctx = getCtx();
      if (!ctx) return;
      const active = document.querySelector('.md-sidebar--secondary .md-nav__link--active');
      // Keep the bar where it is during the brief moments the scrollspy has no
      // active link (it toggles classes in two steps) — avoids flicker.
      if (!active) return;
      const a = active.getBoundingClientRect(), l = ctx.list.getBoundingClientRect();
      ctx.bar.style.height = Math.round(a.height) + 'px';
      ctx.bar.style.transform = 'translateY(' + Math.round(a.top - l.top) + 'px)';
      ctx.bar.style.opacity = '1';
    };
    if (!window.__tocSliderWired) {
      window.__tocSliderWired = true;
      onScroll(move);
      window.addEventListener('resize', move, { passive: true });
    }
    move();                      // create + position the bar immediately
    setTimeout(move, 400);       // re-position after fonts/layout settle
    setTimeout(move, 1200);      // and once more after instant-nav / late render
  };

  const init = () => {
    stickyHeader();
    scrollProgress();
    backToTop();
    taskFlow();
    tocSlider();
  };

  document$.subscribe(init);    // Material: on the first load and after every instant navigation
})();
