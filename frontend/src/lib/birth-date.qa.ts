import {
  parseCombinedBirthText,
  partsFromIso,
  resolveBirthDate,
  sanitizeBirthPart,
} from './birth-date';

function require(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const now = new Date(2026, 7, 14);

const typed = resolveBirthDate(
  {
    year: sanitizeBirthPart('year', '1992'),
    month: sanitizeBirthPart('month', '3'),
    day: sanitizeBirthPart('day', '1'),
  },
  now,
);
require(typed.iso === '1992-03-01', `typed ${typed.iso}`);

const pasteCases = ['1992.03.01', '1992-03-01', '19920301', '1992년 3월 1일', '1992 3 1'];
for (const raw of pasteCases) {
  const parsed = parseCombinedBirthText(raw);
  require(parsed, `parse ${raw}`);
  const resolved = resolveBirthDate(parsed, now);
  require(resolved.iso === '1992-03-01', `${raw} -> ${resolved.iso}`);
}

require(resolveBirthDate({ year: '1992', month: '3', day: '' }, now).iso === null, 'incomplete stays empty');
require(resolveBirthDate({ year: '1993', month: '2', day: '29' }, now).error, 'invalid day');
require(partsFromIso('1992-03-01').month === '3', 'iso roundtrip');

console.log('birth-date-qa: PASS');
