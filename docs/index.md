---
hide:
  - navigation
  - toc
---

<div class="lp" markdown>

<!-- ━━━━━━━━━━━━━━━━━━━━ HERO (text + task-flow card) ━━━━━━━━━━━━━━━━━━━━ -->
<section class="lp-hero" markdown>
<div class="lp-hero-text" markdown>

# kDomainBench

<p class="lp-sub">
  kDomainBench is a benchmark of methods that estimate the number of spatial
  domains (<em>k</em>) in spatial transcriptomics data. The <code>kdomainbench</code>
  package runs 10 of them from Python and scores the estimated <em>k</em>
  against the ground truth.
</p>

```bash
pip install -e kdomainbench
```

[Get started](quickstart.md){ .md-button .md-button--primary .lp-cta }
[How it works](methods.md){ .md-button .lp-cta }

</div>
<div class="lp-hero-card">
<div class="taskflow" data-taskflow="kdomain">
<div class="tf-main">
<div class="tf-head">
<span class="tf-num">1</span>
<span class="tf-title">Run a method</span>
</div>
<div class="tf-stage">
<svg viewBox="0 0 460 210" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif" aria-hidden="true"><g class="tf-scenes">
<g class="tf-fallback" font-size="12" text-anchor="middle" fill="#1e293b">
<rect x="14" y="78" width="124" height="54" rx="8" fill="#eef2f7"/>
<text x="76" y="102" font-weight="700">Run a method</text>
<text x="76" y="119" font-size="10" fill="#475569">10 methods</text>
<path d="M144 105 H164 M158 100 L164 105 L158 110" fill="none" stroke="#94a3b8" stroke-width="1.6"/>
<rect x="168" y="78" width="124" height="54" rx="8" fill="#eef2f7"/>
<text x="230" y="102" font-weight="700">Estimate k</text>
<text x="230" y="119" font-size="10" fill="#475569">model selection</text>
<path d="M298 105 H318 M312 100 L318 105 L312 110" fill="none" stroke="#94a3b8" stroke-width="1.6"/>
<rect x="322" y="78" width="124" height="54" rx="8" fill="#eef2f7"/>
<text x="384" y="102" font-weight="700">Compare</text>
<text x="384" y="119" font-size="10" fill="#475569">k error, ARI, runtime</text>
</g>
</g></svg>
</div>
<div class="tf-dots"><span class="is-active"></span></div>
</div>
</div>
</div>
</section>

<!-- ━━━━━━━━━━━━━━━━━━━━ TUTORIAL CARDS (4-across link cards) ━━━━━━━━━━━━━━━━━━━━ -->
<section class="lp-section">
<div class="lp-grid-4">
<div class="lp-card lp-card-link">
<a class="lp-card-cover" href="guide/discover.html">
<span class="lp-card-kicker">Discover</span>
<span class="lp-card-title">Find a method</span>
<span class="lp-card-desc">See what each method needs and how it picks the number of domains.</span>
</a>
</div>
<div class="lp-card lp-card-link">
<a class="lp-card-cover" href="guide/run.html">
<span class="lp-card-kicker">Run</span>
<span class="lp-card-title">Run a method</span>
<span class="lp-card-desc">Run any of the 10 methods on an <code>.h5ad</code> file, each in its own environment.</span>
</a>
</div>
<div class="lp-card lp-card-link">
<a class="lp-card-cover" href="tutorials/benchmark.html">
<span class="lp-card-kicker">Benchmark</span>
<span class="lp-card-title">Compare estimated k</span>
<span class="lp-card-desc">Run all ten methods, then compare k error, ARI, domains and cost against the ground truth.</span>
</a>
</div>
<div class="lp-card lp-card-link">
<a class="lp-card-cover" href="api.html">
<span class="lp-card-kicker">Reference</span>
<span class="lp-card-title">API reference</span>
<span class="lp-card-desc">Every function of <code>kdomainbench</code>, with its parameters and examples.</span>
</a>
</div>
</div>
</section>

<!-- ━━━━━━━━━━━━━━━━━━━━ FEATURES (three pillars, full-width grey band) ━━━━━━━━━━━━━━━━━━━━ -->
<section class="lp-section lp-section--band">
<div class="lp-feature-row">
<div class="lp-feat">
<span class="lp-feat-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5Z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/></svg></span>
<span class="lp-feat-title">10 methods, one API</span>
<span class="lp-feat-desc">Six R methods (PRECAST, SC.MEB, BayesSpace, BNPSpace, DR.SC, iSC.MEB) and four Python methods (CellCharter, DeepST, SpaGCN, SpatialDE2) through <code>kdb.run</code>.</span>
</div>
<div class="lp-feat">
<span class="lp-feat-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg></span>
<span class="lp-feat-title">Reproducible environments</span>
<span class="lp-feat-desc">The Python methods run in two locked conda environments (PyTorch, TensorFlow), the R methods in your own R. The method scripts are the benchmark's own.</span>
</div>
<div class="lp-feat">
<span class="lp-feat-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="12" width="3" height="6"/><rect x="12" y="8" width="3" height="10"/><rect x="17" y="5" width="3" height="13"/></svg></span>
<span class="lp-feat-title">Scored against the truth</span>
<span class="lp-feat-desc">Every run records the estimated <em>k</em>, wall time and peak memory. <code>kdb.evaluate</code> adds the <em>k</em> error, ARI and NMI against the ground-truth domains.</span>
</div>
</div>
</section>

</div>
