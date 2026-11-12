// Static-site data layer: answers api() GETs from the JSON files exported by scripts/build_static.py
// (api/info.json, api/catalog.json, api/examples.json, api/examples/<name>.json). The editor itself needs no
// server; only "Check vs Python" (POST /analyze) is local-app only and is hidden on the static site.
const files = new Map();
function file(rel) {
  if (!files.has(rel)) {
    files.set(rel, fetch('api/' + rel + '.json').then(r => { if (!r.ok) throw new Error(`${r.status} ${rel}`); return r.json(); }));
  }
  return files.get(rel);
}

export async function staticApi(path, body) {
  if (body) throw new Error('This needs the local app (python run_web.py).');
  return file(path.split('?')[0].replace(/^\/+/, ''));
}
