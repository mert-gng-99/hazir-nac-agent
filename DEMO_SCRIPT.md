# Hazir - demo video script

Target: **3 minutes**. Screen recording of the running app with a voice-over.
Record at 1920x1080, browser zoomed so the three columns are readable.

Before recording: `uvicorn main:app --port 8000`, open the dashboard, press
**Clear ledger** so the metric strip starts at zero.

---

## 0:00-0:25 - The problem

> "Ten thousand workers, many square kilometres, and a headcount that takes an hour. Hazir asks the network instead, one cheap question per worker."

On screen: the dashboard, still empty. Let the header sit for a moment so the
product name, the theme and the CAMARA API count register.

## 0:25-1:00 - One case, start to finish

Click **Worker at the muster point**.

> "The agent is handed a case and decides which network question is worth
> asking. It does not call every API, because each one costs money and reveals
> something about a person."

Point at the step list as it fills.

> "One call at a time, with the reason it chose that call. Here is the CAMARA
> answer, and here is what the agent concluded from it."

Scroll to the evidence table.

> "Every answer is tagged with where it came from. This is simulator mode, and
> it says so. A simulated answer never passes itself off as a real one."

Point at the two badges in the header while you say it. They read the mode and
the planner straight from the running service, so they say `simulator answers`
and `policy planner` on a default deployment, and `live network` and
`gemini verified` once real credentials are in place. Judges get the honest
state of your deployment in one glance, which is worth more than a claim.

## 1:00-1:40 - Restraint is the product

Click **Run all eight site events**.

> "All 8 scenarios. Every one reached the outcome it claims, and the
> demo asserts the same thing the test suite does."

Point at the cost line.

> "45 units spent. Calling every available check on every case would
> have cost 200. That is 77.5% saved, and look at the spread:
> *Worker at the muster point* took 1 call, *Missing, and the incident has filled the cell* earned 6. An
> agent that checks everyone is safe, useless and unaffordable."

## 1:40-2:15 - Consent is real

Press **Withdraw consent**, then re-run the same scenario.

> "CAMARA location and identity APIs need the consent of the line owner. That
> is enforced in the transport layer, not promised in a policy document."

Point at the empty evidence table and the refusal list.

> "Zero calls. The agent is refused before a request is even built."

Press **Restore**.

## 2:15-2:45 - The guardrail

> "With a Gemini key the model chooses the calls. But the policy computes a
> floor from the evidence alone, and if the model proposes something less
> cautious, the floor wins and the disagreement is recorded."

Optionally show `tests/test_agent.py::test_the_floor_overrides_an_over_confident_model`.

> "A language model should decide which checks to buy. It should not be able to
> clear a case the evidence says to escalate. There is a test for that."

## 2:45-3:00 - Close

> "Hazir. A live evacuation headcount from the network. 8 CAMARA APIs on Nokia Network as Code,
> an agent layer that spends against a budget, and a record that explains every
> decision to the person it affects."

---

## If you have 30 seconds more

Run muster-accounted first to show the cheap path, then the uncertain case to show the agent refusing to declare a man missing on a PARTIAL answer.

## Notes

- Say "simulator mode" out loud. Judges who know CAMARA will wonder, and
  answering before they ask reads as confidence.
- The honest limits in README.md are worth 15 seconds if the video runs short.
  Stating what a product cannot do is unusual enough to be memorable.
- Scenarios worth using: Worker at the muster point, Out of the zone but not at muster, Not at muster and unreachable
