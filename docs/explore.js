/* explore.js — /map.html only.

   The map draws into the basemap rather than over it (see explore_layer.py for
   why this one page is allowed to). Everything it paints comes from the
   per-shelf GeoJSON files build.py already writes, fetched only when a reader
   asks for that shelf — nothing here pulls down a shelf nobody switched on. */
(function(){
var el=document.getElementById('xmap');
/* No basemap — the archive is unreachable, or this browser could not have it.
   The page still works: the shelf list below is the whole directory and it is
   plain links. What must NOT happen is chips sitting there looking like
   buttons and doing nothing when touched, so they are turned off and told
   why, and the reader is pointed at the list that does work. Silence here
   would read as a broken page rather than a page in its other mode. */
if(!el||!window.MDMAP){
  var picker=document.querySelector('.xpick');
  if(picker){
    picker.querySelectorAll('.xchip').forEach(function(b){
      b.disabled=true;b.setAttribute('aria-disabled','true');});
    var say=document.createElement('p');
    say.className='quiet';
    say.textContent='ตอนนี้ยังเปิดแผนที่ไม่ได้ — เลื่อนลงไปดูรายชื่อตามหมวดได้เลย · '+
      'The map cannot open just now. The shelves below are the same places, as a list.';
    picker.insertBefore(say,picker.firstChild.nextSibling);
  }
  ['xhere','xopen','xshot','xclear'].forEach(function(id){
    var b=document.getElementById(id);if(b)b.hidden=true;});
  return;
}

var INKS=[["#C2401C", "แดงมด · ant red"], ["#1F6B57", "เขียวหยก · jade"], ["#14479B", "น้ำเงิน · blue"], ["#8A4E9E", "ม่วง · purple"], ["#B06A00", "ส้มเข้ม · amber"], ["#2A6E86", "ฟ้าคราม · teal"]],MAX_ON=6,DEFAULT_ON=["cm-wat"];
var chips=[].slice.call(document.querySelectorAll('.xchip'));
var elCount=document.getElementById('xcount');
var on=[];               /* keys, in the order switched on — ink follows order */
var loaded={};           /* key -> true once its source is added */
var busy={};

function root(){return document.documentElement.getAttribute('data-root')||'';}
function inkFor(k){var i=on.indexOf(k);return i<0?null:INKS[i%INKS.length][0];}

/* ---- the address bar IS the view -------------------------------------
   #zoom/lat/lng/shelf,shelf. Written with replaceState so panning does not
   fill the reader's back button with a thousand entries, and read on load so
   a link somebody was sent opens on what they were shown. */
function writeHash(map){
  if(!map)return;
  var c=map.getCenter();
  var h='#'+map.getZoom().toFixed(2)+'/'+c.lat.toFixed(5)+'/'+c.lng.toFixed(5)+
        (on.length?'/'+on.join(','):'');
  try{history.replaceState(null,'',h);}catch(e){}
}
function readHash(){
  var h=(location.hash||'').replace(/^#/,'');
  if(!h)return null;
  var p=h.split('/');
  var z=parseFloat(p[0]),la=parseFloat(p[1]),ln=parseFloat(p[2]);
  if(!isFinite(z)||!isFinite(la)||!isFinite(ln))return null;
  return {zoom:z,lat:la,lng:ln,on:(p[3]||'').split(',').filter(Boolean)};
}

function paintChips(){
  chips.forEach(function(b){
    var k=b.dataset.x,ink=inkFor(k);
    b.setAttribute('aria-pressed',ink?'true':'false');
    b.querySelector('.xswatch').style.background=ink||'';
    b.disabled=!ink&&on.length>=MAX_ON;
  });
  if(elCount){
    elCount.textContent=on.length?
      (on.length+'/'+MAX_ON+' ชั้น · shelves'):'';
  }
}

MDMAP.ready(el,function(map){
  /* Where a reader was sent, or the whole of Chiang Mai. */
  var want=readHash();
  if(want){
    map.jumpTo({center:[want.lng,want.lat],zoom:want.zoom});
    on=want.on.slice(0,MAX_ON);
  }else{
    on=DEFAULT_ON.slice(0,MAX_ON);
  }

  function srcId(k){return 'x-'+k;}

  function addLayer(k,gj){
    var id=srcId(k);
    if(map.getSource(id))return;
    map.addSource(id,{type:'geojson',data:gj});
    /* A halo under the dot, for the same reason every pin on this site wears
       one: the ground has real ink in it now. */
    map.addLayer({id:id+'-halo',type:'circle',source:id,paint:{
      'circle-radius':['interpolate',['linear'],['zoom'],10,3.2,14,5.4,17,8],
      'circle-color':'#FFFCF6','circle-opacity':.85}});
    map.addLayer({id:id+'-dot',type:'circle',source:id,paint:{
      'circle-radius':['interpolate',['linear'],['zoom'],10,2,14,3.6,17,5.6],
      'circle-color':inkFor(k)||'#C2401C','circle-opacity':.95}});
    loaded[k]=true;
  }

  function recolour(){
    Object.keys(loaded).forEach(function(k){
      var ink=inkFor(k);
      if(!ink)return;
      if(map.getLayer(srcId(k)+'-dot'))
        map.setPaintProperty(srcId(k)+'-dot','circle-color',ink);
    });
  }

  function show(k,yes){
    /* '-open' belongs in this list: a shelf switched off and on again while
       the open-now rings are lit would otherwise come back without them,
       because only its dots were ever hidden. */
    ['-halo','-dot','-open'].forEach(function(sfx){
      if(map.getLayer(srcId(k)+sfx))
        map.setLayoutProperty(srcId(k)+sfx,'visibility',yes?'visible':'none');
    });
  }

  function load(k,then){
    if(loaded[k]){show(k,true);recolour();if(then)then();return;}
    if(busy[k])return;
    busy[k]=true;
    var b=document.querySelector('.xchip[data-x="'+k+'"]');
    if(b)b.setAttribute('aria-busy','true');
    fetch(root()+'data/'+k+'.geojson').then(function(r){
      if(!r.ok)throw new Error(r.status);return r.json();})
      .then(function(gj){addLayer(k,gj);recolour();
        /* A shelf switched on while "open now" is already lit gets its rings
           straight away, rather than only after the next tap of the button. */
        if(openOn){openLayerFor(k);markOpen();}
        if(then)then();})
      .catch(function(){
        /* A shelf that will not load is taken back off rather than left as a
           chip that claims to be showing something. */
        var i=on.indexOf(k);if(i>-1)on.splice(i,1);
        paintChips();
        if(elCount)elCount.textContent='ชั้นนี้โหลดไม่ได้ · that shelf did not load';
      })
      .then(function(){busy[k]=false;if(b)b.removeAttribute('aria-busy');});
  }

  /* ---- a dot answers ---------------------------------------------------
     Same card as every other map on this site, so what a touch is worth does
     not change from page to page. */
  function wireTap(){
    map.on('click',function(e){
      var ids=[];
      on.forEach(function(k){
        if(map.getLayer(srcId(k)+'-dot'))ids.push(srcId(k)+'-dot');});
      if(!ids.length)return;
      /* A fingertip, not a pixel: query a box around the touch and take the
         nearest, so a near miss still names the thing that was aimed at. */
      var R=22,pt=e.point;
      var f=map.queryRenderedFeatures(
        [[pt.x-R,pt.y-R],[pt.x+R,pt.y+R]],{layers:ids});
      if(!f.length)return;
      var best=f[0],bd=Infinity;
      f.forEach(function(ft){
        var p=map.project(ft.geometry.coordinates);
        var d=(p.x-pt.x)*(p.x-pt.x)+(p.y-pt.y)*(p.y-pt.y);
        if(d<bd){bd=d;best=ft;}});
      var pr=best.properties||{};
      var nm=[pr.nameTh,pr.nameEn].filter(Boolean).join(' · ')||pr.name||'';
      if(window.MDCARD)MDCARD.show({
        name:nm,
        sub:(pr.province==='cr'?'เชียงราย · Chiang Rai':'เชียงใหม่ · Chiang Mai'),
        href:root()+pr.province+'/p/'+pr.slug+'.html',
        plan:pr.province+':'+pr.slug,
        rank:(pr.rank&&pr.rank!=='0'&&pr.rank!==0)?pr.rank:''},el);
    });
    map.on('mousemove',function(e){
      var ids=[];
      on.forEach(function(k){
        if(map.getLayer(srcId(k)+'-dot'))ids.push(srcId(k)+'-dot');});
      if(!ids.length)return;
      var f=ids.length?map.queryRenderedFeatures(e.point,{layers:ids}):[];
      map.getCanvas().style.cursor=f.length?'pointer':'';
    });
  }

  chips.forEach(function(b){
    b.addEventListener('click',function(){
      var k=b.dataset.x,i=on.indexOf(k);
      if(i>-1){on.splice(i,1);show(k,false);}
      else{
        if(on.length>=MAX_ON)return;
        on.push(k);load(k);
      }
      paintChips();recolour();writeHash(map);
    });
  });

  document.getElementById('xclear').addEventListener('click',function(){
    on.slice().forEach(function(k){show(k,false);});
    on=[];paintChips();writeHash(map);
  });

  /* Near me goes through the one door on this site that may ask. */
  var here=document.getElementById('xhere');
  here.addEventListener('click',function(){
    if(!window.MDLOC)return;
    here.setAttribute('aria-busy','true');
    MDLOC.ask(function(pt){
      here.removeAttribute('aria-busy');
      map.flyTo({center:[pt.lng,pt.lat],zoom:15,
        duration:matchMedia('(prefers-reduced-motion:reduce)').matches?0:900});
    },function(){
      here.removeAttribute('aria-busy');
      if(elCount)elCount.textContent='ยังไม่ได้บอกตำแหน่ง · no position given';
    });
  });

  /* ---- what is open, right now -----------------------------------------
     THE RULE THIS IS BUILT ON, and it is not a detail: a place with no
     opening hours on record is NOT closed. Most places here have never told
     anybody their hours, and a map that dimmed them would be publishing a
     claim about several thousand businesses that nobody made. So this
     EMPHASISES what we know is open and touches nothing else — no dot is
     ever hidden or dimmed by it — and the counter says how many places that
     is, so the reader can see for themselves how partial the knowledge is.

     The schedules are the same file the lamp map reads: intervals in minutes
     from Monday midnight, so "now" is one sum in the reader's own clock and
     no request to anybody. */
  var openBtn=document.getElementById('xopen'),openIds=null,openOn=false;
  function weekMinute(){
    var d=new Date();
    return ((d.getDay()+6)%7)*1440+d.getHours()*60+d.getMinutes();
  }
  function markOpen(){
    Object.keys(loaded).forEach(function(k){
      var id=srcId(k)+'-open';
      if(!map.getLayer(id))return;
      map.setFilter(id,(openOn&&openIds&&openIds.length)
        ?['in',['get','id'],['literal',openIds]]:['==',['literal',0],1]);
    });
  }
  function openLayerFor(k){
    var id=srcId(k);
    if(map.getLayer(id+'-open'))return;
    /* A ring around the dot rather than a different colour: the colour is
       already saying which shelf this is, and a mark may only carry one
       meaning at a time. Added under the dot so the dot stays on top. */
    map.addLayer({id:id+'-open',type:'circle',source:id,
      filter:['==',['literal',0],1],paint:{
        'circle-radius':['interpolate',['linear'],['zoom'],10,5.5,14,8.5,17,12],
        'circle-color':'rgba(0,0,0,0)',
        'circle-stroke-color':'#1F6B57','circle-stroke-width':2.2,
        'circle-stroke-opacity':.9}},id+'-dot');
  }
  function loadOpen(then){
    if(openIds)return then&&then();
    fetch(root()+'data/open_lamps.json').then(function(r){return r.json();})
      .then(function(d){
        var now=weekMinute(),ids=[];
        (d.places||[]).forEach(function(p){
          var s=(d.schedules||[])[p.k];
          if(!s)return;
          for(var i=0;i<s.length;i++){
            if(now>=s[i][0]&&now<s[i][1]){ids.push(p.id);break;}
          }
        });
        openIds=ids;
        if(then)then();
      }).catch(function(){openIds=[];if(then)then();});
  }
  if(openBtn)openBtn.addEventListener('click',function(){
    openOn=!openOn;
    openBtn.setAttribute('aria-pressed',openOn?'true':'false');
    if(!openOn){markOpen();if(elCount)elCount.textContent='';return;}
    openBtn.setAttribute('aria-busy','true');
    loadOpen(function(){
      openBtn.removeAttribute('aria-busy');
      Object.keys(loaded).forEach(openLayerFor);
      markOpen();
      if(elCount)elCount.textContent=openIds.length
        ? ('วงเขียว = รู้ว่าเปิดอยู่ '+openIds.length.toLocaleString()+
           ' แห่ง · green ring = known open; the rest have never said')
        : 'ยังไม่รู้เวลาเปิดของที่ไหนตอนนี้ · no hours on record for now';
    });
  });

  /* ---- send this view ---------------------------------------------------
     A link is the better thing to send and the page already makes one. But a
     link pasted into a LINE chat does not unfurl, and the picture is what
     people actually look at — the same reasoning that put a share card on
     every shelf. So this hands over the view itself: what is on screen, the
     shelves named along the bottom, and the ODbL credit drawn INTO the
     pixels, because a picture travels with no page around it.

     Offered only where the browser can actually pass a file to another app.
     A button that silently does nothing is worse than no button, so it is
     hidden until canShare says yes. */
  var shot=document.getElementById('xshot');
  function canShareFiles(){
    try{return !!(navigator.canShare&&navigator.canShare(
      {files:[new File([new Blob([1])],'a.png',{type:'image/png'})]}));}
    catch(e){return false;}
  }
  if(shot&&canShareFiles()){
    shot.hidden=false;
    shot.addEventListener('click',function(){
      shot.setAttribute('aria-busy','true');
      var src=map.getCanvas();
      var w=src.width,h=src.height,r=(window.devicePixelRatio||1);
      var band=Math.round(46*r);
      var c=document.createElement('canvas');
      c.width=w;c.height=h+band;
      var x=c.getContext('2d');
      x.fillStyle='#FBF6EC';x.fillRect(0,0,c.width,c.height);
      x.drawImage(src,0,0);
      /* The band under the picture: what these dots are, then who the map
         belongs to. Both are conditions of using this data, not decoration. */
      x.fillStyle='#FFFDF8';x.fillRect(0,h,w,band);
      x.fillStyle='#2A1E16';
      x.font='700 '+Math.round(15*r)+'px system-ui,sans-serif';
      var names=on.map(function(k){
        var b=document.querySelector('.xchip[data-x="'+k+'"]');
        return b?b.textContent.replace(/\s+/g,' ').replace(/[\d,]+$/,'').trim():k;});
      x.fillText(('มดแดง · motdang.net'+(names.length?' — '+names.join(', '):''))
        .slice(0,90),Math.round(10*r),h+Math.round(19*r));
      x.fillStyle='#6B5A48';
      x.font=Math.round(12*r)+'px system-ui,sans-serif';
      x.fillText('© OpenStreetMap contributors (ODbL)',Math.round(10*r),h+Math.round(37*r));
      c.toBlob(function(b){
        shot.removeAttribute('aria-busy');
        if(!b)return;
        var f=new File([b],'motdang-map.png',{type:'image/png'});
        navigator.share({files:[f],title:'มดแดง · Mot Dang',
          text:location.href}).catch(function(){});
      },'image/png');
    });
  }

  map.on('moveend',function(){writeHash(map);});
  wireTap();
  on.slice().forEach(function(k){load(k);});
  paintChips();
  writeHash(map);
});
})();
