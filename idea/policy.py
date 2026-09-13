"""Hazir - a live evacuation headcount from the network on giga-project sites.

A giga-project site in the Gulf can hold more than ten thousand workers across
many square kilometres. When a fire, a gas leak or a storm forces an
evacuation, the site has to know who came out, and today that is a supervisor
walking a line of tired people with a clipboard. It takes an hour.

Heat is the quieter problem. Work bans exist, but a manager cannot see who is
still standing in open sun on a far corner of the site. Zone control stops at
the gate: once a worker is inside, nobody knows if he walked into a crane path
he holds no ticket for.

Hazir gets all of it from the mobile line the worker already carries - no new
tag, no beacon, no app. The policy handles four events and keeps them separate,
because they deserve different spending:

*   **induction** - verify the line, subscribe the work-zone fence. Once.
*   **evacuation** - the muster question, asked of everyone, and it must be
    cheap: one area check per worker for ten thousand workers.
*   **zone control** - is this worker somewhere he is not ticketed for, and the
    answer goes to *his zone supervisor*, not to him, because he may not read
    the language the system speaks.
*   **heat** - who is still in an open-air zone now that the index crossed.

The rule that costs the most to get right: never declare a worker missing on an
uncertain answer. A PARTIAL from a man standing behind a steel container is not
a man who failed to muster.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core.agent import Case
from core.camara import ApiResult
from core.signals import read_signal

LEVELS = ["clear", "notify", "breach", "missing"]


class HazirPolicy:
    name = "hazir"
    kind = "site_event"
    levels = LEVELS
    budget_units = 24.0

    tool_names = [
        "verify_number",
        "verify_location",
        "check_reachability",
        "retrieve_location",
        "query_congestion",
        "watch_area",
        "reserve_quality",
        "attach_slice",
    ]

    def system_prompt(self, case: Case) -> str:
        return (
            "You are Hazir, the agent inside the safety system of a Gulf "
            "giga-project site holding more than ten thousand workers. You handle "
            "four events: induction, evacuation muster, zone control and heat.\n\n"
            "Scale decides your spending. An evacuation asks the muster question "
            "of every worker on site, so the first call must be the cheap yes/no "
            "area check and most workers must end there. If you retrieve a "
            "position for everyone, the product cannot be sold.\n\n"
            "How to work:\n"
            "1. Evacuation: ask whether the line is inside the muster circle. If "
            "yes, that worker is accounted for and you are done.\n"
            "2. If not at muster, ask reachability before anything else. A worker "
            "who answers is out of the danger zone but wandering - that is a "
            "supervisor's phone call. A worker the network cannot reach at all is "
            "the one the rescue team needs, and only then do you retrieve a "
            "position.\n"
            "3. Never declare a worker missing on a PARTIAL or UNKNOWN answer if "
            "the line is reachable. Steel, containers and scaffolding produce those "
            "answers constantly, and a false missing report sends a rescue team "
            "away from a real casualty.\n"
            "4. Before promising the rescue team video or telemetry, check "
            "congestion. An incident fills the local cell. A saturated cell earns "
            "the responders a slice; a merely busy one earns a quality session.\n"
            "5. Zone control and heat findings go to the zone supervisor, never to "
            "the worker, who may not read the system's language.\n\n"
            "Workers consented at induction. Checks run during shift hours and "
            "during a declared incident, and stop when the worker clocks out. You "
            "read zone level, never a pin on a map."
        )

    def describe_case(self, case: Case) -> str:
        f = case.facts
        lines = [
            "Site event: %s" % f.get("event", "evacuation"),
            "  worker: %s (badge %s), speaks %s"
            % (f.get("worker", "unknown"), f.get("badge", "?"), f.get("language", "unknown")),
            "  contractor: %s" % f.get("contractor", "unknown"),
            "  zone supervisor: %s" % f.get("supervisor", "unknown"),
        ]
        event = f.get("event")
        if event == "evacuation":
            lines.append("  incident: %s" % f.get("incident", "unspecified"))
            lines.append("  muster circle: %s m" % case.radius_m)
            lines.append("  minutes since evacuation called: %s" % f.get("minutes_since_alarm", "?"))
        if event == "zone_control":
            lines.append("  restricted zone: %s" % f.get("zone_name", "?"))
            lines.append("  holds a ticket for it: %s" % bool(f.get("ticketed")))
        if event == "heat":
            lines.append("  heat index: %s" % f.get("heat_index", "?"))
            lines.append("  open-air zone: %s" % f.get("zone_name", "?"))
        return "\n".join(lines)

    def interpret(self, tool: str, result: ApiResult, facts: Dict[str, Any]) -> Dict[str, Any]:
        return read_signal(tool, result)

    def next_tool(
        self, case: Case, facts: Dict[str, Any], used: List[str]
    ) -> Optional[Tuple[str, Dict[str, Any], str]]:
        event = case.facts.get("event", "evacuation")
        if event == "induction":
            return self._induction(case, facts)
        if event in {"zone_control", "heat"}:
            return self._single_question(case, facts, event)
        return self._evacuation(case, facts)

    def _induction(self, case: Case, facts: Dict[str, Any]):
        if "number_verified" not in facts:
            return (
                "verify_number",
                {},
                "Confirm the company line is in the handset before it becomes this "
                "worker's identity on site for the next two years.",
            )
        if not facts.get("number_verified"):
            return None
        if "geofence_id" not in facts:
            return (
                "watch_area",
                {"event": "left", "radius_m": case.radius_m},
                "Subscribe this line to area-left events for its work zone. Created "
                "once at induction, and it is what makes an instant muster possible "
                "later without any spend at the moment of the alarm.",
            )
        return None

    def _single_question(self, case: Case, facts: Dict[str, Any], event: str):
        if "location_result" not in facts:
            why = (
                "Ask whether this worker is inside the restricted zone. One yes/no "
                "question, no coordinates, and the answer goes to his supervisor."
                if event == "zone_control"
                else "Ask whether this worker is still inside the open-air zone now "
                "that the heat index has crossed the limit."
            )
            return ("verify_location", {}, why)
        return None

    def _evacuation(self, case: Case, facts: Dict[str, Any]):
        if "location_result" not in facts:
            return (
                "verify_location",
                {},
                "The muster question, asked of every worker on site. Two units, "
                "no position returned, and for most workers this is the only call.",
            )

        if facts.get("location_inside"):
            return None  # accounted for; stop

        if "reachability" not in facts:
            return (
                "check_reachability",
                {},
                "Not at the muster point. One unit separates a worker walking the "
                "wrong way from a worker on the ground behind a container.",
            )

        if facts.get("reachable"):
            return None  # a supervisor's phone call, not a rescue

        if "has_last_known_point" not in facts:
            return (
                "retrieve_location",
                {},
                "The line cannot be reached at all and the muster is short by one. "
                "This is where retrieving a position is justified: a rescue team is "
                "about to walk somewhere.",
            )

        if "congestion" not in facts:
            return (
                "query_congestion",
                {},
                "An incident fills the local cell with calls. Check before promising "
                "the rescue team a video feed.",
            )

        if facts.get("cell_saturated") and "slice_attachment_id" not in facts:
            return (
                "attach_slice",
                {"slice_id": case.params.get("slice_id", "site-emergency-slice")},
                "The cell is saturated. Put the rescue team's line on the emergency "
                "slice so their maps and helmet video keep working while everyone "
                "else's calls fail.",
            )

        if facts.get("cell_crowded") and "qod_session_id" not in facts:
            return (
                "reserve_quality",
                {"profile": "QOS_L", "duration_s": 900},
                "Busy but not saturated, so a reserved quality session is "
                "proportionate and far cheaper than a slice.",
            )
        return None

    # -- the floor -----------------------------------------------------------

    def decide(self, case: Case, facts: Dict[str, Any]) -> Tuple[str, str, str, float]:
        event = case.facts.get("event", "evacuation")
        if event == "induction":
            return self._decide_induction(case, facts)
        if event == "zone_control":
            return self._decide_zone(case, facts)
        if event == "heat":
            return self._decide_heat(case, facts)
        return self._decide_evacuation(case, facts)

    def _decide_induction(self, case: Case, facts: Dict[str, Any]):
        worker = case.facts.get("worker", "this worker")
        if not facts.get("number_verified", True):
            return (
                "notify",
                "Send %s back to the badge desk; the line does not match the handset" % worker,
                "The network would not confirm this line is in this phone, so it "
                "cannot become the worker's site identity.",
                0.85,
            )
        if facts.get("geofence_active"):
            return (
                "clear",
                "%s is inducted; the work-zone fence is live" % worker,
                "The company line is confirmed in the handset and an area-left "
                "subscription is active for the work zone. One consent at induction "
                "covers shift hours and incidents, and nothing else.",
                0.92,
            )
        return (
            "notify",
            "Retry the work-zone subscription for this line",
            "The line verified but the area subscription did not come back active.",
            0.6,
        )

    def _decide_zone(self, case: Case, facts: Dict[str, Any]):
        f = case.facts
        worker = f.get("worker", "this worker")
        zone = f.get("zone_name", "the restricted zone")
        supervisor = f.get("supervisor", "the zone supervisor")

        if "location_result" not in facts:
            return (
                "notify",
                "Ask %s to do a visual check of %s" % (supervisor, zone),
                "No network evidence was available for this line.",
                0.35,
            )
        if f.get("ticketed"):
            return (
                "clear",
                "No action; the worker is cleared for this zone",
                "%s is inside %s and holds a ticket for it." % (worker, zone),
                0.9,
            )
        if facts.get("location_inside"):
            return (
                "breach",
                "Tell %s now: %s is inside %s without a ticket" % (supervisor, worker, zone),
                "The network places this line inside a zone the worker is not "
                "cleared for. The message goes to the supervisor rather than to the "
                "worker, who may not read the language this system speaks.",
                0.92,
            )
        if facts.get("location_uncertain"):
            return (
                "notify",
                "Ask %s for a visual check at the edge of %s" % (supervisor, zone),
                "The network could not answer cleanly, which is what standing next "
                "to the zone boundary looks like. Worth a look, not worth a breach "
                "report against someone's record.",
                0.7,
            )
        return (
            "clear",
            "No action",
            "%s is outside %s." % (worker, zone),
            0.88,
        )

    def _decide_heat(self, case: Case, facts: Dict[str, Any]):
        f = case.facts
        worker = f.get("worker", "this worker")
        supervisor = f.get("supervisor", "the zone supervisor")
        index = f.get("heat_index", "the limit")

        if "location_result" not in facts:
            return (
                "notify",
                "Ask %s to sweep the open-air zones" % supervisor,
                "No network evidence was available for this line.",
                0.35,
            )
        if facts.get("location_inside") or facts.get("location_uncertain"):
            return (
                "notify",
                "Tell %s to move %s into shade now" % (supervisor, worker),
                "The heat index is %s and this line is still inside an open-air "
                "zone. A work ban that nobody can see being broken is not a work "
                "ban, and this is the gap it fills." % index,
                0.88,
            )
        return (
            "clear",
            "No action; this worker is already out of the open-air zone",
            "The network places this line outside the open-air zone.",
            0.88,
        )

    def _decide_evacuation(self, case: Case, facts: Dict[str, Any]):
        f = case.facts
        worker = f.get("worker", "this worker")
        supervisor = f.get("supervisor", "the zone supervisor")
        minutes = f.get("minutes_since_alarm", "several")

        if "location_result" not in facts:
            return (
                "notify",
                "Count this worker by hand at the muster point",
                "No network evidence was available for this line, so the muster "
                "falls back to a clipboard for this one worker.",
                0.35,
            )

        if facts.get("location_inside"):
            return (
                "clear",
                "Accounted for at the muster point",
                "The network places %s inside the muster circle %s minutes after "
                "the alarm. One call, and this worker is off the list." % (worker, minutes),
                0.93,
            )

        if facts.get("silent"):
            detail = ""
            if facts.get("has_last_known_point"):
                detail = " A last known area is attached for the rescue team"
                if facts.get("slice_attachment_id"):
                    detail += ", and the team's line is on the emergency slice because the cell is saturated"
                elif facts.get("qod_session_id"):
                    detail += ", with a reserved quality session for their video"
                detail += "."
            return (
                "missing",
                "Send the rescue team to the last known area for %s now" % worker,
                "%s is not at the muster point and the network cannot reach the "
                "line at all, %s minutes after the alarm. That rules out a worker "
                "who simply walked the wrong way and is the pattern of a phone that "
                "lost power in a fall.%s" % (worker, minutes, detail),
                0.92,
            )

        if facts.get("location_uncertain"):
            return (
                "notify",
                "Have %s eyeball the muster edge for %s" % (supervisor, worker),
                "The network could not place this line cleanly inside or outside the "
                "muster circle, which is what standing behind a container looks "
                "like. The line is reachable, so this is a visual check - declaring "
                "a worker missing on an uncertain answer sends a rescue team away "
                "from a real casualty.",
                0.72,
            )

        return (
            "notify",
            "Have %s call %s; he is out of the zone but not at muster" % (supervisor, worker),
            "%s is outside the muster circle but the line is reachable, so this is a "
            "worker walking the wrong way rather than a casualty. A phone call "
            "settles it." % worker,
            0.86,
        )
