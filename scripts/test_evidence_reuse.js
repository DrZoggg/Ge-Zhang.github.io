const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
async function main(){
  const code=fs.readFileSync(path.join(__dirname,'../assets/evidence-reuse.js'),'utf8');
  let click, fail=false, copied;const events=[],status={textContent:''},fallback={hidden:true,focus(){},select(){}};
  const payload={doi:'10.1234/example',finding_id:'KF1',text:'Complete claim\nContext\nSource locator\nDoes Not Establish\nDOI'};
  const button={dataset:{copyEvidence:'ev-copy-kf1'},hidden:true,closest:()=>({querySelector:s=>s==='textarea'?fallback:status}),addEventListener:(_,f)=>{click=f;}};
  const document={querySelectorAll:s=>s==='[data-copy-evidence]'?[button]:[],getElementById:()=>({textContent:JSON.stringify(payload)})};
  const window={location:{pathname:'/papers/example.html'},gtag:(...e)=>events.push(e)};
  const navigator={clipboard:{writeText:async text=>{if(fail)throw Error('denied');copied=text;}}};
  vm.runInNewContext(code,{document,window,navigator});assert(!button.hidden);
  await click();assert.equal(copied,payload.text);assert.equal(status.textContent,'Copied');assert.equal(events.length,1);
  assert.equal(events[0][1],'evidence_copy');assert.deepEqual(Object.keys(events[0][2]).sort(),['paper_doi','paper_path']);
  fail=true;await click();assert.equal(events.length,1);assert.notEqual(status.textContent,'Copied');assert(!fallback.hidden);assert.equal(fallback.value,payload.text);
  delete navigator.clipboard;await click();assert.equal(events.length,1);assert(!fallback.hidden);
  navigator.clipboard={writeText:async()=>{}};delete window.gtag;await click();assert.equal(status.textContent,'Copied');
  window.gtag=()=>{throw Error('analytics unavailable');};await click();assert.equal(status.textContent,'Copied');
  console.log('REUSE JS PASS: successful copy only, full manual fallback, missing clipboard, absent/throwing GA4, no citation events');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
