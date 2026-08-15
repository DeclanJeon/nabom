import type { AppView } from '@/types/nabom';

// URL 경로 ⇄ 앱 뷰 매핑. 내비게이션의 단일 진실.
export const VIEW_PATHS: Record<AppView, string> = {
  landing: '/',
  auth: '/auth',
  welcome: '/welcome',
  today: '/today',
  profile: '/profile',
  mirror: '/mirror',
  journey: '/journey',
  settings: '/settings',
  legal: '/legal',
  admin: '/admin',
};

export function pathFromView(view: AppView): string {
  return VIEW_PATHS[view] ?? '/';
}

export function viewFromPath(pathname: string): AppView | null {
  const path = pathname === '/' ? '/' : pathname.replace(/\/+$/, '') || '/';
  const entry = Object.entries(VIEW_PATHS).find(([, p]) => p === path);
  return entry ? (entry[0] as AppView) : null;
}
