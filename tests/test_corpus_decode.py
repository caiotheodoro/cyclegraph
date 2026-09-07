"""Tests for `src/cyclegraph/corpus/decode.py`.

The network path is not tested; `docs/WAVES.md` requires the suite to run offline. What is
tested is the command construction, because both of its load-bearing details fail silently:
`-ss` after `-i` still decodes, just by reading the whole shard, and a missing protocol
whitelist still runs, just with `file:` re-enabled.
"""

from __future__ import annotations

import numpy as np
import pytest

from cyclegraph.corpus.decode import (
    PROTOCOL_WHITELIST,
    DecodeOutcome,
    ffmpeg_clip_argv,
    subfile_url,
)
from cyclegraph.models import ClipRef
from tests import fixtures

URL = "https://cdn.example/shard.tar?sig=abc"


def _clip(**over: object) -> ClipRef:
    return ClipRef.model_validate({**fixtures.CLIP_REF, **over})


def test_the_subfile_url_names_the_byte_window() -> None:
    assert subfile_url(URL, 512, 8419328) == f"subfile,,start,512,end,8419328,,:{URL}"


def test_an_inverted_byte_range_is_refused() -> None:
    with pytest.raises(ValueError):
        subfile_url(URL, 900, 100)


def test_the_input_seek_comes_before_the_input() -> None:
    """After `-i` ffmpeg decodes from the start and discards, turning a ~2 s seek into a
    sequential read of an 800 MB shard."""
    argv = ffmpeg_clip_argv(URL, _clip(), fps_sampled=4.0, width=480, height=270, start_s=12.5)
    assert argv.index("-ss") < argv.index("-i")


def test_no_seek_flag_is_emitted_when_decoding_from_the_start() -> None:
    argv = ffmpeg_clip_argv(URL, _clip(), fps_sampled=4.0, width=480, height=270)
    assert "-ss" not in argv


def test_the_protocol_whitelist_is_present_and_carries_every_scheme_the_path_needs() -> None:
    argv = ffmpeg_clip_argv(URL, _clip(), fps_sampled=4.0, width=480, height=270)
    assert "-protocol_whitelist" in argv
    listed = argv[argv.index("-protocol_whitelist") + 1]
    assert listed == PROTOCOL_WHITELIST
    for scheme in ("subfile", "https", "tls", "tcp", "crypto"):
        assert scheme in listed.split(",")


def test_the_rate_and_size_reach_the_filter_graph() -> None:
    argv = ffmpeg_clip_argv(URL, _clip(), fps_sampled=8.0, width=960, height=540)
    assert argv[argv.index("-vf") + 1] == "fps=8.0,scale=960:540"
    assert argv[argv.index("-pix_fmt") + 1] == "gray"


def test_a_non_positive_rate_is_refused() -> None:
    with pytest.raises(ValueError):
        ffmpeg_clip_argv(URL, _clip(), fps_sampled=0.0, width=480, height=270)


def test_pairs_are_consecutive_frames_so_n_pairs_is_one_less_than_n_frames() -> None:
    outcome = DecodeOutcome(clip_id="c", n_frames=749, n_pairs_planned=748,
                            status="ok", reason=None, seconds=1.0)
    assert outcome.n_pairs_decoded == 748
    assert outcome.pair_failures == 0


def test_a_short_decode_is_counted_as_failed_pairs_not_dropped() -> None:
    """`docs/METHOD.md` E2's gate is per pair, and a clip that decodes half its length is
    half a failure rather than either a pass or a discarded clip."""
    outcome = DecodeOutcome(clip_id="c", n_frames=100, n_pairs_planned=748,
                            status="ok", reason=None, seconds=1.0)
    assert outcome.n_pairs_decoded == 99
    assert outcome.pair_failures == 649


def test_a_failed_decode_carries_its_reason() -> None:
    outcome = DecodeOutcome(clip_id="c", n_frames=0, n_pairs_planned=748,
                            status="decode_failed", reason="moov atom not found", seconds=0.4)
    assert outcome.pair_failures == 748
    assert outcome.reason


def test_the_thread_cap_is_an_input_option_and_absent_unless_asked() -> None:
    """`-threads` before `-i` caps the *decoder* pool; after `-i` it would size the encoder
    instead and leave the decode uncapped. The pilot box starved on that difference."""
    assert "-threads" not in ffmpeg_clip_argv(URL, _clip(), fps_sampled=4.0,
                                              width=480, height=270)
    argv = ffmpeg_clip_argv(URL, _clip(), fps_sampled=4.0, width=480, height=270, threads=2)
    assert argv[argv.index("-threads") + 1] == "2"
    assert argv.index("-threads") < argv.index("-i")


def test_a_non_positive_thread_cap_is_refused() -> None:
    with pytest.raises(ValueError):
        ffmpeg_clip_argv(URL, _clip(), fps_sampled=4.0, width=480, height=270, threads=0)


def test_a_read_deadline_is_set_on_the_input_and_can_be_disabled() -> None:
    """D063. Without it a stalled read has no deadline anywhere: the reader blocks in
    `stdout.read()`, and `decode_gray_frames`'s own `timeout_s` guards only `communicate()`,
    which a hung ffmpeg never reaches. An 8 Hz run sat on a CDN read for eleven hours and
    looked exactly like slow work."""
    argv = ffmpeg_clip_argv(URL, _clip(), fps_sampled=4.0, width=480, height=270)
    assert argv[argv.index("-rw_timeout") + 1] == str(120 * 1_000_000)  # microseconds
    assert argv.index("-rw_timeout") < argv.index("-i")  # bounds the read, not the decode

    tighter = ffmpeg_clip_argv(URL, _clip(), fps_sampled=4.0, width=480, height=270,
                               rw_timeout_s=5.0)
    assert tighter[tighter.index("-rw_timeout") + 1] == str(5_000_000)
    assert "-rw_timeout" not in ffmpeg_clip_argv(URL, _clip(), fps_sampled=4.0,
                                                 width=480, height=270, rw_timeout_s=0)
