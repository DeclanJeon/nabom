import {
  daysInMonth,
  parseCombinedBirthText,
  partsFromIso,
  resolveBirthDate,
  sanitizeBirthPart,
} from './birth-date';

function require(condition: unknown, message: string): void {
  if (!condition) throw new Error(message);
}

const now = new Date(2026, 7, 14);

require(daysInMonth(1992, 3) === 31, '1992-03 days');
require(daysInMonth(1992, 2) === 29, '1992 leap feb');
require(daysInMonth(1993, 2) === 28, '1993 feb');

require(JSON.stringify(partsFromIso('1992-03-01')) === JSON.stringify({ year: '1992', month: '3', day: '1' }), 'iso parts');
require(partsFromIso('').year === '', 'empty iso');

require(sanitizeBirthPart('year', '19a92x') === '1992', 'year digits');
require(sanitizeBirthPart('month', '013') === '01', 'month cap');
require(sanitizeBirthPart('day', '9') === '9', 'day pass');

const dotted = parseCombinedBirthText('1992.3.1');
require(dotted?.year === '1992' && dotted.month === '3' && dotted.day === '1', `dotted ${JSON.stringify(dotted)}`);
const dashed = parseCombinedBirthText('1992-03-01');
require(dashed?.year === '1992' && dashed.month === '3' && dashed.day === '1', 'dashed');
const compact = parseCombinedBirthText('19920301');
require(compact?.year === '1992' && compact.month === '3' && compact.day === '1', 'compact');
const korean = parseCombinedBirthText('1992년 3월 1일');
require(korean?.year === '1992' && korean.month === '3' && korean.day === '1', 'korean');
require(parseCombinedBirthText('not-a-date') === null, 'reject garbage');

const ok = resolveBirthDate({ year: '1992', month: '3', day: '1' }, now);
require(ok.iso === '1992-03-01' && ok.error === null, `ok ${JSON.stringify(ok)}`);

const partial = resolveBirthDate({ year: '1992', month: '3', day: '' }, now);
require(partial.iso === null && partial.error === null, 'partial is not an error');

const future = resolveBirthDate({ year: '2099', month: '1', day: '1' }, now);
require(future.iso === null && Boolean(future.error), 'future year blocked');

const feb = resolveBirthDate({ year: '1993', month: '2', day: '29' }, now);
require(feb.iso === null && Boolean(feb.error), 'invalid feb 29');

const leap = resolveBirthDate({ year: '1992', month: '2', day: '29' }, now);
require(leap.iso === '1992-02-29', 'leap day accepted');

console.log('birth-date: PASS');
