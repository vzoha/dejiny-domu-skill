// Data exported from the research repo by tools/export_web.py (re-run `npm run data` after changes).
import site from '../data/site.json';

export const { village, houses, stats, issues, docs, config, maps, places } = site;
export const mainHouse = site.mainHouse ? houses[site.mainHouse] : null;
export const records = Object.fromEntries(site.records.map((r) => [r.key, r]));
export const recordList = site.records;
export const houseList = Object.values(houses);

export const href = {
  house: (slug) => `/dum/${slug}/`,
  record: (key) => `/zdroj/${key}/`,
};

/** Sortable number from dates like "12. 5. 1811", "3/1867", "12/1790", "1797", "asi 1600". */
export function dateKey(date) {
  const y = ((date ?? '').match(/\d{4}/) || ['9999'])[0];
  const parts = date.slice(0, date.indexOf(y)).match(/\d+/g) || [];
  const [d, m] = parts.length >= 2 ? [parts[0], parts[1]] : [0, parts[0] || 0];
  return Number(y) * 10000 + Number(m) * 100 + Number(d);
}

export const houseTitle = (h) => `čp. ${h.cp}${h.name ? ` – ${h.name}` : ''}`;
export const statusClass = (st) => ({ doc: 'st-doc', lit: 'st-fam', prob: 'st-prob', fam: 'st-fam' })[st] ?? 'st-unk';
