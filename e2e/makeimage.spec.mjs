import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';

for (const viewport of [{width:1280,height:900},{width:390,height:844}]) {
  test('local PNG and receipt handoff at '+viewport.width+'px',async ({page},info)=>{
    await page.setViewportSize(viewport);
    const external=[];
    const errors=[];
    page.on('request',r=>{if(/^https?:/.test(r.url())&&!r.url().startsWith('http://127.0.0.1:4173/')) external.push(r.url());});
    page.on('pageerror',error=>errors.push(error.message));
    await page.goto('http://127.0.0.1:4173/');
    await expect(page.locator('#download-receipt')).toBeDisabled();
    await page.locator('#format').selectOption('9:16');
    const [png]=await Promise.all([page.waitForEvent('download'),page.locator('#download').click()]);
    const pngPath=info.outputPath('image.png');
    await png.saveAs(pngPath);
    await expect(page.locator('#download-receipt')).toBeEnabled();
    const [json]=await Promise.all([page.waitForEvent('download'),page.locator('#download-receipt').click()]);
    const receiptPath=info.outputPath('receipt.json');
    await json.saveAs(receiptPath);
    const receipt=JSON.parse(await readFile(receiptPath,'utf8'));
    expect(receipt.state).toBe('VERIFIED_LOCAL_RENDER');
    expect(receipt.output.full_decode).toBe(true);
    expect(receipt.output.width).toBe(720);
    expect(receipt.output.height).toBe(1280);
    expect(receipt.output.sha256).toBe(createHash('sha256').update(await readFile(pngPath)).digest('hex'));
    expect(receipt.continuity_cookie.publish_authority).toBe(false);
    const storyboard=info.outputPath('storyboard.json');
    execFileSync('python3',['export_makevideo.py','--image',pngPath,'--receipt',receiptPath,'--output',storyboard,'--format','9:16']);
    expect(JSON.parse(await readFile(storyboard,'utf8')).schema).toBe('makevideo/storyboard/v1');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
    expect(errors).toEqual([]);
    expect(external).toEqual([]);
  });
}
