// Runs a lunadoc command on the site's own pages (content/) and on every mod (mods/*/doc).
//   node tools/each-doc.mjs update     regenerate manual.pot and merge every manual.po
//   node tools/each-doc.mjs check      validate layout, catalogs and links
//   node tools/each-doc.mjs status     translation coverage

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const { workspace = 'mods' } = JSON.parse(fs.readFileSync(path.join(root, 'config', 'repos.json'), 'utf8'));
const command = process.argv[2] ?? 'status';
const cli = path.join(root, 'tools', 'lunadoc', 'cli.mjs');

const targets = [{ name: 'site', repo: root, doc: path.join(root, 'content') }];
const mods = path.join(root, workspace);
for (const name of fs.existsSync(mods) ? fs.readdirSync(mods).sort() : []) {
  const doc = path.join(mods, name, 'doc');
  if (fs.existsSync(path.join(doc, 'conf.json'))) targets.push({ name, repo: path.join(mods, name), doc });
}

let failed = 0;
for (const target of targets) {
  console.log(`== ${target.name}`);
  const run = spawnSync(process.execPath, [cli, command, target.repo, '--doc', target.doc], { stdio: 'inherit' });
  if (run.status !== 0) failed += 1;
}
process.exit(failed ? 1 : 0);
