# Reproduction

How a third party re-runs this end to end. The standard cyclegraph applies to a vendor's
measurement applies here first: if this document does not let a stranger obtain commensurable
numbers, the project has failed on its own terms.

**Current state: there is nothing to reproduce.** W0 is documentation only. What follows is
the path as it is being built, and the free portion of it is already real.

## Prerequisites

- Python 3.11 or later.
- `ffmpeg` on `PATH`, built with `https` and `tls` protocol support. Check with
  `ffmpeg -protocols | grep -E 'https|subfile'`; the corpus path needs both.
- For anything touching the corpus: a Hugging Face token with `builddotai/Egocentric-10K`'s
  terms accepted. The dataset is gated. Put it in `.env`; see `.env.example`. The token is
  read-only, is never committed (`make privacy-gate` and `.gitignore`), and should be
  rotated at `huggingface.co/settings/tokens` after the corpus reads are done or if it was
  ever pasted anywhere other than `.env`.
- For E6 onward: nothing to buy. The HAL mappings are the two open, peer-reviewed equations
  in `docs/SURVEY.md` S3, transcribed into `src/cyclegraph/exposure/hal.py` with golden
  tests against the papers' table cells.

## The free path — $0, no token, no network

Everything that verifies the repository's internal consistency runs offline.

```
git clone <this repo> && cd cyclegraph
pip install -e ".[dev]"
make validate
```

That runs the privacy gate, the placeholder gate, the cited-path gate, the test suite and
`mypy --strict`. It is the whole of W0's deliverable and it passes with `src/` empty — which
is the point: the gates work on documentation alone, so the ordering claim is checkable
before any code exists.

## Compute

- **Corpus reads** (E1, E2): any machine with `ffmpeg` and network. No GPU.
- **Probe, detector, flow** (E3): GPU, on **AWS through the CLI** — a single `g5.xlarge`
  (A10G, 24 GB) is enough for 100DOH at ~20 frames/s and RAFT-small flow; the pilot's ~1.7M
  frames is ~24 GPU-hours, so a spot instance with checkpointed progress, not a long-lived
  box. Launch, run the stage, pull `results/` down, terminate. `AWS_PROFILE`/`AWS_REGION` in
  `.env` name the account; nothing in this repository provisions infrastructure, and the
  instance does not need the HF token beyond the corpus reads it performs.
- **Judge** (E3 calibration subset): the sibling's self-hosted Qwen3-VL route
  (`../vernier/docs/METHOD.md`), or any OpenAI-compatible endpoint via `OPENAI_BASE_URL`.
- **Everything after E3**: CPU, minutes.

**Who builds.** The author does not run W3+ themself; the stages are specified in
`docs/METHOD.md`, the exit conditions in `docs/WAVES.md`, and the resume point in
`docs/HANDOFF.md`. Whoever runs a stage records its measured cost beside the estimate.

## The paid path

Costs are estimates under stated assumptions until each stage runs; `docs/METHOD.md` carries
the assumption beside each figure and replaces it with a measured value as it lands.

```
make manifest FACTORY=factory_001    # E1. Negligible: shard index reads only.
make signal                          # E2+E3. ~1.7M frames for the pilot factory.
make cycles                          # E5. Negligible.
make hal                             # E6. Published equations; docs/DECISIONS.md D013.
make estimate                        # E8. Minutes.
make card                            # E9. Exits nonzero while the verdict is NOT_VERIFIED.
```

Every stage that is not written yet fails loudly with a pointer to the wave that lands it.
That is deliberate — a stage that silently no-ops is how a pipeline comes to look finished
before it is.

## Known footguns

- **`make hal` still fails** at W1–W2 because the stage is not written, not because anything
  is blocked. The mapping is resolved (`docs/DECISIONS.md` D013).
- **The evaluation release will not work.** Its `frame_id` carries no clip linkage, so no
  duty cycle can be computed from it. Use the raw release. `docs/DECISIONS.md` D011.
- **A shallow clone breaks the ordering check.** `git log --diff-filter=A` needs full
  history to show that every document predates the first `src/` file.
- **Re-pinning the corpus revision invalidates every stored record.** `corpus_rev` is on the
  record for exactly this reason; records from two revisions are never pooled, and the
  pipeline will refuse rather than mix them.
- **Reproducing the numbers does not reproduce the validation.** There is none. No
  ergonomist scored this corpus, and running these commands successfully does not change
  that. `docs/COVERAGE.md`.
