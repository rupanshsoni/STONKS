export type AgentId =
  | "prime"
  | "senti"
  | "toro"
  | "ursa"
  | "verdi"
  | "gate"
  | "xq"
  | "sage"
  | "desk";

export type MascotState =
  | "idle"
  | "analyzing"
  | "reading_news"
  | "debating"
  | "trading"
  | "celebrating"
  | "post_mortem"
  | "risk_alert"
  | "sleeping";

export type Surface = "api" | "mcp" | "cli";

export interface Verdict {
  direction: "BULLISH" | "BEARISH" | "NEUTRAL";
  conviction: number;
  key_factor: string;
  weakest_link: string;
  model: string;
}

export interface SourceLean {
  source: string;
  credibility: number;
  lean: number;
  headline?: string | null;
  note?: string | null;
}

export interface SentimentReport {
  symbol: string;
  public_sentiment: number;
  confidence: number;
  source_breakdown: SourceLean[];
  expert_consensus: { lean: number; summary: string } | null;
  event_flags: string[];
  citations: string[];
  as_of: string;
}

export interface DebateClaim {
  fact_ref: string;
  argument: string;
}

export interface DebateRound {
  round: number;
  agent: "toro" | "ursa";
  claims: DebateClaim[];
  risks: string[];
  conviction: number;
}

export interface Leg {
  option_symbol: string;
  side: "buy" | "sell";
  ratio: number;
  strike: number;
  option_type: "call" | "put";
}

export interface StructureSpec {
  kind: string;
  intent: string;
  symbol: string;
  legs: Leg[];
  expiry: string;
  dte: number;
  width: number;
  credit: number;
  max_loss: number;
  contracts: number;
  premium_risk: number;
  pop: number | null;
  expected_move: number | null;
  notes: string;
}

export interface GateResult {
  gate: string;
  passed: boolean;
  reason_code: string | null;
  detail: string;
}

export interface JournalEvent {
  id: string;
  ts: string;
  cycle_id: string;
  agent: AgentId;
  type: string;
  symbol: string | null;
  summary: string;
  data: {
    mascot_state?: MascotState;
    approved?: boolean;
    results?: GateResult[];
    verdict?: Verdict;
    rounds?: DebateRound[];
    spec?: StructureSpec;
    sentiment?: SentimentReport;
    coid?: string;
    surface?: Surface;
    equity?: number;
    [k: string]: unknown;
  };
  surface: Surface | null;
  model: string | null;
  level: "info" | "warn" | "error";
}

export interface PositionView {
  id: string;
  coid: string;
  symbol: string;
  kind: string;
  qty: number;
  entry_ts: string;
  entry_credit: number;
  current_mark: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  dte: number;
  exit_status:
    | "held"
    | "tp_hit"
    | "stop_hit"
    | "time_stop"
    | "event_close"
    | "regime_flip"
    | "expired"
    | "closed_manual";
  legs: Leg[];
  thesis: string;
  verdict: Verdict | null;
}

export interface AgentCard {
  id: AgentId;
  name: string;
  role: string;
  ink: string;
  state: MascotState;
  task: string;
  last_output: string;
  model: string | null;
}

export interface Lesson {
  id: string;
  text: string;
  root_cause: string;
  failed_signal: string;
  missed_check: string;
  trade_coid: string;
  param_proposals: {
    param: string;
    current: number;
    proposed: number;
    status: "pending" | "applied" | "rejected";
    reason: string;
  }[];
  created_ts: string;
  applied_count: number;
  blocked_trades: string[];
}

export interface GateStat {
  gate: string;
  passed: number;
  rejected: number;
  last_verdict: string | null;
}

export interface AppliedParam {
  param: string;
  before: number;
  after: number;
  applied_at?: string;
  motivated_by: string;
}

export interface AskRequest {
  id: string;
  text: string;
  symbols: string[];
  intent: string | null;
  status: "queued" | "running" | "answered" | "rejected";
  created_ts: string;
  result_summary: string | null;
  decision_coid: string | null;
  cycle_id: string | null;
}

export interface Kpis {
  portfolio_value: number;
  today_pnl: number;
  total_pnl: number;
  risk_used_pct: number;
  open_risk_pct: number;
}

export interface EquityPoint {
  ts: string;
  equity: number;
}

export interface AccountView {
  account_number: string;
  paper: boolean;
  equity: number;
  cash: number;
  buying_power: number;
  day_pnl: number;
  total_pnl: number;
  baseline: number;
  options_level: number | null;
  as_of: string;
}

export interface DeskState {
  as_of: string;
  version: string;
  market: {
    open: boolean;
    phase: "pre" | "open" | "closed";
    next_open: string | null;
    next_close: string | null;
  };
  account: AccountView | null;
  kpis: Kpis;
  equity_curve: EquityPoint[];
  positions: PositionView[];
  agents: AgentCard[];
  cycles: Record<string, unknown>;
  halts: string[];
  ask_queue: AskRequest[];
  recent_events: JournalEvent[];
  lessons: Lesson[];
  gate_stats: GateStat[];
  param_history: AppliedParam[];
  config_snapshot: Record<string, unknown>;
  test_mode: boolean;
  paused: boolean;
}
