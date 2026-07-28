// mobile screenshot via CDP device emulation (real 390px layout, mobile:true)
const url = process.argv[2], out = process.argv[3] || '/tmp/shot.png';
const port = 9333;
const { spawn } = await import('node:child_process');
const { writeFileSync } = await import('node:fs');
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ['--headless=new','--disable-gpu',`--remote-debugging-port=${port}`,'--no-first-run','about:blank']);
await new Promise(r => setTimeout(r, 1500));
const targets = await (await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(url)}`, {method:'PUT'})).json();
const ws = new WebSocket(targets.webSocketDebuggerUrl);
let id = 0; const pending = {};
const send = (method, params={}) => new Promise(res => { pending[++id] = res; ws.send(JSON.stringify({id, method, params})); });
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pending[m.id]) { pending[m.id](m.result); delete pending[m.id]; } };
await new Promise(r => ws.onopen = r);
await send('Emulation.setDeviceMetricsOverride', {width:390, height:844, deviceScaleFactor:2, mobile:true});
await send('Page.enable');
await send('Page.navigate', {url});
await new Promise(r => setTimeout(r, 2500));
const metrics = await send('Runtime.evaluate', {expression:
  `JSON.stringify({w:innerWidth, docW:document.documentElement.scrollWidth, over:[...document.querySelectorAll('body *')].filter(el=>el.getBoundingClientRect().right>innerWidth+1).slice(0,8).map(el=>el.tagName+'.'+el.className+' r='+Math.round(el.getBoundingClientRect().right))})`, returnByValue:true});
console.log('METRICS', metrics.result.value);
const shot = await send('Page.captureScreenshot', {captureBeyondViewport:true});
writeFileSync(out, Buffer.from(shot.data, 'base64'));
console.log('saved', out);
chrome.kill();
