#!/usr/bin/env node
// Runs Vitest from the project root with an uppercase Windows drive letter.
// A working directory like c:\dev\... (lowercase, as some tools pass it) makes Vitest load two
// copies of itself and every suite fails with "Cannot read properties of undefined (reading 'config')".
// Usage: node scripts/run-vitest.mjs [vitest args]   (npm run test:unit)
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..").replace(/^[a-z]:/, (drive) => drive.toUpperCase());
const result = spawnSync(process.execPath, [join(root, "node_modules", "vitest", "vitest.mjs"), ...process.argv.slice(2)], {
  cwd: root,
  stdio: "inherit",
});
if (result.error) {
  console.error(`Impossibile avviare Vitest: ${result.error.message}`);
  process.exit(1);
}
process.exit(result.status ?? 1);
