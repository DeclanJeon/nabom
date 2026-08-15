'use client';

import { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  CalendarDays,
  Clock,
  MapPin,
  Target,
  Pencil,
  Sparkles,
  Leaf,
  Info,
  Check,
} from 'lucide-react';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useNabomStore } from '@/store/nabom-store';
import { PRIORITY_OPTIONS } from '@/types/nabom';
import type { BirthGender, BirthInput, CalendarType, TimePrecision, TimeWindow } from '@/types/nabom';
import {
  parseCombinedBirthText,
  partsFromIso,
  resolveBirthDate,
  sanitizeBirthPart,
  type BirthDateParts,
} from '@/lib/birth-date';
import {
  QUICK_BIRTH_PLACES,
  searchBirthPlaces,
  toBirthLocation,
  type BirthPlace,
} from '@/lib/birth-place';

// ─── Constants ───────────────────────────────────────────────────────────────

const TOTAL_STEPS = 9;

const TIME_PERIODS = [
  { value: 'morning', label: '아침 (06:00–11:59)', time: '06:00-11:59' },
  { value: 'afternoon', label: '낮 (12:00–17:59)', time: '12:00-17:59' },
  { value: 'evening', label: '저녁 (18:00–21:59)', time: '18:00-21:59' },
  { value: 'night', label: '밤 (22:00–22:59)', time: '22:00-22:59' },
  { value: 'around_midnight', label: '자정 전후 (23:00–01:00)', time: '23:00-01:00' },
] as const;

const STEP_ICONS = [
  Sparkles,  // 1 welcome
  Pencil,    // 2 nickname
  Sparkles,  // 3 gender
  CalendarDays, // 4 birth date
  Clock,     // 5 birth time
  MapPin,    // 6 birth location
  Target,    // 7 priorities
  Pencil,    // 8 change desire
  Leaf,      // 9 current goal
];

// ─── Animation ───────────────────────────────────────────────────────────────

const prefersReducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const noMotion = prefersReducedMotion();

const slideVariants = {
  enter: (direction: number) =>
    noMotion
      ? { opacity: 0 }
      : { x: direction > 0 ? 300 : -300, opacity: 0 },
  center: { x: 0, opacity: 1 },
  exit: (direction: number) =>
    noMotion
      ? { opacity: 0 }
      : { x: direction > 0 ? -300 : 300, opacity: 0 },
};

const slideTransition = noMotion
  ? { duration: 0 }
  : { type: 'spring' as const, stiffness: 300, damping: 30 };

// ─── Step Indicator ──────────────────────────────────────────────────────────

function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center justify-center gap-1.5 pb-4 pt-2" role="progressbar" aria-valuenow={current} aria-valuemin={1} aria-valuemax={total} aria-label={`온보딩 ${current}/${total}단계`} >
      {Array.from({ length: total }, (_, i) => {
        const step = i + 1;
        const isCompleted = step < current;
        const isCurrent = step === current;
        return (
          <div
            key={step}
            className={`h-2 rounded-full transition-all duration-300 ${
              isCompleted
                ? 'w-6 bg-primary'
                : isCurrent
                  ? 'w-6 bg-primary/80'
                  : 'w-2 bg-border'
            }`}
          />
        );
      })}
    </div>
  );
}

// ─── Back Button ─────────────────────────────────────────────────────────────

function BackButton({
  onClick,
  step,
}: {
  onClick: () => void;
  step: number;
}) {
  const goBack = useNabomStore((s) => s.goBack);
  const setView = useNabomStore((s) => s.setView);

  const handleBack = () => {
    if (step === 1) {
      setView('landing');
    } else {
      onClick();
    }
  };

  return (
    <button
      type="button"
      onClick={handleBack}
      className="flex h-11 w-11 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      aria-label={step === 1 ? '랜딩으로 돌아가기' : '이전 단계'}
    >
      <ArrowLeft className="h-5 w-5" />
    </button>
  );
}

// ─── Step Wrapper ────────────────────────────────────────────────────────────

function StepShell({
  step,
  direction,
  children,
}: {
  step: number;
  direction: number;
  children: React.ReactNode;
}) {
  const StepIcon = STEP_ICONS[step - 1];

  return (
    <motion.div
      key={step}
      custom={direction}
      variants={slideVariants}
      initial="enter"
      animate="center"
      exit="exit"
      transition={slideTransition}
      className="flex min-h-[60vh] flex-col"
    >
      <div className="mb-6 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-warm-100">
          <StepIcon className="h-4 w-4 text-warm-600" />
        </div>
        <span className="text-xs font-medium text-muted-foreground">
          {step}/{TOTAL_STEPS}
        </span>
      </div>
      {children}
    </motion.div>
  );
}

// ─── Step 1: Welcome ─────────────────────────────────────────────────────────

function StepWelcome({ onNext }: { onNext: () => void }) {
  return (
    <StepShell step={1} direction={0}>
      <div className="flex flex-1 flex-col items-center justify-center text-center pb-8">
        <motion.div
          initial={noMotion ? {} : { opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mb-8 flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-warm-100 to-sage-100"
        >
          <Leaf className="h-10 w-10 text-sage-500" />
        </motion.div>
        <h2 className="text-2xl font-bold leading-snug text-foreground">
          나봄에 오신 것을
          <br />
          환영합니다
        </h2>
        <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
          처음에는 몇 가지 정보로 프로필을 만들고,
          <br />
          앞으로의 기록을 통해 계속 당신을 알아갑니다.
        </p>
      </div>
      <Button
        size="lg"
        className="mt-auto h-12 w-full rounded-xl text-base font-semibold"
        onClick={onNext}
      >
        내 프로필 만들기
      </Button>
    </StepShell>
  );
}

// ─── Step 2: Nickname ────────────────────────────────────────────────────────

function StepNickname({
  value,
  onChange,
  onNext,
}: {
  value: string;
  onChange: (v: string) => void;
  onNext: () => void;
}) {
  const canProceed = value.trim().length > 0;

  return (
    <StepShell step={2} direction={0}>
      <div className="flex-1">
        <h2 className="text-xl font-bold text-foreground">
          이름 또는 닉네임을 알려주세요
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          나봄이 당신을 부를 이름입니다.
        </p>
        <div className="mt-8">
          <Input
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="예: 지은, 하늘, 별"
            className="h-12 rounded-xl text-base"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter' && canProceed) onNext();
            }}
          />
        </div>
      </div>
      <Button
        size="lg"
        className="mt-auto h-12 w-full rounded-xl text-base font-semibold"
        disabled={!canProceed}
        onClick={onNext}
      >
        다음
      </Button>
    </StepShell>
  );
}

const GENDER_OPTIONS: Array<{ value: BirthGender; label: string; hint: string }> = [
  { value: 'female', label: '여성', hint: '여성 치비로 맞춥니다' },
  { value: 'male', label: '남성', hint: '남성 치비로 맞춥니다' },
];

function StepBirthGender({
  value,
  onChange,
  onNext,
}: {
  value: BirthGender;
  onChange: (value: BirthGender) => void;
  onNext: () => void;
}) {
  const canProceed = value === 'female' || value === 'male';
  return (
    <StepShell step={3} direction={0}>
      <div className="flex-1">
        <h2 className="text-xl font-bold text-foreground">성별을 알려주세요</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          프로필 캐릭터를 맞추는 데 씁니다.
        </p>
        <div className="mt-8 grid gap-3">
          {GENDER_OPTIONS.map((option) => {
            const selected = value === option.value;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => onChange(option.value)}
                className={`rounded-xl border px-4 py-4 text-left transition-colors ${
                  selected
                    ? 'border-primary bg-warm-50'
                    : 'border-border/70 bg-background hover:border-primary/40 hover:bg-warm-50'
                }`}
              >
                <span className="block text-base font-semibold text-foreground">{option.label}</span>
                <span className="mt-1 block text-xs text-muted-foreground">{option.hint}</span>
              </button>
            );
          })}
        </div>
      </div>
      <Button
        size="lg"
        className="mt-auto h-12 w-full rounded-xl text-base font-semibold"
        disabled={!canProceed}
        onClick={onNext}
      >
        다음
      </Button>
    </StepShell>
  );
}

// ─── Step 4: Birth Date ──────────────────────────────────────────────────────

function StepBirthDate({
  calendarType,
  onCalendarChange,
  iso,
  onIsoChange,
  isLunarLeapMonth,
  onLeapChange,
  onNext,
}: {
  calendarType: CalendarType;
  onCalendarChange: (t: CalendarType) => void;
  iso: string;
  onIsoChange: (iso: string) => void;
  isLunarLeapMonth: boolean | null | undefined;
  onLeapChange: (value: boolean | null) => void;
  onNext: () => void;
}) {
  const [parts, setParts] = useState<BirthDateParts>(() => partsFromIso(iso));
  const [combined, setCombined] = useState(iso ? iso.replaceAll('-', '.') : '');
  const resolved = resolveBirthDate(parts);
  const canProceed = Boolean(resolved.iso) && (calendarType === 'solar' || isLunarLeapMonth !== undefined);

  const commitParts = (next: BirthDateParts) => {
    setParts(next);
    const result = resolveBirthDate(next);
    if (result.iso) {
      onIsoChange(result.iso);
      setCombined(`${result.year}.${result.month.padStart(2, '0')}.${result.day.padStart(2, '0')}`);
    } else {
      onIsoChange('');
    }
  };

  const handleField = (field: keyof BirthDateParts, raw: string) => {
    commitParts({ ...parts, [field]: sanitizeBirthPart(field, raw) });
  };

  const handleCombined = (raw: string) => {
    setCombined(raw);
    const parsed = parseCombinedBirthText(raw);
    if (parsed) commitParts(parsed);
    else if (!raw.trim()) commitParts({ year: '', month: '', day: '' });
  };

  return (
    <StepShell step={4} direction={0}>
      <div className="flex-1">
        <h2 className="text-xl font-bold text-foreground">
          생년월일을 알려주세요
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          직접 치거나, 1992.03.01처럼 붙여넣어도 됩니다.
        </p>

        <div className="mt-6 flex rounded-xl bg-muted p-1">
          {([['solar', '양력'], ['lunar', '음력']] as const).map(
            ([type, label]) => (
              <button
                key={type}
                type="button"
                onClick={() => onCalendarChange(type)}
                className={`flex-1 rounded-lg py-2.5 text-sm font-medium transition-all min-h-[44px] ${
                  calendarType === type
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
                aria-pressed={calendarType === type}
              >
                {label}
              </button>
            ),
          )}
        </div>

        {calendarType === 'lunar' && (
          <motion.div
            initial={noMotion ? {} : { opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-3 space-y-3"
          >
            <div className="flex items-start gap-2 rounded-xl bg-sage-50 p-3 border border-sage-200/50">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-sage-500" />
              <p className="text-xs leading-relaxed text-sage-700">
                그해에 같은 달이 두 번이면 평달과 윤달을 골라야 합니다. 추측하지 않습니다.
              </p>
            </div>
            <div className="flex gap-2">
              {([
                [false, '평달'],
                [true, '윤달'],
                [null, '잘 모름'],
              ] as const).map(([value, label]) => (
                <button
                  key={label}
                  type="button"
                  onClick={() => onLeapChange(value)}
                  className={`flex-1 rounded-xl border py-2.5 text-sm font-medium min-h-[44px] ${
                    isLunarLeapMonth === value
                      ? 'border-primary bg-warm-50 text-foreground'
                      : 'border-border text-muted-foreground'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        <div className="mt-6 space-y-2">
          <label htmlFor="birth-combined" className="text-xs font-medium text-muted-foreground">
            한 줄로 입력
          </label>
          <Input
            id="birth-combined"
            inputMode="numeric"
            autoComplete="bday"
            value={combined}
            onChange={(e) => handleCombined(e.target.value)}
            placeholder="1992.03.01 또는 19920301"
            className="h-12 rounded-xl text-base"
          />
        </div>

        <div className="mt-4 grid grid-cols-3 gap-2">
          <div className="space-y-2">
            <label htmlFor="birth-year" className="text-xs font-medium text-muted-foreground">
              년
            </label>
            <Input
              id="birth-year"
              inputMode="numeric"
              autoComplete="bday-year"
              value={parts.year}
              onChange={(e) => handleField('year', e.target.value)}
              placeholder="1992"
              className="h-12 rounded-xl text-base"
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="birth-month" className="text-xs font-medium text-muted-foreground">
              월
            </label>
            <Input
              id="birth-month"
              inputMode="numeric"
              autoComplete="bday-month"
              value={parts.month}
              onChange={(e) => handleField('month', e.target.value)}
              placeholder="3"
              className="h-12 rounded-xl text-base"
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="birth-day" className="text-xs font-medium text-muted-foreground">
              일
            </label>
            <Input
              id="birth-day"
              inputMode="numeric"
              autoComplete="bday-day"
              value={parts.day}
              onChange={(e) => handleField('day', e.target.value)}
              placeholder="1"
              className="h-12 rounded-xl text-base"
            />
          </div>
        </div>

        {resolved.error && (
          <p className="mt-3 text-sm text-warm-700">{resolved.error}</p>
        )}
        {resolved.iso && !resolved.error && (
          <p className="mt-3 text-sm text-muted-foreground">
            {format(new Date(`${resolved.iso}T00:00:00`), 'yyyy년 M월 d일 (EEEE)', { locale: ko })}
          </p>
        )}
      </div>
      <Button
        size="lg"
        className="mt-auto h-12 w-full rounded-xl text-base font-semibold"
        disabled={!canProceed}
        onClick={onNext}
      >
        다음
      </Button>
    </StepShell>
  );
}

// ─── Step 5: Birth Time ──────────────────────────────────────────────────────

function StepBirthTime({
  timePrecision,
  time,
  onPrecisionChange,
  onTimeChange,
  onPeriodChange,
  onNext,
  onSkip,
}: {
  timePrecision: TimePrecision;
  time: string;
  onPrecisionChange: (p: TimePrecision) => void;
  onTimeChange: (t: string) => void;
  onPeriodChange: (p: string) => void;
  onNext: () => void;
  onSkip: () => void;
}) {
  const canProceedExact = timePrecision === 'exact' && time !== '';
  const canProceedApprox = timePrecision === 'approximate' && time.includes('-');

  const handleSelect = (precision: TimePrecision) => {
    onPrecisionChange(precision);
    if (precision === 'unknown') {
      onTimeChange('');
    }
  };

  return (
    <StepShell step={5} direction={0}>
      <div className="flex-1">
        <h2 className="text-xl font-bold text-foreground">
          태어난 시간을 알려주세요
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          정확할수록 좋지만, 몰라도 괜찮습니다.
        </p>

        <div className="mt-6 flex flex-col gap-3">
          {/* Exact time */}
          <button
            type="button"
            onClick={() => handleSelect('exact')}
            className={`flex items-center gap-4 rounded-xl border p-4 text-left transition-all min-h-[44px] ${
              timePrecision === 'exact'
                ? 'border-primary bg-warm-50 ring-1 ring-primary/20'
                : 'border-border hover:border-warm-300 hover:bg-warm-50/50'
            }`}
          >
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                timePrecision === 'exact'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              <Clock className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-foreground">정확한 시간</p>
              <p className="text-xs text-muted-foreground">출생 시간을 알고 있어요</p>
            </div>
          </button>

          {/* Exact time input (shown when selected) */}
          <AnimatePresence>
            {timePrecision === 'exact' && (
              <motion.div
                initial={noMotion ? { opacity: 1 } : { height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={noMotion ? { opacity: 0 } : { height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="pb-1 pl-4">
                  <Input
                    type="time"
                    value={time}
                    onChange={(e) => onTimeChange(e.target.value)}
                    className="h-12 rounded-xl text-base"
                    autoFocus
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Approximate time */}
          <button
            type="button"
            onClick={() => handleSelect('approximate')}
            className={`flex items-center gap-4 rounded-xl border p-4 text-left transition-all min-h-[44px] ${
              timePrecision === 'approximate'
                ? 'border-primary bg-warm-50 ring-1 ring-primary/20'
                : 'border-border hover:border-warm-300 hover:bg-warm-50/50'
            }`}
          >
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                timePrecision === 'approximate'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              <Sparkles className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-foreground">대략적인 시간대</p>
              <p className="text-xs text-muted-foreground">아침/낮/저녁/밤 중 하나</p>
            </div>
          </button>

          {/* Approximate time select */}
          <AnimatePresence>
            {timePrecision === 'approximate' && (
              <motion.div
                initial={noMotion ? { opacity: 1 } : { height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={noMotion ? { opacity: 0 } : { height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="pb-1 pl-4">
                  <Select onValueChange={onPeriodChange}>
                    <SelectTrigger className="h-12 w-full rounded-xl text-base">
                      <SelectValue placeholder="시간대를 선택하세요" />
                    </SelectTrigger>
                    <SelectContent>
                      {TIME_PERIODS.map((tp) => (
                        <SelectItem key={tp.value} value={tp.value}>
                          {tp.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Unknown */}
          <button
            type="button"
            onClick={() => handleSelect('unknown')}
            className={`flex items-center gap-4 rounded-xl border p-4 text-left transition-all min-h-[44px] ${
              timePrecision === 'unknown'
                ? 'border-primary bg-warm-50 ring-1 ring-primary/20'
                : 'border-border hover:border-warm-300 hover:bg-warm-50/50'
            }`}
          >
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                timePrecision === 'unknown'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              <Info className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-foreground">모르겠어요</p>
              <p className="text-xs text-muted-foreground">
                시간을 몰라도 이용 가능합니다
              </p>
            </div>
          </button>
        </div>
      </div>

      <div className="mt-auto flex gap-3">
        <Button
          variant="ghost"
          className="h-12 rounded-xl text-sm font-medium text-muted-foreground"
          onClick={onSkip}
        >
          건너뛰기
        </Button>
        <Button
          size="lg"
          className="h-12 flex-1 rounded-xl text-base font-semibold"
          disabled={
            !(canProceedExact || canProceedApprox || timePrecision === 'unknown')
          }
          onClick={onNext}
        >
          다음
        </Button>
      </div>
    </StepShell>
  );
}

// ─── Step 6: Birth Location ──────────────────────────────────────────────────

function StepBirthLocation({
  value,
  onSelect,
  onClear,
  onNext,
  onSkip,
}: {
  value: BirthInput['location'];
  onSelect: (place: BirthPlace) => void;
  onClear: () => void;
  onNext: () => void;
  onSkip: () => void;
}) {
  const [query, setQuery] = useState(value.label);
  const hits = useMemo(() => searchBirthPlaces(query), [query]);
  const selected = Boolean(value.label && value.timezone && (value.lat !== 0 || value.lon !== 0));
  const canProceed = selected;

  const choose = (place: BirthPlace) => {
    onSelect(place);
    setQuery(toBirthLocation(place).label);
  };

  return (
    <StepShell step={6} direction={0}>
      <div className="flex-1">
        <h2 className="text-xl font-bold text-foreground">
          태어난 곳을 알려주세요
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          도시 이름만 입력하면 됩니다. 해외 도시도 검색할 수 있어요.
        </p>
        <div className="mt-8 space-y-4">
          <div className="relative">
            <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => {
                const next = e.target.value;
                setQuery(next);
                if (selected && next !== value.label) onClear();
              }}
              placeholder="예: 부산, 서울, Tokyo, New York"
              className="h-12 rounded-xl pl-10 text-base"
              autoFocus
              autoComplete="off"
              role="combobox"
              aria-expanded={hits.length > 0}
              aria-controls="birth-place-results"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && hits[0]) {
                  e.preventDefault();
                  choose(hits[0]);
                }
              }}
            />
          </div>
          {hits.length > 0 && !selected && (
            <ul
              id="birth-place-results"
              role="listbox"
              className="overflow-hidden rounded-xl border border-border/70 bg-card shadow-sm"
            >
              {hits.map((hit) => (
                <li key={hit.id}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={false}
                    className="flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-warm-50"
                    onClick={() => choose(hit)}
                  >
                    <span>
                      <span className="block text-sm font-medium text-foreground">{hit.displayLabel}</span>
                      <span className="mt-0.5 block text-xs text-muted-foreground">{hit.secondary}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {query.trim() && hits.length === 0 && !selected && (
            <p className="rounded-xl bg-warm-50 px-4 py-3 text-sm text-warm-700">
              목록에 없는 도시예요. 가까운 큰 도시로 검색해 주세요.
            </p>
          )}
          {selected && (
            <div className="rounded-xl border border-sage-200 bg-sage-50 px-4 py-3 text-sm text-sage-800">
              {value.label}
              <span className="mt-1 block text-xs text-sage-700">{value.timezone}</span>
            </div>
          )}
          <div className="flex flex-wrap gap-2">
            {QUICK_BIRTH_PLACES.map((place) => (
              <button
                key={place.id}
                type="button"
                className="rounded-full border border-border/70 bg-background px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:border-primary/40 hover:bg-warm-50"
                onClick={() => choose(place)}
              >
                {place.labelKo}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-auto flex gap-3">
        <Button
          variant="ghost"
          className="h-12 rounded-xl text-sm font-medium text-muted-foreground"
          onClick={onSkip}
        >
          건너뛰기
        </Button>
        <Button
          size="lg"
          className="h-12 flex-1 rounded-xl text-base font-semibold"
          disabled={!canProceed}
          onClick={onNext}
        >
          다음
        </Button>
      </div>
    </StepShell>
  );
}

// ─── Step 7: Priorities ──────────────────────────────────────────────────────

function StepPriorities({
  selected,
  onToggle,
  onNext,
  onSkip,
}: {
  selected: string[];
  onToggle: (value: string) => void;
  onNext: () => void;
  onSkip: () => void;
}) {
  const canProceed = selected.length >= 1 && selected.length <= 3;
  const atMax = selected.length >= 3;

  return (
    <StepShell step={7} direction={0}>
      <div className="flex-1">
        <h2 className="text-xl font-bold text-foreground">
          지금 가장 중요한 영역
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          1~3개를 선택해주세요.
        </p>
        <div className="mt-6 flex flex-wrap gap-2.5">
          {PRIORITY_OPTIONS.map((opt) => {
            const isSelected = selected.includes(opt.value);
            const isDisabled = !isSelected && atMax;
            return (
              <button
                key={opt.value}
                type="button"
                disabled={isDisabled}
                onClick={() => onToggle(opt.value)}
                className={`rounded-full border px-4 py-2.5 text-sm font-medium transition-all min-h-[44px] ${
                  isSelected
                    ? 'border-primary bg-primary text-primary-foreground shadow-sm'
                    : isDisabled
                      ? 'cursor-not-allowed border-border bg-muted text-muted-foreground/50'
                      : 'border-border bg-card text-foreground hover:border-warm-300 hover:bg-warm-50'
                }`}
                aria-pressed={isSelected}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
        {selected.length > 0 && (
          <p className="mt-3 text-xs text-muted-foreground">
            {selected.length}/3 선택됨
          </p>
        )}
      </div>
      <div className="mt-auto flex gap-3">
        <Button
          variant="ghost"
          className="h-12 rounded-xl text-sm font-medium text-muted-foreground"
          onClick={onSkip}
        >
          건너뛰기
        </Button>
        <Button
          size="lg"
          className="h-12 flex-1 rounded-xl text-base font-semibold"
          disabled={!canProceed}
          onClick={onNext}
        >
          다음
        </Button>
      </div>
    </StepShell>
  );
}

// ─── Step 8: Change Desire ───────────────────────────────────────────────────

function StepChangeDesire({
  value,
  onChange,
  onNext,
  onSkip,
}: {
  value: string;
  onChange: (v: string) => void;
  onNext: () => void;
  onSkip: () => void;
}) {
  return (
    <StepShell step={8} direction={0}>
      <div className="flex-1">
        <h2 className="text-xl font-bold text-foreground">
          지금 바꾸고 싶은 것
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          마음에 담아둔 것이 있다면 자유롭게 적어주세요.
        </p>
        <div className="mt-6">
          <Textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="예: 매일 밤 스마트폰을 보느라 잠이 늦어요"
            className="min-h-[120px] rounded-xl text-base leading-relaxed"
            autoFocus
          />
        </div>
      </div>
      <div className="mt-auto flex gap-3">
        <Button
          variant="ghost"
          className="h-12 rounded-xl text-sm font-medium text-muted-foreground"
          onClick={onSkip}
        >
          건너뛰기
        </Button>
        <Button
          size="lg"
          className="h-12 flex-1 rounded-xl text-base font-semibold"
          onClick={onNext}
        >
          다음
        </Button>
      </div>
    </StepShell>
  );
}

// ─── Step 9: Current Goal ────────────────────────────────────────────────────

function StepCurrentGoal({
  value,
  onChange,
  onComplete,
  isSubmitting,
  submitError,
}: {
  value: string;
  onChange: (v: string) => void;
  onComplete: () => void;
  isSubmitting: boolean;
  submitError: string | null;
}) {
  return (
    <StepShell step={9} direction={0}>
      <div className="flex-1">
        <h2 className="text-xl font-bold text-foreground">
          지금 이루고 싶은 것
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          생략해도 괜찮습니다. 나중에 언제든 추가할 수 있어요.
        </p>
        <div className="mt-6">
          <Textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="예: 3개월 안에 취미 하나를 꾸준히 해보기"
            className="min-h-[120px] rounded-xl text-base leading-relaxed"
            autoFocus
          />
        </div>
        {submitError && (
          <div className="mt-4 flex items-start gap-2 rounded-xl border border-warm-200/60 bg-warm-50/70 px-4 py-3">
            <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-warm-500" />
            <p className="text-sm text-warm-800">{submitError}</p>
          </div>
        )}
      </div>
      <Button
        size="lg"
        className="mt-auto h-12 w-full rounded-xl text-base font-semibold"
        onClick={onComplete}
        disabled={isSubmitting}
      >
        {isSubmitting ? '프로필을 만드는 중…' : '시작하기'}
      </Button>
    </StepShell>
  );
}

// ─── Main Onboarding Component ────────────────────────────────────────────────

export default function Onboarding() {
  const {
    onboardingStep,
    onboardingData,
    setOnboardingStep,
    updateOnboardingData,
    createProfileFromOnboarding,
    profileCreating,
    profileCreateError,
  } = useNabomStore();

  const [direction, setDirection] = useState(0);

  const goNext = useCallback(() => {
    setDirection(1);
    setOnboardingStep(onboardingStep + 1);
  }, [onboardingStep, setOnboardingStep]);

  const goPrev = useCallback(() => {
    setDirection(-1);
    setOnboardingStep(onboardingStep - 1);
  }, [onboardingStep, setOnboardingStep]);

  const handleCalendarChange = useCallback(
    (type: CalendarType) => {
      updateOnboardingData({
        birth: {
          calendar: type,
          isLunarLeapMonth: type === 'lunar' ? onboardingData.birth.isLunarLeapMonth ?? null : null,
        } as never,
      });
    },
    [onboardingData.birth.isLunarLeapMonth, updateOnboardingData],
  );

  const handleLeapChange = useCallback(
    (value: boolean | null) => {
      updateOnboardingData({
        birth: { isLunarLeapMonth: value } as never,
      });
    },
    [updateOnboardingData],
  );

  const handleDateChange = useCallback(
    (iso: string) => {
      updateOnboardingData({
        birth: { date: iso } as never,
      });
    },
    [updateOnboardingData],
  );

  const handlePrecisionChange = useCallback(
    (precision: TimePrecision) => {
      updateOnboardingData({
        birth: {
          timePrecision: precision,
          time: precision === 'unknown' ? '' : onboardingData.birth.time,
          timeWindow: precision === 'unknown' ? '' : onboardingData.birth.timeWindow,
        } as never,
      });
    },
    [onboardingData.birth.time, onboardingData.birth.timeWindow, updateOnboardingData],
  );

  const handleTimeChange = useCallback(
    (time: string) => {
      updateOnboardingData({ birth: { time, timeWindow: '' } as never });
    },
    [updateOnboardingData],
  );

  const handlePeriodChange = useCallback(
    (period: string) => {
      const selected = TIME_PERIODS.find((item) => item.value === period);
      updateOnboardingData({
        birth: {
          time: selected?.time ?? '',
          timeWindow: (period as TimeWindow) || '',
        } as never,
      });
    },
    [updateOnboardingData],
  );

  const handleLocationSelect = useCallback(
    (place: BirthPlace) => {
      updateOnboardingData({
        birth: { location: toBirthLocation(place) } as never,
      });
    },
    [updateOnboardingData],
  );

  const handleLocationClear = useCallback(() => {
    updateOnboardingData({
      birth: { location: { label: '', lat: 0, lon: 0, timezone: '' } } as never,
    });
  }, [updateOnboardingData]);

  const handlePriorityToggle = useCallback(
    (value: string) => {
      const current = onboardingData.priorities;
      const next = current.includes(value)
        ? current.filter((v) => v !== value)
        : current.length < 3
          ? [...current, value]
          : current;
      updateOnboardingData({ priorities: next });
    },
    [onboardingData.priorities, updateOnboardingData],
  );

  return (
    <main className="min-h-screen flex flex-col bg-background">
      <div className="nabom-narrow flex flex-1 flex-col">
        {/* Header: Back + Step Indicator */}
        <div className="sticky top-0 z-10 bg-background/80 pb-2 pt-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <BackButton onClick={goPrev} step={onboardingStep} />
          </div>
          <StepIndicator current={onboardingStep} total={TOTAL_STEPS} />
        </div>

        {/* Step Content */}
        <div className="relative flex-1 overflow-hidden py-4">
          <AnimatePresence mode="wait" custom={direction}>
            {onboardingStep === 1 && (
              <StepWelcome key="step-1" onNext={goNext} />
            )}
            {onboardingStep === 2 && (
              <StepNickname
                key="step-2"
                value={onboardingData.nickname}
                onChange={(v) => updateOnboardingData({ nickname: v })}
                onNext={goNext}
              />
            )}
            {onboardingStep === 3 && (
              <StepBirthGender
                key="step-3"
                value={onboardingData.birth.gender}
                onChange={(gender) => updateOnboardingData({ birth: { gender } as never })}
                onNext={goNext}
              />
            )}
            {onboardingStep === 4 && (
              <StepBirthDate
                key="step-4"
                calendarType={onboardingData.birth.calendar}
                onCalendarChange={handleCalendarChange}
                iso={onboardingData.birth.date}
                onIsoChange={handleDateChange}
                isLunarLeapMonth={onboardingData.birth.isLunarLeapMonth}
                onLeapChange={handleLeapChange}
                onNext={goNext}
              />
            )}
            {onboardingStep === 5 && (
              <StepBirthTime
                key="step-5"
                timePrecision={onboardingData.birth.timePrecision}
                time={onboardingData.birth.time}
                onPrecisionChange={handlePrecisionChange}
                onTimeChange={handleTimeChange}
                onPeriodChange={handlePeriodChange}
                onNext={goNext}
                onSkip={goNext}
              />
            )}
            {onboardingStep === 6 && (
              <StepBirthLocation
                key="step-6"
                value={onboardingData.birth.location}
                onSelect={handleLocationSelect}
                onClear={handleLocationClear}
                onNext={goNext}
                onSkip={goNext}
              />
            )}
            {onboardingStep === 7 && (
              <StepPriorities
                key="step-7"
                selected={onboardingData.priorities}
                onToggle={handlePriorityToggle}
                onNext={goNext}
                onSkip={goNext}
              />
            )}
            {onboardingStep === 8 && (
              <StepChangeDesire
                key="step-8"
                value={onboardingData.changeDesire}
                onChange={(v) => updateOnboardingData({ changeDesire: v })}
                onNext={goNext}
                onSkip={goNext}
              />
            )}
            {onboardingStep === 9 && (
              <StepCurrentGoal
                key="step-9"
                value={onboardingData.currentGoal}
                onChange={(v) => updateOnboardingData({ currentGoal: v })}
                onComplete={() => {
                  if (profileCreating) return;
                  void (async () => {
                    const ok = await createProfileFromOnboarding();
                    if (!ok) {
                      toast.error(
                        '프로필을 만들지 못했어요. 잠시 후 다시 시도해주세요.',
                      );
                    }
                  })();
                }}
                isSubmitting={profileCreating}
                submitError={profileCreateError}
              />
            )}
          </AnimatePresence>
        </div>
      </div>
    </main>
  );
}
