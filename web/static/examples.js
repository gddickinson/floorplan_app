// Examples page: the plans built by the repo's own code, with previews and .floorplan downloads.
import { $$, api, app, esc, route, download } from './core.js';
import { fromDict, toFileText } from './model.js';
import { previewSvg } from './preview.js';

route('examples', async () => {
  const list = await api('/examples');
  const plans = await Promise.all(list.map(e => api('/examples/' + e.name)));
  app().innerHTML = `<p class="kicker">Examples</p><h1 class="glow">Example plans</h1>
  <p class="lead">Plans built by the repository's own Python code (<code>core/demo_plans.py</code>). Open one in the
    editor, or download it as a <code>.floorplan</code> file for the desktop app (File &gt; Open).</p>
  <div class="grid wide">${list.map((e, i) => `<div class="card excard">
    <a href="#/editor?ex=${e.name}">${previewSvg(plans[i], 400, 190, esc(e.title) + ' preview')}</a>
    <b>${esc(e.title)}</b><small>${e.walls} walls · ${e.openings} openings · ${e.rooms} rooms · ${e.objects} objects</small>
    <span>${esc(e.note)}</span>
    <div class="bar"><a class="btn" href="#/editor?ex=${e.name}">Edit</a>
      <button class="alt" data-dl="${i}">Download .floorplan</button></div></div>`).join('')}</div>`;
  $$('[data-dl]').forEach(b => b.addEventListener('click', () => {
    const i = +b.dataset.dl;
    download(list[i].name + '.floorplan', toFileText(fromDict(plans[i])), 'application/json');
  }));
});
