/* Arte del carburador de la Bajaj Boxer CT100 TEC (fig. 16 del catálogo Auteco, carburador PB-16): dibujos propios de TallerYa.
   Vista de lado: el paso del aire va horizontal (motor a la izquierda, filtro a la derecha) y la torre de la cortina vertical,
   así la pila tapa → resorte → cortina → aguja y la taza con su flotador se ven de canto. Cada función recibe (x,y) = centro.
   Exporta las funciones que nombra el JSON, las defs y «Cómo funciona» con aplicar(s,$). */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["boxer-carburador"]=(function(){
"use strict";
const f=n=>Math.round(n*10)/10;
const DEFS=`
<radialGradient id="gFondo" cx="48%" cy="48%" r="70%"><stop offset="0" stop-color="#232c2f"/><stop offset="1" stop-color="#111517"/></radialGradient>
<linearGradient id="cbAlum" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d7dcdf"/><stop offset=".35" stop-color="#a9b1b6"/><stop offset=".7" stop-color="#7d868c"/><stop offset="1" stop-color="#4c5459"/></linearGradient>
<linearGradient id="cbAlumV" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#596268"/><stop offset=".35" stop-color="#d3d8db"/><stop offset=".65" stop-color="#9ea7ac"/><stop offset="1" stop-color="#4c5459"/></linearGradient>
<linearGradient id="cbLaton" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#7a5b1c"/><stop offset=".4" stop-color="#f0cf72"/><stop offset="1" stop-color="#8d6a22"/></linearGradient>
<linearGradient id="cbAcero" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4c5459"/><stop offset=".4" stop-color="#d0d6d9"/><stop offset="1" stop-color="#3f464b"/></linearGradient>
<linearGradient id="cbPlast" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f1efe6"/><stop offset="1" stop-color="#b9b5a6"/></linearGradient>
<linearGradient id="cbNegro" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4a4f53"/><stop offset="1" stop-color="#16191b"/></linearGradient>
<linearGradient id="cbGas" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f2c14e" stop-opacity=".55"/><stop offset="1" stop-color="#b9821b" stop-opacity=".8"/></linearGradient>
<filter id="cbSombra" x="-30%" y="-20%" width="160%" height="150%"><feDropShadow dx="4" dy="6" stdDeviation="4" flood-color="#000" flood-opacity=".55"/></filter>
`;
const toque=(x,y,w,h)=>`<rect x="${f(x)}" y="${f(y)}" width="${w}" height="${h}" fill="#000" fill-opacity="0" pointer-events="all"/>`;
const rosca=(x,y,w,n,paso)=>Array.from({length:n},(_,k)=>`<line x1="${f(x)}" y1="${f(y+k*paso)}" x2="${f(x+w)}" y2="${f(y+k*paso+paso*.6)}" stroke="#2a3034" stroke-width=".9"/>`).join("");

/* ---------- cuerpo (1): paso del aire, torre de la cortina, bloque de los chiclés ---------- */
function arteCuerpo(x,y){
  const X=x-130, Y=y-28;   // el paso del aire va de X a X+230, alto 56
  return `<g filter="url(#cbSombra)">
  <rect x="${X-18}" y="${y-48}" width="14" height="96" rx="3" fill="url(#cbAlumV)" stroke="#2c3236"/>
  <circle cx="${X-11}" cy="${y-38}" r="4" fill="#15191b"/><circle cx="${X-11}" cy="${y+38}" r="4" fill="#15191b"/>
  <rect x="${X-4}" y="${Y}" width="234" height="56" fill="url(#cbAlum)" stroke="#2c3236"/>
  <path d="M${X+230} ${Y-8} h20 v72 h-20 Z" fill="url(#cbAlum)" stroke="#2c3236"/>
  <ellipse cx="${X+250}" cy="${y}" rx="6" ry="34" fill="#1c2124" stroke="#8d969b"/>
  <rect x="${x-32}" y="${y-108}" width="64" height="84" fill="url(#cbAlumV)" stroke="#2c3236"/>
  <rect x="${x-38}" y="${y-116}" width="76" height="12" rx="3" fill="#c3c9cc" stroke="#2c3236"/>
  <rect x="${x-35}" y="${y+26}" width="70" height="40" rx="4" fill="url(#cbAlum)" stroke="#2c3236"/>
  <path d="M${x+35} ${y+44} h34 l6 -6" stroke="#9aa3a8" stroke-width="7" fill="none" stroke-linecap="round"/>
  <path d="M${X+236} ${y-30} l14 -14" stroke="#c3c9cc" stroke-width="5" stroke-linecap="round"/>
  <line x1="${X+20}" y1="${Y+8}" x2="${X+200}" y2="${Y+8}" stroke="#eef1f2" stroke-opacity=".6" stroke-width="2"/></g>`;
}
/* ---------- taza (1, parte del cuerpo) ---------- */
function arteTaza(x,y){
  return `<g filter="url(#cbSombra)"><path d="M${x-52} ${y-33} h104 v44 q0 22 -22 22 h-60 q-22 0 -22 -22 Z" fill="url(#cbAlum)" stroke="#2c3236"/>
  <rect x="${x-58}" y="${y-36}" width="116" height="8" rx="2" fill="#c3c9cc" stroke="#2c3236"/>
  <rect x="${x-48}" y="${y+26}" width="10" height="16" fill="#9aa3a8" stroke="#2c3236"/>
  <line x1="${x-40}" y1="${y-20}" x2="${x+40}" y2="${y-20}" stroke="#eef1f2" stroke-opacity=".5" stroke-width="2"/></g>`;
}
/* ---------- aislador (2) de canto y o-ring (3) ---------- */
function arteAislador(x,y){
  return `<g filter="url(#cbSombra)"><path d="M${x-9} ${y-50} h18 v100 h-18 Z" fill="#2f3538" stroke="#9aa3a8"/>
  <path d="M${x-12} ${y-30} h24 v60 h-24 Z" fill="#3c4347" stroke="#9aa3a8"/>
  <line x1="${x-12}" y1="${y}" x2="${x+12}" y2="${y}" stroke="#14181a" stroke-width="2"/></g>`;
}
const arteOringLado=(x,y)=>`<g><ellipse cx="${x}" cy="${y}" rx="4" ry="32" fill="none" stroke="#0b0b0b" stroke-width="5"/><ellipse cx="${x}" cy="${y}" rx="4" ry="32" fill="none" stroke="#454545" stroke-width="2"/>${toque(x-12,y-34,24,68)}</g>`;
/* ---------- tornillos de lado: dir 1 = cabeza a la izquierda; con resorte (7, 8) ---------- */
function arteTornillo(x,y,dir=1,largo=40,resorte=0,cab=9){
  const s=dir, hx=x, tx=x+s*largo;
  const res=resorte?Array.from({length:6},(_,k)=>`<ellipse cx="${f(hx+s*(12+k*4))}" cy="${y}" rx="1.8" ry="6" fill="none" stroke="#c9cfd2" stroke-width="1.6"/>`).join(""):"";
  return `<g filter="url(#cbSombra)"><rect x="${f(Math.min(hx,tx))}" y="${y-3.5}" width="${largo}" height="7" fill="url(#cbAcero)" stroke="#2a3034" stroke-width=".8"/>
  ${res}<rect x="${f(s>0?hx-8:hx)}" y="${y-cab}" width="8" height="${2*cab}" rx="1.5" fill="url(#cbAcero)" stroke="#2a3034"/>
  <line x1="${f(hx-s*4)}" y1="${y-cab+2}" x2="${f(hx-s*4)}" y2="${y+cab-2}" stroke="#2a3034" stroke-width="1.5"/>${toque(Math.min(hx,tx)-12,y-13,largo+24,26)}</g>`;
}
/* tornillo vertical de la taza (11), cabeza abajo */
function arteTornTaza(x,y){
  return `<g filter="url(#cbSombra)"><rect x="${x-3}" y="${y-26}" width="6" height="26" fill="url(#cbAcero)" stroke="#2a3034" stroke-width=".8"/>
  <rect x="${x-8}" y="${y}" width="16" height="7" rx="2" fill="url(#cbAcero)" stroke="#2a3034"/><line x1="${x}" y1="${y+1}" x2="${x}" y2="${y+6}" stroke="#2a3034" stroke-width="1.4"/>${toque(x-13,y-26,26,38)}</g>`;
}
/* ---------- tapa (16) con el codo del cable ---------- */
function arteTapa(x,y){
  return `<g filter="url(#cbSombra)"><path d="M${x+6} ${y-12} v-16 q0 -14 14 -14 h18" stroke="#1d2124" stroke-width="13" fill="none"/>
  <path d="M${x+6} ${y-12} v-16 q0 -14 14 -14 h18" stroke="url(#cbNegro)" stroke-width="10" fill="none"/>
  <rect x="${x+36}" y="${y-48}" width="14" height="13" rx="2" fill="#9aa3a8" stroke="#2a3034"/>
  <path d="M${x-30} ${y+10} v-12 q0 -10 10 -12 h40 q10 2 10 12 v12 Z" fill="url(#cbNegro)" stroke="#8d969b"/>
  ${Array.from({length:7},(_,k)=>`<line x1="${x-24+k*8}" y1="${y-6}" x2="${x-24+k*8}" y2="${y+9}" stroke="#7d868c" stroke-width="1.2"/>`).join("")}</g>`;
}
/* ---------- cortina (12): cilindro con el corte del lado del filtro ---------- */
function arteCortina(x,y){
  return `<g class="esq-oculto-arm" filter="url(#cbSombra)"><path d="M${x-22} ${y-30} h44 v48 l-10 12 h-34 Z" fill="url(#cbAcero)" stroke="#2a3034"/>
  <ellipse cx="${x}" cy="${y-30}" rx="22" ry="6" fill="#aeb6ba" stroke="#2a3034"/><ellipse cx="${x}" cy="${y-30}" rx="7" ry="2.4" fill="#1b1f22"/>
  <rect x="${x-3}" y="${y-8}" width="6" height="22" fill="#2a3034" opacity=".7"/></g>`;
}
/* ---------- aguja (18) con su seguro ---------- */
function arteAguja(x,y){
  return `<g class="esq-oculto-arm" filter="url(#cbSombra)"><path d="M${x-2} ${y-32} h4 v22 l-1.2 40 h-1.6 l-1.2 -40 Z" fill="url(#cbAcero)" stroke="#2a3034" stroke-width=".7"/>
  ${[0,4,8].map(k=>`<line x1="${x-3}" y1="${y-29+k}" x2="${x+3}" y2="${y-29+k}" stroke="#2a3034" stroke-width=".8"/>`).join("")}
  <rect x="${x-6}" y="${y-26}" width="12" height="3" rx="1" fill="#d9a441"/>${toque(x-12,y-34,24,68)}</g>`;
}
/* ---------- chiclé y difusor (10), boquerel de baja (19), aguja de la flota (20), flota (21) ---------- */
function arteChicle(x,y){
  return `<g class="esq-oculto-arm" filter="url(#cbSombra)"><rect x="${x-5}" y="${y-32}" width="10" height="30" fill="url(#cbLaton)" stroke="#5a4313" stroke-width=".8"/>
  ${[0,1,2,3].map(k=>`<circle cx="${x}" cy="${y-26+k*7}" r="1.3" fill="#3a2a0a"/>`).join("")}
  <path d="M${x-10} ${y-2} h20 v6 h-20 Z" fill="url(#cbLaton)" stroke="#5a4313"/>
  <path d="M${x-7} ${y+4} h14 l-2 10 h-10 Z" fill="url(#cbLaton)" stroke="#5a4313"/><line x1="${x-5}" y1="${y+12}" x2="${x+5}" y2="${y+12}" stroke="#3a2a0a" stroke-width="1.4"/>${toque(x-13,y-34,26,50)}</g>`;
}
function arteBoquerel(x,y){
  return `<g class="esq-oculto-arm" filter="url(#cbSombra)"><rect x="${x-3.5}" y="${y-18}" width="7" height="24" fill="url(#cbLaton)" stroke="#5a4313" stroke-width=".8"/>
  ${rosca(x-3.5,y-6,7,4,3)}<rect x="${x-6}" y="${y-22}" width="12" height="6" rx="1" fill="url(#cbLaton)" stroke="#5a4313"/>
  <line x1="${x-4}" y1="${y-19}" x2="${x+4}" y2="${y-19}" stroke="#3a2a0a" stroke-width="1.3"/>${toque(x-12,y-24,24,34)}</g>`;
}
function arteAgujaFlota(x,y){
  return `<g class="esq-oculto-arm" filter="url(#cbSombra)"><path d="M${x-3} ${y-10} l3 -6 l3 6 Z" fill="#1d1d1d"/><rect x="${x-3}" y="${y-10}" width="6" height="16" fill="url(#cbAcero)" stroke="#2a3034" stroke-width=".7"/>
  <rect x="${x-1}" y="${y+6}" width="2" height="5" fill="#9aa3a8"/>${toque(x-12,y-17,24,30)}</g>`;
}
function arteFlota(x,y){
  return `<g class="esq-oculto-arm" filter="url(#cbSombra)"><rect x="${x-44}" y="${y-14}" width="36" height="30" rx="8" fill="url(#cbPlast)" stroke="#6d6a5e"/>
  <rect x="${x+8}" y="${y-14}" width="36" height="30" rx="8" fill="url(#cbPlast)" stroke="#6d6a5e"/>
  <rect x="${x-8}" y="${y-10}" width="16" height="8" fill="#d8d4c6" stroke="#6d6a5e"/>
  <path d="M${x-6} ${y-14} v-8 h12 v8" fill="none" stroke="#6d6a5e" stroke-width="2"/><circle cx="${x}" cy="${y-20}" r="2.4" fill="#4a4f53"/></g>`;
}
/* ---------- sensor (13, 14) ---------- */
function arteIman(x,y){
  return `<g filter="url(#cbSombra)"><path d="M${x-10} ${y-7} h20 l-3 14 h-14 Z" fill="url(#cbNegro)" stroke="#8d969b"/><rect x="${x-6}" y="${y-4}" width="12" height="4" fill="#b23a3a"/>${toque(x-13,y-12,26,24)}</g>`;
}
function arteCable(x,y){
  return `<g filter="url(#cbSombra)"><path d="M${x-30} ${y-30} q20 10 26 34 t36 30" stroke="#0f1112" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M${x-30} ${y-30} q20 10 26 34 t36 30" stroke="#3a3f43" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  <rect x="${x-44}" y="${y-38}" width="16" height="12" rx="2" fill="#2c3134" stroke="#8d969b"/>
  <rect x="${x+28}" y="${y+28}" width="14" height="10" rx="2" fill="#d9a441" stroke="#6b4f12"/>${toque(x-46,y-40,92,82)}</g>`;
}

/* pares: tornillos del aislador (9) y de la taza (11); anillos de canto (5) */
const arteTornillo2=(x,y,dir,largo,dy)=>arteTornillo(x,y,dir,largo,0,8)+arteTornillo(x,y+dy,dir,largo,0,8);
const arteTornTaza2=(x,y,dx)=>arteTornTaza(x,y)+arteTornTaza(x+dx,y);
const arteAnilloH=(x,y,r,oc)=>`<g${oc?' class="esq-oculto-arm"':""}><ellipse cx="${x}" cy="${y}" rx="${r}" ry="4.5" fill="none" stroke="#0b0b0b" stroke-width="5"/><ellipse cx="${x}" cy="${y}" rx="${r}" ry="4.5" fill="none" stroke="#4a4a4a" stroke-width="2"/>${toque(x-r-2,y-12,2*r+4,24)}</g>`;

/* ---------- Cómo funciona: corte del carburador ---------- */
const FN_SVG=`<svg id="fn" viewBox="0 0 900 440" role="img" aria-labelledby="fnTit">
  <title id="fnTit">Corte del carburador: la cortina sube con el acelerador, la aguja sale del chiclé y la flota cierra la entrada de gasolina cuando la taza se llena</title>
  <style>
    #cbf-cort,#cbf-flota{transition:transform .8s cubic-bezier(.5,0,.3,1)}
    #cbf-gas{transition:y .8s,height .8s}
    #cbf-acel,#cbf-niv{transition:width .8s}
    .esq-cbf-on{transition:opacity .5s}
  </style>
  <rect width="900" height="440" fill="#151a1c"/>
  <!-- paso del aire -->
  <rect x="16" y="110" width="444" height="70" fill="#22292c" stroke="#8f989d" stroke-width="2"/>
  <g class="esq-cbf-on" id="cbf-aire"><path d="M450 145 h-90 m12 -9 l-12 9 l12 9" stroke="#7fd0ff" stroke-width="4" fill="none"/><path d="M130 145 h-100 m12 -9 l-12 9 l12 9" stroke="#7fd0ff" stroke-width="4" fill="none"/></g>
  <!-- torre de la cortina -->
  <rect x="155" y="14" width="90" height="98" fill="#2a3235" stroke="#8f989d" stroke-width="2"/>
  <rect x="148" y="2" width="104" height="14" rx="4" fill="#4a5256" stroke="#8f989d"/>
  <!-- taza con la gasolina -->
  <path d="M60 215 h300 v135 q0 20 -20 20 h-260 q-20 0 -20 -20 Z" fill="#20272a" stroke="#8f989d" stroke-width="2"/>
  <rect id="cbf-gas" x="64" y="246" width="292" height="120" fill="url(#cbGas)"/>
  <!-- chiclé de alta con su difusor -->
  <rect x="193" y="180" width="14" height="84" fill="#8d6a22" stroke="#f0cf72"/>
  <path d="M187 262 h26 v16 h-26 Z" fill="url(#cbLaton)" stroke="#5a4313"/>
  <!-- boquerel de baja y su conducto al paso del aire -->
  <path d="M100 300 V196 H150 V180" stroke="#f0cf72" stroke-width="7" fill="none"/>
  <rect x="94" y="268" width="12" height="34" fill="url(#cbLaton)" stroke="#5a4313"/>
  <!-- entrada de gasolina y asiento de la aguja de corte -->
  <path d="M470 197 H310 V206" stroke="#9aa3a8" stroke-width="10" fill="none"/>
  <g class="esq-cbf-on" id="cbf-entra" opacity="0"><path d="M292 206 v22 m-7 -9 l7 9 l7 -9" stroke="#ffd36b" stroke-width="4" fill="none"/></g>
  <!-- flota con su aguja (bajan y suben con el nivel) -->
  <g id="cbf-flota"><rect x="230" y="232" width="100" height="30" rx="9" fill="url(#cbPlast)" stroke="#6d6a5e"/>
    <rect x="304" y="206" width="12" height="26" fill="#c9cfd2" stroke="#2a3034"/><path d="M304 206 l6 -6 l6 6 Z" fill="#1d1d1d"/></g>
  <!-- cortina, resorte y aguja (suben con el acelerador) -->
  <g id="cbf-cort"><rect x="165" y="78" width="70" height="100" fill="#b6bec2" stroke="#2a3034"/>
    <path d="M235 150 v28 h-20 Z" fill="#22292c"/>
    <path d="M198 178 h4 l-1 70 h-2 Z" fill="#dfe4e6" stroke="#2a3034" stroke-width=".6"/></g>
  <g id="cbf-res"><path d="M185 18 L215 26 L185 34 L215 42 L185 50 L215 58 L185 66 L215 74" stroke="#9fb0b8" stroke-width="3" fill="none"/></g>
  <!-- rocío de gasolina -->
  <g class="esq-cbf-on" id="cbf-baja" opacity="0"><circle cx="146" cy="166" r="4" fill="#ffd36b"/><circle cx="136" cy="158" r="3" fill="#ffd36b"/><circle cx="126" cy="150" r="2.5" fill="#ffd36b"/></g>
  <g class="esq-cbf-on" id="cbf-alta" opacity="0"><circle cx="196" cy="165" r="5" fill="#ffd36b"/><circle cx="180" cy="152" r="4" fill="#ffd36b"/><circle cx="160" cy="146" r="4" fill="#ffd36b"/><circle cx="140" cy="140" r="3" fill="#ffd36b"/><circle cx="120" cy="148" r="3" fill="#ffd36b"/></g>
  <g class="esq-cbf-on" id="cbf-rebose" opacity="0"><path d="M352 372 q6 12 0 18 q-6 -6 0 -18Z" fill="#ffd36b"/><path d="M340 392 q5 10 0 15 q-5 -5 0 -15Z" fill="#ffd36b"/><circle cx="60" cy="172" r="4" fill="#ffd36b"/><circle cx="76" cy="170" r="3" fill="#ffd36b"/></g>
  <!-- rótulos -->
  <text class="esq-fn-et" x="256" y="44">Cortina</text>
  <text class="esq-fn-et" x="256" y="96">Aguja</text>
  <text class="esq-fn-et" x="380" y="100" data-xm="372" data-ym="100">Aire</text>
  <text class="esq-fn-et" x="20" y="100">Al motor</text>
  <text class="esq-fn-et" x="330" y="230" data-xm="320" data-ym="200">Gasolina</text>
  <text class="esq-fn-et" x="16" y="402">Boquerel de baja</text>
  <text class="esq-fn-et" x="186" y="402">Chiclé</text>
  <text class="esq-fn-et" x="262" y="402">Flotador</text>
  <text class="esq-fn-et" x="248" y="196" data-xm="232" data-ym="434">Aguja de corte</text>
  <path d="M100 384 V304 M206 384 V280 M300 384 V300" stroke="#8f989d" stroke-width="1.5" stroke-dasharray="3 3"/>
  <g id="fnCorte">
    <text class="esq-fn-et" x="500" y="164">Acelerador</text>
    <rect x="500" y="176" width="280" height="26" rx="6" fill="#22292c" stroke="#5d676d"/>
    <rect id="cbf-acel" x="504" y="180" width="0" height="18" rx="3" fill="#e2b33f"/>
    <text id="cbf-pct" class="esq-fn-et" x="500" y="236">0 %</text>
    <text class="esq-fn-et" x="500" y="282">Nivel en la taza</text>
    <rect x="500" y="294" width="280" height="26" rx="6" fill="#22292c" stroke="#5d676d"/>
    <rect id="cbf-niv" x="504" y="298" width="0" height="18" rx="3" fill="#7fd0ff"/>
    <text id="cbf-est" class="esq-fn-et" x="500" y="360">En reposo</text>
  </g>
</svg>`;
function fnAplicar(s,$){
  const a=Math.max(0,Math.min(1,s.acel||0)), n=Math.max(0,Math.min(1.15,s.nivel==null?1:s.nivel));
  $("cbf-cort").style.transform=`translate(0px,${f(-a*70)}px)`;
  $("cbf-res").style.transform=`translate(0px,0px) scaleY(${(1-a*.55).toFixed(3)})`;
  $("cbf-res").style.transformOrigin="200px 18px";
  const top=366-n*120; $("cbf-gas").setAttribute("y",f(top)); $("cbf-gas").setAttribute("height",f(370-top));
  $("cbf-flota").style.transform=`translate(0px,${f((1-Math.min(n,1))*120)}px)`;
  $("cbf-acel").setAttribute("width",f(a*272)); $("cbf-niv").setAttribute("width",f(Math.min(n,1)*272));
  $("cbf-pct").textContent=Math.round(a*100)+" % de acelerador";
  $("cbf-est").textContent=s.estado||"";
  $("cbf-aire").style.opacity=s.aire===false?0:1;
  $("cbf-entra").style.opacity=s.entra?1:0;
  $("cbf-baja").style.opacity=s.baja?1:0;
  $("cbf-alta").style.opacity=s.alta?1:0;
  $("cbf-rebose").style.opacity=s.rebose?1:0;
}
return {defs:DEFS,arteCuerpo,arteTaza,arteAislador,arteOringLado,arteTornillo,arteTornTaza,arteTapa,arteCortina,arteAguja,arteChicle,arteBoquerel,arteAgujaFlota,arteFlota,arteIman,arteCable,arteTornillo2,arteTornTaza2,arteAnilloH,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
