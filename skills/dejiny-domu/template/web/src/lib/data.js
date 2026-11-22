// Data exported from the research repo by tools/export_web.py (re-run `npm run data` after changes).
import site from '../data/site.json';

export const { village, houses, stats, issues, docs, config, maps, places } = site;
export const mapGroups = site.mapGroups ?? {};
export const mainHouse = site.mainHouse ? houses[site.mainHouse] : null;
// Jak se říká místu webu (web.json → pojmy): misto = 1. pád, misto_2 = 2. pád, stred = 2. pád za „… od“ ve vzdálenosti
// v bublině mapy. Bez nastavení obec / obce / návsi; vlastni = projekt pojem nastavil (pak se přeformulují věty,
// kde výchozí text říká „ves“ nebo potřebuje jiný pád). Jiný typ než neprázdný text = výchozí hodnota.
const pojem = (v, vychozi) => (typeof v === 'string' && v.trim() ? v.trim() : vychozi);
const p = config.pojmy ?? {};
const vlastni = !!pojem(p.misto, '');
const misto_2 = pojem(p.misto_2, 'obce');
export const pojmy = {
  misto: pojem(p.misto, 'obec'), misto_2, stred: pojem(p.stred, vlastni ? `středu ${misto_2}` : 'návsi'), vlastni,
};
export const velke = (s) => s.charAt(0).toUpperCase() + s.slice(1);
// Popisky menu podle adresy (web.json → menu.popisky) mají přednost; /obec/ jinak z pojmy.misto.
const popisky = config.menu?.popisky;
export const popiskyMenu = {
  ...(vlastni ? { '/obec/': velke(pojmy.misto) } : {}),
  ...Object.fromEntries(Object.entries(popisky && typeof popisky === 'object' ? popisky : {})
    .filter(([, v]) => pojem(v, '')).map(([k, v]) => [k, v.trim()])),
};
export const records = Object.fromEntries(site.records.map((r) => [r.key, r]));
export const recordList = site.records;
export const houseList = Object.values(houses).sort((a, b) => a.order - b.order);

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

// h.part = část obce (pole `cast`), když má obec víc částí se stejnými čísly
export const houseTitle = (h) => `${h.part ? `${h.part} ` : ''}čp. ${h.cp}${h.name ? ` – ${h.name}` : ''}`;
export const houseAddress = (h) => `${h.part || village.name} čp. ${h.cp}`.trim();
export const houseFullTitle = (h) => `${houseAddress(h)}${h.name ? ` – ${h.name}` : ''}`;
export const statusClass = (st) => ({ doc: 'st-doc', lit: 'st-fam', prob: 'st-prob', fam: 'st-fam' })[st] ?? 'st-unk';
