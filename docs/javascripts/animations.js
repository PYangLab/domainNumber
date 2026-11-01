/* M3 docs — page polish JS.

   Two responsibilities:

   1. Scroll-triggered fade-up:
      - Content is visible by default (CSS).
      - JS finds animation candidates, tags below-fold ones with
        `.anim-pending` (which sets opacity:0 + translate via CSS),
        and uses IntersectionObserver to flip them to `.is-visible`
        as they enter the viewport.
      - If anything fails (JS disabled, iframe with innerHeight=0,
        broken observer), no element ever gets `.anim-pending` →
        content remains fully visible. Fail-open by design.

   2. Sticky header shadow on scroll. */

(function () {
  // With reduced motion only the landing card runs, and it draws a still frame.
  const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const ANIM_SELECTOR =
    '.md-typeset .grid.cards > ul > li, ' +
    '.md-typeset .grid:not(.cards) > *, ' +
    '.anim-fade-up';

  const initFadeUp = () => {
    const targets = document.querySelectorAll(ANIM_SELECTOR);
    if (!targets.length) return;
    if (!('IntersectionObserver' in window)) return;

    const vh = window.innerHeight || document.documentElement.clientHeight || 0;
    // If viewport is degenerate (0 or unknown), bail — keep content visible.
    if (vh < 100) return;

    // Tag below-the-fold targets as pending (CSS hides them); keep above-fold
    // content fully visible to avoid any flash of empty space.
    targets.forEach(el => {
      const r = el.getBoundingClientRect();
      // r.top here is relative to viewport. If element's top is more than ~50px
      // below the visible area, animate. Otherwise leave visible.
      if (r.top > vh - 40) {
        el.classList.add('anim-pending');
      }
    });

    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, {
      rootMargin: '0px 0px 80px 0px',   // pre-reveal 80px before entering
      threshold: 0.01,
    });

    targets.forEach(el => {
      if (el.classList.contains('anim-pending')) io.observe(el);
    });
  };

  const stickyHeader = () => {
    const header = document.querySelector('.md-header');
    if (!header) return;
    const setShadow = () => header.setAttribute('data-md-state', window.scrollY > 8 ? 'shadow' : '');
    setShadow();                        // refresh state on every (re-)init
    if (window.__stickyWired) return;   // but attach the scroll listener only ONCE
    window.__stickyWired = true;        // (instant-nav re-runs init; don't stack handlers)
    let ticking = false;
    window.addEventListener('scroll', () => {
      if (!ticking) { requestAnimationFrame(() => { setShadow(); ticking = false; }); ticking = true; }
    }, { passive: true });
  };

  /* Scroll progress bar (Bioconductor reference) — slim violet bar at top */
  const scrollProgress = () => {
    if (document.querySelector('.scroll-progress')) return;
    const bar = document.createElement('div');
    bar.className = 'scroll-progress';
    document.body.appendChild(bar);

    let ticking = false;
    const update = () => {
      const h = document.documentElement;
      const total = h.scrollHeight - h.clientHeight;
      const pct = total > 0 ? (window.scrollY / total) * 100 : 0;
      bar.style.width = pct + '%';
      bar.classList.toggle('is-scrolling', window.scrollY > 80);
      ticking = false;
    };
    window.addEventListener('scroll', () => {
      if (!ticking) { requestAnimationFrame(update); ticking = true; }
    }, { passive: true });
    update();
  };

  /* Back-to-top button — fastai-style, appears after 600px scroll */
  const backToTop = () => {
    if (document.querySelector('.back-to-top')) return;
    const btn = document.createElement('button');
    btn.className = 'back-to-top';
    btn.setAttribute('aria-label', 'Back to top');
    btn.innerHTML = '↑';
    btn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    document.body.appendChild(btn);

    let ticking = false;
    const update = () => {
      btn.classList.toggle('is-visible', window.scrollY > 600);
      ticking = false;
    };
    window.addEventListener('scroll', () => {
      if (!ticking) { requestAnimationFrame(update); ticking = true; }
    }, { passive: true });
    update();
  };

  const enableSectionNumbersOnHome = () => {
    const path = (window.location.pathname || '').replace(/\/+$/, '/');
    // A landing page is any page carrying the `.lp` wrapper (portal + every tool
    // home) — detect that so the hero styling is identical across all of them,
    // not just at the hardcoded `/m3/` path or the site root.
    const isHome = !!document.querySelector('.lp') || /\/m3\/$/.test(path) || path === '/' || /index\.html?$/i.test(path);
    if (isHome) document.body.classList.add('has-section-numbers');
    // Tutorial pages (notebooks) get step-numbering
    if (/\/notebooks\//.test(path)) {
      document.body.classList.add('has-tutorial-numbers');
    }
  };

  /* Map each H2 to an editorial eyebrow label for the section divider.
     The CSS ::before uses attr(data-eyebrow); fall-back is "Section". */
  const tagSectionEyebrows = () => {
    if (!document.body.classList.contains('has-section-numbers')) return;
    const map = {
      'how-it-works': 'How it works',
      'start-here':   'Start here',
      'why-m3':       'Why M3',
      'cite-m3':      'Citation',
    };
    document.querySelectorAll('.md-typeset h2[id]').forEach((h) => {
      const slug = h.id;
      if (map[slug]) h.setAttribute('data-eyebrow', map[slug]);
    });
  };

  /* Hero reveal sequence — Linear-style restrained orchestration.
     One reveal per browser session via sessionStorage gate.
     Sequence (total ~1200ms):
       t=0     hero eyebrow fades in
       t=100   wordmark word-by-word stagger
       t=600   tagline slides up
       t=750   CTA pair scales + fades in
       t=900   right column (illustration) fades in */
  const heroReveal = () => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    if (!document.body.classList.contains('has-section-numbers')) return; // home only
    if (sessionStorage.getItem('m3-hero-seen') === '1') return;
    return;  // fade-free hero: render the title instantly, skip the opacity-0 letter-stagger

    const eyebrow = document.querySelector('.hero-eyebrow');
    const h1      = document.querySelector('.md-typeset > h1:first-of-type');
    const tagline = document.querySelector('.hero-tagline');
    const cta     = document.querySelector('.hero-cta');
    const badges  = document.querySelector('.hero-badges');
    const illus   = document.querySelector('.hero-illustration');

    const stage = (el, css) => {
      if (!el) return;
      Object.assign(el.style, css);
    };

    // Stage: initial state (hidden offset)
    stage(eyebrow, { opacity: '0', transform: 'translateY(6px)', transition: 'opacity 400ms ease, transform 400ms ease' });
    stage(tagline, { opacity: '0', transform: 'translateY(8px)', transition: 'opacity 400ms ease, transform 400ms ease' });
    stage(cta,     { opacity: '0', transform: 'scale(0.97)',       transition: 'opacity 400ms ease, transform 400ms ease' });
    stage(badges,  { opacity: '0',                                  transition: 'opacity 400ms ease' });
    stage(illus,   { opacity: '0', transform: 'translateY(8px)', transition: 'opacity 500ms ease, transform 500ms ease' });

    // Wordmark: split into letters for stagger
    let wordmarkSpans = [];
    if (h1) {
      const text = h1.textContent.trim();
      h1.textContent = '';
      [...text].forEach((ch, i) => {
        const sp = document.createElement('span');
        sp.textContent = ch === ' ' ? ' ' : ch;
        sp.style.opacity = '0';
        sp.style.display = 'inline-block';
        sp.style.transform = 'translateY(12px)';
        sp.style.transition = 'opacity 380ms cubic-bezier(0.22,1,0.36,1), transform 380ms cubic-bezier(0.22,1,0.36,1)';
        sp.style.transitionDelay = (100 + i * 35) + 'ms';
        h1.appendChild(sp);
        wordmarkSpans.push(sp);
      });
    }

    // Reveal sequence
    requestAnimationFrame(() => {
      setTimeout(() => stage(eyebrow, { opacity: '1', transform: 'translateY(0)' }), 0);
      wordmarkSpans.forEach(sp => {
        sp.style.opacity = '1';
        sp.style.transform = 'translateY(0)';
      });
      setTimeout(() => stage(tagline, { opacity: '1', transform: 'translateY(0)' }), 600);
      setTimeout(() => stage(cta,     { opacity: '1', transform: 'scale(1)' }),    750);
      setTimeout(() => stage(badges,  { opacity: '1' }),                          800);
      setTimeout(() => stage(illus,   { opacity: '1', transform: 'translateY(0)' }), 900);
    });

    sessionStorage.setItem('m3-hero-seen', '1');
  };

  /* === SWISS-WHITE v0.5 ADDITIONS === */

  /* Magnetic buttons — opt-in via .magnetic class only.
     (Get Started / .lp-cta intentionally excluded — plain button, no pull.) */
  const magneticButtons = () => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    if (window.matchMedia('(pointer: coarse)').matches) return; // touch devices
    const targets = document.querySelectorAll('.magnetic');
    targets.forEach((el) => {
      let raf = null;
      const STRENGTH = 0.18;   // 0..1, higher = more pull
      const RANGE   = 90;      // px of activation radius beyond button bounds
      el.addEventListener('mousemove', (e) => {
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          const r = el.getBoundingClientRect();
          const cx = r.left + r.width / 2;
          const cy = r.top + r.height / 2;
          const dx = e.clientX - cx;
          const dy = e.clientY - cy;
          const dist = Math.hypot(dx, dy);
          const max = Math.max(r.width, r.height) / 2 + RANGE;
          if (dist < max) {
            el.style.transform = `translate3d(${dx * STRENGTH}px, ${dy * STRENGTH}px, 0)`;
          }
        });
      });
      el.addEventListener('mouseleave', () => {
        if (raf) cancelAnimationFrame(raf);
        el.style.transform = '';
      });
    });
  };

  /* Section scroll-spy rail — left-fixed §1 §2 §3 navigator */
  const sectionRail = () => {
    if (!document.body.classList.contains('has-section-numbers')) return;
    if (window.innerWidth < 1280) return;
    const sections = document.querySelectorAll('.lp-hero, .lp-section');
    if (sections.length === 0) return;

    /* Build the rail */
    const rail = document.createElement('aside');
    rail.className = 'section-rail';
    rail.setAttribute('aria-label', 'Section navigation');
    sections.forEach((s, i) => {
      const item = document.createElement('a');
      item.className = 'section-rail__item';
      item.setAttribute('data-rail-idx', String(i));
      item.textContent = '§' + (i + 1);
      item.addEventListener('click', (e) => {
        e.preventDefault();
        s.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      rail.appendChild(item);
    });
    document.body.appendChild(rail);

    /* Activate on scroll via IntersectionObserver */
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const idx = Array.prototype.indexOf.call(sections, entry.target);
          rail.querySelectorAll('.section-rail__item').forEach((it, i) => {
            it.classList.toggle('is-active', i === idx);
          });
        }
      });
    }, { threshold: 0.3, rootMargin: '-30% 0px -30% 0px' });
    sections.forEach((s) => io.observe(s));
  };

  /* Number counter — count up to target on viewport entry */
  const numberCounters = () => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const els = document.querySelectorAll('.count-up');
    if (!els.length || !('IntersectionObserver' in window)) return;
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const target = parseFloat(el.getAttribute('data-target') || el.textContent || '0');
        const duration = 450;
        const start = performance.now();
        const easeOutQuart = (t) => 1 - Math.pow(1 - t, 4);
        const step = (now) => {
          const t = Math.min(1, (now - start) / duration);
          const value = Math.round(target * easeOutQuart(t));
          el.textContent = value.toLocaleString();
          if (t < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
        io.unobserve(el);
      });
    }, { threshold: 0.6 });
    els.forEach((el) => io.observe(el));
  };

  /* GSAP ScrollTrigger — tasteful landing choreography (iter 49, "A 轻度增强").
     Loads only if GSAP global present + motion allowed + on a landing page.
     Fail-open: if GSAP missing, elements render at natural CSS state (visible). */
  const gsapLanding = () => {
    const gsap = window.gsap;
    const ScrollTrigger = window.ScrollTrigger;
    if (!gsap || !ScrollTrigger) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    if (!document.querySelector('.lp')) return;

    gsap.registerPlugin(ScrollTrigger);
    /* instant-nav safety: clear triggers from a previous page */
    ScrollTrigger.getAll().forEach((t) => t.kill());

    const OUT = 'power2.out';

    /* (a) Hero text — stagger children in on load */
    const heroBits = document.querySelectorAll(
      '.lp-hero-text .lp-eyebrow, .lp-hero-text > h1, .lp-hero-text .lp-sub,' +
      '.lp-hero-text .highlight, .lp-hero-text .lp-cta'
    );
    const introTweens = [];
    if (heroBits.length) {
      introTweens.push(gsap.from(heroBits, {
        y: 0, duration: 0.5, ease: OUT,
        stagger: 0.09, delay: 0.05, clearProps: 'all',
      }));
    }

    /* (b) Hero diagram card — fade up on load */
    const card = document.querySelector('.lp-hero-card');
    if (card) {
      introTweens.push(gsap.from(card, {
        y: 0, duration: 0.6, ease: OUT,
        delay: 0.25, clearProps: 'all',
      }));
    }

    /* Safety net (truly fail-open): an on-load from() holds the above-the-fold hero
       at opacity:0 until the rAF ticker advances it — but rAF is PAUSED in a
       backgrounded tab, so the hero could stay blank for a never-focused tab, a
       crawler, or a prerender/screenshot. setTimeout still fires in the background,
       so force any unfinished intro tween to its visible end-state. No-op once the
       (sub-second) entrance has already completed in a normal foreground load. */
    setTimeout(() => {
      introTweens.forEach((tw) => { if (tw && tw.progress() < 1) tw.progress(1); });
      const introEls = [...heroBits, card].filter(Boolean);
      if (introEls.length) gsap.set(introEls, { clearProps: 'all' });
    }, 1600);

    /* Only animate blocks that start BELOW the fold; anything already in the
       initial viewport (e.g. the short ecosystem landing) stays visible, so a
       flaky/late ScrollTrigger or a re-init can never strand it at opacity:0. */
    const belowFold = (el) => el.getBoundingClientRect().top > (window.innerHeight || 800) * 0.9;

    /* (c) Section eyebrows (FEATURES / TUTORIALS) — slide in from left on scroll */
    gsap.utils.toArray('.lp-section .lp-eyebrow').forEach((eb) => {
      if (!belowFold(eb)) return;
      gsap.from(eb, {
        scrollTrigger: { trigger: eb, start: 'top 88%' },
        x: -16, duration: 0.45, ease: OUT, clearProps: 'all',
      });
    });

    /* (d) Cards — staggered fade-up per grid on scroll */
    gsap.utils.toArray('.lp-grid-4').forEach((grid) => {
      const cards = grid.querySelectorAll('.lp-card');
      if (!cards.length) return;
      if (!belowFold(grid)) return;   // in view at setup → keep visible, don't hide
      gsap.from(cards, {
        scrollTrigger: { trigger: grid, start: 'top 85%' },
        y: 26, duration: 0.5, ease: OUT,
        stagger: 0.08, clearProps: 'all',
      });
    });

    /* (e) Feature columns — staggered fade-up on scroll */
    const featRow = document.querySelector('.lp-feature-row');
    if (featRow && belowFold(featRow)) {
      const feats = featRow.querySelectorAll('.lp-feat');
      if (feats.length) {
        gsap.from(feats, {
          scrollTrigger: { trigger: featRow, start: 'top 88%' },
          y: 22, duration: 0.5, ease: OUT,
          stagger: 0.08, clearProps: 'all',
        });
      }
    }

    /* (f) Footer bar — fade up on scroll */
    const footer = document.querySelector('.lp-footer-bar');
    if (footer && belowFold(footer)) {
      gsap.from(footer, {
        scrollTrigger: { trigger: footer, start: 'top 92%' },
        y: 16, duration: 0.5, ease: OUT, clearProps: 'all',
      });
    }

    ScrollTrigger.refresh();

    /* Fail-open safety net for the scroll-revealed blocks (cards / features /
       footer / eyebrows). gsap.from(...{scrollTrigger}) parks them at opacity:0
       until the trigger fires. On a SHORT landing they already sit in the initial
       viewport, so if ScrollTrigger doesn't fire on load (backgrounded tab,
       prerender, headless screenshot, or odd scroll metrics) they'd stay blank.
       After a beat, force any still-hidden, in-view block to its visible state.
       Below-the-fold blocks on a long page are untouched — they reveal on scroll
       as designed (a working foreground load makes this a no-op). */
    setTimeout(() => {
      const vh = window.innerHeight || 800;
      document.querySelectorAll(
        '.lp-card, .lp-feat, .lp-footer-bar, .lp-section .lp-eyebrow'
      ).forEach((el) => {
        const r = el.getBoundingClientRect();
        const inView = r.top < vh && r.bottom > 0;
        if (inView && parseFloat(getComputedStyle(el).opacity) < 0.5) {
          gsap.set(el, { clearProps: 'opacity,transform' });
          el.style.opacity = '';
          el.style.transform = '';
        }
      });
    }, 1700);
  };

  /* Disentanglement animation (iter 50) — the hero centrepiece.
     A cloud of mixed-colour dots (entangled latent z) sorts itself into
     three clean factor clusters (Cell type / Condition / Batch effect),
     then re-mixes. Loops. Represents M3's factorised embeddings. */
  let disentTl = null;
  const disentanglement = () => {
    const svg = document.querySelector('.lp-disent svg');
    if (!svg) return;
    const dotsG = svg.querySelector('.disent-dots');
    if (!dotsG) return;

    /* instant-nav safety: clear prior dots + timeline */
    if (disentTl) { disentTl.kill(); disentTl = null; }
    dotsG.innerHTML = '';

    const NS = 'http://www.w3.org/2000/svg';
    const lanes = [
      { x: 68,  color: '#7c3aed' },  // Cell type   — violet  (biological)
      { x: 178, color: '#e11d48' },  // Condition 1 — rose
      { x: 288, color: '#fb7185' },  // Condition 2 — salmon (condition family)
      { x: 398, color: '#64748b' },  // Batch effect — slate  (removed in correction)
    ];
    const PER = 5;                   // fewer dots
    const R = 6;                     // bigger dots
    const blobCx = 233, blobCy = 116, blobR = 52;
    const laneTop = 74, laneBot = 206;
    const rand = (a, b) => a + Math.random() * (b - a);

    const dots = [];
    lanes.forEach((lane, li) => {
      for (let i = 0; i < PER; i++) {
        const ang = Math.random() * Math.PI * 2;
        const rr = Math.sqrt(Math.random()) * blobR;
        const ex = blobCx + Math.cos(ang) * rr;
        const ey = blobCy + Math.sin(ang) * rr * 0.82;
        const dx = lane.x + rand(-14, 14);
        const dy = rand(laneTop, laneBot);
        const c = document.createElementNS(NS, 'circle');
        c.setAttribute('cx', ex.toFixed(1));
        c.setAttribute('cy', ey.toFixed(1));
        c.setAttribute('r', String(R));
        c.setAttribute('fill', lane.color);
        c.__ex = ex; c.__ey = ey; c.__dx = dx; c.__dy = dy; c.__lane = li;
        dotsG.appendChild(c);
        dots.push(c);
      }
    });
    const batchDots = dots.filter((d) => d.__lane === 3);

    const laneLabels = svg.querySelectorAll('.disent-label');
    const axes = svg.querySelectorAll('.disent-axis line');
    const zLabel = svg.querySelector('.disent-z');
    const batchNote = svg.querySelector('.disent-batch-note');
    const batchLabel = laneLabels[3];
    const batchAxis = axes[3];
    const gsap = window.gsap;

    /* Fallback: no GSAP or reduced motion → rest in disentangled state. */
    if (!gsap || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      dots.forEach((c) => { c.setAttribute('cx', c.__dx.toFixed(1)); c.setAttribute('cy', c.__dy.toFixed(1)); });
      laneLabels.forEach((l) => (l.style.opacity = 1));
      axes.forEach((l) => (l.style.opacity = 1));
      if (zLabel) zLabel.style.opacity = 0;
      return;
    }

    const E = 'power2.inOut';
    gsap.set(laneLabels, { opacity: 0 });
    gsap.set(axes, { opacity: 0, transformOrigin: 'center', scaleX: 0.4 });
    gsap.set(zLabel, { opacity: 1 });
    gsap.set(batchNote, { opacity: 0 });

    disentTl = gsap.timeline({ repeat: -1 });

    /* ── beat 1: hold entangled ── */
    disentTl.to({}, { duration: 0.9 });

    /* ── beat 2: DISENTANGLE into 4 factor clusters ── */
    disentTl.to(zLabel, { opacity: 0, duration: 0.3 }, 'sep');
    disentTl.to(dots, {
      duration: 1.5, ease: E, stagger: 0.015,
      attr: { cx: (i, el) => el.__dx, cy: (i, el) => el.__dy },
    }, 'sep');
    disentTl.to(axes, { opacity: 1, scaleX: 1, duration: 0.5, ease: E }, 'sep+=0.8');
    disentTl.to(laneLabels, { opacity: 1, duration: 0.4, stagger: 0.05 }, 'sep+=0.9');

    /* ── beat 3: hold disentangled ── */
    disentTl.to({}, { duration: 0.7 });

    /* ── beat 4: BATCH CORRECTION — batch cluster fades + drifts away ── */
    disentTl.to(batchDots, { opacity: 0.16, y: 18, duration: 0.6, ease: E }, 'rem');
    disentTl.to([batchLabel, batchAxis], { opacity: 0.28, duration: 0.4 }, 'rem');
    disentTl.to(batchNote, { opacity: 1, duration: 0.4 }, 'rem+=0.25');

    /* ── beat 5: hold corrected ── */
    disentTl.to({}, { duration: 1.0 });

    /* ── beat 6: RE-ENTANGLE (restore batch, merge all) ── */
    disentTl.to(batchNote, { opacity: 0, duration: 0.3 }, 'mer');
    disentTl.to(batchDots, { opacity: 1, y: 0, duration: 0.4, ease: E }, 'mer');
    disentTl.to([batchLabel, batchAxis], { opacity: 0, duration: 0.3 }, 'mer');
    disentTl.to(laneLabels, { opacity: 0, duration: 0.3 }, 'mer');
    disentTl.to(axes, { opacity: 0, scaleX: 0.4, duration: 0.3 }, 'mer');
    disentTl.to(dots, {
      duration: 1.4, ease: E, stagger: 0.015,
      attr: { cx: (i, el) => el.__ex, cy: (i, el) => el.__ey },
    }, 'mer');
    disentTl.to(zLabel, { opacity: 1, duration: 0.4 }, 'mer+=0.7');
  };

  /* ── shared SVG helpers for the task-flow ── */
  const TF_NS = 'http://www.w3.org/2000/svg';
  const tfMk = (t, a) => { const e = document.createElementNS(TF_NS, t); for (const k in a) e.setAttribute(k, a[k]); return e; };
  const tfScene = () => { const e = tfMk('g', { class: 'tf-scene', opacity: 0 }); return e; };
  const tfLabel = (x, y, str, anchor, size, fill, weight) => {
    const t = tfMk('text', { x, y, 'text-anchor': anchor || 'start', 'font-size': size || 8.5, fill: fill || 'currentColor' });
    if (weight) t.setAttribute('font-weight', weight);
    t.textContent = str; return t;
  };
  /* seeded PRNG (mulberry32): a scene drawn twice from one seed is identical,
     and every visit sees the same frame */
  const tfRng = (seed) => () => {
    seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  /* organic blob path (smooth closed curve around a centre) */
  const tfBlob = (cx, cy, rx, ry, rnd) => {
    rnd = rnd || Math.random;
    const n = 12, pts = [];
    for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2; const k = 0.93 + rnd() * 0.12; pts.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]); }
    let d = `M ${pts[0][0].toFixed(1)} ${pts[0][1].toFixed(1)} `;
    for (let i = 0; i < n; i++) {
      const p0 = pts[(i - 1 + n) % n], p1 = pts[i], p2 = pts[(i + 1) % n], p3 = pts[(i + 2) % n];
      const c1x = p1[0] + (p2[0] - p0[0]) / 6, c1y = p1[1] + (p2[1] - p0[1]) / 6;
      const c2x = p2[0] - (p3[0] - p1[0]) / 6, c2y = p2[1] - (p3[1] - p1[1]) / 6;
      d += `C ${c1x.toFixed(1)} ${c1y.toFixed(1)}, ${c2x.toFixed(1)} ${c2y.toFixed(1)}, ${p2[0].toFixed(1)} ${p2[1].toFixed(1)} `;
    }
    return d + 'Z';
  };

  /* right-side legend; appended to scene and registered as a fade-in morph */
  const tfLegend = (morphs, sceneG, x, yTop, rows, immediate) => {
    const g = tfMk('g', {});
    let y = yTop;
    rows.forEach((r) => {
      if (r.title) { g.appendChild(tfLabel(x, y, r.title, 'start', 9, 'currentColor', '700')); y += r.gap || 17; return; }
      if (r.swatch === 'tri') g.appendChild(tfMk('polygon', { points: `${x + 5},${y - 8} ${x + 10},${y} ${x},${y}`, fill: r.color || '#64748b' }));
      else if (r.swatch === 'ring') { const rc = tfMk('circle', { cx: x + 5, cy: y - 3, r: 4.5, fill: 'none', stroke: r.color || 'currentColor', 'stroke-width': 1.4 }); if (r.dashed) rc.setAttribute('stroke-dasharray', '2.5 1.8'); g.appendChild(rc); }
      else if (r.swatch === 'striped') { g.appendChild(tfMk('circle', { cx: x + 5, cy: y - 3, r: 5, fill: r.color })); g.appendChild(tfMk('line', { x1: x + 1.5, y1: y, x2: x + 8.5, y2: y - 7, stroke: '#fff', 'stroke-width': 1.1 })); }
      else if (r.swatch === 'sq') g.appendChild(tfMk('rect', { x, y: y - 8, width: 10, height: 10, rx: 1, fill: r.color }));
      else if (r.swatch === 'dot') g.appendChild(tfMk('circle', { cx: x + 5, cy: y - 3, r: 5, fill: r.color }));
      g.appendChild(tfLabel(x + 18, y, r.text, 'start', 8.5));
      y += r.gap || 15;
    });
    sceneG.appendChild(g);
    // immediate → legend rides the scene fade-in (visible from the start), no delayed reveal
    if (!immediate) morphs.push({ el: g, from: { opacity: 0 }, to: { opacity: 1 }, dur: 0.4, delay: 0.5 });
    return g;
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

  /* Task-flow showcase — the landing card's run → evaluate → plot scenes,
     smooth in-place morphs + per-scene legends. GSAP master timeline. */
  const taskFlow = () => {
    const wrap = document.querySelector('.taskflow');
    // instant-nav: a previous page's hero card may have left its perpetual
    // repeat:-1 timeline running on now-detached nodes (burning rAF forever).
    // Kill it when the current page has no task-flow card.
    if (!wrap) {
      if (window.__tfTl) { window.__tfTl.kill(); window.__tfTl = null; }
      if (window.__tfIO) { window.__tfIO.disconnect(); window.__tfIO = null; }
      return;
    }
    const scenesG = wrap.querySelector('.tf-scenes');
    const headNum = wrap.querySelector('.tf-num');
    const headTitle = wrap.querySelector('.tf-title');
    const dots = wrap.querySelectorAll('.tf-dots span');
    if (!scenesG) return;
    if (window.__tfTl) { window.__tfTl.kill(); window.__tfTl = null; }
    if (window.__tfIO) { window.__tfIO.disconnect(); window.__tfIO = null; }
    scenesG.innerHTML = '';

    const mk = tfMk, label = tfLabel;
    const CT = ['#3b82f6', '#10b981', '#ef4444'];

    const reg = (arr, el, from, to, dur, delay, ease) => arr.push({ el, from, to, dur: dur || 1.3, delay: delay || 0, ease });

    /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
       Scene sets. Each builder returns a fresh `scenes[]` array; the active set
       is chosen by `.taskflow[data-taskflow]`.
       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
    const BUILDERS = {};

    /* ══════════════════════════ kdomainbench ══════════════════════════
       run → estimate k → compare with the true k.
       ① a method is picked and a grey Visium spot array splits into coloured
          layered domains; the tissue then shrinks into the thumbnail of ②;
       ② a model-selection curve over K is drawn and its best K becomes k̂;
       ③ each method's k̂ slides onto a k axis next to the true k, and the
          rows glide into order of |k̂ − k|. */
    BUILDERS.kdomain = () => {
    const scenes = [];
    const VIO = '#7c3aed', VIO_DEEP = '#6d28d9', VIO_SOFT = '#a78bfa';
    const CHIP_BG = '#eef2f7', INK_MUT = '#475569', GREY_SPOT = '#cbd5e1';
    const DOM = ['#4e79a7', '#f28e2b', '#59a14f', '#e15759'];   // the logo's palette
    const appear = (m, el, delay, dur) => { el.setAttribute('opacity', 0); reg(m, el, { opacity: 0 }, { opacity: 1 }, dur || 0.3, delay || 0, 'power2.out'); };

    /* The tissue panel is drawn twice from one lattice: animated in ① and, in
       its finished state, as the thumbnail of ②. */
    const PANEL = { x: 250, y: 30, w: 186, h: 158 };
    const THUMB = { k: 0.42, x: 22, y: 66 };
    const THUMB_TX = THUMB.x - PANEL.x * THUMB.k, THUMB_TY = THUMB.y - PANEL.y * THUMB.k;
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
      const ds = out.map((s) => s.d).sort((a, b) => a - b);
      const cuts = [1, 2, 3].map((q) => ds[Math.floor(ds.length * q / 4)]);
      out.forEach((s) => { s.dom = cuts.filter((c) => s.d >= c).length; });
      return out;
    })();
    const buildTissue = (m) => {
      const rnd = tfRng(7);
      const tis = mk('g', {});
      tis.appendChild(mk('rect', { x: PANEL.x, y: PANEL.y, width: PANEL.w, height: PANEL.h, rx: 8, fill: 'none', stroke: 'currentColor', 'stroke-opacity': 0.2, 'stroke-width': 1.4 }));
      spots.forEach((s) => {
        if (!m) { tis.appendChild(mk('circle', { cx: s.x, cy: s.y, r: 4.3, fill: DOM[s.dom] })); return; }
        // grey spots fade in, then take their domain colour layer by layer
        const c = mk('circle', { cx: s.x, cy: s.y, r: 4.3, fill: GREY_SPOT, opacity: 0 });
        tis.appendChild(c);
        reg(m, c, { opacity: 0, attr: { fill: GREY_SPOT } }, { opacity: 1 }, 0.35, 0.3 + rnd() * 0.5, 'power2.out');
        reg(m, c, {}, { attr: { fill: DOM[s.dom] } }, 0.45, T_ARRIVE + 0.1 + s.dom * 0.18 + rnd() * 0.12, 'power2.out');
      });
      if (m) {
        const ping = mk('rect', { x: PANEL.x, y: PANEL.y, width: PANEL.w, height: PANEL.h, rx: 8, fill: 'none', stroke: VIO, 'stroke-width': 1.8, opacity: 0 });
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
      const SEL = 2;                                  // CellCharter — the tutorials' worked example
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
          reg(m, chip, {}, { attr: { fill: VIO } }, 0.25, T_PICK, 'power2.out');
          reg(m, txt, {}, { attr: { fill: '#fff', 'font-weight': 700 } }, 0.25, T_PICK, 'power2.out');
          reg(m, row, {}, { y: -5, scale: 1.06 }, 0.33, T_PICK, 'power3.out');
          reg(m, row, {}, { y: 0, scale: 0.985 }, 0.25, T_LAND, 'power2.in');
          reg(m, row, {}, { scale: 1 }, 0.2, T_RUN, 'power3.out');
        } else {
          reg(m, row, {}, { opacity: 0.55 }, 0.3, T_PICK, 'power2.out');
        }
      });
      list.appendChild(selRow);

      const ring = mk('rect', { x: rx - 3, y: rowY(0) - 3, width: rw + 6, height: rh + 6, rx: 6, fill: 'none', stroke: VIO, 'stroke-width': 1.8, opacity: 0 });
      list.appendChild(ring);
      reg(m, ring, { opacity: 0, y: 0 }, { opacity: 1 }, 0.2, 0.8, 'power2.out');
      reg(m, ring, {}, { y: rowY(SEL) - rowY(0) }, 0.55, 0.95, 'power3.inOut');
      reg(m, ring, {}, { opacity: 0 }, 0.25, T_PICK, 'power2.out');

      const wx0 = rx + rw + 5, wx1 = PANEL.x - 3, wLen = wx1 - wx0;
      const wire = mk('line', { x1: wx0, y1: selCY, x2: wx1, y2: selCY, stroke: VIO, 'stroke-width': 1.8, 'stroke-linecap': 'round', 'stroke-dasharray': wLen, 'stroke-dashoffset': wLen, opacity: 0 });
      g.appendChild(wire);
      reg(m, wire, { opacity: 0, attr: { 'stroke-dashoffset': wLen } }, { opacity: 1 }, 0.05, T_RUN, 'none');
      reg(m, wire, {}, { attr: { 'stroke-dashoffset': 0 } }, T_ARRIVE - T_RUN, T_RUN, 'power2.inOut');
      reg(m, wire, {}, { opacity: 0.45 }, 0.5, T_ARRIVE + 0.1, 'power2.out');
      const head = mk('circle', { cx: wx0, cy: selCY, r: 3.2, fill: VIO, opacity: 0 });
      g.appendChild(head);
      reg(m, head, { opacity: 0, x: 0 }, { opacity: 1 }, 0.05, T_RUN, 'none');
      reg(m, head, {}, { x: wLen }, T_ARRIVE - T_RUN, T_RUN, 'power2.inOut');
      reg(m, head, {}, { opacity: 0 }, 0.12, T_ARRIVE, 'power2.out');

      const tis = buildTissue(m);
      tis.setAttribute('opacity', 0);
      g.appendChild(tis);
      reg(m, tis, { opacity: 0, x: 0, y: 0, scale: 1, svgOrigin: '0 0' }, { opacity: 1 }, 0.4, 0.3, 'power2.out');
      const cap = label(PANEL.x + PANEL.w / 2, 204, 'Spatial domains', 'middle', 9, 'currentColor', '600');
      cap.setAttribute('opacity', 0);
      g.appendChild(cap);
      reg(m, cap, { opacity: 0 }, { opacity: 1 }, 0.5, T_ARRIVE + 0.8, 'power2.out');

      // hand-over to ②: the tissue travels to the thumbnail slot
      [list, wire, cap].forEach((el) => ex.push({ el, to: { opacity: 0 }, dur: 0.3, delay: 0, ease: 'power2.in' }));
      const O = 1.03;
      ex.push({ el: tis, to: { x: THUMB_TX * O, y: THUMB_TY * O, scale: 1 + (THUMB.k - 1) * O }, dur: 0.8, delay: 0.1, ease: 'power2.inOut' });
      ex.push({ el: tis, to: { x: THUMB_TX, y: THUMB_TY, scale: THUMB.k }, dur: 0.3, delay: 0.9, ease: 'power3.out' });
      scenes.push({ num: 1, title: 'Run a method', g, morphs: m, exits: ex, hold: 2.8 });
    })();

    /* ② Estimate k — a model-selection score over K; its best K becomes k̂ */
    (() => {
      const g = tfScene(); const m = [];
      const thumb = buildTissue(null);
      thumb.setAttribute('transform', `translate(${THUMB_TX} ${THUMB_TY}) scale(${THUMB.k})`);
      g.appendChild(thumb);
      const tcx = THUMB.x + PANEL.w * THUMB.k / 2, tcy = THUMB.y + PANEL.h * THUMB.k / 2;
      const glab = label(tcx, THUMB.y + PANEL.h * THUMB.k + 15, 'Domains', 'middle', 8.5, 'currentColor', '600');
      g.appendChild(glab); appear(m, glab, 0.05);

      // axes: K = 2 … 14, score in [0, 1]
      const ax0 = 160, ax1 = 430, ay0 = 172, ay1 = 36;
      const Ks = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14];
      const SC = [0.30, 0.42, 0.55, 0.63, 0.74, 0.86, 0.71, 0.62, 0.55, 0.50, 0.45, 0.41, 0.38];
      const BEST = SC.indexOf(Math.max(...SC));
      const px = (i) => ax0 + 8 + i * (ax1 - ax0 - 16) / (Ks.length - 1);
      const py = (v) => ay0 - v * (ay0 - ay1);

      const wx0 = THUMB.x + PANEL.w * THUMB.k + 5, wx1 = ax0 - 14, wLen = wx1 - wx0;
      const wire = mk('line', { x1: wx0, y1: tcy, x2: wx1, y2: tcy, stroke: '#94a3b8', 'stroke-width': 1.6, 'stroke-linecap': 'round', 'stroke-dasharray': wLen, 'stroke-dashoffset': wLen });
      g.appendChild(wire);
      reg(m, wire, { attr: { 'stroke-dashoffset': wLen } }, { attr: { 'stroke-dashoffset': 0 } }, 0.4, 0.15, 'power2.inOut');

      const axes = mk('path', { d: `M ${ax0} ${ay1 - 4} V ${ay0} H ${ax1}`, fill: 'none', stroke: 'currentColor', 'stroke-opacity': 0.35, 'stroke-width': 1.2 });
      g.appendChild(axes); appear(m, axes, 0.3);
      const yl = label(ax0 - 6, ay1 + 2, 'score', 'end', 8, 'currentColor', '600');
      g.appendChild(yl); appear(m, yl, 0.35);
      [0, 3, 5, 8, 12].forEach((i) => {
        const t = label(px(i), ay0 + 12, String(Ks[i]), 'middle', 8, INK_MUT, '500');
        g.appendChild(t); appear(m, t, 0.35);
      });
      const xl = label(ax1, ay0 + 24, 'K (2 … kmax)', 'end', 8, 'currentColor', '600');
      g.appendChild(xl); appear(m, xl, 0.4);

      // the curve is drawn left to right; each point lands as the pen passes it
      const pts = SC.map((v, i) => [px(i), py(v)]);
      let len = 0; const at = [0];
      for (let i = 1; i < pts.length; i++) { len += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); at.push(len); }
      const T_LINE = 0.7, D_LINE = 1.6;
      const curve = mk('polyline', { points: pts.map((p) => p.join(',')).join(' '), fill: 'none', stroke: VIO_SOFT, 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-dasharray': len, 'stroke-dashoffset': len });
      g.appendChild(curve);
      reg(m, curve, { attr: { 'stroke-dashoffset': len } }, { attr: { 'stroke-dashoffset': 0 } }, D_LINE, T_LINE, 'none');
      pts.forEach((p, i) => {
        const c = mk('circle', { cx: p[0], cy: p[1], r: 3, fill: VIO_SOFT });
        g.appendChild(c);
        reg(m, c, { opacity: 0, scale: 0, svgOrigin: p[0] + ' ' + p[1] }, { opacity: 1, scale: 1 }, 0.25, T_LINE + D_LINE * at[i] / len, 'back.out(2)');
      });

      // the best K: drop line, deep-coloured point, k̂ label
      const T_BEST = T_LINE + D_LINE + 0.35;
      const [bx, by] = pts[BEST];
      const drop = mk('line', { x1: bx, y1: by + 5, x2: bx, y2: ay0, stroke: VIO, 'stroke-width': 1.3, 'stroke-dasharray': '3 2.5' });
      g.appendChild(drop); appear(m, drop, T_BEST + 0.2);
      const halo = mk('circle', { cx: bx, cy: by, r: 9, fill: VIO, opacity: 0 });
      g.appendChild(halo);
      reg(m, halo, { opacity: 0, scale: 0.4, svgOrigin: bx + ' ' + by }, { opacity: 0.15, scale: 1 }, 0.4, T_BEST, 'back.out(1.7)');
      const best = mk('circle', { cx: bx, cy: by, r: 4.6, fill: VIO_DEEP });
      g.appendChild(best);
      reg(m, best, { opacity: 0, scale: 0, svgOrigin: bx + ' ' + by }, { opacity: 1, scale: 1 }, 0.35, T_BEST, 'back.out(2)');
      const kl = label(bx + 12, by - 6, 'k̂ = ' + Ks[BEST], 'start', 11, VIO_DEEP, '700');
      g.appendChild(kl); appear(m, kl, T_BEST + 0.3, 0.35);
      scenes.push({ num: 2, title: 'Estimate k', g, morphs: m, hold: 3 });
    })();

    /* ③ Compare — each method's k̂ on a k axis next to the true k; rows glide
       into order of |k̂ − k| and the closest method is outlined */
    (() => {
      const g = tfScene(); const m = [];
      const TRUE_K = 7;
      const methods = ['Method 1', 'Method 2', 'Method 3', 'Method 4', 'Method 5'];
      const KHAT = [4, 7, 10, 2, 6];
      const err = KHAT.map((k) => Math.abs(k - TRUE_K));
      const order = err.map((_, i) => i).sort((a, b) => err[a] - err[b] || a - b);
      const rank = err.map((_, i) => order.indexOf(i));
      const BEST = order[0];
      const kx0 = 132, kx1 = 400, y0 = 62, ch = 25;
      const kx = (k) => kx0 + (k - 1) * (kx1 - kx0) / 11;   // k = 1 … 12
      const T_SLIDE = 0.6, T_SORT = 2.3, T_TRACE = 3.0, T_CLOSE = 3.9;

      const bx = 44, by = y0 - 12, bw = 380, bhh = 24, brx = 6;
      const band = mk('rect', { x: bx, y: by, width: bw, height: bhh, rx: brx, fill: VIO, opacity: 0 });
      g.appendChild(band);
      reg(m, band, { opacity: 0 }, { opacity: 0.08 }, 0.4, T_CLOSE, 'power2.out');

      // k axis with ticks, and the true k as a dashed reference line
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
      const tl = mk('line', { x1: kx(TRUE_K), y1: 32, x2: kx(TRUE_K), y2: axY, stroke: '#0f172a', 'stroke-opacity': 0.55, 'stroke-width': 1.3, 'stroke-dasharray': '4 3' });
      tl.setAttribute('stroke', 'currentColor');
      g.appendChild(tl); appear(m, tl, 0.15);
      const tlab = label(kx(TRUE_K), 27, 'true k = ' + TRUE_K, 'middle', 8.5, 'currentColor', '700');
      g.appendChild(tlab); appear(m, tlab, 0.15);

      const tRow = [0.2, 0.35, 0.47, 0.57, 0.65];
      methods.forEach((nm, i) => {
        const row = mk('g', {});
        const cy = y0 + i * ch, best = (i === BEST);
        const name = label(96, cy + 3, nm, 'end', 8, 'currentColor', '500');
        row.appendChild(name); appear(m, name, tRow[i]);
        // the error segment between k̂ and the true k grows with the dot
        const seg = mk('line', { x1: kx(TRUE_K), y1: cy, x2: kx(TRUE_K), y2: cy, stroke: VIO_SOFT, 'stroke-width': 3, 'stroke-linecap': 'round', opacity: 0.45 });
        row.appendChild(seg);
        reg(m, seg, { attr: { x2: kx(TRUE_K) } }, { attr: { x2: kx(KHAT[i]) } }, 0.7, T_SLIDE + tRow[i], 'power3.out');
        const dot = mk('circle', { cx: kx(TRUE_K), cy, r: 5.5, fill: VIO_SOFT });
        row.appendChild(dot);
        reg(m, dot, { opacity: 0, attr: { cx: kx(TRUE_K) } }, { opacity: 1 }, 0.2, T_SLIDE + tRow[i], 'power2.out');
        reg(m, dot, {}, { attr: { cx: kx(KHAT[i]) } }, 0.7, T_SLIDE + tRow[i], 'power3.out');
        const val = label(kx(KHAT[i]) + (KHAT[i] < TRUE_K ? -10 : 10), cy + 3, String(KHAT[i]), KHAT[i] < TRUE_K ? 'end' : 'start', 8, INK_MUT, '600');
        if (KHAT[i] === TRUE_K) { val.setAttribute('x', kx(KHAT[i]) + 10); val.setAttribute('text-anchor', 'start'); }
        row.appendChild(val); appear(m, val, T_SLIDE + tRow[i] + 0.6, 0.3);
        if (best) {
          reg(m, dot, {}, { attr: { fill: VIO_DEEP } }, 0.3, T_CLOSE, 'power2.out');
          reg(m, name, {}, { attr: { 'font-weight': 700 } }, 0.2, T_CLOSE, 'power2.out');
        }
        g.appendChild(row);
        if (rank[i] !== i) reg(m, row, { y: 0 }, { y: (rank[i] - i) * ch }, 0.6, T_SORT + i * 0.05, 'power2.inOut');
      });

      const P = 2 * (bw + bhh) - 8 * brx + 2 * Math.PI * brx, PEN = 0.05 * P;
      const outline = { x: bx, y: by, width: bw, height: bhh, rx: brx, fill: 'none', stroke: VIO, 'stroke-linecap': 'round' };
      const trace = mk('rect', Object.assign({ 'stroke-width': 1.6, 'stroke-dasharray': P, 'stroke-dashoffset': P, opacity: 0 }, outline));
      const pen = mk('rect', Object.assign({ 'stroke-width': 3, 'stroke-dasharray': PEN + ' ' + (P - PEN), 'stroke-dashoffset': PEN, opacity: 0 }, outline));
      g.appendChild(trace); g.appendChild(pen);
      reg(m, trace, { opacity: 0, attr: { 'stroke-dashoffset': P, 'stroke-width': 1.6 } }, { opacity: 1 }, 0.05, T_TRACE, 'none');
      reg(m, trace, {}, { attr: { 'stroke-dashoffset': 0 } }, T_CLOSE - T_TRACE, T_TRACE, 'power2.inOut');
      reg(m, trace, {}, { opacity: 0 }, 0.35, T_CLOSE + 0.3, 'power2.out');
      reg(m, pen, { opacity: 0, attr: { 'stroke-dashoffset': PEN } }, { opacity: 1 }, 0.05, T_TRACE, 'none');
      reg(m, pen, {}, { attr: { 'stroke-dashoffset': PEN - P } }, T_CLOSE - T_TRACE, T_TRACE, 'power2.inOut');
      reg(m, pen, {}, { opacity: 0 }, 0.08, T_CLOSE - 0.04, 'none');
      scenes.push({ num: 3, title: 'Compare with the true k', g, morphs: m, hold: 3.2 });
    })();

    return scenes;
    };  /* end BUILDERS.kdomain */

    /* ── Render the active scene-set; dots are rebuilt to match its length ── */
    const render = (key) => {
      if (!BUILDERS[key]) key = 'kdomain';
      if (window.__tfTl) { window.__tfTl.kill(); window.__tfTl = null; }
      scenesG.innerHTML = '';
      const scenes = BUILDERS[key]();
      scenes.forEach((s) => scenesG.appendChild(s.g));

      const dotsWrap = wrap.querySelector('.tf-dots');
      if (dotsWrap) {
        dotsWrap.innerHTML = '';
        scenes.forEach((_, i) => {
          const sp = document.createElement('span');
          if (i === 0) sp.className = 'is-active';
          dotsWrap.appendChild(sp);
        });
      }
      const dots = wrap.querySelectorAll('.tf-dots span');

    const setHead = (i) => {
      headNum.textContent = scenes[i].num;
      headTitle.textContent = scenes[i].title;
      dots.forEach((d, j) => d.classList.toggle('is-active', j === i));
    };

    const gsap = window.gsap;
    setHead(0);
    // No GSAP (its script did not load) or reduced motion: show the first scene as a still frame.
    if (!gsap || REDUCED_MOTION) { tfStill(scenes[0]); return; }

    const master = gsap.timeline({ repeat: -1 });
    window.__tfTl = master;
    const startTimes = [];                   // where each scene begins on the master
    const builtAt = [];                      // where each scene's build-up has finished
    scenes.forEach((s, idx) => {
      startTimes[idx] = master.duration();   // current end = this scene's start time
      const st = gsap.timeline();
      /* enter 'cut': the previous scene has moved its own elements onto this
         scene's first frame, so the scene appears at once and builds round them */
      const cut = s.enter === 'cut';
      const lead = cut ? 0 : 0.45;
      st.call(() => setHead(idx), null, 0);
      st.set(s.g, { opacity: cut ? 1 : 0 }, 0);
      s.morphs.forEach((mo) => st.set(mo.el, mo.from, 0));
      if (!cut) st.to(s.g, { opacity: 1, duration: 0.4, ease: 'power2.out' }, 0);
      let maxEnd = lead;
      s.morphs.forEach((mo) => {
        st.to(mo.el, Object.assign({ duration: mo.dur, ease: mo.ease || 'power2.inOut', delay: mo.delay }, mo.to), lead);
        maxEnd = Math.max(maxEnd, lead + mo.delay + mo.dur);
      });
      /* the finished frame rests, then the scene either hands its elements to
         the next one (exits) or fades as a whole */
      const tExit = maxEnd + (s.hold || 3);
      if (s.exits && s.exits.length) {
        let exitEnd = tExit;
        // the hand-over already belongs to the next step: retitle the card as it starts
        st.call(() => setHead((idx + 1) % scenes.length), null, tExit + 0.1);
        s.exits.forEach((mo) => {
          st.to(mo.el, Object.assign({ duration: mo.dur, ease: mo.ease || 'power2.inOut' }, mo.to), tExit + mo.delay);
          exitEnd = Math.max(exitEnd, tExit + mo.delay + mo.dur);
        });
        st.set(s.g, { opacity: 0 }, exitEnd);
      } else {
        st.to(s.g, { opacity: 0, duration: 0.45, ease: 'power2.in' }, tExit);
      }
      builtAt[idx] = startTimes[idx] + maxEnd;
      master.add(st);
    });

    /* Open the loop on the first scene's finished frame. seek() renders at
       once, without waiting for an animation frame, so the card has content
       in a headless render, a background tab or a paused timeline. The next
       loops play the first scene's build-up from the start. */
    master.seek(builtAt[0]);

    /* Clickable dots: jump to any scene and keep auto-playing from there.
       The master is one declarative timeline, so seeking to a scene's start
       renders that scene's exact state; play() resumes the loop. Dots are
       rebuilt on every render(), so handlers are wired fresh each switch
       (old dot elements — and their listeners — are discarded). */
    dots.forEach((dot, i) => {
      /* a hair past the scene's start: a scene that has never played does not
         render its first frame at exactly its own time 0 */
      dot.addEventListener('click', () => { setHead(i); master.seek(startTimes[i] + 0.001).play(); });
    });
    };  /* end render() */

    render((wrap.dataset.taskflow) || 'kdomain');

    /* Perf: pause the perpetual loop when the card is scrolled off-screen, so it
       isn't burning CPU/rAF the whole time you're reading further down the page. */
    if ('IntersectionObserver' in window) {
      /* The observer must die with the timeline it controls: a stale observer
         from a previous instant-nav visit can deliver a late "not intersecting"
         record for its now-detached card and pause the NEW page's timeline
         through the shared window.__tfTl - the "animation stuck after
         navigating back" bug. Hence the global handle + isConnected guard. */
      window.__tfIO = new IntersectionObserver((ents) => {
        ents.forEach((e) => {
          if (!e.target.isConnected) return;
          const tl = window.__tfTl;
          if (tl) { e.isIntersecting ? tl.play() : tl.pause(); }
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
    let raf = null;
    const move = () => {
      raf = null;
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
    const schedule = () => { if (raf == null) raf = requestAnimationFrame(move); };
    if (!window.__tocSliderWired) {
      window.__tocSliderWired = true;
      window.addEventListener('scroll', schedule, { passive: true });
      window.addEventListener('resize', schedule, { passive: true });
      // NOTE: a document.body-wide class MutationObserver used to re-run move()
      // (a getBoundingClientRect reflow) on EVERY class change Material makes —
      // scrollspy, header autohide, nav state — thrashing layout on every nav
      // click and every scroll frame. Removed; scroll/resize + the timed move()
      // calls below and the per-navigation re-init keep the indicator in sync.
    }
    move();                      // create + position the bar immediately
    setTimeout(move, 400);       // re-position after fonts/layout settle
    setTimeout(move, 1200);      // and once more after instant-nav / late render
  };

  const init = () => {
    if (REDUCED_MOTION) { taskFlow(); return; }
    enableSectionNumbersOnHome();
    tagSectionEyebrows();
    heroReveal();
    initFadeUp();
    stickyHeader();
    scrollProgress();
    backToTop();
    magneticButtons();
    numberCounters();
    gsapLanding();
    taskFlow();
    tocSlider();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  if (typeof document$ !== 'undefined' && document$.subscribe) {
    document$.subscribe(init);
  }
})();
