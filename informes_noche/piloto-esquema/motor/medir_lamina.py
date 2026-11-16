"""Mide una lámina del esquema (motor esquema.js) en un solo comando, con Chrome sin ventana.

Uso (desde la raíz del proyecto):
    venv/Scripts/python.exe informes_noche/piloto-esquema/motor/medir_lamina.py informes_noche/piloto-esquema/motor/cvt.html
Opciones: --json (salida completa en JSON) · --captura ruta.jpg (una captura del armado a 1280×800, escala 0,5; ruta como --pagina: nombre solo = en motor/, con carpeta = desde la raíz) · --chrome ruta.exe
          --ojo 5,4.5,5,4,4,4.5 (notas a ojo de los criterios 1,2,3,4,5,7) · --modelo auto|v2|v1
          --solape (solo 1280, segundos): % de cada pieza tapada por otras en el «Desarmar todo» de la vista general (medir_solape.js),
            con qué pieza la tapa y las cajas para corregir los pasos; --captura-desarme / --captura-trans ruta.jpg capturan ese desarme
            y Transparente dentro del grupo más grande. En la medición completa va a 1280: > 20 % o una pieza sin verse = bloqueante.

Modelos: v2 (estándar desde el 16-nov-2026) = marcas de grupo, piezas que se tocan directo, lista con buscador y hoja inferior;
v1 (viejo) = números sobre el despiece. Con --modelo auto (por omisión) lo detecta: si hay marcas de grupo, mide v2.
En v2 mide además: área tocable real de cada pieza dentro de su grupo, tornillería, «Desarmar» al entrar al grupo,
hoja inferior del celular (alto, si tapa la pieza elegida, botones), toques hasta la ficha y largo de la ficha a 360.
Lo que sigue es la descripción del modelo v1.

Qué hace: sirve la carpeta del proyecto en un puerto libre de 127.0.0.1, abre un Chrome sin ventana con DevTools y, en 6 pestañas
a la vez, fija el viewport exacto (360×740, 390×844, 768×1024, 1024×768, 1280×800, 1440×900), pone el gancho de errores antes de
que cargue la página y corre el medidor. No usa librerías externas: solo Python y el Chrome (o Edge) instalado.
No cambia la lámina ni el motor.

Mide, en cada ancho: distribución (rúbrica v2, criterios 8 a 12), toques estrictos al centro y a ±9 px (armado y despiece,
Normal y Transparente), botones de menos de 44 px en todas las pestañas, desborde horizontal, «Desarmar» a la vista,
densidad de números en el despiece, ficha o barra fija tras tocar un número, filas de controles, errores de consola y,
a 1280, que el visor 3D abra si alguna ficha trae forma3d. Las transiciones se apagan solo mientras se mide y Chrome corre con
«reducir movimiento» (los encuadres animados son instantáneos); el navegador está a la vista, así que rAF no se pausa.
"""
import argparse, base64, json, mimetypes, os, shutil, socket, struct, subprocess, sys, tempfile, threading, time, urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, quote

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ALTO_MIN_MARCA = 44   # alto mínimo del área de toque de una marca de grupo (px). Lo usa también chequeo_rapido.py: un solo valor
ANCHOS = [(360, 740), (390, 844), (768, 1024), (1024, 768), (1280, 800), (1440, 900)]

GANCHO = """window.__errores=[];window.__avisos=[];
addEventListener('error',e=>{const t=e.target;__errores.push(e.message||('no cargó: '+((t&&(t.src||t.href))||'?')))},true);
addEventListener('unhandledrejection',e=>__errores.push('promesa: '+((e.reason&&e.reason.message)||e.reason)));
(()=>{const ce=console.error.bind(console),cw=console.warn.bind(console);
console.error=(...a)=>{__errores.push('console.error: '+a.join(' '));ce(...a)};
console.warn=(...a)=>{__avisos.push(a.join(' '));cw(...a)}})();"""

MEDIDOR = r"""
(async()=>{
const S=ms=>new Promise(r=>setTimeout(r,ms)), q=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const R={ancho:innerWidth,alto:innerHeight}, VH=innerHeight, VW=innerWidth;
const enviar=()=>JSON.stringify(R);
try{
for(let i=0;i<200&&!q('#lamina .esq-bola');i++)await S(100); await S(500);
const L=q('#lamina'); if(!L){R.fatal='no hay #lamina ('+location.href+', '+document.readyState+', errores: '+(window.__errores||[]).join(' | ')+')';return enviar()}
const caja=e=>e&&e.getBoundingClientRect();
const seVe=e=>{if(!e)return false;const r=e.getBoundingClientRect();if(!r.width||!r.height)return false;for(let x=e;x&&x.nodeType===1;x=x.parentElement){const c=getComputedStyle(x);if(c.display==='none'||c.visibility==='hidden'||+c.opacity<0.1)return false}return true};
const visSvg=e=>{for(let x=e;x&&x.tagName!=='svg';x=x.parentElement){const c=getComputedStyle(x);if(+c.opacity<0.1||c.display==='none'||c.visibility==='hidden')return false}return true};
const st=document.createElement('style');st.textContent='*{transition:none!important;animation:none!important}html{scroll-behavior:auto!important}';
// rAF de ventanas sin pantalla puede ir a saltos: mientras se mide, un reloj fijo de 16 ms garantiza que los encuadres terminen
const rafOrig=window.requestAnimationFrame;
const apagar=()=>{document.head.append(st);window.requestAnimationFrame=cb=>setTimeout(()=>cb(performance.now()),16)}, prender=()=>{st.remove();window.requestAnimationFrame=rafOrig};
// 1. ficha vacía y distribución, arriba del todo
R.fichaVacia=(q('#ficha')||{}).textContent?.trim().replace(/\s+/g,' ').slice(0,200)||'';
scrollTo(0,0);await S(150);
const lam=caja(L), todo=caja(q('#bTodo')), tabs=caja(q('[role="tablist"]')), cab=caja(q('header, .esq-cabeza'));
const fila=L.closest('.esq-escenario')||L.parentElement, fb=caja(fila);
const cols=[...fila.children].filter(seVe).map(c=>{const b=caja(c);let fin=b.top;c.querySelectorAll('*').forEach(n=>{const r=n.getBoundingClientRect();if(r.height&&n.getClientRects().length&&getComputedStyle(n).display!=='none')fin=Math.max(fin,r.bottom)});
  const fija=getComputedStyle(c).position==='sticky'&&b.height<=VH;return{top:Math.round(b.top),w:Math.round(b.width),hueco:fija?0:Math.round(Math.max(0,fb.bottom-fin)/fb.height*100),fija}});
R.dist={w:Math.round(lam.width),h:Math.round(lam.height),top:Math.round(lam.top),bottom:Math.round(lam.bottom),pctAncho:Math.round(lam.width/fb.width*100),
  completo:lam.top>=0&&lam.bottom<=VH,cortePct:Math.max(0,Math.round((lam.bottom-VH)/lam.height*100)),desarmar:!!todo&&todo.top>=0&&todo.bottom<=VH,desarmarFin:todo&&Math.round(todo.bottom),
  pestanas:!!tabs&&tabs.bottom<=VH,apoyoPct:Math.round(Math.max(0,lam.top-(cab?cab.height:0)-(tabs?tabs.height+20:0))/VH*100),cols,altoPagina:document.documentElement.scrollHeight};
// 2. filas de controles bajo el dibujo
const ctr=['vNormal','vTrans','zMas','zMenos','zVer','bTodo','bAtras','bAdel','iNum'].map(id=>document.getElementById(id)).filter(seVe);
const tops=[];ctr.map(e=>caja(e).top).sort((a,b)=>a-b).forEach(t=>{if(!tops.length||t-tops[tops.length-1]>8)tops.push(t)});
R.controles={filas:tops.length,sobreDibujo:ctr.filter(e=>caja(e).top<lam.bottom-2&&caja(e).bottom>lam.top).map(e=>e.id)};
// 3. botones chicos y desborde en todas las pestañas
const chicos=new Set(), chicosOtras=new Set(), desb=new Set(), pest=$$('[role="tablist"] [role="tab"]');
for(const [i,t] of (pest.length?pest:[null]).entries()){if(t){t.click();await S(250)}
  $$('button,[role="tab"],[role="button"]:not(svg *),a.esq-btn,summary').filter(e=>!e.closest('svg')&&seVe(e)).forEach(e=>{const r=caja(e);if(Math.min(r.width,r.height)<43.5)(i?chicosOtras:chicos).add((e.id||e.textContent.trim().slice(0,24)||e.getAttribute('aria-label'))+' '+Math.round(r.width)+'×'+Math.round(r.height)+(t?' ('+t.textContent.trim()+')':''))});
  if(document.documentElement.scrollWidth>VW)desb.add((t?t.textContent.trim():'página')+' '+document.documentElement.scrollWidth)}
if(pest.length){pest[0].click();await S(250)}
R.botonesChicos=[...chicos];R.botonesChicosOtras=[...chicosOtras];R.desborde=[...desb];
const ch=q('#chips');R.lista=ch?{h:Math.round(caja(ch).height),deslizable:ch.scrollWidth>ch.clientWidth+2}:null;
// 4. tocar un número: ficha a la vista (≥960) o barra fija (celular)
scrollTo(0,0);await S(100);L.scrollIntoView({block:'center'});await S(250);
const b0=$$('#lamina .esq-bola').find(b=>caja(b).width&&visSvg(b));
if(b0){const r=caja(b0),x=r.left+r.width/2,y=r.top+r.height/2;const e=document.elementFromPoint(x,y);
  (e||b0).dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y}));await S(400);
  const h3=q('#ficha h3'),hoja=q('#hoja');const hv=h3&&caja(h3);
  R.alTocar={pieza:b0.closest('.esq-pz').dataset.n,fichaVisible:!!hv&&hv.top>=0&&hv.bottom<=VH,barraFija:!!hoja&&seVe(hoja)&&caja(hoja).bottom<=VH+1&&caja(hoja).top>=0}}
// 5. toques estrictos y densidad
apagar();
const estable=async()=>{let prev='';for(let i=0;i<40;i++){L.scrollIntoView({block:'center',behavior:'instant'});await S(150);const lr=caja(L);
  const sig=$$('#lamina .esq-bola').map(b=>{const r=caja(b);return Math.round(r.left)+','+Math.round(r.top)}).join('|')+'#'+Math.round(lr.top)+'#'+L.getAttribute('viewBox');
  if(sig===prev&&(lr.height>VH||(lr.top>=-1&&lr.bottom<=VH+1)))return;prev=sig}};
const medir=async()=>{await estable();let n=0,c=0,rmin=1e9;const fallas=[],roces=[],pts=[];const lr=caja(L);
  for(const b of $$('#lamina .esq-bola')){const r=caja(b);if(!r.width||!visSvg(b))continue;n++;const t=b.querySelector('.esq-toque');if(t)rmin=Math.min(rmin,caja(t).width/2);
    const cx=r.left+r.width/2,cy=r.top+r.height/2,num=b.closest('.esq-pz').dataset.n,d=b.querySelector('.esq-disco');pts.push({n:num,x:cx,y:cy,d:d?caja(d).width:0,fuera:cx<lr.left||cx>lr.right||cy<lr.top||cy>lr.bottom});
    const de=(x,y)=>{const e=document.elementFromPoint(x,y);if(!e)return'fuera';const bb=e.closest('.esq-bola');return bb===b?'ok':bb?'n'+bb.closest('.esq-pz').dataset.n:e.tagName};
    const k=de(cx,cy);if(k==='ok')c++;else fallas.push(num+'→'+k);
    for(const[dx,dy]of[[9,0],[-9,0],[0,9],[0,-9]]){const h=de(cx+dx,cy+dy);if(h[0]==='n'&&h!=='n'+num||h==='BUTTON')roces.push(num+'('+dx+','+dy+')→'+h)}}
  const pares=[];let dmin=1e9;for(let i=0;i<pts.length;i++)for(let j=i+1;j<pts.length;j++){const d=Math.hypot(pts[i].x-pts[j].x,pts[i].y-pts[j].y);dmin=Math.min(dmin,d);if(d<24)pares.push(pts[i].n+'-'+pts[j].n+':'+d.toFixed(1))}
  return{centro:c,total:n,fallas,roces,radioMin:+rmin.toFixed(1),distMin:+dmin.toFixed(1),pares24:pares,discoMin:+Math.min(...pts.map(p=>p.d)).toFixed(1),fuera:pts.filter(p=>p.fuera).map(p=>p.n)}};
const N=document.getElementById('vNormal'),T=document.getElementById('vTrans'),ad=document.getElementById('bAdel'),at=document.getElementById('bAtras');
R.toques={};R.toques.armN=await medir();if(T){T.click();await S(300);R.toques.armT=await medir()}
let pasos=0;if(ad){for(let i=0;i<40&&!ad.disabled;i++){ad.click();pasos++;await S(60)}await S(700)}R.pasosDesarme=pasos;
R.toques.desT=await medir();if(N){N.click();await S(300)}R.toques.desN=await medir();
if(at){for(let i=0;i<40&&!at.disabled;i++){at.click();await S(30)}await S(500)}
prender();
// 6. visor 3D (solo a 1280)
if(VW===1280&&window.Esquema3D){R.v3d={hay:false};for(const c of $$('.esq-chip')){c.click();await S(120);const v=q('#ficha .esq-v3d');if(v){R.v3d.hay=true;R.v3d.pieza=c.textContent.trim();
  let e='';for(let i=0;i<80;i++){e=(v.querySelector('.esq-v3d-estado')||{}).textContent||'';if(!/Cargando/.test(e))break;await S(100)}
  const cv=v.querySelector('canvas');R.v3d.estado=e;R.v3d.lienzo=cv?cv.width+'×'+cv.height:'sin canvas';R.v3d.ok=!!cv&&cv.width>0&&!v.classList.contains('esq-v3d-error')&&!/No se pudo/.test(e);break}}}
}catch(err){R.fatal=String(err&&err.stack||err)}
R.errores=window.__errores||[];R.avisos=window.__avisos||[];return enviar();
})();
"""

# ---------- modelo v2 (marcas de grupo, piezas que se tocan directo, lista con buscador) ----------
MEDIDOR_V2 = r"""
(async()=>{
const S=ms=>new Promise(r=>setTimeout(r,ms)), q=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const R={ancho:innerWidth,alto:innerHeight}, VH=innerHeight, VW=innerWidth, fin=()=>JSON.stringify(R);
try{
for(let i=0;i<200&&!q('#lamina .esq-marca-g');i++)await S(100); await S(600);
const L=q('#lamina'); if(!L||!q('#lamina .esq-marca-g')){R.fatal='no hay marcas de grupo ('+location.href+', errores: '+(window.__errores||[]).join(' | ')+')';return fin()}
const caja=e=>e&&e.getBoundingClientRect();
const seVe=e=>{if(!e)return false;const r=e.getBoundingClientRect();if(!r.width||!r.height)return false;for(let x=e;x&&x.nodeType===1;x=x.parentElement){const c=getComputedStyle(x);if(c.display==='none'||c.visibility==='hidden'||+c.opacity<0.1)return false}return true};
const visSvg=e=>{if(!e||!caja(e).width)return false;for(let x=e;x&&x.tagName!=='svg';x=x.parentElement){const c=getComputedStyle(x);if(+c.opacity<0.1||c.display==='none'||c.visibility==='hidden')return false}return true};
// (el globito con el nombre que sale 1,8 s tras un toque de dedo se oculta: si no, tapa lo que se mide después)
const st=document.createElement('style');st.textContent='*{transition:none!important;animation:none!important}html{scroll-behavior:auto!important}.esq-v2-nombre{display:none!important}';
document.head.append(st);window.requestAnimationFrame=cb=>setTimeout(()=>cb(performance.now()),16);
const clic=(el,x,y)=>{const r=caja(el);x=x??r.left+r.width/2;y=y??r.top+r.height/2;const t=document.elementFromPoint(x,y)||el;
  for(const ty of['pointerdown','pointerup'])t.dispatchEvent(new PointerEvent(ty,{bubbles:true,clientX:x,clientY:y,pointerType:'touch',isPrimary:true,pointerId:3}));
  t.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y}))};
const estable=async(centrar=true)=>{let prev='';for(let i=0;i<40;i++){if(centrar)L.scrollIntoView({block:'center',behavior:'instant'});await S(150);const lr=caja(L);
  const sig=L.getAttribute('viewBox')+'#'+Math.round(lr.top)+'#'+$$('#lamina .esq-pz.esq-engr, #lamina .esq-marca').slice(0,40).map(e=>{const r=caja(e);return Math.round(r.left)+','+Math.round(r.top)}).join('|');
  if(sig===prev)return;prev=sig}};
// tornillería: sus piezas se tocan por la píldora, no por la silueta (se leen del JSON de la lámina)
const TORN=new Set();let SIN_IND=false;try{const ed=q('#esq-datos'),s=[...document.scripts].map(x=>x.textContent).join('\n').match(/fetch\("([^"]+\.json)"\)/);
  const D=ed?JSON.parse(ed.textContent):(s?await (await fetch(s[1])).json():null);
  if(D){((D.v2&&D.v2.grupos)||[]).forEach(g=>g.torn.forEach(t=>t.ids.forEach(i=>TORN.add(i))));
    // «Cómo funciona» sin indicador físico, declarado en el JSON: funciona.sinIndicador = true (o funciona.indicador = false)
    SIN_IND=!!(D.funciona&&(D.funciona.sinIndicador||D.funciona.indicador===false))}}catch(e){}
R.tornIds=[...TORN];
R.fichaVacia=(q('#ficha')||{}).textContent?.trim().replace(/\s+/g,' ').slice(0,160)||'';
// 1. distribución de la vista general, arriba del todo
scrollTo(0,0);await S(200);
const lam=caja(L), tabs=caja(q('[role="tablist"]')), cab=caja(q('header, .esq-cabeza')), lado=caja(q('#lDel')||$$('button[data-lado]').find(seVe)||q('#v2Titulo'));
const fila=L.closest('.esq-escenario')||L.parentElement, fb=caja(fila);
const cols=[...fila.children].filter(seVe).map(c=>{const b=caja(c);let f=b.top;c.querySelectorAll('*').forEach(n=>{const r=n.getBoundingClientRect();if(r.height&&n.getClientRects().length&&getComputedStyle(n).display!=='none')f=Math.max(f,r.bottom)});
  const fija=getComputedStyle(c).position==='sticky'&&b.height<=VH;return{top:Math.round(b.top),w:Math.round(b.width),hueco:fija?0:Math.round(Math.max(0,fb.bottom-f)/fb.height*100)}});
R.dist={w:Math.round(lam.width),h:Math.round(lam.height),top:Math.round(lam.top),bottom:Math.round(lam.bottom),pctAncho:Math.round(lam.width/fb.width*100),
  completo:lam.top>=0&&lam.bottom<=VH,cortePct:Math.max(0,Math.round((lam.bottom-VH)/lam.height*100)),ladoVisible:!!lado&&lado.bottom<=VH&&lado.top>=0,
  pestanas:!!tabs&&tabs.bottom<=VH,apoyoPct:Math.round(Math.max(0,lam.top-(cab?cab.height:0)-(tabs?tabs.height+20:0))/VH*100),cols,altoPagina:document.documentElement.scrollHeight};
// 2. botones chicos y desborde en todas las pestañas
const chicos=new Set(),otras=new Set(),desb=new Set(),pest=$$('[role="tablist"] [role="tab"]');
for(const [i,t] of (pest.length?pest:[null]).entries()){if(t){t.click();await S(250)}
  $$('button,[role="tab"],a.esq-btn,summary,input').filter(e=>!e.closest('svg')&&seVe(e)).forEach(e=>{const r=caja(e);if(Math.min(r.width,r.height)<43.5)(i?otras:chicos).add((e.id||e.textContent.trim().slice(0,22)||e.getAttribute('aria-label')||e.tagName)+' '+Math.round(r.width)+'×'+Math.round(r.height)+(t?' ('+t.textContent.trim()+')':''))});
  if(document.documentElement.scrollWidth>VW)desb.add((t?t.textContent.trim():'página')+' '+document.documentElement.scrollWidth)}
if(pest.length){pest[0].click();await S(250)}
R.botonesChicos=[...chicos];R.botonesChicosOtras=[...otras];R.desborde=[...desb];
// marcas: el motor puede tener una píldora corta y otra completa (oculta); se usa la que se ve, o el área de toque
const pildoraVisible=m=>[...m.querySelectorAll('.esq-pildora')].find(x=>caja(x).width&&visSvg(x))||m.querySelector('.esq-toque')||m;
const nombreMarca=m=>(([...m.querySelectorAll('text')].find(t=>caja(t).width&&visSvg(t)))||m).textContent.trim();
// hoja inferior (o barra fija) que aparece al elegir una pieza en el celular: el elemento fijo más grande pegado abajo
const hojaInferior=(P)=>{const fx=$$('body *').filter(e=>{const c=getComputedStyle(e);return(c.position==='fixed'||c.position==='sticky')&&seVe(e)}).map(e=>({e,r:caja(e)}))
    .filter(o=>o.r.bottom>=VH-24&&o.r.bottom<=VH+2&&o.r.top<VH-20&&o.r.width>=VW*0.85&&o.r.height>=40&&!o.e.closest('header'));
  if(!fx.length)return null;fx.sort((a,b)=>b.r.height-a.r.height);const {e,r}=fx[0];
  const pr=P?caja(P.querySelector('.esq-arte')||P):null;
  const tapa=pr&&pr.width?Math.max(0,Math.min(pr.bottom,r.bottom)-Math.max(pr.top,r.top))*Math.max(0,Math.min(pr.right,r.right)-Math.max(pr.left,r.left))/(pr.width*pr.height):0;
  const bs=[...e.querySelectorAll('button,a,[role=button]')].filter(seVe);const nom=((q('#ficha h3')||{}).textContent||'').trim().slice(0,12);
  const desp=e.scrollHeight>e.clientHeight+4||[...e.querySelectorAll('*')].some(x=>x.scrollHeight>x.clientHeight+4&&/auto|scroll/.test(getComputedStyle(x).overflowY));
  return{el:e,id:e.id||String(e.className).split(' ')[0],alto:Math.round(r.height),pct:Math.round(r.height/VH*100),tapaPiezaPct:Math.round(tapa*100),
    nombre:!!nom&&e.textContent.includes(nom),secciones:[...e.querySelectorAll('h4')].filter(h=>{const x=caja(h);return x.height&&x.top<VH}).length,desplaza:desp,
    cerrar:bs.some(b=>/cerrar|close|×|✕/i.test((b.getAttribute('aria-label')||'')+b.textContent)),chicos:bs.filter(b=>Math.min(caja(b).width,caja(b).height)<43.5).map(b=>(b.getAttribute('aria-label')||b.textContent.trim()).slice(0,20))}};
// 3. marcas de grupo de cada lado
const medirMarcas=async()=>{await estable();const lr=caja(L);const ms=$$('#marcasG .esq-marca-g').filter(visSvg);const o={n:ms.length,nombres:[],altoMin:1e9,anchoMin:1e9,fallas:[],roces:[],solapes:[],fuera:[]};
  ms.forEach(m=>{const t=caja(m.querySelector('.esq-toque')),p=caja(pildoraVisible(m)),nom=nombreMarca(m);o.nombres.push(nom);o.altoMin=Math.min(o.altoMin,t.height);o.anchoMin=Math.min(o.anchoMin,t.width);
    const cx=p.left+p.width/2,cy=p.top+p.height/2;if(cx<lr.left||cx>lr.right||cy<lr.top||cy>lr.bottom)o.fuera.push(nom);
    const de=(x,y)=>{const e=document.elementFromPoint(x,y),mm=e&&e.closest('.esq-marca');return mm===m?'ok':mm?nombreMarca(mm):(e?e.tagName:'fuera')};
    const c=de(cx,cy);if(c!=='ok')o.fallas.push(nom+'→'+c);
    for(const[dx,dy]of[[9,0],[-9,0],[0,9],[0,-9]]){const h=de(cx+dx,cy+dy);if(h!=='ok'&&ms.some(x=>nombreMarca(x)===h))o.roces.push(nom+'→'+h)}});
  for(let i=0;i<ms.length;i++)for(let j=i+1;j<ms.length;j++){const a=caja(pildoraVisible(ms[i])),b=caja(pildoraVisible(ms[j]));if(a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top)o.solapes.push(o.nombres[i]+' / '+o.nombres[j])}
  o.altoMin=Math.round(o.altoMin);o.anchoMin=Math.round(o.anchoMin);return o};
// 4. piezas dentro del grupo: área tocable real
const medirPiezas=async()=>{await estable();const lr=caja(L);const out=[];
  for(const P of $$('#lamina .esq-pz.esq-engr').filter(visSvg).filter(P=>!TORN.has(P.id.slice(3)))){const a=caja(P.querySelector('.esq-arte')||P);
    const x0=Math.max(a.left,lr.left,0),y0=Math.max(a.top,lr.top,0),x1=Math.min(a.right,lr.right,VW),y1=Math.min(a.bottom,lr.bottom,VH);
    let hits=0,sx=0,sy=0;const pts=[],paso=Math.max(2,Math.sqrt(Math.max(1,(x1-x0)*(y1-y0))/500));
    if(x1>x0&&y1>y0)for(let x=x0+paso/2;x<x1;x+=paso)for(let y=y0+paso/2;y<y1;y+=paso){const e=document.elementFromPoint(x,y);if(e&&e.closest('.esq-pz')===P&&!e.closest('.esq-marca')){hits++;sx+=x;sy+=y;pts.push([x,y])}}
    // punto para tocar: el acierto más cercano al centro de masa (en una manguera curva el centro cae fuera)
    let rel=null;if(hits){const cx=sx/hits,cy=sy/hits;const b=pts.reduce((m,p)=>Math.hypot(p[0]-cx,p[1]-cy)<Math.hypot(m[0]-cx,m[1]-cy)?p:m);rel=[b[0]-a.left,b[1]-a.top]}
    const area=hits*paso*paso, d=2*Math.sqrt(area/Math.PI);out.push({id:P.id,n:P.dataset.n,d:Math.round(d),rel})}
  // que tocar cada pieza la seleccione (en el punto medio de su área tocable, recalculado por si la página se movió)
  // una pieza con varias siluetas (10a, 10b) se prueba una sola vez: tocar de nuevo la pieza elegida la desmarca
  const probadas={};
  for(const p of out){if(!p.rel){p.sel=false;continue}if(p.n in probadas){p.sel=probadas[p.n];delete p.rel;continue}await estable();const P=document.getElementById(p.id),a=caja(P.querySelector('.esq-arte')||P),x=a.left+p.rel[0],y=a.top+p.rel[1];
    const e=document.elementFromPoint(x,y);if(!e||e.closest('.esq-pz')!==P){p.sel=false;delete p.rel;continue}
    clic(P,x,y);await S(150);p.sel=$$('#lamina .esq-pz.esq-sel').some(z=>z.dataset.n===p.n);probadas[p.n]=p.sel;delete p.rel}
  await estable();  // tocar piezas puede haber movido la página
  const ts=$$('#lamina .esq-marca-t').filter(visSvg).map(m=>{const r=caja(pildoraVisible(m)),e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return{t:nombreMarca(m),hit:e?(e.closest('.esq-marca')?nombreMarca(e.closest('.esq-marca')):(e.closest('.esq-pz')?e.closest('.esq-pz').id:e.tagName+'.'+(e.getAttribute('class')||''))):'fuera',alto:Math.round(caja(m.querySelector('.esq-toque')).height),ok:!!e&&e.closest('.esq-marca')===m}});
  return{piezas:out,torn:ts}};
R.lados={};R.grupos=[];let primero=true;
// lados: Delantera | Trasera si la lámina los tiene; si no, una sola vista ('unico')
const LADOS=[['del','#lDel'],['tra','#lTra']].filter(([,s])=>seVe(q(s)));
if(!LADOS.length)$$('[data-lado]').filter(b=>b.tagName==='BUTTON'&&seVe(b)).forEach(b=>LADOS.push([b.dataset.lado,`[data-lado="${b.dataset.lado}"]`]));if(!LADOS.length)LADOS.push(['unico',null]);
for(const [ld,sel] of LADOS){if(sel){q(sel).click();await S(300)}R.lados[ld]=await medirMarcas();
  const nombres=$$('#marcasG .esq-marca-g').filter(visSvg).map(m=>m.dataset.g);
  for(const gid of nombres){const m=q(`#marcasG .esq-marca-g[data-g="${gid}"]`);if(!m)continue;m.dispatchEvent(new MouseEvent('click',{bubbles:true}));await estable(false);
    const G={lado:ld,g:gid,nombre:m.textContent.trim()};
    if(primero){scrollTo(0,0);await S(200);const l2=caja(L),bt=caja(q('#bTodo'));G.entrada={completo:l2.top>=0&&l2.bottom<=VH,desarmar:!!bt&&bt.width>0&&bt.top>=0&&bt.bottom<=VH,desarmarFin:bt?Math.round(bt.bottom):null,
      volver:seVe(q('#v2Volver'))};
      const ctr=['lDel','lTra','v2Volver','bTodo','bAtras','bAdel','iNum'].map(id=>document.getElementById(id)).filter(seVe);const tops=[];ctr.map(e=>caja(e).top).sort((a,b)=>a-b).forEach(t=>{if(!tops.length||t-tops[tops.length-1]>8)tops.push(t)});
      G.filasControles=tops.length;G.controlesSobreDibujo=ctr.filter(e=>caja(e).top<l2.bottom-2&&caja(e).bottom>l2.top).map(e=>e.id)}
    G.arm=await medirPiezas();
    if(primero){const P=$$('#lamina .esq-pz.esq-engr').filter(visSvg)[0];if(P){await estable();const r=caja(P.querySelector('.esq-arte')||P);clic(P,r.left+r.width/2,r.top+r.height/2);
      // con la máquina cargada la ficha o la hoja pueden tardar: se espera hasta 2 s a que aparezca alguna
      for(let i=0;i<20;i++){await S(100);const h=q('#ficha h3'),hv=h&&caja(h);if((VW>=960&&hv&&hv.top>=0&&hv.bottom<=VH)||(VW<960&&hojaInferior(P)))break}
      const h3=q('#ficha h3');const hv=h3&&caja(h3);const hi=hojaInferior(P);
      G.alTocar={fichaVisible:!!hv&&hv.top>=0&&hv.bottom<=VH&&!(hi&&hv.top>=VH-hi.alto),barraFija:!!hi,hoja:hi};
      // toques hasta ver el contenido de la ficha: marca (1) + pieza (2) [+ abrir la hoja o «Ver ficha» (3)]
      let t=2;if(!G.alTocar.fichaVisible&&!(hi&&hi.secciones>=2)){t=99;const e=hi&&hi.el;const b=e&&[...e.querySelectorAll('button,a,[role=button]')].filter(seVe).find(b=>/ver ficha|abrir|ficha|más|expand|subir/i.test((b.getAttribute('aria-label')||'')+b.textContent));
        // el desplazamiento o la apertura de la hoja puede ser animado: se espera hasta 2,5 s
        if(b){b.click();for(let i=0;i<25&&t>3;i++){await S(100);const h=q('#ficha h3'),r2=h&&caja(h);const hi2=hojaInferior(P);if((r2&&r2.top>=0&&r2.bottom<=VH)||(hi2&&hi2.secciones>=2))t=3}
          // se deja la hoja como estaba: abierta taparía el dibujo en lo que se mide después
          const c2=(e&&e.querySelector('#h2X'))||(e&&[...e.querySelectorAll('button,[role=button]')].filter(seVe).find(x=>/cerrar|close|×|✕/i.test((x.getAttribute('aria-label')||'')+x.textContent)));
          if(b.getAttribute('aria-expanded')==='true')b.click();else if(c2)c2.click();await S(400)}}
      G.toquesFicha=t;if(hi)delete hi.el}primero=false}
    // (tocar una pieza interna desarma el grupo solo: entonces «Desarmar» ya está agotado, pero igual se mide desarmado)
    // cada paso se espera hasta que las piezas queden quietas (las transiciones ya están apagadas; esto cubre animaciones por JS)
    const quieto=async()=>{let prev='';for(let i=0;i<30;i++){await S(80);const s=$$('#lamina .esq-pz.esq-engr').map(e=>{const r=caja(e);return Math.round(r.left)+','+Math.round(r.top)}).join('|');if(s===prev)return;prev=s}};
    // espera real del desarme automático: se toca «Desarmar» y se cronometra hasta que no queden pasos
    const ad=q('#bAdel'),bt=q('#bTodo');let n=0,yaDes=false;
    if(ad&&!ad.hidden&&!ad.disabled&&bt&&!bt.hidden){const t0=performance.now();bt.click();for(let i=0;i<200&&!ad.disabled;i++)await S(50);G.desarmeMs=Math.round(performance.now()-t0);await quieto()}
    if(ad&&!ad.hidden){yaDes=ad.disabled;for(let i=0;i<30&&!ad.disabled;i++){ad.click();n++;await quieto()}}
    if(yaDes){const at=q('#bAtras');let k=0;while(at&&!at.disabled&&k<30){at.click();k++;await quieto()}n=k;for(let i=0;i<k;i++){ad.click();await quieto()}}
    G.pasos=n;
    if(n)G.des=await medirPiezas();
    R.grupos.push(G);const v=q('#v2Volver');if(v&&!v.hidden){v.click();await estable()}}}
q('#lDel')&&q('#lDel').click();await S(300);
// 5. lista y buscador
scrollTo(0,0);const li=q('#v2Lista');if(li){const ds=$$('#v2Lista .esq-v2-grupo');R.lista={grupos:ds.length,abiertos:ds.filter(d=>d.open).length,items:$$('#v2Lista .esq-v2-item').length,alto:Math.round(caja(li).height)};
  const inp=li.querySelector('.esq-v2-q');if(inp){inp.value='bomba';inp.dispatchEvent(new Event('input',{bubbles:true}));await S(200);R.lista.buscarBomba=li.querySelectorAll('.esq-v2-res .esq-v2-item').length;inp.value='';inp.dispatchEvent(new Event('input',{bubbles:true}));await S(100)}}
// 6. ficha: secciones, navegación, alto
const it=q('#v2Lista .esq-v2-item');if(it){it.click();await S(400);const f=q('#ficha');R.ficha={titulo:(q('#ficha h3')||{}).textContent,secciones:$$('#ficha h4, #ficha summary').map(e=>e.textContent.trim().slice(0,40)),alto:Math.round(caja(f).height),nav:!!q('#ficha .esq-v2-nav')};
  // largo de la ficha: a cuántas pantallas del inicio queda «¿Se repara o se cambia?» y «Pedir» (por posición, el orden puede venir del CSS)
  const ft=caja(f).top,hs=$$('#ficha h4').find(h=>/repara/i.test(h.textContent)),pd=q('#ficha a[href="#pedir-repuesto"], #ficha .esq-v2-acciones');
  R.ficha.reparaPantallas=hs?+((caja(hs).top-ft)/VH).toFixed(2):null;R.ficha.pedirPantallas=pd?+((caja(pd).top-ft)/VH).toFixed(2):null;
  const sig=q('#ficha .esq-v2-flecha[data-k]:not([disabled])');const t0=R.ficha.titulo;if(sig){sig.click();await S(300);R.ficha.siguienteCambia=(q('#ficha h3')||{}).textContent!==t0}}
// 6b. «Cómo funciona»: etiquetas montadas, letra mínima, cambios visibles por paso, indicador, detalle y largo del texto
{const tf=window.__ESQ_FINAL?null:q('#t-funciona'),fn=()=>q('#fn');if(tf){tf.click();await S(500);const F=fn();
 if(F){const visT=e=>{const r=e.getBoundingClientRect();if(!r.width)return false;for(let x=e;x&&x.nodeType===1;x=x.parentElement){const c=getComputedStyle(x);if(c.display==='none'||c.visibility==='hidden'||+c.opacity<0.15)return false}return true};
  const k=()=>F.getBoundingClientRect().width/(F.viewBox.baseVal.width||F.getBoundingClientRect().width);
  const foto=()=>[...F.querySelectorAll('*')].map(e=>['transform','d','x','y','cx','cy','r','opacity','fill','stroke','points','width','height','style','class'].map(a=>e.getAttribute(a)).join('|')+'|'+(e.childElementCount?'':e.textContent));
  const IND=/\d\s*(rpm|bar|psi|kpa|°\s*c|°|%|km\/h|l\b|ml|n·m|mm)|rpm|presi[oó]n\s*\d|°c/i;
  const paso=()=>{const ts=[...F.querySelectorAll('text')].filter(visT),rs=ts.map(t=>t.getBoundingClientRect()),sol=[];
    for(let i=0;i<rs.length;i++)for(let j=i+1;j<rs.length;j++){const a=rs[i],b=rs[j],ox=Math.min(a.right,b.right)-Math.max(a.left,b.left),oy=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
      if(ox>2&&oy>2)sol.push(ts[i].textContent.trim().slice(0,24)+' / '+ts[j].textContent.trim().slice(0,24))}
    return{sol,fmin:ts.length?Math.min(...ts.map(t=>parseFloat(getComputedStyle(t).fontSize)*k())):99,ind:ts.map(t=>t.textContent.trim()).filter(t=>IND.test(t)),
      texto:(((q('#fnTexto')||{}).textContent)||'').trim().length}};
  const quietoFn=async()=>{let prev='';for(let i=0;i<25;i++){await S(120);const s=foto().join('#');if(s===prev)return;prev=s}};
  const ad=q('#fnAdel'),at=q('#fnAtras');if(at)while(!at.disabled){at.click();await S(60)}await quietoFn();
  const ps=[paso()],cambios=[];let ant=foto();for(let i=0;i<20&&ad&&!ad.disabled;i++){ad.click();await quietoFn();const f=foto();cambios.push(f.filter((x,j)=>x!==ant[j]).length+Math.abs(f.length-ant.length));ant=f;ps.push(paso())}
  if(at)while(!at.disabled){at.click();await S(40)}
  R.funciona={pasos:ps.length,solapes:[...new Set(ps.flatMap(p=>p.sol))],letraMin:+Math.min(...ps.map(p=>p.fmin)).toFixed(1),cambios,
    indicadores:[...new Set(ps.flatMap(p=>p.ind))].slice(0,6),sinIndicadorDeclarado:SIN_IND,
    formas:F.querySelectorAll('path,rect,circle,ellipse,polygon,polyline,line').length,
    degradados:F.querySelectorAll('linearGradient,radialGradient').length+[...F.querySelectorAll('*')].filter(e=>/url\(/.test(e.getAttribute('fill')||'')).length,
    textoMax:Math.max(...ps.map(p=>p.texto))}}
 else R.funciona={sinEsquema:true};
 const tp=q('#t-piezas');if(tp){tp.click();await S(300)}}}
// 7. 3D a 1280
// (la lista se vuelve a dibujar con cada elección: se busca el botón por su clave cada vez)
if(VW===1280&&window.Esquema3D){R.v3d={hay:false};for(const k of [...new Set($$('#v2Lista .esq-v2-item').map(b=>b.dataset.k))]){const b=q(`.esq-v2-item[data-k="${k}"]`);if(!b)continue;b.click();await S(150);const v=q('#ficha .esq-v3d');if(v){R.v3d.hay=true;R.v3d.pieza=(q('#ficha h3')||{}).textContent;
  let e='';for(let i=0;i<80;i++){e=(v.querySelector('.esq-v3d-estado')||{}).textContent||'';if(!/Cargando/.test(e))break;await S(100)}const cv=v.querySelector('canvas');R.v3d.estado=e;R.v3d.ok=!!cv&&cv.width>0&&!/No se pudo/.test(e);break}}}
st.remove();
}catch(err){R.fatal=String(err&&err.stack||err)}
// marcado crudo [[n|texto]] que quedó sin renderizar en cualquier texto de la página (todas las pestañas)
R.crudo=(((q('.esq-envoltura')||document.body).textContent||'').match(/\[\[[^\]]{0,40}/g)||[]).slice(0,5);
R.errores=window.__errores||[];return fin();
})();
"""


def texto_solape(so):
    if not so or so.get("fatal"): return "solape: no se pudo medir " + str((so or {}).get("fatal", ""))[:200]
    return "solape del desarme general: " + " · ".join(f"{l}: peor {o['peor']} % (" + ", ".join(f"{p['id']} {p['tapado']} %" + (f" bajo {p['por']}" if p.get("por") and p["tapado"] > 8 else "") for p in o["piezas"][:4]) + ")"
                                                      + (f", sin verse: {', '.join(o['invisibles'])}" if o["invisibles"] else "") for l, o in so["lados"].items())


def notas_v2(R):
    d = {w: R[w]["dist"] for w in R}
    falla, bloq = [], []
    so = R.get(1280, {}).get("solape")
    if so and not so.get("fatal"):
        for l, o in so["lados"].items():
            if o["peor"] > UMBRAL_SOLAPE or o["invisibles"]: bloq.append(f"desarme general ({l}): piezas tapadas por otras > {UMBRAL_SOLAPE} % o sin verse: " + texto_solape({"lados": {l: o}})[28:])
            elif o["peor"] > 8: falla.append(f"aviso: desarme general ({l}): pieza tapada {o['peor']} % (umbral {UMBRAL_SOLAPE} %)")
    m = lambda xs: round(sum(xs) / len(xs), 1)
    # piezas: mejor diámetro tocable por pieza y ancho (armado o desarmado)
    mejor = {}
    for w in R:
        for G in R[w]["grupos"]:
            for est in ("arm", "des"):
                for p in (G.get(est) or {}).get("piezas", []):
                    k = (w, G["lado"], p["id"]); mejor[k] = max(mejor.get(k, -1), p["d"])
    # «no se selecciona» solo si falla en todos los estados donde tiene área (armado y desarmado); si falla solo en uno, va como aviso
    estSel = {}
    for w in R:
        for G in R[w]["grupos"]:
            for est in ("arm", "des"):
                for p in (G.get(est) or {}).get("piezas", []):
                    if p["d"] > 0: estSel.setdefault((w, G["nombre"], p["n"]), []).append((est, p["sel"]))
    noSel = sorted(f"{w}:{g}:{n}" for (w, g, n), v in estSel.items() if not any(s for _, s in v))
    parcial = sorted({f"{g}:{n} ({e})" for (w, g, n), v in estSel.items() if any(s for _, s in v) for e, s in v if not s})
    if parcial: falla.append("aviso, no baja la nota: piezas que no responden en un estado y sí en el otro: " + ", ".join(parcial[:6]))
    d360 = [v for (w, l, i), v in mejor.items() if w == 360]
    chicas360 = sorted({f"{l}:{i[3:]}({v} px)" for (w, l, i), v in mejor.items() if w == 360 and v < 24})
    cero = sorted({f"{w}:{l}:{i[3:]}" for (w, l, i), v in mejor.items() if v <= 0})
    frac = sum(v >= 24 for v in d360) / max(1, len(d360))
    marcas = [(w, l, o) for w in R for l, o in R[w]["lados"].items()]
    mf = [f"{w}:{l}:{x}" for w, l, o in marcas for x in o["fallas"] + o["fuera"]]
    mr = [f"{w}:{l}:{x}" for w, l, o in marcas for x in o["roces"] + o["solapes"]]
    malto = min((o["altoMin"] for _, _, o in marcas if o["n"]), default=0)
    if not any(o["n"] for _, _, o in marcas): bloq.append("no se encontraron marcas de grupo visibles")
    torn = [f"{w}:{G['nombre']}:{t['t']}" for w in R for G in R[w]["grupos"] for est in ("arm", "des") for t in (G.get(est) or {}).get("torn", []) if not t["ok"]]
    chicos = [f"{w}: {b}" for w in R for b in R[w]["botonesChicos"]]
    chicos += [f"{w}: {b} (hoja)" for w in R for G in R[w]["grupos"] if "alTocar" in G for b in ((G["alTocar"].get("hoja") or {}).get("chicos") or [])]
    desb = [f"{w}: {x}" for w in R for x in R[w]["desborde"]]
    # 6. Pulgar (modelo v2): marcas, piezas tocables y su tamaño
    n6 = 5 if frac >= 1 else 4.5 if frac >= .9 else 4 if frac >= .75 else 3
    if mf or torn: n6 = min(n6, 3); falla.append("marcas que no reciben su toque: " + ", ".join((mf + torn)[:8]))
    if mr or chicos or desb or noSel: n6 = min(n6, 3.5)
    if malto < ALTO_MIN_MARCA: n6 = min(n6, 4); falla.append(f"marcas de grupo de {malto} px de alto (< {ALTO_MIN_MARCA})")
    if mr: falla.append("marcas que se rozan o se solapan: " + ", ".join(mr[:6]))
    if noSel: falla.append("piezas que no se seleccionan al tocarlas: " + ", ".join(noSel[:8]))
    if chicas360: falla.append(f"360: {len(chicas360)} de {len(d360)} piezas con área tocable < 24 px de diámetro: " + ", ".join(chicas360[:10]))
    if cero: falla.append("piezas sin área tocable en el dibujo (solo por la lista): " + ", ".join(cero[:10]))
    if chicos: falla.append("botones de menos de 44 px: " + "; ".join(chicos[:6]))
    otras = sorted({b for w in R for b in R[w]["botonesChicosOtras"]})
    if otras: falla.append(f"aviso: {len(otras)} botones < 44 px en otras pestañas, p. ej. " + "; ".join(otras[:3]))
    # 8. Protagonismo
    pct = min(d[w]["pctAncho"] for w in (1024, 1280, 1440))
    n8 = [escala(pct, 55, 50, 40, 35), escala(d[1280]["h"], 460, 420, 360, 300), escala(d[360]["h"], 260, 235, 210, 190)]
    # 9. Primer pantallazo (v2: vista general con Delantera | Trasera; al entrar a un grupo, dibujo y Desarmar)
    e = {w: next((G["entrada"] for G in R[w]["grupos"] if "entrada" in G), {}) for w in R}
    if not d[1280]["completo"]: a = 1; bloq.append("dibujo cortado a 1280×800")
    elif all(d[w]["ladoVisible"] and e[w].get("completo") and e[w].get("desarmar") for w in (1280, 1024)) and d[1024]["completo"]: a = 5
    elif d[1024]["completo"] and e[1280].get("desarmar"): a = 4
    else: a = 3
    b = (5 if e[390].get("desarmar") else 4) if d[390]["pestanas"] and d[390]["completo"] else 3 if d[390]["cortePct"] < 15 else 1
    ap = max(d[1280]["apoyoPct"], d[390]["apoyoPct"]); c = escala(ap, 15, 20, 30, 35, mayor=False)
    n9 = [a, b, c]
    for w in (1024, 1280, 1440):
        if not e[w].get("desarmar"): falla.append(f"{w}: al entrar a un grupo, «Desarmar» queda fuera de la pantalla")
    # 10. Espacio muerto
    hueco = max(col["hueco"] for w in (1024, 1280, 1440) for col in d[w]["cols"])
    vacia = R[1280]["fichaVacia"].lower()
    n10 = [escala(hueco, 10, 20, 35, 50, mayor=False), 5 if ("lista" in vacia or "buscar" in vacia or "toca un grupo" in vacia) else 4, 5]
    # 11. Proximidad
    g12 = next((G for G in R[1280]["grupos"] if "alTocar" in G), {}); g36 = next((G for G in R[360]["grupos"] if "alTocar" in G), {})
    fila_n = lambda f: 5 if f <= 1 else 4 if f == 2 else 3.5 if f == 3 else 3
    sobre = [f"{w}: {x}" for w in R for G in R[w]["grupos"] for x in G.get("controlesSobreDibujo", [])]
    # celular: hoja inferior o barra fija con el nombre; 4 si en reposo tapa la pieza elegida (> 20 %) o pasa del 50 % de la pantalla
    hojas = {w: (next((G for G in R[w]["grupos"] if "alTocar" in G), {}).get("alTocar") or {}).get("hoja") for w in (360, 390, 768)}
    def nota_hoja(h):
        if not h: return 3
        return 4 if (h["tapaPiezaPct"] > 20 or h["pct"] > 50 or not h["nombre"]) else 5
    n_hoja = min(nota_hoja(h) for h in hojas.values())
    for w, h in hojas.items():
        if h and h["tapaPiezaPct"] > 20: falla.append(f"{w}: la hoja inferior tapa el {h['tapaPiezaPct']} % de la pieza elegida")
        if h and h["pct"] > 50: falla.append(f"{w}: la hoja inferior ocupa el {h['pct']} % de la pantalla al abrirse (pedir ≤ 50 %)")
        if h and h["chicos"]: falla.append(f"{w}: botones < 44 px en la hoja inferior: " + ", ".join(h["chicos"][:4]))
    n11 = [5 if g12.get("alTocar", {}).get("fichaVisible") else 3, n_hoja,
           1 if sobre else m([fila_n(g12.get("filasControles", 9)), fila_n(g36.get("filasControles", 9))])]
    if sobre: bloq.append("controles encima del dibujo: " + "; ".join(sobre))
    if not g12.get("alTocar", {}).get("fichaVisible"): falla.append("1280: la ficha no queda a la vista al tocar una pieza")
    if not g36.get("alTocar", {}).get("barraFija"): falla.append("360: no aparece la barra fija al tocar una pieza")
    # 12. Ritmo
    difs = [abs(d[w]["cols"][0]["top"] - d[w]["cols"][1]["top"]) for w in (1024, 1280, 1440) if len(d[w]["cols"]) >= 2]
    colmin = min(col["w"] for w in d for col in d[w]["cols"])
    n12 = [5 if max(difs or [0]) <= 2 else 4 if max(difs) <= 8 else 3, escala(colmin, 300, 280, 240, 220), 1 if desb else 5, 4]
    if desb: bloq.append("desborde horizontal: " + "; ".join(desb))
    errores = sorted({x for w in R for x in R[w]["errores"]})
    if errores: falla.append("errores de consola: " + " | ".join(errores[:5]))
    v = R[1280].get("v3d")
    if v and v.get("hay") and not v.get("ok"): falla.append(f"visor 3D no abrió ({v.get('pieza')}): {v.get('estado')}")
    N = {"6": n6, "8": m(n8), "9": m(n9), "10": m(n10), "11": m(n11), "12": m(n12)}
    # medidas que alimentan criterios a ojo: toques hasta la ficha (criterio 1) y largo de la ficha a 360 (criterio 3)
    tq = max(next((G for G in R[w]["grupos"] if "toquesFicha" in G), {}).get("toquesFicha", 99) for w in R)
    medidas_ms = [G["desarmeMs"] for w in R for G in R[w]["grupos"] if G.get("desarmeMs")]
    espera = round(max(medidas_ms) / 1000, 1) if medidas_ms else round(max([G.get("pasos", 0) for w in R for G in R[w]["grupos"]] or [0]) * 1.3, 1)
    sub1 = 5 if tq <= 2 and espera <= 5 else 4 if tq <= 3 and espera <= 5 else 3
    rp = (R[360].get("ficha") or {}).get("reparaPantallas"); pp = (R[360].get("ficha") or {}).get("pedirPantallas")
    sub3 = None if rp is None else 5 if rp <= 1.5 else 4 if rp <= 2.5 else 3
    if tq > 3: falla.append("en algún ancho no se llega al contenido de la ficha con 3 toques")
    if sub3 is not None and sub3 < 5: falla.append(f"360: «¿Se repara o se cambia?» queda a {rp} pantallas del inicio de la ficha (pedir ≤ 1,5)")
    fn = funciona_minimo(R, falla, bloq)
    crudo = sorted({c for w in R for c in (R[w].get("crudo") or [])})
    if crudo: bloq.append("marcado [[n|texto]] sin renderizar en la página: " + "; ".join(crudo[:3]))
    return N, falla, bloq, {"funciona": fn, "piezas360": len(d360), "piezas360_24": sum(v >= 24 for v in d360), "diam360": sorted(d360), "8": n8, "9": n9, "10": n10, "11": n11, "12": n12,
                            "toques": {"visible": tq, "adentro": tq + 1, "esperaDesarme_s": espera, "subnota_criterio1": sub1},
                            "ficha360": {"reparaPantallas": rp, "pedirPantallas": pp, "subnota_criterio3": sub3}, "hojas": hojas}



class Manejador(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=RAIZ, **k)

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    # Cada archivo se lee una vez, con reintentos, y se guarda en memoria: con varias pestañas a la vez,
    # leer en paralelo desde OneDrive llegó a fallar (MemoryError en copyfileobj).
    CACHE, CANDADO = {}, threading.Lock()

    def do_GET(self):
        ruta = os.path.normpath(os.path.join(RAIZ, urlparse(self.path).path.lstrip("/")))
        if not ruta.startswith(RAIZ) or not os.path.isfile(ruta):
            return self.send_error(404)
        with self.CANDADO:
            datos = self.CACHE.get(ruta)
            if datos is None:
                for intento in range(4):
                    try:
                        with open(ruta, "rb") as f:
                            datos = f.read()
                        break
                    except (OSError, MemoryError):
                        time.sleep(0.2 * (intento + 1))
                if datos is None:
                    return self.send_error(500, "no se pudo leer")
                self.CACHE[ruta] = datos
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(ruta)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)


class CDP:
    """Cliente mínimo del protocolo de DevTools sobre websocket (solo biblioteca estándar)."""

    def __init__(self, ws_url):
        u = urlparse(ws_url)
        self.s = socket.create_connection((u.hostname, u.port), timeout=300)   # el evaluate puede durar hasta 280 s en láminas grandes
        clave = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET {u.path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {clave}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        resp = b""
        while b"\r\n\r\n" not in resp:
            resp += self.s.recv(1)
        if b" 101 " not in resp.split(b"\r\n")[0]:
            raise RuntimeError("DevTools no aceptó el websocket")
        self.n = 0

    def _leer(self, k):
        b = b""
        while len(b) < k:
            x = self.s.recv(k - len(b))
            if not x: raise RuntimeError("se cerró DevTools")
            b += x
        return b

    def _recibir(self):
        datos = b""
        while True:
            c0, c1 = self._leer(2)
            largo = c1 & 127
            if largo == 126: largo = struct.unpack(">H", self._leer(2))[0]
            elif largo == 127: largo = struct.unpack(">Q", self._leer(8))[0]
            datos += self._leer(largo)
            if c0 & 0x80:
                return datos.decode("utf-8", "replace")

    def __call__(self, metodo, **params):
        self.n += 1
        carga = json.dumps({"id": self.n, "method": metodo, "params": params}).encode()
        mascara = os.urandom(4); L = len(carga)
        cab = bytes([0x81]) + (bytes([0x80 | L]) if L < 126 else bytes([0x80 | 126]) + struct.pack(">H", L) if L < 65536 else bytes([0x80 | 127]) + struct.pack(">Q", L))
        self.s.sendall(cab + mascara + bytes(b ^ mascara[i % 4] for i, b in enumerate(carga)))
        while True:
            m = json.loads(self._recibir())
            if m.get("id") == self.n:
                if "error" in m: raise RuntimeError(f"{metodo}: {m['error']}")
                return m.get("result", {})


def buscar_chrome(dado):
    if dado:
        return dado
    for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", shutil.which("chrome") or "", shutil.which("google-chrome") or "",
              shutil.which("chromium") or ""]:
        if c and os.path.exists(c):
            return c
    sys.exit("No encontré Chrome ni Edge: pasa la ruta con --chrome")


def lanzar(chrome, perfil):
    """Abre Chrome sin ventana con DevTools en un puerto libre y devuelve (proceso, puerto)."""
    p = subprocess.Popen([chrome, "--headless=new", "--remote-debugging-port=0", f"--user-data-dir={perfil}", "--hide-scrollbars",
                          "--no-first-run", "--no-default-browser-check", "--disable-extensions", "--mute-audio",
                          "--disable-background-timer-throttling", "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows",
                          "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "about:blank"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    archivo = os.path.join(perfil, "DevToolsActivePort")
    for _ in range(150):
        if os.path.exists(archivo):
            try:  # Chrome puede tenerlo abierto mientras lo escribe (en Windows da PermissionError): se reintenta
                with open(archivo) as f:
                    linea = f.readline().strip()
            except OSError:
                linea = ""
            if linea: return p, int(linea)
        time.sleep(0.1)
    cerrar(p); sys.exit("Chrome no abrió DevTools")


def cerrar(proc, puerto=None):
    """Cierra Chrome entero. En Windows, proc.kill() solo mata el proceso principal y deja vivos los hijos
    (renderer, GPU, red): en una corrida llegó a haber 43 chrome.exe abiertos. Se pide Browser.close por DevTools,
    se espera y, si sigue vivo, se mata el árbol con taskkill /T."""
    if puerto:
        try:
            ws = json.load(urllib.request.urlopen(f"http://127.0.0.1:{puerto}/json/version", timeout=3))["webSocketDebuggerUrl"]
            CDP(ws)("Browser.close")
        except Exception:
            pass
    try:
        proc.wait(timeout=5)
    except Exception:
        pass
    if proc.poll() is None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            proc.kill()


def resolver(p):
    """Mismo formato para --pagina y --captura: absoluta; con carpeta, relativa a la raíz del proyecto; nombre solo, en motor/."""
    if os.path.isabs(p): return p
    if "/" in p or "\\" in p: return os.path.abspath(os.path.join(RAIZ, p))
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), p)


FINAL = False   # --final: medición final corta; «Cómo funciona» y el solape del desarme los cubre chequeo_rapido.py (autocontrol --previa)
SOLO_CAPTURA = False   # --solo-captura: sin medidor, solo la captura del armado limpio
SOLAPE = None   # --solape: solo 1280, solapamiento del desarme general (y capturas de estados con --captura-desarme / --captura-trans)
UMBRAL_SOLAPE = 20   # % de una pieza tapada por otras en el desarme general: más es bloqueante (de 8 a 20, aviso)
JS_SOLAPE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "medir_solape.js"), encoding="utf-8").read()
ESTADOS = {   # estados para capturar (v2): desarme general completo, y Transparente dentro del grupo más grande
    "desarme": "(async()=>{const S=ms=>new Promise(r=>setTimeout(r,ms));const ad=document.getElementById('bAdel');let g=0;while(!ad.disabled&&g++<120){ad.click();await S(15)}"
               "await S(700);document.getElementById('lamina').scrollIntoView({block:'center'});await S(300);return 1})()",
    "trans": "(async()=>{const S=ms=>new Promise(r=>setTimeout(r,ms));const it=document.getElementById('iTrans');if(!it)return 0;"
             "const m=[...document.querySelectorAll('#lamina .esq-marca-g')].filter(e=>e.getBoundingClientRect().width).map(e=>[e,document.querySelectorAll('#capas .esq-pz[data-g=\"'+e.dataset.g+'\"]').length]).sort((a,b)=>b[1]-a[1])[0];"
             "if(m)m[0].dispatchEvent(new MouseEvent('click',{bubbles:true}));await S(500);if(it.getAttribute('aria-pressed')!=='true')it.click();await S(600);"
             "document.getElementById('lamina').scrollIntoView({block:'center'});await S(300);return 1})()",
}


def solape(c):
    # encuadres al instante (sin la animación de 650 ms con rAF, que en Chrome sin ventana puede quedar a medias)
    c("Emulation.setEmulatedMedia", features=[{"name": "prefers-reduced-motion", "value": "reduce"}])
    r = c("Runtime.evaluate", expression="(async()=>{" + JS_SOLAPE + ";return JSON.stringify(await medir_solape())})()", awaitPromise=True, returnByValue=True, timeout=120000)
    if "exceptionDetails" in r: return {"fatal": json.dumps(r["exceptionDetails"], ensure_ascii=False)[:300]}
    return json.loads(r["result"]["value"])


def recargar(c):
    c("Page.reload", ignoreCache=False)
    for _ in range(100):
        time.sleep(0.1)
        v = c("Runtime.evaluate", expression="document.readyState+'|'+!!document.querySelector('#lamina .esq-pz')", returnByValue=True)["result"].get("value", "")
        if v == "complete|true": break
    time.sleep(1.5)


def medir_ancho(puerto_cdp, url, w, h, salida, captura=None):
    """Una pestaña por ancho: viewport exacto, «reducir movimiento», gancho de errores antes de la página y el medidor."""
    try:
        # Cada ancho en su propia ventana: una pestaña de fondo pausa rAF y las animaciones del desarme
        nav = CDP(json.load(urllib.request.urlopen(f"http://127.0.0.1:{puerto_cdp}/json/version", timeout=20))["webSocketDebuggerUrl"])
        tid = nav("Target.createTarget", url="about:blank", newWindow=True, width=w, height=h)["targetId"]
        c = CDP(f"ws://127.0.0.1:{puerto_cdp}/devtools/page/{tid}")
        c("Emulation.setFocusEmulationEnabled", enabled=True)
        c("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=w < 768)
        c("Page.enable"); c("Page.addScriptToEvaluateOnNewDocument", source=GANCHO)
        c("Page.navigate", url=url)
        for _ in range(400):
            v = c("Runtime.evaluate", expression="location.href.split('?')[0]+'|'+document.readyState", returnByValue=True)["result"].get("value", "")
            if v == url + "|complete": break
            time.sleep(0.1)
        if SOLO_CAPTURA: salida[w] = {}
        elif SOLAPE is not None:
            c("Emulation.setEmulatedMedia", features=[{"name": "prefers-reduced-motion", "value": "reduce"}])
            recargar(c); salida[w] = {"solape": solape(c)}
            for est, ruta in SOLAPE.items():
                recargar(c); c("Runtime.evaluate", expression=ESTADOS[est], awaitPromise=True, returnByValue=True, timeout=60000)
                img = c("Page.captureScreenshot", format="jpeg", quality=70, clip={"x": 0, "y": 0, "width": w, "height": h, "scale": 0.5})
                with open(ruta, "wb") as f: f.write(base64.b64decode(img["data"]))
            return
        else:
            if FINAL: c("Runtime.evaluate", expression="window.__ESQ_FINAL=true")
            r = c("Runtime.evaluate", expression=despacho(MODELO), awaitPromise=True, returnByValue=True, timeout=280000)
            if "exceptionDetails" in r:
                salida[w] = {"fatal": json.dumps(r["exceptionDetails"], ensure_ascii=False)[:400]}; return
            salida[w] = json.loads(r["result"]["value"])
            if w == 1280 and salida[w].get("modelo") == "v2" and not FINAL:
                c("Emulation.setEmulatedMedia", features=[{"name": "prefers-reduced-motion", "value": "reduce"}])
                recargar(c); salida[w]["solape"] = solape(c)
        if captura:
            # la captura es del armado limpio (para juzgar el dibujo): se recarga la página, sin grupo ni pieza elegida
            c("Page.reload", ignoreCache=False)
            for _ in range(100):
                time.sleep(0.1)
                v = c("Runtime.evaluate", expression="document.readyState+'|'+!!document.querySelector('#lamina .esq-pz')", returnByValue=True)["result"].get("value", "")
                if v == "complete|true": break
            time.sleep(1.5)
            c("Runtime.evaluate", expression="scrollTo(0,0)")
            time.sleep(0.4)
            img = c("Page.captureScreenshot", format="jpeg", quality=70, clip={"x": 0, "y": 0, "width": w, "height": h, "scale": 0.5})
            with open(captura, "wb") as f:
                f.write(base64.b64decode(img["data"]))
    except Exception as e:
        salida[w] = {"fatal": f"{type(e).__name__}: {e}"}


# ---------- notas (rúbrica v2, criterios-ux.md) ----------
def escala(v, t5, t4, t3, tb, mayor=True):
    """Nota de una medida: 5/4/3, 2 entre la columna 3 y el bloqueante, 1 = bloqueante."""
    ok = (lambda a, b: a >= b) if mayor else (lambda a, b: a <= b)
    if ok(v, t5): return 5
    if ok(v, t4): return 4
    if ok(v, t3): return 3
    return 2 if not ((v < tb) if mayor else (v > tb)) else 1


def notas(R):
    d = {w: R[w]["dist"] for w in R}
    falla, bloq = [], []
    m = lambda xs: round(sum(xs) / len(xs), 1)
    # 6. Pulgar
    tq = {w: R[w]["toques"] for w in R}
    centros = sum(t["centro"] for w in tq for t in tq[w].values()); total = sum(t["total"] for w in tq for t in tq[w].values())
    roces = [f"{w}:{k}:{r}" for w in tq for k, t in tq[w].items() for r in t["roces"]]
    fallas = [f"{w}:{k}:{f}" for w in tq for k, t in tq[w].items() for f in t["fallas"]]
    chicos = [f"{w}: {b}" for w in R for b in R[w]["botonesChicos"]]
    desb = [f"{w}: {x}" for w in R for x in R[w]["desborde"]]
    sobre = [f"{w}: {x}" for w in R for x in R[w]["controles"]["sobreDibujo"]]
    r360 = min(t["radioMin"] for t in tq[360].values()); p360 = len(tq[360]["desT"]["pares24"])
    lista_ok = not (R[360].get("lista") or {}).get("deslizable", False)
    if fallas or sobre: n6 = 3; falla.append("números que no reciben su toque: " + ", ".join((fallas + sobre)[:8]))
    elif roces or chicos or desb: n6 = 3.5
    elif r360 >= 12 and p360 == 0: n6 = 5
    elif lista_ok: n6 = 4.5
    else: n6 = 4
    if sobre: bloq.append("controles encima de los números")
    if roces: falla.append("roces a ±9 px: " + ", ".join(roces[:8]))
    if chicos: falla.append("botones de menos de 44 px: " + "; ".join(chicos[:6]))
    otras = sorted({b.split(" (")[0] + " (" + b.split(" (")[-1] + f" a {w}" for w in R for b in R[w].get("botonesChicosOtras", [])})
    if otras: falla.append(f"aviso, no baja la nota: {len(otras)} botones de menos de 44 px en otras pestañas, p. ej. " + "; ".join(otras[:4]))
    if p360: falla.append(f"360: {p360} pares de números a < 24 px (mín. {tq[360]['desT']['distMin']} px), radio mín. {r360} px" + ("" if lista_ok else "; y la lista de piezas se desliza (control equivalente incómodo)"))
    # 8. Protagonismo
    pct = min(d[w]["pctAncho"] for w in (1024, 1280, 1440))
    n8 = [escala(pct, 55, 50, 40, 35), escala(d[1280]["h"], 460, 420, 360, 300), escala(d[360]["h"], 260, 235, 210, 190)]
    if 1 in n8: bloq.append("dibujo demasiado chico")
    # 9. Primer pantallazo
    c12, c10 = d[1280], d[1024]
    if not c12["completo"]: a = 1; bloq.append(f"dibujo cortado a 1280×800 (termina en {c12['bottom']} px)")
    elif c12["desarmar"] and c10["completo"] and c10["desarmar"]: a = 5
    elif c12["desarmar"] and c10["completo"]: a = 4
    else: a = 3
    c39 = d[390]
    if c39["pestanas"] and c39["completo"]: b = 5 if c39["desarmar"] else 4
    elif c39["cortePct"] < 15: b = 3
    else: b = 1; bloq.append("dibujo cortado ≥ 15 % a 390")
    ap = max(d[1280]["apoyoPct"], d[390]["apoyoPct"]); c = escala(ap, 15, 20, 30, 35, mayor=False)
    if c == 1: bloq.append("textos de apoyo > 35 %")
    n9 = [a, b, c]
    for w in (1024, 1280, 1440):
        if not d[w]["desarmar"]: falla.append(f"{w}: «Desarmar» fuera de la pantalla al llegar (termina en {d[w]['desarmarFin']} px)")
    # 10. Espacio muerto
    hueco = max(col["hueco"] for w in (1024, 1280, 1440) for col in d[w]["cols"])
    vacia = R[1280]["fichaVacia"]
    n10 = [escala(hueco, 10, 20, 35, 50, mayor=False), 5 if any(k in vacia.lower() for k in ("plan", "km", "estado", "próxim")) else 4, 5]
    if n10[0] == 1: bloq.append(f"hueco de {hueco} % bajo una columna")
    # 11. Proximidad
    t12 = R[1280].get("alTocar") or {}; t36 = R[360].get("alTocar") or {}
    f12 = R[1280]["controles"]["filas"]; f36 = R[360]["controles"]["filas"]
    fila_n = lambda f: 5 if f <= 1 else 4 if f == 2 else 3.5 if f == 3 else 3
    n11 = [5 if t12.get("fichaVisible") else 3, 5 if t36.get("barraFija") else 3, 1 if sobre else m([fila_n(f12), fila_n(f36)])]
    if not t12.get("fichaVisible"): falla.append("1280: la ficha no queda a la vista al tocar un número")
    if not t36.get("barraFija"): falla.append("360: no aparece la barra fija al tocar un número")
    # 12. Ritmo
    difs = [abs(d[w]["cols"][0]["top"] - d[w]["cols"][1]["top"]) for w in (1024, 1280, 1440) if len(d[w]["cols"]) >= 2]
    colmin = min(col["w"] for w in d for col in d[w]["cols"])
    tres = any(len(d[w]["cols"]) >= 3 for w in d if w < 1200)
    n12 = [5 if max(difs or [0]) <= 2 else 4 if max(difs) <= 8 else 3, 1 if tres else escala(colmin, 300, 280, 240, 220), 1 if desb else 5, 4]
    if desb: bloq.append("desborde horizontal: " + "; ".join(desb))
    # errores y 3D
    errores = sorted({f"{e}" for w in R for e in R[w]["errores"]})
    if errores: falla.append("errores de consola: " + " | ".join(errores[:5]))
    v = R[1280].get("v3d")
    if v and v.get("hay") and not v.get("ok"): falla.append(f"visor 3D no abrió ({v.get('pieza')}): {v.get('estado')}")
    N = {"6": n6, "8": m(n8), "9": m(n9), "10": m(n10), "11": m(n11), "12": m(n12)}
    return N, falla, bloq, {"centros": f"{centros}/{total}", "roces": len(roces), "radio360": r360, "pares24_360": p360, "8": n8, "9": n9, "10": n10, "11": n11, "12": n12}


MODELO = "auto"


def funciona_minimo(R, falla, bloq):
    """Mínimo medible de «Cómo funciona» (criterios-ux.md): etiquetas sin montarse, letra ≥ 12 px a 360 y 1280,
    cada paso con cambios visibles, texto ≤ 250 caracteres (estos cuatro son requisito para aprobar);
    indicador físico y detalle del dibujo son alertas para revisar a ojo."""
    f36 = R.get(360, {}).get("funciona") or {}; f12 = R.get(1280, {}).get("funciona") or {}
    if not f36 or f36.get("sinEsquema"):
        return {"hay": False}
    sol = sorted(set(f36.get("solapes", [])) | set(f12.get("solapes", [])))
    l36, l12 = f36.get("letraMin", 0), f12.get("letraMin", 0)
    cam = f36.get("cambios", []); pocos = [i + 2 for i, c in enumerate(cam) if c <= 1]; justos = [i + 2 for i, c in enumerate(cam) if c == 2]
    txt = max(f36.get("textoMax", 0), f12.get("textoMax", 0))
    ind = f36.get("indicadores", []); sin_ind = f36.get("sinIndicadorDeclarado")
    poco_det = f36.get("formas", 0) < 30 and f36.get("degradados", 0) < 3
    req = {"etiquetas": not sol, "letra": l36 >= 12 and l12 >= 12, "cambios": not pocos, "texto": txt <= 250}
    if sol: bloq.append("Cómo funciona: etiquetas montadas: " + "; ".join(sol[:4]))
    if not req["letra"]: bloq.append(f"Cómo funciona: letra mínima {l36} px a 360 y {l12} px a 1280 (pedir ≥ 12)")
    if pocos: bloq.append("Cómo funciona: pasos sin cambio visible (0 o 1 elemento): " + ", ".join(map(str, pocos)))
    if txt > 250: bloq.append(f"Cómo funciona: un paso tiene {txt} caracteres (pedir ≤ 250)")
    if justos: falla.append("aviso: Cómo funciona con pasos de apenas 2 cambios: " + ", ".join(map(str, justos)))
    if not ind and not sin_ind: falla.append("alerta: Cómo funciona sin indicador físico (rpm, presión, °C, %, L…); si no aplica, declarar funciona.sinIndicador en el JSON")
    if poco_det: falla.append(f"alerta: Cómo funciona con poco detalle ({f36.get('formas')} formas, {f36.get('degradados')} degradados): revisar a ojo si las piezas son reconocibles")
    return {"hay": True, "cumpleMinimo": all(req.values()), "requisitos": req, "solapes": sol, "letra360": l36, "letra1280": l12, "pasos": f36.get("pasos"),
            "cambios": cam, "textoMax": txt, "indicadores": ind, "sinIndicadorDeclarado": sin_ind, "formas": f36.get("formas"), "degradados": f36.get("degradados"), "pocoDetalle": poco_det}


def imprimir_v2(R, b):
    if FINAL: print("  (modo final: «Cómo funciona» y solape del desarme los revisa chequeo_rapido.py)")
    for w in R:
        x = R[w]; dd = x["dist"]; gs = x["grupos"]; e = next((G["entrada"] for G in gs if "entrada" in G), {})
        mk = " · ".join(f"{l}: {o['n']} marcas de {o['altoMin']} px, fallas {len(o['fallas'])}, solapes {len(o['solapes'])}" for l, o in x["lados"].items())
        h = (next((G for G in gs if "alTocar" in G), {}).get("alTocar") or {}).get("hoja")
        hs = f" · hoja {h['pct']} % (tapa {h['tapaPiezaPct']} % de la pieza)" if (h and w < 960) else ""
        print(f"  {w}×{x['alto']}: dibujo {dd['w']}×{dd['h']} {'completo' if dd['completo'] else 'CORTADO'} · apoyo {dd['apoyoPct']} % · "
              f"en grupo: Desarmar {'sí' if e.get('desarmar') else 'no'} · {mk}{hs}")
    li = R[1280].get("lista"); fi = R[1280].get("ficha")
    if li: print(f"  Lista: {li['grupos']} grupos ({li['abiertos']} abiertos), {li['items']} piezas; buscador «bomba» → {li.get('buscarBomba')}")
    if fi: print(f"  Ficha: {len(fi['secciones'])} secciones, {fi['alto']} px a 1280 / {(R[360].get('ficha') or {}).get('alto')} px a 360; ‹ › {'funcionan' if fi.get('siguienteCambia') else 'NO'}")
    print(f"  Piezas a 360: {b['piezas360_24']} de {b['piezas360']} con área tocable ≥ 24 px de diámetro")
    fn = b.get("funciona") or {}
    if fn.get("hay"):
        ok = lambda v: "✓" if v else "✗"; rq = fn["requisitos"]
        print(f"  Cómo funciona: {fn['pasos']} pasos · etiquetas {ok(rq['etiquetas'])} · letra {fn['letra360']}/{fn['letra1280']} px {ok(rq['letra'])} · "
              f"cambios por paso {fn['cambios']} {ok(rq['cambios'])} · texto ≤ {fn['textoMax']} car. {ok(rq['texto'])} · "
              f"indicador {'declarado que no aplica' if fn['sinIndicadorDeclarado'] else (', '.join(fn['indicadores'][:2]) or 'ninguno')} · "
              f"detalle {fn['formas']} formas / {fn['degradados']} degradados{' (poco)' if fn['pocoDetalle'] else ''} → mínimo {'CUMPLE' if fn['cumpleMinimo'] else 'NO CUMPLE'}")
    t = b["toques"]; f3 = b["ficha360"]
    print(f"  Para criterios a ojo: toques hasta la ficha {t['visible']} (adentro {t['adentro']}, desarme ≤ {t['esperaDesarme_s']} s) → subnota del 1: {t['subnota_criterio1']} · "
          f"ficha a 360: «¿Se repara?» a {f3['reparaPantallas']} pantallas, «Pedir» a {f3['pedirPantallas']} → subnota del 3: {f3['subnota_criterio3']}")


def despacho(modelo):
    """Expresión que espera la lámina, detecta el modelo (v2: marcas de grupo; v1: números) y corre su medidor."""
    v1 = MEDIDOR.strip().rstrip(";"); v2 = MEDIDOR_V2.strip().rstrip(";")
    return ("(async()=>{const S=ms=>new Promise(r=>setTimeout(r,ms));"
            "for(let i=0;i<200&&!document.querySelector('#lamina .esq-marca-g, #lamina .esq-bola');i++)await S(100);"
            f"const hay2=!!document.querySelector('#lamina .esq-marca-g'),m='{modelo}',usar=m==='auto'?(hay2?'v2':'v1'):m;"
            f"const r=JSON.parse(usar==='v2'?await {v2}:await {v1});r.modelo=usar;return JSON.stringify(r)}})()")


def main():
    global MODELO
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pagina", help="ruta de la lámina, relativa a la raíz del proyecto (o absoluta)")
    ap.add_argument("--json", action="store_true"); ap.add_argument("--captura"); ap.add_argument("--chrome")
    ap.add_argument("--solo-captura", action="store_true", help="solo el ancho 1280 y la captura (para mirarla antes de dar las notas --ojo)")
    ap.add_argument("--solape", action="store_true", help="solo 1280: solapamiento de las piezas en el «Desarmar todo» de la vista general (segundos)")
    ap.add_argument("--captura-desarme", help="con --solape: captura del desarme general (escala 0,5)")
    ap.add_argument("--captura-trans", help="con --solape: captura de Transparente dentro del grupo más grande (escala 0,5)")
    ap.add_argument("--modelo", choices=["auto", "v2", "v1"], default="auto", help="v2 = marcas de grupo (estándar); v1 = números del modelo viejo; auto = lo detecta")
    ap.add_argument("--espera", type=int, default=480, help="segundos máximos de espera (las láminas de muchos grupos con «Cómo funciona» pueden pasar de 300 con la máquina cargada)")
    ap.add_argument("--ojo", help="notas a ojo de los criterios 1,2,3,4,5,7 separadas por coma (p. ej. 4.5,4.5,4,4,4,4.5) para dar el promedio total")
    ap.add_argument("--final", action="store_true", help="medición final corta: sin «Cómo funciona» ni solape del desarme (ya los revisa chequeo_rapido.py)")
    a = ap.parse_args(); MODELO = a.modelo
    global FINAL; FINAL = a.final
    global SOLO_CAPTURA; SOLO_CAPTURA = a.solo_captura
    global SOLAPE
    if a.solape: SOLAPE = {k: resolver(v) for k, v in (("desarme", a.captura_desarme), ("trans", a.captura_trans)) if v}
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    ruta = os.path.relpath(resolver(a.pagina), RAIZ).replace(os.sep, "/")
    if not os.path.exists(os.path.join(RAIZ, ruta)): sys.exit(f"No existe {ruta}")
    chrome = buscar_chrome(a.chrome)
    ThreadingHTTPServer.request_queue_size = 128  # con 5 (por omisión) Windows rechaza conexiones cuando cargan 6 pestañas a la vez
    ThreadingHTTPServer.daemon_threads = True
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Manejador); puerto = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{puerto}/{ruta}"
    tmp = tempfile.mkdtemp(prefix="medir_lamina_"); t0 = time.time(); RESULTADOS = {}
    proc, pcdp = lanzar(chrome, tmp)
    try:
        hilos = [threading.Thread(target=medir_ancho, args=(pcdp, base, w, h, RESULTADOS, resolver(a.captura) if a.captura and w == 1280 else None), daemon=True)
                 for w, h in ANCHOS if not (a.solo_captura or a.solape) or w == 1280]
        for t in hilos: t.start()
        for t in hilos: t.join(max(1, a.espera - (time.time() - t0)))
    finally:
        cerrar(proc, pcdp); srv.shutdown(); time.sleep(0.5); shutil.rmtree(tmp, ignore_errors=True)
    if a.solape:
        x = RESULTADOS.get(1280, {}); print(f"{ruta} · {time.time() - t0:.0f} s"); print(texto_solape(x.get("solape") or x))
        for l, o in ((x.get("solape") or {}).get("lados") or {}).items():
            for q in o["piezas"]:
                if q.get("caja"): print(f"  {l} {q['id']} {q['caja']} bajo " + " ".join(f"{i}{c}" for i, c in q["cajasPor"]))
        d = (x.get("solape") or {}).get("dbg")
        if d: print(d)
        return
    if a.solo_captura:
        print(f"captura previa: {resolver(a.captura) if a.captura else '(sin --captura)'} · {time.time() - t0:.0f} s"); return
    faltan = [w for w, _ in ANCHOS if w not in RESULTADOS]
    if faltan: sys.exit(f"Sin resultado en {faltan} tras {a.espera} s")
    fatales = {w: RESULTADOS[w]["fatal"] for w in RESULTADOS if RESULTADOS[w].get("fatal")}
    if fatales: sys.exit("Falló el medidor: " + json.dumps(fatales, ensure_ascii=False))
    R = dict(sorted(RESULTADOS.items()))
    modelo = R[360].get("modelo", "v1")
    N, falla, bloq, base_n = (notas_v2 if modelo == "v2" else notas)(R)
    prom = round(sum(N.values()) / len(N), 2)
    aprueba = not bloq and min(N.values()) >= 4
    if a.json:
        print(json.dumps({"pagina": ruta, "modelo": modelo, "notas": N, "promedio": prom, "bloqueantes": bloq, "falla": falla, "base": base_n, "medidas": R}, ensure_ascii=False, indent=1)); return
    print(f"{ruta} · {time.time() - t0:.0f} s · 6 anchos · modelo {modelo}")
    if modelo == "v2":
        imprimir_v2(R, base_n)
    for w in (R if modelo == "v1" else []):
        x = R[w]; dd = x["dist"]; tq = x["toques"]
        print(f"  {w}×{x['alto']}: dibujo {dd['w']}×{dd['h']} ({dd['pctAncho']} %) {'completo' if dd['completo'] else 'CORTADO'} · Desarmar {'sí' if dd['desarmar'] else 'no'} · "
              f"apoyo {dd['apoyoPct']} % · toques {sum(t['centro'] for t in tq.values())}/{sum(t['total'] for t in tq.values())} · roces {sum(len(t['roces']) for t in tq.values())} · "
              f"radio {min(t['radioMin'] for t in tq.values())} · pares<24 {len(tq['desT']['pares24'])} · filas de controles {x['controles']['filas']}")
    v = R[1280].get("v3d")
    if v is not None: print("  3D: " + ("sin forma3d" if not v.get("hay") else f"{'abre' if v.get('ok') else 'NO ABRE'} ({v.get('pieza')}, {v.get('estado')}, {v.get('lienzo', '')})"))
    print("Notas estimadas (criterios medibles): " + " · ".join(f"{k}: {v}" for k, v in N.items()) + f"  → promedio {prom}")
    print(f"Bloqueantes: {'; '.join(bloq) or 'ninguno'} · Medible {'APRUEBA' if aprueba else 'NO APRUEBA'}" + ("" if a.ojo else " (faltan las notas a ojo 1-5 y 7: --ojo)"))
    if a.ojo:
        ojo = [float(x) for x in a.ojo.replace(";", ",").split(",")]
        if len(ojo) == 6:
            total = round((sum(ojo) + sum(N.values())) / 12, 2)
            ok = aprueba and min(ojo) >= 4 and total >= 4
            print(f"Con los criterios a ojo (1,2,3,4,5,7 = {a.ojo}): promedio de los 12 = {total} → {'APRUEBA' if ok else 'NO APRUEBA'}")
    for f in falla: print("  - " + f)


if __name__ == "__main__":
    main()
