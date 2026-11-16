/* Arte de la lámina 8 de la NMAX 155 (admisión y filtro de aire): dibujos propios de TallerYa.
   Vista desde el lado izquierdo de la moto: a la derecha, la caja del filtro con su tapa; al centro, la unión de caucho y el
   cuerpo de aceleración; a la izquierda, el múltiple con el inyector, que baja a la culata.
   La caja, la tapa, mangueras, abrazaderas, empaques y tornillería salen de piezas-comunes.js; aquí va solo lo propio. */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["nmax-fig8"]=(function(){
"use strict";
const f=n=>Math.round(n*10)/10;
const ATRAS=[5,-8];
function extruir(d,pasos,fill,k=1){let r="";for(let i=pasos;i>=1;i--)r+=`<path d="${d}" transform="translate(${f(ATRAS[0]*i*k/pasos)} ${f(ATRAS[1]*i*k/pasos)})" fill="${fill}"/>`;return r}

const DEFS=`
<linearGradient id="a8Alum" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#eef0f1"/><stop offset=".4" stop-color="#a9b0b4"/><stop offset=".6" stop-color="#d7dbde"/><stop offset="1" stop-color="#6e767b"/></linearGradient>
<linearGradient id="a8AlumOsc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#a3abb0"/><stop offset=".5" stop-color="#6c7479"/><stop offset="1" stop-color="#3b4246"/></linearGradient>
<linearGradient id="a8Acero" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef0f1"/><stop offset=".5" stop-color="#a7aeb2"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
<linearGradient id="a8Caja" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4a5055"/><stop offset=".5" stop-color="#2a2f33"/><stop offset="1" stop-color="#16191b"/></linearGradient>
<linearGradient id="a8Tapa" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3f454a"/><stop offset=".6" stop-color="#23272a"/><stop offset="1" stop-color="#121416"/></linearGradient>
<linearGradient id="a8Plast" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3a3f43"/><stop offset="1" stop-color="#0f1113"/></linearGradient>
<linearGradient id="a8Papel" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e9d9a8"/><stop offset=".5" stop-color="#d2bd84"/><stop offset="1" stop-color="#b59f63"/></linearGradient>
<pattern id="a8Pliegue" width="9" height="10" patternUnits="userSpaceOnUse"><rect width="9" height="10" fill="url(#a8Papel)"/><path d="M0 0 V10 M4.5 0 V10" stroke="#8e7a45" stroke-width="1.1"/><path d="M2 0 V10" stroke="#fff6d6" stroke-opacity=".5"/></pattern>
<filter id="a8Sombra" x="-20%" y="-20%" width="150%" height="150%"><feDropShadow dx="4" dy="7" stdDeviation="5" flood-color="#000" flood-opacity=".55"/></filter>
`;

/* ---------- contexto: culata (otra lámina) ---------- */
const arteCulata=()=>`<g class="esq-ctx esq-ctx-culata" pointer-events="none">
  <path d="M60,262 L230,262 L230,350 L60,350 Z" fill="#b9c2c7" fill-opacity=".05" stroke="#c9bfa7" stroke-opacity=".5" stroke-width="1.6" stroke-dasharray="7 5"/>
  <text class="esq-ctx-txt" x="70" y="370">Culata (lámina 3)</text></g>`;

/* múltiple de admisión (1): codo de aluminio de la culata al cuerpo de aceleración */
const P_MUL="M150,246 C150,205 180,190 238,190";
const arteMultiple=()=>`<g filter="url(#a8Sombra)">
  <path d="${P_MUL}" transform="translate(4 -6)" fill="none" stroke="#3b4246" stroke-width="34"/>
  <path d="${P_MUL}" fill="none" stroke="#2a2f33" stroke-width="36"/><path d="${P_MUL}" fill="none" stroke="url(#a8Alum)" stroke-width="30"/>
  <path d="M138,232 C140,206 168,186 230,182" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="2"/>
  <rect x="116" y="240" width="68" height="12" rx="3" fill="url(#a8AlumOsc)" stroke="#2a2f33"/>
  <rect x="236" y="158" width="12" height="64" rx="3" fill="url(#a8AlumOsc)" stroke="#2a2f33"/>
  <ellipse cx="186" cy="196" rx="12" ry="6" fill="#6c7479" stroke="#2a2f33"/></g>`;
/* inyector (5): cuerpo con el conector eléctrico de lado y la punta hacia el múltiple */
const arteInyector=()=>`<g filter="url(#a8Sombra)">
  <rect x="179" y="128" width="14" height="58" rx="4" fill="url(#a8Acero)" stroke="#3a4144"/>
  <rect x="176" y="146" width="20" height="22" rx="3" fill="#1a1d20" stroke="#3b4246"/>
  <rect x="194" y="150" width="16" height="12" rx="2" fill="#26292c" stroke="#3b4246"/><rect x="206" y="152" width="4" height="8" fill="#7a2a20"/>
  <path d="M181,186 L191,186 L188,200 L184,200 Z" fill="#8a9297"/></g>`;
/* unión del tubo de combustible (4, el conjunto del inyector): el acople negro donde entra el tubo */
const arteUnion4=()=>`<g filter="url(#a8Sombra)"><rect x="175" y="112" width="22" height="18" rx="5" fill="url(#a8Plast)" stroke="#3b4246"/>
  <rect x="179" y="116" width="14" height="4" rx="2" fill="#5a6064"/></g>`;
/* cuerpo de aceleración (12): cuerpo de aluminio con la polea del cable y el sensor de la mariposa */
const arteCuerpo=()=>`<g filter="url(#a8Sombra)">${extruir("M258,162 L348,162 Q358,162 358,172 L358,214 Q358,224 348,224 L258,224 Z",4,"#3b4246",.8)}
  <path d="M258,162 L348,162 Q358,162 358,172 L358,214 Q358,224 348,224 L258,224 Z" fill="url(#a8Alum)" stroke="#40474c"/>
  <rect x="252" y="160" width="10" height="68" rx="3" fill="url(#a8AlumOsc)" stroke="#2a2f33"/>
  <circle cx="296" cy="200" r="19" fill="url(#a8AlumOsc)" stroke="#2a2f33"/><circle cx="296" cy="200" r="13" fill="none" stroke="#1b1f22" stroke-width="3"/>
  <circle cx="296" cy="200" r="4" fill="#2a2f33"/><path d="M296,181 L318,176" stroke="#111" stroke-width="2.4"/>
  <rect x="326" y="186" width="24" height="30" rx="4" fill="#1a1d20" stroke="#3b4246"/><rect x="331" y="191" width="14" height="6" rx="2" fill="#3a3f43"/>
  <path d="M262,168 H350" stroke="#fff" stroke-opacity=".5" stroke-width="1.4"/></g>`;
/* motor de ralentí (16): motor paso a paso con su conector, encima del cuerpo */
const arteMotorRalenti=()=>`<g filter="url(#a8Sombra)">
  <rect x="284" y="136" width="34" height="26" rx="5" fill="url(#a8Plast)" stroke="#3b4246"/>
  <rect x="280" y="156" width="42" height="7" rx="2" fill="url(#a8AlumOsc)" stroke="#2a2f33"/>
  <rect x="318" y="140" width="10" height="14" rx="2" fill="#26292c" stroke="#3b4246"/>
  <path d="M288,140 H312" stroke="#fff" stroke-opacity=".25"/></g>`;
/* filtro (23): panel de papel plegado con marco de caucho; adentro de la caja, solo se ve desarmado */
const arteFiltro=()=>`<g class="esq-oculto-arm" filter="url(#a8Sombra)">
  <rect x="520" y="322" width="260" height="78" rx="10" fill="#1d1d1d" stroke="#050505"/>
  <rect x="532" y="330" width="236" height="62" rx="4" fill="url(#a8Pliegue)"/>
  <rect x="532" y="330" width="236" height="62" rx="4" fill="none" stroke="#000" stroke-opacity=".35"/></g>`;
/* sellos de la caja (24, dos): marcos de caucho que cierran el filtro contra la caja y contra la tapa */
const sello=dy=>`<rect x="505" y="${312+dy}" width="290" height="98" rx="16" fill="none" stroke="#050505" stroke-width="7"/>
  <rect x="505" y="${312+dy}" width="290" height="98" rx="16" fill="none" stroke="#2c2c2c" stroke-width="4"/>`;
const arteSellos=()=>`<g class="esq-oculto-arm">${sello(-10)}${sello(10)}</g>`;

/* ---------- «Cómo funciona»: el camino del aire en corte (izquierda) y lo que mide el computador (derecha) ----------
   Izquierda (x 0-470): caja con el filtro plisado, unión, cuerpo de aceleración cortado con la mariposa y el motor de
   ralentí, múltiple con el inyector rociando su cono, válvula de admisión y cilindro.
   Derecha (#fn8-der): tacómetro y barras de acelerador, aire y gasolina; abajo, la mariposa y el filtro de frente.
   En el celular la columna derecha baja debajo del corte. */
const FLUJO_A="M34,334 C34,300 40,280 56,262 C70,246 70,214 92,196 L300,190 L356,190";
const FLUJO_M="M356,190 L362,190 C392,190 405,214 405,240 L405,318";
const FN_SVG=`<svg id="fn" viewBox="0 0 900 440" role="img" aria-labelledby="fnTit">
  <title id="fnTit">Esquema de la admisión en corte: el aire pasa por el filtro plisado y la mariposa, el inyector rocía la gasolina y la mezcla entra al cilindro; a la derecha, las rpm y los porcentajes de acelerador, aire y gasolina</title>
  <style>
    @keyframes esq8fluye{to{stroke-dashoffset:-36}}
    @keyframes esq8valv{0%,100%{transform:translateY(0)}50%{transform:translateY(12px)}}
    @keyframes esq8pist{0%,100%{transform:translateY(0)}50%{transform:translateY(26px)}}
    @keyframes esq8rocio{0%,100%{opacity:.35}50%{opacity:1}}
    .esq-fn8-flujo{stroke-dasharray:14 22;animation:esq8fluye 1s linear infinite;transition:opacity .5s,stroke-width .6s,stroke .5s}
    #fn8-mariposa{transition:transform .8s cubic-bezier(.5,0,.3,1);transform-origin:252px 190px}
    #fn8-aguja{transition:transform .8s cubic-bezier(.5,0,.3,1);transform-origin:570px 130px}
    #fn8-valv{animation:esq8valv 1s ease-in-out infinite}
    #fn8-piston{animation:esq8pist 1s ease-in-out infinite}
    #fn8-cono{transform-origin:358px 172px;transition:transform .6s;animation:esq8rocio .5s ease-in-out infinite}
    #fn8-cono-c{transition:opacity .5s}
    .esq-fn8-barra,#fn8-disco{transition:width .8s cubic-bezier(.5,0,.3,1),ry .8s cubic-bezier(.5,0,.3,1)}
    #fn8-bypass,.esq-fn8-polvo,#fn8-capa,#fn8-sucio,#fn8-mezcla,#fn8-plunger{transition:opacity .6s,transform .6s}
    @media(max-width:700px){#fn8-der{transform:translate(-480px,400px)}}
    @media(prefers-reduced-motion:reduce){#fn8-valv,#fn8-piston,#fn8-cono,.esq-fn8-flujo{animation:none!important}}
  </style>
  <defs>
    <linearGradient id="fn8Acero" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef0f1"/><stop offset=".5" stop-color="#a7aeb2"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
    <linearGradient id="fn8Alum" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#eef0f1"/><stop offset=".4" stop-color="#a9b0b4"/><stop offset=".6" stop-color="#d7dbde"/><stop offset="1" stop-color="#6e767b"/></linearGradient>
    <linearGradient id="fn8AlumOsc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#a3abb0"/><stop offset=".5" stop-color="#6c7479"/><stop offset="1" stop-color="#3b4246"/></linearGradient>
    <linearGradient id="fn8Caja" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4a5055"/><stop offset=".5" stop-color="#2a2f33"/><stop offset="1" stop-color="#16191b"/></linearGradient>
    <radialGradient id="fn8Rocio" cx=".5" cy="0" r="1"><stop offset="0" stop-color="#fff1b0"/><stop offset=".55" stop-color="#e8c34a" stop-opacity=".8"/><stop offset="1" stop-color="#e8c34a" stop-opacity="0"/></radialGradient>
    <linearGradient id="fn8Iny" x1="0" x2="1"><stop offset="0" stop-color="#1c1f22"/><stop offset=".45" stop-color="#4a5257"/><stop offset="1" stop-color="#1c1f22"/></linearGradient>
    <linearGradient id="fn8Corte" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2125"/><stop offset="1" stop-color="#101417"/></linearGradient>
    <linearGradient id="fn8Piston" x1="0" x2="1"><stop offset="0" stop-color="#6c7479"/><stop offset=".5" stop-color="#c9ced1"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
  </defs>
  <text class="esq-fn-et esq-claro" x="14" y="30">El camino del aire, en corte</text>
  <!-- ducto de entrada y caja del filtro cortada, con el elemento plisado -->
  <path d="M14,350 L54,350 L54,286 L14,286 Z" fill="#26292c" stroke="#45494d"/>
  <text class="esq-fn-et" x="12" y="376">Entra aire</text>
  <rect x="20" y="96" width="150" height="196" rx="16" fill="url(#fn8Caja)" stroke="#5a6266" stroke-width="2"/>
  <rect x="30" y="106" width="130" height="176" rx="10" fill="url(#fn8Corte)"/>
  <rect x="86" y="108" width="30" height="172" fill="#3b3424"/>
  <polyline points="${Array.from({length:22},(_,i)=>(i%2?112:90)+","+(110+i*8)).join(" ")}" fill="none" stroke="#e3cf93" stroke-width="3" stroke-linejoin="round"/>
  <rect id="fn8-capa" x="84" y="108" width="12" height="172" fill="#5b4a32" opacity="0"/>
  <g class="esq-fn8-polvo" opacity="0">${Array.from({length:14},(_,i)=>`<circle cx="${44+(i*17)%38}" cy="${122+i*11}" r="${2+(i%3)*.6}" fill="#a07f52"/>`).join("")}</g>
  <text class="esq-fn-et" x="22" y="86">Filtro plisado</text>
  <!-- unión de caucho (corrugada) -->
  <rect x="170" y="166" width="36" height="48" rx="6" fill="#1d1d1d" stroke="#3a3a3a"/>
  ${[176,184,192,200].map(x=>`<line x1="${x}" y1="168" x2="${x}" y2="212" stroke="#333"/>`).join("")}
  <!-- cuerpo de aceleración cortado: conducto, mariposa, paso de ralentí y su motor -->
  <rect x="206" y="136" width="96" height="108" rx="8" fill="url(#fn8Alum)" stroke="#40474c"/>
  <rect x="206" y="170" width="96" height="40" fill="url(#fn8Corte)"/>
  <path d="M216,170 L216,152 L290,152 L290,170" fill="none" stroke="#101417" stroke-width="8"/>
  <path id="fn8-bypass" d="M216,170 L216,152 L290,152 L290,170" fill="none" stroke="#7fd3ff" stroke-width="4" stroke-dasharray="5 5" opacity="0"/>
  <rect x="240" y="114" width="26" height="24" rx="3" fill="#1a1d20" stroke="#59646a"/>
  <rect id="fn8-plunger" x="249" y="138" width="8" height="12" fill="#9aa3a8"/>
  <text class="esq-fn-et" x="196" y="106">Motor de ralentí</text>
  <g id="fn8-mariposa"><rect x="249" y="171" width="6" height="38" rx="2" fill="#d9dee1" stroke="#40474c"/></g>
  <circle cx="252" cy="190" r="4" fill="#59646a"/>
  <text class="esq-fn-et" x="208" y="268">Mariposa</text>
  <!-- múltiple que baja a la culata -->
  <path d="M302,170 L362,170 C404,170 425,198 425,240 L425,272 L385,272 L385,242 C385,222 376,210 362,210 L302,210 Z" fill="url(#fn8AlumOsc)" stroke="#2a2f33"/>
  <path d="M302,176 L362,176 C398,176 419,200 419,240 L419,272 L391,272 L391,242 C391,218 378,204 362,204 L302,204 Z" fill="url(#fn8Corte)"/>
  <!-- inyector: conector con su traba, cuerpo, o-ring y punta, rociando un cono -->
  <rect x="344" y="98" width="28" height="18" rx="3" fill="#2a2f33" stroke="#59646a"/>
  <rect x="368" y="102" width="8" height="10" rx="2" fill="#59646a"/>
  <rect x="350" y="116" width="16" height="40" rx="4" fill="url(#fn8Iny)" stroke="#59646a"/>
  <rect x="348" y="146" width="20" height="5" rx="2" fill="#0d0f10"/>
  <path d="M352,156 L364,156 L361,172 L355,172 Z" fill="url(#fn8Acero)" stroke="#3a4144"/>
  <g id="fn8-cono-c" opacity="0"><path id="fn8-cono" d="M358,174 L340,204 Q358,210 376,204 Z" fill="url(#fn8Rocio)"/></g>
  <text class="esq-fn-et" x="382" y="112">Inyector</text>
  <!-- flujo: aire (azul) y mezcla (amarillo) -->
  <path class="esq-fn8-flujo" id="fn8-aire" d="${FLUJO_A}" fill="none" stroke="#7fd3ff" stroke-width="6" stroke-linecap="round" opacity="0"/>
  <path class="esq-fn8-flujo" id="fn8-mez" d="${FLUJO_M}" fill="none" stroke="#e8c34a" stroke-width="6" stroke-linecap="round" opacity="0"/>
  <!-- culata con la válvula de admisión y el cilindro cortado con el pistón -->
  <rect x="352" y="272" width="110" height="30" rx="4" fill="url(#fn8AlumOsc)" stroke="#2a2f33"/>
  <rect x="385" y="272" width="40" height="30" fill="url(#fn8Corte)"/>
  <rect x="360" y="302" width="94" height="104" fill="url(#fn8Corte)" stroke="#45494d" stroke-width="2"/>
  <rect id="fn8-mezcla" x="362" y="304" width="90" height="46" fill="#e8c34a" opacity="0"/>
  <g id="fn8-valv"><rect x="402" y="258" width="6" height="40" fill="#9aa3a8"/><path d="M388,302 L422,302 L412,296 L398,296 Z" fill="#c9ced1" stroke="#40474c"/></g>
  <g id="fn8-piston"><rect x="364" y="352" width="86" height="36" rx="3" fill="url(#fn8Piston)" stroke="#40474c"/><line x1="364" y1="360" x2="450" y2="360" stroke="#40474c"/><line x1="364" y1="366" x2="450" y2="366" stroke="#40474c"/></g>
  <text class="esq-fn-et" x="346" y="300" text-anchor="end">Válvula</text>
  <text class="esq-fn-et" x="346" y="340" text-anchor="end">Cilindro</text>
  <text class="esq-fn-et" x="346" y="380" text-anchor="end">Pistón</text>
  <g id="fn8-der">
    <!-- lo que mide el computador: rpm, acelerador, aire y gasolina -->
    <rect x="490" y="12" width="400" height="188" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="38">Lo que mide el computador</text>
    <path d="M520 130 A50 50 0 0 1 620 130" fill="none" stroke="#2b3135" stroke-width="11"/>
    <path d="M605 95 A50 50 0 0 1 620 130" fill="none" stroke="#f2611d" stroke-width="11" opacity=".75"/>
    <g id="fn8-aguja"><line x1="570" y1="130" x2="570" y2="88" stroke="#f2e6c8" stroke-width="4" stroke-linecap="round"/></g>
    <circle cx="570" cy="130" r="6" fill="#9aa3a8"/>
    <text class="esq-fn-et esq-claro" id="fn8-rpm" x="570" y="168" text-anchor="middle">0 rpm</text>
    ${[["acel","Acelerador","#f2611d",68],["airep","Aire","#7fd3ff",118],["gasp","Gasolina","#e8c34a",168]].map(([k,n,c,y])=>
      `<text class="esq-fn-et" id="fn8-t-${k}" x="650" y="${y}">${n} 0 %</text><rect x="650" y="${y+6}" width="226" height="10" rx="5" fill="#2b3135"/><rect class="esq-fn8-barra" id="fn8-b-${k}" x="650" y="${y+6}" width="0" height="10" rx="5" fill="${c}"/>`).join("")}
    <!-- de frente: la mariposa en su conducto y el filtro -->
    <rect x="490" y="212" width="400" height="220" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="238">De frente</text>
    <circle cx="590" cy="324" r="74" fill="url(#fn8Alum)" stroke="#40474c"/>
    <circle cx="590" cy="324" r="62" fill="#7fd3ff" opacity=".45"/>
    <ellipse id="fn8-disco" cx="590" cy="324" rx="61" ry="61" fill="#c9ced1" stroke="#40474c" stroke-width="2"/>
    <line x1="520" y1="324" x2="660" y2="324" stroke="#59646a" stroke-width="5"/>
    <text class="esq-fn-et" id="fn8-mtxt" x="590" y="424" text-anchor="middle">Cerrada</text>
    <rect x="702" y="252" width="160" height="146" rx="6" fill="#2a2f33" stroke="#59646a"/>
    <rect x="710" y="260" width="144" height="130" fill="#e3cf93"/>
    ${Array.from({length:14},(_,i)=>`<line x1="${716+i*10}" y1="260" x2="${716+i*10}" y2="390" stroke="#a8955c" stroke-width="2"/>`).join("")}
    <rect id="fn8-sucio" x="710" y="260" width="144" height="130" fill="#5b4a32" opacity="0"/>
    <text class="esq-fn-et" id="fn8-ftxt" x="782" y="424" text-anchor="middle">Filtro limpio</text>
  </g>
</svg>`;
function fnAplicar(s,$){
  const q=sel=>document.querySelector("#fn "+sel), on=s.rpm>0, pct=v=>Math.round(100*(v||0));
  // flujo: grosor según el aire que entra; la mezcla amarilla solo si el inyector rocía
  const a=$("fn8-aire");a.style.opacity=on?Math.min(1,.3+s.aire):0;a.style.strokeWidth=3+9*(s.aire||0);
  const m=$("fn8-mez");m.style.opacity=on?Math.min(1,.3+s.aire):0;m.style.strokeWidth=3+9*(s.aire||0);
  // mariposa: cerrada casi vertical (6°), a fondo casi horizontal; de frente el disco se angosta
  const ang=6+78*(s.acel||0);$("fn8-mariposa").style.transform=`rotate(${-ang}deg)`;
  $("fn8-disco").setAttribute("ry",Math.max(5,Math.round(61*Math.cos(ang*Math.PI/180))));
  $("fn8-mtxt").textContent=s.acel?`Abierta ${pct(s.acel)} %`:"Cerrada";
  // ralentí: el motor de ralentí retira su vástago y abre el paso chico
  $("fn8-bypass").style.opacity=s.ralenti?1:0;$("fn8-plunger").style.transform=s.ralenti?"translateY(-8px)":"none";
  // inyector: el cono crece con la gasolina
  $("fn8-cono-c").style.opacity=s.inyecta?1:0;$("fn8-cono").style.transform=`scale(${.55+.5*(s.gas||0)})`;
  $("fn8-mezcla").style.opacity=s.inyecta?(.2+.6*(s.gas||0)):0;
  // filtro: polvo atrapado y capa de mugre
  q(".esq-fn8-polvo").style.opacity=s.polvo?1:0;$("fn8-capa").style.opacity=s.sucio||0;$("fn8-sucio").style.opacity=.85*(s.sucio||0);
  $("fn8-ftxt").textContent=s.sucio>.6?"Filtro tapado":s.sucio>0?"Filtro con polvo":"Filtro limpio";
  // tablero
  $("fn8-aguja").style.transform=`rotate(${(-90+180*Math.min(1,s.rpm/10000)).toFixed(1)}deg)`;
  $("fn8-rpm").textContent=s.rpm.toLocaleString("es-CO")+" rpm";
  [["acel",s.acel],["airep",s.aire],["gasp",s.gas]].forEach(([k,v])=>{$("fn8-b-"+k).setAttribute("width",Math.round(226*(v||0)));
    $("fn8-t-"+k).textContent=({acel:"Acelerador",airep:"Aire",gasp:"Gasolina"})[k]+" "+pct(v)+" %"});
  // válvula y pistón: suben y bajan más rápido con más rpm; quietos con la moto apagada
  const dur=on?(1.6*1600/Math.max(1600,s.rpm)).toFixed(2)+"s":"1s";
  ["fn8-valv","fn8-piston"].forEach(id=>{const e=$(id);e.style.animationDuration=dur;e.style.animationPlayState=on?"running":"paused"});
}
return {defs:DEFS,arteCuerpo,arteCulata,arteFiltro,arteInyector,arteMotorRalenti,arteMultiple,arteSellos,arteUnion4,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
