# BRAND & MASCOTS — Identity, The Cast, States, Animation

> The STONKS identity: a meme-man trading desk, alive on screen. Every mascot is a low-poly "stonks meme man" figure in the logo's style, individually colored from the logo's spectral palette, each with a signature prop and personality.

## 1. Brand identity

**Name:** STONKS (always caps in the wordmark; sentence case only in body text if ever needed).
**Full name:** Strategic Trading & Orchestration Network for Knowledge-driven Systems — README subtitle, footer tagline, submission description only.
**Mark:** `Assets/logo.png` — white low-poly meme-man head on deep navy `#04091B` with an RGB spectral scatter (glitch).
**Aesthetic:** meme-native but executed with Linear-grade discipline. The joke is the cast; the craft is the interface. One glance says "this is fun"; one minute says "this is engineered."

## 2. Visual language of the mascots

All characters share one anatomy — the classic stonks meme-man: **a smooth, low-poly faceted head (a rounded box built from flat polygon facets), no mouth, small dark eyes, an implied dark suit body below**. The "2.5D" feel comes from the facet shading: each head is built from 5–9 flat polygons with two or three brightness steps of the character's ink color — this is literally the meme's native style, so the authenticity is free.

- **Heads:** faceted polygon geometry (SVG polygons), two-tone shading (base ink + 12% darker facet planes on the "shadow side"), subtle white rim highlight on the "light side."
- **Eyes:** small dark ellipses; expressive via position/rotation only (never new anatomy).
- **Bodies:** minimal dark suit (near-navy `#0A0F26` so characters sit on the UI background), simple arms/hands rendered as flat shapes — enough to hold a prop.
- **Color:** each character's head facets use its accent ink (pure logo hues inside white 1.5px outline strokes so pure `#00FF00`-class colors stay punchy on navy).
- **No mouths.** All expression is posture, props, eyes, and caption text. (Meme-canon.)

## 3. The cast

| # | Character | Role | Ink (logo-derived) | Signature prop | Personality |
|---|---|---|---|---|---|
| 1 | **Stonks Prime** | Orchestrator & narrator — the brand mascot (the logo figure itself) | White `#F8F8F8` head; spectral glitch on celebrate | Crossed arms; occasionally the up-arrow (`/stonks` arrow) | Deadpan boss. Speaks in one-liners. "The desk is open." |
| 2 | **Senti** | Sentiment analyst | Blue `#4DA3FF` | A phone; newspaper when reading expert reviews | Empathic reader; quotes headlines; slightly dramatic |
| 3 | **Toro** | Bull researcher | Green `#00FF87` | Tiny horns headband | Relentless optimist; momentum lover |
| 4 | **Ursa** | Bear researcher | Red `#FF4D5E` | A closed umbrella | Professional pessimist; respected, not disliked |
| 5 | **Verdi** | Judge | Purple `#C77DFF` | A gavel | Impartial arbiter; declares verdicts with a tap |
| 6 | **Sgt. Gate** | Risk-kernel officer | Amber `#FFB020` | Hardhat + clipboard (the 12 gates) | Strict, incorruptible; "REJECTED: EVENT_RISK" with total calm |
| 7 | **XQ** | Executor | Cyan `#00E5FF` | An order stamp | Fast, precise; stamps FILLED |
| 8 | **Sage** | Post-mortem & self-improvement | Orange `#FF8A3D` | A lightbulb + a hand mirror | Reflective; turns losses into lessons |

## 4. States (event-driven, per mascot)

| State | Trigger | Animation notes |
|---|---|---|
| `idle` | default | breathing bob (y ±3px, sine, 1.6s loop), occasional blink (eyelid scaleY 0.1s) |
| `analyzing` | analyst/code agent running a task | head tilt; eyes narrow (scaleY 0.6); scanning sway; magnifier for flow analyst contexts |
| `reading_news` | Senti ingesting articles | newspaper up, page-flip every 900ms; head nods |
| `debating` | debate rounds active (Toro & Ursa) | lean-ins toward center; Toro gestures up, Ursa gestures down; Verdi watches (stern) |
| `trading` | order submitted/route working (XQ) | rapid stamp motion (y ±6px, 120ms) |
| `celebrating` | position closed at profit ≥ target | spectral glitch flash across facets (once, 180ms) + arrow-up pop |
| `post_mortem` | Sage analyzing a loss | mirror gaze → lightbulb blinks on |
| `risk_alert` | gate rejection / daily halt | Sgt. Gate clipboard raise + red X; others: brow furrow via eye-angle |
| `sleeping` | market closed | head droop, slow breathing (2.4s), tiny "z" glyph floats |

**Mapping example (a live cycle):** Prime narrates from `idle` → Senti `reading_news` → Toro & Ursa `debating` → Verdi `analyzing` (deliberation) → Sgt. Gate `analyzing` then `risk_alert` OR pass → XQ `trading` → on fill: XQ + Prime `celebrating` (glitch) → back to `idle`. Sage `post_mortem` interrupts the sequence when triggered, then returns with the lesson card.

## 5. Technical implementation (SVG + GSAP, 2.5D)

**Why SVG+GSAP:** full brand control (the logo's exact aesthetic), zero license/export risk (own .riv export needs a paid Rive plan), guaranteed to ship in ~2 days, tiny bundle, and state machines are trivial at this scale. **Rive polish for Prime is a stretch goal only.**

### 5.1 Component architecture

```
apps/web/src/components/mascots/
├── MascotAvatar.tsx        # shared anatomy; props: ink, prop, state
├── anatomy/
│   ├── head.facets.tsx     # polygon set (shared geometry, per-ink recolor)
│   ├── eyes.tsx            # expressive eyes (idle/blink/narrow)
│   ├── body.tsx            # suit silhouette + arms + prop mount points
│   └── props/              # phone, newspaper, horns, gavel, clipboard,
│                           # stamp, lightbulb, mirror, umbrella  (one SVG each)
├── animations/
│   └── states.ts           # Record<MascotState, TimelineFactory> — GSAP timelines
├── MascotStage.tsx         # the dock/portrait wrapper; hover tilt; reduced-motion
└── cast.ts                 # the 8 characters' config (ink, prop, role, quips)
```

- One **shared facet geometry** for all 8 heads (they're the same species) recolored per `ink` — consistency + 8× less SVG to author.
- `MascotAvatar` takes `{ character, state, size }`; GSAP timelines in `states.ts` map state → animation, killed & re-created on state change via `useGSAP` (`revertOnUpdate: true`, StrictMode-safe, auto-cleanup).
- **2.5D depth, three layers:** (1) facet shading (static polygons at two brightness steps); (2) hover tilt — the stage rotates the whole SVG ±6° toward the cursor (pointer tracking, transform-style flat but perspective-rotated) with the head layer counter-rotating +2° for parallax; (3) props positioned with small `translateZ`-faked offsets (darker drop shapes). No WebGL; the illusion is enough.
- **Drag:** Prime is draggable within the dock (GSAP `Draggable`, inertia, snaps back to dock with an elastic ease). Clicking any mascot plays its `poke` quip (Sonner toast with the character's voice line).
- `prefers-reduced-motion`: static pose per state (a `data-state` attribute swaps a keyframed CSS class to none) + caption text still updates.

### 5.2 State bridge (one source of truth)

```tsx
// the SSE event bus → zustand → mascot states (same store the feed uses)
type DeskEvent = { agent: AgentId; type: EventType; ... };

const agentStatus = useAgentStatusStore();   // e.g. senti: "reading_news"

function DeskDock() {
  return (
    <div className="mascot-dock">
      {cast.map(c => (
        <MascotAvatar key={c.id} character={c}
                      state={agentStatus[c.id] ?? "idle"} />
      ))}
    </div>
  );
}
```

No mascot ever polls; they render state emitted by the desk worker's SSE stream. A state always carries a fallback static cue (caption text under the dock: "Senti is reading 14 articles…").

## 6. Portraits in the UI

- **Overview dock:** the cast in a row (Prime center, larger) + Prime's caption line — the "desk meeting" composition.
- **Activity feed:** each event shows a 28px portrait of its agent (ink-colored ring).
- **/agents page:** 160px portraits with live state animation + role cards.
- **Post-mortem card:** Sage's portrait with mirror→lightbulb micro-story.
- **Empty/loading:** Prime shrugging (arms out) with "Scanning the tape…" caption.

## 7. Asset production plan (2-day-safe)

1. Author the **shared facet head** once (inks recolored) + body/arms + the 9 props — one focused pass.
2. Ship states in priority order: `idle, analyzing, debating, trading, celebrating, reading_news, sleeping, post_mortem, risk_alert` (first six are the demo path; last three complete the set).
3. Only after the full cast is wired, consider the Rive Prime upgrade (needs the one-month export plan; skip without hesitation if the submission clock is at risk).

## 8. Voice & quips (one-liners per character, used sparingly)

- **Prime:** "The desk is open." / "Stonks." (on wins)
- **Senti:** "Fourteen articles. Three mention earnings."
- **Toro:** "Momentum is a friend."
- **Ursa:** "It's expensive to be this right."
- **Verdi:** "Verdict." (gavel tap)
- **Sgt. Gate:** "No. EVENT_RISK." / "Twelve gates. Zero exceptions."
- **XQ:** "Filled." (stamp)
- **Sage:** "We lost. We learned."

Full copy rules: [UI.md](UI.md) §6.
