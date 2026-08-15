import { searchBirthPlaces, toBirthLocation } from './birth-place';

function require(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const cases: Array<[string, string]> = [
  ['부산', 'kr-busan'],
  ['서울', 'kr-seoul'],
  ['해운대', 'kr-busan'],
  ['Busan', 'kr-busan'],
  ['incheon', 'kr-incheon'],
  ['제주', 'kr-jeju'],
  ['도쿄', 'jp-tokyo'],
  ['osaka', 'jp-osaka'],
  ['paris', 'fr-paris'],
  ['sydney', 'au-sydney'],
  ['la', 'us-losangeles'],
];

for (const [query, id] of cases) {
  const hit = searchBirthPlaces(query)[0];
  require(hit?.id === id, `${query} → ${hit?.id ?? 'none'}, expected ${id}`);
}

const busan = searchBirthPlaces('부산')[0];
const wire = toBirthLocation(busan);
require(wire.lat !== 0 && wire.lon !== 0, 'coords filled');
require(wire.timezone === 'Asia/Seoul', 'kr tz');
require(!/주작|일간|병화|용신/.test(JSON.stringify(wire)), 'no myeongni leak');

console.log('birth-place-qa: PASS');
