// After `astro build`: serve the site from its base path.
//
// Pages, components and generated Markdown write root-relative links ("/en/quick-call/",
// "/attachments/..."). The site is published at https://kcn-judu.github.io<base>/, so every
// root-relative href, src and srcset in the built HTML, and every absolute URL Astro
// built from `site` without the base, gets the base prefix. Astro's own assets already
// carry it and are left alone.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dist = path.join(root, 'dist');
const { base } = JSON.parse(fs.readFileSync(path.join(root, 'config', 'repos.json'), 'utf8'));
const origin = 'https://kcn-judu.github.io';

function* htmlFiles(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) yield* htmlFiles(full);
    else if (entry.name.endsWith('.html')) yield full;
  }
}

const prefix = (url) => (url.startsWith(`${base}/`) || url === base || url.startsWith('//') ? url : `${base}${url}`);
let files = 0;
for (const file of htmlFiles(dist)) {
  const html = fs.readFileSync(file, 'utf8');
  const out = html
    .replace(/\b(href|src|action|content)="(\/[^"]*)"/g, (_, attr, url) => `${attr}="${prefix(url)}"`)
    .replace(/\bsrcset="([^"]*)"/g, (_, set) => `srcset="${set.replace(/(^|,\s*)(\/[^\s,]*)/g, (m, sep, url) => sep + prefix(url))}"`)
    .replaceAll(`${origin}/`, `${origin}${base}/`)
    .replaceAll(`${origin}${base}${base}/`, `${origin}${base}/`);
  if (out !== html) {
    fs.writeFileSync(file, out);
    files += 1;
  }
}
console.log(`Prefixed links with ${base} in ${files} pages.`);
