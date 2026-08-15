'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale/ko';
import {
  Heart,
  CheckCircle2,
  Eye,
  Leaf,
  Send,
  Sparkles,
  Star,
  Shield,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { useNabomStore } from '@/store/nabom-store';
import type { ProfileFeedback } from '@/types/nabom';
import { CONFIDENCE_LABEL } from '@/types/nabom';
import { profileVersionLabel } from '@/lib/profile-label';
import { characterImagePath } from '@/lib/character-visual';

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

// ─── Element → Gradient Mapping ──────────────────────────────────────────────

const ELEMENT_GRADIENTS: Record<string, { bg: string; ring: string; text: string }> = {
  fire: {
    bg: 'bg-gradient-to-br from-terra-200/80 via-warm-100 to-terra-100/40',
    ring: 'ring-terra-200/50',
    text: 'text-terra-700',
  },
  wood: {
    bg: 'bg-gradient-to-br from-sage-200/80 via-sage-100/60 to-warm-100/40',
    ring: 'ring-sage-200/50',
    text: 'text-sage-700',
  },
  earth: {
    bg: 'bg-gradient-to-br from-warm-200/80 via-warm-100 to-warm-50',
    ring: 'ring-warm-200/50',
    text: 'text-warm-700',
  },
  metal: {
    bg: 'bg-gradient-to-br from-warm-200/60 via-muted to-warm-100/40',
    ring: 'ring-warm-200/40',
    text: 'text-warm-800',
  },
  water: {
    bg: 'bg-gradient-to-br from-warm-100/80 via-sage-100/50 to-warm-50',
    ring: 'ring-sage-100/50',
    text: 'text-sage-800',
  },
};

// ─── Feedback Options ────────────────────────────────────────────────────────

interface FeedbackOption {
  value: ProfileFeedback['rating'];
  label: string;
}

const FEEDBACK_OPTIONS: FeedbackOption[] = [
  { value: 'correct', label: '맞아요' },
  { value: 'mostly_correct', label: '어느 정도 맞아요' },
  { value: 'situational', label: '상황에 따라 달라요' },
  { value: 'unsure', label: '잘 모르겠어요' },
  { value: 'incorrect', label: '아니에요' },
];

// ─── Trait Bar Component ────────────────────────────────────────────────────

interface TraitBarProps {
  labelKo: string;
  value: number;
  confidence: number;
  index: number;
}

function TraitBar({ labelKo, value, confidence, index }: TraitBarProps) {
  const percentage = Math.round(value * 100);
  const confLabel = CONFIDENCE_LABEL(confidence);
  const isHighConfidence = confidence >= 0.7;
  const isLowConfidence = confidence < 0.3;
  const isVeryHighConfidence = confidence >= 0.85;

  // Color based on value
  const barColor =
    value >= 0.7
      ? 'bg-primary'
      : value >= 0.5
        ? 'bg-warm-500'
        : 'bg-warm-300';

  return (
    <motion.div {...staggerChild(0.06 * index)} className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground">{labelKo}</span>
          {isHighConfidence && (
            <Star className="h-3 w-3 text-terra-400" aria-label="높은 신뢰도" />
          )}
        </div>
        <span className="text-sm font-semibold tabular-nums text-warm-700">
          {percentage}%
        </span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-muted">
        <motion.div
          className={`h-full rounded-full ${barColor}`}
          {...(noMotion()
            ? { style: { width: `${percentage}%` } }
            : {
                initial: { width: 0 },
                animate: { width: `${percentage}%` },
                transition: {
                  duration: 0.8,
                  delay: 0.3 + 0.06 * index,
                  ease: [0.22, 1, 0.36, 1] as const,
                },
              })}
        />
      </div>
      <div className="flex items-center gap-2 min-h-[20px]">
        {confLabel && (
          <span className="text-xs text-muted-foreground">{confLabel}</span>
        )}
      </div>
    </motion.div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function Profile() {
  const { currentProfile, characterProfile, submitFeedbackViaApi, feedbackSubmitting } =
    useNabomStore();

  // Feedback state
  const [selectedRating, setSelectedRating] = useState<ProfileFeedback['rating'] | null>(null);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [feedbackSent, setFeedbackSent] = useState(false);

  // Element gradient
  const element = characterProfile?.representativeElement ?? 'earth';
  const gradient = ELEMENT_GRADIENTS[element] ?? ELEMENT_GRADIENTS.earth;

  // Format creation date
  const createdDate = useMemo(() => {
    if (!currentProfile?.createdAt) return '';
    try {
      return format(new Date(currentProfile.createdAt), 'yyyy년 M월 d일', {
        locale: ko,
      });
    } catch {
      return '';
    }
  }, [currentProfile]);

  // Handle feedback submit
  const handleFeedbackSubmit = async () => {
    if (!selectedRating || !currentProfile || feedbackSubmitting) return;

    const ok = await submitFeedbackViaApi({
      profileVersionId: currentProfile.profileVersionId,
      targetType: 'overall',
      targetKey: 'overall',
      rating: selectedRating,
      comment: feedbackComment.trim(),
    });

    if (!ok) {
      toast.error('피드백을 보내지 못했어요. 잠시 후 다시 시도해주세요.');
      return;
    }

    setFeedbackSent(true);
    toast.success('피드백을 보냈어요. 프로필이 더 정확해질 거예요.');
  };

  // Null/empty states
  if (!currentProfile) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center bg-background px-6">
        <div className="text-center space-y-4">
          <Leaf className="mx-auto h-10 w-10 text-warm-300" />
          <h1 className="text-xl font-bold text-foreground">아직 프로필이 없어요</h1>
          <p className="text-sm text-muted-foreground">
            일상을 기록하면 프로필이 만들어져요.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col bg-background">
      <div className="nabom-page">
        {/* ── Header ─────────────────────────────────────────────────────── */}
        <motion.div {...fadeUp(0)} className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              내 프로필
            </h1>
            <Badge variant="secondary" className="text-xs">
              {profileVersionLabel(currentProfile.number)}
            </Badge>
          </div>
          {createdDate && (
            <p className="text-sm text-muted-foreground">
              {createdDate} 생성
            </p>
          )}
        </motion.div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">

        {/* ── Character Hero (bento hero, span 2) ──────────────────────── */}
        <motion.div {...fadeUp(0.05)} className="md:col-span-2">
          <Card className="border-border/50 shadow-sm overflow-hidden">
            <CardContent className="p-0">
              <div className={`flex flex-col items-start gap-4 p-5 sm:flex-row sm:items-center ${gradient.bg}`}>
                {(() => {
                  const imageUrl =
                    characterProfile?.imageGifUrl ||
                    characterProfile?.imageUrl ||
                    (characterProfile?.visualKey
                      ? characterImagePath(characterProfile.visualKey)
                      : characterProfile?.guardianBeast.code
                        ? characterImagePath(characterProfile.guardianBeast.code)
                        : '');
                  // GIF가 있으면 자체 루프 애니메이션 (스프라이트). 없으면 정적 PNG.
                  const isGif = characterProfile?.imageGifUrl != null;
                  return imageUrl ? (
                    <motion.div
                      className="h-28 w-20 shrink-0"
                      animate={isGif ? {} : { y: [0, -6, 0], rotate: [0, 1.5, 0] }}
                      transition={{
                        duration: 3.2,
                        repeat: Infinity,
                        ease: 'easeInOut',
                      }}
                    >
                      <img
                        src={imageUrl}
                        alt={characterProfile?.guardianBeast.labelKo ?? '나의 캐릭터'}
                        className="h-28 w-20 object-contain drop-shadow-md"
                      />
                    </motion.div>
                  ) : (
                    <div
                      className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-full ${gradient.bg} ring-4 ${gradient.ring} shadow-lg`}
                    >
                      <Sparkles className={`h-7 w-7 ${gradient.text}`} />
                    </div>
                  );
                })()}
                <div className="min-w-0">
                  <p className={`text-lg font-bold ${gradient.text}`}>
                    {characterProfile?.guardianBeast.labelKo ?? '지금의 나'}
                  </p>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    {characterProfile?.stageName && (
                      <Badge
                        variant="outline"
                        className="border-primary/30 bg-background/60 text-xs font-medium text-warm-700"
                      >
                        {characterProfile.stageName}
                      </Badge>
                    )}
                    {characterProfile?.stage && (
                      <span className="text-xs text-warm-600 tabular-nums">
                        {characterProfile.stage}단계
                      </span>
                    )}
                    {characterProfile?.conditionLabel && (
                      <span className="text-xs text-warm-600">
                        · {characterProfile.conditionLabel}
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-foreground/80">
                    {currentProfile.identitySentence}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Traits Section ────────────────────────────────────────────── */}
        <motion.div {...fadeUp(0.12)} className="h-full">
          <Card className="h-full border-border/50 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">특성</CardTitle>
              <CardDescription>
                기록을 바탕으로 발견된 나의 성향이에요
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {currentProfile.traits.map((trait, i) => (
                <TraitBar
                  key={trait.trait}
                  labelKo={trait.labelKo}
                  value={trait.value}
                  confidence={trait.confidence}
                  index={i}
                />
              ))}
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Strengths Section ─────────────────────────────────────────── */}
        <motion.div {...fadeUp(0.18)}>
          <Card className="h-full border-sage-200/50 shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Heart className="h-4 w-4 text-sage-500" />
                <CardTitle className="text-base">나의 강점</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {currentProfile.strengths.map((strength, i) => (
                  <motion.div
                    key={i}
                    {...staggerChild(0.08 * i)}
                    className="flex items-start gap-3 rounded-xl bg-sage-50/60 border border-sage-100/80 p-4"
                  >
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-sage-500" />
                    <p className="text-sm leading-relaxed text-foreground">
                      {strength}
                    </p>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Watch Patterns Section ────────────────────────────────────── */}
        <motion.div {...fadeUp(0.24)}>
          <Card className="h-full border-warm-200/50 shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-warm-500" />
                <CardTitle className="text-base">관찰 포인트</CardTitle>
              </div>
              <CardDescription>
                살펴보면 좋을 패턴이에요. 부정적인 게 아니에요.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {currentProfile.watchPatterns.map((pattern, i) => (
                  <motion.div
                    key={i}
                    {...staggerChild(0.08 * i)}
                    className="flex items-start gap-3 rounded-xl bg-warm-50/80 border border-warm-100/80 p-4"
                  >
                    <Shield className="mt-0.5 h-5 w-5 shrink-0 text-warm-400" />
                    <p className="text-sm leading-relaxed text-foreground">
                      {pattern}
                    </p>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Profile Lenses (bento wide, span 2) ──────────────────────── */}
        {currentProfile.lenses && (
          <motion.div {...fadeUp(0.28)} className="md:col-span-2">
            <Card className="border-border/50 shadow-sm">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-warm-500" />
                  <CardTitle className="text-base">나를 보는 다양한 각도</CardTitle>
                </div>
                <CardDescription>
                  출생 정보 기반 초기 가설이에요. 기록이 쌓이면 더 선명해져요.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {currentProfile.lenses.headline.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {currentProfile.lenses.headline.map((keyword) => (
                      <span
                        key={keyword}
                        className="rounded-full border border-primary/30 bg-warm-50 px-3 py-1.5 text-sm font-semibold text-primary"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                )}

                {/* 3분 요약 (fatemirror 구조) */}
                {currentProfile.lenses.summary && (
                  <div className="grid gap-2.5 sm:grid-cols-3">
                    {[
                      currentProfile.lenses.summary.movingForce,
                      currentProfile.lenses.summary.adjustPoint,
                      currentProfile.lenses.summary.todayAction,
                    ].map((block) => (
                      <div
                        key={block.title}
                        className="rounded-xl bg-gradient-to-br from-warm-50 to-sage-50/30 border border-warm-100/60 p-4"
                      >
                        <p className="text-xs font-semibold tracking-wide text-primary uppercase">
                          {block.title}
                        </p>
                        <p className="mt-1.5 text-sm leading-relaxed text-foreground">
                          {block.body}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                {/* 잘 쓰이면 / 과하면 (fatemirror 이진 구조) */}
                {currentProfile.lenses.patternBalance && (
                  <div className="grid gap-2.5 sm:grid-cols-2">
                    <div className="rounded-xl border border-sage-200/70 bg-sage-50/60 p-4">
                      <p className="text-xs font-semibold tracking-wide text-sage-600 uppercase">
                        {currentProfile.lenses.patternBalance.good.title}
                      </p>
                      <p className="mt-1.5 text-sm leading-relaxed text-foreground">
                        {currentProfile.lenses.patternBalance.good.body}
                      </p>
                    </div>
                    <div className="rounded-xl border border-warm-200/70 bg-warm-50/70 p-4">
                      <p className="text-xs font-semibold tracking-wide text-warm-600 uppercase">
                        {currentProfile.lenses.patternBalance.over.title}
                      </p>
                      <p className="mt-1.5 text-sm leading-relaxed text-foreground">
                        {currentProfile.lenses.patternBalance.over.body}
                      </p>
                    </div>
                  </div>
                )}

                {/* 나머지 렌즈 5블록 */}
                <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
                  {[
                    currentProfile.lenses.energyStyle,
                    currentProfile.lenses.elementStyle,
                    currentProfile.lenses.seasonRhythm,
                    currentProfile.lenses.relationStyle,
                    currentProfile.lenses.rootSupport,
                  ].map(
                    (block, i) =>
                      block && (
                        <div
                          key={`${block.title}-${i}`}
                          className="rounded-xl border border-border/60 bg-card p-4"
                        >
                          <p className="text-xs font-semibold tracking-wide text-warm-500 uppercase">
                            {block.title}
                          </p>
                          <p className="mt-1.5 text-sm leading-relaxed text-foreground">
                            {block.body}
                          </p>
                        </div>
                      ),
                  )}
                </div>

                {/* 계산 안정도 (fatemirror 구조) */}
                {currentProfile.lenses.stability && (
                  <div className="rounded-xl border border-border/60 bg-muted/30 p-4">
                    <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase mb-1.5">
                      {currentProfile.lenses.stability.title}
                    </p>
                    <p className="text-sm leading-relaxed text-foreground/80">
                      {currentProfile.lenses.stability.body}
                    </p>
                  </div>
                )}

                {currentProfile.lenses.attentionPoints.length > 0 && (
                  <div className="rounded-xl border border-warm-200/60 bg-warm-50/70 p-4">
                    <p className="text-xs font-semibold tracking-wide text-warm-500 uppercase mb-2">
                      주의 신호
                    </p>
                    <ul className="space-y-1.5">
                      {currentProfile.lenses.attentionPoints.map((point) => (
                        <li key={point} className="flex items-start gap-2 text-sm text-warm-800">
                          <Shield className="mt-0.5 h-4 w-4 shrink-0 text-warm-400" />
                          {point}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* ── Growth Theme ──────────────────────────────────────────────── */}
        <motion.div {...fadeUp(0.3)} className="h-full">
          <Card className="border-primary/20 bg-gradient-to-br from-warm-50 to-sage-50/40 shadow-sm">
            <CardContent className="p-6">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="h-5 w-5 text-primary" />
                <p className="text-xs font-semibold tracking-wide text-primary uppercase">
                  지금의 성장 주제
                </p>
              </div>
              <p className="text-lg font-semibold leading-relaxed text-foreground">
                {currentProfile.growthTheme}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Feedback Section (bento wide, span 2) ────────────────────── */}
        <motion.div {...fadeUp(0.35)} className="md:col-span-2">
          <Card className="border-border/50 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">
                이 설명이 나와 얼마나 비슷한가요?
              </CardTitle>
              <CardDescription>
                피드백은 프로필을 더 정확하게 만들어줘요
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {feedbackSent ? (
                <motion.div
                  {...(noMotion()
                    ? {}
                    : {
                        initial: { opacity: 0, scale: 0.97 },
                        animate: { opacity: 1, scale: 1 },
                        transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] as const },
                      })}
                  className="text-center py-4"
                >
                  <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-sage-100">
                    <CheckCircle2 className="h-6 w-6 text-sage-600" />
                  </div>
                  <p className="text-sm font-medium text-sage-700">
                    소중한 피드백 감사해요!
                  </p>
                </motion.div>
              ) : (
                <>
                  {/* Radio options */}
                  <div className="space-y-2">
                    {FEEDBACK_OPTIONS.map((option) => {
                      const isSelected = selectedRating === option.value;
                      return (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => setSelectedRating(option.value)}
                          className={`flex w-full items-center gap-3 rounded-xl border p-4 text-left text-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring min-h-[44px] ${
                            isSelected
                              ? 'border-primary bg-warm-50 text-foreground ring-1 ring-primary/20'
                              : 'border-border/60 bg-card text-foreground hover:bg-muted/50'
                          }`}
                          aria-pressed={isSelected}
                        >
                          {/* Custom radio indicator */}
                          <div
                            className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
                              isSelected
                                ? 'border-primary bg-primary'
                                : 'border-muted-foreground/40'
                            }`}
                          >
                            {isSelected && (
                              <div className="h-2 w-2 rounded-full bg-primary-foreground" />
                            )}
                          </div>
                          <span className="font-medium">{option.label}</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Optional comment */}
                  <div className="space-y-2">
                    <label
                      htmlFor="feedback-comment"
                      className="text-sm font-medium text-foreground"
                    >
                      추가 의견 (선택)
                    </label>
                    <Textarea
                      id="feedback-comment"
                      placeholder="더 자세히 말하고 싶다면 적어주세요"
                      value={feedbackComment}
                      onChange={(e) => setFeedbackComment(e.target.value)}
                      className="min-h-20 text-sm leading-relaxed placeholder:text-muted-foreground/60"
                      rows={3}
                    />
                  </div>

                  {/* Submit */}
                  <Button
                    size="lg"
                    className="w-full h-12 rounded-xl text-base font-semibold shadow-md transition-all hover:shadow-lg active:scale-[0.98] disabled:opacity-40"
                    disabled={!selectedRating || feedbackSubmitting}
                    onClick={handleFeedbackSubmit}
                  >
                    <Send className="h-4 w-4" />
                    {feedbackSubmitting ? '보내는 중…' : '피드백 보내기'}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </motion.div>
        </div>
      </div>
    </main>
  );
}
