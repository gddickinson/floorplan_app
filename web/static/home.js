// Home page: hero, counts from the catalog, examples and what the editor does.
import { api, app, esc, route } from './core.js';
import { previewSvg } from './preview.js';

route('home', async () => {
  const [info, examples] = await Promise.all([api('/info'), api('/examples')]);
  const demo = await api('/examples/demo_house');
  app().innerHTML = `
  <section class="hero"><p class="kicker">2D drafting · 3D preview · in your browser</p>
    <h1 class="glow">Floor Plan Editor</h1>
    <p class="lead">${esc(info.description)} This site is the editor itself: draw walls on a 1 ft grid with snapping,
      put in doors and windows, close rooms to get their areas, furnish them from the desktop app's library and walk
      around the result in a WebGL 3D view. Files are saved in the desktop app's <code>.floorplan</code> format.</p>
    <a class="btn" href="#/editor?ex=demo_house">Open the demo house</a><a class="btn alt" href="#/editor?new=1">Start a new plan</a></section>
  <div class="tiles">
    <div class="tile"><b>${info.furniture}</b><span>furniture types</span></div>
    <div class="tile"><b>${info.fixtures}</b><span>fixture types</span></div>
    <div class="tile"><b>${info.stairs}</b><span>stair types</span></div>
    <div class="tile"><b>${info.opening_types}</b><span>door / window / archway types</span></div>
    <div class="tile"><b>${info.grid_inches / 12} ft</b><span>snap grid</span></div>
  </div>
  <a class="card excard" href="#/editor?ex=demo_house">${previewSvg(demo, 1000, 330, 'Demo house plan')}<b>Demo House</b>
    <span>${esc(examples[0].note)}</span></a>
  <h2>What you can do</h2>
  <div class="grid wide">
    <div class="card"><b>Draw</b><span>Walls snap to existing wall ends (within 6 inches) and then to the 1 ft grid, exactly
      as on the desktop canvas. Drag a corner and every wall joined there follows.</span></div>
    <div class="card"><b>Doors, windows, rooms</b><span>Nine door types, ten window types and archways cut into walls.
      Click a room's walls in any order: the outline is found by joining them, and its area and perimeter are shown.</span></div>
    <div class="card"><b>Furnish</b><span>The desktop Object Library: beds, sofas, tables, kitchen and bathroom fixtures,
      stairs. Move, resize with corner handles, rotate in 15° steps.</span></div>
    <div class="card"><b>See it in 3D</b><span>Walls at their real heights with door and window openings (sills and
      lintels), coloured by wall style; orbit, pan and zoom.</span></div>
    <div class="card"><b>Measure and count</b><span>Feet-inches dimension labels, a measuring tool, and the desktop
      Statistics: wall lengths, door and window counts, room areas.</span></div>
    <div class="card"><b>Save, open, export</b><span>.floorplan files move between this page and the desktop app;
      export the plan as SVG or PNG, the 3D view as PNG. Your work is also kept in this browser.</span></div>
  </div>`;
});
