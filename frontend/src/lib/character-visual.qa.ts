import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { CHARACTER_VISUALS, characterImagePath } from './character-visual';

function require(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const codes = Object.keys(CHARACTER_VISUALS);
require(codes.length === 5, `expected 5 archetypes, got ${codes.length}`);
for (const code of codes) {
  const webPath = characterImagePath(code);
  require(webPath === `/characters/${code}.png`, webPath);
  const disk = resolve(import.meta.dir, '../../public', webPath.slice(1));
  require(existsSync(disk), `missing archetype fallback ${disk}`);
  const bytes = readFileSync(disk);
  require(bytes.length > 50_000, `${code} too small: ${bytes.length}`);
  require(bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4e && bytes[3] === 0x47, `${code} is not PNG`);
}
require(characterImagePath('brightener_shinyak_water_metal_high_male') === '/characters/brightener_shinyak_water_metal_high_male.png', 'keyed path');

console.log('character-visual-qa: PASS');
