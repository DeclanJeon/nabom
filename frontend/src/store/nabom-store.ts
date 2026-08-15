import { create } from 'zustand';
import { api, clearToken, getToken, loadStoredSession } from '@/lib/api';
import type {
  AppView,
  OnboardingData,
  ProfileVersion,
  CharacterProfile,
  DailyEntry,
  WeeklyMirror,
  CanonicalReflection,
  GrowthExperiment,
  ProfileFeedback,
  ReflectionIntensity,
  JourneySummary,
  Session,
  DeviceInfo,
} from '@/types/nabom';

export type LoadStatus = 'idle' | 'loading' | 'ready' | 'error';

interface NabomState {
  // Navigation
  currentView: AppView;
  previousView: AppView | null;
  isOnboarded: boolean;
  setView: (view: AppView) => void;
  goBack: () => void;
  legalKind: 'privacy' | 'terms';
  openLegal: (kind: 'privacy' | 'terms') => void;

  // Auth
  session: Session | null;
  authStatus: LoadStatus;
  authError: string | null;
  signup: (email: string, password: string, nickname: string) => Promise<boolean>;
  login: (email: string, password: string) => Promise<boolean>;
  loginWithGoogle: () => Promise<boolean>;
  completeOAuthToken: (token: string) => Promise<boolean>;
  logout: () => void;

  // Hydration
  hydrationStatus: LoadStatus;
  hydrate: (opts?: { route?: boolean }) => Promise<void>;

  // Onboarding
  onboardingStep: number;
  onboardingData: OnboardingData;
  setOnboardingStep: (step: number) => void;
  updateOnboardingData: (data: Partial<OnboardingData>) => void;

  // Profile
  currentProfile: ProfileVersion | null;
  characterProfile: CharacterProfile | null;
  profileVersions: ProfileVersion[];
  journeySummary: JourneySummary | null;
  profileCreating: boolean;
  profileCreateError: string | null;
  createProfileFromOnboarding: () => Promise<boolean>;

  // Daily
  dailyEntries: DailyEntry[];
  entriesStatus: LoadStatus;
  entrySubmitting: boolean;
  addDailyEntryViaApi: (entry: Omit<DailyEntry, 'entryId' | 'createdAt'>) => Promise<boolean>;

  // Mirror
  weeklyMirrors: WeeklyMirror[];
  currentReflection: CanonicalReflection | null;
  mirrorStatus: LoadStatus;
  reflectionGenerating: boolean;
  reflectionError: string | null;
  generateReflection: () => Promise<boolean>;

  // Experiments
  experiments: GrowthExperiment[];
  updateExperimentViaApi: (id: string, patch: { status: GrowthExperiment['status']; userResult?: string | null }) => Promise<boolean>;

  // Feedback
  feedbackHistory: ProfileFeedback[];
  feedbackSubmitting: boolean;
  submitFeedbackViaApi: (fb: Omit<ProfileFeedback, 'feedbackId' | 'createdAt'>) => Promise<boolean>;

  // Devices
  devices: DeviceInfo[];
  devicesLimit: number;
  loadDevices: () => Promise<void>;
  revokeDevice: (deviceId: string) => Promise<boolean>;

  // Settings
  reflectionIntensity: ReflectionIntensity;
  setReflectionIntensity: (intensity: ReflectionIntensity) => void;
  settingsBusy: boolean;
  exportData: () => Promise<boolean>;
  deleteAccountViaApi: () => Promise<boolean>;
  deleteRecordsViaApi: () => Promise<boolean>;

  // Devices (기기 등록: 계정당 최대 5대)
  devices: DeviceInfo[];
  devicesLimit: number;
  loadDevices: () => Promise<void>;
  revokeDevice: (deviceId: string) => Promise<boolean>;
}

function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message;
  return '알 수 없는 오류가 발생했어요. 잠시 후 다시 시도해주세요.';
}

export const useNabomStore = create<NabomState>((set, get) => ({
  // Navigation
  currentView: 'landing',
  previousView: null,
  isOnboarded: false,
  legalKind: 'privacy' as const,
  openLegal: (kind) => set({ previousView: get().currentView, currentView: 'legal', legalKind: kind }),
  setView: (view) => set({ previousView: get().currentView, currentView: view }),
  goBack: () => {
    const prev = get().previousView;
    if (prev) set({ currentView: prev, previousView: null });
  },

  // Auth
  session: null,
  authStatus: 'idle',
  authError: null,
  signup: async (email, password, nickname) => {
    set({ authStatus: 'loading', authError: null });
    try {
      const session = await api.signup(email, password, nickname);
      set({ session, authStatus: 'ready' });
      await get().hydrate({ route: false });
      set({ currentView: get().isOnboarded ? 'today' : 'welcome' });
      return true;
    } catch (error) {
      set({ authStatus: 'error', authError: errorMessage(error) });
      return false;
    }
  },
  login: async (email, password) => {
    set({ authStatus: 'loading', authError: null });
    try {
      const session = await api.login(email, password);
      set({ session, authStatus: 'ready' });
      await get().hydrate({ route: false });
      set({ currentView: get().isOnboarded ? 'today' : 'welcome' });
      return true;
    } catch (error) {
      set({ authStatus: 'error', authError: errorMessage(error) });
      return false;
    }
  },
  loginWithGoogle: async () => {
    set({ authStatus: 'loading', authError: null });
    try {
      const started = await api.startGoogle();
      window.location.assign(started.authorizationUrl);
      return true;
    } catch (error) {
      set({ authStatus: 'error', authError: errorMessage(error) });
      return false;
    }
  },
  completeOAuthToken: async (token) => {
    set({ authStatus: 'loading', authError: null });
    try {
      api.adoptToken(token);
      const session = await api.me();
      set({ session, authStatus: 'ready' });
      await get().hydrate({ route: false });
      set({ currentView: get().isOnboarded ? 'today' : 'welcome' });
      return true;
    } catch (error) {
      clearToken();
      set({ authStatus: 'error', authError: errorMessage(error), session: null });
      return false;
    }
  },
  logout: () => {
    clearToken();
    set({
      session: null,
      currentProfile: null,
      characterProfile: null,
      profileVersions: [],
      journeySummary: null,
      dailyEntries: [],
      weeklyMirrors: [],
      currentReflection: null,
      experiments: [],
      feedbackHistory: [],
      isOnboarded: false,
      currentView: 'landing',
    });
  },

  // Hydration: 세션이 있으면 서버에서 모든 Living 데이터를 불러온다.
  hydrationStatus: 'idle',
  hydrate: async (opts?: { route?: boolean }) => {
    if (!getToken()) {
      set({ hydrationStatus: 'ready', session: null });
      return;
    }
    if (get().hydrationStatus === 'loading') return;
    set({ hydrationStatus: 'loading' });
    try {
      const session = await api.me();
      const [current, journey, entries, mirrors, experiments] = await Promise.all([
        api.getCurrentProfile().catch(() => null),
        api.getJourney().catch(() => null),
        api.listEntries().catch(() => [] as DailyEntry[]),
        api.listMirrors().catch(() => [] as WeeklyMirror[]),
        api.listExperiments().catch(() => [] as GrowthExperiment[]),
      ]);
      let reflection: CanonicalReflection | null = null;
      try {
        const latest = await api.getLatestReflection();
        reflection = latest.reflection;
        if (latest.mirror && !mirrors.some((item) => item.mirrorId === latest.mirror!.mirrorId)) {
          mirrors.push(latest.mirror);
        }
      } catch {
        reflection = null;
      }
      const currentProfile = current?.profile ?? (get().currentProfile ?? null);
      const nextView = currentProfile ? 'today' : 'welcome';
      set({
        session,
        currentProfile,
        characterProfile: current?.characterProfile ?? (get().characterProfile ?? null),
        profileVersions: journey?.profiles && journey.profiles.length > 0 ? journey.profiles : get().profileVersions,
        journeySummary: journey?.summary ?? get().journeySummary,
        dailyEntries: entries,
        weeklyMirrors: mirrors,
        currentReflection: reflection,
        experiments,
        isOnboarded: currentProfile !== null || get().isOnboarded,
        hydrationStatus: 'ready',
        ...(opts?.route === false ? {} : { currentView: nextView }),
      });
    } catch {
      clearToken();
      set({
        session: null,
        isOnboarded: false,
        hydrationStatus: 'ready',
        ...(opts?.route === false ? {} : { currentView: 'landing' }),
      });
    }
  },

  // Onboarding
  onboardingStep: 1,
  onboardingData: {
    nickname: '',
    birth: {
      calendar: 'solar',
      date: '',
      time: '',
      timePrecision: 'unknown',
      timeWindow: '',
      isLunarLeapMonth: null,
      location: { label: '', lat: 0, lon: 0, timezone: 'Asia/Seoul' },
      gender: 'unknown',
    },
    priorities: [],
    changeDesire: '',
    currentGoal: '',
  },
  setOnboardingStep: (step) => set({ onboardingStep: step }),
  updateOnboardingData: (data) =>
    set((s) => ({
      onboardingData: {
        ...s.onboardingData,
        ...data,
        birth: data.birth
          ? { ...s.onboardingData.birth, ...data.birth }
          : s.onboardingData.birth,
      },
    })),

  // Profile
  currentProfile: null,
  characterProfile: null,
  profileVersions: [],
  journeySummary: null,
  profileCreating: false,
  profileCreateError: null,
  createProfileFromOnboarding: async () => {
    set({ profileCreating: true, profileCreateError: null });
    try {
      const { profile, characterProfile } = await api.createProfile(get().onboardingData);
      set({
        currentProfile: profile,
        characterProfile,
        profileVersions: [profile],
        isOnboarded: true,
        hydrationStatus: 'ready',
        currentView: 'profile',
      });
      return true;
    } catch (error) {
      set({ profileCreateError: errorMessage(error) });
      return false;
    } finally {
      set({ profileCreating: false });
    }
  },

  // Devices
  devices: [],
  devicesLimit: 5,
  loadDevices: async () => {
    try {
      const { devices, limit } = await api.listDevices();
      set({ devices, devicesLimit: limit });
    } catch {
      // 비로그인 등에서는 조용히 무시
    }
  },
  revokeDevice: async (deviceId: string) => {
    try {
      await api.revokeDevice(deviceId);
      set((s) => ({ devices: s.devices.filter((d) => d.deviceId !== deviceId) }));
      return true;
    } catch {
      return false;
    }
  },

  // Daily
  dailyEntries: [],
  entriesStatus: 'idle',
  entrySubmitting: false,
  addDailyEntryViaApi: async (entry) => {
    set({ entrySubmitting: true });
    try {
      const saved = await api.upsertEntry(entry);
      set((s) => ({
        dailyEntries: [...s.dailyEntries.filter((e) => e.date !== saved.date), saved].sort((a, b) =>
          a.date.localeCompare(b.date),
        ),
        entriesStatus: 'ready',
      }));
      await api.createEvidence(saved.entryId).catch(() => undefined);
      return true;
    } catch (error) {
      set({ entriesStatus: 'error' });
      return false;
    } finally {
      set({ entrySubmitting: false });
    }
  },

  // Mirror
  weeklyMirrors: [],
  currentReflection: null,
  mirrorStatus: 'idle',
  reflectionGenerating: false,
  reflectionError: null,
  generateReflection: async () => {
    set({ reflectionGenerating: true, reflectionError: null });
    try {
      const today = new Date();
      const periodTo = today.toISOString().slice(0, 10);
      const from = new Date(today);
      from.setDate(from.getDate() - 6);
      const periodFrom = from.toISOString().slice(0, 10);
      const { mirror, reflection } = await api.createReflection(periodFrom, periodTo);
      const experiments = await api.listExperiments().catch(() => get().experiments);
      set((s) => ({
        weeklyMirrors: [...s.weeklyMirrors.filter((m) => m.mirrorId !== mirror.mirrorId), mirror],
        currentReflection: reflection,
        experiments,
        mirrorStatus: 'ready',
      }));
      return true;
    } catch (error) {
      set({ reflectionError: errorMessage(error), mirrorStatus: 'error' });
      return false;
    } finally {
      set({ reflectionGenerating: false });
    }
  },

  // Experiments
  experiments: [],
  updateExperimentViaApi: async (id, patch) => {
    try {
      const updated = await api.updateExperiment(id, patch);
      set((s) => ({
        experiments: s.experiments.map((e) => (e.experimentId === id ? updated : e)),
      }));
      return true;
    } catch {
      return false;
    }
  },

  // Feedback
  feedbackHistory: [],
  feedbackSubmitting: false,
  submitFeedbackViaApi: async (fb) => {
    set({ feedbackSubmitting: true });
    try {
      const currentProfile = get().currentProfile;
      if (!currentProfile) return false;
      const saved = await api.postProfileFeedback(currentProfile.profileVersionId, fb);
      set((s) => ({ feedbackHistory: [...s.feedbackHistory, saved] }));
      return true;
    } catch {
      return false;
    } finally {
      set({ feedbackSubmitting: false });
    }
  },

  // Settings
  reflectionIntensity: 'grow',
  setReflectionIntensity: (intensity) => set({ reflectionIntensity: intensity }),
  settingsBusy: false,
  exportData: async () => {
    set({ settingsBusy: true });
    try {
      const data = await api.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json;charset=utf-8',
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `nabom-export-${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(url);
      return true;
    } catch {
      return false;
    } finally {
      set({ settingsBusy: false });
    }
  },
  deleteAccountViaApi: async () => {
    set({ settingsBusy: true });
    try {
      await api.deleteAccount();
      get().logout();
      return true;
    } catch {
      return false;
    } finally {
      set({ settingsBusy: false });
    }
  },
  deleteRecordsViaApi: async () => {
    set({ settingsBusy: true });
    try {
      await api.deleteRecords();
      set({
        dailyEntries: [],
        weeklyMirrors: [],
        currentReflection: null,
        experiments: [],
        currentView: 'today',
      });
      return true;
    } catch {
      return false;
    } finally {
      set({ settingsBusy: false });
    }
  },
}));

// 세션 복원은 모듈 로드 시 한다. 프로필/데이터 hydrate는 AppShell이
// URL 기반 뷰 결정 이후에 호출하므로, 여기서는 currentView를 건드리지 않는다.
if (typeof window !== 'undefined') {
  const stored = loadStoredSession();
  if (stored) {
    useNabomStore.setState({ session: stored, authStatus: 'ready' });
  }
}
