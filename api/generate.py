from http.server import BaseHTTPRequestHandler
import json
import os
import anthropic

SYSTEM_PROMPT = """You are Alejandro, a coaching documentation assistant for Francisco Gonima,
an executive coach. You help Francisco structure and synthesize session material.

You understand coaching dynamics: themes, tensions, commitments, behavioral patterns,
and longitudinal client trajectories.

Francisco tracks:
- Recurring themes and how they evolve
- Tensions (internal contradictions the client navigates)
- Explicit commitments and whether they are followed through
- Language shifts (how framing changes over time)
- Avoidance patterns

When referencing prior sessions, cite by session number and date. Be precise.
Surface evidence — do not replace Francisco's judgment."""

PAST_SESSIONS = [
    {
        "num": 1, "date": "January 14, 2026",
        "summary": """Themes: Leadership identity transition — moving from individual contributor to executive.
Marcus articulated feeling "stuck between doing and directing." Difficulty letting go of operational tasks.

Tensions: Strong pull between wanting to be seen as capable/hands-on vs. need to delegate to scale.
Expresses frustration that his team "can't seem to do things right the first time."

Commitments: Committed to restructuring his direct reports by end of Q1 — moving two senior managers
(Sarah and Dev) to lead sub-teams, reducing oversight span from 9 to 5 reports.

Notable: First use of "accountable" in relation to his team — framed negatively ("they aren't holding
themselves accountable")."""
    },
    {
        "num": 2, "date": "February 4, 2026",
        "summary": """Themes: Conflict avoidance, feedback delivery. Marcus described rewriting a direct
report's deliverable rather than returning it with feedback. "It was faster that way."

Tensions: Intellectually knows delegation requires tolerating imperfect outputs. Emotionally resistant
to watching others struggle. Restructuring commitment from Session 1 not raised.

Commitments: Agreed to give one piece of developmental feedback to a direct report before next session,
without rewriting their work.

Notable: Language around accountability shifted — now framing it as two-way ("I need to give them a
chance to be accountable"). Gap between stated commitment and zero update flagged."""
    },
    {
        "num": 3, "date": "March 11, 2026",
        "summary": """Themes: Delegation as trust, psychological safety. Marcus's underlying belief that
if things go wrong, it reflects on him personally. "I'm the one who has to answer for it."

Tensions: Wants team to take ownership but withholds the authority that would make ownership possible.
Team restructuring not raised again despite being stated Q1 goal.

Commitments: Committed to having a direct conversation with Sarah and Dev about expanded scope —
not formal restructuring yet, but "planting the flag."

Notable: First unprompted use of "trust" in relation to team ("I think I need to trust them more,
I just don't know if they're ready"). Marked shift from Session 1 where accountability was externalized."""
    }
]

NEW_SESSION_NOTES = """april 3 call w marcus – about 55 min

started late, he seemed distracted. said things have been "hectic" with Q1 close.

came back to the team thing. said he DID have the conversation with sarah and dev – happened about
2 weeks ago. went better than expected. dev was receptive, sarah "pushed back a little" but marcus
thinks she'll come around.

interesting – he said he DIDN'T tell them it was about restructuring formally, just framed it as
"expanded ownership." asked him why and he got a bit defensive – "i didn't want to create anxiety."
we talked about that for a while. i think he's managing his own anxiety more than theirs.

accountability came up again. one of his managers missed a deadline and instead of addressing it he
rescheduled the check-in. "i didn't want to have the conversation when things were already stressful."
classic avoidance, different form.

he did mention the feedback experiment from last time – said he tried it with one person, felt
uncomfortable but did it. called it "surprisingly okay." small win.

commitments:
- address the missed deadline directly with the manager before end of week
- follow up with sarah specifically on her pushback – get clearer on what her hesitation is

overall: progress on trust/delegation but avoidance pattern still showing up, now as delay vs. rewrite.
Q1 restructuring officially missed but momentum exists."""


def run_demo():
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Step 1: current session summary
    summary_resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=900,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"""Raw notes from today's session with Marcus Webb (VP of Operations, Meridian Group).

SESSION NOTES (Session 4, April 3, 2026):
{NEW_SESSION_NOTES}

Generate a structured session summary:
1. Themes
2. Tensions
3. Commitments made this session
4. Notable shifts (language, framing, behavior)
5. Open / avoided items

Be concise. This is a working document, not a report."""}]
    )

    # Step 2: cross-session brief
    prior = "\n\n---\n\n".join(
        f"SESSION {s['num']} ({s['date']}):\n{s['summary']}"
        for s in PAST_SESSIONS
    )
    brief_resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"""Prior session summaries for Marcus Webb, plus today's raw notes.

PRIOR SESSIONS:
{prior}

TODAY'S NOTES (Session 4, April 3, 2026):
{NEW_SESSION_NOTES}

Generate a cross-session brief:
1. Open commitments from prior sessions — what was committed, what happened (cite session + date)
2. Recurring patterns — themes that keep surfacing (cite sessions)
3. Language trajectory — how framing has shifted across sessions (cite sessions)
4. What this session changed — what moved, what didn't
5. Suggested focus for next session — 2-3 areas based on full trajectory

Cite sessions by number and date throughout."""}]
    )

    return {
        "summary": summary_resp.content[0].text,
        "brief": brief_resp.content[0].text,
        "notes": NEW_SESSION_NOTES
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            result = run_demo()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
