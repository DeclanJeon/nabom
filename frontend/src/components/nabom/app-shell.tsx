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
  const session = useNabomStore((s) => s.session);
  const isOnboarded = useNabomStore((s) => s.isOnboarded);
  const hydrate = useNabomStore((s) => s.hydrate);
  const completeOAuthToken = useNabomStore((s) => s.completeOAuthToken);
  const pathname = usePathname();
  const router = useRouter();
  // URL⇄뷰 동기화 상태.
  // mounted: 이 마운트에서 URL 채택을 처리했는지. 마운트 직후 1회만 URL→뷰를 적용한다.
  //   이후에는 내부 뷰 변경 → push, URL 변경(back/forward) → URL 채택만 한다.
  // prevViewRef: 직전 렌더의 뷰. push는 "뷰가 내부에서 바뀌었을 때"만 한다.
  // lastPathRef: 마지막으로 처리한 URL 경로. 브라우저 back/forward 감지용.
  const mounted = useRef(false);
  const prevViewRef = useRef(currentView);
  const lastPathRef = useRef(pathname);

  // 초기화: OAuth 콜백 처리 + 세션 데이터 로드. 뷰 정렬은 nav 이펙트의 마운트 채택이 담당한다.
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
      return;
    }
    void hydrate({ route: false });
  }, [hydrate, completeOAuthToken]);

  // URL ⇄ 뷰 동기화.
  // - 마운트 직후: URL(initialView)이 진실. 스토어 뷰가 URL과 다르면 URL을 채택한다.
  //   (직접 URL 진입, back/forward, 로그인 후 새로고침 등). 비로그인 보호 뷰는 /auth로 replace.
  // - 이후 URL이 바뀌면(back/forward) URL을 채택하고 되받아치지 않는다.
  // - 뷰가 내부에서 바뀌면(내비게이션) router.push로 URL을 따라가게 한다.
  // hydrate가 진행 중이어도 뷰 전환은 막지 않는다 — hydrate는 currentView를 건드리지 않는다.
  useEffect(() => {
    const urlView = (initialView as AppView | undefined) ?? viewFromPath(pathname);
    const state = useNabomStore.getState();
    if (!mounted.current) {
      mounted.current = true;
      lastPathRef.current = pathname;
      prevViewRef.current = state.currentView;
      if (urlView && urlView !== state.currentView) {
        if (!state.session && !PUBLIC_VIEWS.has(urlView)) {
          if (urlView === 'auth') {
            useNabomStore.setState({ currentView: 'auth' });
          } else {
            router.replace(pathFromView('auth'));
          }
        } else {
          useNabomStore.setState({ currentView: urlView });
        }
      }
      return;
    }
    if (pathname !== lastPathRef.current) {
      // URL 내비게이션 (back/forward/주소 직접 입력): URL을 뷰로 수용한다.
      lastPathRef.current = pathname;
      const view = viewFromPath(pathname);
      if (view && view !== currentView) {
        useNabomStore.setState({ currentView: view });
      }
      return;
    }
    // 세션 만료 등으로 보호 뷰에 비로그인 상태가 되면 로그인으로 안내한다.
    if (!state.session && !PUBLIC_VIEWS.has(currentView as AppView) && urlView !== 'auth') {
      router.replace(pathFromView('auth'));
      return;
    }
    const viewChanged = currentView !== prevViewRef.current;
    prevViewRef.current = currentView;
    if (!viewChanged) return;
    const path = pathFromView(currentView as AppView);
    if (path !== pathname) router.push(path);
  }, [currentView, pathname, router, initialView]);

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
