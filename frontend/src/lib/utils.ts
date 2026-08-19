import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 서비스 기준 시간대(Asia/Seoul)의 날짜 문자열(YYYY-MM-DD).
// toISOString()은 UTC 기준이라 KST 00:00~08:59에 전날을 반환해,
// 기록 날짜(Asia/Seoul)와 비교하는 주간 창 계산이 어긋난다. 여기서 맞춘다.
export function kstDateString(date: Date): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date);
}
