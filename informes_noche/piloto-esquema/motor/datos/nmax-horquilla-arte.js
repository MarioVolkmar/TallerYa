/* Arte de la horquilla delantera y la dirección de la Yamaha NMAX (fig. 18 del catálogo): dibujos propios de TallerYa.
   Vista de frente de la moto: las barras van verticales y las piezas de revolución se ven de lado
   (los anillos como elipses). Cada función recibe (x,y) = centro de la pieza; las posiciones salen
   de datos/nmax-horquilla.json (piezas[].args), así el despiece solo traslada.
   Exporta las funciones que nombra el JSON, las defs y «Cómo funciona» con aplicar(s,$). */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["nmax-horquilla"]=(function(){
"use strict";
const f=n=>Math.round(n*10)/10;
const DEFS=`
<radialGradient id="gFondo" cx="48%" cy="48%" r="70%"><stop offset="0" stop-color="#232c2f"/><stop offset="1" stop-color="#111517"/></radialGradient>
<linearGradient id="hqCromo" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6c767c"/><stop offset=".22" stop-color="#f4f7f8"/><stop offset=".45" stop-color="#aab3b8"/><stop offset=".7" stop-color="#e3e8ea"/><stop offset="1" stop-color="#59636a"/></linearGradient>
<linearGradient id="hqAlum" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4f585e"/><stop offset=".3" stop-color="#cfd5d8"/><stop offset=".6" stop-color="#9aa3a8"/><stop offset="1" stop-color="#454d52"/></linearGradient>
<linearGradient id="hqAcero" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4c5459"/><stop offset=".35" stop-color="#c9cfd2"/><stop offset="1" stop-color="#3f464b"/></linearGradient>
<linearGradient id="hqCaucho" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#121212"/><stop offset=".4" stop-color="#3d3d3d"/><stop offset="1" stop-color="#0c0c0c"/></linearGradient>
<linearGradient id="hqAceite" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d9a441" stop-opacity=".75"/><stop offset="1" stop-color="#8a5a12" stop-opacity=".85"/></linearGradient>
<filter id="hqSombra" x="-30%" y="-10%" width="160%" height="130%"><feDropShadow dx="4" dy="6" stdDeviation="4" flood-color="#000" flood-opacity=".55"/></filter>
`;
/* ---------- ayudas ---------- */
const elip=(x,y,r,k=.3)=>`<ellipse cx="${f(x)}" cy="${f(y)}" rx="${r}" ry="${f(r*k)}"`;
function anilloE(x,y,r,alto,cara,borde,ancho=4){       // anillo visto de lado: banda con su elipse de arriba
  return `<path d="M${f(x-r)} ${f(y)} v${alto} a${r} ${f(r*.3)} 0 0 0 ${2*r} 0 v${-alto}" fill="${cara}" stroke="${borde}" stroke-width="1"/>
  ${elip(x,y,r)} fill="none" stroke="${cara}" stroke-width="${ancho}"/>${elip(x,y,r)} fill="none" stroke="${borde}" stroke-width=".8"/>`;
}
function espiral(x,y,r,L,n,color,grueso){              // resorte de lado, centrado en (x,y)
  const y0=y-L/2, p=L/n; let a="",b="";
  for(let k=0;k<n;k++){const t=y0+k*p;
    a+=`M${f(x-r)} ${f(t+p/2)} L${f(x+r)} ${f(t)} `; b+=`M${f(x-r)} ${f(t+p/2)} L${f(x+r)} ${f(t+p)} `}
  return `<path d="${b}" stroke="#2a2f33" stroke-width="${grueso}" stroke-linecap="round" fill="none"/>
  <path d="${a}" stroke="#1b1f22" stroke-width="${grueso+1.6}" stroke-linecap="round" fill="none"/><path d="${a}" stroke="${color}" stroke-width="${grueso}" stroke-linecap="round" fill="none"/>`;
}
const toque=(x,y,w,h)=>`<rect x="${f(x)}" y="${f(y)}" width="${w}" height="${h}" fill="#000" fill-opacity="0" pointer-events="all"/>`;

/* ---------- tapón (13) y su o-ring (17) ---------- */
function arteTapon(x,y){
  return `<g filter="url(#hqSombra)"><rect x="${x-10}" y="${y+6}" width="20" height="12" fill="url(#hqAcero)"/>
  ${[0,3,6,9].map(k=>`<line x1="${x-10}" y1="${y+7+k}" x2="${x+10}" y2="${y+8.5+k}" stroke="#2a3034" stroke-width="1"/>`).join("")}
  <path d="M${x-15} ${y-8} h30 l2 7 v6 h-34 v-6 Z" fill="url(#hqAcero)" stroke="#262c30"/><line x1="${x-5}" y1="${y-8}" x2="${x-5}" y2="${y+5}" stroke="#262c30"/><line x1="${x+5}" y1="${y-8}" x2="${x+5}" y2="${y+5}" stroke="#262c30"/></g>`;
}
const arteOring=(x,y)=>`<g>${elip(x,y,13)} fill="none" stroke="#0b0b0b" stroke-width="5"/>${elip(x,y,13)} fill="none" stroke="#3b3b3b" stroke-width="2"/>${toque(x-15,y-7,30,14)}</g>`;
/* ---------- resortes (2, 4) ---------- */
const arteResorte=(x,y)=>`<g class="esq-oculto-arm">${espiral(x,y,12,200,17,"#9fb0b8",3)}${toque(x-13,y-100,26,200)}</g>`;
const arteRebote=(x,y)=>`<g class="esq-oculto-arm">${espiral(x,y,11,40,6,"#c9a23a",2.4)}${toque(x-12,y-20,24,40)}</g>`;
/* ---------- barra (3): tubo cromado ---------- */
function arteBarra(x,y){
  const L=358, t=y-L/2;
  return `<g filter="url(#hqSombra)"><rect x="${x-17}" y="${t}" width="34" height="${L}" fill="url(#hqCromo)" stroke="#3a4247" stroke-width="1"/>
  ${elip(x,t,17,.28)} fill="#5d676d" stroke="#2c3337"/>${elip(x,t,11,.28)} fill="#1d2225"/>
  <rect x="${x-17}" y="${t+L-30}" width="34" height="30" fill="#7b858b" opacity=".55"/>
  <circle cx="${x}" cy="${t+L-16}" r="3.2" fill="#1d2225"/><path d="M${x-10} ${t+40} v${L-90}" stroke="#fff" stroke-opacity=".35" stroke-width="3"/></g>`;
}
/* ---------- dirección: tija inferior con su eje (34) y tapa de abajo (49) ---------- */
function arteTija(x,y){
  const a=170;
  return `<g filter="url(#hqSombra)"><rect x="${x-9}" y="${y-175}" width="18" height="175" fill="url(#hqAcero)" stroke="#2b3135"/>
  <path d="M${x-a-24} ${y-14} h${2*a+48} v28 h-${2*a+48} Z" fill="#3b4348" stroke="#9aa3a8" stroke-width="1.2"/>
  <path d="M${x-a+30} ${y+14} Q${x} ${y+40} ${x+a-30} ${y+14}" fill="#2f363a" stroke="#9aa3a8"/>
  ${[-a,a].map(d=>`<ellipse cx="${x+d}" cy="${y}" rx="24" ry="16" fill="none" stroke="#c3cacd" stroke-width="3"/>`).join("")}
  <path d="M${x-a+28} ${y-8} h${2*a-56}" stroke="#fff" stroke-opacity=".25" stroke-width="3"/></g>`;
}
const arteTapaTija=(x,y)=>`<g><path d="M${x-70} ${y-6} h140 l-16 18 h-108 Z" fill="#1f2427" stroke="#8f989d" stroke-width="1.2"/><path d="M${x-50} ${y+3} h100" stroke="#8f989d" stroke-opacity=".5"/></g>`;
/* ---------- amortiguador: asiento (8), aro (7), pieza de tope (6) ---------- */
function arteAsiento(x,y){
  const L=200, t=y-L/2;
  return `<g class="esq-oculto-arm"><rect x="${x-7}" y="${t+12}" width="14" height="${L-12}" fill="url(#hqAcero)" stroke="#2b3135"/>
  <rect x="${x-11}" y="${t}" width="22" height="14" rx="2" fill="url(#hqAcero)" stroke="#2b3135"/>
  <circle cx="${x}" cy="${t+40}" r="2.4" fill="#15191b"/><circle cx="${x}" cy="${t+L-24}" r="2.4" fill="#15191b"/><circle cx="${x}" cy="${t+L-36}" r="2.4" fill="#15191b"/>${toque(x-12,t,24,L)}</g>`;
}
const arteAro=(x,y)=>`<g class="esq-oculto-arm">${anilloE(x,y-2,12,4,"#7d6a4a","#2b2119",3)}${toque(x-14,y-8,28,16)}</g>`;
const arteTope=(x,y)=>`<g class="esq-oculto-arm"><path d="M${x-8} ${y-10} h16 l6 20 h-28 Z" fill="url(#hqAcero)" stroke="#262c30"/>${elip(x,y+10,14,.25)} fill="#5d676d"/></g>`;
/* ---------- botellas (11 izquierda, 5 derecha) ---------- */
function arteBotella(x,y,lado){
  const s=lado==="der"?1:-1, t=y-135;                    // la oreja de la pinza va por fuera
  return `<g filter="url(#hqSombra)"><path d="M${x-26} ${t+8} Q${x-26} ${t} ${x-18} ${t} h36 Q${x+26} ${t} ${x+26} ${t+8} L${x+23} ${y+108} h-46 Z" fill="url(#hqAlum)" stroke="#2f363a" stroke-width="1.2"/>
  <rect x="${x-27}" y="${t}" width="54" height="16" rx="5" fill="url(#hqAlum)" stroke="#2f363a"/>
  <path d="M${x+s*22} ${y+20} l${s*20} 6 v26 l${-s*20} 6 Z" fill="url(#hqAlum)" stroke="#2f363a"/><circle cx="${x+s*34}" cy="${y+39}" r="4" fill="#1d2225"/>
  <circle cx="${x}" cy="${y+108}" r="24" fill="url(#hqAlum)" stroke="#2f363a" stroke-width="1.2"/><circle cx="${x}" cy="${y+108}" r="10" fill="#1a1f22"/>
  <path d="M${x-12} ${t+24} v${170}" stroke="#fff" stroke-opacity=".3" stroke-width="3"/></g>`;
}
/* ---------- guardapolvo (16), seguro (15), retén (9) ---------- */
const arteGuardapolvo=(x,y)=>`<g><path d="M${x-22} ${y+8} L${x-19} ${y-8} h38 l3 16 Z" fill="url(#hqCaucho)" stroke="#4a4a4a"/>
  <line x1="${x-20}" y1="${y-2}" x2="${x+20}" y2="${y-2}" stroke="#555" stroke-width="1"/><line x1="${x-21}" y1="${y+3}" x2="${x+21}" y2="${y+3}" stroke="#555" stroke-width="1"/>${toque(x-24,y-17,48,34)}</g>`;
function arteSeguro(x,y){
  return `<g class="esq-oculto-arm"><path d="M${x+6} ${f(y+5.4)} A20 6 0 1 1 ${x+14} ${f(y+4.3)}" fill="none" stroke="#1d2225" stroke-width="5" stroke-linecap="round"/><path d="M${x+6} ${f(y+5.4)} A20 6 0 1 1 ${x+14} ${f(y+4.3)}" fill="none" stroke="#9aa3a8" stroke-width="2.4" stroke-linecap="round"/>${toque(x-24,y-17,48,34)}</g>`;
}
const arteReten=(x,y)=>`<g class="esq-oculto-arm">${anilloE(x,y-5,22,10,"url(#hqCaucho)","#555",6)}${elip(x,y-5,15)} fill="none" stroke="#7d6a4a" stroke-width="1.6"/></g>`;
/* ---------- tornillo allen (12) y arandela (14) del fondo ---------- */
const arteAllen=(x,y)=>`<g><rect x="${x-4}" y="${y-30}" width="8" height="24" fill="url(#hqAcero)" stroke="#262c30"/>
  ${[0,5,10,15].map(k=>`<line x1="${x-4}" y1="${y-28+k}" x2="${x+4}" y2="${y-26.5+k}" stroke="#2a3034"/>`).join("")}
  <rect x="${x-8}" y="${y-7}" width="16" height="14" rx="2" fill="url(#hqAcero)" stroke="#262c30"/>${elip(x,y+7,8,.3)} fill="#3f464b"/></g>`;
const arteArandela=(x,y)=>`<g class="esq-oculto-arm">${anilloE(x,y-1,10,2,"#b9a05a","#4a3d1c",3)}${toque(x-12,y-6,24,12)}</g>`;
/* ---------- pinza de la manguera (18) y su tornillo (19) ---------- */
const artePinza=(x,y)=>`<g><path d="M${x-12} ${y-7} h18 a7 7 0 0 1 0 14 h-18 Z" fill="#2c3236" stroke="#8f989d"/><circle cx="${x+6}" cy="${y}" r="4.5" fill="#15191b"/></g>`;
const arteTornPinza=(x,y)=>`<g><rect x="${x}" y="${y-2.5}" width="14" height="5" fill="url(#hqAcero)"/><path d="M${x-8} ${y-6} h8 v12 h-8 Z" fill="url(#hqAcero)" stroke="#262c30"/></g>`;

/* ---------- Cómo funciona: barra cortada que se comprime y se extiende ---------- */
const FN_SVG=`<svg id="fn" viewBox="0 0 900 440" role="img" aria-labelledby="fnTit">
  <title id="fnTit">Corte de una barra de la horquilla: la barra cromada baja dentro de la botella, el resorte se comprime y el aceite pasa por los orificios del amortiguador</title>
  <style>
    #hqf-movil,#hqf-res{transition:transform .8s cubic-bezier(.5,0,.3,1)}
    #hqf-barra-ind{transition:height .8s,y .8s}
    .esq-hqf-flecha,#hqf-fuga,#hqf-lock-on{transition:opacity .5s}
  </style>
  <rect width="900" height="440" fill="#151a1c"/>
  <!-- botella cortada (fija) -->
  <path d="M150 190 h100 v190 q0 30 -50 30 q-50 0 -50 -30 Z" fill="#3b4347" stroke="#8f989d" stroke-width="2"/>
  <path d="M162 200 h76 v178 q0 20 -38 20 q-38 0 -38 -20 Z" fill="url(#hqAceite)"/>
  <rect x="145" y="180" width="110" height="16" rx="5" fill="#646d72"/>
  <rect x="166" y="184" width="68" height="10" fill="#1b1f22"/>
  <!-- amortiguador fijo (asiento) con su tope -->
  <rect x="190" y="210" width="20" height="175" fill="#9aa3a8" stroke="#2b3135"/>
  <rect x="184" y="200" width="32" height="14" rx="2" fill="#b6bec2" stroke="#2b3135"/>
  <circle cx="200" cy="260" r="3" fill="#15191b"/><circle cx="200" cy="350" r="3" fill="#15191b"/>
  <path d="M188 362 h24 l7 22 h-38 Z" fill="#b6bec2" stroke="#2b3135"/>
  <path id="hqf-lock-on" d="M188 362 h24 l7 22 h-38 Z" fill="#e2b33f" opacity="0"/>
  <!-- parte móvil: barra cromada + tapón; el resorte se estira entre el tapón y el asiento -->
  <g id="hqf-res" style="transform-origin:200px 200px">${espiral(200,120,15,160,12,"#9fb0b8",3)}</g>
  <g id="hqf-movil">
    <rect x="172" y="30" width="56" height="300" fill="url(#hqCromo)" fill-opacity=".35" stroke="#cfd5d8" stroke-width="2"/>
    <rect x="178" y="18" width="44" height="16" rx="3" fill="#9aa3a8" stroke="#262c30"/>
    <rect x="172" y="300" width="56" height="30" fill="#7b858b" opacity=".6"/>
  </g>
  <!-- retenes en la boca de la botella -->
  <rect x="160" y="174" width="12" height="10" fill="#111"/><rect x="228" y="174" width="12" height="10" fill="#111"/>
  <g id="hqf-fuga" opacity="0"><path d="M240 168 q8 14 0 22 q-8 -8 0 -22Z" fill="#d9a441"/><path d="M256 200 q7 12 0 19 q-7 -7 0 -19Z" fill="#d9a441"/></g>
  <!-- flechas del aceite -->
  <g class="esq-hqf-flecha" id="hqf-baja" opacity="0"><path d="M226 240 v60 m-8 -12 l8 12 l8 -12" stroke="#ffd36b" stroke-width="4" fill="none"/><path d="M174 300 v-50 m-8 12 l8 -12 l8 12" stroke="#ffd36b" stroke-width="4" fill="none"/></g>
  <g class="esq-hqf-flecha" id="hqf-sube" opacity="0"><path d="M226 300 v-60 m-8 12 l8 -12 l8 12" stroke="#7fd0ff" stroke-width="4" fill="none"/><path d="M174 250 v50 m-8 -12 l8 12 l8 -12" stroke="#7fd0ff" stroke-width="4" fill="none"/></g>
  <text class="esq-fn-et" x="270" y="60">Tapón</text>
  <text class="esq-fn-et" x="270" y="135">Resorte</text>
  <text class="esq-fn-et" x="270" y="215">Retén</text>
  <text class="esq-fn-et" x="270" y="290">Aceite</text>
  <text class="esq-fn-et" x="270" y="375">Tope de aceite</text>
  <text class="esq-fn-et" x="20" y="250" data-xm="20" data-ym="250">Barra</text>
  <text class="esq-fn-et" x="262" y="425">Botella</text>
  <g id="fnCorte">
    <text class="esq-fn-et" x="540" y="70">Recorrido</text>
    <rect x="540" y="90" width="40" height="230" rx="6" fill="#22292c" stroke="#5d676d"/>
    <rect id="hqf-barra-ind" x="544" y="316" width="32" height="0" fill="#e2b33f"/>
    <text id="hqf-mm" class="esq-fn-et" x="600" y="210">0 mm</text>
    <text id="hqf-est" class="esq-fn-et" x="600" y="250">En reposo</text>
  </g>
</svg>`;
function fnAplicar(s,$){
  const c=Math.max(0,Math.min(1,s.comp||0)), d=c*60;
  $("hqf-movil").style.transform=`translate(0px,${f(d)}px)`;
  $("hqf-res").style.transform=`scaleY(${(1-d/160).toFixed(3)})`;   // la base del resorte (y=200) no se mueve
  const h=c*222; $("hqf-barra-ind").setAttribute("height",f(h)); $("hqf-barra-ind").setAttribute("y",f(316-h));
  $("hqf-mm").textContent=Math.round(c*120)+" mm (aprox.)";
  $("hqf-est").textContent=s.estado||"";
  $("hqf-baja").style.opacity=s.flujo==="baja"?1:0;
  $("hqf-sube").style.opacity=s.flujo==="sube"?1:0;
  $("hqf-lock-on").style.opacity=s.tope?1:0;
  $("hqf-fuga").style.opacity=s.fuga?1:0;
}
return {defs:DEFS,arteTija,arteTapaTija,arteAllen,arteArandela,arteAro,arteAsiento,arteBarra,arteBotella,arteGuardapolvo,arteOring,artePinza,arteRebote,arteResorte,arteReten,arteSeguro,arteTapon,arteTope,arteTornPinza,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
