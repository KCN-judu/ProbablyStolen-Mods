import fs from 'node:fs';
import gp from 'gettext-parser';
const [,, out, ...files] = process.argv;
const result = {};
for (const file of files) {
  const po = gp.po.parse(fs.readFileSync(file));
  const todo = [];
  for (const [ctx, entries] of Object.entries(po.translations)) for (const [id, e] of Object.entries(entries)) {
    if (!id) continue;
    const fuzzy = (e.comments?.flag ?? '').includes('fuzzy');
    if (!e.msgstr[0] || fuzzy) todo.push(id);
  }
  result[file] = todo;
}
fs.writeFileSync(out, JSON.stringify(result, null, 1));
console.log(Object.entries(result).map(([f, t]) => `${f}: ${t.length}`).join('\n'));
