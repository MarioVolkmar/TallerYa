/* Arte de la lámina 1 de la NMAX 155 (cilindro, culata y bujía): dibujos propios de TallerYa.
   Vista desde arriba, a lo largo del eje del cilindro (dibujado de pie, como en el catálogo): adelante la tapa de la culata,
   detrás la culata y al fondo el cilindro, cada uno con su espesor hacia «atrás». La bujía entra por el lado de la culata.
   Tornillería, espárragos, pasadores, guías, retén y empaques salen de piezas-comunes.js. */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["nmax-fig1"]=(function(){
"use strict";
const f=n=>Math.round(n*10)/10;
const AT=[0.5,-0.32];
function extruir(d,t,pasos,fill){pasos=Math.max(pasos,Math.round(t/4));let r=`<path d="${d}" transform="translate(${f(AT[0]*t)} ${f(AT[1]*t)})" fill="${fill}" stroke="#23282b" stroke-width="1.2"/>`;for(let i=pasos-1;i>=1;i--)r+=`<path d="${d}" transform="translate(${f(AT[0]*t*i/pasos)} ${f(AT[1]*t*i/pasos)})" fill="${fill}"/>`;return r}
/* cuerpo redondeado con el túnel de la cadena a la derecha */
function cuerpo(cx,cy,w,h,r,tun){
  const x0=cx-w/2,x1=cx+w/2,y0=cy-h/2,y1=cy+h/2;
  const t=tun?`L${x1} ${cy-24} L${x1+tun} ${cy-20} L${x1+tun} ${cy+20} L${x1} ${cy+24}`:"";
  return `M${x0+r} ${y0} L${x1-r} ${y0} Q${x1} ${y0} ${x1} ${y0+r} ${t} L${x1} ${y1-r} Q${x1} ${y1} ${x1-r} ${y1} L${x0+r} ${y1} Q${x0} ${y1} ${x0} ${y1-r} L${x0} ${y0+r} Q${x0} ${y0} ${x0+r} ${y0} Z`;
}

const DEFS=`
<linearGradient id="c1Alum" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e2e6e8"/><stop offset=".45" stop-color="#a7afb4"/><stop offset=".75" stop-color="#c6ccd0"/><stop offset="1" stop-color="#626a6f"/></linearGradient>
<linearGradient id="c1AlumOsc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9ba3a8"/><stop offset="1" stop-color="#40474b"/></linearGradient>
<linearGradient id="c1Negro" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6a7177"/><stop offset=".5" stop-color="#3a3f44"/><stop offset="1" stop-color="#1b1e21"/></linearGradient>
<linearGradient id="c1Ceram" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#dfe2e4"/><stop offset="1" stop-color="#a9afb3"/></linearGradient>
<linearGradient id="c1Acero" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9ecee"/><stop offset=".5" stop-color="#9aa2a7"/><stop offset="1" stop-color="#5a6166"/></linearGradient>
<radialGradient id="c1Camisa" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#d7dcdf"/><stop offset=".7" stop-color="#8e969b"/><stop offset="1" stop-color="#4b5256"/></radialGradient>
<filter id="c1Sombra" x="-20%" y="-20%" width="150%" height="150%"><feDropShadow dx="4" dy="7" stdDeviation="5" flood-color="#000" flood-opacity=".55"/></filter>
`;

/* ---------- cilindro (25): bloque de aluminio con la camisa, la chaqueta de agua, los cuatro pasos de espárrago y el túnel de la cadena ---------- */
const CY=[455,397.6];
function arteCilindro(){
  const [x,y]=CY,P=cuerpo(x,y,136,112,14,16);
  return `<g filter="url(#c1Sombra)">
    ${extruir(P,100,9,"#737c82")}
    <path d="M${x-68} ${y+30} L${x-86} ${y+30} L${x-86} ${y+14} L${x-68} ${y+14}" fill="url(#c1AlumOsc)" stroke="#23282b"/>
    <path d="${P}" fill="url(#c1Alum)" stroke="#23282b" stroke-width="1.6"/>
    <path d="M${x-60} ${y-50} L${x+58} ${y-50}" stroke="#fff" stroke-opacity=".5" stroke-width="2.4"/>
    <circle cx="${x}" cy="${y}" r="45" fill="none" stroke="#2c4a5c" stroke-width="7" stroke-dasharray="16 6"/>
    <circle cx="${x}" cy="${y}" r="35" fill="url(#c1Camisa)" stroke="#23282b" stroke-width="1.4"/>
    <circle cx="${x}" cy="${y}" r="27" fill="#16191b" opacity=".85"/>
    ${[[-52,-42],[52,-42],[-52,42],[52,42]].map(([a,b])=>`<circle cx="${x+a}" cy="${y+b}" r="5.5" fill="#1a1d20"/>`).join("")}
    <rect x="${x+56}" y="${y-18}" width="14" height="36" rx="4" fill="#1a1d20"/>
  </g>`;
}
/* ---------- culata (1): vista de arriba, con la cámara de levas, los cuatro asientos de tuerca, el pozo de la bujía y el túnel ---------- */
const HC=[420,420];
function arteCulata(){
  const [x,y]=HC,P=cuerpo(x,y,136,112,16,16);
  return `<g filter="url(#c1Sombra)">
    ${extruir(P,70,7,"#5f686e")}
    <rect x="${x-86}" y="${y-22}" width="20" height="26" rx="4" fill="url(#c1AlumOsc)" stroke="#23282b"/>
    <path d="${P}" fill="url(#c1Alum)" stroke="#23282b" stroke-width="1.6"/>
    <path d="M${x-58} ${y-50} L${x+54} ${y-50}" stroke="#fff" stroke-opacity=".55" stroke-width="2.4"/>
    <rect x="${x-50}" y="${y-38}" width="100" height="76" rx="10" fill="url(#c1AlumOsc)" stroke="#23282b"/>
    <rect x="${x-44}" y="${y-8}" width="88" height="16" rx="7" fill="#7d868b" stroke="#2b3135"/>
    <circle cx="${x-6}" cy="${y}" r="12" fill="#1a1d20" stroke="#5f676c" stroke-width="2"/>
    ${[[-52,-42],[52,-42],[-52,42],[52,42]].map(([a,b])=>`<circle cx="${x+a}" cy="${y+b}" r="9" fill="url(#c1AlumOsc)" stroke="#23282b"/>`).join("")}
    <rect x="${x+56}" y="${y-16}" width="12" height="32" rx="4" fill="#1a1d20"/>
  </g>`;
}
/* ---------- tapa de la culata (7): plástica/aluminio negro con nervios, cuatro tornillos y la salida del respiradero ---------- */
const TC=[397.5,434.4];
function arteTapa(){
  const [x,y]=TC,P=cuerpo(x,y,108,86,18,0);
  let nerv="";for(let k=-2;k<=2;k++)nerv+=`<path d="M${x-34} ${y+k*12} L${x+34} ${y+k*12}" stroke="#8b949a" stroke-opacity=".55" stroke-width="3"/>`;
  return `<g filter="url(#c1Sombra)">
    ${extruir(P,45,5,"#25292c")}
    <path d="${P}" fill="url(#c1Negro)" stroke="#aeb6bb" stroke-width="1.8"/>
    <path d="M${x-40} ${y-40} L${x+36} ${y-40}" stroke="#fff" stroke-opacity=".5" stroke-width="2"/>
    ${nerv}
    <rect x="${x+20}" y="${y-58}" width="16" height="18" rx="4" fill="url(#c1AlumOsc)" stroke="#23282b"/>
    ${[[-44,-33],[44,-33],[-44,33],[44,33]].map(([a,b])=>`<circle cx="${x+a}" cy="${y+b}" r="8" fill="#2d3236" stroke="#aeb6bb"/>`).join("")}
  </g>`;
}
/* ---------- bujía (20): de lado, entrando por el costado de la culata ---------- */
function arteBujia(){
  const x=282,y=405;
  return `<g filter="url(#c1Sombra)">
    <rect x="${x}" y="${y-4}" width="8" height="8" rx="1.5" fill="url(#c1Acero)" stroke="#2b3135"/>
    <rect x="${x+7}" y="${y-6}" width="22" height="12" rx="3" fill="url(#c1Ceram)" stroke="#8a9196"/>
    <path d="M${x+12} ${y-6} L${x+12} ${y+6} M${x+17} ${y-6} L${x+17} ${y+6} M${x+22} ${y-6} L${x+22} ${y+6}" stroke="#9aa1a6" stroke-width="1"/>
    <rect x="${x+29}" y="${y-9}" width="12" height="18" rx="1.5" fill="url(#c1Acero)" stroke="#2b3135"/>
    <path d="M${x+33} ${y-9} L${x+33} ${y+9} M${x+37} ${y-9} L${x+37} ${y+9}" stroke="#2b3135" stroke-opacity=".6"/>
    <rect x="${x+41}" y="${y-5}" width="15" height="10" fill="url(#c1Acero)" stroke="#2b3135"/>
    <path d="M${x+44} ${y-5} L${x+45} ${y+5} M${x+48} ${y-5} L${x+49} ${y+5} M${x+52} ${y-5} L${x+53} ${y+5}" stroke="#4b5256"/>
    <path d="M${x+56} ${y-1} L${x+61} ${y-1} M${x+56} ${y+4} L${x+61} ${y+4} L${x+61} ${y+1}" stroke="#c9ced1" stroke-width="1.6" fill="none"/>
  </g>`;
}

/* ---------- «Cómo funciona»: los cuatro tiempos en corte (izquierda) y, a la derecha, el ángulo del cigüeñal (0-720°)
   y la bujía de cerca ----------
   Izquierda (x 0-470): culata con las levas, las dos válvulas y la bujía; cilindro con la chaqueta de agua; pistón, biela y
   cigüeñal. Todo se calcula desde el ángulo: cada paso hace girar el cigüeñal hasta su ángulo (con temporizador).
   Derecha (#fn1-der): línea de 0 a 720° con los cuatro tiempos y la marca; la punta de la bujía con su chispa.
   En el celular la columna derecha baja debajo del corte. */
const C1=[235,350], R1=34, L1=120;
const leva1=(cx,cy)=>`M${cx-12} ${cy} A12 12 0 0 1 ${cx+12} ${cy} L${cx+5} ${cy+22} A5.5 5.5 0 0 1 ${cx-5} ${cy+22} Z`;
const TIEMPOS=[["Admisión","#4f8fc0"],["Compresión","#2f6aa0"],["Fuerza","#f08a24"],["Escape","#7a7f84"]];
const FN_SVG=`<svg id="fn" viewBox="0 0 900 440" role="img" aria-labelledby="fnTit">
  <title id="fnTit">Corte del cilindro y la culata con los cuatro tiempos: el cigüeñal gira, el pistón sube y baja, las levas abren las válvulas de admisión y de escape por turnos, la bujía hace la chispa y el refrigerante rodea el cilindro; a la derecha, el ángulo del cigüeñal de 0 a 720° y la punta de la bujía</title>
  <style>
    @keyframes esq1fluye{to{stroke-dashoffset:-30}}
    .esq-fn1-agua{stroke-dasharray:8 22;animation:esq1fluye 1s linear infinite;transition:opacity .6s}
    #fn1-chispa,#fn1-chispa2,#fn1-gap,#fn1-portA,#fn1-portE{transition:opacity .25s}
    @media(max-width:700px){#fn1-der{transform:translate(-480px,430px)}}
    @media(prefers-reduced-motion:reduce){.esq-fn1-agua{animation:none!important}}
  </style>
  <defs>
    <linearGradient id="fn1Acero" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9ecee"/><stop offset=".5" stop-color="#9aa2a7"/><stop offset="1" stop-color="#5a6166"/></linearGradient>
    <linearGradient id="fn1Alum" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e2e6e8"/><stop offset=".45" stop-color="#a7afb4"/><stop offset=".75" stop-color="#c6ccd0"/><stop offset="1" stop-color="#626a6f"/></linearGradient>
    <linearGradient id="fn1AlumOsc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9ba3a8"/><stop offset="1" stop-color="#40474b"/></linearGradient>
    <linearGradient id="fn1Ceram" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#dfe2e4"/><stop offset="1" stop-color="#a9afb3"/></linearGradient>
    <linearGradient id="fn1Corte" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2125"/><stop offset="1" stop-color="#101417"/></linearGradient>
    <linearGradient id="fn1Piston" x1="0" x2="1"><stop offset="0" stop-color="#6c7479"/><stop offset=".5" stop-color="#dfe3e5"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
    <linearGradient id="fn1Agua" x1="0" x2="1"><stop offset="0" stop-color="#1f5a80"/><stop offset=".5" stop-color="#4aa3d8"/><stop offset="1" stop-color="#1f5a80"/></linearGradient>
    <radialGradient id="fn1Llama" cx=".5" cy="0" r="1"><stop offset="0" stop-color="#fff1b0"/><stop offset=".4" stop-color="#f08a24"/><stop offset="1" stop-color="#9c2f14"/></radialGradient>
  </defs>
  <text class="esq-fn-et esq-claro" x="14" y="30">Cilindro en corte</text>
  <!-- cilindro con la chaqueta de agua -->
  <rect x="128" y="138" width="214" height="166" fill="url(#fn1AlumOsc)" stroke="#5a6266" stroke-width="2"/>
  <rect x="136" y="142" width="20" height="150" rx="4" fill="url(#fn1Agua)"/>
  <rect x="314" y="142" width="20" height="150" rx="4" fill="url(#fn1Agua)"/>
  <rect x="160" y="138" width="150" height="166" fill="url(#fn1Corte)"/>
  <path class="esq-fn1-agua" id="fn1-aguaF" d="M146,292 L146,150 M324,150 L324,292" stroke="#cdeeff" stroke-width="3" fill="none" opacity="0"/>
  <!-- cárter con el cigüeñal -->
  <path d="M120,304 L350,304 L350,370 Q350,412 300,412 L170,412 Q120,412 120,370 Z" fill="url(#fn1AlumOsc)" stroke="#5a6266" stroke-width="2"/>
  <path d="M132,306 L338,306 L338,368 Q338,400 298,400 L172,400 Q132,400 132,368 Z" fill="url(#fn1Corte)"/>
  <g id="fn1-cig"><path d="M${C1[0]-48},${C1[1]} A48 48 0 0 0 ${C1[0]+48},${C1[1]} L${C1[0]+24},${C1[1]} A24 24 0 0 1 ${C1[0]-24},${C1[1]} Z" fill="url(#fn1Alum)" stroke="#2a2f33"/></g>
  <!-- gas en la cámara (color según el tiempo) -->
  <rect id="fn1-gas" x="160" y="140" width="150" height="40" fill="#4f8fc0" opacity=".6"/>
  <!-- biela y pistón -->
  <line id="fn1-biela" x1="235" y1="316" x2="235" y2="196" stroke="#a7afb4" stroke-width="13" stroke-linecap="round"/>
  <circle id="fn1-muneq" cx="235" cy="316" r="10" fill="#9aa3a8" stroke="#2a2f33"/>
  <circle cx="${C1[0]}" cy="${C1[1]}" r="11" fill="url(#fn1Acero)" stroke="#2a2f33"/>
  <g id="fn1-piston"><rect x="164" y="166" width="142" height="54" rx="4" fill="url(#fn1Piston)" stroke="#40474c"/><line x1="164" y1="176" x2="306" y2="176" stroke="#40474c"/><line x1="164" y1="183" x2="306" y2="183" stroke="#40474c"/><circle cx="235" cy="196" r="7" fill="#59646a"/></g>
  <!-- culata con los ductos, las válvulas, las levas y la bujía -->
  <path d="M112,138 L112,74 Q235,46 358,74 L358,138 Z" fill="url(#fn1AlumOsc)" stroke="#9aa2a7" stroke-width="2"/>
  <path d="M112,100 L170,100 L196,136" fill="none" stroke="#101417" stroke-width="18"/>
  <path d="M358,100 L300,100 L274,136" fill="none" stroke="#101417" stroke-width="18"/>
  <path id="fn1-portA" d="M112,100 L170,100 L196,136" fill="none" stroke="#4f8fc0" stroke-width="10" opacity="0"/>
  <path id="fn1-portE" d="M358,100 L300,100 L274,136" fill="none" stroke="#7a7f84" stroke-width="10" opacity="0"/>
  <path class="esq-fn1-agua" id="fn1-aguaC" d="M140,126 Q235,96 330,126" stroke="#4aa3d8" stroke-width="5" fill="none" opacity="0"/>
  <g id="fn1-vadm"><rect x="194" y="56" width="6" height="80" fill="url(#fn1Acero)"/><path d="M180,140 L214,140 L203,132 L191,132 Z" fill="#c9ced1" stroke="#40474c"/></g>
  <g id="fn1-vesc"><rect x="270" y="56" width="6" height="80" fill="url(#fn1Acero)"/><path d="M256,140 L290,140 L279,132 L267,132 Z" fill="#c9ced1" stroke="#40474c"/></g>
  <path id="fn1-levaA" d="${leva1(197,40)}" fill="url(#fn1Acero)" stroke="#2a2f33"/>
  <path id="fn1-levaE" d="${leva1(273,40)}" fill="url(#fn1Acero)" stroke="#2a2f33"/>
  <circle cx="197" cy="40" r="4" fill="#3a4246"/><circle cx="273" cy="40" r="4" fill="#3a4246"/>
  <rect x="229" y="22" width="12" height="44" rx="3" fill="url(#fn1Ceram)" stroke="#9aa2a7"/>
  <rect x="226" y="66" width="18" height="16" fill="url(#fn1Acero)"/><rect x="231" y="82" width="8" height="54" fill="#9aa2a7"/>
  <path id="fn1-chispa" d="M235,138 L227,152 L236,149 L230,166 L246,144 L237,147 Z" fill="#ffd54a" opacity="0"/>
  <text class="esq-fn-et" x="14" y="88">Admisión</text>
  <text class="esq-fn-et" x="362" y="88">Escape</text>
  <text class="esq-fn-et" x="252" y="22">Bujía</text>
  <text class="esq-fn-et" x="296" y="50">Levas</text>
  <text class="esq-fn-et" x="4" y="232">Refrigerante</text>
  <text class="esq-fn-et" x="346" y="232">Pistón</text>
  <text class="esq-fn-et" x="356" y="380">Cigüeñal</text>
  <g id="fn1-der">
    <!-- ángulo del cigüeñal: dos vueltas = un ciclo -->
    <rect x="490" y="12" width="400" height="190" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="38">Ángulo del cigüeñal</text>
    <text class="esq-fn-et esq-claro" id="fn1-ang" x="504" y="76">0°</text>
    <text class="esq-fn-et esq-claro" id="fn1-fase" x="600" y="76">Admisión</text>
    ${TIEMPOS.map(([n,c],i)=>`<rect x="${504+i*93}" y="94" width="93" height="26" fill="${c}" opacity=".85" stroke="#161b1e" stroke-width="2"/>`).join("")}
    ${["Adm.","Comp.","Fuerza","Esc."].map((n,i)=>`<text class="esq-fn-et" x="${550+i*93}" y="146" text-anchor="middle">${n}</text>`).join("")}
    <g id="fn1-marca"><path d="M504,90 L497,80 L511,80 Z" fill="#f2e6c8"/><line x1="504" y1="90" x2="504" y2="124" stroke="#f2e6c8" stroke-width="3"/></g>
    <text class="esq-fn-et" x="504" y="182">0°</text>
    <text class="esq-fn-et" x="690" y="182" text-anchor="middle">360°</text>
    <text class="esq-fn-et" x="876" y="182" text-anchor="end">720°</text>
    <!-- la bujía de cerca -->
    <rect x="490" y="214" width="400" height="218" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="240">La bujía, de cerca</text>
    <rect x="562" y="252" width="36" height="64" rx="6" fill="url(#fn1Ceram)" stroke="#9aa2a7"/>
    <path d="M550,316 L610,316 L614,334 L610,352 L550,352 L546,334 Z" fill="url(#fn1Acero)" stroke="#40474c"/>
    <rect x="562" y="352" width="36" height="40" fill="url(#fn1Acero)" stroke="#40474c"/>
    ${[358,366,374,382].map(y=>`<line x1="562" y1="${y}" x2="598" y2="${y+4}" stroke="#59646a" stroke-width="2"/>`).join("")}
    <rect x="576" y="392" width="8" height="12" fill="#c9ced1"/>
    <path d="M596,392 L604,392 L604,418 L572,418 L572,412 L598,412 L598,392 Z" fill="#c9ced1" stroke="#59646a"/>
    <path id="fn1-gap" d="M566,404 L594,404 M566,412 L594,412" stroke="#ffd54a" stroke-width="2" opacity=".35"/>
    <path id="fn1-chispa2" d="M580,404 L576,408 L583,407 L579,412" stroke="#ffd54a" stroke-width="3" fill="none" opacity="0"/>
    <text class="esq-fn-et" x="632" y="290">NGK CPR8EA-9</text>
    <text class="esq-fn-et" x="632" y="380">Separación</text>
    <text class="esq-fn-et esq-claro" x="632" y="408">0,8–0,9 mm</text>
  </g>
</svg>`;
const GAS1=a=>a<180?["#4f8fc0",.55]:a<345?["#2f6aa0",.55+.3*(a-180)/165]:a<480?["url(#fn1Llama)",.9]:a<540?["#f08a24",.6]:["#7a7f84",.5];
let est1={ang:0,anim:0};
function dibujar1(ang){
  const $=id=>document.getElementById(id); if(!$("fn1-cig"))return;
  const a=((ang%720)+720)%720, r=a*Math.PI/180, px=C1[0]+R1*Math.sin(r), py=C1[1]-R1*Math.cos(r);
  const pinY=py-Math.sqrt(L1*L1-Math.pow(px-C1[0],2)), top=pinY-30;
  $("fn1-cig").setAttribute("transform",`rotate(${f(a)} ${C1[0]} ${C1[1]})`);
  $("fn1-muneq").setAttribute("cx",f(px));$("fn1-muneq").setAttribute("cy",f(py));
  $("fn1-biela").setAttribute("x1",f(px));$("fn1-biela").setAttribute("y1",f(py));$("fn1-biela").setAttribute("y2",f(pinY));
  $("fn1-piston").setAttribute("transform",`translate(0 ${f(pinY-196)})`);
  const g=$("fn1-gas"),[col,op]=GAS1(a);g.setAttribute("height",f(Math.max(4,top-140)));g.setAttribute("fill",col);g.setAttribute("opacity",op);
  // levas: una vuelta cada dos del cigüeñal; la válvula baja cuando el lóbulo la empuja
  // tiempos ideales de 180°, más el cruce: la admisión empieza a abrir a 690° y el escape termina de cerrar a 20° (las dos abiertas un instante)
  const liftA=a<=180?12*Math.sin(Math.PI*a/180):a>=690?4*(a-690)/30:0, liftE=a>=540?12*Math.sin(Math.PI*(a-540)/180):a<20?4*(20-a)/20:0;
  $("fn1-levaA").setAttribute("transform",`rotate(${f((a-90)/2)} 197 40)`);$("fn1-levaE").setAttribute("transform",`rotate(${f((a-630)/2)} 273 40)`);
  $("fn1-vadm").setAttribute("transform",`translate(0 ${f(liftA)})`);$("fn1-vesc").setAttribute("transform",`translate(0 ${f(liftE)})`);
  $("fn1-portA").style.opacity=liftA>1?.9:0;$("fn1-portE").style.opacity=liftE>1?.9:0;
  const chispa=a>=335&&a<=365;$("fn1-chispa").style.opacity=chispa?1:0;$("fn1-chispa2").style.opacity=chispa?1:0;$("fn1-gap").style.opacity=chispa?1:.35;
  $("fn1-marca").setAttribute("transform",`translate(${f(372*a/720)} 0)`);
  $("fn1-ang").textContent=Math.round(a)+"°";$("fn1-fase").textContent=TIEMPOS[Math.min(3,Math.floor(a/180))][0]+(liftA>1&&liftE>1?" · cruce":"");
}
function fnAplicar(s,$){
  const quieto=matchMedia("(prefers-reduced-motion:reduce)").matches;
  ["fn1-aguaF","fn1-aguaC"].forEach(id=>$(id).style.opacity=s.agua?1:0);
  clearTimeout(est1.anim);
  const ini=est1.ang, fin=s.ang, t0=performance.now(), dur=quieto?0:Math.min(1600,300+Math.abs(fin-ini)*3);
  // temporizador y no requestAnimationFrame: así termina aunque la pestaña esté oculta
  const paso=()=>{const p=dur?Math.min(1,(performance.now()-t0)/dur):1, e=p<.5?2*p*p:1-Math.pow(-2*p+2,2)/2;est1.ang=ini+(fin-ini)*e;dibujar1(est1.ang);
    if(p<1)est1.anim=setTimeout(paso,16)};
  paso();
}
return {defs:DEFS,arteBujia,arteCilindro,arteCulata,arteTapa,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
