#!/usr/bin/env node
/**
 * no-raw-hex.mjs
 *
 * Fails CI (and pre-commit hooks) when a raw hex color literal appears
 * inside a SmartInv component or web file. Enforces the tokens-only policy
 * from ADR-015 and AGENTS.md non-negotiable #7.
 *
 * Allowed locations for hex literals:
 *   - packages/tokens/          (the single source of truth)
 *   - apps/web/tailwind.config.ts  (consumer; may inline defaults)
 *   - .next/, dist/, node_modules/
 *
 * Scanned locations:
 *   - apps/web/app/**, apps/web/components/**, apps/web/features/**
 *   - packages/ui-web/src/**
 *
 * Usage:
 *   node scripts/no-raw-hex.mjs
 *   pnpm lint:hex                (npm script)
 *
 * Exit codes:
 *   0  no raw hex found
 *   1  raw hex found (file:line printed)
 *   2  invocation error
 */

import { readFileSync, statSync } from 'node:fs';
import { readdir } from 'node:fs/promises';
import { join, relative } from 'node:path';
import process from 'node:process';

const ROOT = process.cwd();

const SCAN_ROOTS = [
  'apps/web/app',
  'apps/web/components',
  'apps/web/features',
  'packages/ui-web/src',
];

const SCAN_EXTENSIONS = new Set(['.ts', '.tsx', '.js', '.jsx', '.mjs', '.css', '.scss']);

const IGNORE_DIR_NAMES = new Set([
  'node_modules',
  '.next',
  'dist',
  'build',
  '.turbo',
  'coverage',
  '.git',
]);

// Match #RGB, #RGBA, #RRGGBB, #RRGGBBAA. Allow them only when preceded by
// a non-word character (avoids matching commit SHAs, hash anchors, etc.).
const HEX_REGEX = /(^|[^\w])#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})\b/gi;

async function walk(dir) {
  let files = [];
  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch (err) {
    if (err.code === 'ENOENT') return files;
    throw err;
  }
  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (IGNORE_DIR_NAMES.has(entry.name)) continue;
      files = files.concat(await walk(fullPath));
    } else if (entry.isFile()) {
      if (SCAN_EXTENSIONS.has(extName(entry.name))) {
        files.push(fullPath);
      }
    }
  }
  return files;
}

function extName(name) {
  const idx = name.lastIndexOf('.');
  return idx >= 0 ? name.slice(idx) : '';
}

function scanFile(path) {
  const text = readFileSync(path, 'utf8');
  const matches = [];
  const lines = text.split(/\r?\n/);
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    HEX_REGEX.lastIndex = 0;
    // Allow inline disable on the same line: `// no-raw-hex:allow`
    if (line.includes('no-raw-hex:allow')) continue;
    let match = HEX_REGEX.exec(line);
    while (match !== null) {
      const hex = `#${match[2]}`;
      matches.push({ line: i + 1, column: match.index + 1, hex });
      match = HEX_REGEX.exec(line);
    }
  }
  return matches;
}

async function main() {
  let totalHits = 0;
  for (const root of SCAN_ROOTS) {
    const absRoot = join(ROOT, root);
    try {
      statSync(absRoot);
    } catch {
      continue;
    }
    const files = await walk(absRoot);
    for (const file of files) {
      const hits = scanFile(file);
      if (hits.length > 0) {
        for (const hit of hits) {
          const rel = relative(ROOT, file);
          process.stdout.write(
            `${rel}:${hit.line}:${hit.column}  raw hex literal "${hit.hex}" — use @smartinv/tokens instead\n`,
          );
        }
        totalHits += hits.length;
      }
    }
  }
  if (totalHits > 0) {
    process.stdout.write(
      `\n${totalHits} raw hex literal(s) found. Use tokens from @smartinv/tokens (see packages/tokens/README.md).\n`,
    );
    process.stdout.write(
      'If a literal is genuinely required, append // no-raw-hex:allow on the same line.\n',
    );
    process.exit(1);
  }
  process.stdout.write('no-raw-hex: clean\n');
}

main().catch((err) => {
  process.stderr.write(`no-raw-hex error: ${err.stack || err.message}\n`);
  process.exit(2);
});
