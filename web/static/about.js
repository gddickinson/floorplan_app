// About page: what the app is, how the web editor relates to the desktop code, how to run both, credits.
import { app, route } from './core.js';

route('about', () => {
  app().innerHTML = `<p class="kicker">About</p><h1 class="glow">How it works</h1>
  <p class="lead">Floor Plan Editor is an interactive 2D architectural floor plan editor built with Python and PyQt6:
    walls, doors, windows, rooms, furniture, fixtures, stairs and multi-floor buildings, with import of iPhone LiDAR
    scans (Apple RoomPlan JSON). This web version is the same editor's model and geometry ported to JavaScript, so the
    GitHub Pages site works with no server.</p>
  <h2>Model and units</h2>
  <p>Everything is in inches, as in <code>core/geometry.py</code>: a <b>wall</b> is a centre line with thickness
    (default 6"), height (96") type and style; a <b>door or window</b> sits at a fraction 0–1 along a wall with a width,
    a height and (windows) a sill height; a <b>room</b> is a name, a colour and the list of its walls; furniture and
    fixtures are rectangles with a centre, width, depth and rotation; stairs run from a start to an end point.
    Lengths are shown in feet and inches (<code>format_dimension</code>), areas in square feet.</p>
  <h3>Geometry shared with the desktop app</h3>
  <ul>
    <li><b>Snapping</b>: a click within 6" of a wall end snaps to it, otherwise to the 1 ft grid (Python's round-half-even
      included).</li>
    <li><b>Room outlines</b>: the room's walls are joined by shared ends and T-junctions, in any order, and a corner is
      placed where consecutive wall centre lines meet; area (shoelace) and perimeter come from that outline.</li>
    <li><b>Openings</b> are placed where the click projects onto the wall, kept between 10 % and 90 % of its length.</li>
    <li><b>Statistics</b>: wall lengths by type, door/window/archway counts, room areas and perimeters, plan bounds.</li>
  </ul>
  <p>These live in Qt-free Python modules (<code>core/snapping.py</code>, <code>core/room_geometry.py</code>,
    <code>core/plan_stats.py</code>, <code>core/units.py</code>) that the desktop canvas also uses. The JavaScript port
    (<code>model.js</code>, <code>geometry.js</code>, <code>stats.js</code>, <code>units.js</code>) is checked against them
    by a node test on a fixture written by the Python code: three plans, about 3,000 values (outlines, areas,
    perimeters, statistics, snapping, hit tests, file round trips, labels), largest difference about 1e-14.</p>
  <h3>The 3D view</h3>
  <p>Raw WebGL, no libraries. Walls are boxes at their own height and thickness, extended at joined ends so corners
    close; doors and archways leave an opening up to their height, windows from the sill to the sill plus their
    height. Room floors use the room colours and the wall colours follow the desktop 3D viewer's style colours.
    The file format has no heights for furniture and fixtures, so their 3D blocks use typical display heights; stairs
    rise to the plan's ceiling height in their number of steps.</p>
  <h2>Files</h2>
  <p><b>Save .floorplan</b> writes the same JSON as <code>FloorPlan.save_to_file</code> (key for key); <b>Open</b>
    accepts files from the desktop app and checks them as <code>FloorPlan.from_dict</code> does. A test opens files
    saved by the web model in the Python loader and compares them field by field. <b>SVG</b> and <b>PNG</b> export a
    light print version of the plan; <b>3D PNG</b> saves the 3D view. Not in the web version: multi-floor buildings,
    iPhone scan import and PDF export (desktop only).</p>
  <h2>Run it yourself</h2>
  <h3>Desktop app</h3>
  <pre>pip install -r requirements.txt
python main.py [plan.floorplan]</pre>
  <h3>Web app (local)</h3>
  <pre>pip install -r requirements-web.txt
python run_web.py          # http://127.0.0.1:8217</pre>
  <p>The local app serves the same pages plus <code>POST /api/analyze</code>, which runs a plan through the Python
    core; the editor's <b>Check vs Python</b> button compares the two.</p>
  <h2>Credits</h2>
  <p>Floor Plan Editor by George Dickinson (MIT licence), built with substantial assistance from Claude (Anthropic).
    Source: <a href="https://github.com/gddickinson/floorplan_app">github.com/gddickinson/floorplan_app</a>.</p>`;
});
