import { cp, mkdir, rm, stat } from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const inputs = ['web/index.html', 'web/app.js', 'web/styles.css'];
for (const entry of inputs) {
  const info = await stat(path.join(root, entry));
  if (!info.isFile() || info.size === 0) {
    throw new Error('Missing site source: ' + entry);
  }
}
const output = path.join(root, 'dist');
await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });
await cp(path.join(root, 'web'), output, { recursive: true });
console.log('MakeImage static studio ready: dist/');
