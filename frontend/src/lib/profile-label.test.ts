import { profileVersionChangeLabel, profileVersionLabel } from './profile-label';

function require(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

require(profileVersionLabel(1) === '첫 프로필', 'first');
require(profileVersionLabel(2) === '2번째 프로필', 'second');
require(profileVersionLabel(12) === '12번째 프로필', 'twelfth');
require(profileVersionLabel(1, { compact: true }) === '처음', 'compact first');
require(profileVersionLabel(3, { compact: true }) === '3번째', 'compact third');
require(profileVersionChangeLabel(1, 2) === '첫 프로필 → 2번째 프로필', 'delta');

console.log('profile-label: PASS');
