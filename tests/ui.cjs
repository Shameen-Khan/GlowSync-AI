const fs=require('node:fs');
const assert=require('node:assert/strict');
const {JSDOM,VirtualConsole}=require('jsdom');
const root=process.env.GLOWSYNC_ROOT,base=process.env.GLOWSYNC_TEST_BASE;
let cookie='',calls=[],failures=[];
const virtualConsole=new VirtualConsole();virtualConsole.on('jsdomError',e=>{if(!e.message.includes('navigation'))failures.push(e.message)});
const dom=new JSDOM(fs.readFileSync(root+'/templates/index.html','utf8'),{url:base+'/',runScripts:'outside-only',pretendToBeVisual:true,virtualConsole});
const w=dom.window;
w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};
w.HTMLDialogElement.prototype.showModal=function(){this.open=true};w.HTMLDialogElement.prototype.close=function(){this.open=false};
w.CSS={escape:s=>String(s).replace(/[^a-zA-Z0-9_-]/g,c=>'\\'+c)};
w.fetch=async(path,options={})=>{
 const headers={...options.headers,Cookie:cookie};
 const response=await fetch(new URL(path,base),{...options,headers});
 const setCookie=response.headers.get('set-cookie');if(setCookie)cookie=setCookie.split(';')[0];
 calls.push({path,status:response.status});return response;
};
w.eval('function initStudio(){} function stopCamera(){}\n'+fs.readFileSync(root+'/static/app.js','utf8').replace(/^import .*;\s*/,''));
const $=q=>w.document.querySelector(q),$$=q=>[...w.document.querySelectorAll(q)];
const wait=async(fn,label)=>{for(let i=0;i<120;i++){if(fn())return;await new Promise(r=>setTimeout(r,40));}throw Error('Timed out: '+label+'; '+$('#toast').textContent)};
const change=(q,value)=>{$(q).value=value;$(q).dispatchEvent(new w.Event('change',{bubbles:true}))};
const click=q=>$(q).click();
const submit=q=>$(q).dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
(async()=>{
 await wait(()=>$$('#product-grid .product-card').length===12,'home catalogue');
 assert.equal($('#catalogue-count').textContent,'3,827 product listings');console.log('PASS home loads real catalogue');
 change('#brand-filter','swiss-beauty');
 await wait(()=>w.location.hash==='#catalogue'&&$$('#product-grid .product-card').length===24,'brand filter');
 assert($$('#product-grid .product-brand').every(n=>n.textContent==='Swiss Beauty'));console.log('PASS navigation and brand filtering');
 $('#search').value='no-such-product-zzq';$('#search').dispatchEvent(new w.Event('input',{bubbles:true}));
 await wait(()=>$('#product-grid .empty-state'),'empty search');click('#clear-filters');
 await wait(()=>$$('#product-grid .product-card').length===24,'reset filters');console.log('PASS search empty state and reset');
 const first=$('#product-grid .product-card');const pid=first.dataset.product;
 click('#product-grid .save-button');assert($('#auth-dialog').open);click('#toggle-auth');
 $('#auth-name').value='UI Test';$('#auth-email').value='ui-test@example.test';$('#auth-password').value='LocalUITest-12345';submit('#auth-form');
 await wait(()=>!$('#auth-dialog').open&&$('#saved-count').textContent==='1','register and resume save');console.log('PASS registration and pending save');
 click('#product-grid [data-detail]');await wait(()=>$('#product-dialog').open,'product dialog');
 assert($('#product-detail').textContent.includes('Range photo'));
 assert($('#product-detail .detail-visit').href.startsWith('https://'));
 const select=$('#product-detail [data-variant]');if(select.options.length>1){select.value=select.options[1].value;select.dispatchEvent(new w.Event('change',{bubbles:true}));}
 click('#product-dialog [data-close]');assert(!$('#product-dialog').open);console.log('PASS product detail, variant selection and source link');
 const compares=$$('#product-grid [data-compare]');for(let i=0;i<2;i++){compares[i].checked=true;compares[i].dispatchEvent(new w.Event('change',{bubbles:true}))}
 assert(!$('#compare-bar').hidden);click('#open-compare');assert($('#compare-dialog').open);assert.equal($$('#compare-content tr')[0].querySelectorAll('td').length,2);click('#compare-dialog [data-close]');console.log('PASS two-product comparison');
 w.location.hash='saved';await wait(()=>!$('#saved-page').hidden&&$('#saved-grid .saved-card'),'saved route');
 const watch=$('#saved-grid [data-watch]');if(watch){watch.checked=true;watch.dispatchEvent(new w.Event('change',{bubbles:true}));await wait(()=>$('#saved-grid').textContent.includes('Awaiting your first live check'),'watch');}
 console.log('PASS persistent wishlist and price-watch control');
 w.location.hash='studio';await wait(()=>!$('#studio-page').hidden,'studio route');submit('#studio-form');
 await wait(()=>$('#palette-result').textContent.includes('YOUR COLOUR DIRECTION'),'Java palette');
 await wait(()=>$('#studio-product-grid .product-card')||$('#studio-product-grid .empty-state'),'shade suggestions');
 click('[data-region="lips"]');await wait(()=>$('#studio-product-grid .product-card')&&!$('#studio-product-grid .loading'),'lip products');
 assert($('#studio-region-title').textContent.includes('lips'));console.log('PASS real Java palette and feature product browsing');
 w.location.hash='brands';await wait(()=>!$('#brands-page').hidden,'brands');assert.equal($$('.brand-card').length,17);assert(!$('#manager-controls').hidden);console.log('PASS brand coverage and owner-only catalogue controls');
 click('#account-button');assert($('#account-dialog').open);click('#logout');await wait(()=>$('#account-button').textContent.includes('Sign in'),'logout');assert($('#manager-controls').hidden);console.log('PASS logout removes account access');
 assert.equal(failures.length,0,failures.join('\n'));
 assert(!calls.some(c=>c.status>=500),JSON.stringify(calls.filter(c=>c.status>=500)));
 console.log('PASS UI integration: '+calls.length+' real HTTP calls, no JavaScript errors');
 dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1});
