# The hand box was measuring the wall

I built a synthetic test to size a small correction, and found the correction was the whole
signal.

The project is cyclegraph. It reads Build AI's per-frame "active manipulation" flag over
`builddotai/Egocentric-10K` as duty cycle, one of the two inputs the ACGIH TLV needs for Hand
Activity Level. The other input is hand speed. Ten thousand hours of head-mounted factory video,
2,144 workers, and no way to ask any of them how fast their hands were moving. So you estimate
it. Put a detector on the hand, run dense optical flow, take the median magnitude inside the box,
subtract the camera's own motion, convert pixels to millimetres.

That pipeline is ordinary. I wanted its error bar before spending GPU hours on it. What I got
back was a number that stops describing the hand entirely, past a threshold that normal work
crosses.

## What the speed was for

The HAL mapping I use is Akkas 2015, fitted over hand speeds from 255.3 to 1288.0 mm/s. It is
logistic in log speed, which makes the exposure number sensitive in a specific and unfriendly
way: the error you can afford is a percentage, not a quantity.

I pre-registered the tolerable systematic error at 0.25 HAL. Running that back through the
equation gives the budget in speed terms. At an assumed corpus median of 612.4 mm/s, 0.25 HAL is
26.7 mm/s. That is 4.4% of the speed. At 400 mm/s it is 5.7%, at 800 mm/s 4.6%.

So the whole allowance is about five percent. Hold that number.

## The check that was supposed to be routine

Before any of this touches a real frame, there is a sanity test. Point the camera at a hand that
is not moving, rotate the camera, and ask the estimator for the hand's speed. The answer must be
zero. Rotational optical flow is depth-independent, so a correct ego-motion model cancels it
exactly, everywhere in the frame.

It does cancel, on a narrow lens. The corpus does not have a narrow lens. Its cameras are
fisheye: Kannala-Brandt, 67.892 degrees of half-angle, published per worker and identical for
all 2,144 of them.

Rotational flow on a fisheye is not uniform across the frame. It varies strongly with radius. And
the rule I am implementing subtracts a *scalar*: the median flow over everything outside the hand
box. A scalar cancels a uniform field and leaves a radial one mostly intact.

I computed that residual in closed form, no estimator involved, so it is a property of the rule
and the lens rather than of anyone's code. At 10 degrees per second of head rotation the corpus
fisheye leaves 10.0916 mm/s of apparent hand speed. A narrow lens leaves 0.1328 mm/s. Seventy-six
times more, from the same subtraction.

Against a 26.7 mm/s budget, 10 mm/s is uncomfortable but survivable. Head translation is worse:
3 cm/s exhausts the entire allowance. Still, this is the shape of problem I expected. A geometric
error, bounded, disclosable, subtractable.

Then I ran the estimators.

## The number that would not move

I rendered frame pairs under the same fisheye, with a hand plane at 0.45 m and a background plane
at 2.5 m, and swept one variable: how far the hand moves between the two frames. Because the
scene is synthetic the true flow field is known exactly. That is the only reason any of this is
measurable.

The quantity is gain. Median recovered flow magnitude over median true flow magnitude, inside the
hand box. Gain 1.0 recovers the motion. Gain 0.2 reports a fifth of it.

Farneback at 960x540, seed 11:

| hand displacement | gain |
|---|---|
| 5.7 px | 0.9973 |
| 11.399 px | 0.9973 |
| 22.794 px | 0.9925 |
| 34.181 px | 0.2024 |
| 45.539 px | 0.2323 |
| 68.025 px | 0.1773 |

Gain does not decay. It holds at essentially one, falls off a cliff between 22.8 and 34.2 px, and
then sits on a shelf.

I expected degradation; degradation you can model, bound, and correct. A cliff into a shelf is a
different kind of object, and the shelf turned out to be the interesting half.

## What the shelf is

0.18.

Which is 0.45 divided by 2.5. The hand plane over the background plane.

Past the knee the estimator is not measuring the hand badly. It is measuring the background
correctly, and the background is 5.6 times further away, so it moves 5.6 times slower in pixels.
The window has smoothed across the depth discontinuity at the edge of the hand, lost the hand,
and locked onto the wall behind it. The number that comes out is a real measurement of a real
thing. It is a measurement of the wall.

Recall the budget was five percent. The shelf under-reports by eighty-two.

## The second estimator

The obvious response is that Farneback is from 2003 and I should use something better. So I ran
RAFT-small on the same sweep, same seed, same scenes.

RAFT is better, and it is better in a way that does not help.

| hand displacement | farneback | raft-small |
|---|---|---|
| 22.794 px | 0.9925 | 0.9946 |
| 34.181 px | 0.2024 | 0.9738 |
| 45.539 px | 0.2323 | 0.32 |
| 68.025 px | 0.1773 | 0.1724 |
| 132.883 px | 0.1964 | 0.1801 |

RAFT holds full gain at 34.2 px, where Farneback has already fallen. It buys roughly one more
doubling of usable displacement. Then it falls to the same shelf: 0.172, 0.177, 0.180, 0.184
against Farneback's 0.177, 0.187, 0.196.

**The knee belongs to the estimator. The shelf belongs to the geometry.** A better estimator moves
where the cliff is and does not touch what is underneath it. That is the finding I would want
someone to take away, because it says what buying a better model does and does not purchase.

There is a tell in the ego-motion column too. On the rotation-only test the exact geometry leaves
1.1461 px of residual — that is what a perfect estimator should report, because the scalar median
genuinely cannot cancel the radial field. Farneback reports 1.2171. RAFT reports 1.014.

RAFT comes in *below* the floor an ideal estimator would leave. That is not accuracy. It is
under-recovery, and it happens to point in the direction that looks like a better score.

## Decode resolution, which goes the wrong way

I swept four decode sizes, expecting a monotone trade of cost against fidelity. At the same
box-relative displacement, 0.236 of the hand box width:

| decode | 480x270 | 960x540 | 1440x810 | 1920x1080 |
|---|---|---|---|---|
| gain | 0.7656 | 0.9925 | 0.2036 | 0.1978 |

960x540 is a measured optimum. 1920x1080 does worse than 480x270 — four times the pixels, four
times the decode cost, and it has already fallen off the cliff at a displacement where 960x540 is
still recovering 99% of the motion.

I do not have a clean account of why. The knee is not fixed in absolute pixels, and it is not
fixed as a fraction of the hand box either; both readings are contradicted by a row in that table.
Farneback's window is 15 px and its pyramid is three levels, which sets a search range, but the
crossings do not line up with that arithmetic cleanly enough for me to claim it.

What I will claim is the operational part. If you are picking a decode resolution for this by
reasoning that more pixels means more signal, the measurement disagrees, and it disagrees by a
factor of five.

## Why this hides

Here is the part that made me write it up rather than fix it and move on.

The pipeline subtracts ego-motion as the median flow outside the hand box. Past the knee, the
inside of the hand box already contains the background's flow. So the correction removes the
signal it was meant to clean.

Two failures, pointing the same way, cancelling. The residual that comes out is small. It is also
plausible: a hand moving slowly, at a factory workstation, is not a suspicious reading. Nothing
throws, nothing nulls, no rate crosses a ceiling. In the run that produced these numbers the
flow-null rate was 0.0 across 200 pairs on both estimators. Every frame returned a clean answer.

An error that fails loudly costs you a day. An error that fails quietly gets published.

## Honest limits

This is synthetic. That is deliberate — ground-truth flow has to be known exactly for a gain to
exist at all — but it means the texture is rendered, not factory video. The lens is the corpus's
real published model. The content is not.

The two depth planes are stated assumptions about workstation geometry, not measurements. 0.45 m
and 2.5 m are reasonable for a bench, and the shelf sits at their ratio, so a different workstation
gives a different shelf. That is a prediction; it is testable; I have not tested it.

I have not measured the corpus's own ego-motion distribution, because that needs frames decoded
and the corpus stages of this project are blocked on cost. Everything above is an instrument
check. The measurement cyclegraph exists to make has not run, and nothing here brings it closer.

The far tail has a second regime I am not making claims about. Past roughly 1.4 hand-box widths
of displacement, gain falls below the depth ratio toward zero, because the estimator has exceeded
its search range and is tracking nothing at all. Those points are not on the shelf and must not be
averaged with the ones that are.

And two estimators is two. Farneback and RAFT-small agree, which is weak evidence about dense
optical flow in general and no evidence at all about a method that models depth.

## What to do with this

Do not take my displacement numbers and apply them to your setup. The knee moves with the
estimator, the decode resolution, the frame interval and the geometry; I have shown all four
moving it.

Run it instead. The generator and the sweep are published, they need no corpus, no token and no
GPU for the Farneback arm, and the harness takes your estimator as an argument and reports three
things: the displacement where your gain leaves 1.0, the shelf it lands on, and the depth ratio
that shelf should equal if it has silently switched to the background.

Passing is not gain near 1.0 everywhere. Nothing does that. Passing is your knee sitting outside
the displacements your work actually produces, and the harness tells you which side of it you
are on.

- Benchmark and harness: <https://huggingface.co/datasets/caiotheodoro/cyclegraph-flow-gain>
- The data behind every table above: <https://huggingface.co/spaces/caiotheodoro/cyclegraph>
- Repository, including what is blocked and why: <https://github.com/caiotheodoro/cyclegraph>
