/* Arte de la lámina 11 de la NMAX 155 (tapa de la transmisión y filtro de la correa): dibujos propios de TallerYa.
   Vista desde el lado izquierdo de la moto, de frente a la tapa; la profundidad va hacia arriba a la derecha (ATRAS).
   La silueta de las tapas sale del contexto de la fig. 12 (arteTapa). Por dentro de la tapa exterior (8) van las espumas
   antirruido; entre las dos tapas, el filtro de la correa con sus sellos. Tornillería, pasador, manguera, abrazadera,
   o-ring y placas de espuma salen de piezas-comunes.js; aquí va solo lo propio. */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["nmax-fig11"]=(function(){
"use strict";
const f=n=>Math.round(n*10)/10;
const ATRAS=[9,-6];
const TAPA="M150 300 Q150 250 200 245 L470 228 Q560 214 650 236 Q752 262 760 340 Q768 440 690 492 Q620 530 520 520 L250 530 Q160 532 150 470 Z";   // silueta de la fig. 12
const BOCA=[310,350];   // toma de aire de la tapa interior (frente al variador)
function extruir(d,pasos,fill,k,tr){let r="";for(let i=pasos;i>=1;i--)r+=`<path d="${d}" transform="translate(${f(ATRAS[0]*i*k/pasos)} ${f(ATRAS[1]*i*k/pasos)}) ${tr}" fill="${fill}"/>`;return r}

const DEFS=`
<linearGradient id="a11Alum" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d9dde0"/><stop offset=".45" stop-color="#9aa2a7"/><stop offset=".7" stop-color="#c3c9cc"/><stop offset="1" stop-color="#5f676c"/></linearGradient>
<linearGradient id="a11AlumOsc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8d959a"/><stop offset="1" stop-color="#3b4246"/></linearGradient>
<linearGradient id="a11Plast" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6a7177"/><stop offset=".45" stop-color="#3a4045"/><stop offset="1" stop-color="#1c1f22"/></linearGradient>
<linearGradient id="a11Brillo" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<linearGradient id="a11Caucho" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3a3f42"/><stop offset="1" stop-color="#16191b"/></linearGradient>
<pattern id="a11Malla" width="7" height="7" patternUnits="userSpaceOnUse"><rect width="7" height="7" fill="#c9b98a"/><circle cx="2" cy="2" r="1.3" fill="#9c8b5c"/><circle cx="5.5" cy="5.5" r="1.1" fill="#a8976a"/></pattern>
<pattern id="a11Espuma" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#55594f"/><circle cx="1.5" cy="1.5" r="1" fill="#41443c"/><circle cx="4.5" cy="4" r=".8" fill="#6a6e62"/></pattern>
<filter id="a11Sombra" x="-20%" y="-20%" width="150%" height="150%"><feDropShadow dx="4" dy="7" stdDeviation="5" flood-color="#000" flood-opacity=".55"/></filter>
`;

/* ---------- tapa interior de la transmisión (1): aluminio, con la toma de aire redonda y la boca del ducto arriba ---------- */
const TR1="translate(70 30) scale(.8)";
function arteTapaInt(){
  let resaltes="";[[178,320],[200,262],[330,244],[470,236],[600,232],[730,300],[748,410],[660,500],[470,514],[240,516]].forEach(([x,y])=>{
    resaltes+=`<circle cx="${f(70+.8*x)}" cy="${f(30+.8*y)}" r="9" fill="url(#a11AlumOsc)" stroke="#2b3135" stroke-width=".8"/><circle cx="${f(70+.8*x)}" cy="${f(30+.8*y)}" r="3.5" fill="#1d2124"/>`});
  let costillas="";for(let k=0;k<8;k++){const a=k*Math.PI/4;costillas+=`<line x1="${f(BOCA[0]+14*Math.cos(a))}" y1="${f(BOCA[1]+14*Math.sin(a))}" x2="${f(BOCA[0]+54*Math.cos(a))}" y2="${f(BOCA[1]+54*Math.sin(a))}" stroke="url(#a11AlumOsc)" stroke-width="5"/>`}
  return `<g filter="url(#a11Sombra)">
    ${extruir(TAPA,6,"#3b4246",2.2,TR1)}
    <path d="${TAPA}" transform="${TR1}" fill="url(#a11Alum)" stroke="#2b3135" stroke-width="1.6"/>
    <path d="${TAPA}" transform="translate(72 32) scale(.795)" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="1.4"/>
    <path d="M220 238 Q380 214 560 212" fill="none" stroke="#fff" stroke-opacity=".4" stroke-width="3" stroke-linecap="round"/>
    <rect x="262" y="196" width="66" height="44" rx="6" fill="url(#a11AlumOsc)" stroke="#2b3135"/>
    <rect x="270" y="202" width="50" height="30" rx="4" fill="#1a1d20"/>
    <circle cx="${BOCA[0]}" cy="${BOCA[1]}" r="66" fill="url(#a11AlumOsc)" stroke="#2b3135" stroke-width="1.2"/>
    <circle cx="${BOCA[0]}" cy="${BOCA[1]}" r="58" fill="#14171a"/>
    ${costillas}
    <circle cx="${BOCA[0]}" cy="${BOCA[1]}" r="36" fill="none" stroke="url(#a11AlumOsc)" stroke-width="4"/>
    <circle cx="${BOCA[0]}" cy="${BOCA[1]}" r="14" fill="url(#a11Alum)" stroke="#2b3135"/>
    <circle cx="560" cy="340" r="78" fill="none" stroke="#fff" stroke-opacity=".12" stroke-width="10"/>
    <path d="M420 470 Q520 486 640 448" fill="none" stroke="#2b3135" stroke-opacity=".5" stroke-width="2"/>
    ${resaltes}
  </g>`;
}
/* empaque de la tapa (2): cordón de la misma silueta, detrás de la tapa */
const arteEmpaque=()=>`<g class="esq-oculto-arm"><path d="${TAPA}" transform="translate(76 26) scale(.8)" fill="none" stroke="#2a2f33" stroke-width="8"/>
  <path d="${TAPA}" transform="translate(76 26) scale(.8)" fill="none" stroke="#7c6f55" stroke-width="5"/></g>`;

/* ---------- tapa exterior (8): plástico negro, con la rejilla de entrada de aire adelante y arriba ---------- */
const TR8="translate(60 16) scale(.8)";
function arteTapaExt(){
  let rejilla="";for(let k=0;k<7;k++)rejilla+=`<path d="M${226+k*15} 232 l12 30" stroke="#0b0d0e" stroke-width="6" stroke-linecap="round"/><path d="M${226+k*15} 232 l12 30" stroke="#c9ced1" stroke-opacity=".6" stroke-width="1.4" transform="translate(-2 0)"/>`;
  return `<g filter="url(#a11Sombra)">
    ${extruir(TAPA,5,"#0c0e10",1.6,TR8)}
    <path d="${TAPA}" transform="${TR8}" fill="url(#a11Plast)" stroke="#060708" stroke-width="2.4"/>
    <path d="${TAPA}" transform="translate(62 18) scale(.795)" fill="none" stroke="#b9c2c7" stroke-opacity=".55" stroke-width="1.6"/>
    <path d="M200 300 Q205 262 250 258 L470 244 Q560 236 630 254 Q700 276 704 340 Q706 420 650 452 L250 462 Q205 462 200 430 Z" fill="none" stroke="#9aa2a7" stroke-opacity=".55" stroke-width="2"/>
    <path d="M214 234 Q330 214 520 210 Q600 210 660 228" fill="none" stroke="url(#a11Brillo)" stroke-width="10" stroke-linecap="round"/>
    <path d="M214 226 L350 214 L350 270 L222 278 Z" fill="#101214" stroke="#8d959a" stroke-opacity=".7" stroke-width="1.4"/>
    ${rejilla}
    <path d="M430 300 Q560 280 650 320" fill="none" stroke="#fff" stroke-opacity=".14" stroke-width="16" stroke-linecap="round"/>
    <path d="M300 440 L620 430" stroke="#c9ced1" stroke-opacity=".55" stroke-width="3" stroke-linecap="round"/>
    ${[[200,300],[262,252],[520,232],[690,296],[700,420],[420,466]].map(([x,y])=>`<circle cx="${x}" cy="${y}" r="5.5" fill="#8d959a" stroke="#060708"/><circle cx="${x}" cy="${y}" r="2" fill="#2a2f33"/>`).join("")}
  </g>`;
}

/* ---------- respiradero (5): tapón de caucho con su boquilla hacia arriba ---------- */
const arteRespiradero=()=>`<g filter="url(#a11Sombra)">
  <rect x="588" y="196" width="26" height="14" rx="4" fill="url(#a11Caucho)" stroke="#060708"/>
  <rect x="595" y="180" width="12" height="18" rx="3" fill="url(#a11Caucho)" stroke="#060708"/>
  <rect x="597" y="182" width="3" height="14" fill="#fff" fill-opacity=".18"/></g>`;

/* tubo de drenaje (6): sale de la boquilla del respiradero; el rectángulo invisible es su área de toque (un tubo delgado es difícil de tocar) */
const P_TUBO="M601 182 C612 166 626 158 650 152 S680 148 692 148";
const arteTubo=()=>`<g filter="url(#a11Sombra)"><path d="${P_TUBO}" fill="none" stroke="#060708" stroke-width="12" stroke-linecap="round"/>
  <path d="${P_TUBO}" fill="none" stroke="#3a3f43" stroke-width="9" stroke-linecap="round"/><path d="${P_TUBO}" fill="none" stroke="#fff" stroke-opacity=".18" stroke-width="2" transform="translate(-1 -2)"/>
  <rect x="618" y="130" width="88" height="42" rx="18" fill="#000" fill-opacity="0" pointer-events="all"/></g>`;

/* ---------- filtro de la correa (11): espuma redonda en un marco, y sus sellos ---------- */
const arteFiltroCorrea=()=>`<g class="esq-oculto-arm" filter="url(#a11Sombra)">
  <circle cx="${BOCA[0]+5}" cy="${BOCA[1]-4}" r="56" fill="#7d7150"/>
  <circle cx="${BOCA[0]}" cy="${BOCA[1]}" r="56" fill="url(#a11Malla)" stroke="#4a4232" stroke-width="2"/>
  <circle cx="${BOCA[0]}" cy="${BOCA[1]}" r="47" fill="none" stroke="#4a4232" stroke-opacity=".5" stroke-width="1.5"/>
  <path d="M${BOCA[0]-38} ${BOCA[1]-26} A46 46 0 0 1 ${BOCA[0]+20} ${BOCA[1]-44}" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="4" stroke-linecap="round"/></g>`;
/* sello de caucho (9): media luna que cierra la parte de arriba del filtro contra la tapa exterior */
const arteSelloArco=()=>`<g class="esq-oculto-arm" filter="url(#a11Sombra)">
  <path d="M${BOCA[0]-58} ${BOCA[1]-30} A66 66 0 0 1 ${BOCA[0]+58} ${BOCA[1]-30} L${BOCA[0]+48} ${BOCA[1]-24} A54 54 0 0 0 ${BOCA[0]-48} ${BOCA[1]-24} Z" fill="url(#a11Caucho)" stroke="#060708"/>
  <path d="M${BOCA[0]-50} ${BOCA[1]-34} A62 62 0 0 1 ${BOCA[0]+10} ${BOCA[1]-61}" fill="none" stroke="#fff" stroke-opacity=".2" stroke-width="2"/></g>`;
/* sello del ducto (13): caucho en U sobre la boca de arriba de la tapa interior */
const arteSelloU=()=>`<g class="esq-oculto-arm" filter="url(#a11Sombra)">
  <path d="M266 188 L266 238 M324 188 L324 238 M266 190 Q295 176 324 190" fill="none" stroke="#060708" stroke-width="9" stroke-linecap="round"/>
  <path d="M266 188 L266 238 M324 188 L324 238 M266 190 Q295 176 324 190" fill="none" stroke="#3a3f42" stroke-width="6" stroke-linecap="round"/></g>`;

/* ---------- espumas antirruido pegadas por dentro de la tapa exterior (14, 15, 20, 22) ---------- */
const arteEspumaRedonda=()=>`<g class="esq-oculto-arm" filter="url(#a11Sombra)">
  <circle cx="566" cy="334" r="48" fill="#3c3f37"/><circle cx="560" cy="338" r="48" fill="url(#a11Espuma)" stroke="#2c2e28" stroke-width="1.5"/></g>`;
const arteEspumaBloque=()=>`<g class="esq-oculto-arm" filter="url(#a11Sombra)">
  <path d="M370 250 L414 250 L424 243 L380 243 Z" fill="#6a6e62"/><path d="M414 250 L424 243 L424 280 L414 287 Z" fill="#3c3f37"/>
  <rect x="370" y="250" width="44" height="37" fill="url(#a11Espuma)" stroke="#2c2e28"/></g>`;
const arteEspumaL=()=>`<g class="esq-oculto-arm" filter="url(#a11Sombra)">
  <path d="M640 250 L668 250 L668 318 L650 318 L650 268 L640 268 Z" fill="url(#a11Espuma)" stroke="#2c2e28" stroke-width="1.5"/></g>`;
const arteEspumaCurva=()=>`<g class="esq-oculto-arm" filter="url(#a11Sombra)">
  <path d="M196 392 Q206 446 262 456 L262 470 Q194 462 182 396 Z" fill="url(#a11Espuma)" stroke="#2c2e28" stroke-width="1.5"/></g>`;

/* ---------- «Cómo funciona»: la caja de la correa en corte (izquierda); termómetro, flujo, la espuma del filtro de cerca
   y el tubo de drenaje (derecha) ----------
   Izquierda (x 0-470): aire que entra por la rejilla de la tapa exterior, pasa por la espuma del filtro, lo chupan las aletas
   del variador, recorre la correa y el clutch y sale por atrás; abajo atrás, el tubo de drenaje.
   Derecha (#fn11-der): °C de la correa (aprox.), % de aire, la espuma cortada con el polvo y el tubo con agua.
   En el celular la columna derecha baja debajo del corte. */
const VAR=[130,230], CLU=[370,230];
let aletas11="";for(let k=0;k<12;k++)aletas11+=`<path d="M-5 -40 L5 -40 L9 -66 L-1 -66 Z" transform="rotate(${k*30})" fill="url(#fn11Alum)" stroke="#2a2f33"/>`;
const FLUJO11="M95,52 L95,138 Q95,176 124,206 M196,196 Q260,150 340,160 L466,138";
const FN_SVG=`<svg id="fn" viewBox="0 0 900 440" role="img" aria-labelledby="fnTit">
  <title id="fnTit">Esquema de la caja de la correa en corte: el aire entra por la rejilla, pasa por el filtro de espuma, las aletas del variador lo chupan, enfría la correa y el clutch y sale por atrás; a la derecha, la temperatura de la correa, el flujo de aire, la espuma de cerca y el tubo de drenaje</title>
  <style>
    @keyframes esq11fluye{to{stroke-dashoffset:-36}}
    @keyframes esq11gira{to{transform:rotate(360deg)}}
    @keyframes esq11cae{0%{transform:translateY(0);opacity:0}20%{opacity:1}100%{transform:translateY(34px);opacity:0}}
    .esq-fn11-flujo{stroke-dasharray:12 24;animation:esq11fluye .9s linear infinite;transition:opacity .5s,stroke-width .6s}
    #fn11-aletas{transform-origin:${VAR[0]}px ${VAR[1]}px;animation:esq11gira .6s linear infinite}
    #fn11-zap{transform-origin:${CLU[0]}px ${CLU[1]}px;animation:esq11gira 1s linear infinite}
    #fn11-correa{transition:stroke .8s}
    #fn11-mercurio{transition:transform .9s cubic-bezier(.5,0,.3,1);transform-box:fill-box;transform-origin:bottom}
    .esq-fn11-barra{transition:width .8s}
    #fn11-calor,#fn11-agua,#fn11-aguaT,.esq-fn11-polvo,#fn11-pasa,#fn11-aceite{transition:opacity .6s}
    .esq-fn11-gota{animation:esq11cae 1s linear infinite}
    @media(max-width:700px){#fn11-der{transform:translate(-480px,430px)}}
    @media(prefers-reduced-motion:reduce){.esq-fn11-flujo,#fn11-aletas,#fn11-zap,.esq-fn11-gota{animation:none!important}}
  </style>
  <defs>
    <linearGradient id="fn11Alum" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d9dde0"/><stop offset=".45" stop-color="#9aa2a7"/><stop offset=".7" stop-color="#c3c9cc"/><stop offset="1" stop-color="#5f676c"/></linearGradient>
    <linearGradient id="fn11AlumOsc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8d959a"/><stop offset="1" stop-color="#3b4246"/></linearGradient>
    <linearGradient id="fn11Plast" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6a7177"/><stop offset=".45" stop-color="#3a4045"/><stop offset="1" stop-color="#1c1f22"/></linearGradient>
    <linearGradient id="fn11Corte" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2125"/><stop offset="1" stop-color="#101417"/></linearGradient>
    <radialGradient id="fn11Calor" cx=".5" cy=".5" r=".6"><stop offset="0" stop-color="#ff5a2a" stop-opacity=".6"/><stop offset="1" stop-color="#ff5a2a" stop-opacity="0"/></radialGradient>
    <pattern id="fn11Espuma" width="14" height="12" patternUnits="userSpaceOnUse"><rect width="14" height="12" fill="#c98a3a"/><circle cx="4" cy="4" r="2.6" fill="#7a4f1c"/><circle cx="11" cy="9" r="2" fill="#7a4f1c"/><circle cx="11" cy="2" r="1.2" fill="#8f5e22"/></pattern>
  </defs>
  <text class="esq-fn-et esq-claro" x="14" y="30">La caja de la correa, en corte</text>
  <!-- tapa interior (caja) cortada -->
  <path d="M30,140 Q30,72 100,72 L400,82 Q460,86 460,150 L460,320 Q460,366 400,366 L90,366 Q30,366 30,310 Z" fill="url(#fn11AlumOsc)" stroke="#5a6266" stroke-width="2"/>
  <path d="M42,144 Q42,84 102,84 L398,94 Q448,98 448,152 L448,318 Q448,354 400,354 L92,354 Q42,354 42,308 Z" fill="url(#fn11Corte)"/>
  <ellipse id="fn11-calor" cx="250" cy="230" rx="220" ry="110" fill="url(#fn11Calor)" opacity="0"/>
  <!-- tapa exterior con la rejilla y el filtro de espuma cortado -->
  <rect x="44" y="70" width="104" height="18" rx="4" fill="url(#fn11Plast)" stroke="#6a7177"/>
  ${[0,1,2,3,4,5,6].map(i=>`<rect x="${52+i*13}" y="74" width="7" height="10" rx="2" fill="#0d0f10"/>`).join("")}
  <rect x="50" y="94" width="92" height="36" rx="6" fill="url(#fn11Espuma)" stroke="#7a4f1c"/>
  <g class="esq-fn11-polvo" id="fn11-polvoA" opacity="0">${Array.from({length:10},(_,i)=>`<circle cx="${56+i*9}" cy="${96+(i%3)*3}" r="2.3" fill="#5a4630"/>`).join("")}</g>
  <text class="esq-fn-et" x="160" y="62">Entra aire</text>
  <text class="esq-fn-et" x="160" y="118">Filtro</text>
  <!-- variador con sus aletas, correa y clutch -->
  <circle cx="${VAR[0]}" cy="${VAR[1]}" r="58" fill="url(#fn11Alum)" stroke="#2a2f33"/>
  <g id="fn11-aletas">${`<g transform="translate(${VAR[0]} ${VAR[1]})">${aletas11}</g>`}<circle cx="${VAR[0]}" cy="${VAR[1]}" r="30" fill="url(#fn11AlumOsc)"/><rect x="${VAR[0]-3}" y="${VAR[1]-28}" width="6" height="18" fill="#2a2f33"/></g>
  <circle cx="${VAR[0]}" cy="${VAR[1]}" r="9" fill="#9aa3a8"/>
  <path id="fn11-correa" d="M130,170 L370,176 A54 54 0 0 1 370,284 L130,290 A60 60 0 0 1 130,170 Z" fill="none" stroke="#141414" stroke-width="10" stroke-linejoin="round"/>
  <circle cx="${CLU[0]}" cy="${CLU[1]}" r="50" fill="url(#fn11AlumOsc)" stroke="#2a2f33"/>
  <g id="fn11-zap"><circle cx="${CLU[0]}" cy="${CLU[1]}" r="40" fill="none" stroke="#59646a" stroke-width="6" stroke-dasharray="20 10"/><circle cx="${CLU[0]}" cy="${CLU[1]}" r="18" fill="url(#fn11Alum)"/></g>
  <circle cx="${CLU[0]}" cy="${CLU[1]}" r="7" fill="#9aa3a8"/>
  <!-- flujo de aire -->
  <path class="esq-fn11-flujo" id="fn11-flujo" d="${FLUJO11}" fill="none" stroke="#7fd3ff" stroke-width="6" stroke-linecap="round" opacity="0"/>
  <text class="esq-fn-et" x="214" y="154">Correa</text>
  <text class="esq-fn-et" x="400" y="124">Sale</text>
  <text class="esq-fn-et" x="56" y="334">Variador</text>
  <text class="esq-fn-et" x="330" y="334">Clutch</text>
  <!-- tubo de drenaje -->
  <path d="M400,354 L400,404" stroke="#1d1d1d" stroke-width="12" stroke-linecap="round"/>
  <g id="fn11-agua" opacity="0"><rect x="52" y="340" width="370" height="12" rx="4" fill="#4aa3d8" opacity=".6"/><circle class="esq-fn11-gota" cx="400" cy="404" r="5" fill="#7fd3ff"/></g>
  <text class="esq-fn-et" x="390" y="424" text-anchor="end">Drenaje</text>
  <g id="fn11-der">
    <!-- termómetro de la correa y flujo de aire -->
    <rect x="490" y="12" width="400" height="190" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="38">Lo que pasa adentro</text>
    <rect x="522" y="54" width="18" height="110" rx="9" fill="#2b3135"/>
    <circle cx="531" cy="172" r="16" fill="#f2611d"/>
    <rect id="fn11-mercurio" x="526" y="58" width="10" height="110" rx="5" fill="#f2611d"/>
    <text class="esq-fn-et esq-claro" id="fn11-temp" x="560" y="110">aprox. 25 °C</text>
    <text class="esq-fn-et" x="560" y="136">Correa</text>
    <text class="esq-fn-et" id="fn11-taire" x="704" y="80">Aire 0 %</text>
    <rect x="704" y="88" width="172" height="10" rx="5" fill="#2b3135"/>
    <rect class="esq-fn11-barra" id="fn11-baire" x="704" y="88" width="0" height="10" rx="5" fill="#7fd3ff"/>
    <text class="esq-fn-et esq-claro" id="fn11-estado" x="704" y="150">Quieta</text>
    <!-- la espuma del filtro cortada, de cerca, y el tubo de drenaje -->
    <rect x="490" y="214" width="400" height="218" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="238">El filtro, de cerca</text>
    <rect x="560" y="254" width="96" height="146" rx="6" fill="url(#fn11Espuma)" stroke="#7a4f1c" stroke-width="2"/>
    <rect id="fn11-aceite" x="560" y="254" width="96" height="146" rx="6" fill="#ffd27a" opacity=".18"/>
    <g id="fn11-pasa" opacity="0">${[278,312,346,380].map(y=>`<path class="esq-fn11-flujo" d="M506,${y} L716,${y}" stroke="#7fd3ff" stroke-width="4" fill="none" stroke-linecap="round"/>`).join("")}</g>
    <g class="esq-fn11-polvo" id="fn11-polvo1" opacity="0">${Array.from({length:12},(_,i)=>`<circle cx="${560+(i%3)*7}" cy="${262+i*11}" r="3" fill="#5a4630"/>`).join("")}</g>
    <g class="esq-fn11-polvo" id="fn11-polvo2" opacity="0">${Array.from({length:30},(_,i)=>`<circle cx="${562+(i*13)%60}" cy="${258+(i*29)%138}" r="${3+(i%3)}" fill="#3e301f"/>`).join("")}</g>
    <text class="esq-fn-et" x="520" y="424">Espuma con aceite</text>
    <rect x="770" y="250" width="34" height="140" rx="14" fill="#1d1d1d" stroke="#3a3f42"/>
    <rect id="fn11-aguaT" x="776" y="320" width="22" height="64" rx="10" fill="#4aa3d8" opacity="0"/>
    <text class="esq-fn-et" x="764" y="424">Tubo</text>
    <text class="esq-fn-et esq-claro" id="fn11-tubo" x="814" y="312" data-xm="812">Seco</text>
  </g>
</svg>`;
function fnAplicar(s,$){
  const on=!!s.gira, a=s.aire||0;
  // variador y clutch giran con el motor
  ["fn11-aletas","fn11-zap"].forEach(id=>$(id).style.animationPlayState=on?"running":"paused");
  const fl=$("fn11-flujo");fl.style.opacity=a?Math.min(1,.3+a):0;fl.style.strokeWidth=2+8*a;
  $("fn11-pasa").style.opacity=a?Math.min(1,.2+a):0;
  // temperatura de la correa (escala 20 a 120 °C)
  $("fn11-mercurio").style.transform=`scaleY(${Math.max(.05,((s.temp||25)-20)/100)})`;
  $("fn11-temp").textContent="aprox. "+(s.temp||25)+" °C";
  $("fn11-correa").setAttribute("stroke",s.calor?"#9c2f14":"#141414");$("fn11-calor").style.opacity=s.calor?1:0;
  $("fn11-baire").setAttribute("width",Math.round(172*a));$("fn11-taire").textContent="Aire "+Math.round(100*a)+" %";
  $("fn11-estado").textContent=s.estado||"Quieta";
  // filtro: polvo pegado a la espuma aceitada
  $("fn11-polvoA").style.opacity=s.sucio?1:0;$("fn11-polvo1").style.opacity=s.polvo||s.sucio?1:0;$("fn11-polvo2").style.opacity=s.sucio?1:0;
  $("fn11-aceite").style.opacity=s.seco?0:.18;
  // agua en la caja y en el tubo de drenaje
  $("fn11-agua").style.opacity=s.agua?1:0;$("fn11-aguaT").style.opacity=s.agua?.85:0;$("fn11-tubo").textContent=s.agua?"Con agua":"Seco";
}
return {defs:DEFS,arteEmpaque,arteEspumaBloque,arteEspumaCurva,arteEspumaL,arteEspumaRedonda,arteFiltroCorrea,arteRespiradero,arteSelloArco,arteSelloU,arteTapaExt,arteTapaInt,arteTubo,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
