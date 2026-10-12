// Headless local visual checks. Uses existing Edge and Playwright, no installs.
const fs = require('fs');
const path = require('path');
const http = require('http');
const { chromium } = require('C:/Users/zg381/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = path.resolve(__dirname, '../..');
const out = path.resolve(root, '../orcid-reconciliation-20261012-evidence/ui-review');
fs.mkdirSync(out, {recursive:true});
const mime = {'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.json':'application/json','.svg':'image/svg+xml'};
const server = http.createServer((req,res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const target = path.resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
  if (!target.startsWith(root + path.sep)) {res.writeHead(403); res.end(); return;}
  fs.readFile(target, (err,data) => { if(err){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',mime[path.extname(target)] || 'application/octet-stream');res.end(data); });
});
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1',resolve));
  let browser;
  try {
    browser = await chromium.launch({headless:true,channel:'msedge'});
    const context = await browser.newContext();
    const results = [];
    for (const width of [390,1440]) {
      for (const url of ['index.html','papers/doi-10-1126-science-aek9583.html','papers/doi-10-1016-j-medd-2026-100004.html']) {
        const page = await context.newPage();
        await page.setViewportSize({width,height:950});
        const errors=[];
        page.on('pageerror',err=>errors.push(err.message));
        await page.goto(`http://127.0.0.1:${server.address().port}/${url}`,{waitUntil:'networkidle'});
        const metrics=await page.evaluate(()=>({h1Count:document.querySelectorAll('h1').length,overflow:document.documentElement.scrollWidth>innerWidth+1,canonical:document.querySelector('link[rel="canonical"]')?.href}));
        const filename=url.replaceAll('/','-')+`-${width}.png`;
        await page.screenshot({path:path.join(out,filename),fullPage:true});
        if(metrics.h1Count!==1 || metrics.overflow || errors.length) throw Error(JSON.stringify({url,width,metrics,errors}));
        results.push({url,width,...metrics,scriptErrors:errors,screenshot:filename});
        await page.close();
      }
    }
    fs.writeFileSync(path.join(__dirname,'VISUAL_ACCEPTANCE.json'),JSON.stringify({status:'PASS',results},null,2)+'\n');
    console.log(JSON.stringify({status:'PASS',views:results.length,screenshotDirectory:out}));
  } finally {if(browser)await browser.close();server.close();}
})().catch(err=>{console.error(err);process.exitCode=1;});
