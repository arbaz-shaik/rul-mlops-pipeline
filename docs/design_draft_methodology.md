# Design Chapter Draft: Methodology Decisions and Threats to Validity
# CSC8099 | working draft | source reasoning: Phase 6 harness build, 21 July 2026
# Move into the IEEE dissertation template in the Academic Writing chat.
# Hard rules observed: no em-dashes, no first person, formal register.

## Target standardisation: capped RUL

The remaining-useful-life target was standardised on the capped formulation,
RUL = min(max_cycle - current_cycle, 125), across both training and evaluation.
This decision followed the discovery that the stored training-label array was
uncapped while every registered model, including the production baseline, had
been trained on capped labels through a shared training path that applies the
cap after loading. The two facts were reconciled by confirming, through the
model registry, that the deployed champion and all challengers already shared
the capped target. Capping the evaluation labels to match was therefore the
internally consistent choice that required no retraining of the baseline. The
cap value of 125 is standard for the CMAPSS FD001 benchmark and aligns the
reported error with the published literature [Wu 2019, Li 2018]. A provenance
gate confirmed that an uncapped per-row reconstruction from the raw cycle
counts reproduces the stored training labels element for element, verifying
both the reconstruction function and the row-to-label alignment before any
capping is applied.

## Threat to validity 1: shadow evaluation floor versus engine length

The shadow validation stage requires a minimum of 500 paired predictions before
a bootstrap confidence interval is computed, a floor chosen to ensure the
interval is not dominated by sampling noise. A single engine's contiguous run
cannot supply this floor: the longest FD001 training engine contains 362 cycles,
yielding at most 333 windows at a window length of 30. The detection stream and
the evaluation set are, however, separable objects. Detection requires a
time-ordered stream so that a drift onset can be located, whereas the shadow
bootstrap requires only a pooled count of paired predictions and is indifferent
to their ordering. The evaluation set was therefore assembled as pooled
per-engine windows, each drawn wholly within a single engine from its post-onset
tail, preserving on-manifold degradation sequences with zero cross-engine
boundary straddle while meeting the statistical floor.

## Threat to validity 2: PSI inflation under narrow, non-representative samples

The population stability index is a distributional test and assumes the current
batch is representative of the reference population. The reference distribution
pools all training engines. A single engine occupies only a narrow band of that
pooled degradation manifold, so a single-engine batch reads far above the 0.2
threshold (approximately 3.3) with no drift present, and no sampling method
applied to a single engine can fall below the population it draws from. A random
sample of the reference against itself, by contrast, reads near zero (0.0099),
and a multi-engine representative batch reads approximately 0.1 when clean. The
detector was therefore designed to compare the reference against a multi-engine
representative batch rather than a single-engine or contiguous window. This
preserves the literature-justified threshold of 0.2 [Fiddler 2023, Arize 2023]
and the frozen reference distribution, while ensuring that a clean regime reads
below threshold and only genuine distributional change triggers retraining. The
detection stream is consequently a sequence of multi-engine batches, clean
batches followed by drifted batches, with drift onset placed on a batch boundary
so that no batch straddles the onset.

## Threat to validity 3: drift injection semantics and label integrity

Synthetic drift is injected as a constant offset on a single signal-bearing
sensor (sensor 9), expressed in units of that sensor's training standard
deviation, applied from a defined onset onward. Single-sensor injection
preserves the rationale for maximum-based aggregation of the per-feature index:
averaging would dilute a single drifted sensor below the trigger threshold.
Expressing intensity in standard-deviation units keeps the injected magnitude
comparable across sensors and independent of any sensor's raw scale. The true
remaining-useful-life labels travel with the sensor rows and are never perturbed
by injection: the offset shifts the sensor reading while the true target is
unchanged, so an unadapted model degrades on the drifted stream and a retrained
model recovers. This is the property that allows accuracy retention to measure
the intended quantity rather than an artefact of label corruption.

## Note on the drift-detection latency metric

Because the detection stream is a sequence of batches scraped on a fixed
interval, drift-detection latency is measured as the number of batches from
onset to the first batch whose index crosses the 0.2 threshold, multiplied by
the batch interval. This quantises the metric to the batch interval and is
reported as such. The batch interval is chosen small enough that observed
latencies are several multiples of it, so the quantisation does not dominate the
measurement. This is a faithful representation of a real streaming detector,
which observes the incoming distribution on a scrape interval rather than
continuously.

## Note on reproducibility

Each scenario is persisted as a single self-describing compressed archive
holding the detection batches, the pooled evaluation set, the labels, and every
injection parameter (drift type, affected sensor, magnitude, onset batch, seed,
and the sensor standard deviation used). The archive is written atomically and
loaded without pickling, so a scenario is reconstructable and a run whose
parameters are recorded is a valid, repeatable data point.
