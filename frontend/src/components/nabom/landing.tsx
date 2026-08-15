'use client';

import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { Feather, BookOpen, Sparkles, ArrowRight, Sun, Leaf, Heart } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNabomStore } from '@/store/nabom-store';

// ─── Animation Helpers ───────────────────────────────────────────────────────

const prefersReducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const fadeUp = (delay = 0) => {
  if (prefersReducedMotion()) return {};
  return {
    initial: { opacity: 0, y: 24 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true, margin: '-40px' },
    transition: { duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] as const },
  };
};

const fadeIn = (delay = 0) => {
  if (prefersReducedMotion()) return {};
  return {
    initial: { opacity: 0 },
    whileInView: { opacity: 1 },
    viewport: { once: true, margin: '-40px' },
    transition: { duration: 0.8, delay, ease: 'easeOut' },
  };
};

// ─── Data ─────────────────────────────────────────────────────────────────────

const VALUE_CARDS = [
  {
    icon: Feather,
    title: '단순한 성격검사가 아닙니다',
    description: '시간에 따라 변화하는 실제 삶을 기반으로 합니다',
    accent: 'bg-warm-100 text-warm-700',
    iconColor: 'text-warm-600',
  },
  {
    icon: BookOpen,
    title: '기록이 곧 거울입니다',
    description: '일상의 작은 기록이 모여 나를 입체적으로 보여줍니다',
    accent: 'bg-sage-100 text-sage-700',
    iconColor: 'text-sage-600',
  },
  {
    icon: Sparkles,
    title: 'AI가 판단하지 않습니다',
    description: '당신의 데이터가 당신을 말하게 합니다',
    accent: 'bg-terra-100 text-terra-700',
    iconColor: 'text-terra-500',
  },
] as const;

const TIMELINE_ITEMS = [
  { period: '1일 차', label: '첫 프로필이 만들어집니다', emoji: '🌱' },
  { period: '1주일', label: '첫 주간 거울이 펼쳐집니다', emoji: '🌿' },
  { period: '1개월', label: '나만의 패턴이 보이기 시작합니다', emoji: '🍃' },
  { period: '3개월', label: '프로필이 진화합니다', emoji: '🌳' },
  { period: '6개월+', label: '시간 속에 선명해진 나를 만납니다', emoji: '✨' },
];

// ─── Section Components ───────────────────────────────────────────────────────

function HeroSection() {
  const ctaRef = useRef<HTMLDivElement>(null);
  const ctaInView = useInView(ctaRef, { once: true, margin: '-20px' });
  const noMotion = prefersReducedMotion();

  return (
    <section className="relative flex min-h-[85vh] flex-col items-center justify-center overflow-hidden px-6 py-16">
      {/* Soft warm gradient background */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-warm-50/60 via-transparent to-transparent" />
      <div className="pointer-events-none absolute -top-32 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-warm-200/30 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-20 right-0 h-60 w-60 rounded-full bg-sage-200/20 blur-3xl" />

      {/* Brand name */}
      <motion.div
        initial={noMotion ? {} : { opacity: 0, scale: 0.9 }}
        animate={noMotion ? {} : { opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] as const }}
        className="mb-6 flex items-center gap-2"
      >
        <Leaf className="h-5 w-5 text-sage-500" />
        <span className="text-sm font-medium tracking-widest text-warm-600">
          NABOM
        </span>
      </motion.div>

      {/* Tagline */}
      <motion.h1
        initial={noMotion ? {} : { opacity: 0, y: 30 }}
        animate={noMotion ? {} : { opacity: 1, y: 0 }}
        transition={{ duration: 0.9, delay: 0.15, ease: [0.22, 1, 0.36, 1] as const }}
        className="max-w-sm text-center text-3xl font-bold leading-tight tracking-tight text-foreground sm:text-4xl md:max-w-2xl md:text-5xl"
      >
        기록할수록{' '}
        <span className="bg-gradient-to-r from-warm-700 via-terra-500 to-warm-700 bg-clip-text text-transparent">
          선명해지는
        </span>{' '}
        나
      </motion.h1>

      {/* Subtitle */}
      <motion.p
        initial={noMotion ? {} : { opacity: 0, y: 20 }}
        animate={noMotion ? {} : { opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.35, ease: [0.22, 1, 0.36, 1] as const }}
        className="mt-5 max-w-xs text-center text-base leading-relaxed text-muted-foreground sm:text-lg md:max-w-xl"
      >
        오늘의 나는, 어제의 나와 조금 다르니까.
      </motion.p>

      {/* Decorative line */}
      <motion.div
        initial={noMotion ? {} : { scaleX: 0 }}
        animate={noMotion ? {} : { scaleX: 1 }}
        transition={{ duration: 1, delay: 0.5, ease: [0.22, 1, 0.36, 1] as const }}
        className="mt-8 h-px w-16 origin-left bg-gradient-to-r from-warm-300 to-transparent"
      />

      {/* Scroll hint */}
      <motion.div
        initial={noMotion ? {} : { opacity: 0 }}
        animate={noMotion ? {} : { opacity: 1 }}
        transition={{ duration: 0.6, delay: 1.2 }}
        className="absolute bottom-8 flex flex-col items-center gap-1"
      >
        <span className="text-xs text-muted-foreground/60">아래로 스크롤</span>
        <motion.div
          animate={noMotion ? {} : { y: [0, 6, 0] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          className="text-muted-foreground/40"
        >
          <ArrowRight className="h-4 w-4 rotate-90" />
        </motion.div>
      </motion.div>
    </section>
  );
}

function ValueCardsSection() {
  return (
    <section className="px-6 pb-16">
      <div className="mx-auto max-w-lg md:max-w-4xl">
        <motion.p {...fadeUp(0)} className="mb-8 text-center text-sm font-medium tracking-wide text-warm-600 uppercase">
          나봄의 다른 점
        </motion.p>
        <div className="flex flex-col gap-4 md:grid md:grid-cols-3">
          {VALUE_CARDS.map((card, i) => {
            const Icon = card.icon;
            return (
              <motion.div
                key={card.title}
                {...fadeUp(0.1 * i)}
                className="group rounded-2xl border border-border/60 bg-card p-5 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="flex items-start gap-4">
                  <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${card.accent}`}>
                    <Icon className={`h-5 w-5 ${card.iconColor}`} />
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-base font-semibold leading-snug text-foreground">
                      {card.title}
                    </h3>
                    <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                      {card.description}
                    </p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function TimelineSection() {
  return (
    <section className="px-6 pb-16">
      <div className="mx-auto max-w-lg md:max-w-3xl">
        <motion.div {...fadeUp(0)} className="mb-8 text-center">
          <Sun className="mx-auto mb-3 h-5 w-5 text-terra-400" />
          <h2 className="text-xl font-bold text-foreground">가치 타임라인</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            기록이 쌓일수록, 당신은 더 선명해집니다
          </p>
        </motion.div>

        <div className="relative pl-8">
          {/* Vertical line */}
          <div className="absolute bottom-0 left-[11px] top-0 w-px bg-gradient-to-b from-warm-300 via-sage-300 to-terra-300" />

          <div className="flex flex-col gap-6">
            {TIMELINE_ITEMS.map((item, i) => (
              <motion.div
                key={item.period}
                {...fadeUp(0.08 * i)}
                className="relative"
              >
                {/* Dot on the timeline */}
                <div className="absolute -left-8 top-1 flex h-6 w-6 items-center justify-center">
                  <div className="h-2.5 w-2.5 rounded-full bg-warm-400 ring-4 ring-warm-100" />
                </div>
                <div className="rounded-xl bg-card p-4 border border-border/40 shadow-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-lg" role="img" aria-label={item.period}>
                      {item.emoji}
                    </span>
                    <span className="text-sm font-semibold text-foreground">
                      {item.period}
                    </span>
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                    {item.label}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  const setView = useNabomStore((s) => s.setView);
  const session = useNabomStore((s) => s.session);
  const isOnboarded = useNabomStore((s) => s.isOnboarded);
  const noMotion = prefersReducedMotion();

  const handleStart = () => {
    if (!session) {
      setView('auth');
    } else if (!isOnboarded) {
      setView('welcome');
    } else {
      setView('today');
    }
  };

  return (
    <section className="px-6 pb-20 pt-4">
      <div className="mx-auto max-w-lg md:max-w-2xl">
        <motion.div
          {...fadeUp(0)}
          className="rounded-2xl bg-gradient-to-br from-warm-100 via-warm-50 to-sage-100/40 p-8 text-center border border-warm-200/50"
        >
          <Heart className="mx-auto mb-4 h-6 w-6 text-terra-400" />
          <h2 className="text-lg font-bold text-foreground">
            지금, 나를 기록하기 시작하세요
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            몇 가지 질문으로 프로필을 만들고, 앞으로의 기록을 통해
            <br className="hidden sm:block" />
            계속 당신을 알아갑니다.
          </p>
          <Button
            size="lg"
            className="mt-6 h-12 w-full max-w-xs rounded-xl text-base font-semibold shadow-md transition-all hover:shadow-lg active:scale-[0.98]"
            onClick={handleStart}
          >
            {session
              ? isOnboarded
                ? '오늘의 나 기록하기'
                : '내 프로필 만들기'
              : '시작하기'}
            <ArrowRight className="h-4 w-4" />
          </Button>
        </motion.div>
      </div>
    </section>
  );
}

function LandingFooter() {
  const openLegal = useNabomStore((s) => s.openLegal);
  return (
    <footer className="mt-auto border-t border-border/40 bg-card/50 px-6 py-6">
      <div className="mx-auto flex max-w-lg flex-col items-center gap-2 text-center md:max-w-4xl">
        <p className="text-xs text-muted-foreground">
          © 2026 나봄 (NABOM)
        </p>
        <button
          type="button"
          className="text-xs text-muted-foreground underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm"
          aria-label="개인정보처리방침 열기"
          onClick={() => openLegal('privacy')}
        >
          개인정보처리방침
        </button>
      </div>
    </footer>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function Landing() {
  return (
    <main className="min-h-screen flex flex-col bg-background">
      <HeroSection />
      <ValueCardsSection />
      <TimelineSection />
      <CTASection />
      <LandingFooter />
    </main>
  );
}
