// Fills msgstr in gettext catalogs from a msgid -> msgstr table and clears the fuzzy flag
// of every message it fills. With --force it also replaces translations that differ from
// the table. Run `npm run update-po` afterwards to normalise the files.
//   node tools/i18n/apply.mjs [--force] tools/i18n/zh_CN.json <catalog.po>...

import fs from 'node:fs';
import gp from 'gettext-parser';

const args = process.argv.slice(2);
const force = args[0] === '--force' && args.shift() !== undefined;
const [tablePath, ...files] = args;
const table = JSON.parse(fs.readFileSync(tablePath, 'utf8'));
let filled = 0;
let missing = 0;
for (const file of files) {
  const po = gp.po.parse(fs.readFileSync(file));
  for (const entries of Object.values(po.translations)) {
    for (const [id, entry] of Object.entries(entries)) {
      if (!id) continue;
      const flags = (entry.comments?.flag ?? '').split(',').map((f) => f.trim()).filter(Boolean);
      const fuzzy = flags.includes('fuzzy');
      if (entry.msgstr[0] && !fuzzy && !(force && id in table && table[id] !== entry.msgstr[0])) continue;
      if (!(id in table)) {
        missing += 1;
        console.warn(`${file}: no translation for: ${id.slice(0, 80)}`);
        continue;
      }
      entry.msgstr = [table[id]];
      if (entry.comments) {
        entry.comments.flag = flags.filter((f) => f !== 'fuzzy').join(', ');
        delete entry.comments.previous;
      }
      filled += 1;
    }
  }
  fs.writeFileSync(file, gp.po.compile(po, { foldLength: 0 }));
}
console.log(`filled ${filled}, missing ${missing}`);
