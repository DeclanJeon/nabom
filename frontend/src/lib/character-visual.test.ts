import { CHARACTER_VISUALS, characterImagePath } from './character-visual';

function require(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

require(characterImagePath('brightener') === '/characters/brightener.png', 'brightener path');
require(characterImagePath('pathfinder') === '/characters/pathfinder.png', 'pathfinder path');
require(CHARACTER_VISUALS.brightener.labelKo === '분위기를 밝히는 사람', 'fire voice');
require(!Object.values(CHARACTER_VISUALS).some((item) => /주작|백호|청룡|현무|황룡|일간|병화/.test(JSON.stringify(item))), 'no myeongni leak');

console.log('character-visual: PASS');
