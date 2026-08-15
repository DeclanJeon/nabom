'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale/ko';
import {
  TrendingUp,
  TrendingDown,
  Leaf,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Sparkles,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useNabomStore } from '@/store/nabom-store';
import { TRAIT_LABELS } from '@/types/nabom';
import type { ProfileVersion, TraitState } from '@/types/nabom';
import { profileVersionChangeLabel, profileVersionLabel } from '@/lib/profile-label';

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

function formatDate(dateStr: string): string {
  try {
    return format(new Date(dateStr), 'yyyy년 M월 d일', { locale: ko });
  } catch {
    return dateStr;
  }
}

function barColor(value: number): string {
  if (value >= 0.7) return 'bg-primary';
  if (value >= 0.5) return 'bg-warm-500';
  return 'bg-warm-300';
}

interface TraitDelta {
  trait: string;
  labelKo: string;
  prev: number;
  curr: number;
  delta: number;
}

function computeDeltas(prev: ProfileVersion, curr: ProfileVersion): TraitDelta[] {
  const deltas: TraitDelta[] = [];
  const prevMap = new Map(prev.traits.map((t) => [t.trait, t]));

  for (const ct of curr.traits) {
    const pt = prevMap.get(ct.trait);
    if (pt) {
      const delta = ct.value - pt.value;
      if (Math.abs(delta) >= 0.01) {
        deltas.push({
          trait: ct.trait,
          labelKo: ct.labelKo,
          prev: pt.value,
          curr: ct.value,
          delta,
        });
      }
    }
  }

  // Sort by absolute delta descending
  deltas.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
  return deltas;
}

// ─── Compact Trait Bar ───────────────────────────────────────────────────────

function CompactTraitBar({ label, value, index }: { label: string; value: number; index: number }) {
  const pct = Math.round(value * 100);
  return (
    <motion.div {...staggerChild(0.04 * index)} className="flex items-center gap-2">
      <span className="text-xs text-muted-foreground w-8 shrink-0 text-right">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
        <motion.div
          className={`h-full rounded-full ${barColor(value)}`}
          {...(noMotion()
            ? { style: { width: `${pct}%` } }
            : {
                initial: { width: 0 },
                animate: { width: `${pct}%` },
                transition: { duration: 0.6, delay: 0.2 + 0.04 * index, ease: [0.22, 1, 0.36, 1] as const },
              })}
        />
      </div>
      <span className="text-[10px] tabular-nums text-muted-foreground w-7 shrink-0">{pct}%</span>
    </motion.div>
  );
}

// ─── Delta Indicator ─────────────────────────────────────────────────────────

function DeltaIndicator({ delta }: { delta: number }) {
  if (delta > 0.01) {
    return (
      <span className="inline-flex items-center gap-0.5 text-xs font-medium text-sage-600">
        <ArrowUpRight className="h-3.5 w-3.5" />
        +{Math.round(delta * 100)}
      </span>
    );
  }
  if (delta < -0.01) {
    return (
      <span className="inline-flex items-center gap-0.5 text-xs font-medium text-warm-600">
        <ArrowDownRight className="h-3.5 w-3.5" />
        {Math.round(delta * 100)}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-0.5 text-xs text-muted-foreground">
      <Minus className="h-3.5 w-3.5" />
      0
    </span>
  );
}

// ─── Trait Evolution Chart ───────────────────────────────────────────────────

function TraitEvolutionChart({ versions }: { versions: ProfileVersion[] }) {
  // Collect all traits across versions
  const allTraits = useMemo(() => {
    const traitSet = new Set<string>();
    versions.forEach((v) => v.traits.forEach((t) => traitSet.add(t.trait)));
    return Array.from(traitSet);
  }, [versions]);

  if (allTraits.length === 0) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <TrendingUp className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-semibold text-foreground">특성 변화 추이</h3>
      </div>
      <div className="space-y-3">
        {allTraits.map((trait, ti) => {
          const label = TRAIT_LABELS[trait] ?? trait;
          return (
            <motion.div
              key={trait}
              {...staggerChild(0.05 * ti)}
              className="space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-foreground">{label}</span>
              </div>
              <div className="flex items-center gap-1.5">
                {versions.map((v, vi) => {
                  const t = v.traits.find((tr) => tr.trait === trait);
                  const val = t ? Math.round(t.value * 100) : 0;
                  return (
                    <div key={v.profileVersionId} className="flex-1 space-y-0.5">
                      <div className="h-3 w-full overflow-hidden rounded-sm bg-muted/60">
                        <motion.div
                          className={`h-full rounded-sm ${barColor(t?.value ?? 0)}`}
                          {...(noMotion()
                            ? { style: { width: `${val}%` } }
                            : {
                                initial: { width: 0 },
                                animate: { width: `${val}%` },
                                transition: {
                                  duration: 0.7,
                                  delay: 0.3 + 0.05 * ti + 0.1 * vi,
                                  ease: [0.22, 1, 0.36, 1] as const,
                                },
                              })}
                        />
                      </div>
                      <span className="text-[9px] tabular-nums text-muted-foreground block text-center">
                        {val}%
                      </span>
                    </div>
                  );
                })}
              </div>
              {/* Version labels under the last trait only */}
              {ti === allTraits.length - 1 && (
                <div className="flex items-center gap-1.5 mt-1">
                  {versions.map((v) => (
                    <span
                      key={v.profileVersionId}
                      className="flex-1 text-[9px] text-muted-foreground text-center"
                    >
                      {profileVersionLabel(v.number, { compact: true })}
                    </span>
                  ))}
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function Journey() {
  const profileVersions = useNabomStore((s) => s.profileVersions);
  const currentProfile = useNabomStore((s) => s.currentProfile);

  const sortedVersions = useMemo(
    () => [...profileVersions].sort((a, b) => a.number - b.number),
    [profileVersions],
  );

  const totalVersions = sortedVersions.length;
  const latestVersion = sortedVersions[sortedVersions.length - 1];
  const hasMultiple = totalVersions >= 2;

  // Only 1 version — show encouragement
  if (!hasMultiple) {
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
              <Clock className="h-7 w-7 text-warm-400" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              나의 여정
            </h1>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-xs">
              아직 첫 프로필이 생성되었어요.
              <br />
              시간이 지나면 여기서 변화를 볼 수 있어요.
            </p>
            <div className="rounded-xl bg-warm-50/70 border border-warm-100/70 px-5 py-3">
              <p className="text-sm text-warm-700 font-medium">
                기록이 쌓일수록 더 선명해질 거예요.
              </p>
            </div>
          </motion.div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col bg-background">
      <div className="nabom-page">
        {/* ── Header ─────────────────────────────────────────────────────── */}
        <motion.div {...fadeUp(0)} className="mb-5">
          <h1 className="text-3xl font-bold tracking-tight text-foreground mb-1.5">
            나의 여정
          </h1>
          <p className="text-sm text-muted-foreground">
            총 {totalVersions}개의 프로필
          </p>
        </motion.div>

        {/* ── Timeline View ──────────────────────────────────────────────── */}
        <div className="relative mb-6">
          {/* Vertical connecting line */}
          <div className="absolute left-[19px] top-8 bottom-8 w-px bg-border/60" aria-hidden="true" />

          <div className="space-y-5">
            {sortedVersions.map((version, vi) => {
              const isLatest = version.number === latestVersion?.number;
              const prevVersion = vi > 0 ? sortedVersions[vi - 1] : null;
              const deltas = prevVersion ? computeDeltas(prevVersion, version) : [];
              const topTraits = [...version.traits]
                .sort((a, b) => b.value - a.value)
                .slice(0, 3);

              return (
                <motion.div
                  key={version.profileVersionId}
                  {...(noMotion()
                    ? {}
                    : {
                        initial: { opacity: 0, x: -20 },
                        animate: { opacity: 1, x: 0 },
                        transition: {
                          duration: 0.5,
                          delay: 0.1 * vi,
                          ease: [0.22, 1, 0.36, 1] as const,
                        },
                      })}
                  className="relative pl-12"
                >
                  {/* Timeline node */}
                  <div
                    className={`absolute left-[12px] top-6 z-10 flex h-[15px] w-[15px] items-center justify-center rounded-full border-2 transition-colors ${
                      isLatest
                        ? 'border-primary bg-primary'
                        : 'border-warm-300 bg-background'
                    }`}
                    aria-hidden="true"
                  >
                    {isLatest && (
                      <div className="h-[5px] w-[5px] rounded-full bg-primary-foreground" />
                    )}
                  </div>

                  <Card
                    className={`shadow-sm transition-colors ${
                      isLatest
                        ? 'border-primary/30 bg-card'
                        : 'border-border/50 bg-card/70 opacity-80'
                    }`}
                  >
                    <CardHeader>
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={isLatest ? 'default' : 'secondary'}
                            className="text-xs"
                          >
                            {profileVersionLabel(version.number)}
                          </Badge>
                          {isLatest && (
                            <Badge variant="outline" className="text-xs border-sage-300 text-sage-600">
                              최신
                            </Badge>
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {formatDate(version.createdAt)}
                        </span>
                      </div>
                      <CardDescription className="mt-2 text-sm leading-relaxed font-medium text-foreground/80">
                        &ldquo;{version.identitySentence}&rdquo;
                      </CardDescription>
                    </CardHeader>

                    <CardContent className="space-y-4">
                      {/* Top 3 Traits */}
                      <div className="space-y-2">
                        <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                          주요 특성
                        </p>
                        {topTraits.map((trait, i) => (
                          <CompactTraitBar
                            key={trait.trait}
                            label={trait.labelKo}
                            value={trait.value}
                            index={i}
                          />
                        ))}
                      </div>

                      {/* Growth Theme */}
                      <div className="rounded-lg bg-warm-50/60 px-3 py-2.5">
                        <div className="flex items-center gap-1.5 mb-1">
                          <Sparkles className="h-3 w-3 text-primary" />
                          <span className="text-[10px] font-semibold tracking-wide text-primary uppercase">
                            성장 주제
                          </span>
                        </div>
                        <p className="text-sm text-foreground">{version.growthTheme}</p>
                      </div>

                      {/* Delta Section (v2+) */}
                      {deltas.length > 0 && (
                        <div className="space-y-2">
                          <Separator />
                          <p className="text-xs font-semibold tracking-wide text-muted-foreground mt-3">
                            {profileVersionChangeLabel(prevVersion!.number, version.number)} 변화
                          </p>
                          <div className="space-y-2">
                            {deltas.map((d) => (
                              <div
                                key={d.trait}
                                className="flex items-center justify-between rounded-lg bg-muted/30 px-3 py-2"
                              >
                                <span className="text-sm text-foreground">{d.labelKo}</span>
                                <DeltaIndicator delta={d.delta} />
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* ── Trait Evolution Chart ──────────────────────────────────────── */}
        <motion.div {...fadeUp(0.3)} className="mb-5">
          <Card className="border-border/50 shadow-sm">
            <CardContent className="p-5">
              <TraitEvolutionChart versions={sortedVersions} />
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Coming Soon: 내가 말한 나 vs 기록된 나 ────────────────────── */}
        <motion.div {...fadeUp(0.35)} className="mb-5">
          <Card className="border-dashed border-border/60 shadow-none bg-muted/20">
            <CardContent className="p-6 text-center space-y-2">
              <p className="text-sm font-medium text-foreground">
                내가 말한 나 vs 기록된 나
              </p>
              <p className="text-xs text-muted-foreground">
                4주 이상의 기록이 모이면 비교 분석을 볼 수 있어요. 곧 만나요!
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Long-term Insight ──────────────────────────────────────────── */}
        <motion.div {...fadeUp(0.4)} className="mb-6">
          <div className="text-center space-y-2 rounded-xl bg-gradient-to-br from-warm-50 to-sage-50/30 border border-warm-100/60 p-6">
            <Leaf className="mx-auto h-6 w-6 text-sage-500" />
            <p className="text-sm font-medium text-foreground leading-relaxed">
              지금까지 <span className="font-bold text-primary">{totalVersions}개</span>의 프로필을 만들었어요.
              <br />
              기록이 쌓일수록 더 선명해질 거예요.
            </p>
          </div>
        </motion.div>
      </div>
    </main>
  );
}
