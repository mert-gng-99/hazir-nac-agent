# Hazir

> A live evacuation headcount from the network

**MENA Ignite Hackathon - GSMA Open Gateway - Theme 2: Smart Cities, Urban Safety & Mega-Project Infrastructure**

Ten thousand workers, many square kilometres, and a headcount that takes an hour. Hazir asks the network instead, one cheap question per worker.

On a giga-project site holding ten thousand workers, an evacuation headcount takes an hour with a clipboard. Hazir gets it from the mobile line each worker already carries - no tag, no beacon, no app - and turns silence into a rescue list with a last known area in the first minutes.

---

## Quick start

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000. You need no credentials, because the app starts in
`simulator` mode and every answer is tagged with its source.

Full instructions, including the Gemini planner and the live Nokia gateway, are
in **INSTRUCTIONS.md**. The design is in **ARCHITECTURE.md**.

## What it is

An AI agent that decides *which* CAMARA network check is worth making for a
given case, spends against a budget, refuses calls it has no consent for, and
explains every decision with the network answers behind it.

- **8 scenarios** ship with it, all reaching the outcome they claim
- **8 CAMARA APIs** on the Nokia Network-as-Code platform
- **77.5% cheaper** than calling every available check on every case
- **1 to 6 calls** per case, depending on what the case deserves

## Scenarios

- Worker at the muster point. Four minutes after the alarm, inside the 300 m circle (expects `clear`)
- Out of the zone but not at muster. 1.1 km away and answering on data (expects `notify`)
- Not at muster and unreachable. Seven minutes after the alarm, the network cannot reach the line (expects `missing`)
- Missing, and the incident has filled the cell. Unreachable line plus a saturated cell around the last ping (expects `missing`)
- The network answers PARTIAL at the muster edge. Standing behind steel containers, line still reachable (expects `notify`)
- Inside the crane zone without a ticket. Zone control after the gate, reported to the zone supervisor (expects `breach`)
- Still in open sun at heat index 46. The work ban crossed twenty minutes ago (expects `notify`)
- Induct a new starter. Verify the company line, then create the work-zone fence (expects `clear`)

## CAMARA APIs used

| CAMARA API | What the agent asks it | Cost | Reveals |
| --- | --- | --- | --- |
| `number-verification` | Confirm the line on the phone | 1 | boolean |
| `location-verification` | Is the line inside this area | 2 | boolean |
| `device-status` | Can the line be reached | 1 | enum |
| `location-retrieval` | Where is the line | 4 | area |
| `congestion-insights` | How loaded is the serving cell | 1 | enum |
| `geofencing-subscriptions` | Notify me when the line leaves or enters an area | 2 | area |
| `quality-on-demand` | Reserve network quality for this line | 8 | mutates |
| `network-slice-device-attachment` | Put this line on a dedicated slice | 6 | mutates |

## The agent

```
planner proposes one call  ->  runtime checks allowlist, consent, budget
      ^                                        |
      |                                        v
  answer becomes a fact   <-   CAMARA call recorded with provenance
      |
      +--> planner submits a decision  ->  policy floor applied  ->  ledger
```

The planner is Google AI Studio (Gemini) through Pydantic AI when
`AGENT_PROVIDER=gemini` and a `GEMINI_API_KEY` are both set, and a deterministic
policy ladder otherwise. Pydantic AI returns a typed proposal only; the runtime
still holds the budget, allowlist and consent gate, and the policy holds a floor
the model cannot talk its way under.

## Tests

```bash
pytest -q
```

## What this does not do

- Hazir accounts for lines, not bodies. A worker who leaves his phone in the canteen shows as accounted for at the canteen, so this shortens the clipboard round rather than replacing it.
- Location verification is cell and area resolution. A 300 m muster circle works; telling two adjacent scaffolds apart does not.
- PARTIAL answers are common around steel and concrete, and the policy deliberately downgrades them to a visual check. That means some genuinely missing workers will first read as uncertain.
- Network slices and quality sessions depend on the operator actually offering them on that site. Where they are not available the agent still produces the rescue list, just without the reserved bandwidth.

## Layout

```
main.py            uvicorn entry point
app_spec.py        re-exports this product's spec
core/              shared platform: CAMARA client, agent, consent, ledger, UI
  camara.py        the eleven CAMARA API families, live + simulator
  simulator.py     deterministic network simulator
  agent.py         the agent loop, budget, guardrail
  tools.py         CAMARA tool registry with cost and reveal metadata
  consent.py       consent ledger enforced in the transport path
  ledger.py        SQLite decision ledger
  signals.py       CAMARA answers -> named facts
  server.py        FastAPI app
  webui.py         the operator console
idea/              this product: policy, scenarios, demo lines, copy
tests/             pytest suite
```

## Licence

MIT. See LICENSE.
