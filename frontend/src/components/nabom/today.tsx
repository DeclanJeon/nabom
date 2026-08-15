'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale/ko';
import {
  ChevronDown,
  ChevronUp,
  Check,
  Sparkles,
  Plus,
  Zap,
  Smile,
  Heart,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { useNabomStore } from '@/store/nabom-store';
import type { DailyEntry } from '@/types/nabom';
import {
  MOOD_LABELS,
  MOOD_EMOJI,
  ENERGY_LABELS,
  SATISFACTION_LABELS,
} from '@/types/nabom';

// ─── Animation Helpers ───────────────────────────────────────────────────────

const noMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const fadeUp = (delay = 0) => {
  if (noMotion()) return {};
  return {
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] as const },
  };
};

const staggerContainer = (stagger = 0.06) => {
  if (noMotion()) return {};
  return {
    animate: { transition: { staggerChildren: stagger } },
  };
};

// ─── Constants ───────────────────────────────────────────────────────────────

const TAG_OPTIONS = [
  { value: 'work', label: '일' },
  { value: 'relationship', label: '관계' },
  { value: 'health', label: '건강' },
  { value: 'growth', label: '성장' },
  { value: 'creativity', label: '창작' },
  { value: 'rest', label: '휴식' },
  { value: 'emotion', label: '감정' },
] as const;

const AI_RESPONSES: Record<number, string[]> = {
  1: [
    '오늘 하루가 힘들었나 봐요. 스스로를 탓하지 않아도 괜찮아요. 기록해둘게요.',
    '무거운 하루였네요. 이 기록이 나를 이해하는 단서가 될 거예요.',
  ],
  2: [
    '조금 어려운 하루였네요. 괜찮아요, 그런 날도 있죠. 기록해둘게요.',
    '복잡한 감정이 있었던 것 같아요. 기록해두면 나중에 패턴이 보일 거예요.',
  ],
  3: [
    '소박하지만 괜찮은 하루였네요. 이 평온함도 나를 알아가는 중요한 기록이에요.',
    '보통의 하루. 특별하지 않아도 괜찮아요. 기록해둘게요.',
  ],
  4: [
    '좋은 에너지가 느껴져요. 이 흐름을 기억해두면 좋겠어요.',
    '오늘은 긍정적인 신호들이 보이네요. 기록해둘게요.',
  ],
  5: [
    '오늘은 정말 빛나는 하루였네요! 이 감정을 꼭 기억해두세요.',
    '마음이 가득 찬 하루였네요. 이 느낌, 나를 위한 좋은 거울이 될 거예요.',
  ],
};

// Warm color for slider value display based on 1-5
const valueColor = (val: number) => {
  switch (val) {
    case 1: return 'text-muted-foreground';
    case 2: return 'text-warm-500';
    case 3: return 'text-warm-600';
    case 4: return 'text-warm-700';
    case 5: return 'text-terra-500';
    default: return 'text-foreground';
  }
};

// Tag label lookup
const TAG_LABELS: Record<string, string> = {
  work: '일',
  relationship: '관계',
  health: '건강',
  growth: '성장',
  creativity: '창작',
  rest: '휴식',
  emotion: '감정',
};

// Format entry date for display
const formatEntryDate = (dateStr: string) => {
  const d = new Date(dateStr + 'T00:00:00');
  return format(d, 'M월 d일', { locale: ko });
};

const formatWeekday = (dateStr: string) => {
  const d = new Date(dateStr + 'T00:00:00');
  return format(d, 'EEEE', { locale: ko });
};

// ─── Slider Row Component ────────────────────────────────────────────────────

interface SliderRowProps {
  icon: React.ElementType;
  label: string;
  value: number;
  labels: Record<number, string>;
  onChange: (val: number) => void;
}

function SliderRow({ icon: Icon, label, value, labels, onChange }: SliderRowProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-warm-500" />
          <span className="text-sm font-medium text-foreground">{label}</span>
        </div>
        <span className={`text-sm font-semibold tabular-nums ${valueColor(value)}`}>
          {labels[value]}
        </span>
      </div>
      <div className="flex items-center gap-3 px-1 py-2">
        <Slider
          min={1}
          max={5}
          step={1}
          value={[value]}
          onValueChange={([v]) => onChange(v)}
          className="w-full"
        />
      </div>
    </div>
  );
}

// ─── Entry Card Component ───────────────────────────────────────────────────

interface EntryCardProps {
  entry: DailyEntry;
  index: number;
}

function EntryCard({ entry, index }: EntryCardProps) {
  return (
    <motion.div
      {...(noMotion() ? {} : fadeUp(0.05 * index))}
      layout
    >
      <Card className="border-border/50 bg-card/80 shadow-sm">
        <CardContent className="p-4 space-y-3">
          {/* Date row */}
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">
              {formatEntryDate(entry.date)} {formatWeekday(entry.date)}
            </span>
            <span className="text-base" role="img" aria-label={`기분: ${MOOD_LABELS[entry.mood]}`}>
              {MOOD_EMOJI[entry.mood]}
            </span>
          </div>

          {/* One-line text */}
          <p className="text-sm leading-relaxed text-foreground">
            {entry.text}
          </p>

          {/* Stats and tags */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Zap className="h-3 w-3" />
              {ENERGY_LABELS[entry.energy]}
            </span>
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Heart className="h-3 w-3" />
              {SATISFACTION_LABELS[entry.satisfaction]}
            </span>
            {entry.tags.map((tag) => (
              <Badge
                key={tag}
                variant="secondary"
                className="text-[11px] px-1.5 py-0 font-normal"
              >
                {TAG_LABELS[tag] ?? tag}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ─── Today's Completed Entry ────────────────────────────────────────────────

interface TodayCompletedProps {
  entry: DailyEntry;
  onAddAnother: () => void;
}

function TodayCompleted({ entry, onAddAnother }: TodayCompletedProps) {
  return (
    <motion.div
      {...(noMotion()
        ? {}
        : {
            initial: { opacity: 0, scale: 0.97 },
            animate: { opacity: 1, scale: 1 },
            transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] as const },
          })}
    >
      <Card className="border-sage-300/50 bg-gradient-to-br from-sage-50/80 to-warm-50/80 shadow-sm">
        <CardContent className="p-5 space-y-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-sage-200">
              <Check className="h-4 w-4 text-sage-700" />
            </div>
            <span className="text-sm font-semibold text-sage-700">
              오늘의 기록이 완료되었어요
            </span>
          </div>
          <div className="flex items-center gap-2 pl-1">
            <span className="text-lg" role="img" aria-label={`기분: ${MOOD_LABELS[entry.mood]}`}>
              {MOOD_EMOJI[entry.mood]}
            </span>
            <span className="text-sm text-foreground">{entry.text}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-sage-600 hover:text-sage-700 hover:bg-sage-100 ml-auto"
            onClick={onAddAnother}
          >
            <Plus className="h-4 w-4" />
            하나 더 기록하기
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ─── AI Daily Response ──────────────────────────────────────────────────────

interface AIResponseProps {
  mood: number;
}

function AIResponse({ mood }: AIResponseProps) {
  const responses = AI_RESPONSES[mood] ?? AI_RESPONSES[3];
  const text = responses[Math.floor(Math.random() * responses.length)];

  return (
    <motion.div
      {...(noMotion()
        ? {}
        : {
            initial: { opacity: 0, y: 8 },
            animate: { opacity: 1, y: 0 },
            transition: { duration: 0.6, delay: 0.2, ease: [0.22, 1, 0.36, 1] as const },
          })}
    >
      <div className="flex gap-3 rounded-xl bg-warm-100/60 border border-warm-200/50 p-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-warm-200/80">
          <Sparkles className="h-4 w-4 text-warm-600" />
        </div>
        <p className="text-sm leading-relaxed text-warm-800 pt-1">
          {text}
        </p>
      </div>
    </motion.div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function Today() {
  const { dailyEntries, addDailyEntryViaApi, entrySubmitting } = useNabomStore();

  // Today's date strings
  const todayStr = useMemo(() => format(new Date(), 'yyyy-MM-dd'), []);
  const todayDisplay = useMemo(
    () => format(new Date(), 'M월 d일 EEEE', { locale: ko }),
    [],
  );

  // Check if today already has an entry
  const todayEntries = useMemo(
    () => dailyEntries.filter((e) => e.date === todayStr),
    [dailyEntries, todayStr],
  );
  const hasTodayEntry = todayEntries.length > 0;

  // Form state
  const [mood, setMood] = useState(3);
  const [energy, setEnergy] = useState(3);
  const [satisfaction, setSatisfaction] = useState(3);
  const [text, setText] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [journalText, setJournalText] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const [showCompleted, setShowCompleted] = useState(false);
  const [submittedMood, setSubmittedMood] = useState<number | null>(null);
  const [showCheckin, setShowCheckin] = useState(true);

  // Last 5 entries in reverse chronological order
  const pastEntries = useMemo(
    () =>
      [...dailyEntries]
        .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
        .slice(0, 5),
    [dailyEntries],
  );

  // Toggle tag
  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    );
  };

  // Submit
  const handleSubmit = async () => {
    if (!text.trim() || entrySubmitting) return;

    const ok = await addDailyEntryViaApi({
      date: todayStr,
      mood,
      energy,
      satisfaction,
      text: text.trim(),
      tags: selectedTags,
    });

    if (!ok) {
      toast.error('기록을 저장하지 못했어요. 잠시 후 다시 시도해주세요.');
      return;
    }

    setSubmittedMood(mood);
    setShowCompleted(true);
    setShowCheckin(false);
  };

  // Reset for "add another"
  const handleAddAnother = () => {
    setMood(3);
    setEnergy(3);
    setSatisfaction(3);
    setText('');
    setSelectedTags([]);
    setJournalText('');
    setIsExpanded(false);
    setShowCompleted(false);
    setShowCheckin(true);
  };

  return (
    <main className="min-h-screen flex flex-col bg-background">
      <div className="nabom-page">
        {/* ── Header ─────────────────────────────────────────────────────── */}
        <motion.div {...fadeUp(0)} className="mb-5">
          <p className="text-xs font-semibold tracking-wide text-warm-500 uppercase mb-1">
            {todayDisplay}
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            오늘의 나
          </h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            30초만 투자해보세요. 나를 조금 더 알게 될 거예요.
          </p>
        </motion.div>

        <div className="md:grid md:grid-cols-[minmax(0,1.15fr)_minmax(280px,0.85fr)] md:items-start md:gap-8">
          <div>

        {/* ── Today's completed entry ────────────────────────────────────── */}
        <AnimatePresence>
          {showCompleted && submittedMood !== null && (
            <motion.div
              {...(noMotion()
                ? {}
                : {
                    initial: { opacity: 0, height: 0, marginBottom: 0 },
                    animate: { opacity: 1, height: 'auto', marginBottom: 24 },
                    exit: { opacity: 0, height: 0, marginBottom: 0 },
                    transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] as const },
                  })}
              className="overflow-hidden"
            >
              <div className="flex items-center gap-2 mb-4">
                <div className="h-6 w-6 rounded-full bg-sage-200 flex items-center justify-center">
                  <Check className="h-3.5 w-3.5 text-sage-700" />
                </div>
                <span className="text-sm font-medium text-sage-700">
                  기록이 저장되었어요
                </span>
              </div>
              <AIResponse mood={submittedMood} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Pre-existing today entry (from past data) ──────────────────── */}
        {hasTodayEntry && showCheckin && !showCompleted && (
          <motion.div {...fadeUp(0)} className="mb-6">
            {todayEntries.map((entry) => (
              <TodayCompleted
                key={entry.entryId}
                entry={entry}
                onAddAnother={handleAddAnother}
              />
            ))}
          </motion.div>
        )}

        {/* ── Check-in Section ───────────────────────────────────────────── */}
        <AnimatePresence>
          {showCheckin && (
            <motion.div
              {...(noMotion()
                ? {}
                : {
                    initial: { opacity: 0 },
                    animate: { opacity: 1 },
                    exit: { opacity: 0, height: 0, overflow: 'hidden' },
                    transition: { duration: 0.3 },
                  })}
            >
              <motion.div {...fadeUp(0.05)}>
                <Card className="border-border/50 shadow-sm">
                  <CardContent className="p-5 space-y-5">
                    {/* Three sliders */}
                    <div className="space-y-4">
                      <SliderRow
                        icon={Smile}
                        label="기분"
                        value={mood}
                        labels={MOOD_LABELS}
                        onChange={setMood}
                      />
                      <SliderRow
                        icon={Zap}
                        label="에너지"
                        value={energy}
                        labels={ENERGY_LABELS}
                        onChange={setEnergy}
                      />
                      <SliderRow
                        icon={Heart}
                        label="만족도"
                        value={satisfaction}
                        labels={SATISFACTION_LABELS}
                        onChange={setSatisfaction}
                      />
                    </div>

                    {/* Divider */}
                    <div className="h-px bg-border/50" />

                    {/* Required one-line input */}
                    <div className="space-y-2">
                      <label
                        htmlFor="today-text"
                        className="text-sm font-medium text-foreground"
                      >
                        오늘 기억하고 싶은 한 줄
                        <span className="text-terra-400 ml-1" aria-hidden="true">
                          *
                        </span>
                      </label>
                      <Input
                        id="today-text"
                        type="text"
                        placeholder="오늘 나의 하루를 한 문장으로 남겨보세요"
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        className="h-12 text-base placeholder:text-muted-foreground/60"
                        maxLength={200}
                      />
                    </div>

                    {/* ── Optional expand section ──────────────────────────── */}
                    <div className="space-y-0">
                      <button
                        type="button"
                        className="flex w-full items-center justify-between rounded-lg px-1 py-3 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring min-h-[44px]"
                        onClick={() => setIsExpanded(!isExpanded)}
                        aria-expanded={isExpanded}
                        aria-controls="optional-section"
                      >
                        <span>더 기록하고 싶다면</span>
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </button>

                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            id="optional-section"
                            {...(noMotion()
                              ? {}
                              : {
                                  initial: { opacity: 0, height: 0 },
                                  animate: { opacity: 1, height: 'auto' },
                                  exit: { opacity: 0, height: 0 },
                                  transition: {
                                    duration: 0.3,
                                    ease: [0.22, 1, 0.36, 1] as const,
                                  },
                                })}
                            className="overflow-hidden"
                          >
                            <div className="space-y-4 pt-2 pb-1">
                              {/* Tags */}
                              <div className="space-y-2">
                                <p className="text-sm font-medium text-foreground">
                                  오늘의 키워드
                                </p>
                                <div className="flex flex-wrap gap-2">
                                  {TAG_OPTIONS.map((tag) => {
                                    const isSelected = selectedTags.includes(
                                      tag.value,
                                    );
                                    return (
                                      <button
                                        key={tag.value}
                                        type="button"
                                        onClick={() => toggleTag(tag.value)}
                                        className={`min-h-[44px] min-w-[44px] rounded-full px-4 py-2 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                                          isSelected
                                            ? 'bg-primary text-primary-foreground shadow-sm'
                                            : 'bg-muted text-muted-foreground hover:bg-muted/80'
                                        }`}
                                        aria-pressed={isSelected}
                                      >
                                        {tag.label}
                                      </button>
                                    );
                                  })}
                                </div>
                              </div>

                              {/* Free-form journal */}
                              <div className="space-y-2">
                                <label
                                  htmlFor="journal-text"
                                  className="text-sm font-medium text-foreground"
                                >
                                  자유롭게 적어보기
                                </label>
                                <Textarea
                                  id="journal-text"
                                  placeholder="오늘 느낀 감정, 생각, 무엇이든 좋아요"
                                  value={journalText}
                                  onChange={(e) => setJournalText(e.target.value)}
                                  className="min-h-24 text-base leading-relaxed placeholder:text-muted-foreground/60"
                                  rows={3}
                                />
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>

                    {/* Submit button */}
                    <Button
                      size="lg"
                      className="w-full h-12 rounded-xl text-base font-semibold shadow-md transition-all hover:shadow-lg active:scale-[0.98] disabled:opacity-40"
                      disabled={!text.trim() || entrySubmitting}
                      onClick={handleSubmit}
                    >
                      {entrySubmitting ? '기록하는 중…' : '기록하기'}
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
          </div>

        {/* ── Past Entries Section ───────────────────────────────────────── */}
        <motion.div {...fadeUp(0.15)} className="mt-5 md:mt-0">
          <h2 className="text-sm font-bold text-foreground mb-3">
            지난 기록
          </h2>

          {pastEntries.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border/60 bg-muted/30 p-8 text-center">
              <p className="text-sm text-muted-foreground">
                아직 기록이 없어요. 오늘의 나를 기록해보세요.
              </p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto scrollbar-thin pr-1 md:max-h-[70vh]">
              {pastEntries.map((entry, index) => (
                <EntryCard key={entry.entryId} entry={entry} index={index} />
              ))}
            </div>
          )}
        </motion.div>
        </div>
      </div>
    </main>
  );
}
