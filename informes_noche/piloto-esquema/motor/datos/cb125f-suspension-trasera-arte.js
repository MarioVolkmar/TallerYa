/* Arte de la figura F-22-1 de la Honda CB 125F GLH125SH (tijera, cadena y guardacadena): dibujos propios de TallerYa.
   Vista desde el lado izquierdo (el de la cadena), en «caballera»: la profundidad va hacia arriba a la derecha (vector B).
   El amortiguador (fig. F-23) y la rueda (fig. F-13-1) van de contexto. Estilo y ayudas tomados de nkd-transmision-arte.js.
   Posiciones en datos/cb125f-suspension-trasera.json. */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["cb125f-suspension-trasera"]=(function(){
"use strict";
const B=[0.5,-0.32];
const f=n=>Math.round(n*10)/10;
function extruir(d,t,fill){const n=Math.max(2,Math.round(t/4));let r=`<path d="${d}" fill-rule="evenodd" transform="translate(${f(B[0]*t)} ${f(B[1]*t)})" fill="${fill}" stroke="#1b2023" stroke-width="1"/>`;
  for(let i=n-1;i>=1;i--)r+=`<path d="${d}" fill-rule="evenodd" transform="translate(${f(B[0]*t*i/n)} ${f(B[1]*t*i/n)})" fill="${fill}"/>`;return r}
function resorte(x1,y1,x2,y2,n,a,col){ // resorte de lado entre dos puntos
  const dx=x2-x1,dy=y2-y1,L=Math.hypot(dx,dy),ux=dx/L,uy=dy/L,nx=-uy,ny=ux;let d="";
  for(let i=0;i<=n*2;i++){const t=i/(n*2),s=(i%2?1:-1)*a;d+=(i?"L":"M")+f(x1+dx*t+nx*s)+" "+f(y1+dy*t+ny*s)+" "}
  return `<path d="${d}" fill="none" stroke="${col}" stroke-width="6" stroke-linejoin="round"/>`;
}

const DEFS=`
<radialGradient id="gFondo" cx="48%" cy="48%" r="70%"><stop offset="0" stop-color="#232c2f"/><stop offset="1" stop-color="#111517"/></radialGradient>
<linearGradient id="stAcero" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef0f1"/><stop offset=".5" stop-color="#a7aeb2"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
<linearGradient id="stCromo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6f8f9"/><stop offset=".35" stop-color="#a3abb0"/><stop offset=".55" stop-color="#eef1f2"/><stop offset="1" stop-color="#5d656a"/></linearGradient>
<linearGradient id="stGris" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9aa3a8"/><stop offset=".45" stop-color="#6b7479"/><stop offset="1" stop-color="#3a4246"/></linearGradient>
<linearGradient id="stNegro" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5a6266"/><stop offset=".5" stop-color="#2c3236"/><stop offset="1" stop-color="#16191b"/></linearGradient>
<linearGradient id="stPlast" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4c5458"/><stop offset="1" stop-color="#1c2124"/></linearGradient>
<pattern id="stRosca" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="3" fill="#2a3034"/><line x1="0" y1="0" x2="3" y2="3" stroke="#59646a" stroke-width=".8"/></pattern>
<filter id="stSombra" x="-20%" y="-20%" width="150%" height="150%"><feDropShadow dx="4" dy="7" stdDeviation="5" flood-color="#000" flood-opacity=".55"/></filter>
`;

/* ---------- contexto: rueda (fig. F-13-1) y amortiguador izquierdo (fig. F-23) ---------- */
function arteRuedaCtx(){
  return `<g opacity=".55"><circle cx="700" cy="400" r="160" fill="none" stroke="#3c464b" stroke-width="22"/>
    <circle cx="700" cy="400" r="128" fill="none" stroke="#2c3438" stroke-width="5"/>
    <text x="760" y="585" fill="#7c878c" font-size="15" font-family="Barlow, sans-serif" text-anchor="middle">Rueda (fig. F-13-1)</text></g>`;
}
function arteAmortCtx(){
  return `<g opacity=".85">
    <path d="M560 178 L596 362" stroke="url(#stCromo)" stroke-width="12" stroke-linecap="round"/>
    <path d="M553 176 L578 300" stroke="url(#stNegro)" stroke-width="30" stroke-linecap="round"/>
    ${resorte(558,196,590,350,9,20,"#b23a2a")}
    <circle cx="556" cy="168" r="14" fill="#262c30" stroke="#6c7479" stroke-width="3"/><circle cx="556" cy="168" r="5" fill="#0d1012"/>
    <circle cx="598" cy="370" r="13" fill="#262c30" stroke="#6c7479" stroke-width="3"/><circle cx="598" cy="370" r="5" fill="#0d1012"/>
    <text x="470" y="150" fill="#7c878c" font-size="15" font-family="Barlow, sans-serif">Amortiguador (fig. F-23)</text></g>`;
}

/* ---------- tijera (7): brazo izquierdo de cajón, tubo del eje de la tijera, ranura del eje y oreja del amortiguador ---------- */
function arteTijera(x,y){
  const dx=x-210, dy=y-390;
  const T=(px,py)=>`${f(px+dx)} ${f(py+dy)}`;
  const brazo=`M${T(196,368)} L${T(640,380)} L${T(738,396)} L${T(738,426)} L${T(640,420)} L${T(196,414)} Z`;
  const oreja=`M${T(580,382)} L${T(592,356)} L${T(608,356)} L${T(622,384)} Z`;
  return `<g filter="url(#stSombra)">
    <path d="M${T(226,370)} L${T(700,378)} L${T(700,396)} L${T(226,394)} Z" transform="translate(34 -22)" fill="#1d2326" stroke="#3a4246"/>
    ${extruir(oreja,8,"#3a4246")}
    ${extruir(brazo,14,"#30373b")}
    <path d="${brazo}" fill="url(#stGris)" stroke="#c3cacd" stroke-width="1.4"/>
    <path d="M${T(206,376)} L${T(640,386)} L${T(735,401)}" fill="none" stroke="#dfe4e6" stroke-width="1.2" opacity=".6"/>
    <rect x="${f(648+dx)}" y="${f(403+dy)}" width="80" height="12" rx="6" fill="#0d1012"/>
    <path d="M${T(652,400)}v-5M${T(662,400)}v-5M${T(672,400)}v-5M${T(682,400)}v-5" stroke="#e8eef0" stroke-width="1.4"/>
    <circle cx="${f(600+dx)}" cy="${f(370+dy)}" r="6" fill="#0d1012"/>
    <circle cx="${f(210+dx)}" cy="${f(390+dy)}" r="30" fill="url(#stAcero)" stroke="#e8eef0" stroke-width="1.4"/>
    <circle cx="${f(210+dx)}" cy="${f(390+dy)}" r="20" fill="#3a4246"/>
    <circle cx="${f(210+dx)}" cy="${f(390+dy)}" r="9" fill="#0d1012"/>
    <rect x="${f(410+dx)}" y="${f(412+dy)}" width="22" height="20" rx="3" fill="#3a4246" stroke="#9aa3a8"/>
  </g>`;
}

/* ---------- «Cómo funciona» ---------- */
const PX=70, PY=200, LA=300; // eje de la tijera y largo hasta el eje de la rueda
const FN_SVG=`<svg id="fn" viewBox="0 0 900 320" role="img" aria-labelledby="fnTit">
  <title id="fnTit">Suspensión trasera de la CB 125F de lado: la tijera gira en su eje y comprime el amortiguador; a la derecha, el amortiguador por dentro con el resorte, el pistón y el aceite</title>
  <circle id="stf-rueda" cx="${PX+LA}" cy="${PY}" r="78" fill="none" stroke="#3c464b" stroke-width="14"/>
  <path d="M10 292 L460 292" stroke="#59646a" stroke-width="3"/>
  <path id="stf-bache" d="" fill="#3a4246"/>
  <g id="stf-tij" style="transform-origin:${PX}px ${PY}px;transition:transform .7s">
    <path d="M${PX} ${PY-12} L${PX+LA} ${PY-6} L${PX+LA} ${PY+8} L${PX} ${PY+12} Z" fill="#6b7479" stroke="#c3cacd"/>
    <circle cx="${PX+LA}" cy="${PY}" r="9" fill="#e8eef0"/>
    <path id="stf-cad" d="M${PX+10} ${PY+16} L${PX+LA-10} ${PY+40}" stroke="#c4952f" stroke-width="4" stroke-dasharray="6 4" fill="none"/>
  </g>
  <circle cx="${PX}" cy="${PY}" r="16" fill="#a7aeb2" stroke="#e8eef0" stroke-width="2"/><circle cx="${PX}" cy="${PY}" r="6" fill="#0d1012" id="stf-piv"/>
  <path id="stf-amo" d="" stroke="#2c3236" stroke-width="16" stroke-linecap="round"/>
  <path id="stf-res" d="" fill="none" stroke="#b23a2a" stroke-width="5"/>
  <circle cx="250" cy="40" r="9" fill="#262c30" stroke="#6c7479" stroke-width="3"/>
  <text class="esq-fn-et" x="${PX}" y="${PY+48}" text-anchor="middle">Eje de la tijera</text>
  <text class="esq-fn-et" x="300" y="34">Amortiguador</text>
  <text class="esq-fn-et" x="160" y="${PY-34}">Tijera</text>
  <text class="esq-fn-et esq-claro" x="20" y="34" id="stf-rec">Recorrido: 0 mm</text>
  <text class="esq-fn-et esq-claro" x="20" y="60" id="stf-cadtxt">Cadena: 25-35 mm</text>
  <g id="fnCorte">
    <rect x="490" y="44" width="400" height="266" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="68">Amortiguador por dentro</text>
    <rect x="560" y="90" width="64" height="200" rx="8" fill="#262c30" stroke="#6c7479" stroke-width="2"/>
    <rect x="566" y="96" width="52" height="188" rx="5" fill="#3b2f1c" id="stf-aceite"/>
    <g id="stf-vast" style="transition:transform .7s">
      <rect x="586" y="40" width="12" height="120" fill="url(#stCromo)"/>
      <rect x="566" y="150" width="52" height="16" fill="#9aa3a8" stroke="#e8eef0"/>
      <circle cx="580" cy="158" r="3" fill="#0d1012"/><circle cx="604" cy="158" r="3" fill="#0d1012"/>
    </g>
    <path class="esq-baja esq-quieto" id="stf-flujo" d="M580 175 L580 230 M604 175 L604 230" stroke="#f3d27a" stroke-width="3"/>
    <path id="stf-gotas" d="" fill="#c4952f"/>
    <text class="esq-fn-et" x="592" y="306" text-anchor="middle">Aceite y pistón</text>
    <text class="esq-fn-et esq-claro" x="660" y="120" id="stf-prec">Precarga: 2 de 5</text>
    <text class="esq-fn-et esq-claro" x="660" y="150" id="stf-vel">Aceite: quieto</text>
    <text class="esq-fn-et esq-claro" x="660" y="180" id="stf-buje">Bujes: bien</text>
    <text class="esq-fn-et esq-claro" x="660" y="230" id="stf-estado">Moto quieta</text>
  </g>
</svg>`;
function fnAplicar(s,$){
  const a=-(s.rec||0)/4; // grados de la tijera
  $("stf-tij").style.transform=`rotate(${a}deg)`;
  const r=a*Math.PI/180, ex=PX+LA*Math.cos(r), ey=PY+LA*Math.sin(r);
  $("stf-rueda").setAttribute("cx",f(ex));$("stf-rueda").setAttribute("cy",f(ey));
  const mx=PX+230*Math.cos(r), my=PY+230*Math.sin(r)-8; // oreja del amortiguador
  $("stf-amo").setAttribute("d",`M250 40 L${f(mx)} ${f(my)}`);
  let d="";const n=8;for(let i=0;i<=n*2;i++){const t=.12+.76*i/(n*2),x=250+(mx-250)*t,y=40+(my-40)*t,s2=(i%2?1:-1)*13;d+=(i?"L":"M")+f(x+s2)+" "+f(y)+" "}
  $("stf-res").setAttribute("d",d);
  $("stf-bache").setAttribute("d",s.rec>0?`M${f(ex-90)} 292 Q${f(ex)} ${f(292-s.rec*0.9)} ${f(ex+90)} 292 Z`:"");
  $("stf-vast").style.transform=`translateY(${f((s.rec||0)*0.9)}px)`;
  const fl=$("stf-flujo");fl.classList.remove("esq-lento","esq-quieto");if(s.aceite!=="rapido")fl.classList.add(s.aceite==="lento"?"esq-lento":"esq-quieto");
  $("stf-rec").textContent="Recorrido: "+(s.rec||0)+" mm";
  $("stf-cadtxt").textContent="Cadena: "+s.cadena;
  $("stf-cadtxt").setAttribute("fill",s.cadena.indexOf("tensa")>=0?"#f2611d":"#e8eef0");
  $("stf-prec").textContent="Precarga: "+s.prec+" de 5";
  $("stf-vel").textContent="Aceite: "+{quieto:"quieto",rapido:"pasa por el pistón",lento:"frena el regreso"}[s.aceite];
  $("stf-buje").textContent="Bujes: "+(s.bujes==="gastados"?"con juego":"bien");
  $("stf-buje").setAttribute("fill",s.bujes==="gastados"?"#f2611d":"#e8eef0");
  $("stf-piv").setAttribute("r",s.bujes==="gastados"?10:6);
  $("stf-gotas").setAttribute("d",s.fuga?"M560 296 q-6 10 0 14 q6 -4 0 -14 Z M548 300 q-5 8 0 11 q5 -3 0 -11 Z":"");
  $("stf-estado").textContent=s.estado;
}
return {defs:DEFS,arteRuedaCtx,arteAmortCtx,arteTijera,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
