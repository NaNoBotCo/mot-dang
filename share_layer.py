"""share_layer.py — send my location, pick what to send, share from a result.

Nan, 2026-10-01: "I want to be able to easily share my location from any
screen on motdang, either as a snapshot or hour-long share option. I also want
to be able to granularly share everything on a placeid page. And share options
should show up on the results page themselves, along with a grab button and
line button."

One script, JS below, in two places: the end of md.js (every built page) and
docs/locshare.js on its own (the front page and the Worker's /find, which do
not load md.js). It guards itself, so a page carrying both runs it once.

  - a "ส่ง · Send" button pinned to the corner of the screen on every page, in
    reach from any part of the page without scrolling back to a header. It
    offers: this whole page; pick any part; where I am now (one position, as a
    link /live.html?p=lat,lng,acc,epoch); live for an hour through /api/live
    (publish/live.js), the phone sending while a Mot Dang page is open, a share
    in progress carrying from page to page (md-live).
  - "Pick any part", on any page: the page read into sections (each H2 a
    section, the lead block the top), every line its own tick box — dl rows,
    contacts, coordinates, photo, tags, and the running text. Per-section and
    whole-page select-all; the message goes by the phone's share sheet, LINE,
    WhatsApp, email or copy.
  - on a result row (search.html via MDSHAREROW, /find from the Worker's
    markup): share, LINE, and Grab where the row has a pin.

VIEW_JS is /live.html's own: it draws the shared point and follows it.

Nan, 2026-10-03: "Share should be on every screen. Share a picture should be an
option. Sharing should be encouraged and include lots of ways for me to
measure." — and "share a calendar item should be an option. again, with magic
and bells and whistles."

  - KIT_JS (first in md.js / locshare.js, window.MDSHAREKIT): share codes,
    tagged links, the calendar file and Google Calendar link, countdowns. No
    DOM; tests/test_share_kit.mjs.
  - each act of sharing gets an eight-letter code; links that leave carry
    ?s=<code>.<channel>. Events go to POST /api/share (publish/sharesense.js):
    sheet, option, channel, native-done/-cancel/-fail, picture, picture-saved,
    calendar, nudge, nudge-tap, nudge-shut, welcome, arrive. The Worker adds
    land for any request carrying ?s=. Weekly: share_learn.py.
  - "As a picture" in the sheet, a Send on every event, and the welcome a
    shared event opens with: PIC_JS, written to docs/sharepic.js and fetched
    on first use.
  - inject(docs): /locshare.js on each page under docs/ that carries neither
    it nor md.js (the minisites, /loop, /roads, /markets, listings…).
"""

KIT_JS = r"""/* share_layer.py KIT — share codes, tagged links, calendar text. No DOM, so node tests it. */
(function(G){
if(G.MDSHAREKIT)return;
/* 32 letters with no l, o, 0 or 1, so a code read aloud or retyped survives. */
var AL='abcdefghijkmnpqrstuvwxyz23456789',CODE_RE=/^([a-km-np-z2-9]{8})(?:\.([a-z]{1,2}))?$/;
function code(bytes){var b=bytes,s='',i;
  if(!b){try{b=G.crypto.getRandomValues(new Uint8Array(8));}catch(e){b=[];for(i=0;i<8;i++)b.push(Math.floor(Math.random()*256));}}
  for(i=0;i<8;i++)s+=AL.charAt(b[i]&31);return s;}
function parse(s){var m=CODE_RE.exec(String(s||''));return m?{code:m[1],ch:m[2]||''}:null;}
/* the channel rides in the link as one or two letters after the code */
var CH={native:'n',line:'l',whatsapp:'w',mail:'m',copy:'c',facebook:'f',messenger:'g',telegram:'t',x:'x',picture:'p',qr:'q',row:'r'};
var CHNAME={};Object.keys(CH).forEach(function(k){CHNAME[CH[k]]=k;});
function ours(host,here){return /(^|\.)motdang\.net$/.test(host)||(!!here&&host===here);}
function tagUrl(u,c,ch,here){
  var m=/^(https?:\/\/)([^\/?#\s]+)([^?#\s]*)(\?[^#\s]*)?(#\S*)?$/.exec(u);if(!m)return u;
  var host=m[2].replace(/:\d+$/,'').toLowerCase();if(!ours(host,here))return u;
  var q=(m[4]||'').replace(/^\?/,'').split('&').filter(function(p){return p&&!/^s=/.test(p);});
  q.push('s='+c+(ch?'.'+ch:''));
  return m[1]+m[2]+(m[3]||'/')+'?'+q.join('&')+(m[5]||'');}
function tagText(t,c,ch,here){return String(t==null?'':t).replace(/https?:\/\/[^\s<>"']+/g,function(u){
  var tail=/[.,;:!?)\]]+$/.exec(u),core=tail?u.slice(0,-tail[0].length):u;
  return tagUrl(core,c,ch,here)+(tail?tail[0]:'');});}
/* A share link of another app (LINE, WhatsApp, Facebook, Telegram, Messenger, X, mail):
   the payload in its query is read, our links in it tagged, and it is put back. */
var SHARE_APPS=[[/^https:\/\/(social-plugins\.line\.me|line\.me\/R\/share|line\.me\/R\/msg)/,'line'],
  [/^https:\/\/(wa\.me|api\.whatsapp\.com|web\.whatsapp\.com)\//,'whatsapp'],
  [/^https:\/\/(www\.|m\.)?facebook\.com\/(sharer|share\.php|dialog\/share)/,'facebook'],
  [/^(fb-messenger:|https:\/\/(www\.)?facebook\.com\/dialog\/send)/,'messenger'],
  [/^https:\/\/t\.me\/share/,'telegram'],[/^https:\/\/(twitter|x)\.com\/intent/,'x'],[/^mailto:/,'mail']];
function appOf(href){for(var i=0;i<SHARE_APPS.length;i++)if(SHARE_APPS[i][0].test(href||''))return SHARE_APPS[i][1];return '';}
function dec(v){try{return decodeURIComponent(v.replace(/\+/g,' '));}catch(e){return v;}}
function retag(href,c,here){
  var app=appOf(href);if(!app)return href;
  var i=href.indexOf('?');if(i<0)return href;
  var hash='',rest=href.slice(i+1),j=rest.indexOf('#');if(j>=0&&app!=='mail'){hash=rest.slice(j);rest=rest.slice(0,j);}
  var parts=rest.split('&').map(function(p){var k=p.indexOf('=');if(k<0)return p;
    var key=p.slice(0,k);if(!/^(text|u|url|body|link|href)$/.test(key))return p;
    return key+'='+encodeURIComponent(tagText(dec(p.slice(k+1)),c,CH[app],here));});
  return href.slice(0,i+1)+parts.join('&')+hash;}
function lineHref(t){return 'https://line.me/R/share?text='+encodeURIComponent(t);}
function waHref(t){return 'https://wa.me/?text='+encodeURIComponent(t);}
function mailHref(t,subj){return 'mailto:?subject='+encodeURIComponent(subj||'มดแดง · Mot Dang')+'&body='+encodeURIComponent(t);}
function fbHref(u){return 'https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(u);}
function msgrHref(u){return 'fb-messenger://share/?link='+encodeURIComponent(u);}
function tgHref(u,t){return 'https://t.me/share/url?url='+encodeURIComponent(u)+(t?'&text='+encodeURIComponent(t):'');}

/* ---- time, in Chiang Mai (UTC+7, no summer time) ---- */
function at(s){var m=/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?/.exec(String(s||''));if(!m)return NaN;
  return Date.UTC(+m[1],+m[2]-1,+m[3],(+m[4]||0)-7,+m[5]||0,+m[6]||0);}
function bkk(ms){var d=new Date(ms+7*3600e3);return {y:d.getUTCFullYear(),mo:d.getUTCMonth()+1,d:d.getUTCDate(),h:d.getUTCHours(),mi:d.getUTCMinutes(),s:d.getUTCSeconds(),wd:d.getUTCDay()};}
function p2(n){return (n<10?'0':'')+n;}
function ymd(ms){var b=bkk(ms);return ''+b.y+p2(b.mo)+p2(b.d);}
function ymdDash(ms){var b=bkk(ms);return b.y+'-'+p2(b.mo)+'-'+p2(b.d);}
function local(ms){var b=bkk(ms);return ''+b.y+p2(b.mo)+p2(b.d)+'T'+p2(b.h)+p2(b.mi)+p2(b.s);}
function utc(ms){return new Date(ms).toISOString().replace(/[-:]/g,'').replace(/\.\d+/,'');}
/* An event's span: all day when the calendar says so (ad) or the start has no clock time;
   a timed one without an end runs two hours, as the front page's own calendar file has it. */
function span(e){
  var s=at(e.s),hasT=/\d{2}:\d{2}/.test(String(e.s||''))&&!/ 00:00(:00)?$/.test(String(e.s||'')),all=!!e.ad||!hasT,end;
  if(all){var last=e.e?at(String(e.e).slice(0,10)):s;if(!(last>=s))last=s;end=last+864e5;}
  else{end=e.e&&/\d{2}:\d{2}/.test(String(e.e))?at(e.e):NaN;if(!(end>s))end=s+2*3600e3;}
  return {s:s,e:end,all:all};}
var DAY_TH=['อา.','จ.','อ.','พ.','พฤ.','ศ.','ส.'],DAY_EN=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
var MON_TH=['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.'],
    MON_EN=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function when(e){var sp=span(e),b=bkk(sp.s),hm=sp.all?'':' '+p2(b.h)+':'+p2(b.mi);
  var th=DAY_TH[b.wd]+' '+b.d+' '+MON_TH[b.mo-1]+(sp.all?' ทั้งวัน':hm),en=DAY_EN[b.wd]+' '+b.d+' '+MON_EN[b.mo-1]+(sp.all?', all day':hm);
  if(sp.all&&sp.e-sp.s>864e5){var z=bkk(sp.e-864e5);th=DAY_TH[b.wd]+' '+b.d+' '+MON_TH[b.mo-1]+' – '+z.d+' '+MON_TH[z.mo-1];en=b.d+' '+MON_EN[b.mo-1]+' – '+z.d+' '+MON_EN[z.mo-1];}
  return {th:th,en:en,day:b,all:sp.all};}
/* How long until it starts: {state:'soon'|'on'|'past', ms, d, h, m, s} */
function until(e,now){var sp=span(e),n=now==null?Date.now():now;
  if(n>=sp.e)return {state:'past',ms:0};if(n>=sp.s)return {state:'on',ms:sp.e-n};
  var ms=sp.s-n,t=Math.floor(ms/1000);return {state:'soon',ms:ms,d:Math.floor(t/86400),h:Math.floor(t%86400/3600),m:Math.floor(t%3600/60),s:t%60};}
function countText(e,now,secs){var u=until(e,now);
  if(u.state==='past')return {th:'จบไปแล้ว',en:'This one has passed'};
  if(u.state==='on')return {th:'กำลังจัดอยู่ตอนนี้',en:'On now'};
  if(u.d>=2)return {th:'อีก '+u.d+' วัน',en:'in '+u.d+' days'};
  if(u.d===1)return {th:'อีก 1 วัน '+u.h+' ชม.',en:'in 1 day '+u.h+' h'};
  if(secs)return {th:'อีก '+u.h+':'+p2(u.m)+':'+p2(u.s),en:'in '+u.h+':'+p2(u.m)+':'+p2(u.s)};
  if(u.h>0)return {th:'อีก '+u.h+' ชม. '+u.m+' นาที',en:'in '+u.h+' h '+u.m+' min'};
  return {th:'อีก '+Math.max(1,u.m)+' นาที',en:'in '+Math.max(1,u.m)+' min'};}

/* ---- the calendar file (RFC 5545) ---- */
function icsEsc(s){return String(s==null?'':s).replace(/\\/g,'\\\\').replace(/;/g,'\\;').replace(/,/g,'\\,').replace(/\r?\n/g,'\\n');}
function u8len(ch){var c=ch.charCodeAt(0);return c<0x80?1:c<0x800?2:(c>=0xD800&&c<=0xDBFF)?4:3;}
function fold(line){var chars=line.match(/[\uD800-\uDBFF][\uDC00-\uDFFF]|[\s\S]/g)||[],out=[],cur='',n=0;
  chars.forEach(function(ch){var b=u8len(ch);if(n+b>75){out.push(cur);cur=' '+ch;n=1+b;}else{cur+=ch;n+=b;}});
  out.push(cur);return out.join('\r\n');}
function uid(e){return (e.k||'event')+'-'+ymdDash(at(e.s))+'@motdang.net';}
function evUrl(e){return e.link||('https://motdang.net/#ev='+(e.k||''));}
function details(e,url){return [e.d||'',e.cost?'ราคา · Price: '+e.cost:'',e.url&&e.url!==url?e.url:'',url].filter(Boolean).join('\n');}
function ics(e,o){o=o||{};var sp=span(e),url=o.url||evUrl(e),L=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//motdang.net//share//TH','CALSCALE:GREGORIAN','METHOD:PUBLISH'];
  if(!sp.all)L.push('BEGIN:VTIMEZONE','TZID:Asia/Bangkok','BEGIN:STANDARD','DTSTART:19700101T000000','TZOFFSETFROM:+0700','TZOFFSETTO:+0700','TZNAME:+07','END:STANDARD','END:VTIMEZONE');
  L.push('BEGIN:VEVENT','UID:'+uid(e),'DTSTAMP:'+utc(o.now==null?Date.now():o.now));
  if(sp.all)L.push('DTSTART;VALUE=DATE:'+ymd(sp.s),'DTEND;VALUE=DATE:'+ymd(sp.e));
  else L.push('DTSTART;TZID=Asia/Bangkok:'+local(sp.s),'DTEND;TZID=Asia/Bangkok:'+local(sp.e));
  L.push('SUMMARY:'+icsEsc(e.t));
  if(e.v)L.push('LOCATION:'+icsEsc(e.v));
  if(isFinite(e.la)&&isFinite(e.lo)&&e.la!==null&&e.lo!==null)L.push('GEO:'+(+e.la).toFixed(6)+';'+(+e.lo).toFixed(6));
  L.push('DESCRIPTION:'+icsEsc(details(e,url)),'URL:'+url);
  if(!sp.all)L.push('BEGIN:VALARM','ACTION:DISPLAY','DESCRIPTION:'+icsEsc(e.t),'TRIGGER:-PT1H','END:VALARM');
  L.push('END:VEVENT','END:VCALENDAR');
  return L.map(fold).join('\r\n')+'\r\n';}
function gcal(e,o){o=o||{};var sp=span(e),url=o.url||evUrl(e);
  var dates=sp.all?ymd(sp.s)+'/'+ymd(sp.e):local(sp.s)+'/'+local(sp.e);
  return 'https://calendar.google.com/calendar/render?action=TEMPLATE&text='+encodeURIComponent(e.t||'')+'&dates='+dates+
    (sp.all?'':'&ctz=Asia%2FBangkok')+'&details='+encodeURIComponent(details(e,url))+(e.v?'&location='+encodeURIComponent(e.v):'');}
/* the words that go with an event's link */
function evText(e,url){var w=when(e);return [e.t,w.th+' · '+w.en,e.v||'',url||evUrl(e)].filter(Boolean).join('\n');}

G.MDSHAREKIT={code:code,parse:parse,CH:CH,CHNAME:CHNAME,ours:ours,tagUrl:tagUrl,tagText:tagText,appOf:appOf,retag:retag,
  lineHref:lineHref,waHref:waHref,mailHref:mailHref,fbHref:fbHref,msgrHref:msgrHref,tgHref:tgHref,
  at:at,bkk:bkk,span:span,when:when,until:until,countText:countText,ics:ics,gcal:gcal,uid:uid,fold:fold,evUrl:evUrl,evText:evText};
})(typeof window!=='undefined'?window:this);
"""


JS = r"""/* share_layer.py — location share, pick-what-to-send, result-row share. */
(function(){
if(window.MDSHARE)return;
var D=document,API='/api/live',KEY='md-live',HOUR=3600000,ORIGIN=location.origin;
if(!/^https?:/.test(ORIGIN))ORIGIN='https://motdang.net';
function E(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function B(th,en){return '<span class="ls-th" lang="th">'+th+'</span><span class="ls-en" lang="en">'+en+'</span>';}
function I(id,n){n=n||20;var h=D.documentElement.getAttribute('data-icons')||'/icons.svg';
  return '<svg class="lsi" width="'+n+'" height="'+n+'" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><use href="'+E(h)+'#'+id+'"></use></svg>';}
function pad(n){return (n<10?'0':'')+n;}
function hm(t){var d=new Date(t);return pad(d.getHours())+':'+pad(d.getMinutes());}
function grab(lat,lng,name){
  var dp='grab://open?screenType=BOOKING&dropOffLatitude='+(+lat).toFixed(6)+'&dropOffLongitude='+(+lng).toFixed(6)+
    '&dropOffAddress='+encodeURIComponent(name||'');
  return 'https://grab.onelink.me/2695613898?af_dp='+encodeURIComponent(dp)+
    '&af_web_dp='+encodeURIComponent('https://www.grab.com/th/transport/');}
var K=window.MDSHAREKIT,HERE=location.hostname;
function lineHref(t){return K.lineHref(t);}
function waHref(t){return K.waHref(t);}
function mailHref(t){return K.mailHref(t);}

/* ---- share codes, and what gets counted (Nan, 2026-10-03: "sharing should be
   encouraged and include lots of ways for me to measure") ------------------
   Each act of sharing gets a random code of eight letters; a link that leaves
   carries it as ?s=<code>.<channel>. The counter (POST /api/share, the Worker's
   shareSense) gets the event, the code, the channel or option, the page, the
   place or event key, and the code the reader arrived with, if any. */
var COUNT=/(^|\.)motdang\.net$/.test(HERE)&&!!navigator.sendBeacon;
var SQ=[],SN=0,STMO=null,CODE=null,FROM=null,SUBJ='';
try{FROM=sessionStorage.getItem('md-sfrom')||null;}catch(e){}
function subject(){var m=/\/(cm|cr)\/p\/([a-z0-9-]+)\.html$/.exec(location.pathname);if(m)return m[1]+':'+m[2];
  var h=/^#ev=([a-z0-9-]+)/.exec(location.hash);return h?'ev:'+h[1]:'';}
function tell(e,o){try{o=o||{};if(SN>=80)return;SN++;
  var r={e:e},s=o.s||CODE;if(s)r.s=s;
  if(o.d)r.d=String(o.d).toLowerCase().replace(/[^a-z0-9_-]/g,'').slice(0,24);
  var k=o.k||SUBJ||subject();if(k&&/^[a-z]{2}:[a-z0-9-]{1,90}$/.test(k))r.k=k;
  if(FROM&&e!=='arrive')r.p=FROM;
  SQ.push(r);var log=window.MDSHARELOG||(window.MDSHARELOG=[]);if(log.length<200)log.push(r);
  clearTimeout(STMO);STMO=setTimeout(flush,1500);}catch(x){}}
function flush(){clearTimeout(STMO);if(!SQ.length)return;var ev=SQ.splice(0,30);if(!COUNT)return;
  try{navigator.sendBeacon('/api/share',new Blob([JSON.stringify({pg:location.pathname.slice(0,96),ev:ev})],{type:'text/plain'}));}catch(e){}}
addEventListener('pagehide',flush);
D.addEventListener('visibilitychange',function(){if(D.visibilityState==='hidden')flush();});
function fresh(){CODE=K.code();return CODE;}
function tagged(t,ch){return K.tagText(t,CODE||fresh(),K.CH[ch]||'',HERE);}
/* arriving by a shared link: counted once, the code kept for this tab (so a
   share made from here names its parent), and taken off the address bar */
function arrival(){var q,p;
  try{q=new URLSearchParams(location.search);p=K.parse(q.get('s'));}catch(e){return;}
  if(!p)return;
  tell('arrive',{s:p.code,d:K.CHNAME[p.ch]||p.ch||'none'});
  FROM=p.code;try{sessionStorage.setItem('md-sfrom',p.code);}catch(e){}
  flush();q.delete('s');
  try{history.replaceState(history.state,'',location.pathname+(String(q)?'?'+q:'')+location.hash);}catch(e){}
  window.MDSHAREFROM=p;
  if(/^#ev=[a-z0-9-]+$/.test(location.hash))needPic(function(P){P.arrive(location.hash.slice(4));});}

/* The picture, the event sheet and the welcome live in /sharepic.js, fetched
   the first time one is asked for. */
var PICQ=null;
function needPic(cb){
  if(window.MDPIC){cb(window.MDPIC);return;}
  if(PICQ){PICQ.push(cb);return;}PICQ=[cb];
  var s=D.createElement('script');s.src='/sharepic.js?v=__PICV__';s.async=true;
  s.onload=function(){var q=PICQ;PICQ=null;q.forEach(function(f){try{f(window.MDPIC);}catch(e){}});};
  s.onerror=function(){PICQ=null;};D.head.appendChild(s);}
function chanName(h){return /line\.me|lin\.ee/.test(h)?'LINE':/facebook\.com|fb\.com/.test(h)?'Facebook':
  /instagram\.com/.test(h)?'Instagram':/tiktok\.com/.test(h)?'TikTok':/youtube\.com|youtu\.be/.test(h)?'YouTube':
  /wa\.me|whatsapp/.test(h)?'WhatsApp':'เว็บ · Website';}
/* Inside the Mot Dang Android app (motdang-app), window.MotDangApp is the
   phone itself: its share sheet, and a live share that keeps sending with
   the screen locked. Everywhere else the browser does what it can. */
var APP=window.MotDangApp||null;
function canShare(){return !!(APP||navigator.share);}
/* the phone's own share sheet; what it answers is counted (sent, or closed) */
function nativeShare(d,what){
  return navigator.share(d).then(function(){tell('native-done',{d:what});},
    function(e){tell(e&&e.name==='AbortError'?'native-cancel':'native-fail',{d:what});});}
function shareOut(t,file,what,u){
  t=tagged(t,'native');tell('channel',{d:'native'});
  if(APP){try{APP.share(t);}catch(e){}return;}
  if(file)file.then(function(f){var d={text:t,files:[f]};if(u)d.url=u;
      return navigator.canShare&&navigator.canShare(d)?nativeShare(d,what||'file'):nativeShare(u?{text:t,url:u}:{text:t},what);}).catch(function(){});
  else nativeShare(u?{text:t,url:u}:{text:t},what);}
function pageUrl(){var c=D.querySelector('link[rel=canonical]'),q='';
  try{var p=new URLSearchParams(location.search);p.delete('embed');p.delete('s');q=String(p);}catch(e){}
  if(q||location.hash||!c)return location.origin+location.pathname+(q?'?'+q:'')+location.hash;return c.href;}
function pageTitle(){return (D.title||'').replace(/\s*·\s*มดแดง Mot Dang\s*$/,'').trim()||'มดแดง Mot Dang';}
function metres(a,b){var k=Math.cos(a.latitude*Math.PI/180),y=(b.latitude-a.latitude)*111320,x=(b.longitude-a.longitude)*111320*k;
  return Math.sqrt(x*x+y*y);}

/* ---- the sheet ------------------------------------------------------- */
var wrap,body,back;
function sheet(html,label){
  if(!wrap){wrap=D.createElement('div');wrap.className='ls-wrap';wrap.hidden=true;
    wrap.innerHTML='<div class="ls-back" data-ls-x></div><div class="ls-sheet" role="dialog" aria-modal="true">'+
      '<button type="button" class="ls-x" data-ls-x aria-label="ปิด · Close">'+I('i-x',22)+'</button><div class="ls-body"></div></div>';
    D.body.appendChild(wrap);body=wrap.querySelector('.ls-body');
    wrap.addEventListener('click',function(e){if(e.target.closest('[data-ls-x]'))shut();});
    D.addEventListener('keydown',function(e){if(e.key==='Escape'&&!wrap.hidden)shut();});}
  stopAnim();
  back=D.activeElement;body.innerHTML=html;body.dataset.mode=label;
  var sh=wrap.querySelector('.ls-sheet');if(sh)sh.scrollTop=0;
  wrap.querySelector('.ls-sheet').setAttribute('aria-label',label);
  wrap.hidden=false;var f=body.querySelector('button,a,input');if(f)f.focus();}
function shut(){stopAnim();SUBJ='';if(wrap)wrap.hidden=true;if(back&&back.focus)try{back.focus();}catch(e){}}
/* sharepic.js animates its preview while the sheet is open; it hands the stop here */
var ANIMSTOP=null;
function stopAnim(){if(ANIMSTOP){var f=ANIMSTOP;ANIMSTOP=null;try{f();}catch(e){}}}
function open(mode){return wrap&&!wrap.hidden&&body.dataset.mode===mode;}

/* LINE, the phone's own share sheet, copy. The message is read at tap time
   from the sheet's textarea, or data-ls-text when there is none. */
function sendRow(text, ll, addr, name){
  var u=ll?'https://www.google.com/maps/search/?api=1&query='+ll:'';
  var d_url=u?' data-ls-url="'+E(u)+'"':'';
  var d_ll=ll?' data-ls-ll="'+E(ll)+'"':'';
  var d_addr=addr?' data-ls-addr="'+E(addr)+'"':'';
  var d_name=name?' data-ls-name="'+E(name)+'"':'';
  var geo=ll?'geo:'+ll+'?q='+ll+(name?'('+E(name)+')':''):'';
  var apple=ll?'https://maps.apple.com/?ll='+ll+'&q='+E(name||ll):'';
  var grab='';
  if(ll){
    var p=ll.split(',');
    var dp='grab://open?screenType=BOOKING&dropOffLatitude='+p[0]+'&dropOffLongitude='+p[1]+'&dropOffAddress='+E(name||'');
    grab='https://grab.onelink.me/2695613898?af_dp='+encodeURIComponent(dp)+'&af_web_dp='+encodeURIComponent('https://www.grab.com/th/transport/');
  }
  return '<div class="ls-send" data-ls-text="'+E(text)+'"'+d_url+d_ll+d_addr+d_name+'>'+
    (canShare()?'<button type="button" class="ls-b" data-ls-native>'+I('i-share')+B('แชร์','Share')+'</button>':'')+
    '<a class="ls-b ls-line" href="'+E(lineHref(text))+'" target="_blank" rel="noopener">'+I('i-chat')+'LINE</a>'+
    '<a class="ls-b ls-wa" href="'+E(waHref(text))+'" target="_blank" rel="noopener">'+I('i-chat')+'WhatsApp</a>'+
    '<a class="ls-b ls-mail" href="'+E(mailHref(text))+'">'+I('i-mail')+B('อีเมล','Email')+'</a>'+
    '<button type="button" class="ls-b" data-ls-copy>'+I('i-link')+B('คัดลอกข้อความ','Copy text')+'</button>'+
    (ll?'<button type="button" class="ls-b" data-ls-copy-ll>'+I('i-link')+B('คัดลอกพิกัด','Copy coordinates')+'</button>':'')+
    (addr?'<button type="button" class="ls-b" data-ls-copy-addr>'+I('i-link')+B('คัดลอกที่อยู่','Copy address')+'</button>':'')+
    (ll?'<a class="ls-b ls-alt" href="'+grab+'" rel="nofollow noopener">'+I('i-ride')+B('เรียก Grab ไปหา','Ride there · Grab')+'</a>':'')+
    (ll?'<a class="ls-b ls-alt" href="'+geo+'">'+I('i-ride')+B('เปิดแอปแผนที่ / เรียกจ้าง','Geo URI / Apps')+'</a>':'')+
    (ll?'<a class="ls-b ls-alt" href="'+apple+'" rel="noopener" target="_blank">'+I('i-map')+B('Apple Maps','Apple Maps')+'</a>':'')+
    (ll?'<a class="ls-b ls-alt" href="'+E(u)+'" rel="noopener" target="_blank">'+I('i-map')+B('เปิดใน Google Maps','Open in Google Maps')+'</a>':'')+
    '</div>';}
/* keep the channel links in step with the composed message (the picker edits it live). */
function setSendHrefs(t){
  var m={'.ls-line':lineHref(t),'.ls-wa':waHref(t),'.ls-mail':mailHref(t)};
  Object.keys(m).forEach(function(s){var a=body&&body.querySelector(s);if(a)a.href=m[s];});}
function msgOf(el){var box=el.closest('.ls-body'),ta=box&&box.querySelector('.ls-msg');
  if(ta)return ta.value;var s=el.closest('.ls-send');return s?s.getAttribute('data-ls-text'):'';}
function copy(t,btn){
  var ok=function(){if(!btn)return;var o=btn.innerHTML;btn.innerHTML=I('i-check')+B('คัดลอกแล้ว','Copied');
    setTimeout(function(){btn.innerHTML=o;},1600);};
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(ok,function(){old(t);ok();});}
  else{old(t);ok();}}
function old(t){var a=D.createElement('textarea');a.value=t;a.setAttribute('readonly','');a.style.position='fixed';a.style.opacity='0';
  D.body.appendChild(a);a.select();try{D.execCommand('copy');}catch(e){}a.remove();}
D.addEventListener('click',function(e){
  var b=e.target.closest&&e.target.closest('[data-ls-copy],[data-ls-copy-ll],[data-ls-copy-addr],[data-ls-native],[data-ls-share]');if(!b)return;
  if(b.hasAttribute('data-ls-share')){e.preventDefault();fresh();
    var u=b.getAttribute('data-ls-share'),t=b.getAttribute('data-ls-t')||'',k=/\/(cm|cr)\/p\/([a-z0-9-]+)\.html/.exec(u);
    tell('option',{d:'row',k:k?k[1]+':'+k[2]:''});
    if(APP||navigator.share)shareOut(t+'\n'+u,null,'row');
    else{tell('channel',{d:'copy'});copy(tagged(t+'\n'+u,'copy'),b);}return;}
  var t=msgOf(b), p=b.closest('.ls-send'), u=p?p.getAttribute('data-ls-url'):null;
  if(b.hasAttribute('data-ls-copy')){tell('channel',{d:'copy'});copy(tagged(t,'copy'),b);return;}
  if(b.hasAttribute('data-ls-copy-ll')){tell('channel',{d:'copy-ll'});copy(p.getAttribute('data-ls-ll'),b);return;}
  if(b.hasAttribute('data-ls-copy-addr')){tell('channel',{d:'copy-addr'});copy(p.getAttribute('data-ls-addr'),b);return;}
  shareOut(t,pickFile(),open('pick')?'part':'page',u);});
/* Any share link on a page — the sheet's own LINE, WhatsApp and email, the
   place page's share row (build.py share_block), a result row's LINE — has
   our links in it tagged with a code as it is tapped, and the tap counted.
   Inside the sheet the sheet's code; elsewhere a fresh one per tap. */
D.addEventListener('click',function(e){
  var el=e.target.closest&&e.target.closest('a[href],button.copylink[data-url],button[data-native][data-url]');if(!el)return;
  var inSheet=!!el.closest('.ls-wrap');
  if(el.tagName==='A'){
    var h=el.getAttribute('data-ls-orig')||el.getAttribute('href')||'',app=K.appOf(h);if(!app)return;
    if(!inSheet||!CODE)fresh();
    el.setAttribute('data-ls-orig',h);el.setAttribute('href',K.retag(h,CODE,HERE));
    tell('channel',{d:app});return;}
  var u=el.getAttribute('data-ls-orig')||el.getAttribute('data-url');fresh();
  el.setAttribute('data-ls-orig',u);
  var nat=el.hasAttribute('data-native');
  el.setAttribute('data-url',K.tagUrl(u,CODE,nat?'n':'c',HERE));
  tell('channel',{d:nat?'native':'copy'});},true);

/* ---- my location: now, or live for an hour --------------------------- */
var L=null,watch=null,last=null,sentAt=0,sentPos=null,okAt=0,beat=null,tick=null,lock=null;
function load(){try{var v=JSON.parse(localStorage.getItem(KEY));if(v&&v.id&&v.tok&&v.until>Date.now())return v;}catch(e){}return null;}
function keep(v){try{if(v)localStorage.setItem(KEY,JSON.stringify(v));else localStorage.removeItem(KEY);}catch(e){}}
function where(ok,no){
  if(!navigator.geolocation){no(0);return;}
  navigator.geolocation.getCurrentPosition(function(p){
    /* the shared tab record every map on the page reads (sessionStorage md-here, twenty minutes) */
    try{sessionStorage.setItem('md-here',JSON.stringify({lat:p.coords.latitude,lng:p.coords.longitude,acc:p.coords.accuracy,t:Date.now()}));}catch(e){}
    ok(p.coords,p.timestamp||Date.now());},function(e){no(e&&e.code);},
    {enableHighAccuracy:true,timeout:20000,maximumAge:15000});}
function whyNot(code){
  return '<p class="ls-err">'+(code===1?B('เบราว์เซอร์ยังไม่ได้รับอนุญาตให้บอกตำแหน่ง — เปิดในการตั้งค่าของเบราว์เซอร์แล้วลองอีกครั้ง',
      'The browser has not been allowed your location — allow it in the browser settings and try again')
    :code==='api'?B('ส่งตำแหน่งสดไม่ได้ตอนนี้ ลองอีกครั้ง','Live sharing did not start; try again')
    :B('หาตำแหน่งไม่ได้ ลองอีกครั้งตรงที่เห็นท้องฟ้า','No position came back; try again where the sky is in view'))+'</p>';}
function liveLink(){return ORIGIN+'/live.html?l='+L.id;}
function liveText(){return 'ตำแหน่งสดของฉัน ถึง '+hm(L.until)+' · My live location until '+hm(L.until)+'\n'+liveLink();}

/* the event the page is showing: the front page's #ev=<key> */
function evHere(){var h=/^#ev=([a-z0-9-]+)$/.exec(location.hash);return h?h[1]:'';}
function menu(src){
  fresh();SUBJ='';tell('sheet',{d:typeof src==='string'?src:'button'});
  var ek=evHere();
  var live=L?'<button type="button" class="ls-big ls-livebtn" data-ls-open>'+I('i-live',26)+'<span><b>'+
      B('ตำแหน่งสด · อีก '+left()+' นาที','Live location · '+left()+' min left')+'</b>'+
      '<small>'+B('ดู ส่งลิงก์ หรือหยุด','see it, send the link, or stop')+'</small></span></button>'
    :'<button type="button" class="ls-big" data-ls-live>'+I('i-live',26)+'<span><b>'+B('ตำแหน่งสด 1 ชั่วโมง','Live location, 1 hour')+'</b>'+
      '<small>'+(APP?B('หมุดขยับตามคุณ ส่งต่อแม้ล็อกจอ','the pin follows you, screen locked or not')
                    :B('หมุดขยับตามคุณ ขณะเปิดหน้ามดแดงไว้','the pin follows you while a Mot Dang page is open'))+'</small></span></button>';
  sheet('<h2>'+B('ส่ง','Send')+'</h2>'+
    (ek?'<button type="button" class="ls-big ls-hot" data-ls-ev="'+ek+'">'+I('i-cal',26)+'<span><b>'+B('งานนี้ พร้อมภาพ','This event, with its picture')+'</b>'+
      '<small>'+B('ภาพวาด วันเวลา นับถอยหลัง ลงปฏิทิน','its drawing, the date, a countdown, add to calendar')+'</small></span></button>':'')+
    '<button type="button" class="ls-big" data-ls-page>'+I('i-link',26)+'<span><b>'+B('ทั้งหน้านี้','This whole page')+'</b>'+
      '<small>'+E(pageTitle())+'</small></span></button>'+
    '<button type="button" class="ls-big'+(ek?'':' ls-hot')+'" data-ls-pic>'+I('i-camera',26)+'<span><b>'+B('เป็นภาพ','As a picture')+'</b>'+
      '<small>'+B('ภาพของหน้านี้ ส่งต่อหรือเก็บไว้','a picture of this page, to send or keep')+'</small></span></button>'+
    '<button type="button" class="ls-big" data-ls-pick>'+I('i-check',26)+'<span><b>'+B('เลือกเฉพาะส่วน','Pick any part')+'</b>'+
      '<small>'+B('ทุกส่วนในหน้านี้ แยกเลือกได้ทีละบรรทัด','every part of this page, line by line')+'</small></span></button>'+
    '<button type="button" class="ls-big" data-ls-now>'+I('i-pin',26)+'<span><b>'+B('ตำแหน่งฉันตอนนี้','Where I am now')+'</b>'+
      '<small>'+B('ตำแหน่งเดียว ณ เวลานี้','one position, as of now')+'</small></span></button>'+
    live+'<div class="ls-out" aria-live="polite"></div>','send');
  body.querySelector('[data-ls-page]').addEventListener('click',function(){
    tell('option',{d:'page'});
    var t=pageTitle()+'\n'+pageUrl();
    if(canShare()){shareOut(t,null,'page');return;}
    body.querySelectorAll('.ls-big').forEach(function(x){x.hidden=true;});
    body.querySelector('.ls-out').innerHTML='<p class="ls-ok">'+E(pageTitle())+'</p>'+sendRow(t);});
  body.querySelector('[data-ls-pic]').addEventListener('click',function(e){busy(e.currentTarget,true);
    tell('option',{d:'picture'});needPic(function(P){P.picture();});});
  var pk=body.querySelector('[data-ls-pick]');if(pk)pk.addEventListener('click',function(){tell('option',{d:'part'});pick();});
  body.querySelector('[data-ls-now]').addEventListener('click',function(e){tell('option',{d:'now'});now(e);});
  var lv=body.querySelector('[data-ls-live]');if(lv)lv.addEventListener('click',function(e){tell('option',{d:'live'});startLive(e);});
  var op=body.querySelector('[data-ls-open]');if(op)op.addEventListener('click',liveSheet);}

function busy(b,on){b.disabled=on;b.classList.toggle('ls-wait',on);}
function now(e){var b=e.currentTarget,out=body.querySelector('.ls-out');busy(b,true);out.innerHTML='';
  where(function(c,t){busy(b,false);
    var link=ORIGIN+'/live.html?p='+c.latitude.toFixed(6)+','+c.longitude.toFixed(6)+','+Math.round(c.accuracy||0)+','+Math.round(t/1000);
    var text='ฉันอยู่ตรงนี้ เมื่อ '+hm(t)+' · I am here, as of '+hm(t)+'\n'+link;
    var a=Math.round(c.accuracy||0);
    var ll=c.latitude.toFixed(6)+','+c.longitude.toFixed(6);
    body.querySelectorAll('.ls-big').forEach(function(x){x.hidden=true;});
    out.innerHTML='<p class="ls-ok">'+B('ได้ตำแหน่งแล้ว ±'+a+' ม. เวลา '+hm(t),'Got it, ±'+a+' m, '+hm(t))+'</p>'+sendRow(text, ll);
    var f=out.querySelector('.ls-b');if(f)f.focus();},
  function(code){busy(b,false);out.innerHTML=whyNot(code);});}

function startLive(e){var b=e.currentTarget,out=body.querySelector('.ls-out');busy(b,true);out.innerHTML='';
  where(function(c){
    fetch(API,{method:'POST'}).then(function(r){return r.json();}).then(function(d){
      if(!d||!d.id)throw 0;
      L={id:d.id,tok:d.tok,until:d.until};
      if(APP&&APP.startLive){try{APP.startLive(d.id,d.tok,String(d.until));L.app=1;okAt=0;}catch(x){}}
      keep(L);last=c;
      if(L.app){tick=setInterval(paint,10000);paint();}else{run();push(true);}
      liveSheet();
    }).catch(function(){busy(b,false);out.innerHTML=whyNot('api');});},
  function(code){busy(b,false);out.innerHTML=whyNot(code);});}

function run(){
  if(!L||watch!=null||!navigator.geolocation)return;
  watch=navigator.geolocation.watchPosition(function(p){last=p.coords;push(false);},function(){},
    {enableHighAccuracy:true,maximumAge:5000,timeout:60000});
  beat=setInterval(function(){push(true);},30000);
  tick=setInterval(paint,10000);
  D.addEventListener('visibilitychange',seen);wake();paint();}
function seen(){if(D.visibilityState==='visible'){wake();push(true);}}
function wake(){try{if(navigator.wakeLock&&!lock)navigator.wakeLock.request('screen').then(function(l){lock=l;
  l.addEventListener('release',function(){lock=null;});}).catch(function(){});}catch(e){}}
/* Sent when it has moved 25 m, or 15 s have passed, and on the 30 s beat so
   the viewer can tell a phone standing still from one that stopped. */
function push(force){
  if(!L||!last)return;var t=Date.now();
  if(t>=L.until){stop(true);return;}
  if(t-sentAt<4000)return;
  if(!force&&t-sentAt<15000&&sentPos&&metres(sentPos,last)<25)return;
  sentAt=t;sentPos={latitude:last.latitude,longitude:last.longitude};
  fetch(API+'/'+L.id,{method:'POST',keepalive:true,headers:{'content-type':'application/json'},
    body:JSON.stringify({tok:L.tok,lat:last.latitude,lng:last.longitude,acc:last.accuracy})})
  .then(function(r){if(r.status===410||r.status===403||r.status===404)stop(true);else if(r.ok){okAt=Date.now();paint();}})
  .catch(function(){});}
function stop(quiet){
  if(L&&L.app&&APP){try{if(!quiet)APP.stopLive();}catch(e){}quiet=true;}
  if(watch!=null&&navigator.geolocation)navigator.geolocation.clearWatch(watch);
  watch=null;clearInterval(beat);clearInterval(tick);D.removeEventListener('visibilitychange',seen);
  if(lock)try{lock.release();}catch(e){}lock=null;
  if(L&&!quiet)fetch(API+'/'+L.id,{method:'POST',keepalive:true,headers:{'content-type':'application/json'},
    body:JSON.stringify({tok:L.tok,stop:1})}).catch(function(){});
  L=null;last=null;sentAt=0;sentPos=null;okAt=0;keep(null);paint();
  if(open('live'))menu();}

function left(){return Math.max(0,Math.ceil((L.until-Date.now())/60000));}
function status(){
  if(!L)return '';
  var s=B('ส่งอยู่ ถึง '+hm(L.until)+' (อีก '+left()+' นาที)','Sharing until '+hm(L.until)+' ('+left()+' min left)');
  if(okAt)s+=' · '+B('ส่งล่าสุด '+hm(okAt),'last sent '+hm(okAt));
  else if(watch==null&&!L.app)s+=' · '+B('หยุดอยู่ แตะ "ส่งต่อ"','paused — tap Resume');
  return s;}
function liveSheet(){
  var ll = last ? last.latitude.toFixed(6) + ',' + last.longitude.toFixed(6) : '';
  sheet('<h2>'+B('ตำแหน่งสด','Live location')+'</h2><p class="ls-stat">'+status()+'</p>'+
    (watch==null&&!L.app?'<button type="button" class="ls-big" data-ls-resume>'+I('i-live',26)+'<span><b>'+B('ส่งต่อ','Resume')+'</b></span></button>':'')+
    sendRow(liveText(), ll)+
    '<p class="ls-note">'+(L.app?B('แอปมดแดงส่งต่อแม้ล็อกจอ หยุดได้จากที่นี่หรือจากแถบแจ้งเตือน',
      'The Mot Dang app keeps sending with the screen locked. Stop it here or from the notification.')
     :B('มือถือส่งตำแหน่งขณะเปิดหน้ามดแดงอยู่ ถ้าล็อกจอหรือปิดเบราว์เซอร์ หมุดจะหยุดที่ตำแหน่งล่าสุด',
      'Your phone sends while a Mot Dang page is open. Lock the screen or close the browser and the pin stays at the last place sent.'))+'</p>'+
    '<button type="button" class="ls-stop" data-ls-stop>'+I('i-x')+B('หยุดส่ง','Stop sharing')+'</button>','live');
  body.querySelector('[data-ls-stop]').addEventListener('click',function(){stop(false);});
  var r=body.querySelector('[data-ls-resume]');
  if(r)r.addEventListener('click',function(){busy(r,true);where(function(c){last=c;run();push(true);liveSheet();},
    function(code){busy(r,false);r.insertAdjacentHTML('afterend',whyNot(code));});});}
function paint(){
  if(L&&Date.now()>=L.until){stop(true);return;}
  /* stopped from the app's notification */
  if(L&&L.app&&APP&&APP.liveState){try{var a=APP.liveState();if(!a){stop(true);return;}okAt=+JSON.parse(a).ok||0;}catch(e){}}
  var b=D.querySelector('.ls-me');
  if(b){b.classList.toggle('ls-on',!!L);
    var n=b.querySelector('.ls-n');
    if(L){if(!n){n=D.createElement('span');n.className='ls-n';b.appendChild(n);}n.textContent=left()+'′';}
    else if(n)n.remove();}
  if(open('live')){var s=body.querySelector('.ls-stat');if(s)s.innerHTML=status();}}

/* One Send button, pinned to the corner of the screen so it stays in reach
   from any part of any page — no scrolling back to a header to share. */
function mount(){
  if(D.querySelector('.ls-me'))return;
  /* inside a frame (the doodle maps on the front page and on place maps) the
     button shows only while that map fills the screen (html.tool) */
  try{if(window.parent!==window)D.documentElement.classList.add('ls-framed');}catch(e){}
  var b=D.createElement('button');b.type='button';b.className='ls-me ls-float';
  b.setAttribute('aria-label','ส่งหน้านี้ เป็นภาพ ส่วนใดก็ได้ในหน้า หรือตำแหน่งของฉัน · Send this page, a picture of it, any part of it, or my location');
  b.title='ส่ง · Send';
  b.innerHTML=I('i-share',20)+'<span class="ls-lab">'+B('ส่ง','Send')+'</span>';
  D.body.appendChild(b);
  b.addEventListener('click',function(){hush();menu('button');});}

/* ---- a word at the right moment -------------------------------------------
   After keeping a place, after asking the way, after keeping an event, and a
   while into the drawn map: one small note beside the Send button, once a
   page, twice a visit. Closed three times, it rests for a month. */
var NUDGE=null,NUDGED=false;
function nudgeOff(){try{var v=JSON.parse(localStorage.getItem('md-nudge')||'{}');
  if(v.n>=3&&Date.now()-v.t<30*864e5)return true;
  return +(sessionStorage.getItem('md-nudges')||0)>=2;}catch(e){return false;}}
function nudge(kind,th,en,go){
  if(NUDGED||nudgeOff()||(wrap&&!wrap.hidden))return;
  var b=D.querySelector('.ls-me');if(!b||getComputedStyle(b).display==='none')return;
  NUDGED=true;try{sessionStorage.setItem('md-nudges',+(sessionStorage.getItem('md-nudges')||0)+1);}catch(e){}
  var n=D.createElement('div');n.className='ls-nudge';n.setAttribute('role','status');
  n.innerHTML='<button type="button" class="ls-nudge-go">'+I('i-share',18)+'<span>'+B(th,en)+'</span></button>'+
    '<button type="button" class="ls-nudge-x" aria-label="ปิด · Close">'+I('i-x',16)+'</button>';
  D.body.appendChild(n);NUDGE=n;tell('nudge',{d:kind});
  n.querySelector('.ls-nudge-go').addEventListener('click',function(){tell('nudge-tap',{d:kind});hush();go();});
  n.querySelector('.ls-nudge-x').addEventListener('click',function(){tell('nudge-shut',{d:kind});hush();
    try{var v=JSON.parse(localStorage.getItem('md-nudge')||'{}');if(!(Date.now()-(v.t||0)<30*864e5))v={n:0};
      v.n=(v.n||0)+1;v.t=Date.now();localStorage.setItem('md-nudge',JSON.stringify(v));}catch(e){}});
  setTimeout(hush,14000);}
function hush(){if(NUDGE){NUDGE.remove();NUDGE=null;}}
var DIR_RE=/google\.[a-z.]+\/maps\/dir|maps\.apple\.com|grab\.onelink|grab:\/\/|\/plan\.html/;
function watchMoments(){
  var asked=0;
  D.addEventListener('click',function(e){var t=e.target.closest&&e.target.closest('a[href],button');if(!t||t.closest('.ls-wrap,.ls-nudge,.ls-me'))return;
    /* keeping: a place page's plan button, a calendar event's keep, a map's save */
    if(t.matches('[data-plan]'))setTimeout(function(){if(t.getAttribute('aria-pressed')==='true')
      nudge('saved','เก็บไว้แล้ว ส่งให้เพื่อนด้วยไหม','Kept. Send it to a friend too?',function(){menu('nudge');});},400);
    else if(t.matches('[data-save]')){var k=t.getAttribute('data-save');setTimeout(function(){var n=D.querySelector('[data-save="'+k.replace(/[^a-z0-9-]/g,'')+'"]');if(n&&n.classList.contains('on'))
      nudge('event','ชวนใครไปด้วยไหม ส่งงานนี้พร้อมภาพ','Bring someone? Send this event with its picture',function(){evShare(k,'nudge');});},400);}
    /* the way there: directions, Grab, the guide, the photo walk */
    else if(t.matches('.waybtn,.grabride,.ls-grab')||(t.tagName==='A'&&DIR_RE.test(t.href))){asked=Date.now();
      setTimeout(function(){if(D.visibilityState==='visible')askWay();},5000);}},true);
  D.addEventListener('visibilitychange',function(){if(D.visibilityState==='visible'&&asked&&Date.now()-asked<20*60e3)setTimeout(askWay,700);});
  function askWay(){if(!asked)return;asked=0;
    nudge('directions','ไปกับใคร ส่งที่นี่ให้เขาด้วย','Going with someone? Send them this place',function(){menu('nudge');});}
  /* the drawn map, a while after it opens full screen (or on its own page) */
  if(D.getElementById('map')&&/\/sites\/doodle-/.test(location.pathname)){
    var since=0;setInterval(function(){var full=!D.documentElement.classList.contains('embed')||D.documentElement.classList.contains('tool');
      since=full?since+1:0;if(since===25)nudge('doodle','ส่งภาพแผนที่วาดนี้ให้เพื่อน','Send a picture of this drawing',function(){fresh();tell('option',{d:'picture'});needPic(function(P){P.picture();});});},1000);}}

/* ---- events: a Send on each one --------------------------------------------
   The front page's calendar (details.ev), the drawing's caption (.ddacts),
   /find's calendar box (.calf), and the cards on /events.html. */
function evShare(k,src){fresh();SUBJ='ev:'+k;tell('option',{d:'event',k:'ev:'+k});needPic(function(P){P.event(k,src);});}
function evButtons(){
  D.querySelectorAll('details.ev[data-k] .acts').forEach(function(a){if(a.querySelector('.ls-evb'))return;
    a.insertAdjacentHTML('afterbegin','<button type="button" class="ls-evb" data-ls-ev="'+E(a.closest('details.ev').getAttribute('data-k'))+'">'+I('i-share',18)+B('ส่งงานนี้','Send this')+'</button>');});
  D.querySelectorAll('.ddacts').forEach(function(a){if(a.querySelector('.ls-evb'))return;var l=a.querySelector('a[href^="#ev="]');if(!l)return;
    a.insertAdjacentHTML('beforeend','<button type="button" class="ls-evb" data-ls-ev="'+E(l.getAttribute('href').slice(4))+'">'+I('i-share',16)+B('ส่ง','Send')+'</button>');});
  D.querySelectorAll('.calf li a.et[href*="#ev="]').forEach(function(a){if(a.nextElementSibling&&a.nextElementSibling.classList.contains('ls-evi'))return;
    a.insertAdjacentHTML('afterend',' <button type="button" class="ls-evi" data-ls-ev="'+E(a.getAttribute('href').split('#ev=')[1])+'" aria-label="ส่งงานนี้ · Send this event">'+I('i-share',16)+'</button>');});
  D.querySelectorAll('article.evcard .evacts').forEach(function(a,i){if(a.querySelector('.ls-evb'))return;
    a.insertAdjacentHTML('afterbegin','<button type="button" class="ls-evb" data-ls-evcard>'+I('i-share',18)+B('ส่งงานนี้','Send this')+'</button>');});}
D.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('[data-ls-ev],[data-ls-evcard]');if(!b)return;
  e.preventDefault();e.stopPropagation();hush();
  if(b.hasAttribute('data-ls-ev')){evShare(b.getAttribute('data-ls-ev'),b.closest('.ls-wrap')?'sheet':'card');return;}
  fresh();tell('option',{d:'event'});var card=b.closest('article.evcard');needPic(function(P){P.eventCard(card);});});
function watchEvents(){
  if(!D.querySelector('#cal,.calf,article.evcard,#doodle,.ddacts'))return;
  evButtons();if(!window.MutationObserver)return;
  var t=null;new MutationObserver(function(){clearTimeout(t);t=setTimeout(evButtons,250);})
    .observe(D.body,{childList:true,subtree:true});}

/* ---- arriving from another app's share sheet --------------------------
   The installed app (manifest share_target, and motdang-app on Android)
   opens /map.html?su=&st=&sn= with whatever was shared: a Google Maps link,
   a LINE location, coordinates, a plus code, a place ID or a name. The map's
   own box reads it; a Google short link is opened out by /api/resolve. */
function inbound(){
  if(!/\/map(\.html)?$/.test(location.pathname))return;
  var q=new URLSearchParams(location.search),parts=[q.get('su'),q.get('st'),q.get('sn')].filter(Boolean);
  if(!parts.length)return;
  ['su','st','sn'].forEach(function(k){q.delete(k);});
  try{history.replaceState(null,'',location.pathname+(String(q)?'?'+q:'')+location.hash);}catch(e){}
  var all=parts.join(' '),m=all.match(/https?:\/\/[^\s]+/),t=(m?m[0]:all).trim().slice(0,500);
  var p=/^https?:\/\/(maps\.app\.goo\.gl|goo\.gl\/maps|g\.co\/kgs)\//.test(t)
    ?fetch('/api/resolve?u='+encodeURIComponent(t)).then(function(r){return r.json();}).then(function(d){return d&&d.url||t;},function(){return t;})
    :Promise.resolve(t);
  p.then(function(v){var n=0,iv=setInterval(function(){
    var f=D.getElementById('mfq'),i=D.getElementById('mfin');
    if(f&&i&&window.MDX){clearInterval(iv);i.value=v;
      if(f.requestSubmit)f.requestSubmit();else f.dispatchEvent(new Event('submit',{cancelable:true}));}
    else if(++n>300)clearInterval(iv);},100);});}

/* ---- pick what to send, on a place page ------------------------------ */
var PHOTO=null;
function pickFile(){
  if(!PHOTO||!open('pick'))return null;
  var on=body.querySelector('input[data-k="photo"]');if(!on||!on.checked)return null;
  return fetch(PHOTO).then(function(r){return r.blob();}).then(function(b){
    return new File([b],(PHOTO.split('/').pop()||'photo.jpg').split('?')[0],{type:b.type||'image/jpeg'});});}
function txt(el){
  if(!el)return '';var c=el.cloneNode(true),m=D.documentElement.classList;
  c.querySelectorAll('.count,.tinynote,.mk,svg,script,button,.sr,.vh').forEach(function(x){x.remove();});
  if(m.contains('lang-th'))c.querySelectorAll('.bi>.en').forEach(function(x){x.remove();});
  if(m.contains('lang-en'))c.querySelectorAll('.bi>.th,.bi>.en>.th').forEach(function(x){x.remove();});
  return (c.textContent||'').replace(/\s+/g,' ').replace(/^[\s·]+|[\s·]+$/g,'');}
function phone(d){d=String(d).replace(/[^\d+]/g,'');if(/^\+66/.test(d))d='0'+d.slice(3);
  if(/^0\d{9}$/.test(d))return d.slice(0,3)+'-'+d.slice(3,6)+'-'+d.slice(6);
  if(/^0\d{8}$/.test(d))return d.slice(0,2)+'-'+d.slice(2,5)+'-'+d.slice(5);return d;}
function abs(h){try{return new URL(h,location.href).href;}catch(e){return h;}}
/* Read the whole page into sections. Each H2 opens a section; whatever comes
   before the first H2 is the top section (the page's name, address, map, phone
   — the things a place page leads with). Every line is its own item: dl rows,
   contact links, coordinates, the photo, tags, and the running text of each
   section, so any part of any page can go out on its own or together. */
var FOLLOW=(typeof Node!=='undefined'&&Node.DOCUMENT_POSITION_FOLLOWING)||4;
var SKIP='.share,.ls-wrap,.ls-send,.adbox,footer,.footsos,nav,.langgroup,.seekrow,'+
  '.tagrow,.honpanel,.prov,.anthill,.beadrule,.nownear,.svcbar,.qrbox,.mast,.livebox,dl';
function scan(){
  var main=D.querySelector('main')||D.body,h2s=[].slice.call(main.querySelectorAll('h2'));
  var groups=[],byKey={},seen={},gen=0,cut=false;
  function keyOf(el){var best=null;for(var i=0;i<h2s.length;i++){var h=h2s[i];
    if(h===el||(h.compareDocumentPosition(el)&FOLLOW))best=h;else break;}return best;}
  function grp(el){var h=keyOf(el),id=h?'h'+h2s.indexOf(h):'__top__';
    if(byKey[id])return byKey[id];
    var g={label:h?txt(h):pageTitle(),el:h||main,items:[]};byKey[id]=g;groups.push(g);return g;}
  function add(el,k,label,v,on){v=String(v==null?'':v).replace(/\s+/g,' ').trim();
    if(!v||seen[v])return;seen[v]=1;grp(el).items.push({k:k,l:label||'',v:v,on:!!on,el:el});}
  grp(main);                                              /* top leads even when empty */
  var h1=main.querySelector('h1');if(h1)add(h1,'name','',txt(h1),true);
  var dl=main.querySelector('dl');
  if(dl)dl.querySelectorAll('dt').forEach(function(dt){
    var dd=dt.nextElementSibling;if(!dd||dd.tagName!=='DD')return;var label=txt(dt);
    if(dd.querySelector('a[href*="map.html"]'))return;
    var code=dd.querySelector('code.mdcode');
    if(code){add(dd,'id',label,code.textContent.trim()+' — '+ORIGIN+'/map.html?go='+encodeURIComponent(code.textContent.trim()),true);return;}
    add(dd,'dd',label,txt(dd),/ที่อยู่|เวลา|Address|Hours|Open/i.test(label));});
  main.querySelectorAll('a[href]').forEach(function(a){
    if(a.closest('.share,.ls-wrap,nav,footer,.footsos,.langgroup,.tagrow'))return;
    var h=a.getAttribute('href')||'';
    if(/^tel:/.test(h))add(a,'tel','โทร · Phone',phone(h.slice(4)),!!a.closest('.reach'));
    else if(/^mailto:/.test(h))add(a,'mail','อีเมล · Email',decodeURIComponent(h.slice(7).split('?')[0]),false);
    else if(/^https?:/.test(h)&&!/map\.html/.test(h))add(a,'web',chanName(h),h,false);});
  var pin=main.querySelector('.waypics[data-to]'),lat,lng,at;
  if(pin){var p=pin.getAttribute('data-to').split(',');lat=+p[0];lng=+p[1];at=pin;}
  else{var m=main.querySelector('[data-mdmap][data-lat]');if(m){lat=+m.getAttribute('data-lat');lng=+m.getAttribute('data-lng');at=m;}}
  if(isFinite(lat)&&isFinite(lng)&&lat){at=at||main;
    add(at,'ll','พิกัด · Coordinates',lat.toFixed(6)+', '+lng.toFixed(6),false);
    add(at,'gm','Google Maps','https://www.google.com/maps/search/?api=1&query='+lat.toFixed(6)+','+lng.toFixed(6),true);
    add(at,'apple','Apple Maps','https://maps.apple.com/?ll='+lat.toFixed(6)+','+lng.toFixed(6)+'&q='+lat.toFixed(6)+','+lng.toFixed(6),false);
    add(at,'geo','แอปแผนที่ / Geo URI','geo:'+lat.toFixed(6)+','+lng.toFixed(6)+'?q='+lat.toFixed(6)+','+lng.toFixed(6),false);
    add(at,'dir','นำทาง · Directions','https://www.google.com/maps/dir/?api=1&destination='+lat.toFixed(6)+','+lng.toFixed(6),false);
    var pk=main.querySelector('.planbtn-lg[data-plan]');
    if(pk)add(at,'guide','นำทางกับมดแดง · Guide me',ORIGIN+'/plan.html?stops='+encodeURIComponent(pk.getAttribute('data-plan'))+'&go=1',false);
    var g=main.querySelector('a.grabride');add(at,'grab','Grab',g?g.href:grab(lat,lng,h1?txt(h1):''),false);}
  var img=main.querySelector('img.photo');PHOTO=img?abs(img.getAttribute('src')):null;
  if(PHOTO)add(img,'photo','รูป · Photo',PHOTO,false);
  var tagEls=main.querySelectorAll('.tagrow a.tag');
  if(tagEls.length){var tags=[].map.call(tagEls,txt).filter(Boolean);
    if(tags.length)add(tagEls[0],'tags','แท็ก · Tags',tags.join(', '),false);}
  var markEls=main.querySelectorAll('.honpanel li b');
  if(markEls.length){var marks=[].map.call(markEls,txt).filter(Boolean);
    if(marks.length)add(markEls[0],'marks','เครื่องหมาย · Marks',marks.join(' · '),false);}
  /* the running text: every leaf paragraph and list line the page shows */
  main.querySelectorAll('p,li,blockquote,figcaption,h3,h4').forEach(function(el){
    if(cut||el.closest(SKIP))return;
    if(el.querySelector('p,li,ul,ol,dl'))return;              /* leaves only */
    var t=txt(el);if(!t||t.length<2)return;
    if(gen++>=160){cut=true;return;}add(el,'text','',t,false);});
  var canon=D.querySelector('link[rel=canonical]');
  add(main,'page','มดแดง · Mot Dang',canon?canon.href:pageUrl().split('#')[0],true);
  groups.sort(function(a,b){if(a.el===main)return -1;if(b.el===main)return 1;
    return (a.el.compareDocumentPosition(b.el)&FOLLOW)?-1:1;});
  var out=groups.filter(function(g){return g.items.length;}),i=0;
  out.forEach(function(g){g.items.forEach(function(it){it._i=i++;});});
  out.cut=cut;return out;}
/* the section nearest the top of the screen — its items come pre-ticked */
function inView(groups){var best=groups[0]||null;
  groups.forEach(function(g){if(g.el&&g.el.getBoundingClientRect){
    var r=g.el.getBoundingClientRect();if(r.top<=140)best=g;}});return best;}
function flatten(groups){var f=[];groups.forEach(function(g){g.items.forEach(function(it){f[it._i]=it;});});return f;}
function pick(){
  var groups=scan(),main=D.querySelector('main')||D.body,iv=inView(groups);
  /* the section you are looking at comes pre-ticked — but the top block keeps
     its curated defaults (name, address, hours, map) rather than everything. */
  if(iv&&iv.el!==main)iv.items.forEach(function(it){if(it.k!=='text')it.on=true;});
  var flat=flatten(groups);
  var html='<h2>'+B('เลือกส่ง','Pick what to send')+'</h2>'+
    '<p class="ls-all"><button type="button" data-ls-all="1">'+B('เลือกทั้งหมด','All')+'</button> '+
      '<button type="button" data-ls-all="0">'+B('ไม่เลือก','None')+'</button></p>';
  groups.forEach(function(g,gx){
    var lis=g.items.map(function(it){
      return '<li><label><input type="checkbox" data-i="'+it._i+'" data-g="'+gx+'" data-k="'+it.k+'"'+(it.on?' checked':'')+'>'+
        '<span>'+(it.l?'<b>'+E(it.l)+'</b> ':'')+E(it.v.length>140?it.v.slice(0,140)+'…':it.v)+'</span></label></li>';}).join('');
    /* the lead block (before the first heading) rides bare; each section is a box with a select-all */
    if(gx===0&&g.el===main)html+='<ul class="ls-pick ls-top">'+lis+'</ul>';
    else html+='<div class="ls-grp"><label class="ls-ghd"><input type="checkbox" class="ls-gall" data-g="'+gx+'"><b>'+
      (E(g.label)||'ส่วนนี้ · This section')+'</b></label><ul class="ls-pick">'+lis+'</ul></div>';});
  html+=(groups.cut?'<p class="ls-note">'+B('หน้านี้ยาว แสดงส่วนข้อความบางส่วน','A long page — some of the running text is left off this list')+'</p>':'')+
    '<label class="ls-ml">'+B('ข้อความ','Message')+'<textarea class="ls-msg" rows="5"></textarea></label>'+sendRow('');
  sheet(html,'pick');
  var ta=body.querySelector('.ls-msg');
  function compose(){var out=[],lastG=-1;
    [].forEach.call(body.querySelectorAll('.ls-pick input:checked'),function(x){
      var it=flat[+x.getAttribute('data-i')],gx=+x.getAttribute('data-g');if(!it)return;
      if(gx!==lastG){var g=groups[gx];if(g&&g.label&&gx!==0){if(out.length)out.push('');out.push('— '+g.label+' —');}lastG=gx;}
      out.push(it.l?it.l+': '+it.v:it.v);});
    return out.join('\n');}
  function syncGroups(){body.querySelectorAll('.ls-gall').forEach(function(ga){
    var gx=ga.getAttribute('data-g'),ins=body.querySelectorAll('.ls-pick input[data-g="'+gx+'"]'),on=0;
    ins.forEach(function(x){if(x.checked)on++;});
    ga.checked=on===ins.length&&on>0;ga.indeterminate=on>0&&on<ins.length;});}
  function redo(){ta.value=compose();setSendHrefs(ta.value);syncGroups();}
  body.querySelectorAll('.ls-pick').forEach(function(u){u.addEventListener('change',redo);});
  body.querySelectorAll('.ls-gall').forEach(function(ga){ga.addEventListener('change',function(){
    var gx=ga.getAttribute('data-g');body.querySelectorAll('.ls-pick input[data-g="'+gx+'"]').forEach(function(x){x.checked=ga.checked;});redo();});});
  ta.addEventListener('input',function(){setSendHrefs(ta.value);});
  body.querySelectorAll('[data-ls-all]').forEach(function(b){b.addEventListener('click',function(){
    var v=b.getAttribute('data-ls-all')==='1';body.querySelectorAll('.ls-pick input').forEach(function(x){x.checked=v;});redo();});});
  redo();}
D.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('[data-pick]');if(b){e.preventDefault();pick();}});
/* /find's Grab links carry the pin, not the booking link (page weight). */
D.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a.ls-grab[data-ll]');if(!a)return;
  var p=a.getAttribute('data-ll').split(',');a.href=grab(p[0],p[1],a.getAttribute('data-n')||'');});

/* ---- a result row: share, LINE, Grab --------------------------------- */
function row(name,href,lat,lng){
  var u=abs(href),t=name+'\n'+u;
  return '<span class="ls-acts">'+
    '<button type="button" class="ls-a" data-ls-share="'+E(u)+'" data-ls-t="'+E(name)+'">'+I('i-share',16)+B('แชร์','Share')+'</button>'+
    '<a class="ls-a ls-line" href="'+E(lineHref(t))+'" target="_blank" rel="noopener">'+I('i-chat',16)+'LINE</a>'+
    (lat!=null&&lat!==''?'<a class="ls-a ls-grab" href="'+E(grab(lat,lng,name))+'" rel="nofollow noopener">'+I('i-ride',16)+'Grab</a>':'')+
    '</span>';}

var CSS='.ls-th+.ls-en::before{content:" · "}html.lang-th .ls-en,html.lang-en .ls-th{display:none}html.lang-en .ls-en::before{content:none}'+
'.ls-me{display:inline-flex;align-items:center;gap:.3rem;min-height:40px;padding:.3rem .7rem;border:2px solid currentColor;border-radius:999px;background:transparent;color:inherit;font:inherit;font-size:.9rem;cursor:pointer;position:relative}'+
'.ls-me.ls-on{background:#C2401C;border-color:#C2401C;color:#fff}.ls-me .ls-n{font-weight:700}'+
'.ls-me.ls-float{position:fixed;left:12px;bottom:calc(12px + env(safe-area-inset-bottom));z-index:56;'+
'background:#C2401C;border-color:#C2401C;color:#fff;font-weight:700;padding:.5rem .95rem;min-height:48px;box-shadow:0 3px 12px rgba(30,20,10,.32)}'+
'.ls-me.ls-float:hover{background:#a33314}'+
'@media (max-width:480px){.ls-me.ls-float .ls-lab{display:none}.ls-me.ls-float{padding:.6rem;border-radius:50%}}'+
'@media print{.ls-me.ls-float{display:none}}'+
'.ls-wrap{position:fixed;top:0;left:0;width:100vw;height:100%;z-index:2000}.ls-wrap[hidden]{display:none}.ls-back{position:absolute;inset:0;background:rgba(30,20,10,.45)}'+
'.ls-sheet{position:absolute;left:0;right:0;bottom:0;box-sizing:border-box;max-height:88vh;overflow:auto;background:#fffdf8;color:#2a1e16;border-radius:18px 18px 0 0;padding:16px 16px calc(20px + env(safe-area-inset-bottom));box-shadow:0 -10px 30px rgba(30,20,10,.25);font-size:1rem;line-height:1.45}'+
'@media (min-width:700px){.ls-sheet{left:50%;right:auto;bottom:auto;top:8vh;width:560px;margin-left:-280px;border-radius:18px;max-height:84vh}}'+
'.ls-sheet h2{margin:.1em 2.6em .6em 0;font-size:1.25rem}.ls-x{position:absolute;right:10px;top:10px;width:44px;height:44px;border-radius:50%;border:2px solid #2a1e16;background:#fffdf8;color:#2a1e16;cursor:pointer}'+
'.lsi{flex:none;vertical-align:middle;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}'+
'.ls-big{display:flex;align-items:center;gap:.8rem;width:100%;text-align:left;margin:0 0 .6rem;padding:.8rem 1rem;min-height:64px;border:2px solid #2a1e16;border-radius:14px;background:#fff;color:#2a1e16;font:inherit;cursor:pointer}'+
'.ls-big[hidden]{display:none}.ls-big b{display:block;font-size:1.1rem}.ls-big small{display:block;color:#5c4d38;font-size:.88rem}.ls-wait{opacity:.55;cursor:progress}'+
'.ls-send{display:flex;flex-wrap:wrap;gap:.5rem;margin:.7rem 0}'+
'.ls-b{display:inline-flex;align-items:center;gap:.4rem;min-height:48px;padding:.4rem 1rem;border:0;border-radius:999px;background:#2a1e16;color:#fff;font:inherit;font-weight:600;text-decoration:none;cursor:pointer}'+
'.ls-b.ls-line,.ls-a.ls-line{background:#06C755;color:#fff}'+
'.ls-b.ls-wa{background:#25D366;color:#073b1e}.ls-b.ls-mail{background:#fff;color:#2a1e16;border:2px solid #2a1e16}'+
'.ls-ok{margin:.4rem 0 0;font-weight:600}.ls-err{color:#9a2a10}.ls-note{font-size:.88rem;color:#5c4d38}.ls-stat{font-weight:600}'+
'.ls-stop{display:inline-flex;align-items:center;gap:.4rem;min-height:48px;padding:.4rem 1rem;border:2px solid #9a2a10;border-radius:999px;background:#fff;color:#9a2a10;font:inherit;font-weight:700;cursor:pointer}'+
'.ls-grp{margin:0 0 .55rem;border:1px solid #eadfcb;border-radius:12px;overflow:hidden;background:#fff}'+
'.ls-ghd{display:flex;gap:.6rem;align-items:center;padding:.55rem .7rem;background:#faf3e4;cursor:pointer;font-size:1.02rem;border-bottom:1px solid #eadfcb}'+
'.ls-ghd input{width:22px;height:22px;flex:none}.ls-grp .ls-pick{margin:0;padding:.1rem .7rem}'+
'.ls-grp .ls-pick li:last-child{border-bottom:0}'+
'.ls-pick{list-style:none;margin:0 0 .6rem;padding:0}.ls-pick li{border-bottom:1px solid #eadfcb}'+
'.ls-pick label{display:flex;gap:.6rem;align-items:flex-start;padding:.5rem 0;cursor:pointer;word-break:break-word}'+
'.ls-pick input{width:22px;height:22px;flex:none;margin-top:.1rem}.ls-all button{font:inherit;font-size:.9rem;min-height:36px;padding:.2rem .8rem;border:1px solid #2a1e16;border-radius:999px;background:#fff;cursor:pointer}'+
'.ls-ml{display:block;font-weight:600;font-size:.9rem}.ls-msg{display:block;width:100%;box-sizing:border-box;margin-top:.3rem;font:inherit;font-size:.95rem;padding:.5rem;border:2px solid #2a1e16;border-radius:10px;background:#fff;color:#2a1e16}'+
'.ls-acts{display:flex;flex-wrap:wrap;gap:.4rem;margin:.35rem 0 .1rem}'+
'.ls-a{display:inline-flex;align-items:center;gap:.3rem;min-height:36px;padding:.2rem .75rem;border:1px solid #2a1e16;border-radius:999px;background:#fff;color:#2a1e16;font:inherit;font-size:.85rem;text-decoration:none;cursor:pointer}'+
'.ls-a.ls-line{border-color:#06C755}.ls-a.ls-grab{background:#00B14F;border-color:#00B14F;color:#fff}'+
'.ls-pickbtn{display:inline-flex;align-items:center;gap:.4rem;margin:.3rem .4rem .3rem 0;min-height:44px;padding:.3rem .9rem;border:2px solid #2a1e16;border-radius:999px;background:#fff;color:#2a1e16;font:inherit;font-weight:600;cursor:pointer}'+
'html[data-contrast="1"] .ls-sheet,html.contrast .ls-sheet{background:#fff;color:#000}'+
'html[data-lang="th"] .ls-en,html[data-lang="en"] .ls-th{display:none}html[data-lang="en"] .ls-en::before{content:none}'+
'.ls-wrap{z-index:2147483100}'+
'html.ls-framed:not(.tool) .ls-me.ls-float,html.ls-framed:not(.tool) .ls-nudge{display:none}'+
'html.ls-framed .ls-me.ls-float{left:auto;right:14px;bottom:auto;top:calc(14px + env(safe-area-inset-top))}'+
'.ls-big.ls-hot{border-color:#C2401C;box-shadow:0 0 0 3px rgba(194,64,28,.16)}.ls-big.ls-hot .lsi{color:#C2401C}'+
'.ls-evb{display:inline-flex;align-items:center;gap:.35rem;min-height:40px;padding:.3rem .95rem;margin:0 .3rem .3rem 0;border:0;border-radius:999px;background:#C2401C;color:#fff;font:inherit;font-weight:700;cursor:pointer}'+
'.ls-evb:hover{background:#a33314}'+
'.ls-evi{display:inline-flex;vertical-align:middle;align-items:center;justify-content:center;width:36px;height:36px;padding:0;margin-left:.2rem;border:1.5px solid #C2401C;border-radius:50%;background:#fff;color:#C2401C;cursor:pointer}'+
'.ls-nudge{position:fixed;left:12px;bottom:calc(72px + env(safe-area-inset-bottom));z-index:57;display:flex;align-items:stretch;max-width:min(340px,calc(100vw - 24px));background:#fffdf8;color:#2a1e16;border:2px solid #C2401C;border-radius:14px;box-shadow:0 6px 18px rgba(30,20,10,.25);animation:lsn .35s ease-out;font-size:1rem;line-height:1.35}'+
'.ls-nudge::after{content:"";position:absolute;left:18px;bottom:-9px;width:14px;height:14px;background:#fffdf8;border-right:2px solid #C2401C;border-bottom:2px solid #C2401C;transform:rotate(45deg)}'+
'html.ls-framed .ls-nudge{left:auto;right:12px;bottom:auto;top:calc(72px + env(safe-area-inset-top))}html.ls-framed .ls-nudge::after{left:auto;right:18px;bottom:auto;top:-9px;transform:rotate(225deg)}'+
'.ls-nudge-go{flex:1;display:flex;gap:.55rem;align-items:center;text-align:left;min-height:48px;padding:.55rem .2rem .55rem .8rem;border:0;background:none;color:inherit;font:inherit;font-weight:600;cursor:pointer}.ls-nudge-go .lsi{color:#C2401C}'+
'.ls-nudge-x{flex:none;width:44px;border:0;background:none;color:#5c4d38;cursor:pointer}'+
'@keyframes lsn{from{transform:translateY(10px);opacity:0}}@media (prefers-reduced-motion:reduce){.ls-nudge{animation:none}}'+
'@media print{.ls-nudge,.ls-evb,.ls-evi{display:none}}';
function style(){if(D.getElementById('ls-css'))return;var s=D.createElement('style');s.id='ls-css';s.textContent=CSS;D.head.appendChild(s);}

window.MDSHARE={menu:menu,pick:pick,row:row,grab:grab,stop:function(){stop(false);},event:evShare,tell:tell,
  /* for sharepic.js */
  ui:{sheet:sheet,shut:shut,B:B,I:I,E:E,tell:tell,fresh:fresh,code:function(){return CODE||fresh();},tagged:tagged,copy:copy,
    canShare:canShare,nativeShare:nativeShare,pageTitle:pageTitle,pageUrl:pageUrl,subject:subject,busy:busy,app:APP,
    anim:function(stopFn){stopAnim();ANIMSTOP=stopFn;},about:function(k){SUBJ=k||'';},isOpen:open,menu:menu}};
window.MDSHAREROW=row;
function init(){style();mount();inbound();arrival();watchMoments();watchEvents();L=load();
  if(APP&&APP.liveState){try{var a=JSON.parse(APP.liveState()||'null');
    if(a&&a.id&&a.until>Date.now()){L={id:a.id,until:+a.until,app:1};okAt=+a.ok||0;tick=setInterval(paint,10000);paint();return;}
    if(L&&L.app){keep(null);L=null;}}catch(e){}}
  if(!L)return;
  /* A share ended elsewhere (stopped on another tab, or the hour ran out
     there) is ended here too. */
  fetch(API+'/'+L.id,{cache:'no-store'}).then(function(r){return r.json();})
    .then(function(d){if(d&&d.ended)stop(true);}).catch(function(){});
  var go=function(){run();if(navigator.geolocation)where(function(c){last=c;push(true);},function(){});};
  if(navigator.permissions&&navigator.permissions.query)
    navigator.permissions.query({name:'geolocation'}).then(function(s){if(s.state==='granted')go();else paint();},go);
  else go();}
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',init);else init();
})();
"""


PIC_JS = r"""/* share_layer.py PIC — a picture of the thing being sent, the event sheet with its
   drawing and countdown, and the welcome a shared event opens with. /sharepic.js,
   fetched by md.js / locshare.js the first time one is asked for. */
(function(){
if(window.MDPIC||!window.MDSHARE||!window.MDSHAREKIT)return;
var S=window.MDSHARE,U=S.ui,K=window.MDSHAREKIT,D=document,B=U.B,I=U.I,E=U.E,tell=U.tell;
var INK='#2a1e16',ANT='#C2401C',PAPER='#f6eedd',CARD='#fffdf8',MUTE='#5c4d38',GOLD='#E9B52F';
var FT='"MD Prompt","Prompt","Mali","Sarabun","Noto Sans Thai",system-ui,sans-serif',FB='"MD Sarabun","Sarabun","Noto Sans Thai",system-ui,sans-serif';
var SZ=1080;                                   /* the picture: square, 1080 × 1080 */
var ORIGIN=K.ours(location.hostname,'')||/^(localhost|127\.0\.0\.1|\[::1\])$|\.localhost$|\.test$/.test(location.hostname)?location.origin:'https://motdang.net';
var COARSE=window.matchMedia&&matchMedia('(pointer:coarse)').matches;
var REDUCED=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ---- fonts: the site's own files, so the picture reads the same everywhere ---- */
var FONTS=null,TH='U+0E00-0E7F,U+200C-200D,U+25CC',LA='U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2190-2193,U+2212,U+2215,U+FEFF,U+FFFD';
function fonts(){
  if(FONTS)return FONTS;
  if(!window.FontFace||!D.fonts)return (FONTS=Promise.resolve());
  var L=[['MD Prompt','600','prompt-600-thai',TH],['MD Prompt','600','prompt-600-latin',LA],
         ['MD Sarabun','400','sarabun-400-thai',TH],['MD Sarabun','400','sarabun-400-latin',LA],
         ['MD Sarabun','600','sarabun-600-thai',TH],['MD Sarabun','600','sarabun-600-latin',LA]];
  var all=Promise.all(L.map(function(f){try{var ff=new FontFace(f[0],'url(/fonts/'+f[2]+'.woff2)',{weight:f[1],unicodeRange:f[3]});
    return ff.load().then(function(x){D.fonts.add(x);},function(){});}catch(e){return null;}}));
  return (FONTS=Promise.race([all,new Promise(function(ok){setTimeout(ok,2500);})]));}

/* ---- drawing helpers ---- */
function rr(c,x,y,w,h,r){c.beginPath();c.moveTo(x+r,y);c.arcTo(x+w,y,x+w,y+h,r);c.arcTo(x+w,y+h,x,y+h,r);c.arcTo(x,y+h,x,y,r);c.arcTo(x,y,x+w,y,r);c.closePath();}
function cover(c,im,x,y,w,h){var iw=im.naturalWidth||im.width,ih=im.naturalHeight||im.height;if(!iw||!ih)return;
  var s=Math.max(w/iw,h/ih),sw=w/s,sh=h/s;c.drawImage(im,(iw-sw)/2,(ih-sh)/2,sw,sh,x,y,w,h);}
function words(t){t=String(t||'');
  if(window.Intl&&Intl.Segmenter){try{return Array.from(new Intl.Segmenter('th',{granularity:'word'}).segment(t),function(s){return s.segment;});}catch(e){}}
  return t.match(/[฀-๿]|[^\s฀-๿]+\s*|\s+/g)||[];}
function lines(c,t,maxW,max){var out=[],cur='';
  words(t).forEach(function(w){var n=cur+w;if(c.measureText(n.trim()).width>maxW&&cur.trim()){out.push(cur.trim());cur=w.replace(/^\s+/,'');}else cur=n;});
  if(cur.trim())out.push(cur.trim());
  if(out.length>max){out=out.slice(0,max);var l=out[max-1];while(l&&c.measureText(l+'…').width>maxW)l=l.slice(0,-1);out[max-1]=l.replace(/\s+$/,'')+'…';}
  return out;}
/* the largest size from hi down to lo at which t fits in max lines */
function fit(c,t,weight,hi,lo,maxW,max,face){for(var s=hi;s>=lo;s-=2){c.font=weight+' '+s+'px '+(face||FT);var L=lines(c,t,maxW,99);if(L.length<=max)return {s:s,L:L};}
  c.font=weight+' '+lo+'px '+(face||FT);return {s:lo,L:lines(c,t,maxW,max)};}
function grain(c,w,h){var r=7;function rnd(){r=(r*1664525+1013904223)>>>0;return r/4294967296;}
  c.fillStyle='rgba(90,60,30,.05)';for(var i=0;i<900;i++)c.fillRect(rnd()*w,rnd()*h,2,2);}
var LOGO=null;
function logo(){if(!LOGO)LOGO=img('/logo/motdang-mark-192.png').catch(function(){return null;});return LOGO;}
function img(src){return new Promise(function(ok,no){var i=new Image();i.crossOrigin='anonymous';i.decoding='async';
  var t=setTimeout(function(){no(new Error('slow'));},9000);
  i.onload=function(){clearTimeout(t);ok(i);};i.onerror=function(){clearTimeout(t);no(new Error('img'));};i.src=src;});}
function blank(cv){try{var x=cv.getContext('2d'),w=cv.width,h=cv.height,n=0;
  [[.5,.5],[.25,.25],[.75,.75],[.25,.75],[.75,.25]].forEach(function(p){var d=x.getImageData(Math.floor(w*p[0]),Math.floor(h*p[1]),1,1).data;if(d[3]>0)n++;});return n===0;}catch(e){return true;}}
function copyOf(cv){if(!cv||!cv.width||!cv.height)return null;var o=D.createElement('canvas');o.width=cv.width;o.height=cv.height;
  try{o.getContext('2d').drawImage(cv,0,0);}catch(e){return null;}return blank(o)?null:o;}
/* A MapLibre canvas keeps no picture between frames. Its own render event
   (via MDMAP) is the moment to copy it; failing that, a resize makes it draw
   and a frame queued after its own runs before the screen shows it. */
function grabGL(cv){return new Promise(function(ok){
  var done=false,fin=function(v){if(!done){done=true;ok(v);}};
  var box=cv.closest&&cv.closest('[data-mdmap]');
  if(box&&window.MDMAP&&MDMAP.ready){try{MDMAP.ready(box,function(m){m.once('render',function(){fin(copyOf(cv));});m.triggerRepaint();});}catch(e){}}
  setTimeout(function(){if(done)return;try{dispatchEvent(new Event('resize'));}catch(e){}
    requestAnimationFrame(function(){fin(copyOf(cv));});},700);
  setTimeout(function(){fin(null);},2200);});}
function visible(el){var r=el.getBoundingClientRect();return r.width>40&&r.height>40&&r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth;}
function area(el){var r=el.getBoundingClientRect();return Math.max(0,Math.min(r.bottom,innerHeight)-Math.max(r.top,0))*Math.max(0,Math.min(r.right,innerWidth)-Math.max(r.left,0));}
/* the drawn map at a pin, drawn out of sight, for a place whose own map is not open yet */
var DRAWN=[{u:'/sites/doodle-map/',b:[18.62,18.87,98.86,99.14]},{u:'/sites/doodle-chiang-rai/',b:[19.70,20.48,99.50,100.47]}];
function drawnAt(lat,lng,label){
  var d=DRAWN.filter(function(x){return lat>=x.b[0]&&lat<=x.b[1]&&lng>=x.b[2]&&lng<=x.b[3];})[0];if(!d)return Promise.resolve(null);
  return new Promise(function(ok){var f=D.createElement('iframe'),t0=Date.now(),done=false;
    f.setAttribute('aria-hidden','true');f.tabIndex=-1;
    f.style.cssText='position:fixed;left:0;top:0;width:984px;height:620px;border:0;opacity:0;pointer-events:none;z-index:-1';
    f.src=d.u+'?embed=1&pin='+lat.toFixed(5)+','+lng.toFixed(5)+'&pn='+encodeURIComponent(label||'');
    function fin(v){if(done)return;done=true;f.remove();ok(v);}
    var iv=setInterval(function(){var doc=null;try{doc=f.contentDocument;}catch(e){}
      var cv=doc&&doc.getElementById('map'),ld=doc&&doc.getElementById('loading');
      if(cv&&ld&&ld.hidden&&Date.now()-t0>1200){clearInterval(iv);setTimeout(function(){fin(copyOf(cv));},600);}
      else if(Date.now()-t0>9000){clearInterval(iv);fin(cv?copyOf(cv):null);}},250);
    D.body.appendChild(f);});}
/* what is on screen: the largest drawing, map or photo in view, looking inside the drawn maps' frames */
function onScreen(){
  var c=[];
  [].forEach.call(D.querySelectorAll('canvas,img,iframe'),function(el){if(!visible(el)||el.closest('.ls-wrap'))return;c.push(el);});
  c.sort(function(a,b){return area(b)-area(a);});
  function next(i){if(i>=c.length)return Promise.resolve(null);var el=c[i];
    if(el.tagName==='IFRAME'){var d=null;try{d=el.contentDocument;}catch(e){}
      var cv=d&&(d.getElementById('map')||d.querySelector('canvas'));return Promise.resolve(cv?copyOf(cv):null).then(function(v){return v||next(i+1);});}
    if(el.tagName==='CANVAS'){if(el.width<120||el.height<120)return next(i+1);
      var gl=/maplibregl-canvas|mapboxgl-canvas/.test(el.className)?grabGL(el):Promise.resolve(copyOf(el));
      return gl.then(function(v){return v||next(i+1);});}
    if(!el.complete||(el.naturalWidth||0)<200)return next(i+1);
    return img(el.currentSrc||el.src).then(function(v){return v;},function(){return next(i+1);});}
  return next(0);}

/* ---- what the picture is of ---- */
function textOf(el){if(!el)return '';var x=el.cloneNode(true);x.querySelectorAll('svg,script,button,.vh,.sr,.count,.mk').forEach(function(n){n.remove();});
  return (x.textContent||'').replace(/\s+/g,' ').trim();}
function pair(el){if(!el)return ['',''];var th=el.querySelector('.bi>.th,.th'),en=el.querySelector('.bi>.en,.en');
  if(th&&en){var e2=en.cloneNode(true);e2.querySelectorAll('.th').forEach(function(n){n.remove();});return [textOf(th),textOf(e2)];}
  return [textOf(el),''];}
function og(){var m=D.querySelector('meta[property="og:image"]');return m&&m.content||'';}
function place(){
  var main=D.querySelector('main')||D.body,h=pair(main.querySelector('h1')),addr='',hours='';
  main.querySelectorAll('dl dt').forEach(function(dt){var l=textOf(dt),dd=dt.nextElementSibling;if(!dd)return;
    if(!addr&&/ที่อยู่|Address/i.test(l))addr=pair(dd)[0]||textOf(dd);
    if(!hours&&/เวลา|Hours|Open/i.test(l))hours=textOf(dd);});
  var p=/\/(cm|cr)\//.exec(location.pathname),prov=p&&p[1]==='cr'?['เชียงราย','Chiang Rai']:['เชียงใหม่','Chiang Mai'];
  var photo=main.querySelector('img.photo');
  var pic=(photo?img(photo.currentSrc||photo.src):Promise.reject()).catch(function(){
    var f=main.querySelector('iframe.mdmap-doodle'),d=null;try{d=f&&f.contentDocument;}catch(e){}
    var dc=d&&d.getElementById('map');if(dc){var v=copyOf(dc);if(v)return v;}
    var gl=main.querySelector('[data-mdmap] canvas.maplibregl-canvas');return gl?grabGL(gl):null;})
    .then(function(v){if(v)return v;var m=main.querySelector('[data-mdmap][data-lat]');
      return m?drawnAt(+m.getAttribute('data-lat'),+m.getAttribute('data-lng'),h[1]||h[0]):null;})
    .then(function(v){return v||img(og()).catch(function(){return null;});});
  return pic.then(function(v){return {kind:'place',
    t1:h[0]||U.pageTitle(),t2:h[1],line:addr,line2:hours,foot:prov[0]+' · '+prov[1],pic:v,url:U.pageUrl().split('#')[0]};});}
function page(){
  var doodle=/\/sites\/doodle-/.test(location.pathname),h1=D.querySelector('h1'),h=h1?pair(h1):[U.pageTitle(),''];
  var desc=D.querySelector('meta[name="description"]');
  return onScreen().then(function(v){return v||img(og()).catch(function(){return null;});}).then(function(v){
    var map=/\/map(\.html)?$/.test(location.pathname);
    return {kind:doodle?'doodle':map?'map':'page',t1:h[0]||U.pageTitle(),t2:h[1],line:doodle||map?'':(desc&&desc.content||'').split(' · ')[0].slice(0,140),
      tag:doodle?['แผนที่วาด','Drawn map']:map?['แผนที่','Map']:null,pic:v,url:U.pageUrl()};});}

/* ---- the card ---- */
function foot(c,lg){c.fillStyle=INK;c.fillRect(56,986,968,3);
  if(lg)c.drawImage(lg,56,1004,56,56);
  c.font='600 36px '+FT;c.fillStyle=ANT;c.textBaseline='middle';c.fillText('มดแดง',lg?124:56,1034);
  var w=c.measureText('มดแดง').width;c.font='400 32px '+FB;c.fillStyle=INK;c.fillText('motdang.net',(lg?124:56)+w+16,1035);}
function box(c,x,y,w,h,draw){c.save();rr(c,x,y,w,h,26);c.fillStyle='#e9dcc0';c.fill();c.clip();draw();c.restore();
  c.save();rr(c,x,y,w,h,26);c.lineWidth=4;c.strokeStyle=INK;c.stroke();c.restore();}
function noPic(c,x,y,w,h){c.fillStyle='#efe2c6';c.fillRect(x,y,w,h);c.strokeStyle='rgba(194,64,28,.18)';c.lineWidth=3;
  for(var i=-h;i<w;i+=46){c.beginPath();c.moveTo(x+i,y+h);c.lineTo(x+i+h,y);c.stroke();}}
function drawCard(c,sub,lg,t){
  c.fillStyle=PAPER;c.fillRect(0,0,SZ,SZ);grain(c,SZ,SZ);
  box(c,48,48,984,620,function(){if(sub.pic)cover(c,sub.pic,48,48,984,620);else noPic(c,48,48,984,620);});
  if(sub.tag){c.font='600 30px '+FT;var tg=sub.tag[0]+' · '+sub.tag[1],tw=c.measureText(tg).width+40;
    c.fillStyle=CARD;rr(c,72,72,tw,52,26);c.fill();c.strokeStyle=INK;c.lineWidth=3;c.stroke();c.fillStyle=INK;c.textBaseline='middle';c.fillText(tg,92,99);}
  c.textBaseline='alphabetic';var y=726,f=fit(c,sub.t1,600,76,46,968,2);
  c.fillStyle=INK;f.L.forEach(function(l,i){c.fillText(l,56,y+f.s*0.9+i*f.s*1.2);});y+=f.s*1.2*f.L.length+8;
  if(sub.t2&&sub.t2!==sub.t1){c.font='600 40px '+FT;c.fillStyle=MUTE;var l2=lines(c,sub.t2,968,1);c.fillText(l2[0]||'',56,y+36);y+=56;}
  c.font='400 34px '+FB;c.fillStyle=MUTE;
  [sub.line,sub.line2].filter(Boolean).forEach(function(s){if(y>940)return;var L=lines(c,s,968,y>860?1:2);L.forEach(function(l){if(y>940)return;c.fillText(l,56,y+34);y+=44;});});
  foot(c,lg);
  if(sub.foot){c.font='400 30px '+FB;c.fillStyle=MUTE;c.textAlign='right';c.textBaseline='middle';c.fillText(sub.foot,1024,1035);c.textAlign='left';}}

/* ---- events: the drawing ---- */
var EVS=null;
function events(){if(!EVS)EVS=fetch('/front/events.json').then(function(r){return r.json();}).then(function(d){return d.events||[];}).catch(function(){EVS=null;return [];});return EVS;}
/* a weekly event is listed once a week under one key: the next one not yet over */
function evFrom(k){return events().then(function(L){var all=L.filter(function(x){return x.k===k;}),now=Date.now();
  var e=all.filter(function(x){return K.span(x).e>now;})[0]||all[all.length-1];if(e)return e;
  var d=D.querySelector('details.ev[data-k="'+k+'"]');
  return d?{k:k,t:textOf(d.querySelector('.tt'))||k}:null;});}
function script(src){return new Promise(function(ok,no){var s=D.createElement('script');s.src=src;s.onload=ok;s.onerror=no;D.head.appendChild(s);});}
function doodler(){
  if(window.MDDOODLER)return Promise.resolve(window.MDDOODLER);
  return (window.MDSKY?Promise.resolve():script('/front/skyline.js')).then(function(){return window.MDDOODLER?0:script('/front/doodler.js');})
    .then(function(){return window.MDDOODLER||null;},function(){return null;});}
/* the scene a set needs may live in its own file; it is in when 'mddoodler' fires */
function sceneReady(DD,set){if(!DD||!DD.files||!DD.files[set]||DD.sets().indexOf(set)>=0)return Promise.resolve();
  return new Promise(function(ok){var t=setTimeout(ok,3500);addEventListener('mddoodler',function f(){if(DD.sets().indexOf(set)>=0){clearTimeout(t);removeEventListener('mddoodler',f);ok();}});DD.need(set);});}
function art(c,w,h,e){var HUE={music:280,dance:330,wellness:160,sport:20,art:45,learn:200,food:30,market:0,social:250,faith:50,family:120,other:210},hue=HUE[e.c]||210;
  var g=c.createLinearGradient(0,0,w,h);g.addColorStop(0,'hsl('+hue+',55%,30%)');g.addColorStop(1,'hsl('+(hue+40)+',60%,12%)');c.fillStyle=g;c.fillRect(0,0,w,h);}
function evDraw(e){
  var sp=K.span(e),b=K.bkk(sp.s),night=!sp.all&&(b.h>=18||b.h<6);
  return doodler().then(function(DD){
    var set=DD?(e.dd==='latin-night'?'latin':DD.setOf(e)):'';
    return sceneReady(DD,set).then(function(){
      var lbl=sp.all?'':(b.h<10?'0':'')+b.h+':'+(b.mi<10?'0':'')+b.mi;
      return {set:set,draw:function(c,w,h,t){
        try{if(set==='latin'&&window.MDSKY&&MDSKY.latinNightScene)MDSKY.latinNightScene(c,w,h,t,null,null);
          else if(DD)DD.full(c,w,h,t,{set:set,variant:DD.variantOf?DD.variantOf(set,e):'',seed:DD.hash(e.k||e.t||''),night:night,label:lbl,
            title:(e.t||'')+' '+(e.v||'')+' '+(e.d||'').slice(0,160),now:sp.s,lat:e.la,lng:e.lo});
          else art(c,w,h,e);}catch(x){art(c,w,h,e);}}};});});}
var MON_TH=['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.'],MON_EN=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
var DAY_TH=['อาทิตย์','จันทร์','อังคาร','พุธ','พฤหัส','ศุกร์','เสาร์'],DAY_EN=['SUN','MON','TUE','WED','THU','FRI','SAT'];
function drawEvent(c,e,dr,lg,t,secs){
  var sp=K.span(e),b=K.bkk(sp.s);
  c.fillStyle=PAPER;c.fillRect(0,0,SZ,SZ);grain(c,SZ,SZ);
  box(c,48,48,984,560,function(){c.save();c.translate(48,48);if(dr)dr.draw(c,984,560,t);else noPic(c,0,0,984,560);c.restore();});
  /* the date, as a page torn from a wall calendar */
  var x=56,y=640,w=212,h=246;
  c.save();c.translate(x+w/2,y+h/2);c.rotate(-0.025);c.translate(-w/2,-h/2);
  c.fillStyle='rgba(42,30,22,.18)';rr(c,6,8,w,h,18);c.fill();
  c.fillStyle=CARD;rr(c,0,0,w,h,18);c.fill();c.save();rr(c,0,0,w,h,18);c.clip();c.fillStyle=ANT;c.fillRect(0,0,w,64);c.restore();
  c.lineWidth=3;c.strokeStyle=INK;rr(c,0,0,w,h,18);c.stroke();
  c.textAlign='center';c.textBaseline='middle';c.fillStyle='#fff';c.font='600 30px '+FT;c.fillText(DAY_TH[b.wd]+' · '+DAY_EN[b.wd],w/2,34);
  c.fillStyle=INK;c.font='600 104px '+FT;c.fillText(String(b.d),w/2,126);
  c.font='600 30px '+FT;c.fillText(MON_TH[b.mo-1]+' '+MON_EN[b.mo-1],w/2,186);
  c.fillStyle=ANT;c.font='600 32px '+FT;c.fillText(sp.all?'ทั้งวัน · all day':(b.h<10?'0':'')+b.h+':'+(b.mi<10?'0':'')+b.mi,w/2,224);
  c.restore();c.textAlign='left';c.textBaseline='alphabetic';
  /* the title, where, and how long until */
  var X=300,W=724,yy=646,f=fit(c,e.t||'',600,62,40,W,3);
  c.fillStyle=INK;f.L.forEach(function(l,i){c.fillText(l,X,yy+f.s*0.92+i*f.s*1.18);});yy+=f.s*1.18*f.L.length+6;
  if(e.v){c.font='400 34px '+FB;c.fillStyle=MUTE;lines(c,e.v,W,yy>820?1:2).forEach(function(l){c.fillText(l,X,yy+34);yy+=44;});}
  var ct=K.countText(e,Date.now(),secs),cw;c.font='600 34px '+FT;var ctx=/\d:\d\d:\d\d/.test(ct.th)?ct.th+' · to go':ct.th+' · '+ct.en;cw=Math.min(W,c.measureText(ctx).width+44);
  var cy=Math.max(yy+16,890);if(cy>916)cy=916;
  c.fillStyle=ANT;rr(c,X,cy,cw,56,28);c.fill();c.fillStyle='#fff';c.textBaseline='middle';c.fillText(lines(c,ctx,W-44,1)[0],X+22,cy+29);c.textBaseline='alphabetic';
  foot(c,lg);
  c.font='400 30px '+FB;c.fillStyle=MUTE;c.textAlign='right';c.textBaseline='middle';c.fillText(e.aen?(e.ath+' · '+e.aen):'เชียงใหม่ · Chiang Mai',1024,1035);c.textAlign='left';c.textBaseline='alphabetic';}

/* ---- the file ---- */
function blobOf(paint){var cv=D.createElement('canvas');cv.width=cv.height=SZ;var c=cv.getContext('2d');paint(c);
  return new Promise(function(ok){try{cv.toBlob(function(b){ok(b);},'image/jpeg',0.9);}catch(e){ok(null);}});}
function slug(s){return String(s||'motdang').toLowerCase().replace(/[^a-z0-9฀-๿]+/g,'-').replace(/^-+|-+$/g,'').slice(0,48)||'motdang';}
function canFiles(){try{return !!(navigator.canShare&&navigator.canShare({files:[new File(['x'],'x.jpg',{type:'image/jpeg'})]}));}catch(e){return false;}}
function save(blob,name,kind){var a=D.createElement('a'),u=URL.createObjectURL(blob);a.href=u;a.download=name;D.body.appendChild(a);a.click();a.remove();
  setTimeout(function(){URL.revokeObjectURL(u);},30000);tell('picture-saved',{d:kind});}
/* a preview canvas sized to its box, drawn in the card's own 1080 units */
function preview(cv){var w=Math.min(cv.parentNode.clientWidth||360,440),dpr=Math.min(window.devicePixelRatio||1,2),px=Math.round(w*dpr);
  cv.width=cv.height=px;cv.style.width=cv.style.height=w+'px';var c=cv.getContext('2d');c.setTransform(px/SZ,0,0,px/SZ,0,0);return c;}
function animate(fn){if(REDUCED){fn(4000);return function(){};}var on=true,t0=performance.now(),last=0;
  (function f(now){if(!on)return;if(now-last>40){last=now;fn(4000+now-t0);}requestAnimationFrame(f);})(t0);
  return function(){on=false;};}
var CSS='.lp-prev{display:flex;justify-content:center;margin:.2rem 0 .5rem}.lp-prev canvas{border-radius:14px;box-shadow:0 4px 16px rgba(30,20,10,.22);background:#f6eedd;max-width:100%}'+
  '.lp-wait{display:flex;align-items:center;justify-content:center;min-height:200px;color:#5c4d38}'+
  '.lp-cd{text-align:center;font-weight:700;font-size:1.15rem;color:#C2401C;margin:.1rem 0 .4rem;font-variant-numeric:tabular-nums}'+
  '.lp-row{justify-content:center}.ls-b.lp-main{background:#C2401C;font-size:1.05rem;min-height:52px;padding:.4rem 1.3rem}'+
  '.ls-b.lp-fb{background:#1877F2}.ls-b.lp-ms{background:#0A7CFF}.ls-b.lp-alt{background:#fff;color:#2a1e16;border:2px solid #2a1e16}'+
  '.lp-hello{text-align:center}.lp-kick{margin:0 2.6em .4rem;font-weight:700;color:#C2401C;letter-spacing:.02em}'+
  '.lp-hello canvas{width:100%;border-radius:14px;border:3px solid #2a1e16;display:block;background:#f6eedd}'+
  '.lp-hello h2{margin:.6rem 0 .2rem;font-size:1.45rem;line-height:1.25}.lp-when,.lp-where{margin:.15rem 0;color:#5c4d38}'+
  '.lp-clock{display:flex;justify-content:center;gap:.5rem;margin:.8rem 0 .4rem}.lp-clock div{min-width:64px;padding:.35rem .3rem;border:2px solid #2a1e16;border-radius:12px;background:#fff;box-shadow:2px 3px 0 rgba(42,30,22,.2)}'+
  '.lp-clock b{display:block;font-size:1.9rem;line-height:1.1;font-variant-numeric:tabular-nums;color:#C2401C}.lp-clock small{display:block;font-size:.8rem;color:#5c4d38}'+
  '.lp-past{font-weight:700;margin:.8rem 0}'+
  '.ls-sheet .lp-where a,.ls-sheet .lp-when a{color:#9a2a10}'+
  '@keyframes lpin{from{transform:translateY(24px) scale(.96);opacity:0}}.lp-hello{animation:lpin .5s cubic-bezier(.2,.8,.2,1)}'+
  '@media (prefers-reduced-motion:reduce){.lp-hello{animation:none}}';
function style(){if(D.getElementById('lp-css'))return;var s=D.createElement('style');s.id='lp-css';s.textContent=CSS;D.head.appendChild(s);}

/* the buttons under a picture. url: the link that goes with it; text: its words */
function buttons(o){var files=canFiles();
  return '<div class="ls-send lp-row">'+
    (files?'<button type="button" class="ls-b lp-main" data-lp-send>'+I('i-share')+B(o.ev?'ส่งพร้อมภาพ':'ส่งภาพ',o.ev?'Send with the picture':'Send the picture')+'</button>':'')+
    '<button type="button" class="ls-b'+(files?' lp-alt':' lp-main')+'" data-lp-save>'+I('i-download')+B('เก็บภาพ','Save the picture')+'</button></div>'+
    '<div class="ls-send lp-row">'+
    '<a class="ls-b ls-line" target="_blank" rel="noopener" href="'+E(K.lineHref(o.text))+'">'+I('i-chat')+'LINE</a>'+
    '<a class="ls-b ls-wa" target="_blank" rel="noopener" href="'+E(K.waHref(o.text))+'">'+I('i-chat')+'WhatsApp</a>'+
    '<a class="ls-b lp-fb" target="_blank" rel="noopener" href="'+E(K.fbHref(o.url))+'">Facebook</a>'+
    (COARSE?'<a class="ls-b lp-ms" href="'+E(K.msgrHref(o.url))+'">Messenger</a>':'')+
    '<button type="button" class="ls-b ls-mail" data-ls-copy>'+I('i-link')+B('คัดลอกลิงก์','Copy link')+'</button></div>';}
function wire(o){var body=D.querySelector('.ls-wrap .ls-body');if(!body)return;
  var send=body.querySelector('.ls-send');if(send)send.setAttribute('data-ls-text',o.text);
  body.querySelectorAll('[data-ls-copy]').forEach(function(b){b.closest('.ls-send').setAttribute('data-ls-text',o.text);});
  var sb=body.querySelector('[data-lp-send]');
  if(sb)sb.addEventListener('click',function(){if(!o.file){o.later=1;U.busy(sb,true);return;}
    var t=U.tagged(o.text,'native');tell('channel',{d:'native'});
    U.nativeShare({files:[o.file],text:t},o.kind);});
  var sv=body.querySelector('[data-lp-save]');
  if(sv)sv.addEventListener('click',function(){if(o.blob)save(o.blob,o.name,o.kind);else{o.saveLater=1;U.busy(sv,true);}});}
function made(o,blob){if(!blob)return;o.blob=blob;tell('picture',{d:o.kind});
  try{o.file=new File([blob],o.name,{type:'image/jpeg'});}catch(e){}
  var body=D.querySelector('.ls-wrap .ls-body');if(!body)return;
  var sb=body.querySelector('[data-lp-send]'),sv=body.querySelector('[data-lp-save]');
  if(sb){U.busy(sb,false);if(o.later){o.later=0;}}
  if(sv){U.busy(sv,false);if(o.saveLater){o.saveLater=0;save(blob,o.name,o.kind);}}}

/* ---- a picture of the page ---- */
function picture(){style();U.code();
  U.sheet('<h2>'+B('ส่งเป็นภาพ','Send as a picture')+'</h2><div class="lp-prev"><p class="lp-wait">'+B('กำลังวาด…','Drawing…')+'</p></div>','picture');
  var isPlace=/\/(cm|cr)\/p\/[a-z0-9-]+\.html$/.test(location.pathname);
  Promise.all([fonts(),logo(),isPlace?place():page()]).then(function(r){
    if(!U.isOpen('picture'))return;
    var lg=r[1],sub=r[2],body=D.querySelector('.ls-wrap .ls-body');
    var o={kind:sub.kind,url:sub.url,text:[sub.t1,sub.url].join('\n'),name:'motdang-'+slug(sub.t2||sub.t1)+'.jpg'};
    body.querySelector('.lp-prev').innerHTML='<canvas class="lp-cv" role="img" aria-label="'+E(sub.t1)+'"></canvas>';
    var c=preview(body.querySelector('.lp-cv'));drawCard(c,sub,lg,0);
    body.insertAdjacentHTML('beforeend',buttons(o));wire(o);
    blobOf(function(x){drawCard(x,sub,lg,0);}).then(function(b){made(o,b);});});}

/* ---- an event ---- */
function evLink(e){return e.link||(ORIGIN+'/#ev='+e.k);}
function eventSheet(e,src){style();
  if(!e){U.sheet('<h2>'+B('ส่งงานนี้','Send this event')+'</h2><p>'+B('หางานนี้ไม่เจอในปฏิทินแล้ว','This event is no longer on the calendar')+'</p>','event');return;}
  var url=evLink(e),has=!!(e.s&&isFinite(K.at(e.s)));
  if(e.k)U.about('ev:'+e.k);
  var o={kind:'event',ev:1,url:url,text:has?K.evText(e,url):e.t+'\n'+url,name:'motdang-'+slug(e.k||e.t)+'.jpg'};
  U.sheet('<h2>'+B('ส่งงานนี้','Send this event')+'</h2><div class="lp-prev"><canvas class="lp-cv" role="img" aria-label="'+E(e.t)+'"></canvas></div>'+
    (has?'<p class="lp-cd" aria-live="off"></p>':'')+buttons(o)+
    (has?'<div class="ls-send lp-row"><a class="ls-b lp-alt" data-lp-ics download="'+E((e.k||'event')+'.ics')+'" href="'+E('data:text/calendar;charset=utf-8,'+encodeURIComponent(K.ics(e,{url:url})))+'">'+I('i-cal')+B('ลงปฏิทิน','Add to calendar')+'</a>'+
      '<a class="ls-b lp-alt" data-lp-gcal target="_blank" rel="noopener" href="'+E(K.gcal(e,{url:url}))+'">'+I('i-cal')+'Google Calendar</a></div>':''),'event');
  wire(o);calWire();
  var body=D.querySelector('.ls-wrap .ls-body'),cv=body.querySelector('.lp-cv'),cd=body.querySelector('.lp-cd'),c=preview(cv);
  c.fillStyle=PAPER;c.fillRect(0,0,SZ,SZ);
  Promise.all([fonts(),logo(),evDraw(e)]).then(function(r){
    if(!U.isOpen('event'))return;var lg=r[1],dr=r[2],sec=-1;
    U.anim(animate(function(t){drawEvent(c,e,dr,lg,t,true);
      var s=Math.floor(Date.now()/1000);if(cd&&s!==sec){sec=s;var x=K.countText(e,Date.now(),true);cd.innerHTML=B(x.th,x.en);}}));
    blobOf(function(x){drawEvent(x,e,dr,lg,4000,false);}).then(function(b){made(o,b);});});}
function calWire(){var body=D.querySelector('.ls-wrap .ls-body');if(!body)return;
  var a=body.querySelector('[data-lp-ics]'),g=body.querySelector('[data-lp-gcal]');
  if(a)a.addEventListener('click',function(){tell('calendar',{d:'ics'});});
  if(g)g.addEventListener('click',function(){tell('calendar',{d:'google'});});}
function event(k,src){U.sheet('<h2>'+B('ส่งงานนี้','Send this event')+'</h2><p class="lp-wait">'+B('กำลังวาด…','Drawing…')+'</p>','event');
  evFrom(k).then(function(e){if(U.isOpen('event'))eventSheet(e,src);});}
/* an /events.html card: read off the card and its calendar file, then matched to the calendar by name and day */
function b64(s){try{var bin=atob(s),u=new Uint8Array(bin.length);for(var i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);return new TextDecoder().decode(u);}catch(e){return '';}}
function icsField(t,name){var v=t.indexOf('BEGIN:VEVENT');if(v>=0)t=t.slice(v);var m=new RegExp('^'+name+'[^:\\n]*:(.*)$','m').exec(t.replace(/\r?\n[ \t]/g,''));return m?m[1].trim().replace(/\\([,;\\])/g,'$1').replace(/\\n/gi,'\n'):'';}
function fromStamp(v){var m=/^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2}))?/.exec(v||'');return m?m[1]+'-'+m[2]+'-'+m[3]+(m[4]?' '+m[4]+':'+m[5]+':00':' 00:00:00'):'';}
function eventCard(card){
  if(!card)return;var a=card.querySelector('a.evcal'),t=textOf(card.querySelector('h3')),h=a&&a.getAttribute('href')||'',ics='';
  var m=/^data:text\/calendar;base64,(.*)$/.exec(h);ics=m?b64(m[1]):/^data:text\/calendar/.test(h)?decodeURIComponent(h.split(',').slice(1).join(',')):'';
  var s=fromStamp(icsField(ics,'DTSTART')),en=fromStamp(icsField(ics,'DTEND')),v=icsField(ics,'LOCATION')||textOf(card.querySelector('.evvenue'));
  var e0={t:t||icsField(ics,'SUMMARY'),s:s,e:en&&/ 00:00:00$/.test(en)?null:en,ad:/VALUE=DATE/.test(ics),v:v,d:textOf(card.querySelector('.evdesc')),link:U.pageUrl().split('#')[0]};
  event_(e0);}
function event_(e0){U.sheet('<h2>'+B('ส่งงานนี้','Send this event')+'</h2><p class="lp-wait">'+B('กำลังวาด…','Drawing…')+'</p>','event');
  events().then(function(L){var day=(e0.s||'').slice(0,10),n=(e0.t||'').toLowerCase().trim();
    var hit=L.filter(function(x){return (x.t||'').toLowerCase().trim()===n&&(!day||String(x.s).slice(0,10)===day);})[0]||
            L.filter(function(x){return (x.t||'').toLowerCase().trim()===n;})[0];
    var e=hit?Object.assign({},hit,e0.s?{s:e0.s,e:e0.e,ad:e0.ad}:{}):e0;
    if(U.isOpen('event'))eventSheet(e,'card');});}

/* ---- the welcome: a shared event opens with its drawing moving, its clock running ---- */
function arrive(k){style();
  evFrom(k).then(function(e){if(!e||!e.s)return;
    var url=evLink(e),w=K.when(e),sp=K.span(e);
    tell('welcome',{d:K.until(e).state,k:'ev:'+k});
    var dir=isFinite(e.la)&&e.la!=null?'https://www.google.com/maps/dir/?api=1&destination='+(+e.la).toFixed(6)+','+(+e.lo).toFixed(6):'';
    U.sheet('<div class="lp-hello"><p class="lp-kick">'+I('i-sparkle',18)+' '+B('มีคนส่งงานนี้มาให้','Someone sent you this')+'</p>'+
      '<canvas class="lp-hc" aria-hidden="true"></canvas><h2>'+E(e.t)+'</h2>'+
      '<p class="lp-when">'+B(E(w.th),E(w.en))+'</p>'+(e.v?'<p class="lp-where">'+(e.vu?'<a href="/'+E(e.vu)+'">'+E(e.v)+'</a>':E(e.v))+(e.cost?' · '+E(e.cost):'')+'</p>':'')+
      '<div class="lp-clock" aria-live="off"></div>'+
      '<div class="ls-send lp-row"><a class="ls-b lp-main" data-lp-ics download="'+E(k+'.ics')+'" href="'+E('data:text/calendar;charset=utf-8,'+encodeURIComponent(K.ics(e,{url:url})))+'">'+I('i-cal')+B('ลงปฏิทิน','Add to calendar')+'</a>'+
      '<a class="ls-b lp-alt" data-lp-gcal target="_blank" rel="noopener" href="'+E(K.gcal(e,{url:url}))+'">Google Calendar</a>'+
      (dir?'<a class="ls-b lp-alt" href="'+E(dir)+'" rel="noopener">'+I('i-route')+B('ไปยังไง','Directions')+'</a>':'')+'</div>'+
      '<div class="ls-send lp-row"><button type="button" class="ls-b lp-alt" data-lp-on>'+I('i-share')+B('ส่งต่อ','Send it on')+'</button>'+
      '<button type="button" class="ls-b lp-alt" data-ls-x>'+B('ดูในปฏิทิน','See the calendar')+'</button></div></div>','welcome');
    calWire();
    var body=D.querySelector('.ls-wrap .ls-body'),cv=body.querySelector('.lp-hc'),clock=body.querySelector('.lp-clock');
    body.querySelector('[data-lp-on]').addEventListener('click',function(){U.fresh();tell('option',{d:'event',k:'ev:'+k});eventSheet(e,'welcome');});
    var wpx=cv.clientWidth||340,dpr=Math.min(window.devicePixelRatio||1,2),hpx=Math.round(wpx*0.62);
    cv.width=Math.round(wpx*dpr);cv.height=Math.round(hpx*dpr);cv.style.height=hpx+'px';var c=cv.getContext('2d');c.setTransform(dpr,0,0,dpr,0,0);
    var sec=-1;
    function tick(){var s=Math.floor(Date.now()/1000);if(s===sec)return;sec=s;var u=K.until(e);
      if(u.state==='past'){clock.outerHTML='<p class="lp-past">'+B('งานนี้จบไปแล้ว ดูงานอื่นในปฏิทินได้','This one has passed; the calendar has others')+'</p>';clock=null;return;}
      if(u.state==='on'){clock.innerHTML='<div><b>'+B('ตอนนี้','Now')+'</b><small>'+B('กำลังจัดอยู่','on now')+'</small></div>';return;}
      function cell(n,th,en){return '<div><b>'+n+'</b><small>'+B(th,en)+'</small></div>';}
      clock.innerHTML=(u.d?cell(u.d,'วัน','days'):'')+cell(u.h,'ชม.','hours')+cell((u.m<10?'0':'')+u.m,'นาที','min')+cell((u.s<10?'0':'')+u.s,'วินาที','sec');}
    tick();
    /* paper confetti in ant red and marigold, once, as it opens */
    var bits=[],r=11;function rnd(){r=(r*1664525+1013904223)>>>0;return r/4294967296;}
    for(var i=0;i<(REDUCED?0:46);i++)bits.push({x:rnd()*wpx,y:-rnd()*hpx*0.8,v:40+rnd()*70,a:rnd()*6,s:5+rnd()*7,c:[ANT,GOLD,'#2f6fbf','#4fae8c'][i%4]});
    Promise.all([evDraw(e),fonts()]).then(function(rr_){var dr=rr_[0];
      U.anim(animate(function(t){c.clearRect(0,0,wpx,hpx);dr.draw(c,wpx,hpx,t);if(clock)tick();
        var age=(t-4000)/1000;if(age<2.4)bits.forEach(function(b){var y=b.y+b.v*age*1.6+40*age*age;if(y>hpx+20)return;
          c.save();c.translate(b.x+Math.sin(age*3+b.a)*14,y);c.rotate(b.a+age*4);c.fillStyle=b.c;c.globalAlpha=Math.max(0,1-age/2.4);c.fillRect(-b.s/2,-b.s/3,b.s,b.s*0.66);c.restore();});}));});});}

style();
window.MDPIC={picture:picture,event:event,eventCard:eventCard,eventOf:event_,arrive:arrive,
  /* for tests and stills */ drawEvent:drawEvent,drawCard:drawCard,size:SZ};
})();
"""



VIEW_JS = r"""/* /live.html — a shared position, drawn and followed (share_layer.py). */
(function(){
var q=new URLSearchParams(location.search),P=q.get('p'),ID=q.get('l'),D=document;
var box=D.getElementById('livemap'),st=D.getElementById('livestat'),acts=D.getElementById('liveacts');
var map=null,cur=null,first=true,timer=null;
function pad(n){return (n<10?'0':'')+n;}
function hm(t){var d=new Date(t);return pad(d.getHours())+':'+pad(d.getMinutes());}
function B(th,en){return '<span class="ls-th" lang="th">'+th+'</span><span class="ls-en" lang="en">'+en+'</span>';}
function say(h){st.innerHTML=h;}
function ring(lat,lng,r){var o=[],k=Math.cos(lat*Math.PI/180);
  for(var i=0;i<=48;i++){var a=i/48*2*Math.PI;o.push([lng+r*Math.sin(a)/(111320*k),lat+r*Math.cos(a)/111320]);}
  return {type:'Feature',geometry:{type:'Polygon',coordinates:[o]},properties:{}};}
function paint(){
  if(!map||!cur)return;
  var pt={type:'Feature',geometry:{type:'Point',coordinates:[cur.lng,cur.lat]},properties:{}};
  var acc=Math.max(5,Math.min(cur.acc||0,3000));
  if(map.getSource('ls-pt')){map.getSource('ls-pt').setData(pt);map.getSource('ls-acc').setData(ring(cur.lat,cur.lng,acc));}
  else{map.addSource('ls-acc',{type:'geojson',data:ring(cur.lat,cur.lng,acc)});
    map.addSource('ls-pt',{type:'geojson',data:pt});
    map.addLayer({id:'ls-acc',type:'fill',source:'ls-acc',paint:{'fill-color':'#C2401C','fill-opacity':0.14}});
    map.addLayer({id:'ls-pt',type:'circle',source:'ls-pt',paint:{'circle-radius':10,'circle-color':'#C2401C','circle-stroke-width':4,'circle-stroke-color':'#fff'}});}
  if(first){first=false;map.jumpTo({center:[cur.lng,cur.lat],zoom:acc>400?14:16.5});}
  else if(!map.getBounds().contains([cur.lng,cur.lat]))map.easeTo({center:[cur.lng,cur.lat]});}
function links(){
  if(!cur)return;var ll=cur.lat.toFixed(6)+','+cur.lng.toFixed(6);
  var dp='grab://open?screenType=BOOKING&dropOffLatitude='+cur.lat.toFixed(6)+'&dropOffLongitude='+cur.lng.toFixed(6)+'&dropOffAddress=';
  var g='https://grab.onelink.me/2695613898?af_dp='+encodeURIComponent(dp)+'&af_web_dp='+encodeURIComponent('https://www.grab.com/th/transport/');
  acts.innerHTML='<a class="ls-b" href="https://www.google.com/maps/dir/?api=1&destination='+ll+'" rel="noopener">'+B('นำทาง','Directions')+'</a>'+
    '<a class="ls-b ls-grabb" href="'+g+'" rel="nofollow noopener">'+B('เรียก Grab ไปหา','Ride there · Grab')+'</a>'+
    '<a class="ls-b ls-alt" href="https://www.google.com/maps/search/?api=1&query='+ll+'" rel="noopener">Google Maps</a>'+
    '<a class="ls-b ls-alt" href="https://maps.apple.com/?ll='+ll+'&q='+ll+'" rel="noopener">Apple Maps</a>'+
    '<a class="ls-b ls-alt" href="geo:'+ll+'?q='+ll+'">'+I('i-ride')+B('เปิดแอปแผนที่ / เรียกจ้าง','Geo URI / Apps')+'</a>'+
    '<button type="button" class="ls-b copylink" data-url="'+ll+'" data-done="'+E(B("คัดลอกแล้ว","Copied"))+'">'+I('i-link')+B('คัดลอกพิกัด','Copy coordinates')+'</button>'+
    '<a class="ls-b ls-alt" href="map.html?go='+ll+'">'+B('แผนที่มดแดง','Mot Dang map')+'</a>';}
function set(lat,lng,acc){cur={lat:lat,lng:lng,acc:acc};links();paint();}
if(window.MDMAP&&box)MDMAP.ready(box,function(m){map=m;paint();});
else addEventListener('load',function(){if(window.MDMAP&&box)MDMAP.ready(box,function(m){map=m;paint();});});
if(P){var p=P.split(',').map(Number);
  if(p.length>=2&&isFinite(p[0])&&isFinite(p[1])){
    box.setAttribute('data-lat',p[0].toFixed(5));box.setAttribute('data-lng',p[1].toFixed(5));
    set(p[0],p[1],p[2]||0);
    var a=p[2]?Math.round(p[2]):0,t=p[3]?p[3]*1000:0,m=t?Math.max(0,Math.round((Date.now()-t)/60000)):0;
    say(B('ตำแหน่งที่ส่งมา'+(t?' เมื่อ '+hm(t)+' ('+(m?m+' นาทีก่อน':'เมื่อสักครู่')+')':'')+(a?' ±'+a+' ม.':''),
          'Position sent'+(t?' at '+hm(t)+' ('+(m?m+' min ago':'just now')+')':'')+(a?', ±'+a+' m':'')));}
  else say(B('ลิงก์นี้ไม่มีตำแหน่ง','This link carries no position'));}
else if(/^[a-z2-7]{16}$/.test(ID||'')){
  say(B('กำลังโหลดตำแหน่ง…','Loading the position…'));
  var poll=function(){fetch('/api/live/'+ID,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
    if(d.ended){clearInterval(timer);
      say(B('การแชร์นี้จบแล้ว','This share has ended')+(cur?' · '+B('หมุดคือตำแหน่งล่าสุดที่ส่งมา','the pin is the last position sent'):''));return;}
    if(d.lat==null){say(B('รอตำแหน่งแรก…','Waiting for the first position…'));return;}
    set(d.lat,d.lng,d.acc);
    var m=Math.max(0,Math.round((d.now-d.at)/60000)),a=d.acc?Math.round(d.acc):0;
    say('<b>'+B('ตำแหน่งสด','Live location')+'</b> · '+
      B('อัปเดต'+(m?' '+m+' นาทีก่อน':'เมื่อสักครู่')+(a?' ±'+a+' ม.':'')+' · แชร์ถึง '+hm(d.until),
        'updated '+(m?m+' min ago':'just now')+(a?', ±'+a+' m':'')+' · shared until '+hm(d.until)));
  }).catch(function(){});};
  poll();timer=setInterval(poll,10000);
  D.addEventListener('visibilitychange',function(){if(D.visibilityState==='visible')poll();});}
else say(B('ลิงก์นี้ไม่มีตำแหน่ง','This link carries no position'));
})();
"""


CSS = """
.livebox{margin:.4rem 0 1rem}
#livemap{height:62vh;min-height:320px;border:2px solid var(--ink,#2a1e16);border-radius:14px;overflow:hidden}
#livestat{font-size:1.05rem;margin:.3rem 0 .6rem;min-height:1.5em}
#liveacts{display:flex;flex-wrap:wrap;gap:.5rem;margin:.6rem 0}
#liveacts .ls-b{display:inline-flex;align-items:center;min-height:48px;padding:.4rem 1rem;border-radius:999px;
  background:#2a1e16;color:#fff;font-weight:600;text-decoration:none}
#liveacts .ls-grabb{background:#00B14F}
#liveacts .ls-alt{background:#fff;color:#2a1e16;border:2px solid #2a1e16}
"""


def pic_version():
    import hashlib
    return hashlib.sha1(PIC_JS.encode("utf-8")).hexdigest()[:8]


def md_js():
    """The kit and the sheet: the end of md.js, and docs/locshare.js."""
    return KIT_JS + "\n" + JS.replace("__PICV__", pic_version())


def pic_js():
    """docs/sharepic.js — fetched the first time a picture or an event is sent."""
    return PIC_JS


_SCRIPT = '<script src="/locshare.js" defer></script>'


def inject(docs, only=None):
    """Put /locshare.js on each page under docs/ that has neither it nor md.js:
    the minisites under /sites/, /loop, /muay-thai, /roads, /markets, /chiang-rai,
    the listings pages. The place pages under cm/p and cr/p come from page() and
    carry md.js; the ones that do not are moved-address stubs. Returns pages written."""
    import pathlib
    import re
    docs = pathlib.Path(docs)
    has = re.compile(r"""(?:["'/])(?:md|locshare)\.js""")
    stub = re.compile(r"""http-equiv=["']?refresh""", re.I)
    files = only if only is not None else (
        f for f in docs.rglob("*.html")
        if f.relative_to(docs).parts[:2] not in (("cm", "p"), ("cr", "p"))
        and not f.name.startswith("google"))
    n = 0
    for f in files:
        f = pathlib.Path(f)
        try:
            t = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if has.search(t) or stub.search(t[:4000]):
            continue
        i = t.rfind("</body>")
        if i < 0:
            continue
        f.write_text(t[:i] + _SCRIPT + t[i:], encoding="utf-8")
        n += 1
    return n


def manifest():
    """docs/app.webmanifest: motdang installs as an app from the browser, and
    once installed it takes shares from other apps onto the map."""
    import json
    return json.dumps({
        "name": "มดแดง Mot Dang", "short_name": "มดแดง",
        "description": "เชียงใหม่ เชียงราย · Chiang Mai and Chiang Rai",
        "lang": "th", "dir": "ltr", "id": "/", "start_url": "/", "scope": "/",
        "display": "standalone", "background_color": "#fffdf8", "theme_color": "#C2401C",
        "icons": [{"src": "/logo/motdang-mark-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/logo/motdang-mark-512.png", "sizes": "512x512", "type": "image/png"}],
        "share_target": {"action": "/map.html", "method": "GET",
                         "params": {"title": "sn", "text": "st", "url": "su"}},
        "shortcuts": [{"name": "แผนที่ · Map", "url": "/map.html"},
                      {"name": "ค้นหา · Search", "url": "/find"}],
    }, ensure_ascii=False, indent=1)


def live_page(page, map_shell, bi, bi_text, esc):
    """/live.html — where someone's shared position opens."""
    body = (f'<h1>{bi("ตำแหน่งที่แชร์", "A shared location")}</h1>'
            f'<div class="livebox"><p id="livestat" aria-live="polite"></p>'
            + map_shell.mount("livemap", "", prov="cm", zoom=14,
                              label=esc(bi_text("ตำแหน่งที่แชร์", "Shared location")))
            + '<div id="liveacts"></div></div>'
            f'<p class="tinynote">{bi("ส่งตำแหน่งของคุณเองได้จากปุ่ม ส่ง ที่มุมจอทุกหน้า", "Send your own from the Send button in the corner of any page.")}</p>'
            f'<style>{CSS}</style><script>{VIEW_JS}</script>')
    return page(bi_text("ตำแหน่งที่แชร์", "A shared location"), body, 0, path="live.html",
                robots="noindex,nofollow", desc=bi_text("ตำแหน่งที่มีคนส่งมาให้ บนแผนที่มดแดง",
                                                         "A location someone sent you, on the Mot Dang map."))
