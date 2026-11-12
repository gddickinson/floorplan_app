// Small read-only plan previews (example cards): the editor's own renderer on a fitted view.
import { fromDict } from './model.js';
import { createState, fitView } from './editor_state.js';
import { renderPlan } from './editor_render.js';

export function previewSvg(dict, w = 400, h = 190, label) {
  const S = createState(fromDict(dict));
  S.view.w = w; S.view.h = h; S.showGrid = false; S.showDims = false;
  fitView(S);
  return `<svg class="thumb plan" viewBox="0 0 ${w} ${h}" role="img" aria-label="${label || 'Floor plan preview'}">${renderPlan(S)}</svg>`;
}
