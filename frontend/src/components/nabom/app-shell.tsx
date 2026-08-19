'use client';

import { useEffect, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { AnimatePresence, motion } from 'framer-motion';
import { useNabomStore } from '@/store/nabom-store';
import { AppNav } from './bottom-nav';
import { pathFromView, viewFromPath } from '@/lib/routes';
import type { AppView } from '@/types/nabom';
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

// 세션 없이 접근 가능한 뷰. 그 외 뷰는 로그인 후에만 렌더링한다.
const PUBLIC_VIEWS = new Set<AppView>(['landing', 'legal']);

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
  const pathname = usePathname();
  const router = useRouter();
  // URL⇄뷰 동기화 상태.
  // aligned: 초기화 이펙트가 뷰를 URL 기준으로 정렬(또는 로그인 리다이렉트)했는지.
  //   정렬 완료 전에는 nav 이펙트가 push/replace를 하지 않는다 —
  //   마운트 직후 스토어 기본 뷰(landing)와 URL의 mismatch가 URL 루프를 만든다.
  // prevViewRef: 직전 렌더의 뷰. push는 "뷰가 내부에서 바뀌었을 때"만 한다.
  // lastPathRef: 마지막으로 처리한 URL 경로. 브라우저 back/forward 감지용.
  const aligned = useRef(false);
  const prevViewRef = useRef(currentView);
  const lastPathRef = useRef(pathname);

  // 초기화: OAuth 콜백 처리 후, 세션 hydrate 후 URL 기준으로 뷰를 결정한다.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const oauth = params.get('oauth');
    const token = params.get('token');
    const code = params.get('code');
    if (oauth === 'ok' && token) {
      window.history.replaceState({}, '', window.location.pathname);
      aligned.current = true;
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
      aligned.current = true;
      return;
    }
    if (aligned.current) return;
    void hydrate({ route: false }).then(() => {
      const state = useNabomStore.getState();
      const view = (initialView as AppView | undefined) ?? viewFromPath(window.location.pathname);
      if (!view) {
        aligned.current = true;
        return;
      }
      if (!state.session && !PUBLIC_VIEWS.has(view)) {
        // 비로그인 사용자의 보호 뷰 직접 진입: 히스토리를 남기지 않고 로그인으로 안내한다.
        if (view === 'auth') {
          useNabomStore.setState({ currentView: 'auth' });
        } else {
          router.replace(pathFromView('auth'));
        }
        aligned.current = true;
        return;
      }
      useNabomStore.setState({ currentView: view });
      aligned.current = true;
    });
  }, [hydrate, completeOAuthToken, initialView, router]);

  // URL ⇄ 뷰 동기화:
  // - URL이 바뀌면(브라우저 back/forward) URL이 진실이며 뷰를 따라간다. 되받아치지 않는다.
  // - 뷰가 내부에서 바뀌면(내비게이션) router.push로 URL을 따라가게 한다.
  // - 마운트 직후(뷰 변화 없음)에는 push하지 않는다 — 정렬 완료까지 대기.
  useEffect(() => {
    if (!aligned.current) return;
    if (pathname !== lastPathRef.current) {
      // URL 내비게이션 (back/forward/직접 진입): URL을 뷰로 수용한다.
      lastPathRef.current = pathname;
      const view = viewFromPath(pathname);
      if (view && view !== currentView) {
        useNabomStore.setState({ currentView: view });
      }
      return;
    }
    const viewChanged = currentView !== prevViewRef.current;
    prevViewRef.current = currentView;
    if (!viewChanged) return;
    const path = pathFromView(currentView as AppView);
    if (path !== pathname) router.push(path);
  }, [currentView, pathname, router]);

  const effectiveView =
    !session && !PUBLIC_VIEWS.has(currentView as AppView) ? 'auth' : (currentView as string);

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
