## Hazir - A live evacuation headcount from the network

On a giga-project site holding ten thousand workers, an evacuation headcount takes an hour with a clipboard. Hazir gets it from the mobile line each worker already carries - no tag, no beacon, no app - and turns silence into a rescue list with a last known area in the first minutes.

### The problem

Ten thousand workers, many square kilometres, and a headcount that takes an hour. Hazir asks the network instead, one cheap question per worker.

### What the prototype actually does

Hazir is a working web application with an operator console, a REST API, and
a live WebSocket feed of the agent's reasoning. Open it, click a scenario, and
you watch the agent choose CAMARA calls one at a time and then justify its
decision with the network answers behind it.

It runs in three modes. `simulator` needs no credentials and answers every
CAMARA call in the real CAMARA response shape, which is how the organisers
recommend demonstrating and how the test suite stays deterministic. `live`
calls the Nokia Network-as-Code gateway with your own key. `hybrid` uses live
where credentials allow and falls back per call. Every answer is tagged with
its source in the UI, so a simulated result can never pass itself off as a real
network answer.

### The AI agent layer

The agent is a planner over a CAMARA tool registry, not a script with an LLM
bolted on. Each tool in the registry carries its price, its typical latency and
how much it reveals about a person, and the planner is judged on choosing well:

1. The planner proposes one call, with a stated reason.
2. The runtime, never the model, checks it against the tool allowlist, the
   consent ledger and the remaining budget.
3. The CAMARA answer is recorded with full provenance and turned into a fact.
4. Repeat until the planner submits a decision, or the budget runs out.

The planner is Google AI Studio (Gemini) through **Pydantic AI**'s typed,
structured-output path. It is enabled by setting `AGENT_PROVIDER=gemini`
alongside a `GEMINI_API_KEY`. A model turn may only propose a next CAMARA check
or a decision; it cannot execute a network call itself. The runtime remains the
only executor of consent, the tool allowlist, argument filtering and budget.

Gemini is opt-in on both counts deliberately: a key sitting in the environment
should not be enough to start spending on a model. Otherwise a deterministic
policy planner implementing the same escalation ladder takes over, so the
prototype is demonstrable offline and CI has something stable to assert. If a
configured model cannot complete a turn, the finished case is explicitly
labelled `policy-fallback` with a bounded error reason. It is never presented
as a successful Gemini-planned decision.

**The guardrail is the part worth looking at.** The policy computes a floor for
every case from the facts alone. If the model proposes something less cautious
than the floor, the floor wins and the disagreement is written into the
decision record. A language model should choose which checks to buy; it should
not be able to clear a case the evidence says to escalate. There is a test for
exactly this.

### Results from the shipped scenarios

8 scenarios ship with the prototype, and all 8 reach the
outcome they claim. The demo and the test suite assert the same thing, so a
scenario drifting from the pitch is a build failure.

- Outcome levels reached: `clear`, `notify`, `breach`, `missing`
- CAMARA calls per case: 1 to 6 (average 2.4)
- Total spend across all scenarios: 45 units, against 200 if
  every available check were called on every case, a saving of 77.5%

| Scenario | Outcome | CAMARA calls | Spend |
| --- | --- | --- | --- |
| Worker at the muster point | `clear` | 1 | 2 |
| Out of the zone but not at muster | `notify` | 2 | 3 |
| Not at muster and unreachable | `missing` | 4 | 8 |
| Missing, and the incident has filled the cell | `missing` | 6 | 22 |
| The network answers PARTIAL at the muster edge | `notify` | 2 | 3 |
| Inside the crane zone without a ticket | `breach` | 1 | 2 |
| Still in open sun at heat index 46 | `notify` | 1 | 2 |
| Induct a new starter | `clear` | 2 | 3 |

The cheapest case, *Worker at the muster point*, resolves in 1 call(s). The
most expensive, *Missing, and the incident has filled the cell*, earns 6. That gap is the product:
an agent that calls everything on everyone is safe, useless and unaffordable.

### CAMARA APIs on Nokia Network as Code

`number-verification`, `location-verification`, `device-status`, `location-retrieval`, `congestion-insights`, `geofencing-subscriptions`, `quality-on-demand`, `network-slice-device-attachment`

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

### Consent

CAMARA identity, location and geofencing APIs are only lawful with the consent
of the line owner, so consent is enforced in the transport path rather than
described in a policy document. An ungranted call raises before a request is
built.

Consent is taken at induction, alongside the site pass and the safety
briefing, from the worker, who is a contracted employee and on most Gulf sites
already carries the company line as part of the kit. Checks run during shift
hours and during a declared incident, and stop when the worker clocks out.
Zone level only, never a pin. A worker can withdraw, and the site then counts
them by hand. Consent for safety monitoring should not be a condition of being
rescued.

You can prove this in the running app: press **Withdraw consent**, run the same
case again, and watch the agent get refused at the transport layer with zero
CAMARA calls made.

### What this does not do

- Hazir accounts for lines, not bodies. A worker who leaves his phone in the canteen shows as accounted for at the canteen, so this shortens the clipboard round rather than replacing it.
- Location verification is cell and area resolution. A 300 m muster circle works; telling two adjacent scaffolds apart does not.
- PARTIAL answers are common around steel and concrete, and the policy deliberately downgrades them to a visual check. That means some genuinely missing workers will first read as uncertain.
- Network slices and quality sessions depend on the operator actually offering them on that site. Where they are not available the agent still produces the rescue list, just without the reserved bandwidth.

### Who pays

- Main contractors and site safety departments paying per worker per month
- Insurers and project clients, who push for it because a live muster lowers their own risk
- Mobile operators, who share the API income and can sell it with the site line plan

### Verification

Run `pytest -q` in the repository. The suite covers the CAMARA transport and
its provenance, the consent gate, budget enforcement, the tool allowlist, the
guardrail floor overruling an over-confident model, the LLM planner loop
against a scripted model, the full HTTP surface, and every shipped scenario.
