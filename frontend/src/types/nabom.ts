// ─── NABOM Type Definitions ───────────────────────────────────────────────────

export type AppView =
  | 'landing'
  | 'auth'
  | 'welcome'
  | 'today'
  | 'profile'
  | 'mirror'
  | 'journey'
  | 'settings'
  | 'legal'
  | 'admin';

export type CalendarType = 'solar' | 'lunar';
export type TimePrecision = 'exact' | 'approximate' | 'unknown';
export type TimeWindow = 'morning' | 'afternoon' | 'evening' | 'night' | 'around_midnight';
export type BirthGender = 'male' | 'female' | 'unknown';

export interface BirthInput {
  calendar: CalendarType;
  date: string; // YYYY-MM-DD
  time: string; // HH:MM, HH:MM-HH:MM, or ''
  timePrecision: TimePrecision;
  timeWindow?: TimeWindow | '';
  isLunarLeapMonth?: boolean | null;
  location: {
    label: string;
    lat: number;
    lon: number;
    timezone: string;
  };
  gender: BirthGender;
}

export interface OnboardingData {
  nickname: string;
  birth: BirthInput;
  priorities: string[];
  changeDesire: string;
  currentGoal: string;
}

export interface TraitState {
  trait: string;
  labelKo: string;
  value: number;
  confidence: number;
  sourceCounts: {
    birth_hypothesis?: number;
    self_report?: number;
    journal?: number;
    profile_feedback?: number;
  };
}

export interface CharacterProfile {
  characterProfileId: string;
  profileVersionId: string;
  dayStem: string;
  representativeElement: string;
  guardianBeast: {
    code: string;
    labelKo: string;
    source: string;
  };
  imageUrl?: string;
  imageGifUrl?: string;
  visualKey?: string;
  catalogKey?: string;
  stateCatalogKey?: string;
  stage?: number;
  stageName?: string;
  conditionState?: 'rising' | 'steady' | 'strained' | 'recovering';
  conditionLabel?: string;
  userEditable: boolean;
  status: string;
}

export interface ProfileLensBlock {
  title: string;
  body: string;
}

export interface ProfileLensSummary {
  movingForce: ProfileLensBlock;
  adjustPoint: ProfileLensBlock;
  todayAction: ProfileLensBlock;
}

export interface ProfileLensPatternBalance {
  verdict: string;
  good: ProfileLensBlock;
  over: ProfileLensBlock;
}

export interface ProfileLensStability {
  title: string;
  body: string;
  points: string[];
}

export interface ProfileLenses {
  headline: string[];
  summary?: ProfileLensSummary;
  energyStyle?: ProfileLensBlock;
  elementStyle?: ProfileLensBlock;
  seasonRhythm?: ProfileLensBlock;
  relationStyle?: ProfileLensBlock;
  rootSupport?: ProfileLensBlock;
  patternBalance?: ProfileLensPatternBalance;
  stability?: ProfileLensStability;
  attentionPoints: string[];
}

export interface ProfileVersion {
  profileVersionId: string;
  number: number;
  createdAt: string;
  identitySentence: string;
  traits: TraitState[];
  strengths: string[];
  watchPatterns: string[];
  growthTheme: string;
  lenses?: ProfileLenses;
  evidenceCutoff: string;
}

export interface DailyEntry {
  entryId: string;
  date: string;
  mood: number;
  energy: number;
  satisfaction: number;
  text: string;
  tags: string[];
  focus?: string;
  concentration?: number;
  relationship?: string;
  createdAt: string;
}

export interface Evidence {
  evidenceId: string;
  type: string;
  occurredAt: string;
  sourceRecordId: string;
  signals: {
    trait: string;
    direction: 'positive' | 'negative' | 'neutral';
    strength: number;
  }[];
  summary: string;
  status: string;
}

export interface GrowthExperiment {
  experimentId: string;
  title: string;
  instruction: string;
  successCondition: string;
  status: 'accepted' | 'in_progress' | 'completed' | 'declined';
  userResult: string | null;
}

export interface WeeklyMirror {
  mirrorId: string;
  period: { from: string; to: string };
  coverage: {
    daysRecorded: number;
    mode: 'full' | 'partial' | 'light';
  };
  summary: string;
  notableMoments: string[];
  emotionFlow: { date: string; mood: number; label: string }[];
  energyGainers: string[];
  energyDrainers: string[];
  patterns: {
    title: string;
    description: string;
    evidenceCount: number;
    confidence: number;
  }[];
  changesFromLastWeek: string[];
  hypotheses: {
    title: string;
    description: string;
    confidence: number;
  }[];
  growthExperiment: GrowthExperiment | null;
  generatedAt: string;
}

export interface CanonicalReflection {
  reflectionId: string;
  mode: string;
  situation: {
    code?: string;
    labelKo: string;
    confidence: number;
  };
  observationFocus: string[];
  cautionSignals: string[];
  recommendedAction: {
    title: string;
    instruction: string;
    successCondition: string;
    reversible: boolean;
  };
}

export interface ProfileFeedback {
  feedbackId: string;
  profileVersionId: string;
  targetType: 'trait' | 'overall';
  targetKey: string;
  rating: 'correct' | 'mostly_correct' | 'situational' | 'unsure' | 'incorrect';
  comment: string;
  createdAt: string;
}

export type ReflectionIntensity = 'reflect' | 'grow' | 'challenge';

export interface Session {
  userId: string;
  email: string;
  nickname: string;
  token: string;
}

export interface DeviceInfo {
  deviceId: string;
  label: string;
  firstSeen: string;
  lastSeen: string;
  status: string;
}

export interface LegalDocument {
  document: 'privacy' | 'terms';
  version: string;
  title: string;
  updatedAt: string;
  sections: { heading: string; body: string }[];
}

export interface AdminUserSummary {
  userId: string;
  email: string;
  nickname: string;
  status: string;
  createdAt?: string;
  profileStatus: string;
  profileNumber?: number;
  entryCount: number;
  journalCount: number;
  recordedDays: number;
  weeklyStatus: string;
  experimentCount: number;
}

export interface JourneySummary {
  profileCount: number;
  recordedDays: number;
  firstProfileAt: string | null;
  longTermReady: boolean;
  note: string;
}

// ─── Trait Labels ─────────────────────────────────────────────────────────────

export const TRAIT_LABELS: Record<string, string> = {
  exploration: '호기심',
  execution: '추진력',
  persistence: '꾸준함',
  connection: '친밀함',
  recovery: '회복력',
  structure: '안정감',
  expression: '명랑함',
};

export const PRIORITY_OPTIONS = [
  { value: 'career', label: '커리어 · 일' },
  { value: 'relationship', label: '관계' },
  { value: 'health', label: '건강 · 체력' },
  { value: 'finance', label: '경제 · 자산' },
  { value: 'growth', label: '성장 · 학습' },
  { value: 'creativity', label: '창작 · 취미' },
  { value: 'identity', label: '자기이해 · 정체성' },
  { value: 'rest', label: '휴식 · 여유' },
];

export const MOOD_LABELS: Record<number, string> = {
  1: '매우 나쁨',
  2: '나쁨',
  3: '보통',
  4: '좋음',
  5: '매우 좋음',
};

export const MOOD_EMOJI: Record<number, string> = {
  1: '😢',
  2: '😔',
  3: '😐',
  4: '😊',
  5: '😄',
};

export const ENERGY_LABELS: Record<number, string> = {
  1: '전혀 없음',
  2: '조금 부족',
  3: '보통',
  4: '충분',
  5: '넘침',
};

export const SATISFACTION_LABELS: Record<number, string> = {
  1: '매우 불만족',
  2: '불만족',
  3: '보통',
  4: '만족',
  5: '매우 만족',
};

export const CONFIDENCE_LABEL = (c: number): string => {
  if (c < 0.30) return '이런 가능성이 조금 보여요.';
  if (c < 0.50) return '';
  if (c < 0.70) return '최근 기록에서는 이런 경향이 몇 차례 보였어요.';
  if (c < 0.85) return '';
  return '지난 몇 주 동안 이 패턴이 반복해서 나타났어요.';
};

export const GUARDIAN_BEAST_LABELS: Record<string, string> = {
  pathfinder: '길을 여는 사람',
  brightener: '분위기를 밝히는 사람',
  steadier: '자리를 지키는 사람',
  decider: '기준을 세우는 사람',
  observer: '흐름을 읽는 사람',
};

export const ELEMENT_LABELS: Record<string, string> = {
  wood: '호기심',
  fire: '명랑함',
  earth: '안정감',
  metal: '추진력',
  water: '차분함',
};
