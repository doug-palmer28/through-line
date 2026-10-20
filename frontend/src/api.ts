// Thin client for the FastAPI backend. Vite proxies /api to port 8000 in development.

export type Health = {
  status: string;
  app: string;
  model: string;
  llm_key_configured: boolean;
  signup_code_required: boolean;
};

// ---------------------------------------------------------------- Studio types

export type StageKey = "inputs" | "activities" | "outputs" | "short_term_outcomes" | "long_term_outcomes";
export type LogicModelStage = { key: StageKey; label: string; hint: string };
export type AgentKey = "boss" | "sector_expert" | "client_advocate" | "evaluation_specialist" | "funder_researcher";
export type AgentCard = { key: AgentKey; name: string; role: string; model: string };
export type StudioOverview = {
  stages: LogicModelStage[];
  agent_team: AgentCard[];
  limits: { answer_words: number; feedback_words: number };
};

export type LogicModel = Record<StageKey, string[]> & {
  program_name: string;
  theory_of_change: string;
  assumptions: string[];
  external_factors: string[];
};

export type Scale = "agree_5" | "confidence_5" | "frequency_5" | "scale_0_10" | "yes_no" | "number" | "open_text";
export type Method = "participant_survey" | "staff_assessment" | "program_records";
export type Citation = {
  id: string;
  title: string;
  publisher: string;
  url: string | null;
  note: string;
  verified: boolean;
};
export type SurveyQuestion = {
  text: string;
  scale: Scale;
  included: boolean;
  note?: string | null;
  source_ids: string[];
};
export type Metric = {
  name: string;
  outcome: string;
  method: Method;
  questions: SurveyQuestion[];
  timing: string;
  how_scored: string;
  why_it_matters: string;
  funder_relevance: string;
  source_ids: string[];
};
export type CollectionTool = { name: string; method: Method; when: string; metrics: string[] };
export type MeasurementPlan = { summary: string; metrics: Metric[]; tools: CollectionTool[]; sources: Citation[] };

type DraftSource = "team" | "team_revision" | "client_edit";
export type AlignmentNote = { note: string; source_ids: string[] };
export type Draft = {
  version: number;
  source: DraftSource;
  logic_model: LogicModel;
  alignment?: AlignmentNote[];
  sources?: Citation[];
};
export type FunderPriority = {
  funder: string;
  funder_type: "government" | "philanthropic" | "both";
  what_they_want: string;
  source_ids: string[];
};
export type Research = {
  mode: "web" | "knowledge" | null;
  funder_priorities: FunderPriority[];
  compelling_metrics: string[];
  sources: Citation[];
};
export type PlanDraft = { version: number; source: DraftSource; plan: MeasurementPlan };
export type Question = { number: number; question: string; why: string | null; answer: string | null };
export type ChatLine = { role: "team" | "client"; text: string; at: string };
export type Phase =
  | "intake"
  | "interview"
  | "ready_to_draft"
  | "review"
  | "ready_for_metrics"
  | "metrics_review"
  | "complete";

/** A document or web page the AI read: sizes only, plus how much hidden text it skipped. */
export type SourceInfo = {
  label: string;
  kind: string;
  chars: number;
  truncated: boolean;
  hidden?: { reason: string; chars: number }[];
};

export type StudioSession = {
  session_id: string;
  org_name: string;
  phase: Phase;
  sources: SourceInfo[];
  sector: string | null;
  question_number: number | null;
  questions_total: number;
  answered: number;
  current_question: Question | null;
  transcript: ChatLine[];
  draft: Draft | null;
  revisions_left: number;
  approved: LogicModel | null;
  metric_draft: PlanDraft | null;
  metric_revisions_left: number;
  approved_plan: MeasurementPlan | null;
  upload_request: string | null;
  uploads_left: number;
  team_notes: string[];
  research: Research | null;
  usage: { requests: number; input_tokens: number; output_tokens: number };
  feed_seq: number;
};

export type FeedEvent = {
  seq: number;
  at: string;
  kind: "thinking" | "ask" | "reply" | "look" | "note" | "done" | "error";
  agent: AgentKey;
  to: AgentKey | null;
  text: string;
};

// ---------------------------------------------------------------- accounts

export type Me = {
  user: { display_name: string; role: "admin" | "staff" };
  org: { id: number; name: string };
  studio_session_id: string | null;
  has_plan: boolean;
};

// ---------------------------------------------------------------- survey tools

export type ToolQuestion = {
  id: string;
  text: string;
  scale: Scale;
  metric: string | null;
  source: "plan" | "staff";
  hidden: boolean;
  reverse: boolean;
  note: string;
  waves: ("pre" | "post")[];
};
export type SurveyFix = {
  action: "rewrite" | "change_scale" | "hide" | "set_waves" | "set_reverse" | "add_open_question";
  text?: string | null;
  scale?: Scale | null;
  waves?: ("pre" | "post")[] | null;
  reverse?: boolean | null;
};
export type SurveyIssue = {
  question_id: string | null;
  kind: string;
  severity: "high" | "medium" | "low";
  problem: string;
  suggestion: string;
  fix: SurveyFix | null;
};
export type InstrumentSummary = {
  id: number;
  name: string;
  method: "participant_survey" | "staff_assessment";
  when: string;
  status: "draft" | "published";
  questions: number;
  hidden: number;
  responses: { pre: number; post: number };
  reviewed: boolean;
  reviews_left: number;
};
export type InstrumentDetail = Omit<InstrumentSummary, "questions"> & {
  questions: ToolQuestion[];
  demographics: string[];
  review: { summary: string; ready: boolean; strengths: string[]; issues: SurveyIssue[]; reviewed_at: string; stale?: boolean } | null;
  checks: SurveyIssue[];
  locked: boolean;
};
export type ScaleInfo = { label: string; options: string[] | null };
export type DemoInfo = { label: string; options: string[]; multi: boolean };
export type CollectionMode = { key: string; name: string; description: string };
export type ToolsData = {
  collection_modes: CollectionMode[];
  has_plan: boolean;
  instruments: InstrumentSummary[];
  scales: Record<Scale, ScaleInfo>;
  demographics: Record<string, DemoInfo>;
};
export type ParticipantRow = { id: number; code: string; active: boolean; created_at: string; completed: string[] };
export type NewCredential = { code: string; pin: string };
export type IndicatorEntry = { id: number; period: string; value: number; note: string };
export type IndicatorRow = {
  id: number;
  name: string;
  unit: string;
  description: string;
  source: "plan" | "custom";
  entries: IndicatorEntry[];
};

// ---------------------------------------------------------------- dashboard

export type ChartSpec = {
  id: string;
  group?: "outcomes" | "people" | "program";
  metric?: string;
  counts?: number[];
  title: string;
  kind: "bar" | "line";
  unit: string;
  categories: string[];
  series: { name: string; values: (number | null)[] }[];
  note: string;
};
export type DashboardData = {
  org_name: string;
  headline: {
    participants: number;
    responses_pre: number;
    responses_post: number;
    matched: number;
    top_improvement: { metric: string; pct: number } | null;
  };
  charts: ChartSpec[];
  open_responses: { instrument: string; question: string; text: string; wave: string }[];
  min_group_size: number;
};

// ---------------------------------------------------------------- report designer

export type Brand = {
  standards?: string;
  primary?: string;
  secondary?: string;
  accent?: string;
  heading_font?: string;
  body_font?: string;
  tagline?: string;
  contact?: string;
};
export type DeckSlide = {
  layout: string;
  headline: string;
  body: string[];
  stats: { value: string; label: string }[];
  chart_id: string | null;
  quote: string | null;
  speaker_notes: string;
};
export type ReportRun = {
  id: number;
  created_at: string;
  request: { chart_ids: string[]; audience: string; minutes: number; include_quotes: boolean; notes: string };
  draft: {
    deck_title: string;
    deck_subtitle: string;
    slides: DeckSlide[];
    one_pager: { headline: string; subhead: string; stats: { value: string; label: string }[]; story: string;
      chart_ids: string[]; quote: string | null; call_to_action: string };
    design: { primary: string; secondary: string; accent: string; background: string; heading_font: string;
      body_font: string; mood: string };
  };
  privacy: PrivacyReport;
  numbers_as_of: string;
  live_numbers: string[];
  missing_numbers: string[];
  feedback: { at: string; text: string }[];
  revisions_left: number;
};
export type PrivacyReport = {
  clean: boolean;
  agent_clean: boolean;
  agent_summary: string;
  agent_findings: { where: string; text: string; issue: string; replacement: string }[];
  code_findings: { where: string; kind: string }[];
  unresolved?: string[];
  quotes_scrubbed_before_agent: number;
  checked_at?: string;
};
export type ReportOptions = {
  charts: { id: string; title: string; group: string; note: string }[];
  quotes_available: number;
  audiences: string[];
  fonts: string[];
  brand: Brand;
  has_logo: boolean;
  designs_left: number;
  runs: ReportRun[];
};

// ---------------------------------------------------------------- grants

export type FoundationProfile = {
  foundation: string;
  mission: string;
  priorities: { priority: string; evidence: string; source_ids: string[] }[];
  funding_areas: string[];
  typical_grant: string | null;
  language: string[];
  evaluation_expectations: string[];
  cautions: string[];
  sources: Citation[];
};
export type GrantAnswer = {
  question: string;
  word_limit: number | null;
  answer: string;
  priorities_addressed: string[];
  source_ids: string[];
  words: number;
  over_limit: boolean;
};
export type GrantApplication = {
  id: number;
  foundation: string;
  foundation_url: string;
  created_at: string;
  updated_at: string;
  request: { opportunity: string; questions: string; notes: string };
  sources: SourceInfo[];
  profile: FoundationProfile | null;
  research_mode: string;
  draft: {
    title: string;
    opportunity: string;
    fit_summary: string;
    answers: GrantAnswer[];
    checklist: { item: string; status: "ready" | "needs_input"; note: string }[];
    needs_input: string[];
  } | null;
  privacy: PrivacyReport | null;
  feedback: { at: string; text: string }[];
  revisions_left: number;
  numbers_as_of: string;
  missing_numbers: string[];
};
export type GrantList = {
  applications: { id: number; foundation: string; created_at: string; title: string; clean: boolean | null }[];
  left_this_month: number;
  per_month: number;
  revisions: number;
  has_plan: boolean;
};

// ---------------------------------------------------------------- usage

export type TokenTotals = { requests: number; input_tokens: number; output_tokens: number; total_tokens: number };
export type UsageReport = {
  me: TokenTotals & { by_feature: (TokenTotals & { key: string })[] };
  organization: TokenTotals & {
    by_feature: (TokenTotals & { key: string })[];
    by_month: (TokenTotals & { key: string })[];
    by_person?: (TokenTotals & { key: string })[];
  };
  allowances: { feature: string; used: number | null; limit: number | null; per: string; note?: string }[];
};

// ---------------------------------------------------------------- participant portal

export type PortalSurvey = { id: number; name: string; waves: { wave: "pre" | "post"; done: boolean }[] };
export type PortalForm = {
  name: string;
  wave: "pre" | "post";
  questions: { id: string; text: string; scale: Scale; options: string[] | null }[];
  demographics: ({ key: string } & DemoInfo)[];
};

// ---------------------------------------------------------------- requests

async function send<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = body?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail) && detail[0]?.msg
          ? String(detail[0].msg).replace(/^Value error, /, "")
          : `Request failed (${res.status})`;
    throw Object.assign(new Error(message), { status: res.status });
  }
  return res.json() as Promise<T>;
}

const getJson = <T,>(path: string) => send<T>(path);
const withJson = <T,>(method: string, path: string, body?: unknown) =>
  send<T>(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

const studio = (id: string) => `/api/logic-model/sessions/${encodeURIComponent(id)}`;

function upload(path: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  return send<StudioSession>(path, { method: "POST", body: form });
}

const tool = (id: number) => `/api/tools/instruments/${id}`;

export const api = {
  health: () => getJson<Health>("/api/health"),

  // accounts
  me: () => getJson<Me>("/api/auth/me"),
  signup: (body: { username: string; password: string; display_name: string; org_name?: string; invite_code?: string;
    access_code?: string }) =>
    withJson<Me>("POST", "/api/auth/signup", body),
  login: (username: string, password: string) => withJson<Me>("POST", "/api/auth/login", { username, password }),
  logout: () => withJson<{ ok: boolean }>("POST", "/api/auth/logout"),
  invite: () => withJson<{ invite_code: string; expires_in_days: number }>("POST", "/api/auth/invite"),

  // staff portal: survey tools
  tools: () => getJson<ToolsData>("/api/tools"),
  buildTools: () => withJson<ToolsData>("POST", "/api/tools/build"),
  instrument: (id: number) => getJson<InstrumentDetail>(tool(id)),
  saveInstrument: (id: number, body: { name: string; questions: ToolQuestion[]; demographics: string[] }) =>
    withJson<InstrumentDetail>("PUT", tool(id), body),
  publish: (id: number) => withJson<InstrumentDetail>("POST", `${tool(id)}/publish`),
  unpublish: (id: number) => withJson<InstrumentDetail>("POST", `${tool(id)}/unpublish`),
  reviewInstrument: (id: number) => withJson<InstrumentDetail>("POST", `${tool(id)}/review`),
  enterResponses: (id: number, wave: string, rows: { participant_code: string; answers: Record<string, unknown> }[]) =>
    withJson<{ saved: number; errors: { row: number; error: string }[] }>("POST", `${tool(id)}/responses`, { wave, rows }),
  participants: () => getJson<{ participants: ParticipantRow[] }>("/api/tools/participants"),
  addParticipants: (count: number) => withJson<{ created: NewCredential[] }>("POST", "/api/tools/participants", { count }),
  resetPin: (id: number) => withJson<NewCredential>("POST", `/api/tools/participants/${id}/reset-pin`),
  indicators: () => getJson<{ indicators: IndicatorRow[] }>("/api/tools/indicators"),
  addIndicator: (body: { name: string; unit: string; description: string }) =>
    withJson<{ indicators: IndicatorRow[] }>("POST", "/api/tools/indicators", body),
  addEntries: (id: number, entries: { period: string; value: number; note: string }[]) =>
    withJson<{ indicators: IndicatorRow[] }>("POST", `/api/tools/indicators/${id}/entries`, { entries }),
  deleteEntry: (id: number) => send<{ indicators: IndicatorRow[] }>(`/api/tools/indicator-entries/${id}`, { method: "DELETE" }),
  numbersTemplate: (month: string) => `/api/tools/indicators/template.xlsx?month=${encodeURIComponent(month)}`,
  uploadNumbers: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return send<{ saved: number; errors: { line: number; error: string }[]; months: string[]; indicators: IndicatorRow[] }>(
      "/api/tools/indicators/upload", { method: "POST", body: form });
  },

  // dashboard + downloads
  dashboard: () => getJson<DashboardData>("/api/dashboard"),
  chartXlsx: (id: string) => `/api/dashboard/charts/${encodeURIComponent(id)}.xlsx`,
  dataXlsx: "/api/dashboard/data.xlsx",
  reportPptx: "/api/dashboard/report.pptx",

  // report designer
  reportOptions: () => getJson<ReportOptions>("/api/reports"),
  saveBrand: (form: FormData) => send<ReportOptions>("/api/reports/brand", { method: "POST", body: form }),
  buildReport: (body: { chart_ids: string[]; audience: string; minutes: number; include_quotes: boolean; notes: string }) =>
    withJson<ReportRun>("POST", "/api/reports/build", body),
  logoUrl: "/api/reports/logo.png",
  deckUrl: (id: number) => `/api/reports/${id}/deck.pptx`,
  onePagerUrl: (id: number) => `/api/reports/${id}/one-pager.pdf`,
  reviseReport: (id: number, feedback: string) => withJson<ReportRun>("POST", `/api/reports/${id}/revise`, { feedback }),
  refreshReport: (id: number) => withJson<ReportRun>("POST", `/api/reports/${id}/refresh`),
  checkReportPrivacy: (id: number) => withJson<ReportRun>("POST", `/api/reports/${id}/privacy-check`),

  // grants
  grants: () => getJson<GrantList>("/api/grants"),
  grant: (id: number) => getJson<GrantApplication>(`/api/grants/${id}`),
  createGrant: (form: FormData) => send<GrantApplication>("/api/grants", { method: "POST", body: form }),
  reviseGrant: (id: number, feedback: string) => withJson<GrantApplication>("POST", `/api/grants/${id}/revise`, { feedback }),
  checkGrantPrivacy: (id: number) => withJson<GrantApplication>("POST", `/api/grants/${id}/privacy-check`),
  deleteGrant: (id: number) => send<GrantList>(`/api/grants/${id}`, { method: "DELETE" }),
  grantDocUrl: (id: number) => `/api/grants/${id}/application.docx`,

  // usage
  usage: () => getJson<UsageReport>("/api/usage"),

  // participant portal
  participantLogin: (code: string, pin: string) =>
    withJson<{ code: string; org_name: string }>("POST", "/api/auth/participant/login", { code, pin }),
  participantLogout: () => withJson<{ ok: boolean }>("POST", "/api/auth/participant/logout"),
  mySurveys: () => getJson<{ code: string; org_name: string; surveys: PortalSurvey[] }>("/api/participant/surveys"),
  surveyForm: (id: number, wave: string) => getJson<PortalForm>(`/api/participant/surveys/${id}/${wave}`),
  submitSurvey: (id: number, wave: string, answers: Record<string, unknown>, demographics: Record<string, unknown>) =>
    withJson<{ ok: boolean }>("POST", `/api/participant/surveys/${id}/${wave}`, { answers, demographics }),

  studio: () => getJson<StudioOverview>("/api/logic-model"),
  startSession: (form: FormData) => send<StudioSession>("/api/logic-model/sessions", { method: "POST", body: form }),
  intake: (id: string) => withJson<StudioSession>("POST", `${studio(id)}/intake`),
  getSession: (id: string) => getJson<StudioSession>(studio(id)),
  feed: (id: string, after: number) => getJson<{ events: FeedEvent[]; phase: Phase }>(`${studio(id)}/feed?after=${after}`),
  answer: (id: string, answer: string) => withJson<StudioSession>("POST", `${studio(id)}/answer`, { answer }),
  addDocument: (id: string, file: File) => upload(`${studio(id)}/documents`, file),
  skipUpload: (id: string) => withJson<StudioSession>("POST", `${studio(id)}/skip-upload`),

  draft: (id: string) => withJson<StudioSession>("POST", `${studio(id)}/draft`),
  feedback: (id: string, feedback: string) => withJson<StudioSession>("POST", `${studio(id)}/feedback`, { feedback }),
  saveLogicModel: (id: string, model: LogicModel) => withJson<StudioSession>("PUT", `${studio(id)}/logic-model`, model),
  approve: (id: string) => withJson<StudioSession>("POST", `${studio(id)}/approve`),

  draftMetrics: (id: string) => withJson<StudioSession>("POST", `${studio(id)}/metrics/draft`),
  metricsFeedback: (id: string, feedback: string) =>
    withJson<StudioSession>("POST", `${studio(id)}/metrics/feedback`, { feedback }),
  savePlan: (id: string, plan: MeasurementPlan) => withJson<StudioSession>("PUT", `${studio(id)}/metrics`, plan),
  approvePlan: (id: string) => withJson<StudioSession>("POST", `${studio(id)}/metrics/approve`),

  endSession: (id: string) => send<{ ended: boolean }>(studio(id), { method: "DELETE" }),
  exportUrl: (id: string) => `${studio(id)}/export.pptx`,
};
