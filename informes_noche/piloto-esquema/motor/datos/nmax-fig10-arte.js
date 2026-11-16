/* Arte de la lámina 10 de la NMAX 155 (cárter y tapones del aceite): dibujos propios de TallerYa.
   Vista desde el lado izquierdo, simplificada: el cárter (dos mitades unidas) como una sola silueta de aluminio; adelante, la
   varilla del aceite y el perno de drenaje A; atrás, la caja de la transmisión final con su tapón de llenado, su perno de
   drenaje y la tapa 2 con el retén del eje; arriba, la tapa 2 del cárter con el respiradero. Tornillería, pasadores, bujes,
   cauchos, retenes, o-rings y juntas salen de piezas-comunes.js. */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["nmax-fig10"]=(function(){
"use strict";
const f=n=>Math.round(n*10)/10;
const ATRAS=[8,-6];
function extruir(d,pasos,fill,k){let r="";for(let i=pasos;i>=1;i--)r+=`<path d="${d}" transform="translate(${f(ATRAS[0]*i*k/pasos)} ${f(ATRAS[1]*i*k/pasos)})" fill="${fill}"/>`;return r}

const DEFS=`
<linearGradient id="a10Alum" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#dfe3e5"/><stop offset=".45" stop-color="#a3abb0"/><stop offset=".7" stop-color="#c3c9cc"/><stop offset="1" stop-color="#5f676c"/></linearGradient>
<linearGradient id="a10AlumOsc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9aa2a7"/><stop offset="1" stop-color="#40474b"/></linearGradient>
<linearGradient id="a10Plast" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5f666b"/><stop offset="1" stop-color="#1c1f22"/></linearGradient>
<linearGradient id="a10Amar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e8c34a"/><stop offset="1" stop-color="#a8841f"/></linearGradient>
<filter id="a10Sombra" x="-20%" y="-20%" width="150%" height="150%"><feDropShadow dx="4" dy="7" stdDeviation="5" flood-color="#000" flood-opacity=".55"/></filter>
`;

/* ---------- cárter (1): las dos mitades unidas, con el apoyo del cigüeñal adelante y la caja de la transmisión final atrás ---------- */
const P_CARTER="M160 300 Q160 220 240 210 L330 206 Q380 206 400 240 L470 250 L640 290 Q720 300 770 340 Q800 380 790 440 Q780 500 720 512 L560 520 L420 500 L360 530 Q300 548 240 530 Q170 510 162 440 Z";
function arteCarter(){
  let costillas="";for(let k=0;k<6;k++)costillas+=`<path d="M${440+k*36} 300 L${470+k*36} 470" stroke="#5f676c" stroke-opacity=".45" stroke-width="5"/>`;
  return `<g filter="url(#a10Sombra)">
    ${extruir(P_CARTER,6,"#3b4246",1.4)}
    <path d="${P_CARTER}" fill="url(#a10Alum)" stroke="#2b3135" stroke-width="1.6"/>
    <path d="M168 300 Q170 226 240 218 L330 214 Q376 214 394 246" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="2.5"/>
    <path d="M400 240 Q392 380 420 500" fill="none" stroke="#2b3135" stroke-opacity=".7" stroke-width="2.4" stroke-dasharray="1 0"/>
    ${costillas}
    <circle cx="250" cy="360" r="46" fill="url(#a10AlumOsc)" stroke="#2b3135"/><circle cx="250" cy="360" r="30" fill="#1a1d20"/>
    <circle cx="720" cy="430" r="68" fill="url(#a10AlumOsc)" stroke="#2b3135" stroke-opacity=".8"/>
    <circle cx="420" cy="262" r="22" fill="url(#a10AlumOsc)" stroke="#2b3135"/><circle cx="210" cy="512" r="20" fill="url(#a10AlumOsc)" stroke="#2b3135"/>
  </g>`;
}
/* ---------- varilla del aceite (14): tapón con mango y la varilla con sus marcas ---------- */
const arteVarilla=()=>`<g filter="url(#a10Sombra)">
  <rect x="306" y="214" width="3.5" height="60" fill="#c9ced1" class="esq-oculto-arm"/>
  <path d="M302 214 L314 214 L316 204 L300 204 Z" fill="#16191b" stroke="#060708"/>
  <path d="M296 204 L320 204 L322 176 Q308 168 294 176 Z" fill="url(#a10Amar)" stroke="#5c4510"/>
  <path d="M300 182 L316 182 M300 190 L316 190" stroke="#5c4510" stroke-width="1.6"/></g>`;
/* ---------- tapón de llenado de la transmisión final (16) ---------- */
const arteTaponLlenado=()=>`<g filter="url(#a10Sombra)">
  <rect x="680" y="318" width="26" height="10" rx="2" fill="url(#a10AlumOsc)" stroke="#2b3135"/>
  <rect x="684" y="304" width="18" height="16" rx="3" fill="url(#a10Alum)" stroke="#2b3135"/>
  <path d="M689 306 L689 318 M697 306 L697 318" stroke="#2b3135" stroke-opacity=".6"/></g>`;
/* ---------- tapa 2 del cárter (24), arriba en el medio, y respiradero (29) ---------- */
const P_TAPA24="M500 262 L600 250 Q640 250 646 286 L650 330 Q648 352 620 354 L512 360 Q490 360 488 336 L486 284 Q488 264 500 262 Z";
const arteTapa24=()=>`<g filter="url(#a10Sombra)">
  ${extruir(P_TAPA24,3,"#3b4246",1)}
  <path d="${P_TAPA24}" fill="url(#a10Alum)" stroke="#2b3135" stroke-width="1.4"/>
  <path d="${P_TAPA24}" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="1.2" transform="translate(2 2) scale(.996)"/>
  <path d="M520 290 L620 280 M520 320 L622 312" stroke="#5f676c" stroke-opacity=".5" stroke-width="4"/>
  <circle cx="568" cy="304" r="16" fill="url(#a10AlumOsc)" stroke="#2b3135"/></g>`;
const arteEmpaque24=()=>`<g class="esq-oculto-arm"><path d="${P_TAPA24}" transform="translate(6 -4)" fill="none" stroke="#2a2f33" stroke-width="7"/><path d="${P_TAPA24}" transform="translate(6 -4)" fill="none" stroke="#7c6f55" stroke-width="4"/></g>`;
const arteRespiradero=()=>`<g filter="url(#a10Sombra)">
  <rect x="590" y="232" width="38" height="20" rx="4" fill="url(#a10AlumOsc)" stroke="#2b3135"/>
  <rect x="600" y="212" width="18" height="22" rx="3" fill="url(#a10Alum)" stroke="#2b3135"/></g>`;
/* ---------- tapa 2 (18): tapa de atrás, sobre la caja de la transmisión final, con el retén del eje ---------- */
const P_TAPA18="M668 380 Q720 360 770 384 Q792 420 780 466 Q760 500 712 500 Q672 494 660 456 Q652 412 668 380 Z";
const arteTapa18=()=>`<g filter="url(#a10Sombra)">
  ${extruir(P_TAPA18,3,"#3b4246",1)}
  <path d="${P_TAPA18}" fill="url(#a10Alum)" stroke="#2b3135" stroke-width="1.4"/>
  <path d="M672 392 Q718 370 762 392" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="2"/>
  <circle cx="720" cy="436" r="24" fill="url(#a10AlumOsc)" stroke="#2b3135"/><circle cx="720" cy="436" r="11" fill="#1a1d20"/></g>`;

/* ---------- «Cómo funciona»: el cárter en corte (izquierda) y, a la derecha, la varilla de cerca, los litros y el retén en corte ----------
   Izquierda (x 0-470): el cigüeñal con su aceite abajo y la varilla metida desde arriba; atrás, separada por una pared,
   la caja de la transmisión final con sus engranajes metidos en su propio aceite.
   Derecha (#fn10-der): la punta de la varilla con la película de aceite, las barras de litros y el retén del eje cortado.
   En el celular la columna derecha baja debajo del corte. */
function engr10(cx,cy,r,n){let d="";for(let i=0;i<n*2;i++){const a=i*Math.PI/n,a2=(i+1)*Math.PI/n,rr=i%2?r-6:r;
  d+=(i?"L":"M")+f(cx+rr*Math.cos(a))+" "+f(cy+rr*Math.sin(a))+" L"+f(cx+rr*Math.cos(a2))+" "+f(cy+rr*Math.sin(a2))+" ";}return d+"Z"}
const FN_SVG=`<svg id="fn" viewBox="0 0 900 440" role="img" aria-labelledby="fnTit">
  <title id="fnTit">Esquema del cárter en corte: el aceite del motor con el cigüeñal y la varilla, y atrás la transmisión final con sus engranajes y su aceite; a la derecha, la punta de la varilla con las marcas, los litros de cada aceite y el retén del eje cortado</title>
  <style>
    @keyframes esq10salta{0%,100%{transform:translateY(0);opacity:.2}50%{transform:translateY(-16px);opacity:1}}
    @keyframes esq10gotea{0%{transform:translateY(0);opacity:0}20%{opacity:1}100%{transform:translateY(46px);opacity:0}}
    #fn10-varilla{transition:transform .9s cubic-bezier(.5,0,.3,1)}
    .esq-fn10-nivel{transition:transform .9s cubic-bezier(.5,0,.3,1);transform-box:fill-box;transform-origin:bottom}
    .esq-fn10-gota{animation:esq10salta .7s ease-in-out infinite}
    .esq-fn10-gota:nth-child(2n){animation-delay:.35s}
    #fn10-salpica,#fn10-salpicaF,#fn10-chorro,#fn10-fuga,#fn10-trapo{transition:opacity .5s}
    .esq-fn10-fugag{animation:esq10gotea 1s linear infinite}
    #fn10-labio{transition:transform .6s}
    @media(max-width:700px){#fn10-der{transform:translate(-480px,430px)}}
    @media(prefers-reduced-motion:reduce){.esq-fn10-gota,.esq-fn10-fugag{animation:none!important}}
  </style>
  <defs>
    <linearGradient id="fn10Alum" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#dfe3e5"/><stop offset=".45" stop-color="#a3abb0"/><stop offset=".7" stop-color="#c3c9cc"/><stop offset="1" stop-color="#5f676c"/></linearGradient>
    <linearGradient id="fn10AlumOsc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9aa2a7"/><stop offset="1" stop-color="#40474b"/></linearGradient>
    <linearGradient id="fn10Amar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e8c34a"/><stop offset="1" stop-color="#a8841f"/></linearGradient>
    <linearGradient id="fn10Corte" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2125"/><stop offset="1" stop-color="#101417"/></linearGradient>
    <linearGradient id="fn10Aceite" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e0a645"/><stop offset="1" stop-color="#9a6216"/></linearGradient>
    <linearGradient id="fn10AceiteF" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b98634"/><stop offset="1" stop-color="#6d4a12"/></linearGradient>
    <linearGradient id="fn10Eje" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6c7479"/><stop offset=".5" stop-color="#d4d9dc"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
  </defs>
  <text class="esq-fn-et esq-claro" x="14" y="30">El cárter, en corte</text>
  <!-- carcasa del motor (adelante) y caja de la transmisión final (atrás) -->
  <path d="M40,150 Q40,110 80,110 L300,110 L300,398 L78,398 Q40,398 40,360 Z" fill="url(#fn10Alum)" stroke="#5a6266" stroke-width="2"/>
  <path d="M52,154 Q52,122 84,122 L290,122 L290,388 L82,388 Q52,388 52,356 Z" fill="url(#fn10Corte)"/>
  <path d="M300,236 L430,236 Q462,236 462,270 L462,370 Q462,398 432,398 L300,398 Z" fill="url(#fn10AlumOsc)" stroke="#5a6266" stroke-width="2"/>
  <path d="M302,248 L428,248 Q450,248 450,272 L450,366 Q450,388 428,388 L302,388 Z" fill="url(#fn10Corte)"/>
  <rect x="288" y="236" width="14" height="162" fill="url(#fn10AlumOsc)" stroke="#5a6266"/>
  <!-- aceite del motor y del final (suben y bajan con su nivel) -->
  <rect class="esq-fn10-nivel" id="fn10-aceite" x="54" y="334" width="234" height="54" fill="url(#fn10Aceite)" opacity=".9"/>
  <rect class="esq-fn10-nivel" id="fn10-aceiteF" x="304" y="364" width="144" height="24" fill="url(#fn10AceiteF)" opacity=".9"/>
  <!-- cigüeñal con sus contrapesos -->
  <g class="esq-giro" id="fn10-cig">
    <circle cx="160" cy="232" r="64" fill="none" stroke="#2b3135" stroke-width="2" stroke-dasharray="4 8"/>
    <path d="M100,232 A60 60 0 0 1 220,232 L196,232 A36 36 0 0 0 124,232 Z" fill="url(#fn10AlumOsc)" stroke="#2a2f33"/>
    <circle cx="160" cy="232" r="22" fill="url(#fn10Alum)" stroke="#2a2f33"/>
    <circle cx="160" cy="268" r="12" fill="#9aa3a8" stroke="#2a2f33"/>
  </g>
  <circle cx="160" cy="232" r="7" fill="#59646a"/>
  <g id="fn10-salpica" opacity="0">${[[110,318],[140,312],[176,316],[210,320],[234,314]].map(([x,y])=>`<circle class="esq-fn10-gota" cx="${x}" cy="${y}" r="4" fill="#e0a645"/>`).join("")}</g>
  <text class="esq-fn-et" x="70" y="152">Cigüeñal</text>
  <!-- engranajes de la transmisión final -->
  <g class="esq-giro" id="fn10-g1"><path d="${engr10(400,326,40,16)}" fill="url(#fn10Alum)" stroke="#2a2f33"/><circle cx="400" cy="326" r="10" fill="#3a4246"/></g>
  <g class="esq-giro esq-lento" id="fn10-g2"><path d="${engr10(340,290,22,9)}" fill="url(#fn10Alum)" stroke="#2a2f33"/><circle cx="340" cy="290" r="6" fill="#3a4246"/></g>
  <g id="fn10-salpicaF" opacity="0">${[[322,350],[356,346],[436,344],[446,300]].map(([x,y])=>`<circle class="esq-fn10-gota" cx="${x}" cy="${y}" r="3.4" fill="#b98634"/>`).join("")}</g>
  <!-- varilla del aceite metida por la boca de llenado -->
  <rect x="254" y="104" width="22" height="20" fill="#2a2f33"/>
  <g id="fn10-varilla">
    <rect x="262" y="104" width="6" height="282" rx="2" fill="#c9ced1" stroke="#59646a"/>
    <line x1="258" y1="340" x2="272" y2="340" stroke="#1a1d20" stroke-width="2"/>
    <rect x="252" y="86" width="26" height="20" rx="5" fill="url(#fn10Amar)" stroke="#7c5f12"/>
  </g>
  <text class="esq-fn-et" x="288" y="100">Varilla</text>
  <!-- perno de drenaje A y chorro al cambiar -->
  <rect x="146" y="398" width="28" height="10" rx="2" fill="#9aa3a8" stroke="#40474c"/>
  <path id="fn10-chorro" d="M160,410 C160,420 158,428 156,438" stroke="#c98a2a" stroke-width="8" fill="none" opacity="0" stroke-linecap="round"/>
  <text class="esq-fn-et" x="14" y="428">Aceite del motor</text>
  <text class="esq-fn-et" x="466" y="428" text-anchor="end">Transmisión final</text>
  <g id="fn10-der">
    <!-- la punta de la varilla de cerca, y los litros de cada aceite -->
    <rect x="490" y="12" width="400" height="244" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="38">La varilla, de cerca</text>
    <rect x="548" y="52" width="34" height="18" rx="5" fill="url(#fn10Amar)" stroke="#7c5f12"/>
    <rect x="556" y="70" width="18" height="168" rx="4" fill="#c9ced1" stroke="#59646a"/>
    <rect class="esq-fn10-nivel" id="fn10-pelicula" x="556" y="128" width="18" height="110" rx="4" fill="#c98a2a" opacity=".9"/>
    <line x1="548" y1="128" x2="586" y2="128" stroke="#f2e6c8" stroke-width="3"/>
    <text class="esq-fn-et" x="596" y="134">Máx.</text>
    <text class="esq-fn-et" x="596" y="240">Punta</text>
    <rect id="fn10-trapo" x="540" y="150" width="52" height="34" rx="8" fill="#b9b2a0" opacity="0"/>
    <text class="esq-fn-et esq-claro" id="fn10-lect" x="596" y="188">Adentro</text>
    <rect x="730" y="70" width="30" height="140" rx="6" fill="#2b3135"/>
    <rect class="esq-fn10-nivel" id="fn10-barra" x="730" y="70" width="30" height="140" rx="6" fill="#c98a2a"/>
    <rect x="820" y="70" width="30" height="140" rx="6" fill="#2b3135"/>
    <rect class="esq-fn10-nivel" id="fn10-barraF" x="820" y="70" width="30" height="140" rx="6" fill="#9a6a1e"/>
    <text class="esq-fn-et esq-claro" id="fn10-l" x="745" y="60" text-anchor="middle">0,90 L</text>
    <text class="esq-fn-et esq-claro" id="fn10-lF" x="835" y="60" text-anchor="middle">0,10 L</text>
    <text class="esq-fn-et" x="745" y="236" text-anchor="middle">Motor</text>
    <text class="esq-fn-et" x="835" y="236" text-anchor="middle">Final</text>
    <!-- el retén del eje trasero, cortado -->
    <rect x="490" y="266" width="400" height="166" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="290">El retén del eje, en corte</text>
    <rect x="504" y="304" width="110" height="94" fill="url(#fn10AceiteF)" opacity=".75"/>
    <rect x="614" y="300" width="40" height="34" fill="url(#fn10AlumOsc)" stroke="#40474c"/>
    <rect x="614" y="368" width="40" height="34" fill="url(#fn10AlumOsc)" stroke="#40474c"/>
    <rect x="504" y="340" width="380" height="22" fill="url(#fn10Eje)" stroke="#40474c"/>
    <g id="fn10-labio">
      <path d="M622,334 L646,334 L646,320 L640,320 L640,328 L628,328 L622,340 Z" fill="#2b2f33" stroke="#0d0f10"/>
      <circle cx="634" cy="330" r="3" fill="#9aa3a8"/>
    </g>
    <path d="M622,368 L646,368 L646,382 L640,382 L640,374 L628,374 L622,362 Z" fill="#2b2f33" stroke="#0d0f10"/>
    <circle cx="634" cy="372" r="3" fill="#9aa3a8"/>
    <rect x="820" y="300" width="12" height="100" rx="3" fill="#8f979c" stroke="#40474c"/>
    <g id="fn10-fuga" opacity="0">
      <path d="M654,362 C700,366 760,364 818,360" stroke="#9a6a1e" stroke-width="4" fill="none"/>
      <circle class="esq-fn10-fugag" cx="700" cy="366" r="4" fill="#9a6a1e"/><circle class="esq-fn10-fugag" cx="824" cy="366" r="4" fill="#9a6a1e"/>
    </g>
    <text class="esq-fn-et" x="508" y="424">Aceite</text>
    <text class="esq-fn-et" x="612" y="424">Retén</text>
    <text class="esq-fn-et esq-claro" id="fn10-reten" x="690" y="324">Sella</text>
    <text class="esq-fn-et" x="800" y="424">Disco</text>
  </g>
</svg>`;
function fnAplicar(s,$){
  const L=v=>v.toFixed(2).replace(".",",")+" L";
  // aceites: el nivel del dibujo y las barras con sus litros
  $("fn10-aceite").style.transform=`scaleY(${Math.max(.02,s.nivel)})`;$("fn10-aceiteF").style.transform=`scaleY(${Math.max(.02,s.nivelF)})`;
  $("fn10-barra").style.transform=`scaleY(${Math.max(.01,s.litros/.9)})`;$("fn10-barraF").style.transform=`scaleY(${Math.max(.01,s.litrosF/.1)})`;
  $("fn10-l").textContent=L(s.litros);$("fn10-lF").textContent=L(s.litrosF);
  // motor y transmisión final: giran y salpican solo prendidos
  ["fn10-cig","fn10-g1","fn10-g2"].forEach(id=>$(id).classList.toggle("esq-quieto",!s.motor));
  $("fn10-salpica").style.opacity=s.motor?1:0;$("fn10-salpicaF").style.opacity=s.motor?1:0;
  // varilla: adentro o afuera; de cerca, la película de aceite y la lectura
  $("fn10-varilla").style.transform=s.varilla==="fuera"?"translateY(-80px)":"none";
  $("fn10-pelicula").style.transform=`scaleY(${Math.max(.01,s.pel||0)})`;$("fn10-pelicula").style.opacity=s.pel?.9:0;
  $("fn10-trapo").style.opacity=s.trapo?1:0;$("fn10-lect").textContent=s.lect;
  $("fn10-chorro").style.opacity=s.drena?1:0;
  // retén: el labio aprieta el eje; gastado, se separa y el aceite sale hacia el disco
  $("fn10-labio").style.transform=s.fuga?"translateY(-5px)":"none";$("fn10-fuga").style.opacity=s.fuga?1:0;
  $("fn10-reten").textContent=s.fuga?"Gotea al disco":"Sella";
}
return {defs:DEFS,arteCarter,arteEmpaque24,arteRespiradero,arteTapa18,arteTapa24,arteTaponLlenado,arteVarilla,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
