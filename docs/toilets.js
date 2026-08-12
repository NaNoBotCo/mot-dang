/* ห้องน้ำใกล้ฉัน. Everything is baked; the only thing this asks the
   network for is the second, larger file, and only if the reader taps for it.
   The location never leaves the browser — there is nowhere on this site to
   send it.

   LOCATION IS NEVER A GATE. The page opens on a working list, sorted from a
   named landmark, before anything has been asked of anybody. The browser's
   own permission dialog is the last step of a path the reader chose, never
   the first thing that happens to them — a stranger's site throwing up a
   location prompt on contact reads as a risk, and the reader who backs out
   of it never sees the page at all. Our own dialog goes first, says in one
   sentence where the coordinate goes (nowhere), and takes no for an answer
   permanently. */
(function(){
var D=null,MORE=null,here=null,filter='all',showCust=false;
var elBtn=document.getElementById('loogo'),elState=document.getElementById('loostate'),
    elList=document.getElementById('loolist'),elFilters=document.getElementById('loofilters'),
    elMore=document.getElementById('loomore'),elNear=document.getElementById('loonear'),
    elMap=document.getElementById('loomap'),elGate=document.getElementById('loogate'),
    elFind=document.getElementById('loofind'),elOrigin=document.getElementById('looorigin');
if(!elList)return;
var LANG=document.documentElement;

/* Where the page opens when nobody has told it anything. Two real landmarks
   people give directions from, not a bounding-box centroid in a rice field. */
var DEFAULTS={
  cm:{lat:18.7876,lng:98.9931,th:'ประตูท่าแพ',en:'Tha Phae Gate',src:'default',prov:'cm'},
  cr:{lat:19.9094,lng:99.8325,th:'หอนาฬิกาเชียงราย',en:'Clock Tower',src:'default',prov:'cr'}
};
/* Set once the reader has said no — by tapping "not now", or because the
   browser already knows the answer is denied. Once true it never goes back
   to false in this page's life, and every door to the prompt is removed
   rather than merely disabled. Re-asking is how a site teaches people to
   refuse it on sight. */
var GPS_OFF=false;
var lastTf=null;   // the projection drawMap last used, so taps can be inverted

function store(k,v){try{v===null?localStorage.removeItem(k):
  localStorage.setItem(k,JSON.stringify(v));}catch(e){}}
function recall(k){try{var v=localStorage.getItem(k);return v?JSON.parse(v):null;}
  catch(e){return null;}}

function bi(th,en){return '<span class="bi"><span class="th">'+esc(th)+'</span>'+
  '<span class="en"><span class="th"> · </span>'+esc(en)+'</span></span>';}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}

function hav(a,b,c,d){var R=6371000,p1=a*Math.PI/180,p2=c*Math.PI/180,
  dp=(c-a)*Math.PI/180,dl=(d-b)*Math.PI/180,
  h=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)*Math.sin(dl/2);
  return 2*R*Math.asin(Math.sqrt(h));}

/* Opening hours. Only the two shapes that actually appear often enough to be
   worth reading are parsed; anything else falls back to the class window and
   is labelled as a habit, not as a fact. We never print a flat "closed" from a
   habit — being wrong about that sends somebody walking the wrong way. */
function stated(h){
  if(!h)return null;
  var s=h.replace(/\s+/g,'');
  if(s==='24/7'||s==='Mo-Su00:00-24:00'||s==='Mo-Su,PH00:00-00:00'||s==='Mo-Su00:00-00:00')return[0,24];
  var m=s.match(/^(?:Mo-Su|Mo-Sa|Daily)?,?(?:PH)?(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$/);
  if(m)return[+m[1]+ +m[2]/60,+m[3]+ +m[4]/60];
  return null;
}
function openness(row,tier){
  var now=new Date(),h=now.getHours()+now.getMinutes()/60;
  var w=stated(row.hours),sure=!!w;
  if(!w&&tier&&tier.window&&D.windows[tier.window])w=D.windows[tier.window];
  if(!w)return null;
  var lo=w[0],hi=w[1]===24?24:w[1],on=(hi<=lo)?(h>=lo||h<hi):(h>=lo&&h<hi);
  return {on:on,sure:sure};
}

function costChip(cost,baht){
  if(cost==='free')return '<span class="loochip free">'+bi('ฟรี','free')+'</span>';
  if(cost==='fee-small')return '<span class="loochip fee">'+
    (baht?bi(baht+' บาท',baht+' baht'):bi('5–10 ฿','5-10 ฿'))+'</span>';
  if(cost==='free-or-small')return '<span class="loochip">'+bi('ฟรี/5–10 ฿','free / 5-10 ฿')+'</span>';
  if(cost==='with-order')return '<span class="loochip cust">'+bi('ซื้อของก่อน','buy something')+'</span>';
  return '';
}

/* Three doors, and which one a row shows depends on what exists. LINE is the
   Thai-facing one and only appears once the Official Account is provisioned;
   the numbered ticks post straight to the worker; GitHub is the developers'
   side entrance and always works. Nobody is sent to the wrong one. */
function reportUrl(name,href,id){
  var body='ห้องน้ำ / Toilet: '+name+'\n'+(href?location.origin+'/'+href+'.html\n':'')+
    (id?'[id:'+id+']\n':'')+
    '\nที่นี่ใช้ได้ไหม เสียเงินเท่าไร / Can it be used, and what does it cost?\n\n'+
    D.reports.map(function(r,i){return (i+1)+'. '+r.emoji+' '+r.th+' / '+r.en;}).join('\n')+
    '\n\nลบข้อที่ไม่ใช่ออก แล้วส่งได้เลย / Delete the lines that do not apply, then send.\n';
  return 'https://github.com/NaNoBotCo/mot-dang/issues/new?title='+
    encodeURIComponent('ห้องน้ำ / Toilet: '+name)+'&body='+encodeURIComponent(body);
}
function lineUrl(name,id){
  if(!D.lineOa||!id)return '';
  return 'https://line.me/R/oaMessage/'+encodeURIComponent(D.lineOa)+'/?'+
    encodeURIComponent('ห้องน้ำ '+name+' [id:'+id+']');
}
/* The quickest door of all: the ticks, right on the row. Posts one closed
   word to the worker and says so on the spot. Falls back to nothing if the
   worker is unreachable — the GitHub link beside it still works. */
function tickRow(id,name){
  if(!id||!D.reportEndpoint)return '';
  /* LINE lives in here rather than on the row: it is the same intent as the
     ticks, and as a fourth link up top it cost a line of every result. */
  var lu=lineUrl(name,id);
  return '<div class="looticks" data-for="'+esc(id)+'" hidden>'+
    D.reports.map(function(r){return '<button type="button" data-rep="'+esc(r.key)+'">'+
      r.emoji+' '+bi(r.th,r.en)+'</button>';}).join('')+
    (lu?'<a class="lookline" href="'+esc(lu)+'" rel="noopener">'+
      bi('หรือบอกทางไลน์','or tell us on LINE')+'</a>':'')+
    '<span class="lookthx" hidden>'+bi('ขอบคุณเจ้า 🐜','thank you 🐜')+'</span>'+
    '<span class="lookerr" hidden>'+bi('ส่งไม่สำเร็จ ลองอีกครั้ง หรือใช้ทางอื่นด้านล่าง',
      'That did not send — try again, or use another door below')+'</span></div>';
}
function wireTicks(){
  elList.querySelectorAll('.looticks').forEach(function(box){
    box.querySelectorAll('button[data-rep]').forEach(function(b){
      b.addEventListener('click',function(){
        box.querySelector('.lookerr').hidden=true;
        box.querySelectorAll('button').forEach(function(x){x.disabled=true;});
        fetch(D.reportEndpoint,{method:'POST',headers:{'content-type':'application/json'},
          body:JSON.stringify({placeId:box.dataset.for,report:b.dataset.rep})})
          .then(function(r){if(!r.ok)throw 0;
            box.querySelector('.lookthx').hidden=false;
            box.querySelectorAll('button').forEach(function(x){x.hidden=true;});})
          /* Say so. A tap that silently does nothing reads as a broken page,
             and the other two doors are right there. */
          .catch(function(){box.querySelector('.lookerr').hidden=false;
            box.querySelectorAll('button').forEach(function(x){x.disabled=false;});});
      });});
    });
  elList.querySelectorAll('[data-tickopen]').forEach(function(a){
    a.addEventListener('click',function(e){e.preventDefault();
      var box=elList.querySelector('.looticks[data-for="'+a.dataset.tickopen+'"]');
      if(box)box.hidden=!box.hidden;});});
}

/* One shape for both kinds of row, so the renderer never has to ask which
   file a result came from — only how sure it is. */
function normalise(){
  var out=[];
  D.verified.forEach(function(v){
    out.push({kind:'v',lat:v[0],lng:v[1],th:v[2]||'ห้องน้ำสาธารณะ',en:v[3]||(v[2]?'':'Public toilet'),
      cost:v[4],baht:v[5],hours:v[6],flags:v[7]||'',href:'',tier:null});
  });
  var add=function(p){
    var t=D.tiers[p[0]];
    var cost=t.cost,baht=0,acc=t.access;
    var rep=p[7];
    if(rep){var R=D.reports.filter(function(x){return x.key===rep;})[0];
      if(R&&R.sets){if(R.sets.cost)cost=R.sets.cost;if(R.sets.access)acc=R.sets.access;
        if(R.sets.baht)baht=R.sets.baht;}}
    out.push({kind:rep?'f':'t',lat:p[1],lng:p[2],th:p[3],en:p[4],cost:cost,baht:baht,
      hours:p[6],flags:'',href:p[5],tier:t,access:acc,id:p[8]||''});
  };
  D.places.forEach(add);
  if(showCust&&MORE)MORE.places.forEach(add);
  return out;
}

function passes(x){
  if(filter==='free')return x.cost==='free'||x.cost==='free-or-small';
  if(filter==='open'){var o=openness(x,x.tier);return !o||o.on;}
  if(filter==='wc')return x.flags.indexOf('w')>=0;
  return true;
}

function render(){
  if(!D)return;
  /* No origin has ever meant no page. It now means Tha Phae Gate, said out
     loud in the status line, which is a thing a reader can correct in one
     tap — unlike a spinner waiting on a permission they did not grant. */
  if(!here)here=DEFAULTS.cm;
  var rows=normalise().filter(passes);
  rows.forEach(function(x){x.d=hav(here.lat,here.lng,x.lat,x.lng);});
  /* Distance, and nothing else. An earlier version nudged mapped points and
     field reports up by 90 m so confirmed things outranked habits, and it
     produced a list reading 80 m, 120 m, 270 m, 180 m — which on a page whose
     one promise is "nearest first" looks broken, and looking broken costs
     more than the nudge was worth. Confidence is already on every row, in the
     "mapped" and "checked by a person" chips; the reader can weigh it. */
  rows.sort(function(a,b){return a.d-b.d;});
  rows=rows.slice(0,40);
  if(!rows.length){elList.innerHTML='<li class="loorow"><div class="loobody">'+
    bi('ไม่พบในตัวกรองนี้ ลองเอาตัวกรองออก','Nothing matches that filter — try clearing it')+
    '</div></li>';return;}
  /* The tier sentence belongs to the CLASS, not the row: printing it under
     all 591 temples restated one paragraph 591 times and pushed the results
     themselves off a phone screen. Shown once, the first time its tier
     appears in this list. */
  var toldTier={};
  elList.innerHTML=rows.map(function(x){
    var t=x.tier,o=openness(x,t),chips=[];
    /* The number once, not once per language — "80 ม. · เดิน ~1 นาที · 80 ม.
       · ~1 min walk" spent two lines saying 80 twice. */
    chips.push('<span class="loodist">'+esc(fmtD(x.d))+'</span>'+
      '<span class="loowalk">'+bi('เดิน ~'+Math.max(1,Math.round(x.d/D.walkMetresPerMinute))+' นาที',
        '~'+Math.max(1,Math.round(x.d/D.walkMetresPerMinute))+' min walk')+'</span>');
    if(x.kind==='v')chips.push('<span class="loochip sure">'+bi('ปักหมุดไว้แล้ว','mapped')+'</span>');
    if(x.kind==='f')chips.push('<span class="loochip sure">'+bi('มีคนไปดูมา','checked by a person')+'</span>');
    chips.push(costChip(x.cost,x.baht));
    if(o)chips.push('<span class="loochip '+(o.on?'open':'shut')+'">'+
      (o.sure?bi(o.on?'เปิดอยู่':'ปิดแล้ว',o.on?'open now':'closed now')
             :bi(o.on?'น่าจะเปิด':'น่าจะปิดแล้ว',o.on?'likely open':'probably closed'))+'</span>');
    if(x.flags.indexOf('w')>=0)chips.push('<span class="loochip wc">♿ '+bi('รถเข็นเข้าได้','step-free')+'</span>');
    if(x.flags.indexOf('r')>=0)chips.push('<span class="loochip cust">'+bi('เจ้าของจำกัดสิทธิ์','restricted')+'</span>');
    /* The name IS the link to the place page. It was a fourth action before,
       and four bilingual links wrapped to a hundred pixels on a phone — which
       on this page costs a whole result you could otherwise have seen. */
    var nm=x.en&&x.en!==x.th?bi(x.th,x.en):'<span class="th">'+esc(x.th)+'</span>';
    if(x.href)nm='<a href="'+esc(x.href)+'.html">'+nm+'</a>';
    var acts=[],nom=x.th||x.en;
    if(x.href)acts.push('<a href="plan.html?stops='+encodeURIComponent(x.href.split('/')[0]+':'+
      x.href.split('/').slice(1).join('/'))+'">'+bi('เดินไปยังไง','walk me there')+'</a>');
    if(x.id&&D.reportEndpoint)acts.push('<a href="#" data-tickopen="'+esc(x.id)+'">'+
      bi('บอกมดแดง','tell the ants')+'</a>');
    if(!x.id||!D.reportEndpoint)acts.push('<a href="'+esc(reportUrl(nom,x.href,x.id))+
      '" rel="noopener">'+bi('บอกมดแดง','tell the ants')+'</a>');
    var tk=t?t.key:'_mapped',basis='';
    if(!toldTier[tk]){toldTier[tk]=1;
      basis='<p class="loobasis">'+(t?bi(t.basis_th,t.basis_en):
        bi('ห้องน้ำสาธารณะที่มีคนปักหมุดไว้ในแผนที่เปิด',
           'A public toilet somebody mapped in OpenStreetMap.'))+'</p>';}
    return '<li class="loorow">'+
      '<span class="lootier" aria-hidden="true">'+(t?t.emoji:'🚻')+'</span>'+
      '<div class="loobody"><b class="looname">'+nm+'</b>'+
      '<div class="loometa">'+chips.join('')+'</div>'+basis+
      '<div class="looacts">'+acts.join(' ')+'</div>'+tickRow(x.id,nom)+'</div></li>';
  }).join('');
  wireTicks();
  if(elMap)drawMap(rows,elMap);
}

function fmtD(m){return m<1000?Math.round(m/10)*10+' ม.':(m/1000).toFixed(1)+' กม.';}

/* The origin's name in whichever language is showing. Used in alt text and
   on the map face, where a two-language string would not fit. */
function originName(){
  if(!here)return '';
  if(here.src==='gps')return LANG.classList.contains('lang-en')?'you':'คุณ';
  return (LANG.classList.contains('lang-en')&&here.en)||here.th||here.en||'';
}

/* ---- the "which way" panel -------------------------------------------
   A list tells you how far; it cannot tell you which way to turn. This is
   drawn here rather than at build time because it has to be centred on
   wherever the reader actually is. No tiles and no map library: the site
   refuses both, and every shape below comes from coordinates already in the
   baked file. Equirectangular with a cos(lat) correction is ample over the
   half-kilometre or so this ever covers. */
function drawMap(rows,host){
  if(!rows.length){var d0=host.querySelector('.mdmap-draw')||host;d0.innerHTML='';return;}
  var S=300,PAD=26,shown=rows.slice(0,10);
  /* Frame on the tenth result so the pins fill the box, with a floor so a
     cluster of very near ones does not zoom to absurdity. */
  var far=Math.max(160,shown[shown.length-1].d)*1.18;
  var cosla=Math.cos(here.lat*Math.PI/180);
  var mPerDegLat=110574,mPerDegLng=111320*cosla;
  var half=S/2-PAD, scale=half/far;                 // px per metre
  /* Kept so a tap on the picture can be turned back into a coordinate. The
     projection is only ever inverted at the scale it was drawn at, which is
     why this is stashed here rather than recomputed from scratch. */
  lastTf={S:S,scale:scale,mLat:mPerDegLat,mLng:mPerDegLng,lat:here.lat,lng:here.lng};
  function px(la,ln){
    return [S/2+((ln-here.lng)*mPerDegLng)*scale,
            S/2-((la-here.lat)*mPerDegLat)*scale];
  }
  function inBox(p){return p[0]>-40&&p[0]<S+40&&p[1]>-40&&p[1]<S+40;}
  var p=[];
  p.push('<svg viewBox="0 0 '+S+' '+S+'" class="loomapsvg" role="img" aria-label="'+
    esc(here.src==='gps'?(D.mapAlt||''):
      (D.mapAltAt||'').replace(/%s/g,originName()))+'">');
  /* The cream card. Class-tagged because it is the "there is no ground here"
     state: with a basemap live underneath, map_shell hides it and these same
     rings and pins land on real streets instead. */
  p.push('<rect class="mdmap-bg" width="'+S+'" height="'+S+'" rx="14" fill="#FFFDF8" stroke="#E4D8C4"/>');
  /* Range rings, labelled — the cheapest way to read distance off a picture. */
  [0.25,0.5,1].forEach(function(f){
    var r=half*f; if(r<18)return;
    p.push('<circle cx="'+(S/2)+'" cy="'+(S/2)+'" r="'+r.toFixed(1)+'" fill="none" '+
      'stroke="#EADFCB" stroke-dasharray="3 4"/>');
    /* The ring itself is a distance and grows with the ground. Its label is
       a label: it rides the ring outward but stays 9px tall. */
    p.push('<text data-mdpin="'+(S/2+3)+','+(S/2-r+11).toFixed(1)+'" x="'+(S/2+3)+'" y="'+(S/2-r+11).toFixed(1)+'" font-size="9" paint-order="stroke" stroke="#FFFDF8" stroke-width="2.5" '+
      'fill="#9C8874">'+esc(fmtD(far*f))+'</text>');
  });
  /* The moat, when any of it is actually in frame. Everyone here navigates by
     it, and it is the difference between a picture of dots and a place. */
  if(D.moat&&D.moat.length){
    var ring=D.moat.map(function(c){return px(c[0],c[1]);});
    /* Overlap of BOUNDING BOXES, not "is a corner in frame". The ring is four
       points with very long sides: standing at Tha Phae Gate, on the moat,
       every corner is off-frame and the vertex test drew nothing — while the
       side you are standing on ran straight through the middle. */
    var xs=ring.map(function(q){return q[0];}),ys=ring.map(function(q){return q[1];});
    var overlaps=Math.min.apply(null,xs)<S+40&&Math.max.apply(null,xs)>-40&&
                 Math.min.apply(null,ys)<S+40&&Math.max.apply(null,ys)>-40;
    if(overlaps){
      p.push('<polygon points="'+ring.map(function(q){
        return q[0].toFixed(1)+','+q[1].toFixed(1);}).join(' ')+
        '" fill="none" stroke="#8FA5CC" stroke-width="2.5" stroke-dasharray="7 4"/>');
    }
    (D.gates||[]).forEach(function(gt){
      var q=px(gt[0],gt[1]); if(!inBox(q))return;
      /* Several of the landmarks people start from ARE moat gates — Tha Phae
         is the default origin and the busiest gate on the ring. Drawing both
         markers put the same name on the picture twice, an inch apart, which
         reads as two places. The centre ring already names it. */
      if(Math.abs(q[0]-S/2)<12&&Math.abs(q[1]-S/2)<12)return;
      /* Dot and name as one mark, pivoting on the gate itself — the moat it
         sits on grows, the gate stays a gate. */
      p.push('<g data-mdpin="'+q[0].toFixed(1)+','+q[1].toFixed(1)+'">');
      p.push('<circle cx="'+q[0].toFixed(1)+'" cy="'+q[1].toFixed(1)+
        '" r="3" fill="#8FA5CC"/>');
      p.push('<text x="'+(q[0]+5).toFixed(1)+'" y="'+(q[1]+3.5).toFixed(1)+
        '" font-size="9" paint-order="stroke" stroke="#FFFDF8" stroke-width="2.5" fill="#5E6C8A">'+esc(gt[2])+'</text>');
      p.push('</g>');
    });
  }
  /* North, so a rotated phone still reads. It belongs to the frame, not to
     the city: it stays in its corner at its own size however far the ground
     under it is dragged. Always true here — the basemap cannot be rotated. */
  p.push('<g data-mdfix="1" opacity=".75"><path d="M'+(S-20)+' '+(PAD-6)+' l5 13 -5-3 -5 3Z" fill="#6B584A"/>'+
    '<text x="'+(S-20)+'" y="'+(PAD+22)+'" font-size="9" fill="#6B584A" text-anchor="middle">N</text></g>');
  /* Pins furthest-first, so the nearest ones land on top of the pile. */
  shown.slice().reverse().forEach(function(x){
    var i=shown.indexOf(x),q=px(x.lat,x.lng);
    var col=x.tier?(x.tier.color||D.mappedColor):D.mappedColor;
    /* Pivoting on the point, not the head of the pin: the tip is the part
       that means an address, and it is the part that must not move. */
    p.push('<g class="loopin" data-mdpin="'+q[0].toFixed(1)+','+q[1].toFixed(1)+
      '" data-pin="'+i+'" tabindex="0" role="button" aria-label="'+
      esc((x.th||x.en)+' — '+fmtD(x.d))+'">');
    p.push('<line x1="'+q[0].toFixed(1)+'" y1="'+q[1].toFixed(1)+'" x2="'+q[0].toFixed(1)+
      '" y2="'+(q[1]-9).toFixed(1)+'" stroke="'+col+'" stroke-width="1.5"/>');
    p.push('<circle cx="'+q[0].toFixed(1)+'" cy="'+(q[1]-15).toFixed(1)+'" r="11" fill="'+col+
      '" stroke="#FFFDF8" stroke-width="2"/>');
    p.push('<text x="'+q[0].toFixed(1)+'" y="'+(q[1]-11).toFixed(1)+
      '" font-size="11" text-anchor="middle">'+(x.tier?x.tier.emoji:'🚻')+'</text>');
    p.push('<circle cx="'+q[0].toFixed(1)+'" cy="'+q[1].toFixed(1)+'" r="2" fill="'+col+'"/>');
    p.push('</g>');
  });
  /* The centre, last, so nothing hides it — but it is only ever drawn as
     "you" when the reader actually handed over a fix. Centred on a landmark
     it gets a hollow ring and the landmark's name, because a solid dot that
     says "you are here" about Tha Phae Gate is a small lie told to somebody
     who may be standing in Santitham. */
  /* Held at drawn size like every other mark. The halo is a fixed 9px, not a
     drawn accuracy radius — it says "here", not "within so many metres" — so
     growing it with the zoom would be inventing a precision claim. */
  p.push('<g data-mdpin="'+(S/2)+','+(S/2)+'">');
  if(here.src==='gps'){
    p.push('<circle cx="'+(S/2)+'" cy="'+(S/2)+'" r="9" fill="#D4552C" opacity=".18"/>');
    p.push('<circle cx="'+(S/2)+'" cy="'+(S/2)+'" r="4.5" fill="#D4552C" stroke="#fff" stroke-width="2"/>');
  }else{
    p.push('<circle cx="'+(S/2)+'" cy="'+(S/2)+'" r="7" fill="#FFFDF8" stroke="#D4552C" '+
      'stroke-width="2.5" stroke-dasharray="3 2.5"/>');
    p.push('<text x="'+(S/2)+'" y="'+(S/2+21)+'" font-size="9.5" text-anchor="middle" paint-order="stroke" stroke="#FFFDF8" stroke-width="2.5" '+
      'fill="#A8371A">'+esc(originName())+'</text>');
  }
  p.push('</g>');
  p.push('</svg>');
  /* When map_shell has wrapped this box the drawn picture belongs in its own
     layer, under the tiles — writing straight into the container would tear
     out the live map along with it. With no basemap configured there is no
     wrapper and this is the container, exactly as before. */
  var el=host.querySelector('.mdmap-draw')||host;
  el.innerHTML=p.join('');
  /* Put the basemap under the drawing at the drawing's own scale. The SVG is
     S viewBox units wide shown at whatever width the box actually got, so
     metres-per-CSS-pixel has to account for both. Without that the streets
     would be at one zoom and the pins at another, which is worse than no
     streets at all. */
  if(window.MDMAP&&MDMAP.live(host)){
    var shown=host.clientWidth||S;
    MDMAP.retarget(host,here.lat,here.lng,1/(scale*(shown/S)));
  }
  el.querySelectorAll('.loopin').forEach(function(g){
    var go=function(){
      var li=elList.children[+g.dataset.pin]; if(!li)return;
      li.scrollIntoView({block:'center'});
      li.classList.add('loohit');
      setTimeout(function(){li.classList.remove('loohit');},1400);
    };
    g.addEventListener('click',go);
    g.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();go();}});
  });
  /* Tap anywhere else on the picture to move the starting point there. This
     is the third of the four ways in, and on a phone it is the fastest one:
     no typing, no list to read, no permission to grant — you point at where
     you are. */
  var svg=el.querySelector('svg');
  if(svg)svg.addEventListener('click',function(e){
    if(e.target.closest('.loopin')||!lastTf)return;
    var b=svg.getBoundingClientRect();
    if(!b.width||!b.height)return;
    var x=(e.clientX-b.left)/b.width*lastTf.S, y=(e.clientY-b.top)/b.height*lastTf.S;
    setOrigin({lat:lastTf.lat-((y-lastTf.S/2)/lastTf.scale)/lastTf.mLat,
               lng:lastTf.lng+((x-lastTf.S/2)/lastTf.scale)/lastTf.mLng,
               th:'จุดที่คุณแตะไว้',en:'the spot you tapped',src:'tap'});
  });
}

/* ---- the origin, and the four equal ways to set one -------------------
   GPS is one of four, not the front door with three consolation prizes
   behind it. The picker is on the page from the first paint, before anyone
   has been asked anything, and it stays there afterwards. */
function setOrigin(o){
  here=o;
  /* A GPS fix is never written to disk. The promise on this page is that the
     coordinate stays in the browser and is never stored; localStorage is
     storage. Landmarks and dropped pins are the reader's own choice of a
     public place and persist happily. */
  if(o.src==='gps')store('md-loo-origin',null);
  else store('md-loo-origin',{lat:o.lat,lng:o.lng,th:o.th,en:o.en,src:o.src,prov:o.prov||''});
  elState.className='loostate';
  elState.innerHTML=o.src==='gps'
    ? bi('เรียงจากใกล้ที่สุด · ระยะเป็นเส้นตรง เดินจริงไกลกว่านี้',
         'Nearest first. Distances are straight-line — the walk is longer, especially across the moat.')
    : bi('เรียงจาก '+(o.th||o.en)+' · แตะแผนที่หรือเลือกที่อื่นเพื่อย้ายจุดตั้งต้น',
         'Measured from '+(o.en||o.th)+'. Tap the map or pick another spot to move it.');
  render();
}

/* Our dialog opens first. One sentence about where the coordinate goes,
   then the two answers — and "not now" is final. */
function openGate(){
  if(GPS_OFF||!elGate)return;
  elGate.hidden=false;
  var yes=elGate.querySelector('[data-gate="yes"]');
  if(yes)yes.focus();
}
function closeGate(){if(elGate)elGate.hidden=true;}

/* The only place in this file that touches navigator.geolocation, and it is
   reachable only from a tap on the dialog's own button. */
function useLocation(){
  closeGate();
  if(!navigator.geolocation){
    fail('เครื่องนี้บอกตำแหน่งไม่ได้ — เลือกจุดตั้งต้นข้างล่างได้เลย · '+
         'This device cannot share a location — pick a starting point below');
    killGps();return;}
  if(elFind)elFind.disabled=true;
  elState.className='loostate';
  elState.innerHTML=bi('กำลังหาตำแหน่ง…','Finding you…');
  navigator.geolocation.getCurrentPosition(function(p){
    if(elFind)elFind.disabled=false;
    setOrigin({lat:p.coords.latitude,lng:p.coords.longitude,src:'gps'});
  },function(){
    /* Refused, or the fix timed out. Either way the list already works from
       wherever it was measuring a moment ago — so this is a note, not an
       error state, and the page never empties out behind it. */
    if(elFind)elFind.disabled=false;
    note('ยังไม่ได้ตำแหน่ง — ยังเรียงจาก '+(here?(here.th||here.en):'จุดตั้งต้น')+' อยู่ เลือกจุดอื่นได้ข้างล่าง',
         'No location — still measuring from '+(here?(here.en||here.th):'the starting point')+
         '. Pick another spot below.');
    killGps();
  },{enableHighAccuracy:true,timeout:10000,maximumAge:60000});
}

/* Said no once, asked never again. Both doors leave the DOM: a disabled
   button that still looks tappable is its own small insult, and a hidden one
   is a thing a later bug can un-hide. */
function killGps(){
  GPS_OFF=true;closeGate();
  if(elFind&&elFind.parentNode)elFind.parentNode.removeChild(elFind);
  if(elGate&&elGate.parentNode)elGate.parentNode.removeChild(elGate);
  elFind=null;elGate=null;
  if(elOrigin)elOrigin.classList.add('sole');
}

function fail(msg){elState.className='loostate err';
  var p=msg.split(' · ');elState.innerHTML=bi(p[0],p[1]||'');}
/* Not an error — the page behind it is fine. Different class, so it does not
   get the red treatment reserved for "this actually broke". */
function note(th,en){elState.className='loostate soft';elState.innerHTML=bi(th,en);}

/* ---- typing a place name --------------------------------------------
   The fourth way in. Matched against names already in the baked file rather
   than sent to a geocoder: the reader typing "where I am" into a stranger's
   search box should not have that shipped to a third party, and every place
   worth naming around here is already in this file. It also keeps working
   with no signal, which the geocoder would not. */
function gazetteer(){
  var out=[];
  if(elNear)elNear.querySelectorAll('a[data-lat]').forEach(function(a){
    out.push({lat:+a.dataset.lat,lng:+a.dataset.lng,
      th:a.dataset.th||a.textContent.trim(),en:a.dataset.en||a.textContent.trim(),
      src:'landmark',prov:a.dataset.prov||''});});
  if(D)D.places.forEach(function(p){
    out.push({lat:p[1],lng:p[2],th:p[3],en:p[4]||p[3],src:'place'});});
  return out;
}
function wireSearch(){
  var box=document.getElementById('loosearch'),out=document.getElementById('loohits');
  if(!box||!out)return;
  function run(){
    var q=box.value.trim().toLowerCase();
    if(q.length<2){out.innerHTML='';out.hidden=true;return;}
    var hits=gazetteer().filter(function(o){
      return (o.th||'').toLowerCase().indexOf(q)>=0||(o.en||'').toLowerCase().indexOf(q)>=0;
    }).slice(0,8);
    if(!hits.length){
      /* Never an empty box with nothing in it. The list behind this is still
         sorted and still usable; say so rather than looking broken. */
      out.innerHTML='<li class="loomiss">'+bi('ไม่พบชื่อนี้ — ลองชื่อสั้นลง หรือแตะแผนที่',
        'No match — try a shorter name, or tap the map')+'</li>';
      out.hidden=false;return;}
    out.innerHTML=hits.map(function(o,i){
      return '<li><button type="button" data-hit="'+i+'">'+bi(o.th,o.en)+'</button></li>';}).join('');
    out.hidden=false;
    out.querySelectorAll('button[data-hit]').forEach(function(b){
      b.addEventListener('click',function(){
        var o=hits[+b.dataset.hit];
        setOrigin({lat:o.lat,lng:o.lng,th:o.th,en:o.en,src:'search',prov:o.prov});
        out.hidden=true;box.value='';});});
  }
  box.addEventListener('input',run);
}

function boot(){
  /* The origin is settled BEFORE the data arrives and before anything is
     asked of anybody: a remembered choice if there is one, Tha Phae Gate if
     not. By the time the list paints it already has somewhere to measure
     from, which is the whole trick — there is no moment where the page needs
     a permission in order to be a page. */
  var saved=recall('md-loo-origin');
  here=(saved&&typeof saved.lat==='number'&&typeof saved.lng==='number'&&saved.src!=='gps')
    ? saved : DEFAULTS.cm;

  /* Ask the browser what it already knows, so the button never promises
     something the OS has already refused. Where this is unsupported the
     button stays — the dialog in front of it is still the reader's own
     choice, and a wrongly-hidden control is worse than an honest one. */
  if(navigator.permissions&&navigator.permissions.query){
    try{navigator.permissions.query({name:'geolocation'}).then(function(st){
      if(st.state==='denied')killGps();
      st.onchange=function(){if(st.state==='denied')killGps();};
    }).catch(function(){});}catch(e){}
  }

  /* Tapping the ground on the live basemap does what tapping the drawn
     picture does. The SVG stops taking pointer events once tiles are under
     it — otherwise the overlay would swallow every attempt to pan — so the
     shell reports the tap instead, and only when it was a tap, not a drag. */
  if(elMap)elMap.addEventListener('mdmap:click',function(e){
    setOrigin({lat:e.detail.lat,lng:e.detail.lng,
      th:'จุดที่คุณแตะไว้',en:'the spot you tapped',src:'tap'});});

  if(elFind)elFind.addEventListener('click',openGate);
  if(elGate){
    var yes=elGate.querySelector('[data-gate="yes"]'),no=elGate.querySelector('[data-gate="no"]');
    if(yes)yes.addEventListener('click',useLocation);
    if(no)no.addEventListener('click',killGps);
    elGate.addEventListener('keydown',function(e){if(e.key==='Escape')closeGate();});
  }

  fetch('data/toilets.json').then(function(r){return r.json();}).then(function(j){
    D=j;
    elFilters.querySelectorAll('button').forEach(function(b){
      b.addEventListener('click',function(){
        filter=b.dataset.f;
        elFilters.querySelectorAll('button').forEach(function(x){
          x.setAttribute('aria-pressed',x===b?'true':'false');});
        render();});});
    elMore.querySelector('button').addEventListener('click',function(){
      var btn=this;btn.disabled=true;
      fetch(D.customersFile).then(function(r){return r.json();}).then(function(m){
        MORE=m;showCust=true;elMore.hidden=true;render();})
        .catch(function(){btn.disabled=false;});});
    elNear.querySelectorAll('a[data-lat]').forEach(function(a){
      a.addEventListener('click',function(e){e.preventDefault();
        setOrigin({lat:+a.dataset.lat,lng:+a.dataset.lng,
          th:a.dataset.th||a.textContent.trim(),en:a.dataset.en||a.textContent.trim(),
          src:'landmark',prov:a.dataset.prov||''});});});
    wireSearch();
    /* Everything on, straight away. These used to wait on a location fix,
       which is what made a permission dialog the price of admission. */
    elFilters.hidden=false;elMore.hidden=false;
    setOrigin(here);
  }).catch(function(){fail('โหลดข้อมูลไม่สำเร็จ ลองรีเฟรช · Could not load the data — try reloading');});
}
boot();
})();
