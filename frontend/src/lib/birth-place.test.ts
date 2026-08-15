import {
  BIRTH_PLACES,
  displayBirthPlace,
  findBirthPlaceById,
  searchBirthPlaces,
  toBirthLocation,
} from './birth-place';

function require(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

require(searchBirthPlaces('').length === 0, 'empty query');
require(searchBirthPlaces('   ').length === 0, 'blank query');

const busan = searchBirthPlaces('부산');
require(busan[0]?.id === 'kr-busan', `부산 → ${busan[0]?.id}`);
require(busan[0]?.timezone === 'Asia/Seoul', 'busan tz');
require(Math.abs(busan[0].lat - 35.1796) < 0.01, 'busan lat');

const seoul = searchBirthPlaces('서울');
require(seoul[0]?.id === 'kr-seoul', `서울 → ${seoul[0]?.id}`);

const seoulEn = searchBirthPlaces('seoul');
require(seoulEn[0]?.id === 'kr-seoul', 'seoul english');

const gangnam = searchBirthPlaces('강남');
require(gangnam[0]?.id === 'kr-seoul', '강남 alias');

const pusan = searchBirthPlaces('pusan');
require(pusan[0]?.id === 'kr-busan', 'pusan romanization');

const tokyo = searchBirthPlaces('tokyo');
require(tokyo[0]?.id === 'jp-tokyo', 'tokyo');
require(tokyo[0]?.timezone === 'Asia/Tokyo', 'tokyo tz');

const nyc = searchBirthPlaces('new york');
require(nyc[0]?.id === 'us-newyork', 'new york');
require(nyc[0]?.timezone === 'America/New_York', 'nyc tz');

const london = searchBirthPlaces('London');
require(london[0]?.id === 'gb-london', 'london');

const hawaii = searchBirthPlaces('하와이');
require(hawaii[0]?.id === 'us-honolulu', 'hawaii alias');

require(searchBirthPlaces('zzzznotacity').length === 0, 'unknown city');

const selected = findBirthPlaceById('kr-busan');
require(selected, 'find busan');
const location = toBirthLocation(selected);
require(location.label === '부산, 대한민국', location.label);
require(location.timezone === 'Asia/Seoul', location.timezone);
require(displayBirthPlace(selected, 'en') === 'Busan, South Korea', 'en label');

const ids = new Set(BIRTH_PLACES.map((item) => item.id));
require(ids.size === BIRTH_PLACES.length, 'unique ids');
require(BIRTH_PLACES.every((item) => item.timezone.includes('/')), 'iana timezones');

console.log('birth-place: PASS');
