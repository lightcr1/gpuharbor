(function(){
  var links=[].slice.call(document.querySelectorAll('nav a[href^="#"]'));
  var sections=[].slice.call(document.querySelectorAll('main section[id]'));
  if(!sections.length)return;
  function setActive(id){links.forEach(function(a){a.classList.toggle('active',a.getAttribute('href')==='#'+id);});}
  function onScroll(){
    var threshold=140,current=sections[0].id;
    sections.forEach(function(s){if(s.getBoundingClientRect().top<=threshold)current=s.id;});
    setActive(current);
  }
  window.addEventListener('scroll',onScroll,{passive:true});
  window.addEventListener('resize',onScroll);
  window.addEventListener('hashchange',onScroll);
  onScroll();
})();
(function(){
  function apply(value){
    var t=(value==='runpod'||value==='light')?value:'blue';
    document.documentElement.dataset.theme=t;
    try{localStorage.setItem('gh-theme',t)}catch(e){}
    var buttons=document.querySelectorAll('.themes button');
    for(var i=0;i<buttons.length;i++)buttons[i].classList.toggle('active',buttons[i].dataset.theme===t);
  }
  window.setTheme=apply;
  document.querySelectorAll('.themes button').forEach(function(b){b.addEventListener('click',function(){apply(b.dataset.theme)})});
  apply(document.documentElement.dataset.theme||'blue');
})();
