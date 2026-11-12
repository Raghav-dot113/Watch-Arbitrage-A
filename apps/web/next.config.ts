import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { NextConfig } from "next";

/**
 * The web app runs from `apps/web`, while local secrets live in the repository
 * root `.env`. Read just the public Bryntum key from the root so it reaches the
 * client bundle without copying secrets between files or exposing other values.
 */
const ENV_FILE_CANDIDATES = [
  ".env.local",
  ".env",
  resolve(process.cwd(), "../..", ".env.local"),
  resolve(process.cwd(), "../..", ".env"),
];

function readPublicEnv(name: string): string | undefined {
  const fromProcess = process.env[name];
  if (fromProcess) {
    return fromProcess;
  }
  for (const candidate of ENV_FILE_CANDIDATES) {
    const path = resolve(process.cwd(), candidate);
    if (!existsSync(path)) {
      continue;
    }
    for (const rawLine of readFileSync(path, "utf8").split(/\r?\n/)) {
      const line = rawLine.trim();
      if (!line || line.startsWith("#")) {
        continue;
      }
      const separator = line.indexOf("=");
      if (separator < 1 || line.slice(0, separator).trim() !== name) {
        continue;
      }
      const value = line
        .slice(separator + 1)
        .trim()
        .replace(/^["']|["']$/g, "");
      if (value) {
        return value;
      }
    }
  }
  return undefined;
}

const bryntumLicenseKey = readPublicEnv("NEXT_PUBLIC_BRYNTUM_LICENSE_KEY");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  env: bryntumLicenseKey
    ? { NEXT_PUBLIC_BRYNTUM_LICENSE_KEY: bryntumLicenseKey }
    : {},
};

export default nextConfig;
