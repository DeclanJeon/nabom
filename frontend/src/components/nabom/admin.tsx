'use client';

import { useEffect, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNabomStore } from '@/store/nabom-store';
import { api } from '@/lib/api';
import type { AdminUserSummary } from '@/types/nabom';

export default function Admin() {
  const setView = useNabomStore((s) => s.setView);
  const [users, setUsers] = useState<AdminUserSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .adminUsers()
      .then((next) => {
        if (!cancelled) setUsers(next);
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : '관리자 목록을 열 수 없어요.');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="min-h-screen flex flex-col bg-background">
      <div className="nabom-narrow">
        <button
          type="button"
          onClick={() => setView('settings')}
          className="mb-6 flex h-11 w-11 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          aria-label="설정으로 돌아가기"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="mb-2 text-2xl font-bold tracking-tight text-foreground">운영 현황</h1>
        <p className="mb-6 text-sm text-muted-foreground">활성 상태와 기록 수만 보입니다. 일기 본문은 열리지 않습니다.</p>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="space-y-3">
          {users.map((user) => (
            <article key={user.userId} className="rounded-xl border border-border/60 bg-card p-4">
              <p className="text-sm font-medium text-foreground">{user.nickname || user.email}</p>
              <p className="text-xs text-muted-foreground">{user.email}</p>
              <dl className="mt-3 grid grid-cols-2 gap-2 text-xs text-foreground/80">
                <div>계정 {user.status}</div>
                <div>프로필 {user.profileStatus}</div>
                <div>기록일 {user.recordedDays}</div>
                <div>주간 {user.weeklyStatus}</div>
                <div>일기 {user.journalCount}건</div>
                <div>실험 {user.experimentCount}건</div>
              </dl>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
