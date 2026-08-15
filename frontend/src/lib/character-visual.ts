export type CharacterCode = 'pathfinder' | 'brightener' | 'steadier' | 'decider' | 'observer';

export const CHARACTER_IMAGE_DIR = '/characters';

export function characterImagePath(codeOrKey: string): string {
  return `${CHARACTER_IMAGE_DIR}/${codeOrKey}.png`;
}

export const CHARACTER_VISUALS: Record<
  CharacterCode,
  { labelKo: string; tone: string; palette: string; motif: string; posture: string }
> = {
  pathfinder: {
    labelKo: '길을 여는 사람',
    tone: '호기심 많고 시작하는',
    palette: 'sage green, leaf-tea, warm ivory',
    motif: 'a tiny paper compass, not a plant god',
    posture: 'one foot stepping forward, looking toward a new path',
  },
  brightener: {
    labelKo: '분위기를 밝히는 사람',
    tone: '명랑하고 드러내는',
    palette: 'terracotta, apricot, warm cream',
    motif: 'a small paper lantern, not a mythical bird',
    posture: 'open chest, easy smile, offering warmth',
  },
  steadier: {
    labelKo: '자리를 지키는 사람',
    tone: '차분하고 돌보는',
    palette: 'warm clay, oatmeal, soft brown',
    motif: 'a ceramic mug, not a mountain spirit',
    posture: 'grounded stance, both feet planted, gentle hands',
  },
  decider: {
    labelKo: '기준을 세우는 사람',
    tone: '또렷하고 정리하는',
    palette: 'muted gold, stone gray, warm white',
    motif: 'a slim notebook, not a blade or beast',
    posture: 'upright, calm, one hand holding a notebook',
  },
  observer: {
    labelKo: '흐름을 읽는 사람',
    tone: '차분하고 깊이 보는',
    palette: 'mist sage, slate blue, paper ivory',
    motif: 'a folded paper boat, not a turtle or dragon',
    posture: 'quiet gaze, slightly turned, listening',
  },
};
