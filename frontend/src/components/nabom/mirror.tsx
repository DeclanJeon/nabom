'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale/ko';
import {
  Sparkles,
  Leaf,
  AlertCircle,
  ArrowRight,
  Lightbulb,
  Eye,
  Shield,
  FlaskConical,
  CheckCircle2,
  ChevronRight,
  CalendarDays,
  CircleDot,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from '@/components/ui/accordion';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { useNabomStore } from '@/store/nabom-store';
import { CONFIDENCE_LABEL } from '@/types/nabom';
import type { WeeklyMirror as WeeklyMirrorType, GrowthExperiment } from '@/types/nabom';

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

const staggerChild = (delay = 0) => {
  if (noMotion()) return {};
  return {
    initial: { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.45, delay, ease: [0.22, 1, 0.36, 1] as const },
  };
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

const COVERAGE_LABEL: Record<string, string> = {
  full: '풀커버리지',
  partial: '부분',
  light: '가벼운 기록',
};

const COVERAGE_VARIANT: Record<string, 'default' | 'secondary' | 'outline'> = {
  full: 'default',
  partial: 'secondary',
  light: 'outline',
};

function formatPeriodDate(dateStr: string): string {
  try {
    return format(new Date(dateStr), 'M월 d일', { locale: ko });
  } catch {
    return dateStr;
  }
}

function formatDayLabel(dateStr: string): string {
  try {
    return format(new Date(dateStr), 'd일', { locale: ko });
  } catch {
    return dateStr;
  }
}

function moodToColor(mood: number): string {
  // mood 1-5 → muted to terra-400
  const colors = [
    'bg-muted',                    // 1
    'bg-warm-200',                 // 2
    'bg-warm-300',                 // 3
    'bg-warm-400',                 // 4
    'bg-terra-400',                // 5
  ];
  return colors[Math.max(0, Math.min(4, mood - 1))];
}

function moodToSize(mood: number): string {
  const sizes = ['h-3 w-3', 'h-4 w-4', 'h-5 w-5', 'h-6 w-6', 'h-7 w-7'];
  return sizes[Math.max(0, Math.min(4, mood - 1))];
}

// ─── Emotion Flow Component ───────────────────────────────────────────────────

function EmotionFlow({ emotionFlow }: { emotionFlow: WeeklyMirrorType['emotionFlow'] }) {
  return (
    <div className="w-full overflow-x-auto scrollbar-hide py-2">
      <div className="flex items-end justify-start gap-3 min-w-max px-1 pb-1">
        {emotionFlow.map((ef, i) => (
          <motion.div
            key={ef.date}
            {...(noMotion()
              ? {}
              : {
                  initial: { opacity: 0, scale: 0.5 },
                  animate: { opacity: 1, scale: 1 },
                  transition: { duration: 0.4, delay: 0.05 * i, ease: [0.22, 1, 0.36, 1] as const },
                })}
            className="flex flex-col items-center gap-1.5"
          >
            <span className="text-[10px] text-muted-foreground tabular-nums">{ef.label}</span>
            <div
              className={`rounded-full ${moodToColor(ef.mood)} ${moodToSize(ef.mood)} transition-all`}
              aria-label={`${formatDayLabel(ef.date)} 기분 ${ef.mood}/5`}
            />
            <span className="text-xs text-muted-foreground font-medium">
              {formatDayLabel(ef.date)}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// ─── Growth Experiment Component ─────────────────────────────────────────────

function ExperimentSection({
  experiment,
}: {
  experiment: NonNullable<WeeklyMirrorType['growthExperiment']>;
}) {
  const updateExperimentViaApi = useNabomStore((s) => s.updateExperimentViaApi);
  const [result, setResult] = useState(experiment.userResult ?? '');

  const handleStart = async () => {
    const ok = await updateExperimentViaApi(experiment.experimentId, { status: 'in_progress' });
    if (ok) toast.success('실험이 시작되었어요!');
    else toast.error('실험 상태를 저장하지 못했어요.');
  };

  const handleComplete = async () => {
    const ok = await updateExperimentViaApi(experiment.experimentId, {
      status: 'completed',
      userResult: result.trim() || null,
    });
    if (ok) toast.success('실험이 완료되었어요. 수고했어요!');
    else toast.error('실험 결과를 저장하지 못했어요.');
  };

  const handleDecline = async () => {
    const ok = await updateExperimentViaApi(experiment.experimentId, { status: 'declined' });
    if (!ok) toast.error('실험 상태를 저장하지 못했어요.');
  };

  const handleRetry = async () => {
    const ok = await updateExperimentViaApi(experiment.experimentId, {
      status: 'accepted',
      userResult: null,
    });
    if (ok) {
      setResult('');
    } else {
      toast.error('실험 상태를 저장하지 못했어요.');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3 rounded-xl bg-warm-50/80 border border-warm-100/80 p-4">
        <FlaskConical className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
        <div className="space-y-1.5 flex-1">
          <p className="text-sm font-semibold text-foreground">{experiment.title}</p>
          <p className="text-sm leading-relaxed text-foreground/80">{experiment.instruction}</p>
          <p className="text-xs text-muted-foreground">
            <span className="font-medium">성공 조건:</span> {experiment.successCondition}
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {experiment.status === 'accepted' && (
          <div className="flex flex-col gap-2">
            <Button
              size="lg"
              className="w-full h-12 rounded-xl font-semibold"
              onClick={handleStart}
            >
              <FlaskConical className="h-4 w-4" />
              실험 시작하기
            </Button>
            <button
              type="button"
              className="min-h-[44px] w-full text-center text-sm text-muted-foreground hover:text-foreground transition-colors"
              onClick={handleDecline}
            >
              이번 주는 건너뛸래요
            </button>
          </div>
        )}

        {experiment.status === 'in_progress' && (
          <div className="space-y-3">
            <div className="space-y-2">
              <label
                htmlFor="experiment-result"
                className="text-sm font-medium text-foreground"
              >
                실험 후기 (선택)
              </label>
              <Textarea
                id="experiment-result"
                placeholder="어떻게 진행되었나요? 느낀 점을 자유롭게 적어주세요"
                value={result}
                onChange={(e) => setResult(e.target.value)}
                className="min-h-20 text-sm leading-relaxed"
                rows={3}
              />
            </div>
            <Button
              size="lg"
              className="w-full h-12 rounded-xl font-semibold"
              onClick={handleComplete}
            >
              <CheckCircle2 className="h-4 w-4" />
              실험 완료하기
            </Button>
          </div>
        )}

        {experiment.status === 'completed' && (
          <div className="flex items-center gap-2 py-1">
            <Badge className="bg-sage-500 text-white border-sage-500">완료</Badge>
            {experiment.userResult && (
              <p className="text-sm text-muted-foreground flex-1">&ldquo;{experiment.userResult}&rdquo;</p>
            )}
          </div>
        )}

        {experiment.status === 'declined' && (
          <div className="flex flex-col items-center gap-3 py-2">
            <Badge variant="outline" className="text-muted-foreground">
              건너뛰기
            </Badge>
            <button
              type="button"
              className="min-h-[44px] text-sm text-primary font-medium hover:underline transition-colors"
              onClick={handleRetry}
            >
              다시 시도하기
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function Mirror() {
  const weeklyMirrors = useNabomStore((s) => s.weeklyMirrors);
  const currentReflection = useNabomStore((s) => s.currentReflection);
  const experiments = useNabomStore((s) => s.experiments);
  const generateReflection = useNabomStore((s) => s.generateReflection);
  const reflectionGenerating = useNabomStore((s) => s.reflectionGenerating);
  const reflectionError = useNabomStore((s) => s.reflectionError);

  // Get the latest mirror
  const mirror = weeklyMirrors.length > 0 ? weeklyMirrors[weeklyMirrors.length - 1] : null;

  // 실험 상태는 experiments 컬렉션이 최신 (mirror 스냅샷보다 우선)
  const liveExperiment = useMemo(() => {
    if (!mirror?.growthExperiment) return null;
    const fresh = experiments.find((e) => e.experimentId === mirror.growthExperiment!.experimentId);
    return fresh ?? mirror.growthExperiment;
  }, [mirror, experiments]);

  // Empty state
  if (!mirror) {
    return (
      <main className="min-h-screen flex flex-col bg-background">
        <div className="nabom-page">
          <motion.div
            {...(noMotion()
              ? {}
              : {
                  initial: { opacity: 0, y: 20 },
                  animate: { opacity: 1, y: 0 },
                  transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] as const },
                })}
            className="flex flex-col items-center text-center space-y-4 pt-10"
          >
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-warm-100">
              <CalendarDays className="h-7 w-7 text-warm-400" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              아직 주간 거울이 없어요
            </h1>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-xs">
              일상을 매일 기록하면,
              <br />
              일주일이 모일 때마다 나의 모습이 선명해져요.
            </p>
            <Button
              size="lg"
              className="w-full h-12 rounded-xl text-base font-semibold shadow-md"
              disabled={reflectionGenerating}
              onClick={() => {
                void (async () => {
                  const ok = await generateReflection();
                  if (!ok) toast.error('회고를 만들지 못했어요. 기록이 있는지 확인해주세요.');
                })();
              }}
            >
              <Sparkles className="h-4 w-4" />
              {reflectionGenerating ? '회고를 만드는 중…' : '이번 주 회고 만들기'}
            </Button>
            {reflectionError && (
              <p className="text-sm text-warm-600">{reflectionError}</p>
            )}
          </motion.div>
        </div>
      </main>
    );
  }

  const periodLabel = `${formatPeriodDate(mirror.period.from)} — ${formatPeriodDate(mirror.period.to)}`;

  return (
    <main className="min-h-screen flex flex-col bg-background">
      <div className="nabom-page">
        {/* ── Header ─────────────────────────────────────────────────────── */}
        <motion.div {...fadeUp(0)} className="mb-5">
          <div className="flex items-center gap-3 mb-1.5">
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              이번 주의 나
            </h1>
            <Badge
              variant={COVERAGE_VARIANT[mirror.coverage.mode] ?? 'outline'}
              className="text-xs"
            >
              {COVERAGE_LABEL[mirror.coverage.mode] ?? mirror.coverage.mode}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">{periodLabel}</p>
        </motion.div>

        {/* ── Summary Card ──────────────────────────────────────────────── */}
        <motion.div {...fadeUp(0.05)} className="mb-5">
          <Card className="border-primary/20 bg-gradient-to-br from-warm-50 to-sage-50/30 shadow-sm">
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="h-4 w-4 text-primary" />
                <p className="text-xs font-semibold tracking-wide text-primary uppercase">
                  이번 주 한 문장
                </p>
              </div>
              <p className="text-base font-medium leading-relaxed text-foreground">
                {mirror.summary}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Emotion Flow ──────────────────────────────────────────────── */}
        <motion.div {...fadeUp(0.1)} className="mb-5">
          <Card className="border-border/50 shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <CircleDot className="h-4 w-4 text-warm-500" />
                <CardTitle className="text-base">감정 흐름</CardTitle>
              </div>
              <CardDescription>일주일 동안의 기분 변화예요</CardDescription>
            </CardHeader>
            <CardContent>
              <EmotionFlow emotionFlow={mirror.emotionFlow} />
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Energy Gainers / Drainers ──────────────────────────────────── */}
        <motion.div {...fadeUp(0.14)} className="mb-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Gainers */}
            <Card className="border-sage-200/50 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <Leaf className="h-4 w-4 text-sage-500" />
                  <CardTitle className="text-base">에너지를 채운 것</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {mirror.energyGainers.map((item, i) => (
                    <motion.div
                      key={i}
                      {...staggerChild(0.06 * i)}
                      className="flex items-center gap-2.5 rounded-lg bg-sage-50/60 px-3 py-2.5"
                    >
                      <Leaf className="h-3.5 w-3.5 shrink-0 text-sage-400" />
                      <span className="text-sm text-foreground">{item}</span>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Drainers */}
            <Card className="border-warm-200/50 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-warm-500" />
                  <CardTitle className="text-base">에너지를 빼앗은 것</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {mirror.energyDrainers.map((item, i) => (
                    <motion.div
                      key={i}
                      {...staggerChild(0.06 * i)}
                      className="flex items-center gap-2.5 rounded-lg bg-warm-50/80 px-3 py-2.5"
                    >
                      <AlertCircle className="h-3.5 w-3.5 shrink-0 text-warm-400" />
                      <span className="text-sm text-foreground">{item}</span>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </motion.div>

        {/* ── Changes from last week ─────────────────────────────────────── */}
        {mirror.changesFromLastWeek.length > 0 && (
          <motion.div {...fadeUp(0.18)} className="mb-5">
            <Card className="border-border/50 shadow-sm">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <ArrowRight className="h-4 w-4 text-primary" />
                  <CardTitle className="text-base">지난 주와의 변화</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mirror.changesFromLastWeek.map((change, i) => (
                    <motion.div
                      key={i}
                      {...staggerChild(0.06 * i)}
                      className="flex items-start gap-3"
                    >
                      <ArrowRight className="mt-0.5 h-4 w-4 shrink-0 text-warm-400" />
                      <p className="text-sm leading-relaxed text-foreground">{change}</p>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* ── Expandable Sections (Accordion) ───────────────────────────── */}
        <motion.div {...fadeUp(0.22)} className="mb-5">
          <Accordion type="multiple" className="w-full">
            {/* Notable Moments */}
            <AccordionItem value="notable-moments" className="border-border/50">
              <AccordionTrigger className="text-base font-semibold text-foreground hover:no-underline">
                <div className="flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-warm-400" />
                  기억할 만한 순간
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-3">
                  {mirror.notableMoments.map((moment, i) => (
                    <motion.div
                      key={i}
                      {...staggerChild(0.05 * i)}
                      className="flex items-start gap-3 rounded-lg bg-muted/40 px-4 py-3"
                    >
                      <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-warm-400" />
                      <p className="text-sm leading-relaxed text-foreground">{moment}</p>
                    </motion.div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* Patterns */}
            <AccordionItem value="patterns" className="border-border/50">
              <AccordionTrigger className="text-base font-semibold text-foreground hover:no-underline">
                <div className="flex items-center gap-2">
                  <ChevronRight className="h-4 w-4 text-terra-400" />
                  발견된 패턴
                  <Badge variant="secondary" className="text-xs ml-1">
                    {mirror.patterns.length}
                  </Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  {mirror.patterns.map((pattern, i) => {
                    const confLabel = CONFIDENCE_LABEL(pattern.confidence);
                    const needsConfirmation = pattern.confidence < 0.5;
                    return (
                      <motion.div
                        key={i}
                        {...staggerChild(0.06 * i)}
                        className="rounded-xl border border-border/60 bg-card p-4 space-y-2"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm font-semibold text-foreground">{pattern.title}</p>
                          <div className="flex items-center gap-1.5 shrink-0">
                            <Badge variant="outline" className="text-[10px]">
                              증거 {pattern.evidenceCount}건
                            </Badge>
                          </div>
                        </div>
                        <p className="text-sm leading-relaxed text-foreground/80">{pattern.description}</p>
                        {confLabel && (
                          <p className="text-xs text-muted-foreground italic">{confLabel}</p>
                        )}
                        {needsConfirmation && (
                          <p className="text-xs text-warm-500 font-medium">
                            아직 확인이 필요해요
                          </p>
                        )}
                      </motion.div>
                    );
                  })}
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* Hypotheses */}
            <AccordionItem value="hypotheses" className="border-border/50">
              <AccordionTrigger className="text-base font-semibold text-foreground hover:no-underline">
                <div className="flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-sage-500" />
                  가설
                  <Badge variant="secondary" className="text-xs ml-1">
                    {mirror.hypotheses.length}
                  </Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  {mirror.hypotheses.map((hypothesis, i) => {
                    const isHighConfidence = hypothesis.confidence >= 0.7;
                    return (
                      <motion.div
                        key={i}
                        {...staggerChild(0.06 * i)}
                        className="rounded-xl border border-border/60 bg-card p-4 space-y-2"
                      >
                        <p className="text-sm font-semibold text-foreground">{hypothesis.title}</p>
                        <p className="text-sm leading-relaxed text-foreground/80">
                          {hypothesis.description}
                        </p>
                        <Separator className="my-2" />
                        <p className="text-sm text-muted-foreground">
                          {isHighConfidence
                            ? '여러 기록에서 이 가설을 지지하는 증거가 꽤 모였어요. 당신에게도 맞게 느껴지나요?'
                            : '이 가설이 당신에게도 맞게 느껴지나요?'}
                        </p>
                      </motion.div>
                    );
                  })}
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* Reflection (if exists) */}
            {currentReflection && (
              <AccordionItem value="reflection" className="border-border/50">
                <AccordionTrigger className="text-base font-semibold text-foreground hover:no-underline">
                  <div className="flex items-center gap-2">
                    <Eye className="h-4 w-4 text-primary" />
                    이번 주의 흐름
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-5">
                    {/* Situation */}
                    <div className="rounded-xl bg-warm-50/80 border border-warm-100/80 p-4 space-y-2">
                      <p className="text-xs font-semibold tracking-wide text-warm-600 uppercase">
                        이번 주의 흐름
                      </p>
                      <p className="text-sm font-medium text-foreground">
                        {currentReflection.situation.labelKo}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        신뢰도 {Math.round(currentReflection.situation.confidence * 100)}%
                      </p>
                    </div>

                    {/* Observation Focus */}
                    <div className="space-y-2">
                      <p className="text-xs font-semibold tracking-wide text-sage-600 uppercase">
                        살펴볼 관찰 초점
                      </p>
                      <div className="space-y-2">
                        {currentReflection.observationFocus.map((focus, i) => (
                          <div
                            key={i}
                            className="flex items-start gap-2.5 rounded-lg bg-sage-50/60 px-3 py-2.5"
                          >
                            <div className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sage-400" />
                            <span className="text-sm text-foreground">{focus}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Caution Signals — warm/amber, NOT red */}
                    {currentReflection.cautionSignals.length > 0 && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Shield className="h-3.5 w-3.5 text-warm-500" />
                          <p className="text-xs font-semibold tracking-wide text-warm-600 uppercase">
                            주의 신호
                          </p>
                        </div>
                        <div className="space-y-2">
                          {currentReflection.cautionSignals.map((signal, i) => (
                            <div
                              key={i}
                              className="flex items-start gap-2.5 rounded-lg bg-warm-50/60 border border-warm-100/60 px-3 py-2.5"
                            >
                              <Shield className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warm-400" />
                              <span className="text-sm text-foreground">{signal}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            )}
          </Accordion>
        </motion.div>

        {/* ── Growth Experiment Section ──────────────────────────────────── */}
        {liveExperiment && (
          <motion.div {...fadeUp(0.28)} className="mb-5">
            <Card className="border-primary/20 shadow-sm">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <FlaskConical className="h-4 w-4 text-primary" />
                  <CardTitle className="text-base">성장 실험</CardTitle>
                </div>
                <CardDescription>
                  이번 주 제안하는 작은 실험이에요. 부담 없이 시도해 보세요.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ExperimentSection experiment={liveExperiment} />
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>
    </main>
  );
}
