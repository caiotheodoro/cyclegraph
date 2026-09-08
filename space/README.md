---
title: cyclegraph flow gain
emoji: 🖐
colorFrom: gray
colorTo: pink
sdk: static
pinned: false
license: apache-2.0
---

# cyclegraph flow gain

What a dense optical flow estimator reports when it is asked for a hand's speed, and what it
reports instead once the hand moves further than it can follow.

Every number on this page is read from `data.json`, which `scripts/export_space_data.py`
generates from `results/` in the [cyclegraph repository](https://github.com/caiotheodoro/cyclegraph).
Nothing is typed into the page, so a figure here and the same figure in the
[dataset](https://huggingface.co/datasets/caiotheodoro/cyclegraph-flow-gain) cannot drift apart.

No corpus frame was decoded for any of it. The scenes are rendered under the corpus's own
published fisheye, which is the only reason the true flow field is known exactly and a gain is
measurable at all.
