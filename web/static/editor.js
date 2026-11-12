// Editor page (#/editor?ex=<example> | ?new=1): SVG plan editor + WebGL 3D preview + properties + statistics.
import { $, $$, api, app, esc, route, isStatic, download, onLeave } from './core.js';
import { emptyPlan, fromDict, toDict, ENUMS, isDoor, isWindow } from './model.js';
import { createState, fitView, loadAutosave, zoomAt } from './editor_state.js';
import { renderPlan } from './editor_render.js';
import { attachTools } from './editor_tools.js';
import { renderProps, renderStats, deleteSelected } from './editor_props.js';
import { exportPng, exportSvg, openFile, safeName, savePlan } from './editor_io.js';
import { View3D } from './view3d.js';
import { statistics } from './stats.js';

const TOOLS = [['select', 'Select', 'S'], ['wall', 'Wall', 'W'], ['door', 'Door', 'D'], ['window', 'Window', 'N'],
  ['room', 'Room', 'R'], ['measure', 'Measure', 'M'], ['pan', 'Pan', 'H']];
const DOORS = ENUMS.opening_type.filter(t => isDoor(t) || t === 'archway'), WINDOWS = ENUMS.opening_type.filter(isWindow);
const opt = (v, l, on) => `<option value="${esc(v)}"${on ? ' selected' : ''}>${esc(l)}</option>`;
const tname = t => t.replace(/_/g, ' ');

route('editor', async (args, query) => {
  const [catalog, examples] = await Promise.all([api('/catalog'), api('/examples')]);
  let plan, note = '';
  if (query.new) plan = emptyPlan();
  else if (query.ex) { plan = fromDict(await api('/examples/' + encodeURIComponent(query.ex))); note = (examples.find(e => e.name === query.ex) || {}).note || ''; }
  else plan = loadAutosave() || fromDict(await api('/examples/demo_house'));
  const lib = kind => catalog[kind].map(i => opt(i.type, `${i.name} (${i.width}×${i.depth}")`)).join('');
  app().innerHTML = `
  <div class="edhead"><div><p class="kicker">Editor</p><h1 class="glow" id="ed-title"></h1></div>
    <div class="bar">
      <label class="sr" for="ex-sel">Open an example</label>
      <select id="ex-sel">${opt('', 'Examples…')}${examples.map(e => opt(e.name, e.title, e.name === query.ex)).join('')}</select>
      <button class="alt" id="b-new">New</button><button class="alt" id="b-open">Open .floorplan</button>
      <button id="b-save">Save .floorplan</button><button class="alt" id="b-svg">SVG</button><button class="alt" id="b-png">PNG</button>
      <input type="file" id="f-open" accept=".floorplan,.json,application/json" hidden>
    </div></div>
  ${note ? `<p class="mute small">${esc(note)}</p>` : ''}
  <div class="ed">
    <aside class="panel tools" aria-label="Tools">
      <div class="toolgrid" role="toolbar">${TOOLS.map(([k, l, key]) => `<button class="tool" data-tool="${k}" title="${l} (${key})">${l}<kbd>${key}</kbd></button>`).join('')}</div>
      <label for="door-type">Door type</label><select id="door-type">${DOORS.map(t => opt(t, tname(t), t === 'door_single')).join('')}</select>
      <label for="win-type">Window type</label><select id="win-type">${WINDOWS.map(t => opt(t, tname(t), t === 'window_double')).join('')}</select>
      <div class="pair"><div><label for="w-th">Wall thickness (in)</label><input id="w-th" type="number" min="1" step="0.5" value="${catalog.settings.wall_thickness}"></div>
        <div><label for="w-type">Wall type</label><select id="w-type">${ENUMS.wall_type.map(t => opt(t, tname(t), t === 'interior')).join('')}</select></div></div>
      <h3>Library</h3>
      ${['furniture', 'fixtures', 'stairs'].map(k => `<label for="lib-${k}">${k[0].toUpperCase() + k.slice(1)}</label>
        <div class="row"><select id="lib-${k}">${lib(k)}</select><button class="alt" data-place="${k}">Place</button></div>`).join('')}
      <div id="roombox" class="roombox" hidden><h3>New room</h3>
        <label for="r-name">Name</label><input id="r-name" type="text">
        <label for="r-col">Colour</label><input id="r-col" type="color" value="#ffe4b5">
        <button id="b-room">Create room</button><p class="small mute" id="r-count"></p></div>
      <h3>View</h3>
      <label class="chk"><input type="checkbox" id="t-grid" checked> Grid <kbd>G</kbd></label>
      <label class="chk"><input type="checkbox" id="t-dims" checked> Wall lengths <kbd>Ctrl+D</kbd></label>
      <label class="chk"><input type="checkbox" id="t-area" checked> Room areas</label>
      <label for="t-unit">Length labels</label><select id="t-unit">${opt('ft', 'feet-inches')}${opt('auto', 'auto')}${opt('in', 'inches')}</select>
      <div class="bar"><button class="alt" id="b-undo" title="Undo (Ctrl+Z)">Undo</button><button class="alt" id="b-redo" title="Redo (Ctrl+Shift+Z)">Redo</button>
        <button class="alt" id="b-fit" title="Fit to view (Ctrl+0)">Fit</button><button class="alt" id="b-clear" title="Clear measurements">Clear ruler</button></div>
    </aside>
    <section class="stagewrap">
      <div class="bar viewbar" role="tablist" aria-label="View">
        ${[['plan', '2D plan'], ['split', '2D + 3D'], ['3d', '3D']].map(([k, l]) => `<button class="alt vbtn" role="tab" data-view="${k}">${l}</button>`).join('')}
        <span class="mono small" id="cursor"></span></div>
      <div class="stages" id="stages">
        <svg id="plan" class="plan" tabindex="0" role="application" aria-label="Floor plan drawing area"></svg>
        <div class="v3wrap"><canvas id="v3d" tabindex="0" aria-label="3D preview of the floor plan: drag to orbit, Shift-drag to pan, wheel to zoom"></canvas>
          <button class="alt small" id="b-png3d">3D PNG</button></div>
      </div>
      <p class="small" id="status" role="status" aria-live="polite"></p>
    </section>
    <aside class="panel pside"><div id="props"></div>
      <h3>Statistics</h3><pre class="stats" id="stats"></pre>
      ${isStatic() ? '' : '<button class="alt" id="b-check" title="Compute the same statistics with the Python core">Check vs Python</button><p class="small" id="check"></p>'}
    </aside>
  </div>`;

  const S = createState(plan), svg = $('#plan'), v3 = new View3D($('#v3d'));
  const ui = { status: m => { $('#status').textContent = m; }, cursor: m => { $('#cursor').textContent = m; },
    wallThickness: () => Math.max(1, +$('#w-th').value || 6), wallType: () => $('#w-type').value };
  let viewMode = window.innerWidth < 760 ? 'plan' : 'split', t3 = 0;

  const draw = () => {
    svg.setAttribute('viewBox', `0 0 ${S.view.w} ${S.view.h}`);
    svg.innerHTML = renderPlan(S);
    $('#ed-title').textContent = S.plan.name;
    $$('.tool').forEach(b => b.classList.toggle('on', b.dataset.tool === toolKey()));
  };
  const toolKey = () => (S.tool === 'opening' ? (isDoor(S.openingType) || S.openingType === 'archway' ? 'door' : 'window') : S.tool);
  const update3d = (refit = false) => { if (viewMode === 'plan' || !v3.ok) return; clearTimeout(t3); t3 = setTimeout(() => v3.setPlan(S.plan, refit), 60); };
  const roomBox = () => { const box = $('#roombox'); box.hidden = S.tool !== 'room'; $('#r-count').textContent = `${S.roomPick.length} wall(s) picked`; };
  S.on(what => {
    draw();
    if (what === 'plan' || what === 'select') renderProps(S, $('#props'));
    if (what === 'plan') { renderStats(S, $('#stats')); update3d(); }
    if (what === 'pick' || what === 'tool') roomBox();
  });

  function setTool(k) {
    S.temp = null; S.hover = null;
    if (k === 'door') { S.tool = 'opening'; S.openingType = $('#door-type').value; }
    else if (k === 'window') { S.tool = 'opening'; S.openingType = $('#win-type').value; }
    else S.tool = k;
    if (k !== 'room') S.roomPick = [];
    else if (!$('#r-name').value) $('#r-name').value = `Room ${S.plan.rooms.length + 1}`;
    svg.classList.toggle('panning', k === 'pan');
    ui.status({ select: 'Click to select; drag to move; corner handles resize, the round handle rotates (15° steps, Shift = free).',
      wall: 'Click the start point, then each corner; double-click, right-click or Esc to stop. Snaps to wall ends, then the 1 ft grid.',
      door: 'Click on a wall to add a door.', window: 'Click on a wall to add a window.',
      room: 'Click the walls around the room (any order), then Create room or press Enter.',
      measure: 'Click two points to measure distance and angle.', pan: 'Drag to pan; wheel zooms.' }[k] || '');
    S.emit('tool');
  }
  function createRoom() {
    if (S.roomPick.length < 3) return ui.status('Need at least 3 walls to create a room');
    S.checkpoint();
    const r = { id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()), name: $('#r-name').value || `Room ${S.plan.rooms.length + 1}`,
      wall_ids: S.roomPick.slice(), color: $('#r-col').value };
    S.plan.rooms.push(r); S.roomPick = []; S.sel = { kind: 'room', id: r.id };
    $('#r-name').value = `Room ${S.plan.rooms.length + 1}`;
    ui.status(`Created room: ${r.name}`); S.emit('plan'); roomBox();
  }
  function setView(k) {
    viewMode = k;
    $('#stages').dataset.view = k;
    $$('.vbtn').forEach(b => b.setAttribute('aria-selected', String(b.dataset.view === k)));
    resize(); if (k !== 'plan') update3d(true);
  }
  function resize() {
    const r = svg.getBoundingClientRect();
    const first = S.view.w === 800 && S.view.h === 600;
    S.view.w = Math.max(50, r.width); S.view.h = Math.max(50, r.height);
    if (first) fitView(S);
    draw(); if (viewMode !== 'plan') v3.draw();
  }
  async function loadPlan(p, msg) { S.load(p); renderProps(S, $('#props')); renderStats(S, $('#stats')); update3d(true); ui.status(msg); }

  $$('.tool').forEach(b => b.addEventListener('click', () => setTool(b.dataset.tool)));
  $('#door-type').addEventListener('change', () => setTool('door'));
  $('#win-type').addEventListener('change', () => setTool('window'));
  $$('[data-place]').forEach(b => b.addEventListener('click', () => {
    const k = b.dataset.place, item = catalog[k].find(i => i.type === $('#lib-' + k).value);
    S.libItem = { kind: { furniture: 'furniture', fixtures: 'fixture', stairs: 'stair' }[k], ...item };
    S.tool = 'place'; S.temp = null;
    ui.status(k === 'stairs' ? `Click the start and end of the ${item.name}` : `Click to place: ${item.name} (Esc to stop)`);
    S.emit('tool');
  }));
  $('#b-room').addEventListener('click', createRoom);
  for (const [id, key] of [['#t-grid', 'showGrid'], ['#t-dims', 'showDims'], ['#t-area', 'showAreas']]) {
    $(id).addEventListener('change', e => { S[key] = e.target.checked; S.emit('view'); });
  }
  $('#t-unit').addEventListener('change', e => { S.unit = e.target.value; S.emit('select'); });
  $('#b-undo').addEventListener('click', () => S.doUndo());
  $('#b-redo').addEventListener('click', () => S.doRedo());
  $('#b-fit').addEventListener('click', () => { fitView(S); S.emit('view'); });
  $('#b-clear').addEventListener('click', () => { S.measurements = []; S.emit('view'); });
  $$('.vbtn').forEach(b => b.addEventListener('click', () => setView(b.dataset.view)));
  $('#ex-sel').addEventListener('change', async e => {
    if (!e.target.value) return;
    const ex = examples.find(x => x.name === e.target.value);
    await loadPlan(fromDict(await api('/examples/' + e.target.value, { fresh: true })), `Opened example: ${ex.title}`);
  });
  $('#b-new').addEventListener('click', () => { loadPlan(emptyPlan(), 'New floor plan: pick the Wall tool (W) to start drawing'); setTool('wall'); });
  $('#b-open').addEventListener('click', () => $('#f-open').click());
  $('#f-open').addEventListener('change', async e => {
    const f = e.target.files[0]; e.target.value = '';
    if (!f) return;
    try { await loadPlan(await openFile(f), `Opened ${f.name}`); } catch (err) { ui.status(`Could not open ${f.name}: ${err.message}`); }
  });
  $('#b-save').addEventListener('click', () => { savePlan(S); ui.status('Saved .floorplan (opens in the desktop app with File > Open)'); });
  $('#b-svg').addEventListener('click', () => exportSvg(S));
  $('#b-png').addEventListener('click', () => exportPng(S).catch(err => ui.status(err.message)));
  $('#b-png3d').addEventListener('click', async () => { if (v3.ok) download(safeName(S.plan.name) + '_3d.png', await v3.pngBlob()); });
  const chk = $('#b-check');
  if (chk) chk.addEventListener('click', async () => {
    const py = await api('/analyze', { body: toDict(S.plan) }), js = statistics(S.plan);
    let max = 0;
    const walk = (a, b) => { if (typeof b === 'number') max = Math.max(max, Math.abs(a - b)); else if (b && typeof b === 'object') for (const k of Object.keys(b)) walk(a?.[k], b[k]); };
    walk(js, py.stats);
    $('#check').textContent = Number.isFinite(max) ? `Python core agrees: max |JS − Python| = ${max.toExponential(1)}` : 'Python and JS differ (see console)';
    if (!Number.isFinite(max)) console.warn({ js, py });
  });

  const onKey = e => {
    if (e.target.closest && e.target.closest('input, select, textarea')) return;
    const mod = e.ctrlKey || e.metaKey, k = e.key.toLowerCase();
    if (mod && k === 'z') { e.preventDefault(); return e.shiftKey ? S.doRedo() : S.doUndo(); }
    if (mod && k === 'y') { e.preventDefault(); return S.doRedo(); }
    if (mod && k === 's') { e.preventDefault(); return savePlan(S); }
    if (mod && k === 'o') { e.preventDefault(); return $('#f-open').click(); }
    if (mod && k === 'd') { e.preventDefault(); $('#t-dims').click(); return; }
    if (mod && k === '0') { e.preventDefault(); fitView(S); return S.emit('view'); }
    if (mod) return;
    if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); return deleteSelected(S); }
    if (e.key === 'Escape') { S.temp = null; S.roomPick = []; S.sel = null; if (S.tool === 'place') S.tool = 'select'; S.emit('select'); return roomBox(); }
    if (e.key === 'Enter' && S.tool === 'room') return createRoom();
    if (e.target === $('#v3d')) return;
    const t = TOOLS.find(x => x[2].toLowerCase() === k);
    if (t) return setTool(t[0]);
    if (k === 'g') return $('#t-grid').click();
    if (k === '+' || k === '=' || k === '-') { zoomAt(S, k === '-' ? 1 / 1.2 : 1.2, S.view.w / 2, S.view.h / 2); S.emit('view'); }
  };
  document.addEventListener('keydown', onKey);
  const ro = new ResizeObserver(resize);
  ro.observe(svg);
  onLeave(() => { document.removeEventListener('keydown', onKey); ro.disconnect(); });

  attachTools(S, svg, ui);
  if (!v3.ok) $('.v3wrap').innerHTML = '<p class="static-note">WebGL is not available in this browser, so the 3D preview is off.</p>';
  setView(viewMode);
  renderProps(S, $('#props')); renderStats(S, $('#stats'));
  setTool('select');
  ui.status(query.ex ? `Opened example: ${(examples.find(e => e.name === query.ex) || {}).title || query.ex}` : 'Ready');
});
