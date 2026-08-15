'use client';

import { useEffect, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { AnimatePresence, motion } from 'framer-motion';
import { useNabomStore } from '@/store/nabom-store';
import { AppNav } from './bottom-nav';
import { pathFromView, viewFromPath } from '@/lib/routes';
import Landing from './landing';
import Auth from './auth';
import Onboarding from './onboarding';
import Today from './today';
import Profile from './profile';
import Mirror from './mirror';
import Journey from './journey';
import Settings from './settings';
import Legal from './legal';
import Admin from './admin';

const VIEW_VARIANTS = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
};

function ViewRenderer({ view }: { view: string }) {
  switch (view) {
    case 'landing':
      return <Landing />;
    case 'auth':
      return <Auth />;
    case 'welcome':
      return <Onboarding />;
    case 'today':
      return <Today />;
    case 'profile':
      return <Profile />;
    case 'mirror':
      return <Mirror />;
    case 'journey':
      return <Journey />;
    case 'settings':
      return <Settings />;
    case 'legal':
      return <Legal />;
    case 'admin':
      return <Admin />;
    default:
      return <Today />;
  }
}

export function AppShell({ initialView }: { initialView?: string }) {
  const currentView = useNabomStore((s) => s.currentView);
  const isOnboarded = useNabomStore((s) => s.isOnboarded);
  const session = useNabomStore((s) => s.session);
  const hydrate = useNabomStore((s) => s.hydrate);
  const completeOAuthToken = useNabomStore((s) => s.completeOAuthToken);
  const setView = useNabomStore((s) => s.setView);
  const pathname = usePathname();
  const router = useRouter();
  const hydratedOnce = useRef(false);
  const navSynced = useRef(false);

  // 초기화: 세션이 있으면 hydrate 후 URL 기준으로 뷰를 결정한다.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const oauth = params.get('oauth');
    const token = params.get('token');
    const code = params.get('code');
    if (oauth === 'ok' && token) {
      window.history.replaceState({}, '', window.location.pathname);
      void completeOAuthToken(token);
      return;
    }
    if (oauth === 'error') {
      window.history.replaceState({}, '', window.location.pathname);
      useNabomStore.setState({
        currentView: 'auth',
        authStatus: 'error',
        authError: code === 'OAUTH_STATE_INVALID'
          ? 'Google 로그인 세션이 만료됐어요. 다시 시도해주세요.'
          : 'Google 로그인에 실패했어요. 다시 시도해주세요.',
      });
      setView('auth');
      return;
    }
    if (!hydratedOnce.current) {
      hydratedOnce.current = true;
      void hydrate({ route: false }).then(() => {
        const view = initialView ?? viewFromPath(window.location.pathname);
        if (view) useNabomStore.setState({ currentView: view });
      });
    }
  }, [hydrate, completeOAuthToken, initialView, setView]);

  // 뷰 → 라우트(URL): 내부 내비게이션이 URL을 따라가고 히스토리를 쌓는다.
  // 첫 동기화는 히스토리에 쌓지 않는다 (직접 URL 진입/새로고침 시 중복 방지).
  useEffect(() => {
    const path = pathFromView(currentView as Parameters<typeof pathFromView>[0]);
    if (pathname === path) {
      navSynced.current = true;
      return;
    }
    if (!navSynced.current) {
      navSynced.current = true;
      router.replace(path);
    } else {
      router.push(path);
    }
  }, [currentView, pathname, router]);

  const publicViews = new Set(['landing', 'legal']);
  const effectiveView =
    !session && !publicViews.has(currentView as string) ? 'auth' : (currentView as string);

  const showNav =
    isOnboarded &&
    !!session &&
    effectiveView !== 'landing' &&
    effectiveView !== 'auth' &&
    effectiveView !== 'welcome' &&
    effectiveView !== 'legal' &&
    effectiveView !== 'admin';

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {showNav && <AppNav />}
      <main
        className={`flex-1 ${showNav ? 'pb-20 md:pb-0' : ''}`}
        role="main"
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={effectiveView}
            variants={VIEW_VARIANTS}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.25, ease: 'easeOut' }}
          >
            <ViewRenderer view={effectiveView} />
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
