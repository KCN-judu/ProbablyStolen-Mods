// Astro configuration of the documentation site. Pages are generated into .generated/ by tools/prepare-site.mjs
// before the build (npm run build); `base` comes from config/repos.json.
import fs from 'node:fs';
import { defineConfig } from 'astro/config';
import remarkAlerts from './src/plugins/remark-alerts.mjs';
import rehypeHeadingIds from './src/plugins/rehype-heading-ids.mjs';
import rehypeSidenotes from './src/plugins/rehype-sidenotes.mjs';
import rehypeTableScroll from './src/plugins/rehype-table-scroll.mjs';

const { base } = JSON.parse(fs.readFileSync(new URL('./config/repos.json', import.meta.url), 'utf8'));

// Pages and components write root-relative links ("/en/..."); tools/finalize-site.mjs
// prefixes them with `base` after the build, because the site is served from
// https://kcn-judu.github.io/ProbablyStolen-Mods/.
export default defineConfig({
  site: 'https://kcn-judu.github.io',
  base,
  trailingSlash: 'always',
  build: { format: 'directory' },
  markdown: {
    remarkPlugins: [remarkAlerts],
    rehypePlugins: [rehypeHeadingIds, rehypeSidenotes, rehypeTableScroll],
    shikiConfig: {
      themes: { light: 'github-light', dark: 'github-dark-dimmed' },
      defaultColor: false,
    },
  },
});
