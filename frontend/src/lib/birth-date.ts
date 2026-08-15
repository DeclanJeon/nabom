export const BIRTH_YEAR_MIN = 1900;

export function birthYearMax(now = new Date()): number {
  return now.getFullYear();
}

export function daysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate();
}

export type BirthDateParts = {
  year: string;
  month: string;
  day: string;
};

export type BirthDateDraft = BirthDateParts & {
  iso: string | null;
  error: string | null;
};

const EMPTY: BirthDateParts = { year: '', month: '', day: '' };

export function emptyBirthParts(): BirthDateParts {
  return { ...EMPTY };
}

export function partsFromIso(iso: string | undefined): BirthDateParts {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso ?? '');
  if (!match) return emptyBirthParts();
  return {
    year: String(Number(match[1])),
    month: String(Number(match[2])),
    day: String(Number(match[3])),
  };
}

export function partsFromDate(date: Date | undefined): BirthDateParts {
  if (!date || Number.isNaN(date.getTime())) return emptyBirthParts();
  return {
    year: String(date.getFullYear()),
    month: String(date.getMonth() + 1),
    day: String(date.getDate()),
  };
}

function digitsOnly(value: string): string {
  return value.replace(/\D/g, '');
}

export function parseCombinedBirthText(raw: string): BirthDateParts | null {
  const trimmed = raw.trim();
  if (!trimmed) return emptyBirthParts();
  const compact = digitsOnly(trimmed);
  if (compact.length === 8) {
    return {
      year: compact.slice(0, 4),
      month: String(Number(compact.slice(4, 6))),
      day: String(Number(compact.slice(6, 8))),
    };
  }
  const pieces = trimmed.split(/[.\-/년월일\s]+/).filter(Boolean);
  if (pieces.length === 3 && pieces.every((part) => /^\d{1,4}$/.test(part))) {
    return {
      year: String(Number(pieces[0])),
      month: String(Number(pieces[1])),
      day: String(Number(pieces[2])),
    };
  }
  return null;
}

export function sanitizeBirthPart(field: keyof BirthDateParts, raw: string): string {
  const digits = digitsOnly(raw);
  if (field === 'year') return digits.slice(0, 4);
  return digits.slice(0, 2);
}

export function resolveBirthDate(
  parts: BirthDateParts,
  now = new Date(),
): BirthDateDraft {
  const year = parts.year;
  const month = parts.month;
  const day = parts.day;
  if (!year && !month && !day) {
    return { year, month, day, iso: null, error: null };
  }
  if (year.length !== 4 || month.length === 0 || day.length === 0) {
    return { year, month, day, iso: null, error: null };
  }
  const y = Number(year);
  const m = Number(month);
  const d = Number(day);
  const maxYear = birthYearMax(now);
  if (!Number.isInteger(y) || y < BIRTH_YEAR_MIN || y > maxYear) {
    return { year, month, day, iso: null, error: `${BIRTH_YEAR_MIN}–${maxYear}년 사이여야 해요` };
  }
  if (!Number.isInteger(m) || m < 1 || m > 12) {
    return { year, month, day, iso: null, error: '월은 1–12 사이여야 해요' };
  }
  const maxDay = daysInMonth(y, m);
  if (!Number.isInteger(d) || d < 1 || d > maxDay) {
    return { year, month, day, iso: null, error: `${m}월은 ${maxDay}일까지예요` };
  }
  const iso = `${String(y).padStart(4, '0')}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
  return { year: String(y), month: String(m), day: String(d), iso, error: null };
}

export function isoToLocalDate(iso: string): Date {
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year, month - 1, day);
}
