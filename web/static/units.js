// Number formatting that matches Python: core/units.py format_dimension, f"{x:.1f}" and round().

// Python's round(v) (half to even) for the grid snap: round(0.5) = 0, round(1.5) = 2.
export function pyRound(v) {
  const r = Math.round(v);
  return Math.abs(v % 1) === 0.5 ? 2 * Math.round(v / 2) : r;
}

// f"{x:.1f}": Python rounds the exact binary value half-to-even; JS toFixed rounds exact ties up. The only exact
// ties at one decimal are k + 0.25 and k + 0.75 (k/4 with odd k), so those are corrected.
export function fmt1(x) {
  const a = Math.abs(x);
  if (Number.isInteger(a * 4) && !Number.isInteger(a * 2) && a < 2 ** 50) {
    let n = Math.floor(a * 10);          // e.g. 126.25 -> 1262
    if (n % 2) n += 1;                   // half to even
    const s = (n / 10).toFixed(1);
    return (x < 0 ? '-' : '') + s;
  }
  if (Object.is(x, -0)) return '-0.0';
  return x.toFixed(1);
}

// core/units.py format_dimension(inches, unit='ft'|'in'|'auto').
export function formatDimension(inches, unit = 'ft') {
  if (unit === 'in') return `${fmt1(inches)}"`;
  if (unit === 'ft' || (unit === 'auto' && Math.abs(inches) >= 12)) {
    const sign = inches < 0 ? '-' : '';
    const size = Math.abs(inches);
    let feet = Math.floor(size / 12);
    let rem = size % 12;
    if (rem >= 11.95) { feet += 1; rem = 0; }
    if (rem < 0.1) return `${feet ? sign : ''}${feet}'`;
    return `${sign}${feet}' ${fmt1(rem)}"`;
  }
  return `${fmt1(inches)}"`;
}

export const sqft = v => `${fmt1(v)} sq ft`;
export const ft = inches => fmt1(inches / 12) + ' ft';
