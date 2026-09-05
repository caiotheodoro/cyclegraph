"""Manipulation-bout frequency, by two methods that cross-check each other.

Deliberately empty of re-exports, for the reason `cyclegraph.corpus` gives. Depends on
`signal` and **not** on `exposure`: frequency does not know what it will be used for
(`docs/ARCHITECTURE.md`).

Both methods measure the rate of manipulation *bouts*, which is a lower bound on the TLV's
exertion frequency and never the thing itself (`docs/DECISIONS.md` D014, `docs/RED-TEAM.md`
A10). Every record says so, and the demotion of this whole path to a cross-check is what
that concession bought.
"""
