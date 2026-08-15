'use client';

import { motion } from 'framer-motion';
import {
  Sun,
  User,
  BookOpen,
  Map,
  Settings,
  Leaf,
} from 'lucide-react';
import { useNabomStore } from '@/store/nabom-store';
import type { AppView } from '@/types/nabom';

type NavItem = {
  view: AppView;
  label: string;
  icon: React.ElementType;
};

const NAV_ITEMS: NavItem[] = [
  { view: 'today', label: '오늘', icon: Sun },
  { view: 'profile', label: '프로필', icon: User },
  { view: 'mirror', label: '회고', icon: BookOpen },
  { view: 'journey', label: '여정', icon: Map },
  { view: 'settings', label: '설정', icon: Settings },
];

function NavButtons({ orientation }: { orientation: 'top' | 'bottom' }) {
  const currentView = useNabomStore((s) => s.currentView);
  const setView = useNabomStore((s) => s.setView);
  const top = orientation === 'top';

  return (
    <>
      {NAV_ITEMS.map((item) => {
        const isActive = currentView === item.view;
        const Icon = item.icon;
        return (
          <button
            key={item.view}
            type="button"
            onClick={() => setView(item.view)}
            className={
              top
                ? `inline-flex min-h-11 items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                    isActive ? 'bg-warm-100 text-primary' : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                  }`
                : 'relative flex min-h-[56px] min-w-[48px] flex-col items-center justify-center gap-0.5 rounded-lg px-3 py-1.5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 active:scale-95'
            }
            aria-label={item.label}
            aria-current={isActive ? 'page' : undefined}
          >
            <Icon
              className={top ? 'h-4 w-4' : `h-5 w-5 ${isActive ? 'text-primary' : 'text-muted-foreground'}`}
              strokeWidth={isActive ? 2.2 : 1.8}
            />
            <span className={top ? '' : `text-[10px] font-medium ${isActive ? 'text-primary' : 'text-muted-foreground'}`}>
              {item.label}
            </span>
            {!top && isActive && (
              <motion.div
                layoutId="nav-indicator"
                className="absolute -bottom-1 left-1/2 h-0.5 w-4 -translate-x-1/2 rounded-full bg-primary"
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              />
            )}
          </button>
        );
      })}
    </>
  );
}

export function AppNav() {
  const setView = useNabomStore((s) => s.setView);
  return (
    <>
      <nav
        className="sticky top-0 z-50 hidden border-b border-border bg-card/80 backdrop-blur-xl md:block"
        role="navigation"
        aria-label="메인 내비게이션"
      >
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6 lg:px-8">
          <button
            type="button"
            onClick={() => setView('today')}
            className="flex min-h-11 items-center gap-2 rounded-lg px-2 text-sm font-semibold tracking-wide text-warm-700 transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="나봄 홈으로 이동"
          >
            <Leaf className="h-4 w-4 text-sage-500" />
            나봄
          </button>
          <div className="flex items-center gap-1">
            <NavButtons orientation="top" />
          </div>
        </div>
      </nav>
      <nav
        className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-card/80 backdrop-blur-xl md:hidden"
        role="navigation"
        aria-label="메인 내비게이션"
      >
        <div className="mx-auto flex items-center justify-around px-2 py-1">
          <NavButtons orientation="bottom" />
        </div>
        <div className="h-[env(safe-area-inset-bottom)]" />
      </nav>
    </>
  );
}

