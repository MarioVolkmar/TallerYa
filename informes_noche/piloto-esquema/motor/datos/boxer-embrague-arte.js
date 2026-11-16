/* Arte de la lámina 14 de la Bajaj Boxer CT100 (clutch de discos en el cigüeñal): dibujos propios de TallerYa.
   Vista «caballera» como la CVT: las caras de las piezas se ven de frente (círculos) y la profundidad del eje
   del cigüeñal va hacia arriba a la izquierda (vector B), así el despiece baja a la derecha como en el plano.
   Cada función recibe (x,y) = centro de su cara de adelante; las posiciones salen de datos/boxer-embrague.json. */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["boxer-embrague"]=(function(){
"use strict";
const B=[-0.5,-0.32];
const BL=Math.hypot(B[0],B[1]), N=[-B[1]/BL,B[0]/BL];
const f=n=>Math.round(n*10)/10;
const atras=(x,y,d)=>[x+B[0]*d,y+B[1]*d];
const rad=g=>g*Math.PI/180;

/* ---------- ayudas ---------- */
function cil(x,y,r,d,cara,lado,extra=""){
  const [bx,by]=atras(x,y,d), nx=N[0]*r, ny=N[1]*r;
  return `<circle cx="${f(bx)}" cy="${f(by)}" r="${r}" fill="${lado}" stroke="#1b2023" stroke-width=".8"/>
  <path d="M${f(x+nx)} ${f(y+ny)} L${f(bx+nx)} ${f(by+ny)} L${f(bx-nx)} ${f(by-ny)} L${f(x-nx)} ${f(y-ny)} Z" fill="${lado}"/>
  <circle cx="${f(x)}" cy="${f(y)}" r="${r}" fill="${cara}" ${extra}/>`;
}
// contorno dentado (corona): n dientes entre r1 y r2
function dentado(x,y,n,r1,r2){
  let d="";for(let i=0;i<n;i++){const a=rad(i*360/n), da=rad(360/n);
    const p=[[r1,a],[r2,a+da*.18],[r2,a+da*.5],[r1,a+da*.68]];
    p.forEach(([r,t],k)=>{d+=(i===0&&k===0?"M":"L")+f(x+r*Math.cos(t))+" "+f(y+r*Math.sin(t))+" "})}
  return d+"Z";
}
// espesor de un contorno: copias hacia atrás sin borde y borde solo en la del fondo
function extruir(d,t,fill){const n=Math.max(2,Math.round(t/4));let r=`<path d="${d}" transform="translate(${f(B[0]*t)} ${f(B[1]*t)})" fill="${fill}" stroke="#1b2023" stroke-width="1"/>`;
  for(let i=n-1;i>=1;i--)r+=`<path d="${d}" transform="translate(${f(B[0]*t*i/n)} ${f(B[1]*t*i/n)})" fill="${fill}"/>`;return r}

const DEFS=`
<radialGradient id="gFondo" cx="48%" cy="48%" r="70%"><stop offset="0" stop-color="#232c2f"/><stop offset="1" stop-color="#111517"/></radialGradient>
<linearGradient id="bxLado" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5d666b"/><stop offset="1" stop-color="#262c30"/></linearGradient>
<linearGradient id="bxAcero" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef0f1"/><stop offset=".5" stop-color="#a7aeb2"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
<linearGradient id="bxCromo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6f8f9"/><stop offset=".35" stop-color="#a3abb0"/><stop offset=".55" stop-color="#eef1f2"/><stop offset="1" stop-color="#5d656a"/></linearGradient>
<linearGradient id="bxAlum" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d9dde0"/><stop offset=".5" stop-color="#9ea6ab"/><stop offset="1" stop-color="#5f676c"/></linearGradient>
<radialGradient id="bxCampana" cx="38%" cy="36%" r="70%"><stop offset="0" stop-color="#8a9297"/><stop offset=".55" stop-color="#4a5257"/><stop offset="1" stop-color="#262b2f"/></radialGradient>
<linearGradient id="bxPlast" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f0e2c4"/><stop offset="1" stop-color="#a8977a"/></linearGradient>
<pattern id="bxFric" width="7" height="7" patternUnits="userSpaceOnUse"><rect width="7" height="7" fill="#6b5442"/><circle cx="1.6" cy="2" r=".9" fill="#9a8068"/><circle cx="5" cy="5.2" r=".8" fill="#3c2f25"/><circle cx="5.4" cy="1.4" r=".5" fill="#b49a80"/></pattern>
<pattern id="bxRosca" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="3" fill="#2a3034"/><line x1="0" y1="0" x2="3" y2="3" stroke="#59646a" stroke-width=".8"/></pattern>
<pattern id="bxEstrias" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="#5d666b"/><rect width="2" height="4" fill="#2f363a"/></pattern>
<filter id="bxSombra" x="-20%" y="-20%" width="150%" height="150%"><feDropShadow dx="4" dy="7" stdDeviation="5" flood-color="#000" flood-opacity=".55"/></filter>
`;

/* ---------- corona del clutch (1): canasta abierta hacia ti y piñón de dientes atrás ---------- */
function arteCorona(x,y){
  const [gx,gy]=atras(x,y,40);
  let s=`<g filter="url(#bxSombra)">${extruir(dentado(gx,gy,58,98,110),8,"#3d454a")}
    <path d="${dentado(gx,gy,58,98,110)}" fill="url(#bxAcero)" stroke="#262c30" stroke-width=".8"/>
    <circle cx="${f(gx)}" cy="${f(gy)}" r="92" fill="#2f363a"/>
    ${cil(x,y,96,38,"url(#bxCampana)","url(#bxLado)")}
    <circle cx="${x}" cy="${y}" r="86" fill="#14181a"/>`;
  // ventanas de la canasta: ahí entran las orejas de los discos de fricción
  for(let k=0;k<6;k++){const a=rad(k*60+15), ux=Math.cos(a), uy=Math.sin(a);
    s+=`<rect x="${f(x+ux*91-6)}" y="${f(y+uy*91-6)}" width="12" height="12" rx="2" fill="#0b0e0f" transform="rotate(${k*60+15} ${f(x+ux*91)} ${f(y+uy*91)})"/>`}
  const [fx,fy]=atras(x,y,30);
  s+=`<circle cx="${f(fx)}" cy="${f(fy)}" r="30" fill="#2a3135"/><circle cx="${f(fx)}" cy="${f(fy)}" r="16" fill="#0e1113"/>
    <path d="M${x-72} ${y-46} A86 86 0 0 1 ${x+6} ${y-88}" fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="6" stroke-linecap="round"/>`;
  return s+`</g>`;
}

/* ---------- manzana (8): disco con estrías por fuera, torres de los resortes y estrías del cigüeñal ---------- */
function arteManzana(x,y){
  let s=`<g filter="url(#bxSombra)">${extruir(dentado(x,y,40,62,67),14,"#4a5257")}
    <path d="${dentado(x,y,40,62,67)}" fill="url(#bxAlum)" stroke="#2b3135" stroke-width=".8"/>
    <circle cx="${x}" cy="${y}" r="54" fill="none" stroke="#3a4246" stroke-width="2"/>`;
  for(let k=0;k<6;k++){const a=rad(k*60), cx=x+32*Math.cos(a), cy=y+32*Math.sin(a);
    s+=`${cil(cx,cy,9,-6,"#c3c9cd","#59646a")}<circle cx="${f(cx)}" cy="${f(cy)}" r="3.5" fill="#20262a"/>`}
  s+=`<circle cx="${x}" cy="${y}" r="17" fill="url(#bxAcero)"/><circle cx="${x}" cy="${y}" r="10" fill="url(#bxEstrias)"/>
    <path d="M${x-48} ${y-30} A56 56 0 0 1 ${x+4} ${y-58}" fill="none" stroke="#fff" stroke-opacity=".3" stroke-width="5" stroke-linecap="round"/>`;
  return s+`</g>`;
}

/* ---------- leva interna (14): eje que cruza la tapa, con la leva arriba y el brazo del cable abajo ---------- */
function arteLeva(x,y){
  const x2=x+46, y2=y+120;
  return `<g filter="url(#bxSombra)">
    <rect x="${f(x2-10)}" y="${f(y2-6)}" width="56" height="13" rx="6" fill="url(#bxAcero)" stroke="#262c30" transform="rotate(28 ${f(x2-10)} ${f(y2)})"/>
    <circle cx="${f(x2+38)}" cy="${f(y2+26)}" r="5" fill="#20262a"/>
    <line x1="${x}" y1="${y}" x2="${x2}" y2="${y2}" stroke="#262c30" stroke-width="15" stroke-linecap="round"/>
    <line x1="${x}" y1="${y}" x2="${x2}" y2="${y2}" stroke="url(#bxCromo)" stroke-width="11" stroke-linecap="round"/>
    <path d="M${f(x-9)} ${f(y-2)} L${f(x+7)} ${f(y-8)} L${f(x+10)} ${f(y+6)} Z" fill="#59646a"/>
    <rect x="${f(x+18)} " y="${f(y+56)}" width="6" height="12" fill="#1a1d20" transform="rotate(-21 ${f(x+21)} ${f(y+62)})"/>
    <rect x="${f(x-14)}" y="${f(y+60)}" width="70" height="40" fill-opacity="0" pointer-events="all"/>
  </g>`;
}

/* ---------- «Cómo funciona»: corte del clutch (izquierda) y la corona con el piñón de la caja (derecha) ---------- */
const CY=170;   // eje del cigüeñal en el corte
function discos(){
  let s="";
  for(let i=0;i<4;i++){const xf=150+i*22;   // fricción: orejas hasta la canasta
    s+=`<g class="esq-bxf-d" data-i="${i}" style="transition:transform .6s"><rect x="${xf}" y="${CY-96}" width="7" height="192" rx="2" fill="url(#bxfFric)" stroke="#2b2119"/></g>`;}
  for(let i=0;i<4;i++){const xm=161+i*22;   // metálicos: dientes hacia la manzana
    s+=`<g class="esq-bxf-d" data-i="${i+.5}" style="transition:transform .6s"><rect x="${xm}" y="${CY-80}" width="5" height="160" fill="#b8bfc3" stroke="#4f585e"/></g>`;}
  return s;
}
const FN_SVG=`<svg id="fn" viewBox="0 0 900 320" role="img" aria-labelledby="fnTit">
  <title id="fnTit">Corte del clutch de la Boxer: canasta de la corona, discos, manzana, resortes y el mando que los separa; a la derecha, la corona moviendo el piñón de la caja</title>
  <defs>
    <pattern id="bxfFric" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#6b5442"/><circle cx="1.5" cy="2" r=".8" fill="#9a8068"/></pattern><pattern id="bxEstriasF" width="16" height="6" patternUnits="userSpaceOnUse"><rect width="16" height="6" fill="#8c959a"/><rect width="16" height="3" fill="#4f585e"/></pattern>
  </defs>
  <!-- cigüeñal -->
  <rect x="10" y="${CY-9}" width="300" height="18" rx="3" fill="#59646a"/>
  <text class="esq-fn-et" x="14" y="${CY+34}">Cigüeñal</text>
  <!-- corona (1): canasta en corte, gira loca sobre su buje -->
  <g id="bxf-corona" style="transition:opacity .4s">
    <path d="M118 ${CY-112} L270 ${CY-112} L270 ${CY-102} L130 ${CY-102} L130 ${CY+102} L270 ${CY+102} L270 ${CY+112} L118 ${CY+112} Z" fill="#59646a" stroke="#2b3135"/>
    <rect x="104" y="${CY-124}" width="16" height="248" fill="url(#bxEstriasF)" stroke="#2b3135"/>
    <rect x="118" y="${CY-16}" width="14" height="32" fill="#3a4246"/>
  </g>
  <text class="esq-fn-et esq-claro" x="80" y="${CY-132}" text-anchor="middle" data-xm="96">Corona</text>
  <!-- placa de presión (5) y lo que se mueve con el mando -->
  <g id="bxf-mueve" style="transition:transform .6s">
    <rect x="136" y="${CY-84}" width="10" height="168" fill="#8c959a" stroke="#2b3135"/>
    <rect x="146" y="${CY-60}" width="140" height="5" fill="#4f585e"/><rect x="146" y="${CY+55}" width="140" height="5" fill="#4f585e"/>
    <rect x="284" y="${CY-70}" width="9" height="140" fill="#c3c9cd" stroke="#2b3135"/>
    <rect x="293" y="${CY-14}" width="14" height="28" rx="3" fill="#9aa3a8" stroke="#2b3135"/>
  </g>
  ${discos()}
  <!-- manzana (8), fija al cigüeñal -->
  <rect x="242" y="${CY-82}" width="16" height="164" fill="#aeb5b9" stroke="#2b3135"/>
  <!-- resortes (9): entre la manzana y la placa de los resortes -->
  <g id="bxf-res"><path id="bxf-res1" d="" fill="none" stroke="#e8a92a" stroke-width="3"/><path id="bxf-res2" d="" fill="none" stroke="#e8a92a" stroke-width="3"/></g>
  <text class="esq-fn-et" x="244" y="${CY-118}" text-anchor="middle">Manzana</text>
  <text class="esq-fn-et" x="160" y="${CY+132}" text-anchor="middle" data-ym="${CY+130}">Discos</text>
  <text class="esq-fn-et" x="296" y="${CY+100}" data-ym="${CY+98}">Resortes</text>
  <!-- impulsor (13) y leva (14) -->
  <g id="bxf-imp" style="transition:transform .6s"><rect x="309" y="${CY-5}" width="44" height="10" rx="3" fill="#c3c9cd" stroke="#2b3135"/></g>
  <g id="bxf-leva" style="transition:transform .6s;transform-origin:372px ${CY}px"><rect x="356" y="${CY-30}" width="32" height="60" rx="10" fill="#59646a" stroke="#2b3135"/><rect x="368" y="${CY+20}" width="8" height="70" fill="#9aa3a8"/></g>
  <path id="bxf-cable" d="M372 ${CY+92} L450 ${CY+100}" stroke="#e8a92a" stroke-width="3" fill="none"/>
  <text class="esq-fn-et" x="336" y="${CY-48}" text-anchor="middle">Leva</text>
  <text class="esq-fn-et" x="400" y="${CY+128}" text-anchor="middle" data-ym="${CY+126}">Cable</text>
  <!-- derecha: la corona de frente moviendo el piñón de la caja, y la palanca -->
  <g id="fnCorte">
    <rect x="490" y="44" width="400" height="266" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="68">Corona y caja, de frente</text>
    <circle cx="600" cy="204" r="74" fill="#3a4246" stroke="#6c7479" stroke-width="2"/>
    <g class="esq-giro" id="bxf-gcor"><circle cx="600" cy="204" r="70" fill="none" stroke="#b8bfc3" stroke-width="7" stroke-dasharray="5 6"/></g>
    <circle cx="704" cy="204" r="32" fill="#3a4246" stroke="#6c7479" stroke-width="2"/>
    <g class="esq-giro" id="bxf-gcaja"><circle cx="704" cy="204" r="29" fill="none" stroke="#b8bfc3" stroke-width="7" stroke-dasharray="5 6"/></g>
    <text class="esq-fn-et" x="600" y="300" text-anchor="middle">Corona</text>
    <text class="esq-fn-et" x="704" y="260" text-anchor="middle">Caja</text>
    <text class="esq-fn-et" id="bxf-marcha" x="704" y="284" text-anchor="middle">Neutro</text>
    <!-- palanca: cuánto la aprietas -->
    <rect x="790" y="96" width="22" height="160" rx="6" fill="#20272b" stroke="#3a4246"/>
    <rect id="bxf-barra" x="792" y="254" width="18" height="0" rx="4" fill="#f2611d" style="transition:all .6s"/>
    <text class="esq-fn-et" x="801" y="86" text-anchor="middle">Palanca</text>
    <text class="esq-fn-et esq-claro" id="bxf-pct" x="801" y="284" text-anchor="middle">0 %</text>
    <text class="esq-fn-et esq-claro" id="bxf-estado" x="504" y="96">Pegado: todo gira junto</text>
    <text class="esq-fn-et esq-claro" id="bxf-luz" x="504" y="124">Luz entre discos: 0 mm</text>
  </g>
</svg>`;
function fnAplicar(s,$){
  const L=s.palanca;                       // 0 = suelta, 1 = apretada a fondo
  const g=f(-10*L);                       // la placa de presión se va hacia el motor
  $("bxf-mueve").style.transform=`translate(${g}px,0)`;
  $("bxf-imp").style.transform=`translate(${g}px,0)`;
  $("bxf-leva").style.transform=`rotate(${f(-18*L)}deg)`;
  document.querySelectorAll("#fn .esq-bxf-d").forEach(e=>{const i=+e.dataset.i;e.style.transform=`translate(${f(-L*(3.5-i)*2.4)}px,0)`;
    const r=e.querySelector("rect");if(r&&r.getAttribute("height")==="192")r.setAttribute("stroke",s.patina?"#f2611d":"#2b2119");});
  // resortes: se comprimen cuando aprietas
  const x0=258, x1=f(284+g), paso=(x1-x0)/8;
  [CY-40,CY+40].forEach((yy,k)=>{let d=`M${x0} ${yy}`;for(let i=1;i<=8;i++)d+=` L${f(x0+paso*i)} ${yy+(i%2?-7:7)}`;$("bxf-res"+(k+1)).setAttribute("d",d)});
  $("bxf-luz").textContent=`Luz entre discos: ${s.luz}`;
  $("bxf-barra").setAttribute("height",f(156*L));$("bxf-barra").setAttribute("y",f(254-156*L));
  $("bxf-pct").textContent=Math.round(L*100)+" %";
  $("bxf-marcha").textContent=s.marcha;$("bxf-marcha").setAttribute("fill",s.marcha==="Neutro"?"#9aa3a8":"#f2611d");$("bxf-gcaja").querySelector("circle").setAttribute("stroke",s.marcha==="Neutro"?"#b8bfc3":"#e8a92a");$("bxf-estado").textContent=s.estado;
  const vel=(id,v)=>{const e=$(id);e.classList.remove("esq-lento","esq-quieto");if(v)e.classList.add("esq-"+v)};
  vel("bxf-gcor",s.corona);vel("bxf-gcaja",s.caja);
}
return {defs:DEFS,arteCorona,arteLeva,arteManzana,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
