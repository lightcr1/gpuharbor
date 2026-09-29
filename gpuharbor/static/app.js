const I18N={
en:{
 "app.subtitle":"RunPod model control","nav.docs":"Documentation","nav.logout":"Sign out","nav.settings":"Settings",
 "pill.billable_on":"Billable actions ENABLED","pill.billable_off":"Cost lock active",
 "pill.update":"Update available: ","pill.update_title":"Open the release page",
 "settings.title":"Settings","settings.updates":"Updates","settings.notifications":"Show update notifications","settings.notifications_hint":"When on, GPUHarbor asks the public GitHub releases API once a day and shows a link when a newer version exists. Only that request leaves the machine; no token is sent.","settings.saved":"Saved.","settings.close":"Close","settings.appearance":"Appearance","settings.theme_blue":"Harbor blue","settings.theme_light":"Harbor light","settings.theme_runpod":"RunPod violet","settings.theme_hint":"Applies to the dashboard and the documentation.",
 "login.subtitle":"Sign in to the local controller.","login.username":"Username","login.password":"Password","login.button":"Sign in","login.failed":"Sign-in failed.",
 "start.title":"Start a model","start.model":"Model profile","start.region":"Region","start.datacenter":"Datacenter (advanced)",
 "start.auto_region":"Automatic","start.auto_dc":"Automatic","start.auto_gpu":"Automatic by priority",
 "field.context":"Context (tokens)","field.sequences":"Parallel sequences","field.memory":"GPU utilisation (0–1)","field.volume":"Volume (GB)","field.gpu":"GPU",
 "hint.context":"Maximum length of one request. More uses more VRAM.","hint.sequences":"Requests handled at the same time.",
 "hint.memory":"Share of VRAM the runtime may use.","hint.volume":"Space for the model cache.","hint.gpu":"Only GPUs allowed by this profile.",
 "btn.plan":"Check launch plan","btn.preflight":"Check availability","btn.start":"Start pod","btn.stop":"Stop","btn.delete":"Delete pod and volume",
 "btn.save":"Save","btn.cancel":"Cancel","btn.delete_profile":"Delete profile","btn.reset":"Reset to default",
 "lookup.button":"Look up on Hugging Face","lookup.busy":"Looking up …","lookup.found":"Found: ","lookup.failed":"Lookup failed: ","lookup.gguf":"GGUF files: ",
 "output.title":"Output","output.simple":"Simple","output.pretty":"Pretty","output.raw":"Raw","output.ready":"Ready. Billable actions are locked by default.","output.wait":"Please wait …",
 "status.title":"Status","status.loading":"Loading …","status.refresh":"Refresh","status.none":"No managed pod","status.error":"Error: ",
 "ready.unknown":"Model status unknown","ready.none":"No pod — model status n/a","ready.loaded":"Model loaded","ready.loading":"Model loading …","ready.label":"Model status",
 "catalog.title":"Model catalog","catalog.hint":"Shipped profiles survive upgrades; your profiles and overrides are stored separately.",
 "catalog.new":"New model","catalog.edit":"Edit selected","catalog.export":"Export","catalog.import":"Import",
 "integrations.title":"Optional integrations","integrations.hint":"Enabled through separate Compose files. Details are in the documentation.",
 "runtimes.title":"Runtime images","runtimes.ready":"ready","runtimes.missing":"no digest configured",
 "editor.new_title":"New model profile","editor.edit_title":"Edit model","editor.preset":"Template",
 "gpu.loading":"Loading catalog …","gpu.none":"No GPU catalog available — use the text field below.",
 "field.id":"ID","field.name":"Name","field.description":"Description","field.model_id":"Hugging Face repository","field.runtime":"Runtime",
 "field.gguf":"GGUF file","field.aliases":"Served names (comma)","field.capabilities":"Capabilities (comma)","field.gpus":"Allowed GPUs","field.volume_gb":"Volume GB",
 "field.gpus_extra":"Other GPUs (one per line)","field.license":"License","field.status":"Status","field.gated":"Restricted access (gated)",
 "field.verified":"Verified on a real GPU","field.trust":"Trust Hugging Face remote code","field.reasoning":"Qwen3 reasoning parser","field.tools":"Qwen3 tool parser and auto tool choice",
 "hint.id":"Lowercase letters, digits and hyphen. Cannot be changed later.","hint.name":"Display name.",
 "hint.model_id":"For example Qwen/Qwen3.8-27B-FP8.","hint.runtime":"vLLM for FP8/BF16, llama.cpp for GGUF.",
 "hint.gguf":"GGUF runtimes only: the exact filename from the repository.","hint.aliases":"For example default, chat, code.",
 "hint.capabilities":"chat, code, tools, vision — labels only.","hint.gpus":"Only these GPUs may run the profile. Availability comes from the RunPod catalog.",
 "hint.gpus_extra":"For GPUs missing from the catalog, use the exact RunPod name.","hint.license":"Display only, for example Apache-2.0.",
 "hint.status":"disabled means it cannot start.","hint.preset":"Fills in sensible starting values. Everything stays editable.",
 "hint.vllm":"\"Trust remote code\" runs Python shipped inside the model repository. Only enable it for repositories you trust.",
 "vllm.title":"vLLM options",
 "tip.trust":"Runs model-supplied Python on the pod","tip.reasoning":"Splits thinking into the reasoning field","tip.tools":"Lets the model emit tool calls",
 "confirm.start":"Start the pod? Depending on your settings this begins GPU billing immediately.",
 "confirm.delete":"Delete the pod and its volume? The model cache is lost, but all costs stop.",
 "confirm.remove":"Delete profile {id}?","confirm.reset":"Discard your changes to {id} and restore the shipped default?",
 "confirm.import":"Merge profiles and overrides from this file?",
 "msg.imported":"Model catalog imported.","msg.export_error":"Export failed: ","msg.import_error":"Import failed: ","msg.error":"Error: ",
 "sum.plan":"Launch plan","sum.billable":"Billable actions: ","sum.allowed":"allowed","sum.locked":"locked","sum.candidates":"Candidates: ",
 "sum.first":"First choice: ","sum.config_errors":"Configuration errors: ","sum.none":"none",
 "sum.preflight":"Availability (free, nothing started)","sum.pods":"Pods in the account: ",
 "sum.ready":"Model ready: ","sum.yes":"yes","sum.no":"no","sum.pod":"Pod: ","sum.status":"Status: ","sum.model":"Model: ",
 "cost.single":"About {price} $/h while the pod runs.","cost.range":"About {min}–{max} $/h while the pod runs, depending on the GPU.","cost.unknown":"No price available.","cost.estimate":" (estimate; the live RunPod catalog is not reachable)",
 "badge.stable":"stable","badge.experimental":"experimental","badge.disabled":"disabled","badge.builtin":"built-in","badge.custom":"custom","badge.override":"override","badge.orphaned-override":"orphaned override","badge.gated":"gated","badge.verified":"verified","badge.unverified":"not verified",
 "sum.no_pod":"No managed pod."
},
de:{
 "app.subtitle":"RunPod-Modellsteuerung","nav.docs":"Dokumentation","nav.logout":"Abmelden","nav.settings":"Einstellungen",
 "pill.billable_on":"Kostenpflichtig AKTIV","pill.billable_off":"Kostensperre aktiv",
 "pill.update":"Update verfügbar: ","pill.update_title":"Release-Seite öffnen",
 "settings.title":"Einstellungen","settings.updates":"Updates","settings.notifications":"Update-Hinweise anzeigen","settings.notifications_hint":"Wenn aktiv, fragt GPUHarbor einmal täglich die öffentliche GitHub-Releases-API und zeigt einen Link, wenn eine neuere Version existiert. Nur diese Anfrage verlässt den Rechner; kein Token wird gesendet.","settings.saved":"Gespeichert.","settings.close":"Schließen","settings.appearance":"Design","settings.theme_blue":"Harbor-Blau","settings.theme_light":"Harbor-Hell","settings.theme_runpod":"RunPod-Lila","settings.theme_hint":"Gilt für Dashboard und Dokumentation.",
 "login.subtitle":"Am lokalen Controller anmelden.","login.username":"Benutzername","login.password":"Passwort","login.button":"Anmelden","login.failed":"Anmeldung fehlgeschlagen.",
 "start.title":"Modell starten","start.model":"Modellprofil","start.region":"Region","start.datacenter":"Rechenzentrum (erweitert)",
 "start.auto_region":"Automatisch","start.auto_dc":"Automatisch","start.auto_gpu":"Automatisch nach Priorität",
 "field.context":"Kontext (Token)","field.sequences":"Parallele Sequenzen","field.memory":"GPU-Nutzung (0–1)","field.volume":"Volume (GB)","field.gpu":"GPU",
 "hint.context":"Maximale Länge einer Anfrage. Mehr braucht mehr VRAM.","hint.sequences":"Gleichzeitig bearbeitete Anfragen.",
 "hint.memory":"Anteil des VRAM, den die Runtime nutzen darf.","hint.volume":"Speicher für den Modell-Cache.","hint.gpu":"Nur GPUs, die dieses Profil erlaubt.",
 "btn.plan":"Startplan prüfen","btn.preflight":"Verfügbarkeit prüfen","btn.start":"Pod starten","btn.stop":"Stoppen","btn.delete":"Pod & Volume löschen",
 "btn.save":"Speichern","btn.cancel":"Abbrechen","btn.delete_profile":"Profil löschen","btn.reset":"Auf Standard zurücksetzen",
 "lookup.button":"Bei Hugging Face nachsehen","lookup.busy":"Suche läuft …","lookup.found":"Gefunden: ","lookup.failed":"Suche fehlgeschlagen: ","lookup.gguf":"GGUF-Dateien: ",
 "output.title":"Ausgabe","output.simple":"Einfach","output.pretty":"Schön","output.raw":"Roh","output.ready":"Bereit. Kostenpflichtige Aktionen sind standardmäßig gesperrt.","output.wait":"Bitte warten …",
 "status.title":"Status","status.loading":"Wird geladen …","status.refresh":"Aktualisieren","status.none":"Kein Pod verwaltet","status.error":"Fehler: ",
 "ready.unknown":"Modellstatus unbekannt","ready.none":"Kein Pod — Modellstatus n/a","ready.loaded":"Modell geladen","ready.loading":"Modell lädt …","ready.label":"Modellstatus",
 "catalog.title":"Modellkatalog","catalog.hint":"Mitgelieferte Profile überleben Updates; eigene Profile und Anpassungen liegen getrennt.",
 "catalog.new":"Neues Modell","catalog.edit":"Gewähltes bearbeiten","catalog.export":"Exportieren","catalog.import":"Importieren",
 "integrations.title":"Optionale Integrationen","integrations.hint":"Über getrennte Compose-Dateien aktivierbar. Details stehen in der Dokumentation.",
 "runtimes.title":"Runtime-Images","runtimes.ready":"bereit","runtimes.missing":"kein Digest konfiguriert",
 "editor.new_title":"Neues Modellprofil","editor.edit_title":"Modell bearbeiten","editor.preset":"Vorlage",
 "gpu.loading":"Katalog wird geladen …","gpu.none":"Kein GPU-Katalog verfügbar — nutze das Textfeld unten.",
 "field.id":"ID","field.name":"Name","field.description":"Beschreibung","field.model_id":"Hugging-Face-Repository","field.runtime":"Runtime",
 "field.gguf":"GGUF-Datei","field.aliases":"API-Namen (Komma)","field.capabilities":"Fähigkeiten (Komma)","field.gpus":"Erlaubte GPUs","field.volume_gb":"Volume GB",
 "field.gpus_extra":"Weitere GPUs (eine pro Zeile)","field.license":"Lizenz","field.status":"Status","field.gated":"Zugriff eingeschränkt (gated)",
 "field.verified":"Auf echter GPU geprüft","field.trust":"Hugging-Face Remote-Code vertrauen","field.reasoning":"Qwen3 Reasoning-Parser","field.tools":"Qwen3 Tool-Parser + Auto-Tool-Wahl",
 "hint.id":"Kleinbuchstaben, Zahlen und Bindestrich. Später nicht änderbar.","hint.name":"Anzeigename.",
 "hint.model_id":"Zum Beispiel Qwen/Qwen3.8-27B-FP8.","hint.runtime":"vLLM für FP8/BF16, llama.cpp für GGUF.",
 "hint.gguf":"Nur bei GGUF-Runtimes: exakter Dateiname aus dem Repository.","hint.aliases":"Zum Beispiel default, chat, code.",
 "hint.capabilities":"chat, code, tools, vision — nur Beschriftung.","hint.gpus":"Nur diese GPUs dürfen das Profil starten. Verfügbarkeit kommt aus dem RunPod-Katalog.",
 "hint.gpus_extra":"Für GPUs, die nicht im Katalog stehen: exakter RunPod-Name.","hint.license":"Nur Anzeige, zum Beispiel Apache-2.0.",
 "hint.status":"disabled bedeutet: nicht startbar.","hint.preset":"Setzt sinnvolle Startwerte. Danach frei anpassbar.",
 "hint.vllm":"„Remote-Code vertrauen“ führt Python aus dem Modell-Repository aus. Nur bei geprüften Repos aktivieren.",
 "vllm.title":"vLLM-Optionen",
 "tip.trust":"Führt modell-eigenen Python-Code auf dem Pod aus","tip.reasoning":"Trennt die Denk-Ausgabe ins Feld reasoning","tip.tools":"Erlaubt Tool-Aufrufe",
 "confirm.start":"Pod starten? Je nach Einstellung beginnt sofort die GPU-Abrechnung.",
 "confirm.delete":"Pod und Volume löschen? Der Modell-Cache geht verloren, alle Kosten enden.",
 "confirm.remove":"Profil {id} löschen?","confirm.reset":"Anpassungen an {id} verwerfen und Standard wiederherstellen?",
 "confirm.import":"Profile und Overrides aus dieser Datei zusammenführen?",
 "msg.imported":"Modellkatalog importiert.","msg.export_error":"Exportfehler: ","msg.import_error":"Importfehler: ","msg.error":"Fehler: ",
 "sum.plan":"Startplan","sum.billable":"Kosten erlaubt: ","sum.allowed":"ja","sum.locked":"nein (gesperrt)","sum.candidates":"Kandidaten: ",
 "sum.first":"Erste Wahl: ","sum.config_errors":"Konfigurationsfehler: ","sum.none":"keine",
 "sum.preflight":"Verfügbarkeit (kostenlos, nichts gestartet)","sum.pods":"Pods im Konto: ",
 "sum.ready":"Modell bereit: ","sum.yes":"ja","sum.no":"nein","sum.pod":"Pod: ","sum.status":"Status: ","sum.model":"Modell: ",
 "cost.single":"Etwa {price} $/h, solange der Pod läuft.","cost.range":"Etwa {min}–{max} $/h, solange der Pod läuft (je nach GPU).","cost.unknown":"Kein Preis verfügbar.","cost.estimate":" (Schätzwert; der Live-Katalog von RunPod ist nicht erreichbar)",
 "badge.stable":"stabil","badge.experimental":"experimentell","badge.disabled":"deaktiviert","badge.builtin":"mitgeliefert","badge.custom":"eigenes","badge.override":"angepasst","badge.orphaned-override":"verwaiste Anpassung","badge.gated":"eingeschränkt","badge.verified":"geprüft","badge.unverified":"ungeprüft",
 "sum.no_pod":"Kein Pod verwaltet."
}};

let lang=null;
try{lang=localStorage.getItem('gh-lang')}catch(e){}
if(!I18N[lang])lang=(navigator.language||'en').toLowerCase().startsWith('de')?'de':'en';
function t(key){const table=I18N[lang]||I18N.en;return table[key]||I18N.en[key]||key}
function setLang(value){
  lang=I18N[value]?value:'en';
  try{localStorage.setItem('gh-lang',lang)}catch(e){}
  applyLang();
  // Option labels are built from settings, so they have to be rebuilt too.
  loadCatalog().then(()=>{render(lastKey?t(lastKey):lastRaw);return refreshStatus()}).catch(()=>{});
}
function applyLang(){
  document.documentElement.lang=lang;
  document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.dataset.i18n)});
  document.querySelectorAll('[data-i18n-title]').forEach(el=>{el.title=t(el.dataset.i18nTitle)});
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el=>{el.placeholder=t(el.dataset.i18nPlaceholder)});
  $('lang-switch').value=lang;
  updateBillablePill();
  renderUpdatePill();
}

let gpuSource='live',models={},runtimes={},settingsData={},gpuOptions=[],regions=[],presets={},csrfToken='',podActive=false,lastRaw='',lastKey=null,updateInfo=null,theme=document.documentElement.dataset.theme||'blue';
let mode='simple';
const $=id=>document.getElementById(id), output=$('output'), editor=$('editor'), settingsDialog=$('settings');

async function api(path,options={}){
  const method=(options.method||'GET').toUpperCase();
  const csrf=csrfToken&&!['GET','HEAD','OPTIONS'].includes(method)?{'X-CSRF-Token':csrfToken}:{};
  const r=await fetch(path,{...options,headers:{'Content-Type':'application/json',...csrf,...(options.headers||{})}});
  const text=await r.text();let data;
  try{data=JSON.parse(text)}catch{data=text}
  if(r.status===401&&path!=='/api/login'&&csrfToken){csrfToken='';showLogin()}
  if(!r.ok)throw new Error(typeof data==='object'?JSON.stringify(data.detail??data):data);
  return data;
}
function showLogin(){
  $('app').classList.add('hidden');$('login').classList.remove('hidden');
  $('login-error').textContent='';$('password').value='';
}
function updateBillablePill(){
  const on=!!settingsData.billable_actions_enabled;
  $('billable-pill').textContent=on?t('pill.billable_on'):t('pill.billable_off');
  $('billable-pill').className='pill '+(on?'danger-text':'ok');
}
function renderUpdatePill(){
  const a=$('update-pill');
  if(!updateInfo||!updateInfo.update_available){a.classList.add('hidden');return}
  a.textContent=t('pill.update')+(updateInfo.latest||'');
  a.title=t('pill.update_title');
  a.href=/^https:\/\//.test(updateInfo.url||'')?updateInfo.url:'#';
  a.classList.remove('hidden');
}
async function checkUpdate(){
  if(!settingsData.update_check_enabled){updateInfo=null;renderUpdatePill();return}
  try{updateInfo=await api('/api/update-check')}catch{updateInfo=null}
  renderUpdatePill();
}
async function openSettings(){
  try{const s=await api('/api/settings');$('set-update-notifications').checked=!!s.update_notifications}catch{}
  $('settings-saved').textContent='';
  const el=document.querySelector('input[name="theme"][value="'+theme+'"]');if(el)el.checked=true;
  settingsDialog.showModal();
}
function setTheme(value){
  theme=['runpod','light'].includes(value)?value:'blue';
  try{localStorage.setItem('gh-theme',theme)}catch(e){}
  document.documentElement.dataset.theme=theme;
  const el=document.querySelector('input[name="theme"][value="'+theme+'"]');if(el)el.checked=true;
}
function showSettingsTab(name,button){
  for(const b of document.querySelectorAll('.settings-tab'))b.classList.toggle('active',b===button);
  $('settings-updates').classList.toggle('hidden',name!=='updates');
  $('settings-design').classList.toggle('hidden',name!=='design');
}
async function saveUpdateSetting(){
  const value=$('set-update-notifications').checked;
  try{
    await api('/api/settings',{method:'PUT',body:JSON.stringify({update_notifications:value})});
    settingsData.update_check_enabled=value;
    updateInfo=null;renderUpdatePill();
    if(value)checkUpdate();
    $('settings-saved').textContent=t('settings.saved');
  }catch(err){$('settings-saved').textContent=t('msg.error')+err.message}
}
function showMessage(key){lastKey=key;render(t(key))}
function setMode(m){mode=m;for(const n of ['simple','pretty','raw'])$('mode-'+n).classList.toggle('active',n===m);render(lastRaw)}
function render(text){
  lastRaw=text;
  if(mode==='raw'){output.textContent=text;return}
  if(mode==='pretty'){try{output.textContent=JSON.stringify(JSON.parse(text),null,2)}catch{output.textContent=text}return}
  output.textContent=summarize(text);
}
function summarize(text){
  let d;try{d=JSON.parse(text)}catch{return text}
  if(!d||typeof d!=='object')return text;
  if(d.pod_id)return t('sum.pod')+(d.pod_id||'?')+"\n"+t('sum.status')+(d.status||'?')+"\n"+t('sum.model')+(d.model_id||'?');
  if(d.candidates){
    const c=d.candidates[0]||{};
    return t('sum.plan')+"\n"+t('sum.billable')+(d.billable_actions_enabled?t('sum.allowed'):t('sum.locked'))+
      "\n"+t('sum.candidates')+d.candidates.length+"\n"+t('sum.first')+(c.gpu_type_id||'?')+" / "+(c.datacenter_id||'?')+
      "\n"+t('sum.config_errors')+(((d.configuration_errors||[]).join('; '))||t('sum.none'));
  }
  if(d.gpu_catalog){
    const rows=d.gpu_catalog.map(g=>(g.id||g.name)+": "+(g.availability||'?'));
    return t('sum.preflight')+"\n"+t('sum.pods')+(d.pods_total??'-')+"\n"+rows.join("\n");
  }
  if('ready' in d)return t('sum.ready')+(d.ready?t('sum.yes'):t('sum.no'))+"\n"+(d.detail||'');
  if(d.pod)return t('sum.pod')+(d.pod.id||'?')+"\n"+t('sum.status')+(d.pod.status||'?')+"\n"+t('sum.model')+(d.model_id||'?');
  if(d.pod===null)return t('sum.no_pod');
  if(d.ok!==undefined)return d.ok?t('msg.imported'):JSON.stringify(d);
  return text;
}
async function action(path,method='POST',body=null){
  showMessage('output.wait');
  const buttons=[...document.querySelectorAll('.actions button')];
  buttons.forEach(b=>b.disabled=true);
  try{
    const data=await api(path,{method,body:body?JSON.stringify(body):undefined});
    lastKey=null;
    render(typeof data==='string'?data:JSON.stringify(data));
    await refreshStatus();
    return data;
  }catch(err){lastKey=null;render(t('msg.error')+err.message);return null}
  finally{buttons.forEach(b=>{if(b.id!=='remove-model')b.disabled=false})}
}
$('login-form').onsubmit=async e=>{e.preventDefault();
  try{await api('/api/login',{method:'POST',body:JSON.stringify({username:$('username').value,password:$('password').value})});await boot()}
  catch(err){$('login-error').textContent=t('login.failed')+' '+err.message}};
async function boot(){
  applyLang();
  showMessage('output.ready');
  const me=await api('/api/me');
  if(!me.authenticated)return;
  csrfToken=me.csrf_token;
  $('login').classList.add('hidden');$('app').classList.remove('hidden');
  await loadCatalog();
  await Promise.all([loadStatus(),loadReady()]);
}
async function logout(){await api('/api/logout',{method:'POST'});location.reload()}

async function loadCatalog(){
  const [m,r,s,g,reg,p]=await Promise.all([
    api('/api/models'),api('/api/runtimes'),api('/api/controller-settings'),
    api('/api/gpu-options'),api('/api/regions'),api('/api/model-presets')]);
  models=m;runtimes=r;settingsData=s;gpuOptions=g.gpus||[];gpuSource=g.source||'live';regions=reg.regions||[];presets=p;
  const old=$('model').value;
  $('model').replaceChildren();
  for(const [id,mm] of Object.entries(models)){
    const o=document.createElement('option');o.value=id;
    o.textContent=mm.name+' · '+(runtimes[mm.runtime]?.label||mm.runtime)+(mm.verified?' ✓':'');
    $('model').append(o);
  }
  $('model').value=models[old]?old:(Object.keys(models).find(id=>models[id].active)||Object.keys(models)[0]||'');
  $('region').replaceChildren(new Option(t('start.auto_region'),''));
  for(const item of regions){const o=document.createElement('option');o.value=item.id;o.textContent=item.label;$('region').append(o)}
  $('e-runtime').replaceChildren();
  for(const [id,rr] of Object.entries(runtimes)){const o=document.createElement('option');o.value=id;o.textContent=rr.label;$('e-runtime').append(o)}
  $('e-preset').replaceChildren(new Option('— '+t('editor.preset')+' —',''));
  for(const [id,pp] of Object.entries(presets)){const o=document.createElement('option');o.value=id;o.textContent=pp.label;$('e-preset').append(o)}
  $('version-label').textContent=settingsData.version?'v'+settingsData.version:'';
  updateBillablePill();
  checkUpdate();
  renderRuntimes();
  renderGpuOptions();
  regionChanged();
  selectModel();
}
function renderGpuOptions(selected){
  const list=$('e-gpu-list');list.replaceChildren();
  const chosen=new Set(selected||[]);
  if(!gpuOptions.length){const span=document.createElement('span');span.className='hint';span.textContent=t('gpu.none');list.append(span);return}
  for(const g of gpuOptions){
    const id=g.id||g.name;if(!id)continue;
    const label=document.createElement('label');
    const cb=document.createElement('input');cb.type='checkbox';cb.value=id;cb.checked=chosen.has(id);
    const mem=g.memory?g.memory+' GB':'';
    const price=g.secure_price!=null?' · '+g.secure_price+' $/h':'';
    const avail=g.availability?' · '+g.availability:'';
    label.append(cb,document.createTextNode(' '+(g.name||id)+' ('+mem+price+avail+')'));
    list.append(label);
  }
}
function renderRuntimes(){
  const list=$('runtime-list');list.replaceChildren();
  for(const [id,rt] of Object.entries(runtimes)){
    const line=document.createElement('div');line.className='runtime';
    const dot=document.createElement('span');dot.className='dot '+(rt.ready?'ok':'bad');
    const info=document.createElement('span');info.className='hint';
    const digest=(rt.image||'').split('@')[1];
    info.textContent=(rt.ready?t('runtimes.ready'):t('runtimes.missing'))+(digest?' · '+digest.slice(0,19)+'…':'');
    line.append(dot,document.createTextNode(rt.label+' '),info);
    list.append(line);
  }
}
function regionChanged(){
  const selected=$('region').value;
  $('datacenter').replaceChildren(new Option(t('start.auto_dc'),''));
  const source=selected?regions.find(r=>r.id===selected):null;
  const dcs=source?source.datacenters:(settingsData.datacenter_ids||[]);
  for(const dc of dcs)$('datacenter').append(new Option(dc,dc));
  $('datacenter').disabled=!dcs.length;
}
function selectModel(){
  const m=models[$('model').value];
  if(!m)return;
  $('model-description').textContent=m.description||'';
  $('badges').replaceChildren();
  [t('badge.'+m.status),m.license,t('badge.'+m.source),m.overridden?t('badge.override'):null,m.gated?t('badge.gated'):null,
   m.verified?t('badge.verified'):t('badge.unverified'),runtimes[m.runtime]?.label]
   .filter(Boolean).forEach(x=>{const s=document.createElement('span');s.className='pill';s.textContent=x;$('badges').append(s)});
  $('context').value=m.context_length;
  $('sequences').value=m.max_sequences;
  $('memory').value=m.gpu_memory_utilization;
  $('volume').value=m.volume_gb;
  $('gpu').replaceChildren(new Option(t('start.auto_gpu'),''));
  (m.gpu_type_ids||[]).forEach(g=>$('gpu').append(new Option(g,g)));
  updateCost();
}
function updateCost(){
  const m=models[$('model').value],el=$('gpu-cost');
  if(!m){el.textContent='';return}
  const chosen=$('gpu').value?[$('gpu').value]:(m.gpu_type_ids||[]);
  const prices=chosen.map(id=>gpuOptions.find(g=>g.id===id)?.secure_price).filter(p=>typeof p==='number');
  if(!prices.length){el.textContent=t('cost.unknown');return}
  const lo=Math.min(...prices),hi=Math.max(...prices),fmt=n=>n.toFixed(2);
  el.textContent=(lo===hi?t('cost.single').replace('{price}',fmt(lo)):t('cost.range').replace('{min}',fmt(lo)).replace('{max}',fmt(hi)))+(gpuSource==='live'?'':t('cost.estimate'));
}
function launch(){
  return {
    model_id:$('model').value,
    context_length:+$('context').value,
    max_sequences:+$('sequences').value,
    gpu_memory_utilization:+$('memory').value,
    gpu_type_id:$('gpu').value||null,
    datacenter_id:$('datacenter').value||null,
    region:$('region').value||null,
    volume_gb:+$('volume').value
  };
}
const plan=()=>action('/api/pod/plan','POST',launch());
const preflight=()=>action('/api/runpod/preflight','POST',launch());
async function startPod(){if(!confirm(t('confirm.start')))return;await action('/api/pod/start','POST',launch())}
const stopPod=()=>action('/api/pod/stop');
async function deletePod(){if(confirm(t('confirm.delete')))await action('/api/pod','DELETE')}
function setLine(el,state,text){
  const dot=document.createElement('span');dot.className='dot'+(state?' '+state:'');
  el.replaceChildren(dot,document.createTextNode(text));
}
async function loadStatus(){
  try{
    const s=await api('/api/status');
    podActive=!!s.pod;
    const label=s.pod?((s.pod.status||'UNKNOWN')+(s.model_id?' · '+s.model_id:'')):t('status.none');
    setLine($('status'),s.pod?'ok':'',label);
    return s;
  }catch(err){setLine($('status'),'bad',t('status.error')+err.message)}
}
async function loadReady(){
  if(!podActive){setLine($('ready'),'',t('ready.none'));return}
  try{
    const d=await api('/api/model/ready');
    setLine($('ready'),d.ready?'ok':'wait',(d.ready?t('ready.loaded'):t('ready.loading'))+(d.detail?' — '+d.detail:''));
  }catch(err){setLine($('ready'),'bad',t('ready.unknown')+': '+err.message)}
}
async function refreshStatus(){await loadStatus();await loadReady()}
function fillEditor(id,m){
  $('editor-error').textContent='';
  $('editor-title').textContent=m?(t('editor.edit_title')+': '+(m.name||id)):t('editor.new_title');
  $('e-id').value=id||'';$('e-id').disabled=!!id;
  $('e-name').value=m?.name||'';
  $('e-description').value=m?.description||'';
  $('e-model-id').value=m?.model_id||'';
  $('e-runtime').value=m?.runtime||'vllm';
  $('e-gguf').value=m?.gguf_file||'';
  $('e-aliases').value=(m?.served_names||[]).join(', ');
  $('e-capabilities').value=(m?.capabilities||[]).join(', ');
  $('e-context').value=m?.context_length||32768;
  $('e-sequences').value=m?.max_sequences||2;
  $('e-memory').value=m?.gpu_memory_utilization||0.9;
  $('e-volume').value=m?.volume_gb||64;
  $('e-license').value=m?.license||'unknown';
  $('e-status').value=m?.status||'experimental';
  $('e-gated').checked=!!m?.gated;
  $('e-verified').checked=!!m?.verified;
  $('e-trust-remote-code').checked=!!m?.trust_remote_code;
  $('e-reasoning').checked=!!m?.reasoning_parser;
  $('e-tools').checked=!!m?.tool_call_parser;
  $('e-preset').value='';
  const known=new Set(gpuOptions.map(g=>g.id));
  const allowed=m?.gpu_type_ids||[];
  renderGpuOptions(allowed);
  $('e-gpus').value=allowed.filter(g=>!known.has(g)).join('\n');
  const removable=!!m&&(m.source==='custom'||m.source==='orphaned-override'||m.overridden);
  $('remove-model').disabled=!removable;
  $('remove-model').textContent=m?.overridden?t('btn.reset'):t('btn.delete_profile');
  runtimeChanged();
  editor.showModal();
}
const newModel=()=>fillEditor('',null);
function editModel(){const id=$('model').value;if(id)fillEditor(id,models[id])}
async function lookupModel(){
  const repo=$('e-model-id').value.trim();
  const result=$('lookup-result');
  if(!repo){result.textContent='';return}
  result.textContent=t('lookup.busy');
  try{
    const d=await api('/api/model-suggest',{method:'POST',body:JSON.stringify({model_id:repo})});
    if(d.suggested_runtime)$('e-runtime').value=d.suggested_runtime;
    if(d.context_length)$('e-context').value=d.context_length;
    if(d.suggested_volume_gb)$('e-volume').value=d.suggested_volume_gb;
    if(d.license&&d.license!=='unknown')$('e-license').value=d.license;
    $('e-gated').checked=!!d.gated;
    if(d.gguf_files&&d.gguf_files.length)$('e-gguf').value=d.gguf_files[0];
    const known=new Set(gpuOptions.map(g=>g.id));
    const suggested=d.suggested_gpus||[];
    $('e-gpu-list').querySelectorAll('input').forEach(cb=>{cb.checked=suggested.includes(cb.value)});
    $('e-gpus').value=suggested.filter(g=>!known.has(g)).join('\n');
    runtimeChanged();
    const parts=[t('lookup.found')+(d.model_id||repo)];
    if(d.estimated_size_gb)parts.push(d.estimated_size_gb+' GB');
    if(d.notes&&d.notes.length)parts.push(d.notes.join(' '));
    if(d.gguf_files&&d.gguf_files.length>1)parts.push(t('lookup.gguf')+d.gguf_files.slice(0,4).join(', '));
    result.textContent=parts.join(' · ');
  }catch(err){result.textContent=t('lookup.failed')+err.message}
}
function applyPreset(){
  const p=presets[$('e-preset').value];if(!p)return;
  $('e-runtime').value=p.runtime;
  $('e-context').value=p.defaults.context_length;
  $('e-sequences').value=p.defaults.max_sequences;
  $('e-memory').value=p.defaults.gpu_memory_utilization;
  $('e-volume').value=p.defaults.volume_gb;
  if(!$('e-description').value)$('e-description').value=p.description;
  runtimeChanged();
}
function runtimeChanged(){
  const rt=runtimes[$('e-runtime').value];
  $('e-gguf').disabled=!rt?.supports_gguf;
  if(!rt?.supports_gguf)$('e-gguf').value='';
  $('vllm-options').classList.toggle('hidden',$('e-runtime').value!=='vllm');
  if($('e-runtime').value!=='vllm'){$('e-trust-remote-code').checked=false;$('e-reasoning').checked=false;$('e-tools').checked=false}
}
$('model-form').onsubmit=async e=>{
  e.preventDefault();
  const id=$('e-id').value;
  const split=(v,sep)=>v.split(sep).map(x=>x.trim()).filter(Boolean);
  const checked=[...$('e-gpu-list').querySelectorAll('input:checked')].map(c=>c.value);
  const manual=$('e-gpus').value.split('\n').map(x=>x.trim()).filter(Boolean);
  const body={
    name:$('e-name').value,description:$('e-description').value,model_id:$('e-model-id').value,
    runtime:$('e-runtime').value,gguf_file:$('e-gguf').value||null,
    served_names:split($('e-aliases').value,','),capabilities:split($('e-capabilities').value,','),
    context_length:+$('e-context').value,max_sequences:+$('e-sequences').value,
    gpu_memory_utilization:+$('e-memory').value,volume_gb:+$('e-volume').value,
    gpu_type_ids:[...new Set([...checked,...manual])],
    status:$('e-status').value,license:$('e-license').value,
    gated:$('e-gated').checked,verified:$('e-verified').checked,
    trust_remote_code:$('e-trust-remote-code').checked,
    reasoning_parser:$('e-reasoning').checked?'qwen3':null,
    tool_call_parser:$('e-tools').checked?'qwen3_coder':null,
    enable_auto_tool_choice:$('e-tools').checked
  };
  try{
    await api('/api/models/'+encodeURIComponent(id),{method:'PUT',body:JSON.stringify(body)});
    editor.close();await loadCatalog();$('model').value=id;selectModel();
  }catch(err){$('editor-error').textContent=err.message}
};
async function removeModel(){
  const id=$('e-id').value,m=models[id];if(!id)return;
  const reset=!!m?.overridden;
  const question=(reset?t('confirm.reset'):t('confirm.remove')).replace('{id}',id);
  if(!confirm(question))return;
  try{await api('/api/models/'+encodeURIComponent(id)+(reset?'/reset':''),{method:reset?'POST':'DELETE'});editor.close();await loadCatalog()}
  catch(err){$('editor-error').textContent=err.message}
}
async function exportModels(){
  try{
    const data=await api('/api/models-export');
    const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
    const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='gpuharbor-user-models.json';a.click();URL.revokeObjectURL(a.href);
  }catch(err){render(t('msg.export_error')+err.message)}
}
async function importModels(file){
  if(!file)return;
  try{
    const catalog=JSON.parse(await file.text());
    if(!confirm(t('confirm.import')))return;
    await api('/api/models-import',{method:'POST',body:JSON.stringify({catalog,replace:false})});
    await loadCatalog();render(t('msg.imported'));
  }catch(err){render(t('msg.import_error')+err.message)}finally{$('import-file').value=''}
}
const actions={openSettings,logout,newModel,editModel,exportModels,plan,preflight,startPod,stopPod,deletePod,refreshStatus,lookupModel,removeModel,
  pickImport:()=>$('import-file').click(),closeEditor:()=>editor.close(),closeSettings:()=>settingsDialog.close()};
document.addEventListener('click',e=>{
  const target=e.target.closest('[data-click],[data-mode],[data-tab]');
  if(!target)return;
  if(target.dataset.click)actions[target.dataset.click]?.();
  else if(target.dataset.mode)setMode(target.dataset.mode);
  else if(target.dataset.tab)showSettingsTab(target.dataset.tab,target);
});
const onChange=(id,fn)=>$(id).addEventListener('change',fn);
onChange('lang-switch',e=>setLang(e.target.value));
onChange('model',selectModel);
onChange('region',regionChanged);
onChange('gpu',updateCost);
onChange('e-preset',applyPreset);
onChange('e-runtime',runtimeChanged);
onChange('set-update-notifications',saveUpdateSetting);
onChange('import-file',e=>importModels(e.target.files[0]));
for(const radio of document.querySelectorAll('input[name="theme"]'))radio.addEventListener('change',()=>setTheme(radio.value));
boot().catch(()=>{});
setInterval(()=>{if(!$('app').classList.contains('hidden'))refreshStatus()},30000);
