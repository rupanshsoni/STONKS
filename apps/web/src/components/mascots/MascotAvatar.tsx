"use client";

import { useMemo, memo } from "react";
import { motion } from "framer-motion";
import { shade } from "./cast";
import type { MascotState } from "@/lib/types";

export type PropType =
  | "arms"
  | "phone"
  | "horns"
  | "umbrella"
  | "gavel"
  | "clipboard"
  | "stamp"
  | "lightbulb";

interface MascotAvatarProps {
  agent: string;
  ink: string;
  prop?: PropType;
  state?: MascotState | "thinking" | "loss";
  size?: number;
  headOnly?: boolean;
  interactive?: boolean;
}

function AgentProp({ type, ink }: { type: PropType; ink: string }) {
  const light = shade(ink, 0.25);
  const dark = shade(ink, -0.4);

  switch (type) {
    case "horns":
      return (
        <g className="mascot-prop-horns" filter="drop-shadow(0 0 4px rgba(0,255,135,0.4))">
          {/* Left horn */}
          <polygon points="26,34 16,18 29,27" fill={ink} stroke="#FFFFFF" strokeWidth="0.75" />
          <polygon points="26,34 16,18 21,29" fill={light} />
          {/* Right horn */}
          <polygon points="74,34 84,18 71,27" fill={ink} stroke="#FFFFFF" strokeWidth="0.75" />
          <polygon points="74,34 84,18 79,29" fill={light} />
        </g>
      );
    case "phone":
      return (
        <g className="mascot-prop-phone" filter="drop-shadow(0 0 5px rgba(56,189,248,0.4))">
          {/* Holographic news tablet */}
          <rect x="68" y="44" width="16" height="24" rx="2" fill="#070a14" stroke={ink} strokeWidth="1.2" />
          <rect x="71" y="47" width="10" height="2" rx="0.5" fill={ink} />
          <rect x="71" y="51" width="7" height="1.5" rx="0.5" fill={light} opacity="0.8" />
          <rect x="71" y="54" width="9" height="1.5" rx="0.5" fill={light} opacity="0.6" />
          {/* Mini pulse wave */}
          <path d="M71 61 L73 59 L75 62 L77 58 L79 61" stroke={ink} strokeWidth="0.9" fill="none" />
        </g>
      );
    case "umbrella":
      return (
        <g className="mascot-prop-umbrella">
          {/* Carbon umbrella canopy */}
          <path d="M66 42 Q76 34 86 42 Z" fill={ink} stroke="#FFFFFF" strokeWidth="0.75" />
          <path d="M71 42 Q76 37 81 42" fill={dark} opacity="0.5" />
          <line x1="76" y1="42" x2="76" y2="64" stroke="#D1D5DB" strokeWidth="1.2" />
          <path d="M76 64 Q78 67 75 68 Q72 67 74 65" fill="none" stroke="#D1D5DB" strokeWidth="1.2" />
        </g>
      );
    case "gavel":
      return (
        <g className="mascot-prop-gavel" filter="drop-shadow(0 0 4px rgba(199,125,255,0.4))">
          <rect
            x="67"
            y="42"
            width="15"
            height="7"
            rx="1.5"
            fill={ink}
            stroke="#FFFFFF"
            strokeWidth="0.8"
            transform="rotate(-25 74 45)"
          />
          <line x1="78" y1="48" x2="72" y2="62" stroke="#E2E8F0" strokeWidth="1.6" />
          <circle cx="78" cy="48" r="1.5" fill={light} />
        </g>
      );
    case "clipboard":
      return (
        <g className="mascot-prop-clipboard" filter="drop-shadow(0 0 4px rgba(251,191,36,0.3))">
          <rect x="66" y="44" width="16" height="22" rx="2" fill="#0A0E1A" stroke={ink} strokeWidth="1.2" />
          <rect x="70" y="42" width="8" height="3.5" rx="1" fill={ink} />
          {/* 12-gate visual checklist */}
          <line x1="70" y1="49" x2="78" y2="49" stroke={light} strokeWidth="1" />
          <line x1="70" y1="53" x2="78" y2="53" stroke={light} strokeWidth="1" />
          <line x1="70" y1="57" x2="78" y2="57" stroke={light} strokeWidth="1" />
          <line x1="70" y1="61" x2="75" y2="61" stroke={light} strokeWidth="1" />
        </g>
      );
    case "stamp":
      return (
        <g className="mascot-prop-stamp" filter="drop-shadow(0 0 5px rgba(0,229,255,0.4))">
          <rect x="68" y="48" width="14" height="8" rx="1.5" fill={ink} stroke="#FFFFFF" strokeWidth="0.8" />
          <path d="M73 48 L73 41 Q75 39 77 41 L77 48 Z" fill={dark} stroke={ink} strokeWidth="0.8" />
          <line x1="71" y1="52" x2="79" y2="52" stroke="#04091B" strokeWidth="1" strokeDasharray="1.5 1" />
        </g>
      );
    case "lightbulb":
      return (
        <g className="mascot-prop-lightbulb" filter="drop-shadow(0 0 6px rgba(251,146,60,0.5))">
          <circle cx="76" cy="44" r="6" fill={ink} stroke="#FFFFFF" strokeWidth="0.8" />
          <polygon points="73,49 79,49 78,53 74,53" fill="#D1D5DB" />
          <line x1="76" y1="41" x2="76" y2="47" stroke="#060913" strokeWidth="1" />
          {/* Energy rays */}
          <line x1="76" y1="35" x2="76" y2="37" stroke={ink} strokeWidth="1" />
          <line x1="83" y1="38" x2="81" y2="40" stroke={ink} strokeWidth="1" />
          <line x1="69" y1="38" x2="71" y2="40" stroke={ink} strokeWidth="1" />
        </g>
      );
    default:
      return null;
  }
}

export default function MascotAvatar({
  agent,
  ink,
  prop = "arms",
  state = "idle",
  size = 96,
  headOnly = false,
  interactive = false,
}: MascotAvatarProps) {
  const light = useMemo(() => shade(ink, 0.22), [ink]);
  const deep = useMemo(() => shade(ink, -0.25), [ink]);
  const dark = useMemo(() => shade(ink, -0.45), [ink]);

  const isCelebrating = state === "celebrating";
  const isLoss = state === "loss" || state === "risk_alert";
  const isThinking = state === "analyzing" || state === "thinking" || state === "debating";

  return (
    <div
      className={`mascot-container mascot-state-${state} ${interactive ? "cursor-pointer" : ""}`}
      style={{ width: size, height: size }}
    >
      <motion.svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        role="img"
        aria-label={`${agent} mascot`}
        className="mascot-svg select-none overflow-visible"
        animate={
          isCelebrating
            ? { y: [0, -6, 0, -4, 0], scale: [1, 1.05, 1, 1.03, 1] }
            : isLoss
            ? { y: [0, 3, 2, 3], rotate: [0, 3, 2, 3] }
            : isThinking
            ? { rotate: [-2, 2, -2], y: [0, -2, 0] }
            : { y: [0, -4, 0] }
        }
        transition={{
          duration: isCelebrating ? 1.2 : isThinking ? 2.2 : 3,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        <defs>
          {/* Subtle metallic facet gradients */}
          <linearGradient id={`grad-light-${agent}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.4" />
            <stop offset="100%" stopColor={ink} stopOpacity="1" />
          </linearGradient>
          <linearGradient id={`grad-main-${agent}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={light} />
            <stop offset="100%" stopColor={ink} />
          </linearGradient>
          <linearGradient id={`grad-shadow-${agent}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={deep} />
            <stop offset="100%" stopColor={dark} />
          </linearGradient>
          <radialGradient id={`grad-halo-${agent}`} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={ink} stopOpacity="0.35" />
            <stop offset="100%" stopColor={ink} stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Floating shadow beneath avatar */}
        {!headOnly && (
          <ellipse
            cx="50"
            cy="96"
            rx="22"
            ry="3.5"
            fill="rgba(0, 0, 0, 0.45)"
            className="mascot-ground-shadow"
          />
        )}

        {/* Ambient aura halo behind head */}
        <circle
          cx="50"
          cy="48"
          r="34"
          fill={`url(#grad-halo-${agent})`}
          className="mascot-think-halo pointer-events-none"
          opacity={isThinking ? 0.8 : isCelebrating ? 1 : 0.25}
        />

        {/* Celebration sparkles */}
        {isCelebrating && (
          <g className="mascot-sparkles">
            <polygon points="18,24 20,20 24,18 20,16 18,12 16,16 12,18 16,20" fill="#FDE047" opacity="0.9" />
            <polygon points="82,22 84,19 87,17 84,15 82,12 80,15 77,17 80,19" fill="#00FF87" opacity="0.9" />
            <polygon points="50,14 51.5,11 54,10 51.5,9 50,6 48.5,9 46,10 48.5,11" fill="#FFFFFF" opacity="0.95" />
          </g>
        )}

        {/* Suit & Body */}
        {!headOnly && (
          <g className="mascot-body">
            {/* Dark suit torso */}
            <polygon
              points="36,70 64,70 68,95 32,95"
              fill="#0b0f1d"
              stroke={deep}
              strokeWidth="0.8"
            />
            {/* Suit Lapels & Tie / Collar */}
            <polygon points="44,70 50,78 56,70 50,72" fill="#13192e" />
            <polygon points="49,72 51,72 50.5,82 49.5,82" fill={ink} opacity="0.9" />
            {/* Arms / Pose */}
            {prop === "arms" ? (
              <>
                <polygon
                  points="28,74 38,72 36,83 27,80"
                  fill="#0e1426"
                  stroke={deep}
                  strokeWidth="0.75"
                />
                <polygon
                  points="72,74 62,72 64,83 73,80"
                  fill="#0e1426"
                  stroke={deep}
                  strokeWidth="0.75"
                />
                {/* Stonks up-arrow for Prime */}
                {agent === "prime" && (
                  <path
                    d="M48 88 L52 88 L52 83 L55 83 L50 78 L45 83 L48 83 Z"
                    fill="#00FF87"
                    filter="drop-shadow(0 0 3px rgba(0,255,135,0.6))"
                  />
                )}
              </>
            ) : null}
          </g>
        )}

        {/* 2.5D Faceted Head Anatomy */}
        <g className="mascot-stage">
          {/* Main Head Base Silhouette */}
          <polygon
            points="24,28 76,28 80,44 76,68 50,74 24,68 20,44"
            fill={`url(#grad-main-${agent})`}
            stroke="#FFFFFF"
            strokeWidth="1.2"
            strokeLinejoin="round"
          />

          {/* Top light reflection facet */}
          <polygon
            points="24,28 76,28 72,36 28,36"
            fill={`url(#grad-light-${agent})`}
            opacity="0.7"
          />

          {/* Left cheek light facet */}
          <polygon
            points="24,28 28,36 26,52 20,44"
            fill={light}
            opacity="0.6"
          />

          {/* Center forehead plate */}
          <polygon
            points="28,36 72,36 68,48 32,48"
            fill={ink}
          />

          {/* Right shadow-side facet */}
          <polygon
            points="76,28 80,44 76,68 70,64 72,36"
            fill={`url(#grad-shadow-${agent})`}
          />

          {/* Mid-face bridge */}
          <polygon
            points="32,48 68,48 64,60 36,60"
            fill={deep}
            opacity="0.4"
          />

          {/* Lower chin facet */}
          <polygon
            points="36,60 64,60 50,74 36,60"
            fill={dark}
            opacity="0.65"
          />

          {/* Expressive Eyes / Cyber Visor */}
          <g className="mascot-eyes" style={{ transformOrigin: "50px 48px" }}>
            {/* Eye sockets */}
            <ellipse cx="40" cy="46" rx="3.5" ry="4.5" fill="#040711" />
            <ellipse cx="60" cy="46" rx="3.5" ry="4.5" fill="#040711" />

            {/* Glowing pupils with gleam */}
            <circle
              cx={isThinking ? "39" : "40"}
              cy="46"
              r="2"
              fill={isLoss ? "#FF4D5E" : isCelebrating ? "#00FF87" : "#FFFFFF"}
              filter="drop-shadow(0 0 2px rgba(255,255,255,0.8))"
            />
            <circle
              cx={isThinking ? "59" : "60"}
              cy="46"
              r="2"
              fill={isLoss ? "#FF4D5E" : isCelebrating ? "#00FF87" : "#FFFFFF"}
              filter="drop-shadow(0 0 2px rgba(255,255,255,0.8))"
            />

            {/* Eye specular gleam */}
            <circle cx="39.2" cy="45.2" r="0.7" fill="#FFFFFF" />
            <circle cx="59.2" cy="45.2" r="0.7" fill="#FFFFFF" />
          </g>

          {/* Specific Agent Prop */}
          {prop !== "arms" && <AgentProp type={prop} ink={ink} />}
        </g>
      </motion.svg>
    </div>
  );
}

// Ultra-fast, static low-poly Mascot Chip for high performance scrolling in Activity Feed & Audit Journal
export const MascotChip = memo(function MascotChip({
  agent,
  size = 26,
}: {
  agent: string;
  size?: number;
  state?: MascotState;
}) {
  const norm = agent.toLowerCase();
  const colorMap: Record<string, { ink: string; eye: string }> = {
    prime: { ink: "#FFFFFF", eye: "#00E5FF" },
    senti: { ink: "#38BDF8", eye: "#38BDF8" },
    toro: { ink: "#00FF87", eye: "#00FF87" },
    ursa: { ink: "#FF4D5E", eye: "#FF4D5E" },
    verdi: { ink: "#C77DFF", eye: "#C77DFF" },
    gate: { ink: "#FBBF24", eye: "#FBBF24" },
    xq: { ink: "#00E5FF", eye: "#00E5FF" },
    sage: { ink: "#FB923C", eye: "#FB923C" },
    desk: { ink: "#00E5FF", eye: "#00E5FF" },
  };

  const item = colorMap[norm] ?? { ink: "#A8B0D0", eye: "#00E5FF" };
  const ink = item.ink;
  const eye = item.eye;

  return (
    <div
      className="inline-flex shrink-0 items-center justify-center rounded-lg p-0.5 border border-white/10 bg-[#080B15] transition-transform hover:scale-105 select-none"
      style={{
        width: size,
        height: size,
        boxShadow: `0 0 10px ${ink}20`,
        borderColor: `${ink}35`,
      }}
      title={agent.toUpperCase()}
    >
      <svg
        width={Math.max(12, size - 4)}
        height={Math.max(12, size - 4)}
        viewBox="0 0 100 100"
        className="overflow-visible select-none pointer-events-none"
      >
        <polygon points="50,18 68,32 50,38 32,32" fill={shade(ink, 0.25)} />
        <polygon points="32,32 50,38 50,56 26,48" fill={ink} />
        <polygon points="68,32 50,38 50,56 74,48" fill={shade(ink, -0.3)} />
        <polygon points="26,48 50,56 50,72 35,68" fill={shade(ink, -0.45)} />
        <polygon points="74,48 50,56 50,72 65,68" fill="#040711" />
        <rect x="39" y="44" width="4.5" height="2.5" rx="0.8" fill={eye} />
        <rect x="57" y="44" width="4.5" height="2.5" rx="0.8" fill={eye} />
      </svg>
    </div>
  );
});
