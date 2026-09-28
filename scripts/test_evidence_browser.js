/* Run only in the isolated local harness, never inject into the production site. */
document.getElementById('run').addEventListener('click',async()=>{
  const checks=[];const frames=[];
  const assert=(name,value)=>{checks.push({name,pass:!!value});if(!value)throw Error(name);};
  const wait=async(fn)=>{for(let i=0;i<100;i++){if(fn())return;await new Promise(r=>setTimeout(r,50));}throw Error('UI timeout');};
  async function frame(path){const f=document.createElement('iframe');f.src=path;document.body.append(f);frames.push(f);await new Promise((r,j)=>{f.onload=r;f.onerror=j;});return f.contentWindow;}
  let error=null;
  try{
    const pub=await frame('/publications.html');const doc=pub.document;
    assert('74 static records before search',doc.querySelectorAll('[data-paper-record]').length===74);
    assert('MiniSearch and corpus lazy before input',!pub.MiniSearch&&!pub.performance.getEntriesByType('resource').some(r=>r.name.endsWith('evidence-search.json')));
    assert('8 ordinary static question links',doc.querySelectorAll('#scientific-questions li a').length===8);
    async function query(q){doc.querySelector('#pubSearch').value=q;doc.querySelector('#pubSearch').dispatchEvent(new pub.Event('input'));await wait(()=>!doc.querySelector('#evidenceSearchStatus').textContent.includes('Loading'));return doc.querySelector('#evidenceResults').textContent;}
    assert('GPX4 finds Idebenone',(await query('GPX4')).includes('10.1016/j.ejphar.2023.175569'));
    assert('MCC950 finds NLRP3',(await query('MCC950')).includes('10.1136/jitc-2024-010127'));
    await query('https://doi.org/10.1002/mdr2.70052');assert('DOI exact one paper',doc.querySelectorAll('.evidence-search-result').length===1);
    assert('Limitations explicitly labeled',(await query('prospectively validated early diagnostic')).includes('LIMITATION / DOES NOT ESTABLISH'));
    await query('<img src=x onerror="window.bad=true">no_match_9988');assert('Input not HTML or invented answer',!pub.bad&&doc.querySelectorAll('#evidenceResults img').length===0&&doc.querySelector('#evidenceSearchStatus').textContent.includes('No answer is generated'));
    assert('Query not persisted to URL',!pub.location.search&&!pub.location.hash);
    assert('All static records stay visible',Array.from(doc.querySelectorAll('[data-paper-record]')).every(n=>pub.getComputedStyle(n).display!=='none'));
    assert('No search telemetry',pub.testEvents.length===0);
    const nojs=await frame('/nojs/publications.html');assert('JS-off static fallback',nojs.document.querySelectorAll('[data-paper-record] a').length>=74&&nojs.document.querySelectorAll('script').length===0);
    const failed=await frame('/unavailable/publications.html');failed.document.querySelector('#pubSearch').value='GPX4';failed.document.querySelector('#pubSearch').dispatchEvent(new failed.Event('input'));
    await wait(()=>failed.document.querySelector('#evidenceSearchStatus').textContent.includes('Search unavailable'));
    assert('Failed resource fallback 74 static records',failed.document.querySelectorAll('[data-paper-record]').length===74);
    for(const slug of ['aihflevel','doi-10-1002-mdr2-70052','idebenone-ferroptosis','doi-10-1002-ggn2-202500053']){
      const w=await frame('/papers/'+slug+'.html');const d=w.document;
      const b=d.querySelector('[data-copy-evidence]'),group=b.closest('.evidence-actions');
      const payload=JSON.parse(d.getElementById(b.dataset.copyEvidence).textContent);
      let copied=null,denied=false;
      Object.defineProperty(w.navigator,'clipboard',{configurable:true,value:{writeText:async text=>{if(denied)throw Error('test denial');copied=text;}}});
      b.click();await wait(()=>group.querySelector('[role=status]').textContent==='Copied');
      assert(slug+' exact contextual copy',copied===payload.text&&copied.includes('Context:')&&copied.includes('Source locator:')&&copied.includes('Does Not Establish:')&&copied.includes('https://doi.org/'));
      assert(slug+' exactly one evidence event',w.testEvents.length===1&&w.testEvents[0][1]==='evidence_copy');
      denied=true;b.click();await wait(()=>!group.querySelector('textarea').hidden);
      assert(slug+' failed copy full fallback, no success event',group.querySelector('textarea').value===payload.text&&w.testEvents.length===1&&group.querySelector('[role=status]').textContent!=='Copied');
      denied=false;w.gtag=()=>{throw Error('test gtag failure');};b.click();await wait(()=>group.querySelector('[role=status]').textContent==='Copied');
      assert(slug+' analytics failure nonblocking',w.testEvents.length===1);
      w.gtag=(...e)=>w.testEvents.push(e);
      d.addEventListener('click',e=>{if(e.target.closest('a'))e.preventDefault();});
      d.querySelector('[data-evidence-export]').click();
      assert(slug+' one export click only',w.testEvents.length===2&&w.testEvents[1][1]==='evidence_export'&&w.testEvents[1][2].citation_format==='evidence_csv');
      d.querySelector('[data-copy-citation]').click();await wait(()=>w.testEvents.length===3);
      assert(slug+' original citation copy independent',w.testEvents[2][1]==='citation_copy');
      assert(slug+' valid static navigation',Array.from(d.querySelectorAll('.evidence-navigation a')).every(a=>d.querySelector(a.getAttribute('href'))));
      assert(slug+' no remote resources',w.performance.getEntriesByType('resource').every(r=>new URL(r.name).origin===location.origin));
      if(slug.includes('ggn2'))assert('Perspective uses Key arguments',d.querySelector('.evidence-navigation').textContent.includes('Key arguments'));
    }
    assert('All harness frame resources same-origin',frames.every(f=>f.contentWindow.performance.getEntriesByType('resource').every(r=>new URL(r.name).origin===location.origin)));
  }catch(e){error=String(e.stack||e);}
  const result={checks,error,pass:!error,ga4_network:'Blocked by local-only CSP; original GA4 removed from served test copies; local event stubs only'};
  document.getElementById('result').textContent=JSON.stringify(result,null,2);document.title=result.pass?'PASS evidence browser':'FAIL evidence browser';
  await fetch('/test-result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(result)});
},{once:true});
