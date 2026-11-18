/* PILOTO DE ESTILO ILUSTRADO (copia de nkd-freno-arte.js): fondo claro con grilla, metal con brillo,
   color por sistema (mando naranja, hidráulico azul, fricción cobre, eléctrico violeta), rótulos con línea guía
   y flechas de flujo en «Cómo funciona». Mismas formas y medidas que la lámina aprobada.
   Arte de la fig. F-5 de la AKT NKD 125 (sistema del freno delantero): dibujos propios de TallerYa.
   Cáliper, pastillas, disco y «Cómo funciona» adaptados de la lámina del freno de la Crypton (crypton-freno);
   bomba, manigueta e interruptor adaptados de la NMAX fig. 26. Cable del CBS: dibujo nuevo. */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["nkd-freno-estilo"]=(function(){
"use strict";
const C=[407,355], D=[540,390], ROT=15, SX=0.86;
const rc=Math.cos(ROT*Math.PI/180), rs=Math.sin(ROT*Math.PI/180);
const R=(x,y)=>{x*=SX;return [C[0]+x*rc-y*rs, C[1]+x*rs+y*rc]};          // local caliper → pantalla
const LOC=`translate(${C[0]} ${C[1]}) rotate(${ROT}) scale(${SX} 1)`;
const PD=(u,v)=>[D[0]+0.78*u, D[1]-0.16*u+v];              // plano del disco → pantalla
const f=n=>Math.round(n*10)/10;

function hexa(cx,cy,r,rot=0){let p=[];for(let i=0;i<6;i++){const a=(i*60+rot)*Math.PI/180;p.push(f(cx+r*Math.cos(a))+","+f(cy+r*Math.sin(a)))}return p.join(" ")}
function extruir(d,dx,dy,pasos,fill){let s="";for(let k=pasos;k>=1;k--){s+=`<path d="${d}" transform="translate(${f(dx*k/pasos)} ${f(dy*k/pasos)})" fill="${fill}"/>`}return s}
// profundidad hacia atrás (opuesta a la normal que mira al lector), en coordenadas locales del caliper
const ATRAS=[-14,-1];

const DEFS=`
<pattern id="gFondo" width="40" height="40" patternUnits="userSpaceOnUse"><rect width="40" height="40" fill="#f2f4f6"/><path d="M40 0H0V40" fill="none" stroke="#dde3e8" stroke-width="1"/><circle cx="0" cy="0" r="1.1" fill="#c9d1d8"/></pattern>
<linearGradient id="gCara" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f4f6f7"/><stop offset=".35" stop-color="#b9c0c5"/><stop offset=".55" stop-color="#eceff1"/><stop offset="1" stop-color="#8d969c"/></linearGradient>
<linearGradient id="gPista" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".3" stop-color="#aab2b8"/><stop offset=".5" stop-color="#f1f3f5"/><stop offset=".75" stop-color="#9ba4aa"/><stop offset="1" stop-color="#d5dade"/></linearGradient>
<linearGradient id="gCanto" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5a646b"/><stop offset="1" stop-color="#8e989e"/></linearGradient>
<linearGradient id="gCal" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#c3dbf3"/><stop offset=".22" stop-color="#7eaad8"/><stop offset=".5" stop-color="#4a7fb8"/><stop offset="1" stop-color="#1f4370"/></linearGradient>
<linearGradient id="gCalLado" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#16304f"/><stop offset="1" stop-color="#2c5383"/></linearGradient>
<radialGradient id="gDomo" cx="35%" cy="30%" r="75%"><stop offset="0" stop-color="#e3effb"/><stop offset=".25" stop-color="#8fb6df"/><stop offset=".6" stop-color="#4677ad"/><stop offset="1" stop-color="#1e3f69"/></radialGradient>
<linearGradient id="gSop" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef1f3"/><stop offset=".45" stop-color="#b3bbc1"/><stop offset=".6" stop-color="#d3d8dc"/><stop offset="1" stop-color="#7a848b"/></linearGradient>
<linearGradient id="gAcero" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".45" stop-color="#b0b8bd"/><stop offset="1" stop-color="#6c757b"/></linearGradient>
<linearGradient id="gCromoV" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".35" stop-color="#a6aeb3"/><stop offset=".55" stop-color="#f3f5f6"/><stop offset="1" stop-color="#5f676c"/></linearGradient>
<linearGradient id="gCaucho" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3d3f41"/><stop offset=".5" stop-color="#1f2022"/><stop offset="1" stop-color="#0e0f10"/></linearGradient>
<linearGradient id="gPlaca" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e6eaec"/><stop offset=".5" stop-color="#a9b1b6"/><stop offset="1" stop-color="#646c72"/></linearGradient>
<linearGradient id="gLamina" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6b7177"/><stop offset="1" stop-color="#30353a"/></linearGradient>
<linearGradient id="gManguera" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#142a45"/><stop offset=".45" stop-color="#3f6894"/><stop offset="1" stop-color="#142a45"/></linearGradient>
<linearGradient id="gBrilloV" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".45"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<linearGradient id="gDot" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe08a"/><stop offset="1" stop-color="#d89a1c"/></linearGradient>
<linearGradient id="gElec" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#c7b2f0"/><stop offset=".5" stop-color="#7b5bc4"/><stop offset="1" stop-color="#3c2a5c"/></linearGradient>
<pattern id="pFric" width="7" height="7" patternUnits="userSpaceOnUse"><rect width="7" height="7" fill="#9a4f2c"/><circle cx="1.6" cy="2" r=".9" fill="#c9774a"/><circle cx="5" cy="5.2" r=".8" fill="#5e2a14"/><circle cx="5.4" cy="1.4" r=".5" fill="#e3a47a"/></pattern>
<pattern id="pGrano" width="5" height="5" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".6" fill="#fff" opacity=".12"/><circle cx="3.5" cy="3" r=".5" fill="#000" opacity=".10"/></pattern>
<pattern id="pRosca" width="4" height="12" patternUnits="userSpaceOnUse"><rect width="4" height="12" fill="#b0b8bd"/><line x1="0" y1="0" x2="0" y2="12" stroke="#5e666b" stroke-width="1.6"/></pattern>
<filter id="fSombra" x="-20%" y="-20%" width="150%" height="160%"><feDropShadow dx="3" dy="9" stdDeviation="6" flood-color="#1f2d38" flood-opacity=".26"/></filter>
<filter id="fSel" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="0" stdDeviation="3.5" flood-color="#f2611d" flood-opacity="1"/><feDropShadow dx="0" dy="0" stdDeviation="9" flood-color="#ff9a3c" flood-opacity=".6"/></filter>
<mask id="mDisco" maskUnits="userSpaceOnUse" x="-230" y="-230" width="460" height="460"><g id="mDiscoCont"></g></mask>
<linearGradient id="b26Cuerpo" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#c3dbf3"/><stop offset=".25" stop-color="#7eaad8"/><stop offset=".55" stop-color="#4a7fb8"/><stop offset="1" stop-color="#1f4370"/></linearGradient>
<linearGradient id="b26Lado" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#16304f"/><stop offset="1" stop-color="#2c5383"/></linearGradient>
<linearGradient id="b26Tapa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7f9cbd"/><stop offset=".5" stop-color="#3d5a7c"/><stop offset="1" stop-color="#1d3048"/></linearGradient>
<linearGradient id="b26Alum" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe2c2"/><stop offset=".38" stop-color="#f28a30"/><stop offset=".6" stop-color="#ffbe80"/><stop offset="1" stop-color="#9c4510"/></linearGradient>
<linearGradient id="b26Cobre" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f0b98a"/><stop offset=".5" stop-color="#c27a45"/><stop offset="1" stop-color="#7d4522"/></linearGradient>
<linearGradient id="b26Puno" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a3a3a"/><stop offset=".5" stop-color="#1c1c1c"/><stop offset="1" stop-color="#0a0a0a"/></linearGradient>
<pattern id="b26Grano" width="5" height="5" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".6" fill="#fff" opacity=".12"/><circle cx="3.5" cy="3" r=".5" fill="#000" opacity=".10"/></pattern>
<filter id="b26Sombra" x="-20%" y="-20%" width="150%" height="160%"><feDropShadow dx="3" dy="9" stdDeviation="6" flood-color="#1f2d38" flood-opacity=".26"/></filter>
<marker id="estPunta" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><circle cx="5" cy="5" r="3.2" fill="#2b3640"/></marker>
`;

/* ---------- disco (1) ---------- */
// Agujeros (dibujo propio): dos filas de 12 en la pista, 6 ranuras en el porta-disco, 3 agujeros de tornillo.
const R_EXT=200, R_INT=100, R_PISTA=148, R_TOR=115;
function agujerosDisco(color){
  let s="";
  for(let k=0;k<12;k++){const a=(k*30)*Math.PI/180;s+=`<circle cx="${f(165*Math.cos(a))}" cy="${f(165*Math.sin(a))}" r="5.5" fill="${color}"/>`}
  for(let k=0;k<12;k++){const a=(k*30+15)*Math.PI/180;s+=`<circle cx="${f(184*Math.cos(a))}" cy="${f(184*Math.sin(a))}" r="4.8" fill="${color}"/>`}
  for(let k=0;k<6;k++){const g=k*60+30;s+=`<rect x="-14" y="-4.5" width="28" height="9" rx="4.5" fill="${color}" transform="rotate(${g}) translate(0 -128) rotate(90) rotate(-90) translate(0 0)"/>`}
  [45,135,225,315].forEach(g=>{const a=g*Math.PI/180;s+=`<circle cx="${f(R_TOR*Math.cos(a))}" cy="${f(R_TOR*Math.sin(a))}" r="9" fill="${color}"/>`});
  return s;
}
const montar=()=>{document.getElementById("mDiscoCont").innerHTML=`<circle r="${R_EXT}" fill="#fff"/><circle r="${R_INT}" fill="#000"/>${agujerosDisco("#000")}`};
function arteDisco(){
  // canto: la cara de atrás corrida hacia la izquierda-arriba (opuesto a la normal)
  const anillosMaq=[];for(let r=150;r<=198;r+=4)anillosMaq.push(`<circle r="${r}" fill="none" stroke="#fff" stroke-opacity="${r%8?'.05':'.09'}" stroke-width="1"/>`);
  return `<g transform="translate(${D[0]} ${D[1]}) matrix(0.78,-0.16,0,1,0,0)">
    <g mask="url(#mDisco)" transform="translate(-6.4 -2.8)"><circle r="${R_EXT}" fill="url(#gCanto)"/></g>
    <g mask="url(#mDisco)" transform="translate(-3.2 -1.4)"><circle r="${R_EXT}" fill="#5c6468"/></g>
    <g mask="url(#mDisco)">
      <circle r="${R_EXT}" fill="url(#gCara)"/>
      <path d="M${R_EXT} 0 A${R_EXT} ${R_EXT} 0 1 0 -${R_EXT} 0 A${R_EXT} ${R_EXT} 0 1 0 ${R_EXT} 0 Z M${R_PISTA} 0 A${R_PISTA} ${R_PISTA} 0 1 1 -${R_PISTA} 0 A${R_PISTA} ${R_PISTA} 0 1 1 ${R_PISTA} 0 Z" fill="url(#gPista)" fill-rule="evenodd"/>
      ${anillosMaq.join("")}
      <circle r="${R_PISTA}" fill="none" stroke="#000" stroke-opacity=".25" stroke-width="1.5"/>
      <circle r="${R_INT+1}" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="2"/>
      <path d="M-150 -120 A200 200 0 0 1 60 -190" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="10" stroke-linecap="round"/>
      <text x="0" y="-108" font-family="Archivo" font-size="9" font-weight="700" fill="#5a6166" text-anchor="middle" letter-spacing="1">MIN TH</text>
    </g>
    <circle r="${R_EXT}" fill="none" stroke="#2c3336" stroke-width="1.2"/>
  </g>`;
}
function arteTornillosDisco(){
  let s="";
  [45,135,225,315].forEach(g=>{const a=g*Math.PI/180;const [x,y]=PD(R_TOR*Math.cos(a),R_TOR*Math.sin(a));
    s+=`<ellipse cx="${f(x-2)}" cy="${f(y-1)}" rx="10.5" ry="12" fill="#3d4447"/>
        <ellipse cx="${f(x)}" cy="${f(y)}" rx="10" ry="11.5" fill="url(#gAcero)" stroke="#3a4144" stroke-width="1"/>
        <polygon points="${hexa(x,y,5.2,0)}" fill="#3b4246" transform="translate(${f(x)} ${f(y)}) scale(.8 1) translate(${f(-x)} ${f(-y)})"/>`;});
  return s;
}

/* ---------- caliper (3) ---------- */
const P_CUERPO="M-36,-84 Q-36,-98 -22,-98 L18,-98 Q34,-98 37,-82 L41,-40 Q45,0 41,40 L37,82 Q34,98 18,98 L-22,98 Q-36,98 -36,84 Z";
const P_PUENTE="M-36,-82 L-50,-78 Q-58,0 -50,78 L-36,82 Z";
const P_OREJAS="M26,-84 A13,13 0 1 1 26,-60 Z M26,62 A13,13 0 1 1 26,86 Z";
function arteCaliper(){
  return `<g transform="${LOC}" filter="url(#fSombra)">
    ${extruir(P_PUENTE,ATRAS[0],ATRAS[1],6,"#173052")}
    ${extruir(P_CUERPO,ATRAS[0],ATRAS[1],7,"url(#gCalLado)")}
    <circle cx="38" cy="-72" r="13" fill="#2d5486"/><circle cx="38" cy="74" r="13" fill="#2d5486"/>
    <circle cx="38" cy="-72" r="7" fill="#15181a"/><circle cx="38" cy="74" r="7" fill="#15181a"/>
    <path d="${P_PUENTE}" fill="url(#gCalLado)"/>
    <path d="M-36,-82 L-50,-78" stroke="#6b7379" stroke-width="1.2"/>
    <!-- ventana del puente: se ven los cantos de las dos pastillas y el borde del disco -->
    <path d="M-50,-46 Q-53,0 -50,46 L-39,46 L-39,-46 Z" fill="#0b0d0e" stroke="#4b5256" stroke-width=".8"/>
    <rect x="-49" y="-42" width="3" height="84" rx="1" fill="#5a4636"/><rect x="-42.6" y="-42" width="3" height="84" rx="1" fill="#5a4636"/>
    <rect x="-45.6" y="-44" width="2.6" height="88" fill="#b9c0c4"/>
    <rect x="-26" y="-122" width="32" height="28" rx="8" fill="url(#gCal)"/>
    <path d="${P_CUERPO}" fill="url(#gCal)"/>
    <path d="${P_CUERPO}" fill="url(#pGrano)"/>
    <path d="M4,-36 L4,-94 M4,42 L4,94" stroke="#1b1e21" stroke-width="7" stroke-linecap="round"/>
    <path d="M1,-36 L1,-92 M1,42 L1,92" stroke="#6e767c" stroke-width="1.4" stroke-linecap="round"/>
    <circle cx="4" cy="4" r="36" fill="#1d2023"/>
    <circle cx="4" cy="4" r="34" fill="url(#gDomo)"/>
    <circle cx="4" cy="4" r="24" fill="none" stroke="#1a1d20" stroke-opacity=".6" stroke-width="2"/>
    <path d="M-20,-16 A30,30 0 0 1 14,-26" fill="none" stroke="#fff" stroke-opacity=".25" stroke-width="3" stroke-linecap="round"/>
    <path d="M-36,84 L-36,-84 Q-36,-98 -22,-98 L18,-98" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="2.2"/>
    <path d="M-28,60 L-28,-60" stroke="url(#gBrilloV)" stroke-width="9" stroke-linecap="round"/>
    <!-- racor de la manguera (banjo) -->
    <ellipse cx="-10" cy="-124" rx="15" ry="6" fill="#8d959a"/>
    <polygon points="${hexa(-10,-128,9,0)}" fill="url(#gAcero)" stroke="#3a4144"/>
    <circle cx="-10" cy="-128" r="3" fill="#3a4144"/>
    <!-- base del purgador -->
    <rect x="12" y="-106" width="16" height="12" rx="4" fill="#2d5486"/>
  </g>`;
}

/* ---------- soporte del caliper (13) y tornillos (15) ---------- */
// Soporte en C: espina con las dos orejas de los tornillos (15) contra la barra y dos brazos que terminan
// en los pasadores deslizantes salientes (donde van los guardapolvos 6 y 7 y por donde flota el caliper).
const P_SOP="M66,-100 Q106,-96 105,-60 L100,-32 Q93,0 100,32 L105,60 Q106,96 66,100 L36,90 Q24,86 24,73 Q24,61 36,59 L60,57 Q72,54 75,42 L79,0 L75,-42 Q72,-54 60,-57 L36,-59 Q24,-61 24,-73 Q24,-86 36,-90 Z";
function pasadorSop(y){
  return `<rect x="-6" y="${y-6}" width="36" height="12" rx="6" fill="url(#gCromoV)" stroke="#5d656a" stroke-width=".8"/>
    <ellipse cx="-6" cy="${y}" rx="3" ry="6" fill="#c9ced1"/>
    <rect x="22" y="${y-9}" width="6" height="18" rx="2" fill="#3b4246"/>`;
}
function arteSoporte(){
  return `<g transform="${LOC}" filter="url(#fSombra)">
    ${pasadorSop(-73)}${pasadorSop(73)}
    ${extruir(P_SOP,-9,-1,5,"#2a2f33")}
    <path d="${P_SOP}" fill="url(#gSop)"/>
    <path d="${P_SOP}" fill="url(#pGrano)"/>
    <path d="M78,-36 Q86,0 78,36" fill="none" stroke="#2a2f33" stroke-width="5" stroke-linecap="round"/>
    <circle cx="86" cy="-54" r="18" fill="#5b6267" stroke="#2a2f33" stroke-width="1.5"/>
    <circle cx="86" cy="56" r="18" fill="#5b6267" stroke="#2a2f33" stroke-width="1.5"/>
    <circle cx="86" cy="-54" r="9" fill="#1b1f22"/><circle cx="86" cy="56" r="9" fill="#1b1f22"/>
    <circle cx="34" cy="-73" r="9" fill="#454c51" stroke="#2a2f33"/><circle cx="34" cy="73" r="9" fill="#454c51" stroke="#2a2f33"/>
    <path d="M36,-90 L66,-100 Q106,-96 105,-60" fill="none" stroke="#fff" stroke-opacity=".32" stroke-width="1.6"/>
  </g>`;
}
/* ---------- pastillas (9), lámina (14), resorte (11) ---------- */
// Pastilla en proporción ~2:1 (alto:ancho en pantalla; la x local va escalada por SX), esquinas redondeadas,
// oreja con el agujero del pasador (12) arriba y la ranura indicadora de desgaste a lo largo del material.
const P_PLACA_PAST="M-26,-38 Q-26,-45 -19,-45 L-9,-45 L-9,-49 A9,9 0 0 1 9,-49 L9,-45 L19,-45 Q26,-45 26,-38 L26,38 Q26,45 19,45 L-19,45 Q-26,45 -26,38 Z";
const P_FRIC="M-21,-33 Q-21,-39 -15,-39 L15,-39 Q21,-39 21,-33 L21,33 Q21,39 15,39 L-15,39 Q-21,39 -21,33 Z";
function artePastilla(dx,dy,giro){
  return `<g transform="${LOC} translate(${dx} ${dy}) rotate(${giro})" filter="url(#fSombra)">
    <path d="${P_PLACA_PAST}" transform="translate(-4 -1.5)" fill="#3e4549"/>
    <path d="${P_PLACA_PAST}" fill="url(#gPlaca)" stroke="#4b5256" stroke-width="1"/>
    <circle cx="0" cy="-50" r="4.2" fill="#1b1f22"/>
    <path d="${P_FRIC}" fill="url(#pFric)" stroke="#2c231c" stroke-width="1"/>
    <path d="M0,-37 L0,37" stroke="#1d1712" stroke-width="3.2"/>
    <path d="M-21,-33 Q-21,-39 -15,-39 L15,-39" fill="none" stroke="#a89380" stroke-opacity=".7" stroke-width="1"/>
    <path d="M-26,-38 Q-26,-45 -19,-45 L-9,-45" fill="none" stroke="#fff" stroke-opacity=".4" stroke-width="1"/>
  </g>`;
}
// Lámina antirruido: misma silueta que la placa de la pastilla, con recubrimiento oscuro y una pestaña de agarre
/* ---------- purgador (8), pasador (12), grapas (10) ---------- */
const artePurgador=()=>`<g transform="${LOC} translate(20 -104) rotate(-8)">
    <g class="esq-oculto-arm"><rect x="-4" y="6" width="8" height="14" fill="url(#pRosca)" transform="rotate(90 0 13) rotate(-90 0 13)"/></g>
    <polygon points="${hexa(0,0,8,0)}" fill="url(#gAcero)" stroke="#3a4144"/>
    <rect x="-3.5" y="-17" width="7" height="12" fill="#a7aeb2"/>
    <rect x="-6.5" y="-29" width="13" height="14" rx="5" fill="url(#gCaucho)"/>
  </g>`;
/* ---------- bomba (2), manigueta (3) e interruptor (4): adaptados de la NMAX fig. 26 ---------- */
const O26=[330,70], K=0.9;
const G=s=>`translate(${O26[0]} ${O26[1]}) scale(${s*K} ${K})`;
const ATRAS26=[3,-5];
function extruir26(d,pasos,fill,k=1){let r="";for(let i=pasos;i>=1;i--)r+=`<path d="${d}" transform="translate(${f(ATRAS26[0]*i*k/pasos)} ${f(ATRAS26[1]*i*k/pasos)})" fill="${fill}"/>`;return r}
const P_CIL="M-72,-24 L-72,-48 Q-72,-60 -60,-60 L38,-60 Q50,-60 50,-48 L50,-26 Q50,-14 38,-14 L-60,-14 Q-72,-14 -72,-24 Z";
const P_DEP="M-66,-58 L-62,-122 Q-61,-131 -52,-131 L18,-131 Q27,-131 28,-122 L32,-58 Z";
const P_PIV="M44,-62 L58,-64 A18,18 0 0 1 58,-28 L44,-26 Z";
const P_SAL="M-70,-50 L-84,-52 A16,16 0 0 0 -84,-20 L-70,-22 Z";
function arteBomba(s){
  return `<g transform="${G(s)}" filter="url(#b26Sombra)">
    ${extruir26(P_CIL,6,"url(#b26Lado)")}${extruir26(P_DEP,6,"url(#b26Lado)")}
    <path d="M-34,-16 L-34,-4 L34,-4 L34,-16 Z" fill="#202427"/>
    <path d="${P_SAL}" fill="#2a2f33"/><circle cx="-84" cy="-36" r="12" fill="#3b4247"/>
    <path d="${P_CIL}" fill="url(#b26Cuerpo)"/><path d="${P_CIL}" fill="url(#b26Grano)"/>
    <path d="${P_PIV}" fill="url(#b26Cuerpo)"/><circle cx="60" cy="-46" r="12" fill="#2b3034"/>
    <path d="${P_DEP}" fill="url(#b26Cuerpo)"/><path d="${P_DEP}" fill="url(#b26Grano)"/>
    <ellipse cx="-16" cy="-72" rx="11" ry="7" fill="#1a1d20" stroke="#6b7379" stroke-width="1.2"/>
    <ellipse cx="-16" cy="-72" rx="8" ry="4.5" fill="url(#gDot)"/>
    <line x1="-26" y1="-67" x2="-6" y2="-67" stroke="#f3efe6" stroke-width="1" opacity=".7"/>
    <path d="M-60,-58 L38,-58" stroke="#fff" stroke-opacity=".55" stroke-width="2"/><path d="M-62,-52 L40,-52" stroke="#fff" stroke-opacity=".18" stroke-width="5" stroke-linecap="round"/>
    <path d="M-62,-122 Q-61,-131 -52,-131 L18,-131" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="2"/>
    <path d="M-50,-122 L-48,-64" stroke="url(#gBrilloV)" stroke-width="8" stroke-linecap="round"/>
    <ellipse cx="50" cy="-37" rx="4" ry="11" fill="#141618"/>
  </g>`;
}
/* kit (2, 22): pistón, copa primaria y secundaria, resorte, seguro y guardapolvo; sale del cilindro hacia afuera */
const P_TAPA="M-62,-128 Q-62,-136 -54,-136 L20,-136 Q28,-136 28,-128 L28,-100 Q28,-94 22,-94 L-56,-94 Q-62,-94 -62,-100 Z";
const arteTapa=s=>`<g transform="${G(s)}" filter="url(#b26Sombra)">${extruir26(P_TAPA,3,"#0f1112",.6)}<path d="${P_TAPA}" fill="url(#b26Tapa)"/>
    <path d="M-54,-133 L20,-133" stroke="#fff" stroke-opacity=".28" stroke-width="1.4"/>
    <rect x="-34" y="-122" width="36" height="14" rx="3" fill="none" stroke="#3d4448" stroke-width="1.2"/>
    <text x="-16" y="-111.5" font-size="8" font-family="Archivo" font-weight="700" fill="#7c858a" text-anchor="middle" transform="scale(${s} 1)" style="transform-box:fill-box;transform-origin:center">DOT 3/4</text></g>`;
const P_MAN="M48,-58 Q60,-66 74,-60 L118,-58 Q160,-58 200,-50 Q214,-47 214,-38 Q213,-30 200,-32 Q156,-38 118,-40 L80,-38 Q70,-32 60,-34 L46,-40 Z";
const arteManigueta=s=>`<g transform="${G(s)}" filter="url(#b26Sombra)">${extruir26(P_MAN,3,"#a24a10",.7)}
    <path d="${P_MAN}" fill="url(#b26Alum)" stroke="#8f3f0c" stroke-width="1"/>
    <path d="M80,-56 L118,-55 Q160,-55 200,-47" fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="1.8"/>
    <circle cx="60" cy="-46" r="10" fill="#9aa2a7" stroke="#40474c"/><circle cx="60" cy="-46" r="5" fill="#2a2f33"/>
    <circle cx="${f(160)}" cy="-46" r="3" fill="#6e767b"/><circle cx="174" cy="-44" r="3" fill="#6e767b"/><circle cx="188" cy="-42" r="3" fill="#6e767b"/></g>`;
/* abrazadera (10, 30): media luna que aprieta la bomba contra el manubrio */
/* interruptor del freno (12, 32): cajita negra con el émbolo que toca la manigueta, y su cable */
const arteInterruptor=s=>`<g transform="${G(s)}" filter="url(#b26Sombra)">
    <path d="M40,-10 C30,6 18,14 2,18" fill="none" stroke="#111" stroke-width="5" stroke-linecap="round"/>
    <path d="M40,-10 C30,6 18,14 2,18" fill="none" stroke="#a98be0" stroke-width="2" stroke-linecap="round"/>
    <rect x="38" y="-14" width="28" height="22" rx="4" fill="url(#gElec)" stroke="#3c2a5c"/><path d="M41,-11 L63,-11" stroke="#fff" stroke-opacity=".45" stroke-width="1.4"/>
    <rect x="62" y="-8" width="8" height="8" rx="2" fill="#9aa2a7"/>
    <circle cx="56" cy="-3" r="5" fill="#3c2a5c"/></g>`;

/* bomba completa: cuerpo + tapa del depósito (en la NKD la tapa no se vende aparte) + palanca del CBS abajo */
function arteBombaNKD(){
  return `<g>${arteBomba(1)}${arteTapa(1)}
    <g transform="${G(1)}" filter="url(#b26Sombra)">
      <path d="M-40,-14 L-46,10 Q-47,16 -41,17 L-14,17 Q-8,16 -10,10 L-16,-14 Z" fill="url(#b26Alum)" stroke="#8f3f0c"/>
      <circle cx="-28" cy="6" r="5" fill="#1b1f22"/>
      <rect x="-86" y="-31" width="16" height="12" rx="3" fill="url(#b26Cobre)"/>
    </g></g>`;
}
/* cable del CBS (9): funda negra con sus terminales; va de la palanca de la bomba al pedal (pasa por detrás de la manguera) */
const P_CABLE=[[300,92],[296,150],[262,230],[205,320],[176,440]];
function suave(p){let d=`M${p[0][0]},${p[0][1]}`;for(let i=0;i<p.length-1;i++){const a=p[i-1]||p[i],b=p[i],c=p[i+1],e=p[i+2]||c;
  d+=` C${f(b[0]+(c[0]-a[0])/6)},${f(b[1]+(c[1]-a[1])/6)} ${f(c[0]-(e[0]-b[0])/6)},${f(c[1]-(e[1]-b[1])/6)} ${c[0]},${c[1]}`}return d}
function arteCable(){
  const d=suave(P_CABLE), [x1,y1]=P_CABLE[P_CABLE.length-1];
  return `<g filter="url(#fSombra)">
    <path d="${d}" fill="none" stroke="#8f3f0c" stroke-width="9" stroke-linecap="round"/>
    <path d="${d}" fill="none" stroke="#e0731f" stroke-width="6" stroke-linecap="round"/>
    <path d="${d}" fill="none" stroke="#ffd2a3" stroke-opacity=".8" stroke-width="1.6" stroke-linecap="round" transform="translate(-2 -1)"/>
    <rect x="293" y="86" width="14" height="22" rx="3" fill="url(#gAcero)" stroke="#3a4144"/>
    <rect x="${x1-7}" y="${y1-4}" width="14" height="26" rx="3" fill="url(#gAcero)" stroke="#3a4144"/>
    <line x1="${x1}" y1="${y1+22}" x2="${x1-2}" y2="${y1+44}" stroke="#c9ced1" stroke-width="2.4"/>
    <circle cx="${x1-2}" cy="${y1+46}" r="4" fill="#9aa2a7"/>
    <path d="${d}" fill="none" stroke="#000" stroke-opacity="0" stroke-width="26" pointer-events="stroke"/>
    <text class="esq-ctx-txt" x="${x1+16}" y="${y1+40}">al pedal (CBS)</text>
  </g>`;
}
/* cáliper completo (7): soporte, cuerpo y purgador en una sola pieza, como lo vende el catálogo */
const arteCaliperNKD=()=>`<g>${arteSoporte()}${arteCaliper()}${artePurgador()}</g>`;
/* ---------- contexto: manubrio, disco y barra (otras láminas) ---------- */
function arteManubrio(){
  let r="";for(let x=452;x<548;x+=8)r+=`<line x1="${x}" y1="58" x2="${x}" y2="82" stroke="#2f2f2f" stroke-width="2"/>`;
  return `<g class="esq-ctx" pointer-events="none">
    <rect x="150" y="59" width="400" height="22" rx="11" fill="#3b4246"/>
    <rect x="150" y="61" width="400" height="5" rx="2.5" fill="#fff" opacity=".12"/>
    <rect x="446" y="54" width="108" height="32" rx="14" fill="url(#b26Puno)"/>${r}
    <text class="esq-ctx-txt" x="160" y="104">Manubrio</text></g>`;
}
const arteDiscoCtx=()=>`<g class="esq-ctx" data-ctx="disco" pointer-events="none">${arteDisco()}<text class="esq-ctx-txt" x="690" y="560">Disco (fig. F-6)</text></g>`;
function arteBarra(){
  const ax=548, ay=404, ux=-0.44, uy=-0.9, px=0.9, py=-0.44, w=40, L=440;
  const p=[[ax-w*px,ay-w*py],[ax+ux*L-w*px,ay+uy*L-w*py],[ax+ux*L+w*px,ay+uy*L+w*py],[ax+w*px,ay+w*py]];
  const [s1x,s1y]=R(86,-54),[s2x,s2y]=R(86,56);
  return `<g class="esq-ctx esq-ctx-barra" data-ctx="barra" pointer-events="none">
    <path d="M${f(p[0][0])},${f(p[0][1])} L${f(p[1][0])},${f(p[1][1])} L${f(p[2][0])},${f(p[2][1])} L${f(p[3][0])},${f(p[3][1])} A40,40 0 0 1 ${f(p[0][0])},${f(p[0][1])} Z"
      fill="#9fb0bc" fill-opacity=".10" stroke="#7d8a94" stroke-opacity=".8" stroke-width="1.6" stroke-dasharray="7 5" pointer-events="visibleStroke"/>
    <circle cx="${f(s1x)}" cy="${f(s1y)}" r="24" fill="none" stroke="#7d8a94" stroke-opacity=".7" stroke-dasharray="5 4"/>
    <circle cx="${f(s2x)}" cy="${f(s2y)}" r="24" fill="none" stroke="#7d8a94" stroke-opacity=".7" stroke-dasharray="5 4"/>
    <circle cx="${D[0]}" cy="${D[1]}" r="16" fill="#7d8a94" fill-opacity=".12" stroke="#7d8a94" stroke-opacity=".8" stroke-dasharray="4 3"/>
    <rect x="${f(ax+ux*300-60)}" y="${f(ay+uy*300-8)}" width="120" height="40" fill="transparent"/>
    <text class="esq-ctx-txt" x="640" y="156">Barra derecha</text>
    <text class="esq-ctx-txt" x="640" y="171">(otra lámina)</text>
  </g>`;
}
/* ---------- rótulos del estilo ilustrado: nombre + qué hace, con línea guía (solo armado) ---------- */
// [nombre, qué hace, color del sistema, punto en la pieza, posición del texto, alineación]
const ROTU=[
  ["BOMBA (maestro)","crea la presión","#2f6aa8",[262,-26],[112,-30],"start"],
  ["MANIGUETA","inicia la presión","#d9661a",[505,20],[620,-46],"start"],
  ["INTERRUPTOR","prende la luz de stop","#6a4bb0",[392,64],[620,44],"start"],
  ["MANGUERA","lleva el líquido al cáliper","#2f6aa8",[352,190],[620,112],"start"],
  ["CABLE CBS","el pedal también frena","#d9661a",[240,268],[112,226],"start"],
  ["CÁLIPER","aprieta las pastillas","#2f6aa8",[340,392],[112,352],"start"],
  ["PASTILLAS","frenan por fricción","#a4532c",[370,346],[112,432],"start"]
];
function arteRotulos(){
  let s=`<g class="esq-ctx esq-est-rotulos" pointer-events="none" aria-hidden="true">`;
  ROTU.forEach(([n,t,c,[ax,ay],[tx,ty],al])=>{
    const w=Math.max(n.length*8.6,t.length*6.3)+6, bx=al==="start"?tx-6:tx-w, ly=ty+8;
    const ex=al==="start"?(ax<tx?bx:bx+w):bx+w;
    s+=`<path d="M${ax},${ay} L${f(ex+(ax<tx?-14:14))},${ly} L${f(ex)},${ly}" fill="none" stroke="#2b3640" stroke-width="1.2" marker-start="url(#estPunta)"/>
      <rect x="${f(bx)}" y="${ty-15}" width="${f(w)}" height="38" rx="6" fill="#fff" fill-opacity=".86" stroke="${c}" stroke-opacity=".35"/>
      <rect x="${f(bx)}" y="${ty-15}" width="4" height="38" rx="2" fill="${c}"/>
      <text class="esq-est-rot-n" x="${tx}" y="${ty}" fill="${c}">${n}</text>
      <text class="esq-est-rot-t" x="${tx}" y="${ty+16}">${t}</text>`;
  });
  // leyenda de colores por sistema
  const L=[["#d9661a","Mando"],["#2f6aa8","Hidráulico"],["#a4532c","Fricción"],["#6a4bb0","Eléctrico"],["#8d969c","Otra lámina"]];
  s+=`<g transform="translate(112 516)"><rect x="-8" y="-16" width="290" height="58" rx="8" fill="#fff" fill-opacity=".86" stroke="#c9d1d8"/>`;
  L.forEach(([c,t],i)=>{const x=(i%3)*92, y=(i/3|0)*24;s+=`<rect x="${x}" y="${y-9}" width="14" height="12" rx="3" fill="${c}"/><text class="esq-est-rot-t" x="${x+19}" y="${y+1}">${t}</text>`});
  return s+`</g></g>`;
}

/* ============================================================
   Piezas: id, número de lámina, arte, ancla de la etiqueta y su corrimiento,
   y si la etiqueta se ve armado ("arm") o solo en el despiece ("exp").
   ============================================================ */
const FN_SVG=`<svg id="fn" viewBox="0 0 900 440" role="img" aria-labelledby="fnTit">
        <title id="fnTit">Esquema del freno hidráulico: manigueta, bomba, manguera y cáliper cortado con pistón, pastillas y disco; flechas azules para la presión del líquido y rojas para la fuerza</title>
        <defs>
          <pattern id="fnGrilla" width="40" height="40" patternUnits="userSpaceOnUse"><rect width="40" height="40" fill="#f2f4f6"/><path d="M40 0H0V40" fill="none" stroke="#dde3e8" stroke-width="1"/></pattern>
          <linearGradient id="fnCromo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".45" stop-color="#9aa3a8"/><stop offset=".6" stop-color="#eef1f2"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
          <linearGradient id="fnCuerpo" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#b9d4ef"/><stop offset=".3" stop-color="#6f9fd2"/><stop offset="1" stop-color="#22466f"/></linearGradient>
          <linearGradient id="fnMando" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe2c2"/><stop offset=".4" stop-color="#f28a30"/><stop offset=".6" stop-color="#ffbe80"/><stop offset="1" stop-color="#9c4510"/></linearGradient>
          <linearGradient id="fnDisco" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8d959a"/><stop offset=".5" stop-color="#f3f5f6"/><stop offset="1" stop-color="#8d959a"/></linearGradient>
          <linearGradient id="fnDot" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe08a"/><stop offset="1" stop-color="#e0a52a"/></linearGradient>
          <pattern id="fnRayas" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="8" height="8" fill="#c3cad0"/><line x1="0" y1="0" x2="0" y2="8" stroke="#8d969c" stroke-width="3"/></pattern>
          <pattern id="fnFric" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#9a4f2c"/><circle cx="1.5" cy="2" r=".8" fill="#c9774a"/><circle cx="4.5" cy="4.6" r=".7" fill="#5e2a14"/></pattern>
          <radialGradient id="fnCalorG"><stop offset="0" stop-color="#ff9a3c" stop-opacity=".95"/><stop offset=".6" stop-color="#f2611d" stop-opacity=".55"/><stop offset="1" stop-color="#f2611d" stop-opacity="0"/></radialGradient>
          <filter id="fnSombra" x="-20%" y="-20%" width="150%" height="170%"><feDropShadow dx="2" dy="6" stdDeviation="4" flood-color="#1f2d38" flood-opacity=".25"/></filter>
          <marker id="fnPAzul" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#1f6fd1"/></marker>
          <marker id="fnPRojo" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#d7262e"/></marker>
        </defs>
        <rect x="-40" y="-20" width="980" height="760" fill="url(#fnGrilla)"/>
        <!-- manubrio y bomba -->
        <rect x="10" y="98" width="290" height="24" rx="12" fill="url(#fnCromo)" stroke="#8d969c"/>
        <rect x="14" y="92" width="110" height="36" rx="16" fill="#1f2022" filter="url(#fnSombra)"/>
        <g stroke="#3a3c3e" stroke-width="2">
          <line x1="30" y1="94" x2="30" y2="126"/><line x1="46" y1="94" x2="46" y2="126"/><line x1="62" y1="94" x2="62" y2="126"/><line x1="78" y1="94" x2="78" y2="126"/><line x1="94" y1="94" x2="94" y2="126"/>
        </g>
        <text class="esq-fn-et" x="20" y="80">Puño derecho</text>
        <!-- depósito -->
        <g filter="url(#fnSombra)">
        <rect x="168" y="30" width="78" height="52" rx="8" fill="#e8eef4" fill-opacity=".9" stroke="#2f6aa8" stroke-width="1.5"/>
        <rect x="172" y="48" width="70" height="30" rx="5" fill="url(#fnDot)"/>
        <rect x="164" y="24" width="86" height="10" rx="4" fill="#1d3048"/>
        </g>
        <path d="M174 50 L240 50" stroke="#fff" stroke-opacity=".7" stroke-width="2"/>
        <text class="esq-fn-et" x="256" y="44">Depósito</text>
        <text class="esq-fn-et" x="256" y="60" data-ym="68">DOT 3/4</text>
        <!-- cuerpo de la bomba cortado -->
        <rect x="140" y="132" width="132" height="48" rx="10" fill="url(#fnCuerpo)" filter="url(#fnSombra)"/>
        <path d="M150 136 L262 136" stroke="#fff" stroke-opacity=".6" stroke-width="2"/>
        <rect id="fn-camara" x="150" y="144" width="112" height="24" rx="3" fill="#e8a92a" opacity=".9"/>
        <rect x="200" y="82" width="10" height="62" fill="#e8a92a" opacity=".9"/>
        <g id="fn-mpiston"><rect x="150" y="142" width="34" height="28" rx="4" fill="url(#fnCromo)" stroke="#6c7479" stroke-width=".8"/><rect x="128" y="151" width="24" height="10" fill="#9aa3a8"/></g>
        <path id="fn-fl-bomba" class="esq-est-flujo" d="M196 156 L250 156" stroke="#1f6fd1" stroke-width="4" marker-end="url(#fnPAzul)" opacity="0"/>
        <text class="esq-fn-et" x="150" y="204" data-ym="226">Bomba (pistón pequeño)</text>
        <!-- manigueta (mando, naranja) -->
        <g id="fn-lever" style="transform-origin:130px 145px">
          <path d="M138,141 Q139,151 128,153 L34,151 Q19,151 19,144 Q19,136 34,137 L126,137 Q136,135 138,141 Z" fill="url(#fnMando)" stroke="#8f3f0c" stroke-width="1.5"/>
          <path d="M34,139 L126,139" stroke="#fff" stroke-opacity=".7" stroke-width="1.4"/>
          <circle cx="130" cy="145" r="6" fill="#2b3135" stroke="#9aa3a8"/>
        </g>
        <path id="fn-fl-mano" class="esq-est-flujo" d="M64 196 L64 162" stroke="#d7262e" stroke-width="5" marker-end="url(#fnPRojo)" opacity="0"/>
        <text class="esq-fn-et esq-claro" x="24" y="184">Manigueta (delante del puño)</text>
        <!-- manguera (hidráulico, azul oscuro) -->
        <path id="fn-hose" d="M272 156 C330 156 350 92 400 92" fill="none" stroke="#1d3a5e" stroke-width="13" stroke-linecap="round"/>
        <path class="esq-solo-pc" d="M490 92 C560 92 560 150 540 214 L540 222 Q540 248 580 248" fill="none" stroke="#1d3a5e" stroke-width="13" stroke-linecap="round"/>
        <path id="fn-fluido1" d="M272 156 C330 156 350 92 400 92" fill="none" stroke="#e8a92a" stroke-width="5" stroke-linecap="round" opacity=".9"/>
        <path class="esq-solo-pc" id="fn-fluido2" d="M490 92 C560 92 560 150 540 214 L540 222 Q540 248 580 248" fill="none" stroke="#e8a92a" stroke-width="5" stroke-linecap="round" opacity=".9"/>
        <path id="fn-pulso1" d="M272 156 C330 156 350 92 400 92" fill="none" stroke="#fff3d6" stroke-width="3" stroke-linecap="round" opacity="0"/>
        <path class="esq-solo-pc" id="fn-pulso2" d="M490 92 C560 92 560 150 540 214 L540 222 Q540 248 580 248" fill="none" stroke="#fff3d6" stroke-width="3" stroke-linecap="round" opacity="0"/>
        <path class="esq-solo-movil" d="M492 92 Q500 92 500 106 L500 330 Q500 345 485 345 L44 345 Q28 345 28 361 L28 498 Q28 510 40 510 L110 510" fill="none" stroke="#1d3a5e" stroke-width="13" stroke-linecap="round"/>
        <path class="esq-solo-movil" id="fn-fluido2m" d="M492 92 Q500 92 500 106 L500 330 Q500 345 485 345 L44 345 Q28 345 28 361 L28 498 Q28 510 40 510 L110 510" fill="none" stroke="#e8a92a" stroke-width="5" stroke-linecap="round" opacity=".9"/>
        <path class="esq-solo-movil" id="fn-pulso2m" d="M492 92 Q500 92 500 106 L500 330 Q500 345 485 345 L44 345 Q28 345 28 361 L28 498 Q28 510 40 510 L110 510" fill="none" stroke="#fff3d6" stroke-width="3" stroke-linecap="round" opacity="0"/>
        <text class="esq-fn-et esq-solo-movil" x="330" y="330">Manguera</text>
        <path d="M396 92 L494 92" fill="none" stroke="#1d3a5e" stroke-width="13" stroke-linecap="round"/>
        <path d="M396 92 L494 92" fill="none" stroke="#e8a92a" stroke-width="5" stroke-linecap="round" opacity=".9"/>
        <g id="fn-fl-linea" class="esq-est-flujo" opacity="0" fill="none" stroke="#1f6fd1" stroke-width="4" stroke-linecap="round">
          <path d="M300 128 C326 118 340 82 372 72" marker-end="url(#fnPAzul)"/>
          <path d="M420 70 L470 70" marker-end="url(#fnPAzul)"/>
          <path class="esq-solo-pc" d="M568 110 C578 140 574 172 562 200" marker-end="url(#fnPAzul)"/>
          <path class="esq-solo-movil" d="M478 130 L478 300" marker-end="url(#fnPAzul)"/>
          <path class="esq-solo-movil" d="M290 326 L130 326" marker-end="url(#fnPAzul)"/>
        </g>
        <text class="esq-fn-et" x="292" y="186" data-ym="164" data-xm="330">Manguera</text>
        <!-- caliper cortado (en el celular se baja debajo de la bomba) -->
        <g id="fnCorte">
        <g>
          <!-- soporte fijo a la barra (rayado) y pasador -->
          <rect x="560" y="132" width="48" height="40" rx="4" fill="url(#fnRayas)" stroke="#8d969c"/>
          <text class="esq-fn-et" x="556" y="124">Soporte (fijo)</text>
          <rect x="590" y="147" width="230" height="10" rx="5" fill="url(#fnCromo)" stroke="#8d969c" stroke-width=".6"/>
          <text class="esq-fn-et" x="722" y="124">Pasador deslizante</text>
          <!-- disco (corte) -->
          <g id="fn-discoG">
            <rect x="693" y="200" width="16" height="225" fill="url(#fnDisco)" stroke="#8d969c" stroke-width=".6"/>
            <line id="fn-mov" x1="701" y1="204" x2="701" y2="425" stroke="#5f686d" stroke-width="3" class="esq-baja"/>
            <rect id="fn-contacto" x="686" y="212" width="9" height="92" rx="3" fill="#ff9a3c" opacity="0"/>
            <ellipse id="fn-calor" cx="701" cy="260" rx="60" ry="70" fill="url(#fnCalorG)" opacity="0"/>
          </g>
          <text class="esq-fn-et" x="540" y="436">Disco (gira con la rueda) →</text>
          <!-- cuerpo flotante con la pastilla de afuera -->
          <g id="fn-cuerpo">
            <path d="M592 168 L800 168 Q812 168 812 180 L812 312 Q812 322 800 322 L760 322 L760 196 L640 196 L640 322 L604 322 Q592 322 592 310 Z" fill="url(#fnCuerpo)" stroke="#22466f" stroke-width="1.5" filter="url(#fnSombra)"/>
            <path d="M600 174 L804 174" stroke="#fff" stroke-opacity=".6" stroke-width="2"/>
            <rect x="782" y="142" width="26" height="20" rx="5" fill="url(#fnCuerpo)" stroke="#22466f"/>
            <rect x="598" y="142" width="22" height="20" rx="5" fill="url(#fnCuerpo)" stroke="#22466f"/>
            <!-- cilindro con líquido -->
            <rect x="604" y="214" width="52" height="88" fill="#e8a92a" opacity=".9"/>
            <rect x="604" y="210" width="40" height="4" fill="#22466f"/><rect x="604" y="302" width="40" height="4" fill="#22466f"/>
            <rect id="fn-sello1" x="640" y="207" width="9" height="9" fill="#111" rx="1.5"/>
            <rect id="fn-sello2" x="640" y="300" width="9" height="9" fill="#111" rx="1.5"/>
            <!-- pastilla de afuera, sujeta al dedo del cuerpo -->
            <rect x="738" y="210" width="8" height="96" rx="2" fill="#a9b1b6"/>
            <rect x="715" y="214" width="23" height="88" rx="3" fill="url(#fnFric)"/>
            <path id="fn-fl-dedo" class="esq-est-flujo" d="M790 258 L752 258" stroke="#d7262e" stroke-width="6" marker-end="url(#fnPRojo)" opacity="0"/>
          </g>
          <!-- pistón y pastilla de adentro -->
          <g id="fn-piston">
            <rect x="620" y="216" width="36" height="84" rx="4" fill="url(#fnCromo)" stroke="#6c7479" stroke-width=".8"/>
            <rect id="fn-padL" x="656" y="210" width="8" height="96" rx="2" fill="#a9b1b6"/>
            <rect x="664" y="214" width="23" height="88" rx="3" fill="url(#fnFric)"/>
            <path id="fn-fl-piston" class="esq-est-flujo" d="M624 258 L652 258" stroke="#d7262e" stroke-width="6" marker-end="url(#fnPRojo)" opacity="0"/>
          </g>
          <text class="esq-fn-et" x="560" y="345" data-ym="368">Pistón</text>
          <text class="esq-fn-et" x="588" y="302" text-anchor="end">Sello →</text>
          <text class="esq-fn-et" x="588" y="321" data-ym="326" text-anchor="end">(lo devuelve)</text>
          <text class="esq-fn-et" x="740" y="345" data-ym="345" data-xm="704">Pastillas</text>
          <text class="esq-fn-et" x="582" y="275" text-anchor="end">Líquido →</text>
        </g>
        <!-- rueda indicadora -->
        <g transform="translate(856 392)">
          <circle r="40" fill="#1f2022" stroke="#3a3c3e" stroke-width="8"/>
          <g class="esq-giro" id="fn-rueda">
            <circle r="30" fill="url(#fnCromo)"/>
            <path d="M0 -28 L0 28 M-28 0 L28 0 M-20 -20 L20 20 M-20 20 L20 -20" stroke="#6c7479" stroke-width="4"/>
            <circle r="7" fill="#9aa3a8"/>
            <circle cx="0" cy="-22" r="4" fill="#f2611d"/>
          </g>
        </g>
        <text class="esq-fn-et" x="856" y="340" text-anchor="middle">Rueda</text>
        </g>
        <!-- leyenda de flechas -->
        <g class="esq-solo-pc" transform="translate(612 22)">
          <rect x="-10" y="-14" width="282" height="56" rx="8" fill="#fff" fill-opacity=".9" stroke="#c9d1d8"/>
          <path d="M0 2 L34 2" stroke="#1f6fd1" stroke-width="4" marker-end="url(#fnPAzul)"/><text class="esq-est-fn-ley" x="44" y="7">Presión del líquido</text>
          <path d="M0 26 L34 26" stroke="#d7262e" stroke-width="4" marker-end="url(#fnPRojo)"/><text class="esq-est-fn-ley" x="44" y="31">Fuerza (mano, pistón, apriete)</text>
        </g>
        <g class="esq-solo-movil" transform="translate(40 252)">
          <path d="M0 0 L40 0" stroke="#1f6fd1" stroke-width="5" marker-end="url(#fnPAzul)"/><text class="esq-est-fn-ley" x="52" y="8">Presión</text>
          <path d="M200 0 L240 0" stroke="#d7262e" stroke-width="5" marker-end="url(#fnPRojo)"/><text class="esq-est-fn-ley" x="252" y="8">Fuerza</text>
        </g>
      </svg>`;

function fnAplicar(s,$){
  $("fn-lever").style.transform=`rotate(${s.lever}deg)`;
  $("fn-mpiston").style.transform=`translate(${s.mp}px,0)`;
  $("fn-camara").setAttribute("fill",s.mp?"#ff9a3c":"#e8a92a");
  $("fn-piston").style.transform=`translate(${s.piston}px,0)`;
  $("fn-cuerpo").style.transform=`translate(${s.cuerpo}px,0)`;
  $("fn-calor").style.opacity=s.calor;
  $("fn-contacto").style.opacity=s.piston?(s.cuerpo?.95:.75):0;
  ["fn-sello1","fn-sello2"].forEach(id=>{const e=$(id);e.style.transformBox="fill-box";e.style.transformOrigin="center";e.style.transform=s.piston?"rotate(28deg) scale(1.25)":"";e.setAttribute("fill",s.piston?"#4a3a2a":"#111")});
  ["fn-pulso1","fn-pulso2","fn-pulso2m"].forEach(id=>{$(id).classList.toggle("esq-pulso",s.pulso);$(id).style.opacity=s.pulso?1:0});
  ["fn-fluido1","fn-fluido2","fn-fluido2m"].forEach(id=>$(id).setAttribute("stroke",s.pulso?"#ff9a3c":"#e8a92a"));
  // flechas del flujo (estilo ilustrado): roja = fuerza, azul = presión del líquido
  const ver=(id,v)=>{$(id).style.opacity=v?1:0};
  ver("fn-fl-mano",s.lever!==0); ver("fn-fl-bomba",s.mp>0); ver("fn-fl-linea",s.pulso);
  ver("fn-fl-piston",s.piston>0); ver("fn-fl-dedo",s.cuerpo<0);
  const r=$("fn-rueda"),m=$("fn-mov");
  r.classList.remove("esq-lento","esq-quieto");m.classList.remove("esq-lento","esq-quieto");
  if(s.rueda){r.classList.add("esq-"+s.rueda);m.classList.add("esq-"+s.rueda)}
}
return {defs:DEFS,montar,marcos:{LOC},arteBarra,arteBombaNKD,arteCable,arteCaliperNKD,arteDiscoCtx,arteInterruptor,arteManigueta,arteManubrio,artePastilla,arteRotulos,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
