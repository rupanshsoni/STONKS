"use client";

import { shade } from "./cast";

type PropType =
  | "arms"
  | "phone"
  | "horns"
  | "umbrella"
  | "gavel"
  | "clipboard"
  | "stamp"
  | "lightbulb";

interface Props {
  agent: string;
  ink: string;
  prop: PropType;
  size?: number;
  headOnly?: boolean;
}

function Prop({ type, ink }: { type: PropType; ink: string }) {
  const stroke = shade(ink, -0.4);
  switch (type) {
    case "phone":
      return (
        <g className="mascot-prop-phone">
          <rect x="70" y="46" width="9" height="15" rx="1.5" fill="#04091B" stroke={ink} strokeWidth="1.2" />
          <rect x="71.5" y="48" width="6" height="10" fill={shade(ink, -0.6)} />
        </g>
      );
    case "horns":
      return (
        <g className="mascot-prop-horns">
          <polygon points="22,38 14,26 24,30" fill={ink} stroke="#F8F8F8" strokeWidth="0.8" />
          <polygon points="78,38 86,26 76,30" fill={ink} stroke="#F8F8F8" strokeWidth="0.8" />
        </g>
      );
    case "umbrella":
      return (
        <g className="mascot-prop-umbrella">
          <path d="M70 42 a8 8 0 0 1 16 0 z" fill={ink} stroke="#F8F8F8" strokeWidth="0.8" />
          <line x1="78" y1="42" x2="78" y2="60" stroke={ink} strokeWidth="1.2" />
          <path d="M78 60 q2 3 -1 4" fill="none" stroke={ink} strokeWidth="1.2" />
        </g>
      );
    case "gavel":
      return (
        <g className="mascot-prop-gavel">
          <rect x="68" y="44" width="12" height="5" rx="1" fill={ink} stroke="#F8F8F8" strokeWidth="0.8" transform="rotate(-20 74 46)" />
          <line x1="79" y1="49" x2="74" y2="60" stroke={ink} strokeWidth="1.5" />
        </g>
      );
    case "clipboard":
      return (
        <g className="mascot-prop-clipboard">
          <rect x="66" y="44" width="14" height="18" rx="1.5" fill="#0A0F26" stroke={ink} strokeWidth="1" />
          <line x1="69" y1="49" x2="77" y2="49" stroke={ink} strokeWidth="0.8" />
          <line x1="69" y1="52" x2="77" y2="52" stroke={ink} strokeWidth="0.8" />
          <line x1="69" y1="55" x2="74" y2="55" stroke={ink} strokeWidth="0.8" />
          <rect x="70" y="42" width="6" height="3" rx="1" fill={ink} />
        </g>
      );
    case "stamp":
      return (
        <g className="mascot-prop-stamp">
          <rect x="68" y="46" width="11" height="7" rx="1" fill={ink} stroke="#F8F8F8" strokeWidth="0.8" />
          <rect x="71.5" y="40" width="4" height="6" fill={shade(ink, -0.3)} />
        </g>
      );
    case "lightbulb":
      return (
        <g className="mascot-prop-lightbulb">
          <circle cx="76" cy="44" r="5" fill={ink} stroke="#F8F8F8" strokeWidth="0.8" />
          <rect x="74" y="49" width="4" height="3" fill={shade(ink, -0.3)} />
          <line x1="76" y1="41" x2="76" y2="47" stroke="#04091B" strokeWidth="0.8" />
        </g>
      );
    default:
      return null;
  }
}

export default function MascotAvatar({
  agent,
  ink,
  prop,
  size = 96,
  headOnly = false,
}: Props) {
  const light = shade(ink, 0.12);
  const dark = shade(ink, -0.18);
  const eyeBg = "#04091B";

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      role="img"
      aria-label={`${agent} mascot`}
      className="mascot-svg select-none"
    >
      {!headOnly && (
        <g className="mascot-body">
          <polygon
            points="38,72 62,72 66,100 34,100"
            fill="#0A0F26"
            stroke={shade(ink, -0.5)}
            strokeWidth="0.6"
          />
          <polygon points="34,100 38,72 42,72 40,100" fill="#060a1d" />
          <polygon points="58,72 62,72 66,100 60,100" fill="#060a1d" />
          {prop === "arms" && (
            <>
              <polygon points="30,76 38,74 36,84 29,82" fill="#0A0F26" stroke={shade(ink, -0.5)} strokeWidth="0.6" />
              <polygon points="70,76 62,74 64,84 71,82" fill="#0A0F26" stroke={shade(ink, -0.5)} strokeWidth="0.6" />
            </>
          )}
        </g>
      )}

      <g className="mascot-head">
        <g className="mascot-glitch" opacity="0">
          <polygon points="26,30 74,30 78,44 74,66 50,72 26,66 22,44" fill="#FF0000" />
        </g>
        <polygon
          points="26,30 74,30 78,44 74,66 50,72 26,66 22,44"
          fill={ink}
          stroke="#F8F8F8"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        <polygon points="26,30 74,30 72,38 30,42" fill={light} opacity="0.5" />
        <polygon points="74,30 78,44 74,66 70,64 72,40" fill={dark} />
        <polygon points="30,42 70,40 74,52 50,58 28,54" fill={dark} opacity="0.6" />
        <polygon points="30,64 50,70 70,64 66,68 50,72 34,68" fill={dark} opacity="0.4" />

        <g className="mascot-eyes" style={{ transformOrigin: "50px 48px" }}>
          <ellipse cx="41" cy="48" rx="2.4" ry="3.2" fill={eyeBg} />
          <ellipse cx="59" cy="48" rx="2.4" ry="3.2" fill={eyeBg} />
        </g>
        {prop !== "arms" && <Prop type={prop} ink={ink} />}
      </g>

      <style jsx>{`
        .mascot-eyes {
          transition: transform 0.2s ease;
        }
      `}</style>
    </svg>
  );
}
