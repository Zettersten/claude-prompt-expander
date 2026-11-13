import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const script = fileURLToPath(new URL("./rewrite.py", import.meta.url));

export function filterPayload(input: string | Uint8Array): string {
  const result = spawnSync("python3", [script], {
    input,
    encoding: "utf8",
    timeout: 5000,
    maxBuffer: 64 * 1024 * 1024,
  });

  if (result.error || result.status !== 0) {
    throw new Error("Abbreviation filtering failed");
  }

  return result.stdout;
}
