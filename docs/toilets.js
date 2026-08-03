/* ห้องน้ำใกล้ฉัน. Everything is baked; the only thing this asks the
   network for is the second, larger file, and only if the reader taps for it.
   The location never leaves the browser — there is nowhere on this site to
   send it. */
(function(){
var D=null,MORE=null,here=null,filter='all',showCust=false;
var elBtn=document.getElementById('loogo'),elState=document.getElementById('loostate'),
    elList=document.getElementById('loolist'),elFilters=document.getElementById('loofilters'),
    elMore=document.getElementById('loomore'),elNear=document.getElementById('loonear'),
    elMap=document.getElementById('loomap');
if(!elBtn)return;
var LANG=document.documentElement;

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
  if(!here||!D)return;
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

/* ---- the "which way" panel -------------------------------------------
   A list tells you how far; it cannot tell you which way to turn. This is
   drawn here rather than at build time because it has to be centred on
   wherever the reader actually is. No tiles and no map library: the site
   refuses both, and every shape below comes from coordinates already in the
   baked file. Equirectangular with a cos(lat) correction is ample over the
   half-kilometre or so this ever covers. */
function drawMap(rows,el){
  if(!rows.length){el.innerHTML='';return;}
  var S=300,PAD=26,shown=rows.slice(0,10);
  /* Frame on the tenth result so the pins fill the box, with a floor so a
     cluster of very near ones does not zoom to absurdity. */
  var far=Math.max(160,shown[shown.length-1].d)*1.18;
  var cosla=Math.cos(here.lat*Math.PI/180);
  var mPerDegLat=110574,mPerDegLng=111320*cosla;
  var half=S/2-PAD, scale=half/far;                 // px per metre
  function px(la,ln){
    return [S/2+((ln-here.lng)*mPerDegLng)*scale,
            S/2-((la-here.lat)*mPerDegLat)*scale];
  }
  function inBox(p){return p[0]>-40&&p[0]<S+40&&p[1]>-40&&p[1]<S+40;}
  var p=[];
  p.push('<svg viewBox="0 0 '+S+' '+S+'" class="loomapsvg" role="img" aria-label="'+
    esc(D.mapAlt||'')+'">');
  p.push('<rect width="'+S+'" height="'+S+'" rx="14" fill="#FFFDF8" stroke="#E4D8C4"/>');
  /* Range rings, labelled — the cheapest way to read distance off a picture. */
  [0.25,0.5,1].forEach(function(f){
    var r=half*f; if(r<18)return;
    p.push('<circle cx="'+(S/2)+'" cy="'+(S/2)+'" r="'+r.toFixed(1)+'" fill="none" '+
      'stroke="#EADFCB" stroke-dasharray="3 4"/>');
    p.push('<text x="'+(S/2+3)+'" y="'+(S/2-r+11).toFixed(1)+'" font-size="9" '+
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
      p.push('<circle cx="'+q[0].toFixed(1)+'" cy="'+q[1].toFixed(1)+
        '" r="3" fill="#8FA5CC"/>');
      p.push('<text x="'+(q[0]+5).toFixed(1)+'" y="'+(q[1]+3.5).toFixed(1)+
        '" font-size="9" fill="#5E6C8A">'+esc(gt[2])+'</text>');
    });
  }
  /* North, so a rotated phone still reads. */
  p.push('<g opacity=".75"><path d="M'+(S-20)+' '+(PAD-6)+' l5 13 -5-3 -5 3Z" fill="#6B584A"/>'+
    '<text x="'+(S-20)+'" y="'+(PAD+22)+'" font-size="9" fill="#6B584A" text-anchor="middle">N</text></g>');
  /* Pins furthest-first, so the nearest ones land on top of the pile. */
  shown.slice().reverse().forEach(function(x){
    var i=shown.indexOf(x),q=px(x.lat,x.lng);
    var col=x.tier?(x.tier.color||D.mappedColor):D.mappedColor;
    p.push('<g class="loopin" data-pin="'+i+'" tabindex="0" role="button" aria-label="'+
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
  /* You, last, so nothing hides you. */
  p.push('<circle cx="'+(S/2)+'" cy="'+(S/2)+'" r="9" fill="#D4552C" opacity=".18"/>');
  p.push('<circle cx="'+(S/2)+'" cy="'+(S/2)+'" r="4.5" fill="#D4552C" stroke="#fff" stroke-width="2"/>');
  p.push('</svg>');
  el.innerHTML=p.join('');
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
}

function locate(){
  if(!navigator.geolocation){fail('เครื่องนี้บอกตำแหน่งไม่ได้ · This device cannot share a location');return;}
  elBtn.disabled=true;
  elState.className='loostate';
  elState.innerHTML=bi('กำลังหาตำแหน่ง…','Finding you…');
  navigator.geolocation.getCurrentPosition(function(p){
    here={lat:p.coords.latitude,lng:p.coords.longitude};
    elBtn.disabled=false;
    elState.innerHTML=bi('เรียงจากใกล้ที่สุด · ระยะเป็นเส้นตรง เดินจริงไกลกว่านี้',
      'Nearest first. Distances are straight-line — the walk is longer, especially across the moat.');
    elFilters.hidden=false;elMore.hidden=false;
    render();
  },function(){
    elBtn.disabled=false;
    fail('ยังไม่ได้ตำแหน่ง — เลือกจุดใกล้ตัวข้างล่างได้เลย · No location yet — pick a spot below instead');
    elNear.hidden=false;
  },{enableHighAccuracy:true,timeout:10000,maximumAge:60000});
}
function fail(msg){elState.className='loostate err';
  var p=msg.split(' · ');elState.innerHTML=bi(p[0],p[1]||'');}

function boot(){
  fetch('data/toilets.json').then(function(r){return r.json();}).then(function(j){
    D=j;elBtn.disabled=false;
    elBtn.addEventListener('click',locate);
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
        here={lat:+a.dataset.lat,lng:+a.dataset.lng};
        elFilters.hidden=false;elMore.hidden=false;
        elState.className='loostate';
        elState.innerHTML=bi('เรียงจากจุดที่เลือก · ระยะเป็นเส้นตรง',
          'Nearest to the spot you picked. Distances are straight-line.');
        render();});});
  }).catch(function(){fail('โหลดข้อมูลไม่สำเร็จ ลองรีเฟรช · Could not load the data — try reloading');});
}
boot();
})();
