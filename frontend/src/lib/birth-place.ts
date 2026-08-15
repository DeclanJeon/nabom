export type BirthPlace = {
  id: string;
  labelKo: string;
  labelEn: string;
  countryKo: string;
  countryEn: string;
  lat: number;
  lon: number;
  timezone: string;
  aliases: string[];
};

export type BirthPlaceHit = BirthPlace & {
  displayLabel: string;
  secondary: string;
};

function place(
  id: string,
  labelKo: string,
  labelEn: string,
  countryKo: string,
  countryEn: string,
  lat: number,
  lon: number,
  timezone: string,
  aliases: string[] = [],
): BirthPlace {
  return { id, labelKo, labelEn, countryKo, countryEn, lat, lon, timezone, aliases };
}

const KR = '대한민국';
const KR_EN = 'South Korea';
const SEOUL_TZ = 'Asia/Seoul';

export const BIRTH_PLACES: BirthPlace[] = [
  place('kr-seoul', '서울', 'Seoul', KR, KR_EN, 37.5665, 126.978, SEOUL_TZ, [
    '서울특별시',
    '서울시',
    '강남',
    '강남구',
    '송파',
    '마포',
    '종로',
    'seoul',
  ]),
  place('kr-busan', '부산', 'Busan', KR, KR_EN, 35.1796, 129.0756, SEOUL_TZ, [
    '부산광역시',
    '부산시',
    '해운대',
    '해운대구',
    'busan',
    'pusan',
  ]),
  place('kr-incheon', '인천', 'Incheon', KR, KR_EN, 37.4563, 126.7052, SEOUL_TZ, [
    '인천광역시',
    '인천시',
    'incheon',
    'inchon',
  ]),
  place('kr-daegu', '대구', 'Daegu', KR, KR_EN, 35.8714, 128.6014, SEOUL_TZ, [
    '대구광역시',
    '대구시',
    'daegu',
    'taegu',
  ]),
  place('kr-daejeon', '대전', 'Daejeon', KR, KR_EN, 36.3504, 127.3845, SEOUL_TZ, [
    '대전광역시',
    '대전시',
    'daejeon',
    'taejon',
  ]),
  place('kr-gwangju', '광주', 'Gwangju', KR, KR_EN, 35.1595, 126.8526, SEOUL_TZ, [
    '광주광역시',
    '광주시',
    'gwangju',
    'kwangju',
  ]),
  place('kr-ulsan', '울산', 'Ulsan', KR, KR_EN, 35.5384, 129.3114, SEOUL_TZ, ['울산광역시', '울산시', 'ulsan']),
  place('kr-sejong', '세종', 'Sejong', KR, KR_EN, 36.48, 127.289, SEOUL_TZ, ['세종특별자치시', '세종시', 'sejong']),
  place('kr-suwon', '수원', 'Suwon', KR, KR_EN, 37.2636, 127.0286, SEOUL_TZ, ['수원시', 'suwon']),
  place('kr-seongnam', '성남', 'Seongnam', KR, KR_EN, 37.4201, 127.1265, SEOUL_TZ, [
    '성남시',
    '분당',
    '판교',
    'seongnam',
    'bundang',
  ]),
  place('kr-goyang', '고양', 'Goyang', KR, KR_EN, 37.6584, 126.832, SEOUL_TZ, ['고양시', '일산', 'goyang', 'ilsan']),
  place('kr-yongin', '용인', 'Yongin', KR, KR_EN, 37.2411, 127.1776, SEOUL_TZ, ['용인시', 'yongin']),
  place('kr-bucheon', '부천', 'Bucheon', KR, KR_EN, 37.5034, 126.766, SEOUL_TZ, ['부천시', 'bucheon']),
  place('kr-ansan', '안산', 'Ansan', KR, KR_EN, 37.3219, 126.8309, SEOUL_TZ, ['안산시', 'ansan']),
  place('kr-anyang', '안양', 'Anyang', KR, KR_EN, 37.3943, 126.9568, SEOUL_TZ, ['안양시', 'anyang']),
  place('kr-namyangju', '남양주', 'Namyangju', KR, KR_EN, 37.636, 127.2165, SEOUL_TZ, ['남양주시', 'namyangju']),
  place('kr-hwaseong', '화성', 'Hwaseong', KR, KR_EN, 37.1995, 126.8314, SEOUL_TZ, ['화성시', 'hwaseong']),
  place('kr-pyeongtaek', '평택', 'Pyeongtaek', KR, KR_EN, 36.9921, 127.1129, SEOUL_TZ, ['평택시', 'pyeongtaek']),
  place('kr-uijeongbu', '의정부', 'Uijeongbu', KR, KR_EN, 37.7381, 127.0337, SEOUL_TZ, ['의정부시', 'uijeongbu']),
  place('kr-paju', '파주', 'Paju', KR, KR_EN, 37.7599, 126.7802, SEOUL_TZ, ['파주시', 'paju']),
  place('kr-gimpo', '김포', 'Gimpo', KR, KR_EN, 37.6153, 126.7156, SEOUL_TZ, ['김포시', 'gimpo']),
  place('kr-gwangmyeong', '광명', 'Gwangmyeong', KR, KR_EN, 37.4786, 126.8644, SEOUL_TZ, ['광명시', 'gwangmyeong']),
  place('kr-hanam', '하남', 'Hanam', KR, KR_EN, 37.5393, 127.2146, SEOUL_TZ, ['하남시', 'hanam']),
  place('kr-icheon', '이천', 'Icheon', KR, KR_EN, 37.272, 127.435, SEOUL_TZ, ['이천시', 'icheon']),
  place('kr-chuncheon', '춘천', 'Chuncheon', KR, KR_EN, 37.8813, 127.73, SEOUL_TZ, ['춘천시', 'chuncheon']),
  place('kr-wonju', '원주', 'Wonju', KR, KR_EN, 37.3422, 127.9202, SEOUL_TZ, ['원주시', 'wonju']),
  place('kr-gangneung', '강릉', 'Gangneung', KR, KR_EN, 37.7519, 128.8761, SEOUL_TZ, ['강릉시', 'gangneung']),
  place('kr-cheongju', '청주', 'Cheongju', KR, KR_EN, 36.6424, 127.489, SEOUL_TZ, ['청주시', 'cheongju']),
  place('kr-cheonan', '천안', 'Cheonan', KR, KR_EN, 36.8151, 127.1139, SEOUL_TZ, ['천안시', 'cheonan']),
  place('kr-asan', '아산', 'Asan', KR, KR_EN, 36.7898, 127.0018, SEOUL_TZ, ['아산시', 'asan']),
  place('kr-jeonju', '전주', 'Jeonju', KR, KR_EN, 35.8242, 127.148, SEOUL_TZ, ['전주시', 'jeonju']),
  place('kr-gunsan', '군산', 'Gunsan', KR, KR_EN, 35.9677, 126.7366, SEOUL_TZ, ['군산시', 'gunsan']),
  place('kr-iksan', '익산', 'Iksan', KR, KR_EN, 35.9483, 126.9576, SEOUL_TZ, ['익산시', 'iksan']),
  place('kr-mokpo', '목포', 'Mokpo', KR, KR_EN, 34.8118, 126.3922, SEOUL_TZ, ['목포시', 'mokpo']),
  place('kr-yeosu', '여수', 'Yeosu', KR, KR_EN, 34.7604, 127.6622, SEOUL_TZ, ['여수시', 'yeosu']),
  place('kr-suncheon', '순천', 'Suncheon', KR, KR_EN, 34.9506, 127.4872, SEOUL_TZ, ['순천시', 'suncheon']),
  place('kr-pohang', '포항', 'Pohang', KR, KR_EN, 36.019, 129.3435, SEOUL_TZ, ['포항시', 'pohang']),
  place('kr-gyeongju', '경주', 'Gyeongju', KR, KR_EN, 35.8562, 129.2247, SEOUL_TZ, ['경주시', 'gyeongju']),
  place('kr-andong', '안동', 'Andong', KR, KR_EN, 36.5684, 128.7294, SEOUL_TZ, ['안동시', 'andong']),
  place('kr-gumi', '구미', 'Gumi', KR, KR_EN, 36.1195, 128.3446, SEOUL_TZ, ['구미시', 'gumi']),
  place('kr-changwon', '창원', 'Changwon', KR, KR_EN, 35.228, 128.6811, SEOUL_TZ, ['창원시', '마산', '진해', 'changwon']),
  place('kr-gimhae', '김해', 'Gimhae', KR, KR_EN, 35.2285, 128.8894, SEOUL_TZ, ['김해시', 'gimhae']),
  place('kr-jinju', '진주', 'Jinju', KR, KR_EN, 35.1802, 128.1076, SEOUL_TZ, ['진주시', 'jinju']),
  place('kr-yangsan', '양산', 'Yangsan', KR, KR_EN, 35.335, 129.037, SEOUL_TZ, ['양산시', 'yangsan']),
  place('kr-jeju', '제주', 'Jeju', KR, KR_EN, 33.4996, 126.5312, SEOUL_TZ, [
    '제주시',
    '제주특별자치도',
    '서귀포',
    'jeju',
    'jeju-do',
  ]),
  place('jp-tokyo', '도쿄', 'Tokyo', '일본', 'Japan', 35.6762, 139.6503, 'Asia/Tokyo', [
    '동경',
    'tokyo',
    'toukyou',
    '東京',
  ]),
  place('jp-osaka', '오사카', 'Osaka', '일본', 'Japan', 34.6937, 135.5023, 'Asia/Tokyo', ['osaka', '大阪']),
  place('jp-fukuoka', '후쿠오카', 'Fukuoka', '일본', 'Japan', 33.5904, 130.4017, 'Asia/Tokyo', ['fukuoka', '福岡']),
  place('cn-beijing', '베이징', 'Beijing', '중국', 'China', 39.9042, 116.4074, 'Asia/Shanghai', [
    '북경',
    'beijing',
    'peking',
  ]),
  place('cn-shanghai', '상하이', 'Shanghai', '중국', 'China', 31.2304, 121.4737, 'Asia/Shanghai', [
    '상해',
    'shanghai',
  ]),
  place('hk-hongkong', '홍콩', 'Hong Kong', '홍콩', 'Hong Kong', 22.3193, 114.1694, 'Asia/Hong_Kong', [
    'hongkong',
    'hong kong',
  ]),
  place('tw-taipei', '타이베이', 'Taipei', '대만', 'Taiwan', 25.033, 121.5654, 'Asia/Taipei', [
    '台北',
    'taipei',
    '타이페이',
  ]),
  place('sg-singapore', '싱가포르', 'Singapore', '싱가포르', 'Singapore', 1.3521, 103.8198, 'Asia/Singapore', [
    'singapore',
  ]),
  place('th-bangkok', '방콕', 'Bangkok', '태국', 'Thailand', 13.7563, 100.5018, 'Asia/Bangkok', ['bangkok']),
  place('vn-hanoi', '하노이', 'Hanoi', '베트남', 'Vietnam', 21.0278, 105.8342, 'Asia/Bangkok', ['hanoi']),
  place('vn-hcmc', '호치민', 'Ho Chi Minh City', '베트남', 'Vietnam', 10.8231, 106.6297, 'Asia/Ho_Chi_Minh', [
    '사이공',
    'saigon',
    'ho chi minh',
    'hcmc',
  ]),
  place('ph-manila', '마닐라', 'Manila', '필리핀', 'Philippines', 14.5995, 120.9842, 'Asia/Manila', ['manila']),
  place('id-jakarta', '자카르타', 'Jakarta', '인도네시아', 'Indonesia', -6.2088, 106.8456, 'Asia/Jakarta', [
    'jakarta',
  ]),
  place('my-kl', '쿠알라룸푸르', 'Kuala Lumpur', '말레이시아', 'Malaysia', 3.139, 101.6869, 'Asia/Kuala_Lumpur', [
    'kuala lumpur',
    'kl',
  ]),
  place('in-delhi', '델리', 'New Delhi', '인도', 'India', 28.6139, 77.209, 'Asia/Kolkata', [
    'new delhi',
    'delhi',
  ]),
  place('ae-dubai', '두바이', 'Dubai', '아랍에미리트', 'United Arab Emirates', 25.2048, 55.2708, 'Asia/Dubai', [
    'dubai',
  ]),
  place('tr-istanbul', '이스탄불', 'Istanbul', '튀르키예', 'Türkiye', 41.0082, 28.9784, 'Europe/Istanbul', [
    'istanbul',
    '콘스탄티노플',
  ]),
  place('us-newyork', '뉴욕', 'New York', '미국', 'United States', 40.7128, -74.006, 'America/New_York', [
    'new york',
    'nyc',
    'newyork',
  ]),
  place('us-losangeles', '로스앤젤레스', 'Los Angeles', '미국', 'United States', 34.0522, -118.2437, 'America/Los_Angeles', [
    'la',
    'los angeles',
    '엘에이',
  ]),
  place('us-sanfrancisco', '샌프란시스코', 'San Francisco', '미국', 'United States', 37.7749, -122.4194, 'America/Los_Angeles', [
    'san francisco',
    'sf',
  ]),
  place('us-seattle', '시애틀', 'Seattle', '미국', 'United States', 47.6062, -122.3321, 'America/Los_Angeles', [
    'seattle',
  ]),
  place('us-chicago', '시카고', 'Chicago', '미국', 'United States', 41.8781, -87.6298, 'America/Chicago', [
    'chicago',
  ]),
  place('us-boston', '보스턴', 'Boston', '미국', 'United States', 42.3601, -71.0589, 'America/New_York', [
    'boston',
  ]),
  place('us-honolulu', '호놀룰루', 'Honolulu', '미국', 'United States', 21.3069, -157.8583, 'Pacific/Honolulu', [
    'honolulu',
    '하와이',
    'hawaii',
  ]),
  place('ca-vancouver', '밴쿠버', 'Vancouver', '캐나다', 'Canada', 49.2827, -123.1207, 'America/Vancouver', [
    'vancouver',
  ]),
  place('ca-toronto', '토론토', 'Toronto', '캐나다', 'Canada', 43.6532, -79.3832, 'America/Toronto', ['toronto']),
  place('gb-london', '런던', 'London', '영국', 'United Kingdom', 51.5074, -0.1278, 'Europe/London', ['london']),
  place('fr-paris', '파리', 'Paris', '프랑스', 'France', 48.8566, 2.3522, 'Europe/Paris', ['paris']),
  place('de-berlin', '베를린', 'Berlin', '독일', 'Germany', 52.52, 13.405, 'Europe/Berlin', ['berlin']),
  place('nl-amsterdam', '암스테르담', 'Amsterdam', '네덜란드', 'Netherlands', 52.3676, 4.9041, 'Europe/Amsterdam', [
    'amsterdam',
  ]),
  place('es-madrid', '마드리드', 'Madrid', '스페인', 'Spain', 40.4168, -3.7038, 'Europe/Madrid', ['madrid']),
  place('it-rome', '로마', 'Rome', '이탈리아', 'Italy', 41.9028, 12.4964, 'Europe/Rome', ['rome', 'roma']),
  place('ch-zurich', '취리히', 'Zurich', '스위스', 'Switzerland', 47.3769, 8.5417, 'Europe/Zurich', ['zurich']),
  place('au-sydney', '시드니', 'Sydney', '호주', 'Australia', -33.8688, 151.2093, 'Australia/Sydney', ['sydney']),
  place('au-melbourne', '멜버른', 'Melbourne', '호주', 'Australia', -37.8136, 144.9631, 'Australia/Melbourne', [
    'melbourne',
  ]),
  place('nz-auckland', '오클랜드', 'Auckland', '뉴질랜드', 'New Zealand', -36.8509, 174.7645, 'Pacific/Auckland', [
    'auckland',
  ]),
  place('br-saopaulo', '상파울루', 'São Paulo', '브라질', 'Brazil', -23.5505, -46.6333, 'America/Sao_Paulo', [
    'sao paulo',
    'são paulo',
  ]),
  place('mx-mexicocity', '멕시코시티', 'Mexico City', '멕시코', 'Mexico', 19.4326, -99.1332, 'America/Mexico_City', [
    'mexico city',
    'mexico',
  ]),
];

export const QUICK_BIRTH_PLACES = [
  'kr-seoul',
  'kr-busan',
  'kr-incheon',
  'kr-daegu',
  'jp-tokyo',
  'us-newyork',
  'gb-london',
].map((id) => {
  const found = BIRTH_PLACES.find((item) => item.id === id);
  if (!found) throw new Error(`missing quick place ${id}`);
  return found;
});

export function normalizePlaceQuery(raw: string): string {
  return raw
    .trim()
    .toLowerCase()
    .replace(/[.,]/g, ' ')
    .replace(/\s+/g, ' ');
}

function compact(value: string): string {
  return normalizePlaceQuery(value).replace(/\s+/g, '');
}

function tokensOf(placeItem: BirthPlace): string[] {
  return [
    placeItem.labelKo,
    placeItem.labelEn,
    placeItem.countryKo,
    placeItem.countryEn,
    ...placeItem.aliases,
  ].map(compact);
}

function scorePlace(placeItem: BirthPlace, query: string): number {
  if (!query) return 0;
  const compactQuery = compact(query);
  if (!compactQuery) return 0;
  const tokens = tokensOf(placeItem);
  if (tokens.some((token) => token === compactQuery)) return 300;
  if (tokens.some((token) => token.startsWith(compactQuery))) return 200;
  if (tokens.some((token) => token.includes(compactQuery))) return 100;
  const spaced = normalizePlaceQuery(query);
  if (spaced.includes(' ') && tokens.some((token) => token.includes(compact(spaced)))) return 90;
  return 0;
}

export function displayBirthPlace(placeItem: BirthPlace, locale: 'ko' | 'en' = 'ko'): string {
  return locale === 'en'
    ? `${placeItem.labelEn}, ${placeItem.countryEn}`
    : `${placeItem.labelKo}, ${placeItem.countryKo}`;
}

export function toBirthLocation(placeItem: BirthPlace) {
  return {
    label: displayBirthPlace(placeItem),
    lat: placeItem.lat,
    lon: placeItem.lon,
    timezone: placeItem.timezone,
  };
}

export function searchBirthPlaces(raw: string, limit = 8): BirthPlaceHit[] {
  const query = normalizePlaceQuery(raw);
  if (!query) return [];
  return BIRTH_PLACES.map((item) => ({ item, score: scorePlace(item, query) }))
    .filter((entry) => entry.score > 0)
    .sort((left, right) => {
      if (right.score !== left.score) return right.score - left.score;
      const leftKr = left.item.countryKo === KR ? 0 : 1;
      const rightKr = right.item.countryKo === KR ? 0 : 1;
      if (leftKr !== rightKr) return leftKr - rightKr;
      return left.item.labelKo.localeCompare(right.item.labelKo, 'ko');
    })
    .slice(0, limit)
    .map(({ item }) => ({
      ...item,
      displayLabel: displayBirthPlace(item),
      secondary: `${item.labelEn} · ${item.timezone}`,
    }));
}

export function findBirthPlaceById(id: string): BirthPlace | undefined {
  return BIRTH_PLACES.find((item) => item.id === id);
}
