"""Hazir product spec: theme 2, smart cities, urban safety and mega-project infrastructure."""

from __future__ import annotations

from core.agent import Case
from core.idea import ConsentPlan, IdeaSpec, LevelStyle, Scenario, UiSpec
from core.simulator import LineProfile

from .policy import HazirPolicy

POLICY = HazirPolicy()

# A giga-project site on the Red Sea coast. Three geometries matter: where
# people gather when the alarm sounds, the crane zone nobody enters without a
# ticket, and the open-air area the heat ban applies to.
MUSTER = (28.0000, 35.3000)
MUSTER_RADIUS_M = 300
CRANE_ZONE = (28.0150, 35.3100)
CRANE_RADIUS_M = 200
OPEN_AIR = (28.0080, 35.2950)
OPEN_AIR_RADIUS_M = 500

_M_PER_DEG_LAT = 111320.0


def _from(point: tuple, metres: float) -> tuple:
    return (point[0] + metres / _M_PER_DEG_LAT, point[1])


LINE_AT_MUSTER = LineProfile(
    msisdn="+966580000501",
    label="At the muster point, four minutes after the alarm",
    latitude=MUSTER[0],
    longitude=MUSTER[1],
    location_accuracy_m=90,
    notes="One call and he is off the list. This is the branch that has to scale.",
)

LINE_WANDERING = LineProfile(
    msisdn="+966580000502",
    label="1.1 km from muster, phone answering",
    latitude=_from(MUSTER, 1100)[0],
    longitude=_from(MUSTER, 1100)[1],
    location_accuracy_m=150,
    notes="Walked the wrong way. A phone call, not a rescue.",
)

LINE_DOWN = LineProfile(
    msisdn="+966580000503",
    label="Not at muster and unreachable",
    latitude=_from(MUSTER, 1600)[0],
    longitude=_from(MUSTER, 1600)[1],
    location_accuracy_m=400,
    reachability="NOT_CONNECTED",
    congestion="low",
    notes="The casualty the clipboard finds an hour later.",
)

LINE_DOWN_SATURATED = LineProfile(
    msisdn="+966580000504",
    label="Unreachable, and the cell around him is saturated",
    latitude=_from(MUSTER, 2100)[0],
    longitude=_from(MUSTER, 2100)[1],
    location_accuracy_m=500,
    reachability="NOT_CONNECTED",
    congestion="high",
    congestion_confidence=94,
    notes="Same outcome, but the rescue team needs a slice to work at all.",
)

LINE_BEHIND_CONTAINER = LineProfile(
    msisdn="+966580000505",
    label="On the muster edge behind steel, network answers PARTIAL",
    latitude=_from(MUSTER, 320)[0],
    longitude=_from(MUSTER, 320)[1],
    location_accuracy_m=450,
    force_verification="PARTIAL",
    notes="Never declare a man missing on an uncertain answer.",
)

LINE_CRANE_BREACH = LineProfile(
    msisdn="+966580000506",
    label="Inside the crane zone without a ticket",
    latitude=CRANE_ZONE[0],
    longitude=CRANE_ZONE[1],
    location_accuracy_m=80,
    notes="Zone control that does not stop at the gate.",
)

LINE_HEAT = LineProfile(
    msisdn="+966580000507",
    label="Still in open sun at heat index 46",
    latitude=OPEN_AIR[0],
    longitude=OPEN_AIR[1],
    location_accuracy_m=150,
    notes="A work ban nobody can see being broken is not a work ban.",
)

LINE_INDUCTION = LineProfile(
    msisdn="+966580000508",
    label="New starter at the badge desk",
    latitude=MUSTER[0],
    longitude=MUSTER[1],
    location_accuracy_m=90,
    notes="Verify the company line, then create the work-zone fence. Once.",
)


def _evacuation(subject: str, worker: str, badge: str, language: str, minutes: int, label: str) -> Case:
    return Case(
        subject=subject,
        kind="site_event",
        label=label,
        facts={
            "event": "evacuation",
            "worker": worker,
            "badge": badge,
            "language": language,
            "contractor": "Zone 4 civils",
            "supervisor": "Mr Haddad",
            "incident": "gas release, sector 4",
            "minutes_since_alarm": minutes,
        },
        latitude=MUSTER[0],
        longitude=MUSTER[1],
        radius_m=MUSTER_RADIUS_M,
        params={"slice_id": "site-emergency-slice", "qos_profile": "QOS_L"},
    )


SCENARIOS = [
    Scenario(
        id="muster-accounted",
        title="Worker at the muster point",
        subtitle="Four minutes after the alarm, inside the 300 m circle",
        expect_level="clear",
        lines=[LINE_AT_MUSTER],
        narrative="The branch that decides whether this product can be sold.",
        teaches=(
            "One area check, two units, no position retrieved. On a site of ten "
            "thousand workers this is the call that runs ten thousand times, so "
            "everything else in the policy is built around keeping it cheap."
        ),
        build_case=lambda: _evacuation(
            LINE_AT_MUSTER.msisdn, "A. Kumar", "Z4-1187", "Hindi", 4, "At muster"
        ),
    ),
    Scenario(
        id="muster-wandering",
        title="Out of the zone but not at muster",
        subtitle="1.1 km away and answering on data",
        expect_level="notify",
        lines=[LINE_WANDERING],
        narrative="Not every missing head is a casualty.",
        teaches=(
            "Reachability is the cheap question that stops a rescue team being "
            "sent after a man who just walked the wrong way. The supervisor makes "
            "a phone call instead."
        ),
        build_case=lambda: _evacuation(
            LINE_WANDERING.msisdn, "S. Rahman", "Z4-0912", "Bengali", 6, "Walked the wrong way"
        ),
    ),
    Scenario(
        id="muster-missing",
        title="Not at muster and unreachable",
        subtitle="Seven minutes after the alarm, the network cannot reach the line",
        expect_level="missing",
        lines=[LINE_DOWN],
        narrative="What the clipboard finds an hour later.",
        teaches=(
            "The muster is short by one and the line is silent, which rules out a "
            "worker ignoring the alarm. The agent retrieves a last known area so "
            "the rescue team has somewhere to start in the first minutes, not the "
            "first hour."
        ),
        build_case=lambda: _evacuation(
            LINE_DOWN.msisdn, "M. Farouk", "Z4-2231", "Arabic", 7, "Missing at muster"
        ),
    ),
    Scenario(
        id="muster-missing-saturated",
        title="Missing, and the incident has filled the cell",
        subtitle="Unreachable line plus a saturated cell around the last ping",
        expect_level="missing",
        lines=[LINE_DOWN_SATURATED],
        narrative="When the network itself is the obstacle.",
        teaches=(
            "Identical outcome to the previous case, but congestion changes what "
            "the responders get: the rescue team's line goes onto the site "
            "emergency slice, because helmet video over a saturated cell is no "
            "video at all."
        ),
        build_case=lambda: _evacuation(
            LINE_DOWN_SATURATED.msisdn, "J. Silva", "Z4-3040", "English", 9,
            "Missing, saturated cell",
        ),
    ),
    Scenario(
        id="muster-uncertain",
        title="The network answers PARTIAL at the muster edge",
        subtitle="Standing behind steel containers, line still reachable",
        expect_level="notify",
        lines=[LINE_BEHIND_CONTAINER],
        narrative="The mistake that kills people.",
        teaches=(
            "Steel and scaffolding produce PARTIAL answers constantly. Declaring "
            "this worker missing would send a rescue team away from a real "
            "casualty, so the agent asks the supervisor to look instead."
        ),
        build_case=lambda: _evacuation(
            LINE_BEHIND_CONTAINER.msisdn, "R. Dizon", "Z4-1504", "Tagalog", 5,
            "Uncertain at the muster edge",
        ),
    ),
    Scenario(
        id="crane-zone-breach",
        title="Inside the crane zone without a ticket",
        subtitle="Zone control after the gate, reported to the zone supervisor",
        expect_level="breach",
        lines=[LINE_CRANE_BREACH],
        narrative="Where zone control stops working today.",
        teaches=(
            "The finding goes to the supervisor of that zone, not to the worker. He "
            "may not read the language the system speaks, and a warning nobody "
            "understands is not a control."
        ),
        build_case=lambda: Case(
            subject=LINE_CRANE_BREACH.msisdn,
            kind="site_event",
            label="Crane zone entry without a ticket",
            facts={
                "event": "zone_control",
                "worker": "P. Thapa",
                "badge": "Z7-0455",
                "language": "Nepali",
                "contractor": "Lifting subcontractor",
                "supervisor": "Mr Nassar",
                "zone_name": "Crane 12 lifting radius",
                "ticketed": False,
            },
            latitude=CRANE_ZONE[0],
            longitude=CRANE_ZONE[1],
            radius_m=CRANE_RADIUS_M,
        ),
    ),
    Scenario(
        id="heat-open-air",
        title="Still in open sun at heat index 46",
        subtitle="The work ban crossed twenty minutes ago",
        expect_level="notify",
        lines=[LINE_HEAT],
        narrative="A rule that exists but cannot be seen.",
        teaches=(
            "The heat ban is already law in the Gulf. What is missing is knowing "
            "who is still standing in it on a site the size of a city, and that is "
            "one area check per worker in the open-air zones."
        ),
        build_case=lambda: Case(
            subject=LINE_HEAT.msisdn,
            kind="site_event",
            label="Heat ban, worker still in the open",
            facts={
                "event": "heat",
                "worker": "K. Islam",
                "badge": "Z2-7781",
                "language": "Bengali",
                "contractor": "Earthworks",
                "supervisor": "Mr Obaid",
                "zone_name": "Open-air laydown area",
                "heat_index": 46,
            },
            latitude=OPEN_AIR[0],
            longitude=OPEN_AIR[1],
            radius_m=OPEN_AIR_RADIUS_M,
        ),
    ),
    Scenario(
        id="induction-enrol",
        title="Induct a new starter",
        subtitle="Verify the company line, then create the work-zone fence",
        expect_level="clear",
        lines=[LINE_INDUCTION],
        narrative="Where consent is taken and the muster is made possible.",
        teaches=(
            "This runs once per worker. Creating the fence at induction is what "
            "makes an instant muster possible later without any setup at the moment "
            "the alarm sounds."
        ),
        build_case=lambda: Case(
            subject=LINE_INDUCTION.msisdn,
            kind="site_event",
            label="Induction at the badge desk",
            facts={
                "event": "induction",
                "worker": "T. Nguyen",
                "badge": "Z4-4102",
                "language": "Vietnamese",
                "contractor": "Zone 4 civils",
                "supervisor": "Mr Haddad",
            },
            latitude=MUSTER[0],
            longitude=MUSTER[1],
            radius_m=3000,
            params={"webhook_url": "https://hazir.example/hooks/geofence"},
        ),
    ),
]

SPEC = IdeaSpec(
    slug="hazir",
    name="Hazir",
    tagline="A live evacuation headcount from the network",
    theme_number=2,
    theme_name="Smart Cities, Urban Safety & Mega-Project Infrastructure",
    submission_title="Hazir - a live evacuation headcount from the network on giga project sites",
    submission_description=(
        "On a giga-project site holding ten thousand workers, an evacuation "
        "headcount takes an hour with a clipboard. Hazir gets it from the mobile "
        "line each worker already carries - no tag, no beacon, no app - and turns "
        "silence into a rescue list with a last known area in the first minutes."
    ),
    policy=POLICY,
    scenarios=SCENARIOS,
    lines=[
        LINE_AT_MUSTER,
        LINE_WANDERING,
        LINE_DOWN,
        LINE_DOWN_SATURATED,
        LINE_BEHIND_CONTAINER,
        LINE_CRANE_BREACH,
        LINE_HEAT,
        LINE_INDUCTION,
    ],
    consent=ConsentPlan(
        moment="at induction, alongside the site pass and the safety briefing",
        scopes=[
            "identity:verify",
            "location:verify",
            "location:retrieve",
            "location:geofence",
            "device:status",
            "network:insights",
            "network:qod",
            "network:slice",
        ],
        who_consents=(
            "the worker, who is a contracted employee and on most Gulf sites already "
            "carries the company line as part of the kit"
        ),
        duration_note=(
            "Checks run during shift hours and during a declared incident, and stop "
            "when the worker clocks out. Zone level only, never a pin."
        ),
        revocation=(
            "A worker can withdraw, and the site then counts them by hand. Consent "
            "for safety monitoring should not be a condition of being rescued."
        ),
    ),
    ui=UiSpec(
        accent="#c2703a",
        accent_soft="#fbeee5",
        hero_kicker=(
            "Ten thousand workers, many square kilometres, and a headcount that "
            "takes an hour. Hazir asks the network instead, one cheap question per "
            "worker."
        ),
        subject_label="Worker line (company SIM)",
        case_label="Site event",
        run_all_label="Run all eight site events",
        ad_hoc_placeholder="+966580000503",
        ad_hoc_help=(
            "An ad-hoc check runs the evacuation muster path against the 300 m "
            "muster circle. Unregistered numbers get a stable derived profile."
        ),
        levels=[
            LevelStyle("clear", "Accounted for", "calm",
                       "At the muster point, or cleared for the zone."),
            LevelStyle("notify", "Tell the zone supervisor", "watch",
                       "A human should look or make a call."),
            LevelStyle("breach", "Zone breach", "warn",
                       "Inside a zone without a ticket for it."),
            LevelStyle("missing", "Missing - send the rescue team", "alarm",
                       "Not at muster and unreachable."),
        ],
    ),
    honest_limits=[
        "Hazir accounts for lines, not bodies. A worker who leaves his phone in the "
        "canteen shows as accounted for at the canteen, so this shortens the "
        "clipboard round rather than replacing it.",
        "Location verification is cell and area resolution. A 300 m muster circle "
        "works; telling two adjacent scaffolds apart does not.",
        "PARTIAL answers are common around steel and concrete, and the policy "
        "deliberately downgrades them to a visual check. That means some genuinely "
        "missing workers will first read as uncertain.",
        "Network slices and quality sessions depend on the operator actually "
        "offering them on that site. Where they are not available the agent still "
        "produces the rescue list, just without the reserved bandwidth.",
    ],
    buyers=[
        "Main contractors and site safety departments paying per worker per month",
        "Insurers and project clients, who push for it because a live muster lowers their own risk",
        "Mobile operators, who share the API income and can sell it with the site line plan",
    ],
    repo_name="hazir-nac-agent",
    demo_notes=(
        "Run muster-accounted first to show the cheap path, then the uncertain case "
        "to show the agent refusing to declare a man missing on a PARTIAL answer."
    ),
)
