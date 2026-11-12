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
  kDomainBench benchmarks ten methods that estimate the number of spatial
  domains (<em>k</em>) in spatial transcriptomics data. The <code>kdomainbench</code>
  package runs each method from Python and compares its estimated <em>k</em>
  with the number of domains in a manual reference annotation. It is for researchers who want
  to estimate <em>k</em> for their own 10x Visium samples, or to compare k-estimation methods.
</p>

```python
import kdomainbench as kdb
clusters = kdb.run("SpaGCN", "sample.h5ad")
```

[Get started](installation.md){ .md-button .md-button--primary .lp-cta }
[How it works](overview.md){ .md-button .lp-cta }

</div>
<div class="lp-hero-card">
<div class="taskflow">
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
<text x="384" y="119" font-size="10" fill="#475569">k error, ARI, NMI</text>
</g>
</g></svg>
</div>
<div class="tf-dots"></div>
</div>
</div>
</div>
</section>

<!-- ━━━━━━━━━━━━━━━━━━━━ TUTORIAL CARDS (4-across link cards) ━━━━━━━━━━━━━━━━━━━━ -->
<section class="lp-section" markdown>
<div class="lp-grid-4" markdown>
<div class="lp-card lp-card-link" markdown="span">
[<span class="lp-card-kicker">Discover</span><span class="lp-card-title">Discover methods</span><span class="lp-card-desc">See what each method needs and how it picks the number of domains.</span>](tutorials/discover.md){ .lp-card-cover }
</div>
<div class="lp-card lp-card-link" markdown="span">
[<span class="lp-card-kicker">Run</span><span class="lp-card-title">Run a method</span><span class="lp-card-desc">Run any of the ten methods on an <code>.h5ad</code> file, each in the environment it needs.</span>](tutorials/run.md){ .lp-card-cover }
</div>
<div class="lp-card lp-card-link" markdown="span">
[<span class="lp-card-kicker">Benchmark</span><span class="lp-card-title">Benchmark the ten methods</span><span class="lp-card-desc">Run all ten methods on one sample, then compare k error, ARI, the domains and the twelve metrics.</span>](tutorials/benchmark.md){ .lp-card-cover }
</div>
<div class="lp-card lp-card-link" markdown="span">
[<span class="lp-card-kicker">Your data</span><span class="lp-card-title">Your own data</span><span class="lp-card-desc">From a Space Ranger folder to domains on the tissue, with or without an annotation.</span>](how-to/own_data.md){ .lp-card-cover }
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
<span class="lp-feat-title">Three environments, one call</span>
<span class="lp-feat-desc">The Python methods run in two version-locked conda environments (PyTorch, TensorFlow), the R methods in your own R. <code>kdb.run</code> starts each method in the right one.</span>
</div>
<div class="lp-feat">
<span class="lp-feat-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="12" width="3" height="6"/><rect x="12" y="8" width="3" height="10"/><rect x="17" y="5" width="3" height="13"/></svg></span>
<span class="lp-feat-title">Scored against the annotation</span>
<span class="lp-feat-desc">Every run records its estimated <em>k</em>. <code>kdb.evaluate</code> adds the <em>k</em> error, ARI and NMI against the reference annotation, and <code>kdb.metrics</code> the twelve metrics of the paper.</span>
</div>
</div>
</section>

</div>
