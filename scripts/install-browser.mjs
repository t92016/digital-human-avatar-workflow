// Official Chrome for Testing, isolated inside this checkout; no user profile.
import { install, Browser } from '@puppeteer/browsers';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const buildId = '150.0.7871.124';
const result = await install({browser:Browser.CHROMEHEADLESSSHELL, buildId, cacheDir:path.join(root,'work/browsers')});
fs.writeFileSync(path.join(root,'work/browser.json'),JSON.stringify({buildId,executablePath:result.executablePath,source:'https://googlechromelabs.github.io/chrome-for-testing/'},null,2));
console.log(result.executablePath);
