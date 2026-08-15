'use client';

import { motion } from 'framer-motion';
import { ArrowLeft, Leaf } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNabomStore } from '@/store/nabom-store';

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const fadeUp = (delay = 0) => {
  if (prefersReducedMotion()) return {};
  return {
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] as const },
  };
};

export default function Auth() {
  const { loginWithGoogle, authStatus, authError, setView } = useNabomStore();
  const isBusy = authStatus === 'loading';

  return (
    <main className="min-h-screen flex flex-col bg-background">
      <div className="nabom-narrow flex flex-1 flex-col">
        {/* Header */}
        <div className="mb-6">
          <button
            type="button"
            onClick={() => setView('landing')}
            className="flex h-11 w-11 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="랜딩으로 돌아가기"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
        </div>

        {/* Brand */}
        <motion.div {...fadeUp(0)} className="mb-10 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-3xl bg-gradient-to-br from-warm-100 to-sage-100">
            <Leaf className="h-8 w-8 text-sage-500" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            나봄
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            기록할수록 선명해지는 나.
          </p>
        </motion.div>

        {/* Google-only entry */}
        <motion.div {...fadeUp(0.05)} className="flex flex-1 flex-col">
          <div className="flex flex-1 items-start justify-center pt-6">
            <Button
              type="button"
              size="lg"
              className="w-full h-12 rounded-xl text-base font-semibold shadow-md transition-all hover:shadow-lg active:scale-[0.98] disabled:opacity-40"
              disabled={isBusy}
              onClick={() => void loginWithGoogle()}
            >
              {isBusy ? 'Google로 이동 중…' : 'Google로 계속하기'}
            </Button>
          </div>

          {authError && (
            <motion.div
              {...fadeUp(0.1)}
              className="mb-4 flex items-start gap-2 rounded-xl border border-warm-200/60 bg-warm-50/70 px-4 py-3"
            >
              <p className="text-sm text-warm-800">{authError}</p>
            </motion.div>
          )}

          <p className="text-center text-xs text-muted-foreground leading-relaxed pt-4">
            Google로 가입하면 나봄의{' '}
            <button
              type="button"
              className="underline underline-offset-2"
              onClick={() => useNabomStore.getState().openLegal('terms')}
            >
              이용약관
            </button>
            과{' '}
            <button
              type="button"
              className="underline underline-offset-2"
              onClick={() => useNabomStore.getState().openLegal('privacy')}
            >
              개인정보처리방침
            </button>
            에 동의하는 것으로 간주해요.
            <br />
            기록은 언제든 내보내거나 삭제할 수 있어요.
          </p>
        </motion.div>
      </div>
    </main>
  );
}
