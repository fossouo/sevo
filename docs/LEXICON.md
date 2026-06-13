# French lexical resource — integration contract

The French side is graded against a **lexical resource**, not a hardcoded list.
A resource is only accepted under a strict gate, so credibility never rests on an
opaque dump.

## What a resource must carry

* **Verified license** (`ResourceManifest.license` ∈ `VERIFIED_LICENSES`) — never
  `unknown`/empty. Loading an unlicensed resource raises `ProvenanceError`.
* **Traceable per-entry source** — every `LexEntry` has a non-empty `source`
  (e.g. `manulex`, `dubois-buyse`, `bo-cp`). A sourceless entry is refused.
* **Grade level** (`grade`) — used by `is_age_appropriate` and the splits.
* **Frequency band** (`freq_band`).
* **Inflected forms** (`forms`) — plurals / conjugations, so a form resolves to
  its lemma.

## Train / held-out / transfer split

`LexiconResource.split(grade, rng)` partitions a grade's lemmas into **disjoint**
`train` / `heldout` / `transfer` sets (deterministic for a seed). This is the
lexical counterpart of the anti-leakage banks: teaching draws from `train`, the
oracle evaluates on `heldout` / `transfer`. The live Emma adapter can be passed
the `train` set (`generate_french_tasks(..., allowed_words=train)`) so it can
**never propose a held-out/transfer word as a teaching item**.

## Bundled seed vs. full resource

`builtin_resource()` is a **hand-verified CP/CE1 seed** (`license="curated-internal"`,
sources modelled on Manulex / Dubois-Buyse / BO CP) — a partial bootstrap, **not**
the full database.

To plug a real resource, parse your licensed export into rows and load it under
its manifest:

```python
from sevo.curriculum.fr_lexicon import load_external, ResourceManifest

rows = [...]  # [{"lemma","forms","pos","freq_band","grade","source"}, ...]  parsed from CSV/JSON
res = load_external(rows, ResourceManifest(
    name="manulex-2004", license="LGPLLR",         # must be a verified license
    source="Manulex (Lété, Sprenger-Charolles & Colé, 2004)",
    url="https://...", retrieved="2026-06-13"))
```

The same gate runs: a missing license or any sourceless entry is refused. The raw
licensed dataset is **never committed** to this repo — only the manifest + the
loader live here.
