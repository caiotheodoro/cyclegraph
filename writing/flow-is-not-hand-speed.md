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

I rendered frame pairs under the same fisheye, with a hand plane at 0.45 m and a background
plane at 2.5 m. Then I swept one variable: how far the hand box moves between the two frames. Because the
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

RAFT holds full gain at 34.2 px, where Farneback has already fallen. It buys one more step of
the sweep, which on a nine-point grid means somewhere between one and two times the usable
displacement; the grid cannot say where in that range. Then it falls to the same shelf: 0.172, 0.177, 0.180, 0.184
against Farneback's 0.177, 0.187, 0.196.

```json
// cv-chart
{"type":"bars","title":"Recovered flow over true flow, inside the hand box, against hand displacement","series":[{"key":"farneback","label":"farneback-cv2","color":0},{"key":"raft","label":"raft-small","color":1}],"domain":[0,1],"data":[{"label":"5.7","farneback":0.9973,"raft":0.9953},{"label":"11.399","farneback":0.9973,"raft":0.9832},{"label":"22.794","farneback":0.9925,"raft":0.9946},{"label":"34.181","farneback":0.2024,"raft":0.9738},{"label":"45.539","farneback":0.2323,"raft":0.32},{"label":"68.025","farneback":0.1773,"raft":0.1724},{"label":"90.136","farneback":0.1869,"raft":0.1765},{"label":"132.883","farneback":0.1964,"raft":0.1801},{"label":"163.312","farneback":0.0552,"raft":0.184}],"caption":"Both arms are the 960x540 decode at the same 0.25 s pair interval, so they are comparable. Gain 1.0 recovers the hand's motion. The floor both land on is 0.18, which is the hand plane over the background plane: 0.45 m over 2.5 m. RAFT-small holds one step further out and lands on the same floor. The last farneback bar sits below the floor because at that displacement the estimator has exceeded its search range and is tracking nothing at all, which is a different failure and is not averaged with the others."}
```

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

960x540 is a measured optimum. 1920x1080 does worse than 480x270 — sixteen times the pixels, and
it has already fallen off the cliff at a displacement where 960x540 is still recovering 99% of
the motion.

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
throws and nothing nulls. Every pair in the sweep returned a finite, well-formed flow field.
`flow_returned_none` is false on all 54 distinct estimator, decode and displacement
measurements published here. No contract check and no null-rate ceiling anywhere downstream has
anything to fire on.

An error that fails loudly costs you a day. An error that fails quietly gets published.

## Honest limits

**The camera moves, not the hand.** The sweep translates the camera over a static scene, which is
how a static hand is given relative motion in a render. That matters for what the shelf means.
Under camera translation the background is moving too, at the depth ratio, so an estimator that
loses the hand and locks onto the background lands on 0.18. Under a static camera and a hand
moving on its own, the background is not moving at all, and the same estimator falling back to it
would land near zero instead. The knee is unchanged either way. The shelf's *value* is a fact
about ego-motion-dominated frames, and head-mounted factory video is ego-motion-dominated, but
that is an argument rather than a measurement.

**The renderer does not simulate what the prose describes.** Both planes carry one texture, the
hand plane sits in a box that does not move between the frames, and the warp is backward and
first-order. That warp is accurate to a fraction of a pixel where the flow field is smooth. It
is not smooth at the boundary this whole result is about. There is no occlusion, no
disocclusion, no motion blur, no rolling shutter, no sensor noise and no illumination change. The last four are what
the project's own red-team document names as the causes of real flow failure. The estimator here
is being given an easier problem than a factory would — and it still fails.

**The lens is verified on sixteen workers, not 2,144.** The corpus ships a per-worker
`intrinsics.json` and sixteen were drawn at an even stride and found byte-identical; the rest are
assumed, not checked. The corpus also has no real per-camera calibration, so this is a floor for
the nominal lens rather than for the fleet.

The two depth planes are stated assumptions about workstation geometry, not measurements. 0.45 m
and 2.5 m are reasonable for a bench, and the shelf sits at their ratio, so a different
workstation gives a different shelf. That is a prediction; it is testable; I have not tested it.

**The tables above are on the superseded pair interval.** Both estimator sweeps use 0.25 s
between the two frames, which is what reading the rubric's pair at the 4 Hz analysis rate gives.
The project later re-specified the pair to the clip's own frame rate, about 0.033 s. Gain against
pixel displacement is unaffected, because the interval only rescales the speeds. But at the
native rate an assumed corpus median of 612.4 mm/s is roughly 23 px at 960x540. That sits *at*
the Farneback knee rather than comfortably past it. It is a narrower margin than the 0.25 s
framing suggests, and it cuts against me.

The far tail has a second regime I am not making claims about. Gain falls below the depth ratio
toward zero once the estimator has exceeded its search range and is tracking nothing. It arrives
earlier at higher resolution: unambiguously by 0.93 of a hand-box width at 1920x1080, against
1.69 at 960x540. One point sits between the regimes and I will not assign it — 0.1056 at 0.47
box widths, too low to be the shelf and too high to be nothing. Regime-two points are not on the
shelf and must not be averaged with the ones that are.

Two estimators is two. Farneback and RAFT-small agree, which is weak evidence about dense optical
flow in general and no evidence at all about a method that models depth.

**And the metric is magnitude-only.** Gain is a ratio of median magnitudes inside the box, so it
is blind to direction. An estimator returning the exact field negated scores identically to a
perfect one, and a median hides a field that is right in half the box and wrong in the other
half. It is a test for one specific failure and it is not an accuracy measure.

**Nothing here says the instrument works.** No ergonomist has scored this corpus, force is
unobservable from the video at all, and every record this project has written carries
`tlv_evaluable` false. Any summary claiming cyclegraph applies the TLV is wrong, and this piece
is about one input to it behaving badly, not about the index being sound.

## What to do with this

Do not take my displacement numbers and apply them to your setup. The knee moves with the
estimator, the decode resolution, the frame interval and the geometry; I have shown all four
moving it.

Run it instead. The generator and the sweep are published, and the Farneback arm needs no
corpus, no token and no GPU. The harness takes your estimator as an argument and reports three
things — the displacement where your gain leaves 1.0, the shelf it lands on, and the depth ratio
that shelf should equal if it has switched to the background.

Passing is not gain near 1.0 everywhere. Nothing does that. Passing is your knee sitting outside
the displacements your work actually produces, and the harness tells you which side of it you
are on.

- Benchmark and harness: [huggingface.co/datasets/caiotheodoro/cyclegraph-flow-gain](https://huggingface.co/datasets/caiotheodoro/cyclegraph-flow-gain)
- The data behind every table above: [huggingface.co/spaces/caiotheodoro/cyclegraph](https://huggingface.co/spaces/caiotheodoro/cyclegraph)
- Repository, including what is blocked and why: [github.com/caiotheodoro/cyclegraph](https://github.com/caiotheodoro/cyclegraph)
