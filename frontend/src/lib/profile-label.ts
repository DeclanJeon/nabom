export function profileVersionLabel(number: number, opts: { compact?: boolean } = {}): string {
  const n = Math.max(1, Math.trunc(number || 1));
  if (opts.compact) return n === 1 ? '처음' : `${n}번째`;
  return n === 1 ? '첫 프로필' : `${n}번째 프로필`;
}

export function profileVersionChangeLabel(from: number, to: number): string {
  return `${profileVersionLabel(from)} → ${profileVersionLabel(to)}`;
}
