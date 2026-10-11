/* /find learns from what people tap (publish/findlearn.js, Nan 2026-10-04).
 * Appended to docs/locshare.js by build.py — the one script every results
 * page already loads — and idle on every other page. On a results page: when
 * the reader leaves it, one beacon to /api/find with the query, the results
 * ranked above the deepest one tapped (at least the top three), the taps with
 * rank and time, and the query this tab asked just before (five minutes);
 * coming back from a result, a second beacon with the time away. The tab's
 * trail (sessionStorage md-trail, two hours: recent queries and the results
 * opened from them) is what the reader assistant reads as "before". */
(function(){
var P=location.pathname,U=new URLSearchParams(location.search),Q=(U.get("q")||"").trim();
if(!/^\/(find(\/|\.html)?|search(\.html)?)$/.test(P)||!Q||U.get("adv")==="1")return;
function main(){var K="md-trail",T0=Date.now();
function rd(){try{return JSON.parse(sessionStorage.getItem(K))||{}}catch(e){return {}}}
function wr(o){try{sessionStorage.setItem(K,JSON.stringify(o))}catch(e){}}
function send(o){try{if(navigator.sendBeacon&&/(^|\.)motdang\.net$/.test(location.hostname))navigator.sendBeacon("/api/find",new Blob([JSON.stringify(o)],{type:"text/plain"}))}catch(e){}}
var tr=rd(),now=T0;tr.find=(tr.find||[]).filter(function(x){return now-x.t<72e5});tr.open=(tr.open||[]).filter(function(x){return now-x.t<72e5});
var last=tr.find.length?tr.find[tr.find.length-1]:null,pq=last&&last.q!==Q&&now-last.t<3e5?last:null;
function backFrom(){var t=rd();if(t.away&&t.away.q===Q){send({e:"back",q:Q,u:t.away.u,ms:Date.now()-t.away.t});delete t.away;wr(t)}}
backFrom();tr=rd();tr.find=(tr.find||[]).filter(function(x){return now-x.t<72e5});
if(!last||last.q!==Q){tr.find.push({q:Q,t:now,tap:0});tr.find=tr.find.slice(-6)}wr(tr);
var ol=document.querySelector("ol[start]"),S=ol?+ol.getAttribute("start")||1:1;
var lis=ol?[].slice.call(ol.children):[],urls=lis.map(function(li){var a=li.querySelector("a.t");return a?a.href:""});
var taps=[],sentTaps=0,sentShown=0,first=1,tapSent=0,deep=-1;
if(pq&&tr.open.length){var seen={};tr.open.forEach(function(o){seen[o.u]=1});lis.forEach(function(li,i){if(seen[urls[i]]){var a=li.querySelector("a.t");if(a&&!a.querySelector(".seen")){var s=document.createElement("span");s.className="seen";s.textContent=" · เปิดแล้ว · opened";a.after(s)}}})}
if(pq){var f=document.querySelector("form");if(f){var p=document.createElement("p");p.className="note";var a=document.createElement("a");a.href="/find?q="+encodeURIComponent(pq.q);a.textContent=pq.q;p.append("ก่อนหน้า · earlier: ",a);f.after(p)}}
if(ol)ol.addEventListener("click",function(e){var a=e.target.closest&&e.target.closest("a[href]");if(!a||a.closest(".ls-acts"))return;
var li=a.closest("li"),i=lis.indexOf(li);if(i<0||!urls[i])return;deep=Math.max(deep,i);
taps.push({u:urls[i],r:S+i,ms:Date.now()-T0});var t=rd();(t.find||[]).forEach(function(x){if(x.q===Q)x.tap=1});
t.away={q:Q,u:urls[i],t:Date.now()};t.open=(t.open||[]).concat({u:urls[i],ti:(li.querySelector("a.t")||a).textContent.slice(0,80),q:Q,t:Date.now()}).slice(-6);wr(t);},true);
function flush(){var need=Math.min(urls.length,Math.max(3,deep+1));if(sentShown>=need&&sentTaps>=taps.length)return;
var nt=taps.length>sentTaps;send({e:"leave",q:Q,pq:pq?pq.q:"",pqt:pq&&pq.tap?1:0,first:first,ft:nt&&!tapSent?1:0,shown:urls.slice(sentShown,need).filter(Boolean),taps:taps.slice(sentTaps)});
if(nt)tapSent=1;first=0;sentShown=Math.max(sentShown,need);sentTaps=taps.length}
addEventListener("pagehide",flush);document.addEventListener("visibilitychange",function(){if(document.visibilityState==="hidden")flush();else backFrom()});
addEventListener("pageshow",function(e){if(e.persisted)backFrom()});
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",main);else main();
})();
