'use client';

import { useEffect, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNabomStore } from '@/store/nabom-store';
import { api } from '@/lib/api';
import type { LegalDocument } from '@/types/nabom';

export default function Legal() {
  const legalKind = useNabomStore((s) => s.legalKind);
  const setView = useNabomStore((s) => s.setView);
  const goBack = useNabomStore((s) => s.goBack);
  const [document, setDocument] = useState<LegalDocument | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .legal(legalKind)
      .then((next) => {
        if (!cancelled) setDocument(next);
      })
      .catch(() => {
        if (!cancelled) setError('문서를 불러오지 못했어요.');
      });
    return () => {
      cancelled = true;
    };
  }, [legalKind]);

  return (
    <main className="min-h-screen flex flex-col bg-background">
      <div className="nabom-narrow">
        <button
          type="button"
          onClick={() => (useNabomStore.getState().previousView ? goBack() : setView('landing'))}
          className="mb-6 flex h-11 w-11 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          aria-label="돌아가기"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        {error && <p className="text-sm text-destructive">{error}</p>}
        {document && (
          <article className="space-y-6">
            <header className="space-y-2">
              <h1 className="text-2xl font-bold tracking-tight text-foreground">{document.title}</h1>
              <p className="text-xs text-muted-foreground">
                버전 {document.version} · 업데이트 {document.updatedAt}
              </p>
            </header>
            {document.sections.map((section) => (
              <section key={section.heading} className="space-y-2">
                <h2 className="text-base font-semibold text-foreground">{section.heading}</h2>
                <p className="text-sm leading-relaxed text-foreground/80">{section.body}</p>
              </section>
            ))}
          </article>
        )}
      </div>
    </main>
  );
}
