// ─── NABOM Facade API Client ────────────────────────────────────────────────
// 프론트엔드가 사용하는 유일한 API 경로. 백엔드 snake_case 응답을
// 프론트엔드 camelCase 타입으로 변환한다.

import type {
  AdminUserSummary,
  BirthInput,
  CharacterProfile,
  DailyEntry,
  DeviceInfo,
  GrowthExperiment,
  JourneySummary,
  LegalDocument,
  OnboardingData,
  ProfileFeedback,
  ProfileVersion,
  Session,
  WeeklyMirror,
} from '@/types/nabom';
import { characterImagePath } from '@/lib/character-visual';

const BASE_URL = (
  process.env.NEXT_PUBLIC_NABOM_API ?? 'http://localhost:8080'
).replace(/\/+$/, '');
const TOKEN_KEY = 'nabom_session_token';
const SESSION_KEY = 'nabom_session';
const DEVICE_KEY = 'nabom_device_id';

export interface ApiErrorBody {
  code: string;
  message: string;
  retryable: boolean;
  request_id?: string;
}

export class ApiError extends Error {
  status: number;
  code: string;
  retryable: boolean;

  constructor(status: number, body: Partial<ApiErrorBody> | null) {
    const message =
      body?.message ??
      (status === 401
        ? '로그인이 필요해요. 다시 로그인해주세요.'
        : status === 502
          ? '분석 엔진을 잠시 사용할 수 없어요. 잠시 후 다시 시도해주세요.'
          : `요청에 실패했어요 (${status})`);
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = body?.code ?? `HTTP_${status}`;
    this.retryable = body?.retryable ?? status >= 500;
  }
}

// ─── Token helpers ──────────────────────────────────────────────────────────

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  clearSession();
}

export function persistSession(session: Session): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TOKEN_KEY, session.token);
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function loadStoredSession(): Session | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<Session>;
    if (!parsed.userId || !parsed.email || !parsed.token) return null;
    return {
      userId: parsed.userId,
      email: parsed.email,
      nickname: parsed.nickname ?? '',
      token: parsed.token,
    };
  } catch {
    return null;
  }
}

export function clearSession(): void {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(SESSION_KEY);
}

// ─── Device id (browser fingerprint) ────────────────────────────────────────

export function getDeviceId(): string {
  if (typeof window === 'undefined') return '';
  let device = window.localStorage.getItem(DEVICE_KEY);
  if (!device) {
    device = `dev-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    window.localStorage.setItem(DEVICE_KEY, device);
  }
  return device;
}

function deviceHeaders(): Record<string, string> {
  const device = getDeviceId();
  return device ? { 'X-Device-Id': device } : {};
}

// ─── Core request ───────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  init: { method?: string; body?: unknown; headers?: Record<string, string> } = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...deviceHeaders(),
    ...(init.headers ?? {}),
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: init.method ?? 'GET',
      headers,
      body: init.body === undefined ? undefined : JSON.stringify(init.body),
    });
  } catch {
    throw new ApiError(0, {
      code: 'NETWORK_UNAVAILABLE',
      message: '서버에 연결할 수 없어요. 잠시 후 다시 시도해주세요.',
      retryable: true,
    });
  }

  const text = await response.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail = (data as { detail?: ApiErrorBody })?.detail;
    throw new ApiError(response.status, detail ?? null);
  }
  return data as T;
}

// ─── Wire types (backend snake_case) ────────────────────────────────────────

interface WireTrait {
  trait: string;
  label_ko: string;
  value: number;
  confidence: number;
  source_counts: Record<string, number>;
}

interface WireLensBlock {
  title: string;
  body: string;
}

interface WireLenses {
  headline: string[];
  summary: {
    moving_force: WireLensBlock;
    adjust_point: WireLensBlock;
    today_action: WireLensBlock;
  };
  energy_style: WireLensBlock;
  element_style: WireLensBlock;
  season_rhythm: WireLensBlock;
  relation_style: WireLensBlock;
  root_support: WireLensBlock;
  pattern_balance: {
    verdict: string;
    good: WireLensBlock;
    over: WireLensBlock;
  };
  stability: {
    title: string;
    body: string;
    points: string[];
  };
  attention_points: string[];
}

interface WireCharacterProfile {
  character_profile_id: string;
  profile_version_id: string;
  day_stem: string;
  representative_element: string;
  guardian_beast: { code: string; label_ko: string; source: string };
  image_url?: string;
  image_gif_url?: string;
  visual_key?: string;
  catalog_key?: string;
  state_catalog_key?: string;
  stage?: number;
  stage_name?: string;
  condition_state?: 'rising' | 'steady' | 'strained' | 'recovering';
  condition_label?: string;
  user_editable: boolean;
  status: string;
}

interface WireProfile {
  profile_version_id: string;
  number: number;
  created_at: string;
  identity_sentence: string;
  traits: WireTrait[];
  strengths: string[];
  watch_patterns: string[];
  growth_theme: string;
  lenses?: WireLenses;
  evidence_cutoff: string;
  character_profile?: WireCharacterProfile;
  trait_candidates?: unknown[];
  narrative?: unknown;
}

interface WireEntry {
  entry_id: string;
  date: string;
  mood: number;
  energy: number;
  satisfaction: number;
  text: string;
  tags: string[];
  created_at: string;
}

interface WireExperiment {
  experiment_id: string;
  mirror_id: string | null;
  title: string;
  instruction: string;
  success_condition: string;
  reversible: boolean;
  status: 'accepted' | 'in_progress' | 'completed' | 'declined';
  user_result: string | null;
  created_at: string;
  updated_at: string;
}

interface WireMirror {
  mirror_id: string;
  period: { from: string; to: string };
  coverage: { days_recorded: number; mode: 'full' | 'partial' | 'light' };
  summary: string;
  metrics: {
    average_mood?: number | null;
    average_energy?: number | null;
    average_satisfaction?: number | null;
  };
  notable_moments: string[];
  emotion_flow: { date: string; mood: number; label: string }[];
  energy_gainers: string[];
  energy_drainers: string[];
  patterns: {
    trait: string;
    direction: string;
    title: string;
    description: string;
    evidence_count: number;
    confidence: number;
    status: string;
  }[];
  changes: string[];
  hypotheses: { title: string; description: string; confidence: number }[];
  growth_experiment: WireExperiment | null;
  growth_experiment_id: string | null;
  evidence_refs: string[];
  generated_at: string;
  prompt_version: string;
  status: string;
}

interface WireReflection {
  reflection_id: string;
  mode: string;
  resolver_version: string;
  resolver_input_hash?: string;
  situation: { code?: string; label_ko: string; confidence: number };
  observation_focus: string[];
  caution_signals: string[];
  recommended_action: {
    title: string;
    instruction: string;
    success_condition: string;
    reversible: boolean;
  };
  evidence_refs: string[];
  request_id?: string;
}

interface WireFeedback {
  feedback_id: string;
  profile_version_id: string;
  target_type: 'trait' | 'overall';
  target_key: string;
  rating: ProfileFeedback['rating'];
  comment: string;
  created_at: string;
}

interface WireDevice {
  device_id: string;
  label: string;
  first_seen: string;
  last_seen: string;
  status: string;
}

function adaptDevice(d: WireDevice): DeviceInfo {
  return {
    deviceId: d.device_id,
    label: d.label,
    firstSeen: d.first_seen,
    lastSeen: d.last_seen,
    status: d.status,
  };
}

interface WireJourney {
  profiles: WireProfile[];
  summary: {
    profile_count: number;
    recorded_days: number;
    first_profile_at: string | null;
    long_term_ready: boolean;
    note: string;
  };
}

// ─── Adapters ───────────────────────────────────────────────────────────────

function adaptTrait(t: WireTrait): ProfileVersion['traits'][number] {
  return {
    trait: t.trait,
    labelKo: t.label_ko,
    value: t.value,
    confidence: t.confidence,
    sourceCounts: t.source_counts ?? {},
  };
}

function adaptCharacter(c: WireCharacterProfile): CharacterProfile {
  return {
    characterProfileId: c.character_profile_id,
    profileVersionId: c.profile_version_id,
    dayStem: c.day_stem,
    representativeElement: c.representative_element,
    guardianBeast: {
      code: c.guardian_beast.code,
      labelKo: c.guardian_beast.label_ko,
      source: c.guardian_beast.source,
    },
    imageUrl: c.image_url || characterImagePath(c.visual_key || c.guardian_beast.code),
    imageGifUrl: c.image_gif_url,
    visualKey: c.visual_key,
    catalogKey: c.catalog_key,
    stateCatalogKey: c.state_catalog_key,
    stage: c.stage,
    stageName: c.stage_name,
    conditionState: c.condition_state,
    conditionLabel: c.condition_label,
    userEditable: c.user_editable,
    status: c.status,
  };
}

function adaptProfile(p: WireProfile): ProfileVersion {
  return {
    profileVersionId: p.profile_version_id,
    number: p.number,
    createdAt: p.created_at,
    identitySentence: p.identity_sentence,
    traits: (p.traits ?? []).map(adaptTrait),
    strengths: p.strengths ?? [],
    watchPatterns: p.watch_patterns ?? [],
    growthTheme: p.growth_theme ?? '',
    lenses: p.lenses
      ? {
          headline: p.lenses.headline ?? [],
          summary: p.lenses.summary
            ? {
                movingForce: p.lenses.summary.moving_force,
                adjustPoint: p.lenses.summary.adjust_point,
                todayAction: p.lenses.summary.today_action,
              }
            : undefined,
          energyStyle: p.lenses.energy_style,
          elementStyle: p.lenses.element_style,
          seasonRhythm: p.lenses.season_rhythm,
          relationStyle: p.lenses.relation_style,
          rootSupport: p.lenses.root_support,
          patternBalance: p.lenses.pattern_balance
            ? {
                verdict: p.lenses.pattern_balance.verdict,
                good: p.lenses.pattern_balance.good,
                over: p.lenses.pattern_balance.over,
              }
            : undefined,
          stability: p.lenses.stability
            ? {
                title: p.lenses.stability.title,
                body: p.lenses.stability.body,
                points: p.lenses.stability.points ?? [],
              }
            : undefined,
          attentionPoints: p.lenses.attention_points ?? [],
        }
      : undefined,
    evidenceCutoff: p.evidence_cutoff ?? '',
  };
}

function adaptEntry(e: WireEntry): DailyEntry {
  return {
    entryId: e.entry_id,
    date: e.date,
    mood: e.mood,
    energy: e.energy,
    satisfaction: e.satisfaction,
    text: e.text,
    tags: e.tags ?? [],
    createdAt: e.created_at,
  };
}

function adaptExperiment(e: WireExperiment): GrowthExperiment {
  return {
    experimentId: e.experiment_id,
    title: e.title,
    instruction: e.instruction,
    successCondition: e.success_condition,
    status: e.status,
    userResult: e.user_result,
  };
}

function adaptMirror(m: WireMirror): WeeklyMirror {
  return {
    mirrorId: m.mirror_id,
    period: { from: m.period.from, to: m.period.to },
    coverage: { daysRecorded: m.coverage.days_recorded, mode: m.coverage.mode },
    summary: m.summary,
    notableMoments: m.notable_moments ?? [],
    emotionFlow: (m.emotion_flow ?? []).map((ef) => ({
      date: ef.date,
      mood: ef.mood,
      label: ef.label,
    })),
    energyGainers: m.energy_gainers ?? [],
    energyDrainers: m.energy_drainers ?? [],
    patterns: (m.patterns ?? []).map((p) => ({
      title: p.title,
      description: p.description,
      evidenceCount: p.evidence_count,
      confidence: p.confidence,
    })),
    changesFromLastWeek: m.changes ?? [],
    hypotheses: (m.hypotheses ?? []).map((h) => ({
      title: h.title,
      description: h.description,
      confidence: h.confidence,
    })),
    growthExperiment: m.growth_experiment ? adaptExperiment(m.growth_experiment) : null,
    generatedAt: m.generated_at,
  };
}

function adaptReflection(r: WireReflection): import('@/types/nabom').CanonicalReflection {
  return {
    reflectionId: r.reflection_id,
    mode: r.mode,
    situation: {
      code: r.situation.code,
      labelKo: r.situation.label_ko ?? '',
      confidence: r.situation.confidence,
    },
    observationFocus: r.observation_focus ?? [],
    cautionSignals: r.caution_signals ?? [],
    recommendedAction: {
      title: r.recommended_action.title,
      instruction: r.recommended_action.instruction,
      successCondition: r.recommended_action.success_condition,
      reversible: r.recommended_action.reversible,
    },
  };
}

function adaptJourney(j: WireJourney): {
  profiles: ProfileVersion[];
  summary: JourneySummary;
} {
  return {
    profiles: (j.profiles ?? []).map(adaptProfile),
    summary: {
      profileCount: j.summary.profile_count,
      recordedDays: j.summary.recorded_days,
      firstProfileAt: j.summary.first_profile_at,
      longTermReady: j.summary.long_term_ready,
      note: j.summary.note,
    },
  };
}

// ─── Request builders (onboarding → wire birth_input) ───────────────────────

export function toBirthInputWire(birth: BirthInput): Record<string, unknown> {
  const time =
    birth.timePrecision === 'unknown'
      ? ''
      : birth.timeWindow === 'around_midnight'
        ? '23:00-01:00'
        : birth.time;
  return {
    calendar: birth.calendar,
    date: birth.date,
    time,
    time_precision: birth.timePrecision,
    time_window: birth.timeWindow || null,
    is_lunar_leap_month:
      birth.calendar === 'lunar' ? (birth.isLunarLeapMonth ?? null) : null,
    location: {
      label: birth.location.label || null,
      timezone: birth.location.timezone || 'Asia/Seoul',
      lat: birth.location.lat || null,
      lon: birth.location.lon || null,
    },
    gender: birth.gender || 'unknown',
  };
}

// ─── API surface ────────────────────────────────────────────────────────────

export const api = {
  // Auth
  async signup(email: string, password: string, nickname: string): Promise<Session> {
    const res = await request<{
      user_id: string;
      email: string;
      nickname: string;
      token: string;
    }>('/api/v1/auth/signup', {
      method: 'POST',
      body: { email, password, nickname },
    });
    const session = { userId: res.user_id, email: res.email, nickname: res.nickname, token: res.token };
    persistSession(session);
    return session;
  },

  async login(email: string, password: string): Promise<Session> {
    const res = await request<{
      user_id: string;
      email: string;
      nickname: string;
      token: string;
    }>('/api/v1/auth/login', { method: 'POST', body: { email, password } });
    const session = { userId: res.user_id, email: res.email, nickname: res.nickname, token: res.token };
    persistSession(session);
    return session;
  },

  async startGoogle(): Promise<{ authorizationUrl: string }> {
    const device = getDeviceId();
    const qs = device ? `?device_id=${encodeURIComponent(device)}` : '';
    const res = await request<{ authorization_url: string }>(`/api/v1/auth/google/start${qs}`);
    return { authorizationUrl: res.authorization_url };
  },

  async loginWithGoogleToken(idToken: string): Promise<Session> {
    const res = await request<{
      user_id: string;
      email: string;
      nickname: string;
      token: string;
    }>('/api/v1/auth/google', { method: 'POST', body: { id_token: idToken } });
    const session = { userId: res.user_id, email: res.email, nickname: res.nickname, token: res.token };
    persistSession(session);
    return session;
  },

  adoptToken(token: string): void {
    setToken(token);
  },

  async me(): Promise<Session> {
    const token = getToken();
    if (!token) {
      throw new ApiError(401, {
        code: 'AUTHENTICATION_REQUIRED',
        message: '로그인이 필요해요.',
        retryable: false,
      });
    }
    const res = await request<{ user_id: string; email: string; nickname: string }>('/api/v1/auth/me');
    const session = { userId: res.user_id, email: res.email, nickname: res.nickname, token };
    persistSession(session);
    return session;
  },

  async legal(kind: 'privacy' | 'terms'): Promise<LegalDocument> {
    const res = await request<{
      document: 'privacy' | 'terms';
      version: string;
      title: string;
      updated_at: string;
      sections: { heading: string; body: string }[];
    }>(`/api/v1/legal/${kind}`);
    return {
      document: res.document,
      version: res.version,
      title: res.title,
      updatedAt: res.updated_at,
      sections: res.sections,
    };
  },

  async adminUsers(): Promise<AdminUserSummary[]> {
    const res = await request<{
      users: Array<{
        user_id: string;
        email: string;
        nickname: string;
        status: string;
        created_at?: string;
        profile_status: string;
        profile_number?: number;
        entry_count: number;
        journal_count: number;
        recorded_days: number;
        weekly_status: string;
        experiment_count: number;
      }>;
    }>('/api/v1/admin/users');
    return res.users.map((user) => ({
      userId: user.user_id,
      email: user.email,
      nickname: user.nickname,
      status: user.status,
      createdAt: user.created_at,
      profileStatus: user.profile_status,
      profileNumber: user.profile_number,
      entryCount: user.entry_count,
      journalCount: user.journal_count,
      recordedDays: user.recorded_days,
      weeklyStatus: user.weekly_status,
      experimentCount: user.experiment_count,
    }));
  },

  // Profile
  async createProfile(data: OnboardingData): Promise<{ profile: ProfileVersion; characterProfile: CharacterProfile }> {
    const res = await request<{ profile: WireProfile }>('/api/v1/living/profiles/initial', {
      method: 'POST',
      body: {
        birth_input: toBirthInputWire(data.birth),
        current_priorities: data.priorities,
        change_goal: data.changeDesire,
        current_goal: data.currentGoal,
      },
    });
    const profile = adaptProfile(res.profile);
    const character = res.profile.character_profile ? adaptCharacter(res.profile.character_profile) : null;
    return {
      profile,
      characterProfile:
        character ??
        ({
          characterProfileId: '',
          profileVersionId: profile.profileVersionId,
          dayStem: '차분하고 돌보는',
          representativeElement: 'earth',
          guardianBeast: { code: 'steadier', labelKo: '자리를 지키는 사람', source: 'day_stem_element' },
          imageUrl: characterImagePath('steadier'),
          userEditable: true,
          status: 'active',
        } satisfies CharacterProfile),
    };
  },

  async getCurrentProfile(): Promise<{ profile: ProfileVersion; characterProfile: CharacterProfile }> {
    const res = await request<{ profile: WireProfile; character_profile: WireCharacterProfile }>(
      '/api/v1/living/profiles/current',
    );
    return {
      profile: adaptProfile(res.profile),
      characterProfile: adaptCharacter(res.character_profile),
    };
  },

  async postProfileFeedback(
    profileVersionId: string,
    fb: Omit<ProfileFeedback, 'feedbackId' | 'createdAt'>,
  ): Promise<ProfileFeedback> {
    const res = await request<{ feedback: WireFeedback }>(
      `/api/v1/living/profiles/${profileVersionId}/feedback`,
      {
        method: 'POST',
        body: {
          target_type: fb.targetType,
          target_key: fb.targetKey,
          rating: fb.rating,
          comment: fb.comment,
        },
      },
    );
    return {
      feedbackId: res.feedback.feedback_id,
      profileVersionId: res.feedback.profile_version_id,
      targetType: res.feedback.target_type,
      targetKey: res.feedback.target_key,
      rating: res.feedback.rating,
      comment: res.feedback.comment,
      createdAt: res.feedback.created_at,
    };
  },

  // Daily entries + evidence
  async listEntries(): Promise<DailyEntry[]> {
    const res = await request<{ entries: WireEntry[] }>('/api/v1/living/entries');
    return (res.entries ?? []).map(adaptEntry);
  },

  async upsertEntry(entry: {
    date: string;
    mood: number;
    energy: number;
    satisfaction: number;
    text: string;
    tags: string[];
  }): Promise<DailyEntry> {
    const res = await request<WireEntry>('/api/v1/living/entries', {
      method: 'POST',
      body: { ...entry, timezone: 'Asia/Seoul' },
    });
    return adaptEntry(res);
  },

  async createEvidence(sourceRecordId: string): Promise<void> {
    await request('/api/v1/living/evidence', {
      method: 'POST',
      body: { source_type: 'daily', source_record_id: sourceRecordId, timezone: 'Asia/Seoul' },
    });
  },

  // Mirrors / reflections
  async listMirrors(): Promise<WeeklyMirror[]> {
    const res = await request<{ mirrors: WireMirror[] }>('/api/v1/living/mirrors');
    return (res.mirrors ?? []).map(adaptMirror);
  },

  // Devices
  async listDevices(): Promise<{ devices: DeviceInfo[]; limit: number }> {
    const res = await request<{ devices: WireDevice[]; limit: number }>('/api/v1/auth/devices');
    return { devices: (res.devices ?? []).map(adaptDevice), limit: res.limit ?? 5 };
  },

  async revokeDevice(deviceId: string): Promise<void> {
    await request(`/api/v1/auth/devices/${encodeURIComponent(deviceId)}`, { method: 'DELETE' });
  },

  async createReflection(
    periodFrom: string,
    periodTo: string,
  ): Promise<{ mirror: WeeklyMirror; reflection: import('@/types/nabom').CanonicalReflection }> {
    const res = await request<{ mirror: WireMirror; reflection: WireReflection }>(
      '/api/v1/living/reflections',
      { method: 'POST', body: { period_from: periodFrom, period_to: periodTo, timezone: 'Asia/Seoul' } },
    );
    return { mirror: adaptMirror(res.mirror), reflection: adaptReflection(res.reflection) };
  },

  async getLatestReflection(): Promise<{
    mirror: WeeklyMirror | null;
    reflection: import('@/types/nabom').CanonicalReflection;
  }> {
    const res = await request<{ mirror: WireMirror | null; reflection: WireReflection }>(
      '/api/v1/living/reflections/latest',
    );
    return {
      mirror: res.mirror ? adaptMirror(res.mirror) : null,
      reflection: adaptReflection(res.reflection),
    };
  },

  // Experiments
  async listExperiments(): Promise<GrowthExperiment[]> {
    const res = await request<{ experiments: WireExperiment[] }>('/api/v1/living/experiments');
    return (res.experiments ?? []).map(adaptExperiment);
  },

  async updateExperiment(
    experimentId: string,
    patch: { status: GrowthExperiment['status']; userResult?: string | null },
  ): Promise<GrowthExperiment> {
    const res = await request<WireExperiment>(`/api/v1/living/experiments/${experimentId}`, {
      method: 'POST',
      body: { status: patch.status, user_result: patch.userResult ?? null },
    });
    return adaptExperiment(res);
  },

  // Journey
  async getJourney(): Promise<{ profiles: ProfileVersion[]; summary: JourneySummary }> {
    const res = await request<WireJourney>('/api/v1/living/journey');
    return adaptJourney(res);
  },

  // Privacy
  async exportData(): Promise<unknown> {
    return request('/api/v1/privacy/export');
  },

  async deleteRecords(): Promise<void> {
    await request('/api/v1/living/records', { method: 'DELETE' });
  },

  async deleteAccount(): Promise<void> {
    await request('/api/v1/account', { method: 'DELETE' });
    clearToken();
  },
};
