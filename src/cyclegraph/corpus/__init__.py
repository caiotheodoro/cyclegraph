"""Shard access, byte ranges, decode, and the 4 Hz frame-pair plan.

Deliberately empty of re-exports. Callers import from the concrete module
(`from cyclegraph.corpus.manifest import clip_refs`) so that importing this package does
not pull `huggingface_hub` in, and so that each module under it can land in its own commit
without contending on this file.

`docs/ARCHITECTURE.md`: nothing else in the repository knows what a tar shard is. The
pinned revision is a property of the record, not of the process.
"""
