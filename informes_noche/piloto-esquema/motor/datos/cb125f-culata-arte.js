/* Arte de la culata de la Honda CB 125F (GLH125SH), fig. E-1-2 del catálogo Honda: dibujos propios de TallerYa.
   Parte de la lámina hermana nmax-fig1 (DEFS y «Cómo funciona»), adaptada a motor enfriado por aire. */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["cb125f-culata"]=(function(){
const f=n=>Math.round(n*10)/10;
const AT=[0.5,-0.32];
function extruir(d,t,pasos,fill){pasos=Math.max(pasos,Math.round(t/4));let r=`<path d="${d}" transform="translate(${f(AT[0]*t)} ${f(AT[1]*t)})" fill="${fill}" stroke="#23282b" stroke-width="1.2"/>`;for(let i=pasos-1;i>=1;i--)r+=`<path d="${d}" transform="translate(${f(AT[0]*t*i/pasos)} ${f(AT[1]*t*i/pasos)})" fill="${fill}"/>`;return r}
const DEFS=`
<linearGradient id="hcAlum" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e2e6e8"/><stop offset=".45" stop-color="#a7afb4"/><stop offset=".75" stop-color="#c6ccd0"/><stop offset="1" stop-color="#626a6f"/></linearGradient>
<linearGradient id="hcAlumOsc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9ba3a8"/><stop offset="1" stop-color="#40474b"/></linearGradient>
<linearGradient id="hcNegro" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6a7177"/><stop offset=".5" stop-color="#3a3f44"/><stop offset="1" stop-color="#1b1e21"/></linearGradient>
<linearGradient id="hcCeram" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#dfe2e4"/><stop offset="1" stop-color="#a9afb3"/></linearGradient>
<linearGradient id="hcAcero" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9ecee"/><stop offset=".5" stop-color="#9aa2a7"/><stop offset="1" stop-color="#5a6166"/></linearGradient>
<radialGradient id="hcCamisa" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#d7dcdf"/><stop offset=".7" stop-color="#8e969b"/><stop offset="1" stop-color="#4b5256"/></radialGradient>
<filter id="hcSombra" x="-20%" y="-20%" width="150%" height="150%"><feDropShadow dx="4" dy="7" stdDeviation="5" flood-color="#000" flood-opacity=".55"/></filter>


<linearGradient id="hcBronce" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8a6a32"/><stop offset=".5" stop-color="#e0b866"/><stop offset="1" stop-color="#7a5a26"/></linearGradient>
<linearGradient id="hcCaucho" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4a5055"/><stop offset="1" stop-color="#16191b"/></linearGradient>
`;
/* ---------- culata (2): aluminio con aletas de enfriamiento por aire, vista de tres cuartos (el plano va igual) ---------- */
const HC=[450,395];
function arteCulata(){
  const [x,y]=HC,w=240,h=110,x0=x-w/2,y0=y-h/2,P=`M${x0+10} ${y0} L${x0+w-10} ${y0} Q${x0+w} ${y0} ${x0+w} ${y0+10} L${x0+w} ${y0+h} L${x0} ${y0+h} L${x0} ${y0+10} Q${x0} ${y0} ${x0+10} ${y0} Z`;
  let al="";for(let k=0;k<6;k++){const yy=y0+22+k*15;al+=`<rect x="${x0-8}" y="${yy}" width="${w+16}" height="7" rx="3" fill="url(#hcAlum)" stroke="#23282b" stroke-width="1"/><path d="M${x0-4} ${yy+1.5} L${x0+w+4} ${yy+1.5}" stroke="#fff" stroke-opacity=".5" stroke-width="1.4"/>`;}
  return `<g filter="url(#hcSombra)">
    ${extruir(P,60,6,"#5f686e")}
    <path d="${P}" fill="url(#hcAlumOsc)" stroke="#23282b" stroke-width="1.6"/>
    <path d="M${x0} ${y0} L${x0+30} ${y0-19} L${x0+w+30} ${y0-19} L${x0+w} ${y0} Z" fill="#8d969b" stroke="#23282b"/>
    <path d="M${x0+14} ${y0-3} L${x0+38} ${y0-16} L${x0+w+18} ${y0-16} L${x0+w-8} ${y0-3} Z" fill="#2b3034" stroke="#5f676c"/>
    ${al}
    <path d="M${x0+18} ${y0+6} L${x0+w-18} ${y0+6}" stroke="#fff" stroke-opacity=".6" stroke-width="2.2"/>
    <ellipse cx="${x-65}" cy="${y0+h-8}" rx="22" ry="12" fill="#15181a" stroke="#8b949a" stroke-width="2"/>
    <text x="${x-65}" y="${y0+h+14}" font-size="10" fill="#c9ced1" text-anchor="middle" font-family="sans-serif">escape</text>
  </g>`;
}
/* ---------- portalevas (5): soporte del árbol de levas con los balancines, encima de la culata ---------- */
const PL=[450,318];
function artePortalevas(){
  const [x,y]=PL,P=`M${x-70} ${y-14} L${x+70} ${y-14} L${x+70} ${y+16} L${x-70} ${y+16} Z`;
  return `<g filter="url(#hcSombra)">
    ${extruir(P,36,5,"#6b747a")}
    <path d="${P}" fill="url(#hcAlum)" stroke="#23282b" stroke-width="1.5"/>
    ${[-58,58].map(d=>`<rect x="${x+d-12}" y="${y-24}" width="24" height="40" rx="5" fill="url(#hcAlum)" stroke="#23282b"/>`).join("")}
    <circle cx="${x-24}" cy="${y+1}" r="12" fill="#2b3034" stroke="#8b949a" stroke-width="2"/>
    <circle cx="${x+24}" cy="${y+1}" r="12" fill="#2b3034" stroke="#8b949a" stroke-width="2"/>
    <path d="M${x-62} ${y-13} L${x+62} ${y-13}" stroke="#fff" stroke-opacity=".6" stroke-width="2"/>
  </g>`;
}
/* ---------- bujía (11): de lado, entra inclinada en la culata ---------- */
function arteBujia(){
  const x=360,y=262;
  return `<g filter="url(#hcSombra)" transform="rotate(20 ${x} ${y+40})">
    <rect x="${x-3}" y="${y-8}" width="6" height="10" rx="1.5" fill="url(#hcAcero)" stroke="#2b3135"/>
    <rect x="${x-6}" y="${y}" width="12" height="28" rx="3" fill="url(#hcCeram)" stroke="#8a9196"/>
    <path d="M${x-6} ${y+8} L${x+6} ${y+8} M${x-6} ${y+14} L${x+6} ${y+14} M${x-6} ${y+20} L${x+6} ${y+20}" stroke="#9aa1a6" stroke-width="1"/>
    <rect x="${x-10}" y="${y+28}" width="20" height="16" rx="1.5" fill="url(#hcAcero)" stroke="#2b3135"/>
    <path d="M${x-4} ${y+28} L${x-4} ${y+44} M${x+4} ${y+28} L${x+4} ${y+44}" stroke="#2b3135" stroke-opacity=".6"/>
    <rect x="${x-6}" y="${y+44}" width="12" height="20" fill="url(#hcAcero)" stroke="#2b3135"/>
    <path d="M${x-6} ${y+48} L${x+6} ${y+50} M${x-6} ${y+54} L${x+6} ${y+56} M${x-6} ${y+60} L${x+6} ${y+62}" stroke="#4b5256"/>
    <path d="M${x-1} ${y+64} L${x-1} ${y+70} M${x+4} ${y+64} L${x+4} ${y+70} L${x+1} ${y+70}" stroke="#c9ced1" stroke-width="1.6" fill="none"/>
  </g>`;
}
/* ---------- tubo de admisión (9): brida con dos tornillos y boca hacia el carburador ---------- */
function arteAdmision(){
  const x=600,y=381;
  return `<g filter="url(#hcSombra)">
    <path d="M${x-22} ${y-30} L${x+4} ${y-30} Q${x+14} ${y-30} ${x+14} ${y-20} L${x+14} ${y+20} Q${x+14} ${y+30} ${x+4} ${y+30} L${x-22} ${y+30} Z" fill="url(#hcNegro)" stroke="#9aa2a7" stroke-width="1.4"/>
    <path d="M${x+12} ${y-15} L${x+40} ${y-24} Q${x+48} ${y-26} ${x+48} ${y-16} L${x+48} ${y+4} Q${x+48} ${y+12} ${x+40} ${y+12} L${x+12} ${y+15} Z" fill="url(#hcNegro)" stroke="#9aa2a7" stroke-width="1.4"/>
    <ellipse cx="${x+48}" cy="${y-6}" rx="7" ry="17" fill="#15181a" stroke="#b9c0c4" stroke-width="1.6"/>
    <path d="M${x-18} ${y-26} L${x+6} ${y-26}" stroke="#fff" stroke-opacity=".45" stroke-width="2"/>
  </g>`;
}
/* ---------- guías de válvula (3 escape, 4 admisión): tubitos de bronce metidos a presión; armadas no se ven ---------- */
function arteGuia(x,y){
  return `<g class="esq-oculto-arm" filter="url(#hcSombra)">
    <rect x="${x-5}" y="${y-22}" width="10" height="44" rx="2" fill="url(#hcBronce)" stroke="#5a4320"/>
    <rect x="${x-7}" y="${y-8}" width="14" height="3" fill="#c9ced1" stroke="#4b5256" stroke-width=".8"/>
    <ellipse cx="${x}" cy="${y-22}" rx="5" ry="2" fill="#2b2216"/>
  </g>`;
}
const arteGuiaEsc=()=>arteGuia(410,350), arteGuiaAdm=()=>arteGuia(490,350);
/* ---------- cauchos de las aletas (1): bloquecitos que se meten entre las aletas para que no zumben ---------- */
function arteCauchos(){
  const bloque=(x,y)=>`<rect x="${x-7}" y="${y-18}" width="14" height="36" rx="3" fill="url(#hcCaucho)" stroke="#9aa2a7" stroke-width="1"/>${[0,1,2,3].map(k=>`<rect x="${x-4}" y="${y-13+k*8}" width="8" height="3" fill="#0d0f10"/>`).join("")}`;
  return `<g filter="url(#hcSombra)">${bloque(522,402)}${bloque(548,410)}</g>`;
}
/* ---------- empaque de la culata (8): lámina metálica, vista de canto en perspectiva con el hueco del cilindro ---------- */
function arteEmpaque(){
  const x=450,y=459;
  return `<g filter="url(#hcSombra)">
    <path d="M${x-120} ${y+8} L${x+120} ${y+8} L${x+150} ${y-12} L${x-90} ${y-12} Z" fill="url(#hcAcero)" stroke="#2b3135" stroke-width="1.2"/>
    <ellipse cx="${x+15}" cy="${y-2}" rx="62" ry="7" fill="#1a1d20" stroke="#c9ced1" stroke-width="1.4"/>
    <path d="M${x-120} ${y+8} L${x+120} ${y+8} L${x+120} ${y+11} L${x-120} ${y+11} Z" fill="#5a6166"/>
  </g>`;
}

const C1=[235,350], R1=34, L1=120;
const leva1=(cx,cy)=>`M${cx-12} ${cy} A12 12 0 0 1 ${cx+12} ${cy} L${cx+5} ${cy+22} A5.5 5.5 0 0 1 ${cx-5} ${cy+22} Z`;
const TIEMPOS=[["Admisión","#4f8fc0"],["Compresión","#2f6aa0"],["Fuerza","#f08a24"],["Escape","#7a7f84"]];
const FN_SVG=`<svg id="fn" viewBox="0 0 900 440" role="img" aria-labelledby="fnTit">
  <title id="fnTit">Corte del cilindro y la culata con los cuatro tiempos: el cigüeñal gira, el pistón sube y baja, las levas abren las válvulas de admisión y de escape por turnos, la bujía hace la chispa y las aletas pasan el calor al aire; a la derecha, el ángulo del cigüeñal de 0 a 720° y la punta de la bujía</title>
  <style>
    @keyframes esqhfluye{to{stroke-dashoffset:-30}}
    .esq-fh-agua{stroke-dasharray:8 22;animation:esqhfluye 1s linear infinite;transition:opacity .6s}
    #fh-chispa,#fh-chispa2,#fh-gap,#fh-portA,#fh-portE{transition:opacity .25s}
    @media(max-width:700px){#fh-der{transform:translate(-480px,430px)}}
    @media(prefers-reduced-motion:reduce){.esq-fh-agua{animation:none!important}}
  </style>
  <defs>
    <linearGradient id="fhAcero" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9ecee"/><stop offset=".5" stop-color="#9aa2a7"/><stop offset="1" stop-color="#5a6166"/></linearGradient>
    <linearGradient id="fhAlum" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e2e6e8"/><stop offset=".45" stop-color="#a7afb4"/><stop offset=".75" stop-color="#c6ccd0"/><stop offset="1" stop-color="#626a6f"/></linearGradient>
    <linearGradient id="fhAlumOsc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9ba3a8"/><stop offset="1" stop-color="#40474b"/></linearGradient>
    <linearGradient id="fhCeram" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#dfe2e4"/><stop offset="1" stop-color="#a9afb3"/></linearGradient>
    <linearGradient id="fhCorte" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2125"/><stop offset="1" stop-color="#101417"/></linearGradient>
    <linearGradient id="fhPiston" x1="0" x2="1"><stop offset="0" stop-color="#6c7479"/><stop offset=".5" stop-color="#dfe3e5"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
    <linearGradient id="fhAgua" x1="0" x2="1"><stop offset="0" stop-color="#1f5a80"/><stop offset=".5" stop-color="#4aa3d8"/><stop offset="1" stop-color="#1f5a80"/></linearGradient>
    <radialGradient id="fhLlama" cx=".5" cy="0" r="1"><stop offset="0" stop-color="#fff1b0"/><stop offset=".4" stop-color="#f08a24"/><stop offset="1" stop-color="#9c2f14"/></radialGradient>
  </defs>
  <text class="esq-fn-et esq-claro" x="14" y="30">Cilindro en corte</text>
  <!-- cilindro con aletas -->
  <rect x="128" y="138" width="214" height="166" fill="url(#fhAlumOsc)" stroke="#5a6266" stroke-width="2"/>
  <rect x="104" y="150" width="26" height="9" rx="3" fill="#9aa3a8" stroke="#5a6266"/><rect x="104" y="174" width="26" height="9" rx="3" fill="#9aa3a8" stroke="#5a6266"/><rect x="104" y="198" width="26" height="9" rx="3" fill="#9aa3a8" stroke="#5a6266"/><rect x="104" y="222" width="26" height="9" rx="3" fill="#9aa3a8" stroke="#5a6266"/><rect x="104" y="246" width="26" height="9" rx="3" fill="#9aa3a8" stroke="#5a6266"/><rect x="104" y="270" width="26" height="9" rx="3" fill="#9aa3a8" stroke="#5a6266"/>
  <rect x="340" y="150" width="26" height="9" rx="3" fill="#9aa3a8" stroke="#5a6266"/><rect x="340" y="174" width="26" height="9" rx="3" fill="#9aa3a8" stroke="#5a6266"/><rect x="340" y="198" width="26" height="9" rx="3" fill="#9aa3a8" stroke="#5a6266"/><rect x="340" y="222" width="26" height="9" rx="3" fill="#9aa3a8" stroke="#5a6266"/><rect x="340" y="246" width="26" height="9" rx="3" fill="#9aa3a8" stroke="#5a6266"/><rect x="340" y="270" width="26" height="9" rx="3" fill="#9aa3a8" stroke="#5a6266"/>
  <rect x="160" y="138" width="150" height="166" fill="url(#fhCorte)"/>
  <path class="esq-fh-agua" id="fh-aguaF" d="M96,292 L96,150 M374,150 L374,292" stroke="#f3f7fa" stroke-width="3" fill="none" opacity="0"/>
  <!-- cárter con el cigüeñal -->
  <path d="M120,304 L350,304 L350,370 Q350,412 300,412 L170,412 Q120,412 120,370 Z" fill="url(#fhAlumOsc)" stroke="#5a6266" stroke-width="2"/>
  <path d="M132,306 L338,306 L338,368 Q338,400 298,400 L172,400 Q132,400 132,368 Z" fill="url(#fhCorte)"/>
  <g id="fh-cig"><path d="M${C1[0]-48},${C1[1]} A48 48 0 0 0 ${C1[0]+48},${C1[1]} L${C1[0]+24},${C1[1]} A24 24 0 0 1 ${C1[0]-24},${C1[1]} Z" fill="url(#fhAlum)" stroke="#2a2f33"/></g>
  <!-- gas en la cámara (color según el tiempo) -->
  <rect id="fh-gas" x="160" y="140" width="150" height="40" fill="#4f8fc0" opacity=".6"/>
  <!-- biela y pistón -->
  <line id="fh-biela" x1="235" y1="316" x2="235" y2="196" stroke="#a7afb4" stroke-width="13" stroke-linecap="round"/>
  <circle id="fh-muneq" cx="235" cy="316" r="10" fill="#9aa3a8" stroke="#2a2f33"/>
  <circle cx="${C1[0]}" cy="${C1[1]}" r="11" fill="url(#fhAcero)" stroke="#2a2f33"/>
  <g id="fh-piston"><rect x="164" y="166" width="142" height="54" rx="4" fill="url(#fhPiston)" stroke="#40474c"/><line x1="164" y1="176" x2="306" y2="176" stroke="#40474c"/><line x1="164" y1="183" x2="306" y2="183" stroke="#40474c"/><circle cx="235" cy="196" r="7" fill="#59646a"/></g>
  <!-- culata con los ductos, las válvulas, las levas y la bujía -->
  <path d="M112,138 L112,74 Q235,46 358,74 L358,138 Z" fill="url(#fhAlumOsc)" stroke="#9aa2a7" stroke-width="2"/>
  <path d="M112,100 L170,100 L196,136" fill="none" stroke="#101417" stroke-width="18"/>
  <path d="M358,100 L300,100 L274,136" fill="none" stroke="#101417" stroke-width="18"/>
  <path id="fh-portA" d="M112,100 L170,100 L196,136" fill="none" stroke="#4f8fc0" stroke-width="10" opacity="0"/>
  <path id="fh-portE" d="M358,100 L300,100 L274,136" fill="none" stroke="#7a7f84" stroke-width="10" opacity="0"/>
  <path class="esq-fh-agua" id="fh-aguaC" d="M140,126 Q235,96 330,126" stroke="#f3f7fa" stroke-width="5" fill="none" opacity="0"/>
  <g id="fh-vadm"><rect x="194" y="56" width="6" height="80" fill="url(#fhAcero)"/><path d="M180,140 L214,140 L203,132 L191,132 Z" fill="#c9ced1" stroke="#40474c"/></g>
  <g id="fh-vesc"><rect x="270" y="56" width="6" height="80" fill="url(#fhAcero)"/><path d="M256,140 L290,140 L279,132 L267,132 Z" fill="#c9ced1" stroke="#40474c"/></g>
  <path id="fh-levaA" d="${leva1(197,40)}" fill="url(#fhAcero)" stroke="#2a2f33"/>
  <path id="fh-levaE" d="${leva1(273,40)}" fill="url(#fhAcero)" stroke="#2a2f33"/>
  <circle cx="197" cy="40" r="4" fill="#3a4246"/><circle cx="273" cy="40" r="4" fill="#3a4246"/>
  <rect x="229" y="22" width="12" height="44" rx="3" fill="url(#fhCeram)" stroke="#9aa2a7"/>
  <rect x="226" y="66" width="18" height="16" fill="url(#fhAcero)"/><rect x="231" y="82" width="8" height="54" fill="#9aa2a7"/>
  <path id="fh-chispa" d="M235,138 L227,152 L236,149 L230,166 L246,144 L237,147 Z" fill="#ffd54a" opacity="0"/>
  <text class="esq-fn-et" x="14" y="88">Admisión</text>
  <text class="esq-fn-et" x="362" y="88">Escape</text>
  <text class="esq-fn-et" x="252" y="22">Bujía</text>
  <text class="esq-fn-et" x="296" y="50">Levas</text>
  <text class="esq-fn-et" x="4" y="320">Aletas: aire</text>
  <text class="esq-fn-et" x="346" y="232">Pistón</text>
  <text class="esq-fn-et" x="356" y="380">Cigüeñal</text>
  <g id="fh-der">
    <!-- ángulo del cigüeñal: dos vueltas = un ciclo -->
    <rect x="490" y="12" width="400" height="190" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="38">Ángulo del cigüeñal</text>
    <text class="esq-fn-et esq-claro" id="fh-ang" x="504" y="76">0°</text>
    <text class="esq-fn-et esq-claro" id="fh-fase" x="600" y="76">Admisión</text>
    ${TIEMPOS.map(([n,c],i)=>`<rect x="${504+i*93}" y="94" width="93" height="26" fill="${c}" opacity=".85" stroke="#161b1e" stroke-width="2"/>`).join("")}
    ${["Adm.","Comp.","Fuerza","Esc."].map((n,i)=>`<text class="esq-fn-et" x="${550+i*93}" y="146" text-anchor="middle">${n}</text>`).join("")}
    <g id="fh-marca"><path d="M504,90 L497,80 L511,80 Z" fill="#f2e6c8"/><line x1="504" y1="90" x2="504" y2="124" stroke="#f2e6c8" stroke-width="3"/></g>
    <text class="esq-fn-et" x="504" y="182">0°</text>
    <text class="esq-fn-et" x="690" y="182" text-anchor="middle">360°</text>
    <text class="esq-fn-et" x="876" y="182" text-anchor="end">720°</text>
    <!-- la bujía de cerca -->
    <rect x="490" y="214" width="400" height="218" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="240">La bujía, de cerca</text>
    <rect x="562" y="252" width="36" height="64" rx="6" fill="url(#fhCeram)" stroke="#9aa2a7"/>
    <path d="M550,316 L610,316 L614,334 L610,352 L550,352 L546,334 Z" fill="url(#fhAcero)" stroke="#40474c"/>
    <rect x="562" y="352" width="36" height="40" fill="url(#fhAcero)" stroke="#40474c"/>
    ${[358,366,374,382].map(y=>`<line x1="562" y1="${y}" x2="598" y2="${y+4}" stroke="#59646a" stroke-width="2"/>`).join("")}
    <rect x="576" y="392" width="8" height="12" fill="#c9ced1"/>
    <path d="M596,392 L604,392 L604,418 L572,418 L572,412 L598,412 L598,392 Z" fill="#c9ced1" stroke="#59646a"/>
    <path id="fh-gap" d="M566,404 L594,404 M566,412 L594,412" stroke="#ffd54a" stroke-width="2" opacity=".35"/>
    <path id="fh-chispa2" d="M580,404 L576,408 L583,407 L579,412" stroke="#ffd54a" stroke-width="3" fill="none" opacity="0"/>
    <text class="esq-fn-et" x="632" y="290">NGK CPR8EA-9</text>
    <text class="esq-fn-et" x="632" y="380">Separación</text>
    <text class="esq-fn-et esq-claro" x="632" y="408">0,8–0,9 mm</text>
  </g>
</svg>`;
const GAS1=a=>a<180?["#4f8fc0",.55]:a<345?["#2f6aa0",.55+.3*(a-180)/165]:a<480?["url(#fhLlama)",.9]:a<540?["#f08a24",.6]:["#7a7f84",.5];
let est1={ang:0,anim:0};
function dibujar1(ang){
  const $=id=>document.getElementById(id); if(!$("fh-cig"))return;
  const a=((ang%720)+720)%720, r=a*Math.PI/180, px=C1[0]+R1*Math.sin(r), py=C1[1]-R1*Math.cos(r);
  const pinY=py-Math.sqrt(L1*L1-Math.pow(px-C1[0],2)), top=pinY-30;
  $("fh-cig").setAttribute("transform",`rotate(${f(a)} ${C1[0]} ${C1[1]})`);
  $("fh-muneq").setAttribute("cx",f(px));$("fh-muneq").setAttribute("cy",f(py));
  $("fh-biela").setAttribute("x1",f(px));$("fh-biela").setAttribute("y1",f(py));$("fh-biela").setAttribute("y2",f(pinY));
  $("fh-piston").setAttribute("transform",`translate(0 ${f(pinY-196)})`);
  const g=$("fh-gas"),[col,op]=GAS1(a);g.setAttribute("height",f(Math.max(4,top-140)));g.setAttribute("fill",col);g.setAttribute("opacity",op);
  // levas: una vuelta cada dos del cigüeñal; la válvula baja cuando el lóbulo la empuja
  // tiempos ideales de 180°, más el cruce: la admisión empieza a abrir a 690° y el escape termina de cerrar a 20° (las dos abiertas un instante)
  const liftA=a<=180?12*Math.sin(Math.PI*a/180):a>=690?4*(a-690)/30:0, liftE=a>=540?12*Math.sin(Math.PI*(a-540)/180):a<20?4*(20-a)/20:0;
  $("fh-levaA").setAttribute("transform",`rotate(${f((a-90)/2)} 197 40)`);$("fh-levaE").setAttribute("transform",`rotate(${f((a-630)/2)} 273 40)`);
  $("fh-vadm").setAttribute("transform",`translate(0 ${f(liftA)})`);$("fh-vesc").setAttribute("transform",`translate(0 ${f(liftE)})`);
  $("fh-portA").style.opacity=liftA>1?.9:0;$("fh-portE").style.opacity=liftE>1?.9:0;
  const chispa=a>=335&&a<=365;$("fh-chispa").style.opacity=chispa?1:0;$("fh-chispa2").style.opacity=chispa?1:0;$("fh-gap").style.opacity=chispa?1:.35;
  $("fh-marca").setAttribute("transform",`translate(${f(372*a/720)} 0)`);
  $("fh-ang").textContent=Math.round(a)+"°";$("fh-fase").textContent=TIEMPOS[Math.min(3,Math.floor(a/180))][0]+(liftA>1&&liftE>1?" · cruce":"");
}
function fnAplicar(s,$){
  const quieto=matchMedia("(prefers-reduced-motion:reduce)").matches;
  ["fh-aguaF","fh-aguaC"].forEach(id=>$(id).style.opacity=s.agua?1:0);
  clearTimeout(est1.anim);
  const ini=est1.ang, fin=s.ang, t0=performance.now(), dur=quieto?0:Math.min(1600,300+Math.abs(fin-ini)*3);
  // temporizador y no requestAnimationFrame: así termina aunque la pestaña esté oculta
  const paso=()=>{const p=dur?Math.min(1,(performance.now()-t0)/dur):1, e=p<.5?2*p*p:1-Math.pow(-2*p+2,2)/2;est1.ang=ini+(fin-ini)*e;dibujar1(est1.ang);
    if(p<1)est1.anim=setTimeout(paso,16)};
  paso();
}
return {defs:DEFS,arteCulata,artePortalevas,arteBujia,arteAdmision,arteGuiaEsc,arteGuiaAdm,arteCauchos,arteEmpaque,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
