import re

with open('share_layer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Modify sendRow definition
# sendRow(text) -> sendRow(text, ll, addr, name)
new_sendRow = """function sendRow(text, ll, addr, name){
  var u=ll?'https://www.google.com/maps/search/?api=1&query='+ll:'';
  var d_url=u?' data-ls-url="'+E(u)+'"':'';
  var d_ll=ll?' data-ls-ll="'+E(ll)+'"':'';
  var d_addr=addr?' data-ls-addr="'+E(addr)+'"':'';
  var d_name=name?' data-ls-name="'+E(name)+'"':'';
  var geo=ll?'geo:'+ll+'?q='+ll+(name?'('+E(name)+')':''):'';
  return '<div class="ls-send" data-ls-text="'+E(text)+'"'+d_url+d_ll+d_addr+d_name+'>'+
    (canShare()?'<button type="button" class="ls-b" data-ls-native>'+I('i-share')+B('แชร์','Share')+'</button>':'')+
    '<a class="ls-b ls-line" href="'+E(lineHref(text))+'" target="_blank" rel="noopener">'+I('i-chat')+'LINE</a>'+
    '<a class="ls-b ls-wa" href="'+E(waHref(text))+'" target="_blank" rel="noopener">'+I('i-chat')+'WhatsApp</a>'+
    '<a class="ls-b ls-mail" href="'+E(mailHref(text))+'">'+I('i-mail')+B('อีเมล','Email')+'</a>'+
    '<button type="button" class="ls-b" data-ls-copy>'+I('i-link')+B('คัดลอกข้อความ','Copy text')+'</button>'+
    (ll?'<button type="button" class="ls-b" data-ls-copy-ll>'+I('i-link')+B('คัดลอกพิกัด','Copy coordinates')+'</button>':'')+
    (addr?'<button type="button" class="ls-b" data-ls-copy-addr>'+I('i-link')+B('คัดลอกที่อยู่','Copy address')+'</button>':'')+
    (ll?'<a class="ls-b ls-alt" href="'+geo+'">'+I('i-ride')+B('เปิดแอปแผนที่ / เรียกจ้าง','Geo URI / Apps')+'</a>':'')+
    (ll?'<a class="ls-b ls-alt" href="'+E(u)+'" rel="noopener" target="_blank">'+I('i-map')+B('เปิดใน Google Maps','Open in Google Maps')+'</a>':'')+
    '</div>';}"""

content = re.sub(r'function sendRow\(text\)\{[\s\S]*?\}', new_sendRow, content)

# update click listener for the new copy buttons
new_click = """  var t=msgOf(b), p=b.closest('.ls-send'), u=p?p.getAttribute('data-ls-url'):null;
  if(b.hasAttribute('data-ls-copy')){tell('channel',{d:'copy'});copy(tagged(t,'copy'),b);return;}
  if(b.hasAttribute('data-ls-copy-ll')){tell('channel',{d:'copy-ll'});copy(p.getAttribute('data-ls-ll'),b);return;}
  if(b.hasAttribute('data-ls-copy-addr')){tell('channel',{d:'copy-addr'});copy(p.getAttribute('data-ls-addr'),b);return;}
  shareOut(t,pickFile(),open('pick')?'part':'page',u);});"""

content = content.replace("""  var t=msgOf(b);
  if(b.hasAttribute('data-ls-copy')){tell('channel',{d:'copy'});copy(tagged(t,'copy'),b);return;}
  shareOut(t,pickFile(),open('pick')?'part':'page');});""", new_click)


# update shareOut to take u
content = content.replace("""function shareOut(t,file,what){
  t=tagged(t,'native');tell('channel',{d:'native'});
  if(APP){try{APP.share(t);}catch(e){}return;}
  if(file)file.then(function(f){var d={text:t,files:[f]};
      return navigator.canShare&&navigator.canShare(d)?nativeShare(d,what||'file'):nativeShare({text:t},what);}).catch(function(){});
  else nativeShare({text:t},what);}""", """function shareOut(t,file,what,u){
  t=tagged(t,'native');tell('channel',{d:'native'});
  if(APP){try{APP.share(t);}catch(e){}return;}
  if(file)file.then(function(f){var d={text:t,files:[f]};if(u)d.url=u;
      return navigator.canShare&&navigator.canShare(d)?nativeShare(d,what||'file'):nativeShare(u?{text:t,url:u}:{text:t},what);}).catch(function(){});
  else nativeShare(u?{text:t,url:u}:{text:t},what);}""")

with open('share_layer.py', 'w', encoding='utf-8') as f:
    f.write(content)
