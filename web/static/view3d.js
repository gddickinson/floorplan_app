// 3D preview in raw WebGL (no libraries): orbit (drag), pan (Shift/right drag), zoom (wheel), Lambert lighting.
import { buildMesh } from './mesh3d.js';

const VS = `attribute vec3 aPos; attribute vec3 aCol; attribute vec3 aNrm;
uniform mat4 uMVP; varying vec3 vCol; varying vec3 vNrm; varying float vY;
void main(){ gl_Position = uMVP * vec4(aPos, 1.0); vCol = aCol; vNrm = aNrm; vY = aPos.y; }`;
const FS = `precision mediump float; varying vec3 vCol; varying vec3 vNrm; varying float vY;
uniform vec3 uLight;
void main(){ vec3 n = normalize(vNrm); float d = abs(dot(n, uLight));
  float sky = 0.5 + 0.5 * abs(n.y);
  gl_FragColor = vec4(vCol * (0.38 + 0.47 * d + 0.15 * sky), 1.0); }`;

// --- minimal mat4 (column-major, as WebGL expects) ---
function mul(a, b) {
  const o = new Float32Array(16);
  for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) {
    let s = 0;
    for (let k = 0; k < 4; k++) s += a[k * 4 + r] * b[c * 4 + k];
    o[c * 4 + r] = s;
  }
  return o;
}
function perspective(fovy, aspect, near, far) {
  const f = 1 / Math.tan(fovy / 2), nf = 1 / (near - far);
  return new Float32Array([f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) * nf, -1, 0, 0, 2 * far * near * nf, 0]);
}
function lookAt(eye, at, up) {
  const sub = (a, b) => a.map((v, i) => v - b[i]);
  const norm = a => { const l = Math.hypot(...a) || 1; return a.map(v => v / l); };
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const z = norm(sub(eye, at)), x = norm(cross(up, z)), y = cross(z, x);
  return new Float32Array([x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0, -dot(x, eye), -dot(y, eye), -dot(z, eye), 1]);
}

export class View3D {
  constructor(canvas) {
    this.canvas = canvas;
    const gl = canvas.getContext('webgl', { antialias: true, preserveDrawingBuffer: true });
    this.gl = gl;
    if (!gl) return;
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const prog = gl.createProgram();
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog);
    this.prog = prog;
    this.loc = { pos: gl.getAttribLocation(prog, 'aPos'), col: gl.getAttribLocation(prog, 'aCol'), nrm: gl.getAttribLocation(prog, 'aNrm'),
      mvp: gl.getUniformLocation(prog, 'uMVP'), light: gl.getUniformLocation(prog, 'uLight') };
    this.buf = { pos: gl.createBuffer(), col: gl.createBuffer(), nrm: gl.createBuffer() };
    this.cam = { yaw: -0.7, pitch: 0.75, dist: 800, tx: 0, ty: 0, tz: 0 };
    this.count = 0; this.pending = false; this.fitted = false;
    this.controls();
  }
  get ok() { return !!this.gl; }

  setPlan(plan, refit = false) {
    if (!this.gl) return;
    const gl = this.gl, m = buildMesh(plan);
    for (const [k, arr] of [['pos', m.position], ['col', m.color], ['nrm', m.normal]]) {
      gl.bindBuffer(gl.ARRAY_BUFFER, this.buf[k]); gl.bufferData(gl.ARRAY_BUFFER, arr, gl.STATIC_DRAW);
    }
    this.count = m.count;
    if (refit || !this.fitted) this.fit(m.bounds);
    this.draw();
  }
  fit(b) {
    const c = this.cam;
    c.tx = (b.minX + b.maxX) / 2; c.tz = (b.minZ + b.maxZ) / 2; c.ty = b.maxY * 0.25;
    const aspect = (this.canvas.clientWidth || 1) / (this.canvas.clientHeight || 1);
    c.dist = Math.max(240, Math.hypot(b.maxX - b.minX, b.maxZ - b.minZ) * 1.3 / Math.min(1, aspect));
    this.fitted = true;
  }
  draw() {
    if (!this.gl || this.pending) return;
    this.pending = true;
    requestAnimationFrame(() => { this.pending = false; this.render(); });
  }
  render() {
    const gl = this.gl, cv = this.canvas, dpr = Math.min(2, window.devicePixelRatio || 1);
    const w = Math.max(1, Math.round(cv.clientWidth * dpr)), h = Math.max(1, Math.round(cv.clientHeight * dpr));
    if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
    gl.viewport(0, 0, w, h);
    gl.clearColor(0.02, 0.03, 0.07, 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);
    if (!this.count) return;
    const c = this.cam;
    const eye = [c.tx + c.dist * Math.cos(c.pitch) * Math.sin(c.yaw), c.ty + c.dist * Math.sin(c.pitch),
      c.tz + c.dist * Math.cos(c.pitch) * Math.cos(c.yaw)];
    const mvp = mul(perspective(0.8, w / h, 2, c.dist * 10 + 5000), lookAt(eye, [c.tx, c.ty, c.tz], [0, 1, 0]));
    gl.useProgram(this.prog);
    gl.uniformMatrix4fv(this.loc.mvp, false, mvp);
    const L = [0.45, 0.8, 0.35], l = Math.hypot(...L);
    gl.uniform3f(this.loc.light, L[0] / l, L[1] / l, L[2] / l);
    for (const [k, a] of [['pos', this.loc.pos], ['col', this.loc.col], ['nrm', this.loc.nrm]]) {
      gl.bindBuffer(gl.ARRAY_BUFFER, this.buf[k]); gl.enableVertexAttribArray(a); gl.vertexAttribPointer(a, 3, gl.FLOAT, false, 0, 0);
    }
    gl.drawArrays(gl.TRIANGLES, 0, this.count);
  }
  controls() {
    const cv = this.canvas, c = this.cam;
    let drag = null;
    cv.addEventListener('pointerdown', e => { drag = { x: e.clientX, y: e.clientY, pan: e.shiftKey || e.button === 2 }; cv.setPointerCapture(e.pointerId); });
    cv.addEventListener('pointermove', e => {
      if (!drag) return;
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      drag.x = e.clientX; drag.y = e.clientY;
      if (drag.pan) {
        const k = c.dist / 600;
        c.tx -= (Math.cos(c.yaw) * dx) * k; c.tz += (Math.sin(c.yaw) * dx) * k; c.ty += dy * k;
      } else {
        c.yaw -= dx * 0.008;
        c.pitch = Math.max(0.05, Math.min(1.5, c.pitch + dy * 0.008));
      }
      this.draw();
    });
    const up = () => { drag = null; };
    cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
    cv.addEventListener('contextmenu', e => e.preventDefault());
    cv.addEventListener('wheel', e => { e.preventDefault(); c.dist = Math.max(60, Math.min(20000, c.dist * (e.deltaY < 0 ? 0.9 : 1.1))); this.draw(); }, { passive: false });
    cv.addEventListener('keydown', e => {
      const step = { ArrowLeft: [0.1, 0], ArrowRight: [-0.1, 0], ArrowUp: [0, 0.08], ArrowDown: [0, -0.08] }[e.key];
      if (step) { c.yaw += step[0]; c.pitch = Math.max(0.05, Math.min(1.5, c.pitch + step[1])); this.draw(); e.preventDefault(); }
      if (e.key === '+' || e.key === '=') { c.dist *= 0.9; this.draw(); }
      if (e.key === '-') { c.dist *= 1.1; this.draw(); }
    });
  }
  pngBlob() {
    this.render();
    return new Promise(res => this.canvas.toBlob(res, 'image/png'));
  }
}
