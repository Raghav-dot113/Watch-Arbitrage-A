/**
 * Registers the Bryntum Business license before any Bryntum component is created.
 *
 * Bryntum reads `globalThis.bryntum.licenseKey` when it loads, or picks up a key
 * assigned before the modules evaluate. Keeping the assignment here gives every
 * grid in the app one configuration point.
 */
const licenseKey = process.env.NEXT_PUBLIC_BRYNTUM_LICENSE_KEY;

if (licenseKey) {
  const bryntumGlobal = globalThis as typeof globalThis & {
    bryntum?: { licenseKey?: string };
  };
  bryntumGlobal.bryntum ??= {};
  bryntumGlobal.bryntum.licenseKey = licenseKey;
}

export const bryntumLicenseConfigured = Boolean(licenseKey);
