/* Arte de la lámina 7 de la NMAX 155 (bomba de aceite y drenaje): dibujos propios de TallerYa.
   Vista desde abajo y a la izquierda del cárter: a la derecha, la bomba de aceite con su piñón, atornillada por dentro del
   cárter; abajo a la izquierda, el tapón de drenaje B con el tamiz, el resorte y la junta tórica, en el eje vertical del
   orificio. Tornillos, resorte y junta tórica salen de piezas-comunes.js; aquí va solo lo propio. */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["nmax-fig7"]=(function(){
"use strict";
const f=n=>Math.round(n*10)/10;
const EJE=[330,470];          // boca del orificio de drenaje B en el cárter
const BOMBA=[600,300];        // centro del piñón de la bomba

const DEFS=`
<linearGradient id="a7Alum" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#dfe3e5"/><stop offset=".5" stop-color="#a0a8ad"/><stop offset="1" stop-color="#5f676c"/></linearGradient>
<linearGradient id="a7AlumH" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6c7479"/><stop offset=".35" stop-color="#d7dbde"/><stop offset=".7" stop-color="#a7aeb2"/><stop offset="1" stop-color="#5a6267"/></linearGradient>
<linearGradient id="a7Acero" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef0f1"/><stop offset=".5" stop-color="#9aa2a7"/><stop offset="1" stop-color="#4f575c"/></linearGradient>
<linearGradient id="a7Plast" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4a5055"/><stop offset="1" stop-color="#16191b"/></linearGradient>
<pattern id="a7Malla" width="5" height="5" patternUnits="userSpaceOnUse"><rect width="5" height="5" fill="#2a2f33"/><path d="M0 0 L5 5 M5 0 L0 5" stroke="#a7aeb2" stroke-width=".8"/></pattern>
<filter id="a7Sombra" x="-20%" y="-20%" width="150%" height="150%"><feDropShadow dx="4" dy="7" stdDeviation="5" flood-color="#000" flood-opacity=".55"/></filter>
`;

/* ---------- contexto: cárter (otra lámina), con el perno de drenaje A ---------- */
const arteCarter=()=>`<g class="esq-ctx esq-ctx-barra" data-ctx="carter" pointer-events="none">
  <path d="M190 470 L190 330 Q190 250 260 220 L520 150 Q600 130 690 170 L760 220 L760 300 Q760 360 700 380 L470 430 L420 470 Q400 486 370 486 L290 486 Q220 486 190 470 Z"
    fill="#b9c2c7" fill-opacity=".05" stroke="#c9bfa7" stroke-opacity=".5" stroke-width="1.6" stroke-dasharray="7 5" pointer-events="visibleStroke"/>
  <ellipse cx="${EJE[0]}" cy="${EJE[1]}" rx="34" ry="12" fill="none" stroke="#c9bfa7" stroke-opacity=".5" stroke-dasharray="4 3"/>
  <circle cx="470" cy="436" r="10" fill="none" stroke="#c9bfa7" stroke-opacity=".55" stroke-dasharray="3 3"/>
  <text class="esq-ctx-txt" x="210" y="214">Cárter (lámina 10)</text>
  <text class="esq-ctx-txt" x="486" y="460">Perno de drenaje A (lámina 10)</text></g>`;

/* ---------- bomba de aceite (1): cuerpo de aluminio con su piñón de mando ---------- */
function arteBomba(){
  const [x,y]=BOMBA;let dientes="";
  for(let k=0;k<36;k++){const a=k*10*Math.PI/180,a1=a-.07,a2=a+.07;dientes+=`L${f(x+56*Math.cos(a1))} ${f(y+56*Math.sin(a1))} L${f(x+64*Math.cos(a1+.02))} ${f(y+64*Math.sin(a1+.02))} L${f(x+64*Math.cos(a2-.02))} ${f(y+64*Math.sin(a2-.02))} L${f(x+56*Math.cos(a2))} ${f(y+56*Math.sin(a2))} `}
  let ventanas="";for(let k=0;k<5;k++){const a=(k*72+18)*Math.PI/180;ventanas+=`<circle cx="${f(x+33*Math.cos(a))}" cy="${f(y+33*Math.sin(a))}" r="9" fill="#2a2f33"/>`}
  return `<g filter="url(#a7Sombra)">
    <path d="M${x-28} ${y-44} L${x+40} ${y-50} Q${x+70} ${y-46} ${x+72} ${y-14} L${x+72} ${y+30} Q${x+68} ${y+56} ${x+38} ${y+58} L${x-30} ${y+52} Z" transform="translate(16 -12)" fill="#3b4246"/>
    <path d="M${x-28} ${y-44} L${x+40} ${y-50} Q${x+70} ${y-46} ${x+72} ${y-14} L${x+72} ${y+30} Q${x+68} ${y+56} ${x+38} ${y+58} L${x-30} ${y+52} Z" transform="translate(8 -6)" fill="url(#a7Alum)" stroke="#2b3135"/>
    <path d="M${f(x+64)} ${y} ${dientes} Z" transform="translate(4 -3)" fill="#3e4549"/>
    <path d="M${f(x+64)} ${y} ${dientes} Z" fill="url(#a7Acero)" stroke="#40474b" stroke-width=".8" fill-rule="evenodd"/>
    <circle cx="${x}" cy="${y}" r="48" fill="none" stroke="#2b3135" stroke-opacity=".5" stroke-width="2"/>
    ${ventanas}
    <circle cx="${x}" cy="${y}" r="15" fill="url(#a7Alum)" stroke="#2b3135"/><circle cx="${x}" cy="${y}" r="6" fill="#1a1d20"/>
    <path d="M${x-44} ${y-30} A54 54 0 0 1 ${x+10} ${y-54}" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="3" stroke-linecap="round"/>
  </g>`;
}

/* cilindro vertical visto un poco desde arriba: cara de arriba en elipse */
function cilV(x,y,r,alto,cara,lado,borde="#2b3135"){
  return `<path d="M${x-r} ${y} L${x-r} ${y+alto} A${r} ${f(r*.35)} 0 0 0 ${x+r} ${y+alto} L${x+r} ${y} Z" fill="${lado}" stroke="${borde}" stroke-width=".8"/>
  <ellipse cx="${x}" cy="${y}" rx="${r}" ry="${f(r*.35)}" fill="${cara}" stroke="${borde}" stroke-width=".8"/>`;
}
/* ---------- tamiz de aceite (4): malla cilíndrica con su ceja de plástico ---------- */
const arteTamiz=()=>{const [x,y]=EJE;return `<g class="esq-oculto-arm" filter="url(#a7Sombra)">
  ${cilV(x,y-118,24,58,"#2a2f33","url(#a7Malla)")}
  <path d="M${x-24} ${y-110} L${x-24} ${y-66} M${x+24} ${y-110} L${x+24} ${y-66}" stroke="#16191b" stroke-width="3"/>
  ${cilV(x,y-66,32,10,"url(#a7Plast)","#16191b","#060708")}
  <ellipse cx="${x}" cy="${y-66}" rx="14" ry="5" fill="#0c0e10"/>
  <path d="M${x-18} ${y-112} L${x-18} ${y-70}" stroke="#fff" stroke-opacity=".25" stroke-width="2"/></g>`};

/* ---------- tapón de drenaje B (3): cabeza hexagonal grande, rosca y cara de la junta ---------- */
const arteTapon=()=>{const [x,y]=EJE;let hexa="";for(let k=0;k<6;k++){const a=(k*60)*Math.PI/180;hexa+=`${k?"L":"M"}${f(x+30*Math.cos(a))} ${f(y+18+30*Math.sin(a)*.35)} `}
  let rosca="";for(let k=0;k<5;k++)rosca+=`<path d="M${x-24} ${y-6+k*4} Q${x} ${y+2+k*4} ${x+24} ${y-6+k*4}" fill="none" stroke="#5f676c" stroke-width="1.2"/>`;
  return `<g filter="url(#a7Sombra)">
  ${cilV(x,y-10,24,22,"#7c858a","url(#a7AlumH)")}${rosca}
  ${cilV(x,y+8,34,6,"url(#a7Acero)","#5f676c")}
  <path d="${hexa}Z" fill="url(#a7Acero)" stroke="#2b3135"/>
  <path d="M${x-30} ${y+18} L${x-30} ${y+34} L${x-15} ${y+42} L${x+15} ${y+42} L${x+30} ${y+34} L${x+30} ${y+18}" fill="url(#a7AlumH)" stroke="#2b3135"/>
  <path d="M${x-15} ${y+28} L${x-15} ${y+42} M${x+15} ${y+28} L${x+15} ${y+42}" stroke="#2b3135" stroke-opacity=".6"/>
  <ellipse cx="${x}" cy="${y-10}" rx="12" ry="4" fill="#3b4246"/></g>`};

/* ---------- resorte del tamiz (5) y junta tórica (6): adentro del orificio, no se ven armados ---------- */
const arteResorteV=()=>{const [x,y]=EJE;let d=`M${x-14} ${y-56}`;for(let k=0;k<6;k++){const yy=y-56+k*6.5;d+=` Q${x} ${f(yy+5)} ${x+14} ${f(yy+3.2)} Q${x} ${f(yy+1.5)} ${x-14} ${f(yy+6.5)}`}
  return `<g class="esq-oculto-arm" filter="url(#a7Sombra)"><path d="${d}" fill="none" stroke="#2a2f33" stroke-width="4.4"/><path d="${d}" fill="none" stroke="#c9ced1" stroke-width="2.4"/></g>`};
const arteJunta=()=>{const [x,y]=EJE;return `<g class="esq-oculto-arm" filter="url(#a7Sombra)"><ellipse cx="${x}" cy="${y-12}" rx="27" ry="9.5" fill="none" stroke="#060708" stroke-width="6"/>
  <ellipse cx="${x}" cy="${y-12}" rx="27" ry="9.5" fill="none" stroke="#3a3f42" stroke-width="4"/><path d="M${x-22} ${y-17} Q${x-6} ${y-22} ${x+8} ${y-21}" fill="none" stroke="#fff" stroke-opacity=".25" stroke-width="1.4"/></g>`};

/* ---------- «Cómo funciona»: el motor en corte con el camino del aceite (izquierda); la bomba trocoidal cortada,
   el manómetro, el tamiz de cerca y el color del aceite (derecha) ----------
   Izquierda (x 0-470): cárter con el aceite, tamiz, bomba, cigüeñal con biela y pistón, y la culata con las levas.
   Derecha (#fn7-der): rotores de la bomba girando, presión aprox., tamiz con partículas y color según los km.
   En el celular la columna derecha baja debajo del corte. El giro va con un temporizador (requestAnimationFrame no corre con la pestaña oculta). */
const CIG=[240,300], RC=28, LB=110, BOM=[590,130], EXC=9;
const lobulos=(cx,cy,r,a,n,k=72)=>{let d="";for(let i=0;i<=k;i++){const t=i/k*2*Math.PI,rr=r+a*Math.cos(n*t);d+=(i?"L":"M")+f(cx+rr*Math.cos(t))+" "+f(cy+rr*Math.sin(t))}return d+"Z"};
const leva=(cx,cy)=>`M${cx-13} ${cy} A13 13 0 0 1 ${cx+13} ${cy} L${cx+5} ${cy+24} A6 6 0 0 1 ${cx-5} ${cy+24} Z`;
const FLUJO7="M110,394 L110,346 M110,316 L80,300 L80,86 L186,84 M80,300 L206,300";
const FN_SVG=`<svg id="fn" viewBox="0 0 900 440" role="img" aria-labelledby="fnTit">
  <title id="fnTit">Esquema de la lubricación en corte: la bomba trocoidal aspira el aceite del cárter por el tamiz y lo manda a presión al cigüeñal, la biela y las levas; a la derecha, los rotores de la bomba, la presión, el tamiz de cerca y el color del aceite según los km</title>
  <style>
    @keyframes esq7fluye{to{stroke-dashoffset:-36}}
    @keyframes esq7baja{to{stroke-dashoffset:36}}
    .esq-fn7-flujo{stroke-dasharray:12 24;animation:esq7fluye 1s linear infinite;transition:opacity .5s,stroke-width .6s}
    #fn7-vuelve{stroke-dasharray:4 14;animation:esq7baja 1s linear infinite;transition:opacity .5s}
    #fn7-aguja{transition:transform .9s cubic-bezier(.5,0,.3,1);transform-origin:790px 110px}
    .esq-fn7-nivel{transition:transform .9s;transform-box:fill-box;transform-origin:bottom}
    #fn7-calor,#fn7-chorro,.esq-fn7-part,#fn7-gota,#fn7-aceite{transition:opacity .6s,fill .9s}
    @media(max-width:700px){#fn7-der{transform:translate(-480px,430px)}}
    @media(prefers-reduced-motion:reduce){.esq-fn7-flujo,#fn7-vuelve{animation:none!important}}
  </style>
  <defs>
    <linearGradient id="fn7Acero" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef0f1"/><stop offset=".5" stop-color="#9aa2a7"/><stop offset="1" stop-color="#4f575c"/></linearGradient>
    <linearGradient id="fn7Alum" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#dfe3e5"/><stop offset=".5" stop-color="#a0a8ad"/><stop offset="1" stop-color="#5f676c"/></linearGradient>
    <linearGradient id="fn7AlumH" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6c7479"/><stop offset=".35" stop-color="#d7dbde"/><stop offset=".7" stop-color="#a7aeb2"/><stop offset="1" stop-color="#5a6267"/></linearGradient>
    <linearGradient id="fn7Corte" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2125"/><stop offset="1" stop-color="#101417"/></linearGradient>
    <linearGradient id="fn7Piston" x1="0" x2="1"><stop offset="0" stop-color="#6c7479"/><stop offset=".5" stop-color="#d4d9dc"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
    <radialGradient id="fn7Calor" cx=".5" cy=".5" r=".6"><stop offset="0" stop-color="#ff5a2a" stop-opacity=".75"/><stop offset="1" stop-color="#ff5a2a" stop-opacity="0"/></radialGradient>
    <pattern id="fn7Malla" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="#3a4246"/><path d="M0 0 L8 8 M8 0 L0 8" stroke="#a7aeb2" stroke-width="1.2"/></pattern>
  </defs>
  <text class="esq-fn-et esq-claro" x="14" y="30">El camino del aceite, en corte</text>
  <!-- carcasa cortada: culata, cilindro y cárter -->
  <rect x="150" y="48" width="180" height="64" rx="8" fill="url(#fn7Alum)" stroke="#5a6266" stroke-width="2"/>
  <rect x="160" y="58" width="160" height="44" rx="5" fill="url(#fn7Corte)"/>
  <rect x="180" y="112" width="120" height="140" fill="url(#fn7AlumH)" stroke="#5a6266"/>
  <rect x="194" y="112" width="92" height="140" fill="url(#fn7Corte)"/>
  <path d="M40,300 Q40,252 90,252 L390,252 Q440,252 440,300 L440,380 Q440,412 400,412 L80,412 Q40,412 40,380 Z" fill="url(#fn7Alum)" stroke="#5a6266" stroke-width="2"/>
  <path d="M52,302 Q52,264 92,264 L388,264 Q428,264 428,302 L428,378 Q428,400 398,400 L82,400 Q52,400 52,378 Z" fill="url(#fn7Corte)"/>
  <rect class="esq-fn7-nivel" id="fn7-aceite" x="54" y="368" width="372" height="32" fill="#d9a441" opacity=".85"/>
  <!-- calor en la culata cuando falta aceite -->
  <ellipse id="fn7-calor" cx="240" cy="96" rx="110" ry="60" fill="url(#fn7Calor)" opacity="0"/>
  <!-- levas (giran a la mitad que el cigüeñal) -->
  <path id="fn7-leva1" d="${leva(214,80)}" fill="url(#fn7Acero)" stroke="#2a2f33"/>
  <path id="fn7-leva2" d="${leva(266,80)}" fill="url(#fn7Acero)" stroke="#2a2f33"/>
  <circle cx="214" cy="80" r="4" fill="#3a4246"/><circle cx="266" cy="80" r="4" fill="#3a4246"/>
  <!-- cigüeñal, biela y pistón -->
  <g id="fn7-cig"><path d="M${CIG[0]-56},${CIG[1]} A56 56 0 0 0 ${CIG[0]+56},${CIG[1]} L${CIG[0]+30},${CIG[1]} A30 30 0 0 1 ${CIG[0]-30},${CIG[1]} Z" fill="url(#fn7Alum)" stroke="#2a2f33"/></g>
  <line id="fn7-biela" x1="240" y1="272" x2="240" y2="162" stroke="#a3abb0" stroke-width="12" stroke-linecap="round"/>
  <circle id="fn7-muneq" cx="240" cy="272" r="10" fill="#9aa3a8" stroke="#2a2f33"/>
  <circle cx="${CIG[0]}" cy="${CIG[1]}" r="12" fill="url(#fn7Acero)" stroke="#2a2f33"/>
  <g id="fn7-piston"><rect x="198" y="140" width="84" height="44" rx="4" fill="url(#fn7Piston)" stroke="#40474c"/><line x1="198" y1="149" x2="282" y2="149" stroke="#40474c"/><line x1="198" y1="155" x2="282" y2="155" stroke="#40474c"/><circle cx="240" cy="162" r="6" fill="#59646a"/></g>
  <!-- bomba, tamiz y tapón B -->
  <circle cx="110" cy="330" r="18" fill="url(#fn7Alum)" stroke="#2a2f33"/>
  <circle id="fn7-mini" cx="110" cy="330" r="10" fill="none" stroke="#3a4246" stroke-width="4" stroke-dasharray="5 4"/>
  <rect x="94" y="384" width="32" height="14" rx="3" fill="url(#fn7Malla)" stroke="#a7aeb2"/>
  <rect x="98" y="400" width="24" height="12" rx="2" fill="url(#fn7Acero)" stroke="#40474c"/>
  <path id="fn7-chorro" d="M110,414 C110,424 108,430 106,438" stroke="#7a5420" stroke-width="8" fill="none" stroke-linecap="round" opacity="0"/>
  <!-- flujo a presión y retorno por gravedad -->
  <path class="esq-fn7-flujo" id="fn7-flujo" d="${FLUJO7}" fill="none" stroke="#e8a92a" stroke-width="6" stroke-linecap="round" opacity="0"/>
  <path id="fn7-vuelve" d="M350,96 L350,360" fill="none" stroke="#e8a92a" stroke-width="5" stroke-linecap="round" opacity="0"/>
  <text class="esq-fn-et" x="338" y="72">Levas</text>
  <text class="esq-fn-et" x="300" y="190">Pistón</text>
  <text class="esq-fn-et" x="362" y="240">Vuelve</text>
  <text class="esq-fn-et" x="306" y="326">Cigüeñal</text>
  <text class="esq-fn-et" x="134" y="320">Bomba</text>
  <text class="esq-fn-et" x="134" y="396">Tamiz</text>
  <text class="esq-fn-et" x="14" y="434">Tapón B</text>
  <g id="fn7-der">
    <!-- la bomba trocoidal, cortada, y el manómetro -->
    <rect x="490" y="12" width="400" height="220" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="36">La bomba, en corte</text>
    <circle cx="${BOM[0]}" cy="${BOM[1]}" r="74" fill="url(#fn7Alum)" stroke="#40474c"/>
    <path d="M${BOM[0]-44},${BOM[1]+30} A50 50 0 0 1 ${BOM[0]-30},${BOM[1]-42}" stroke="#2c4a5c" stroke-width="16" fill="none" stroke-linecap="round"/>
    <path d="M${BOM[0]+44},${BOM[1]-30} A50 50 0 0 1 ${BOM[0]+30},${BOM[1]+42}" stroke="#a8741c" stroke-width="16" fill="none" stroke-linecap="round"/>
    <g id="fn7-ext"><path d="M${BOM[0]+64},${BOM[1]} A64 64 0 1 1 ${BOM[0]-64},${BOM[1]} A64 64 0 1 1 ${BOM[0]+64},${BOM[1]} Z ${lobulos(BOM[0],BOM[1],50,8,5)}" fill="url(#fn7Acero)" fill-rule="evenodd" stroke="#40474c"/></g>
    <g id="fn7-int"><path d="${lobulos(BOM[0]+EXC,BOM[1],34,8,4)}" fill="url(#fn7Alum)" stroke="#40474c"/><circle cx="${BOM[0]+EXC}" cy="${BOM[1]}" r="9" fill="#3a4246"/></g>
    <text class="esq-fn-et" x="504" y="222">Entra</text>
    <text class="esq-fn-et" x="628" y="222">Sale</text>
    <path d="M748 110 A42 42 0 0 1 832 110" fill="none" stroke="#2b3135" stroke-width="10"/>
    <g id="fn7-aguja"><line x1="790" y1="110" x2="790" y2="74" stroke="#f2e6c8" stroke-width="4" stroke-linecap="round"/></g>
    <circle cx="790" cy="110" r="6" fill="#9aa3a8"/>
    <text class="esq-fn-et esq-claro" id="fn7-bar" x="790" y="148" text-anchor="middle">0 bar</text>
    <text class="esq-fn-et" x="790" y="174" text-anchor="middle">Presión aprox.</text>
    <!-- el tamiz de cerca y el color del aceite -->
    <rect x="490" y="244" width="400" height="188" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="268">El tamiz y el aceite</text>
    <rect x="510" y="284" width="150" height="112" rx="6" fill="url(#fn7Malla)" stroke="#a7aeb2" stroke-width="2"/>
    <g class="esq-fn7-part" id="fn7-part1" opacity="0">${Array.from({length:12},(_,i)=>`<circle cx="${522+(i*37)%128}" cy="${296+(i*23)%90}" r="${2.4+(i%3)}" fill="#c9b48a"/>`).join("")}</g>
    <g class="esq-fn7-part" id="fn7-part2" opacity="0">${Array.from({length:22},(_,i)=>`<circle cx="${518+(i*29)%136}" cy="${292+(i*17)%98}" r="${3+(i%4)}" fill="#6b5634"/>`).join("")}</g>
    <text class="esq-fn-et" x="510" y="424">Tamiz</text>
    <path id="fn7-gota" d="M790,286 C812,316 830,338 830,360 A40 40 0 0 1 750,360 C750,338 768,316 790,286 Z" fill="#d9a441" stroke="#f2e6c8" stroke-width="2"/>
    <text class="esq-fn-et esq-claro" id="fn7-km" x="790" y="424" text-anchor="middle">0 km</text>
  </g>
</svg>`;
let giro={vel:0,th:0,t:0,id:0};
function dibujar7(){
  const $=id=>document.getElementById(id); if(!$("fn7-cig"))return;
  const th=giro.th, r=th*Math.PI/180, px=CIG[0]+RC*Math.sin(r), py=CIG[1]-RC*Math.cos(r);
  const pinY=py-Math.sqrt(LB*LB-Math.pow(px-CIG[0],2));
  $("fn7-cig").setAttribute("transform",`rotate(${f(th)} ${CIG[0]} ${CIG[1]})`);
  $("fn7-muneq").setAttribute("cx",f(px));$("fn7-muneq").setAttribute("cy",f(py));
  $("fn7-biela").setAttribute("x1",f(px));$("fn7-biela").setAttribute("y1",f(py));$("fn7-biela").setAttribute("y2",f(pinY));
  $("fn7-piston").setAttribute("transform",`translate(0 ${f(pinY-162)})`);
  $("fn7-leva1").setAttribute("transform",`rotate(${f(th/2)} 214 80)`);$("fn7-leva2").setAttribute("transform",`rotate(${f(th/2+110)} 266 80)`);
  $("fn7-int").setAttribute("transform",`rotate(${f(th*.6)} ${BOM[0]+EXC} ${BOM[1]})`);$("fn7-ext").setAttribute("transform",`rotate(${f(th*.48)} ${BOM[0]} ${BOM[1]})`);
  $("fn7-mini").setAttribute("transform",`rotate(${f(th*.6)} 110 330)`);
}
function bucle7(){const t=performance.now(),dt=giro.t?Math.min(50,t-giro.t):0;giro.t=t;giro.th=(giro.th+giro.vel*dt)%1440;dibujar7();
  giro.id=giro.vel?setTimeout(bucle7,30):0;if(!giro.vel)giro.t=0}
function fnAplicar(s,$){
  const quieto=matchMedia("(prefers-reduced-motion:reduce)").matches;
  // giro visible: lento, no a escala (las rpm reales serían un borrón)
  giro.vel=quieto?0:(s.rpm?(.08+.22*Math.min(1,s.rpm/8000)):0);
  if(quieto&&s.rpm)giro.th=(giro.th+60)%1440;
  dibujar7();if(giro.vel&&!giro.id)giro.id=setTimeout(bucle7,30);
  // aceite a presión y retorno
  const fl=$("fn7-flujo");fl.style.opacity=s.flujo?Math.min(1,.3+s.flujo):0;fl.style.strokeWidth=2+7*(s.flujo||0);
  $("fn7-vuelve").style.opacity=s.flujo?.8:0;
  // manómetro (0 a 5 bar en 180°)
  $("fn7-aguja").style.transform=`rotate(${(-90+180*Math.min(1,(s.bar||0)/5)).toFixed(1)}deg)`;
  $("fn7-bar").textContent=(s.bar||0).toLocaleString("es-CO",{minimumFractionDigits:1,maximumFractionDigits:1})+" bar";
  // color del aceite según los km (nuevo color miel; a 6.000 km casi negro)
  const k=Math.min(1,(s.km||0)/6000),mez=(a,b)=>Math.round(a+(b-a)*k),col=`rgb(${mez(217,46)},${mez(164,30)},${mez(65,14)})`;
  $("fn7-gota").setAttribute("fill",col);$("fn7-aceite").setAttribute("fill",col);
  $("fn7-km").textContent=(s.km||0).toLocaleString("es-CO")+" km";
  $("fn7-aceite").style.transform=`scaleY(${s.vacio?.03:1})`;
  // tamiz: partículas atrapadas; calor arriba si pasa poco aceite; chorro al drenar
  $("fn7-part1").style.opacity=s.sucio>0?1:0;$("fn7-part2").style.opacity=s.sucio>.6?1:0;
  $("fn7-calor").style.opacity=s.calor?1:0;$("fn7-chorro").style.opacity=s.drena?1:0;
}
return {defs:DEFS,arteBomba,arteCarter,arteJunta,arteResorteV,arteTamiz,arteTapon,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
