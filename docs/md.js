
const B=document.body,btn=document.querySelector('.langbtn');
if(localStorage.getItem('md-lang')==='en')B.classList.add('lang-en');
btn&&btn.addEventListener('click',()=>{B.classList.toggle('lang-en');
localStorage.setItem('md-lang',B.classList.contains('lang-en')?'en':'th');});
const logo=document.querySelector('.logo .ant'),ant=document.getElementById('scurry');
logo&&ant&&logo.closest('.logo').addEventListener('click',e=>{
if(e.detail&&location.pathname.endsWith('/')&&!location.pathname.match(/\/(cm|cr)\//)){}
ant.classList.remove('go');void ant.offsetWidth;ant.classList.add('go');});
