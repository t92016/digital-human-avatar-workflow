/* Portable CLI environment: discover this checkout's Python/browser/FFmpeg. */
const path = require('node:path');
const fs = require('node:fs');
const {spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
if (!fs.existsSync(python)) throw Error('請先建立 .venv 並安裝 requirements-prototype.lock.txt');
const probe = spawnSync(python, ['-c', 'import json,imageio_ffmpeg;from avatar_workflow.hardware import find_browser;print(json.dumps({"ffmpeg":imageio_ffmpeg.get_ffmpeg_exe(),"browser":find_browser()}))'], {cwd:root,encoding:'utf8',windowsHide:true});
if (probe.status !== 0) throw Error(probe.stderr);
const config = JSON.parse(probe.stdout);
const env = {...process.env, HYPERFRAMES_NO_TELEMETRY:'1', DO_NOT_TRACK:'1', HF_NO_BROWSER:'1', HYPERFRAMES_FFMPEG_PATH:config.ffmpeg};
env.HYPERFRAMES_HISTORY_ROOT = path.join(root, 'work/hyperframes-history');
env.HYPERFRAMES_EXTRACT_CACHE_DIR = path.join(root, 'work/hyperframes-extract');
env.HYPERFRAMES_FONT_CACHE_DIR = path.join(root, 'work/hyperframes-fonts');
env.XDG_STATE_HOME = path.join(root, 'work/state');
const ffprobe = path.join(root, 'tools/bin', process.platform === 'win32' ? 'ffprobe.exe' : 'ffprobe');
if (fs.existsSync(ffprobe)) env.HYPERFRAMES_FFPROBE_PATH = ffprobe;
const localFfmpeg = path.join(root, 'tools/bin', process.platform === 'win32' ? 'ffmpeg.exe' : 'ffmpeg');
if (fs.existsSync(localFfmpeg)) env.HYPERFRAMES_FFMPEG_PATH = localFfmpeg;
if (config.browser) env.HYPERFRAMES_BROWSER_PATH = config.browser;
const browserReport = path.join(root, 'work/browser.json');
if (!process.env.AVATAR_CHROME && fs.existsSync(browserReport)) {
  const localBrowser = JSON.parse(fs.readFileSync(browserReport,'utf8'));
  if (fs.existsSync(localBrowser.executablePath)) env.HYPERFRAMES_BROWSER_PATH = localBrowser.executablePath;
}
const cli = path.join(root, 'node_modules/hyperframes/bin/hyperframes.mjs');
const result = spawnSync(process.execPath, [cli, ...process.argv.slice(2)], {cwd:root,env,stdio:'inherit',windowsHide:true});
if (result.error) throw result.error;
process.exitCode = result.status ?? 1;
