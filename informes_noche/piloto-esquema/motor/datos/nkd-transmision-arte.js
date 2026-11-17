/* Arte de la figura F-8 de la AKT NKD 125 CBS 2025 (rueda trasera y transmisión final): dibujos propios de TallerYa.
   Vista desde el lado izquierdo (el de la cadena), en «caballera»: las caras redondas se ven de frente y la profundidad
   del eje va hacia arriba a la derecha (vector B): el freno de tambor queda detrás de la rueda.
   Cada función recibe (x,y) = centro de su cara de adelante; las posiciones salen de datos/nkd-transmision.json. */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["nkd-transmision"]=(function(){
"use strict";
const B=[0.5,-0.32];
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
function dentado(x,y,n,r1,r2){
  let d="";for(let i=0;i<n;i++){const a=rad(i*360/n), da=rad(360/n);
    const p=[[r1,a],[r2,a+da*.2],[r2,a+da*.48],[r1,a+da*.68]];
    p.forEach(([r,t],k)=>{d+=(i===0&&k===0?"M":"L")+f(x+r*Math.cos(t))+" "+f(y+r*Math.sin(t))+" "})}
  return d+"Z";
}
function aro(x,y,r1,r2){ // anillo (dona) que no tapa su centro
  return `M${f(x-r2)} ${y} A${r2} ${r2} 0 1 0 ${f(x+r2)} ${y} A${r2} ${r2} 0 1 0 ${f(x-r2)} ${y} Z M${f(x-r1)} ${y} A${r1} ${r1} 0 1 1 ${f(x+r1)} ${y} A${r1} ${r1} 0 1 1 ${f(x-r1)} ${y} Z`;
}
function extruir(d,t,fill){const n=Math.max(2,Math.round(t/4));let r=`<path d="${d}" fill-rule="evenodd" transform="translate(${f(B[0]*t)} ${f(B[1]*t)})" fill="${fill}" stroke="#1b2023" stroke-width="1"/>`;
  for(let i=n-1;i>=1;i--)r+=`<path d="${d}" fill-rule="evenodd" transform="translate(${f(B[0]*t*i/n)} ${f(B[1]*t*i/n)})" fill="${fill}"/>`;return r}

const DEFS=`
<radialGradient id="gFondo" cx="48%" cy="48%" r="70%"><stop offset="0" stop-color="#232c2f"/><stop offset="1" stop-color="#111517"/></radialGradient>
<linearGradient id="ntLado" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5d666b"/><stop offset="1" stop-color="#262c30"/></linearGradient>
<linearGradient id="ntAcero" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef0f1"/><stop offset=".5" stop-color="#a7aeb2"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
<linearGradient id="ntCromo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6f8f9"/><stop offset=".35" stop-color="#a3abb0"/><stop offset=".55" stop-color="#eef1f2"/><stop offset="1" stop-color="#5d656a"/></linearGradient>
<linearGradient id="ntNegro" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5a6266"/><stop offset=".5" stop-color="#2c3236"/><stop offset="1" stop-color="#16191b"/></linearGradient>
<radialGradient id="ntCaucho" cx="40%" cy="38%" r="70%"><stop offset="0" stop-color="#4a4f52"/><stop offset="1" stop-color="#1a1d1f"/></radialGradient>
<linearGradient id="ntPlast" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f0e2c4"/><stop offset="1" stop-color="#a8977a"/></linearGradient>
<linearGradient id="ntDorado" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f3d27a"/><stop offset=".5" stop-color="#c4952f"/><stop offset="1" stop-color="#7a5a17"/></linearGradient>
<pattern id="ntFric" width="7" height="7" patternUnits="userSpaceOnUse"><rect width="7" height="7" fill="#6b5442"/><circle cx="1.6" cy="2" r=".9" fill="#9a8068"/><circle cx="5" cy="5.2" r=".8" fill="#3c2f25"/></pattern>
<pattern id="ntRosca" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="3" fill="#2a3034"/><line x1="0" y1="0" x2="3" y2="3" stroke="#59646a" stroke-width=".8"/></pattern>
<pattern id="ntEstrias" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="#5d666b"/><rect width="2" height="4" fill="#2f363a"/></pattern>
<linearGradient id="ntAlumP" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d9dde0"/><stop offset="1" stop-color="#5f676c"/></linearGradient>
<filter id="ntSombra" x="-20%" y="-20%" width="150%" height="150%"><feDropShadow dx="4" dy="7" stdDeviation="5" flood-color="#000" flood-opacity=".55"/></filter>
`;

/* ---------- contexto: brazo izquierdo de la tijera (fig. F-14), del piñón a la punta donde va el tensor ---------- */
function arteTijera(){
  return `<g opacity=".8"><path d="M250 236 L548 248 L556 270 L250 262 Z" fill="#20272b" stroke="#4b555a" stroke-width="1.5"/>
    <path d="M520 247 L572 249 L572 272 L520 270 Z" fill="#283034" stroke="#4b555a"/>
    <text x="300" y="285" fill="#7c878c" font-size="15" font-family="Barlow, sans-serif">Tijera (fig. F-14)</text></g>`;
}

/* ---------- eje de la rueda (1): se ve la punta; el resto atraviesa la rueda hacia atrás ---------- */
function arteEje(x,y){
  const [bx,by]=atras(x,y,150);
  return `<g filter="url(#ntSombra)"><line x1="${x}" y1="${y}" x2="${f(bx)}" y2="${f(by)}" stroke="url(#ntCromo)" stroke-width="14" stroke-linecap="round"/>
    <line x1="${f(x+N[0]*4)}" y1="${f(y+N[1]*4)}" x2="${f(bx+N[0]*4)}" y2="${f(by+N[1]*4)}" stroke="#fff" stroke-opacity=".35" stroke-width="2"/>
    <line x1="${x}" y1="${y}" x2="${f(x+B[0]*24)}" y2="${f(y+B[1]*24)}" stroke="url(#ntRosca)" stroke-width="14"/>
    <circle cx="${x}" cy="${y}" r="7" fill="#c9cfd2" stroke="#3a4246"/></g>`;
}

/* ---------- tensor (23): bloque cuadrado en la punta de la tijera, con su tornillo de ajuste hacia adelante ---------- */
function arteTensor(x,y){
  return `<g filter="url(#ntSombra)">${extruir(`M${x-13} ${y-13} H${x+13} V${y+13} H${x-13} Z`,8,"#3d454a")}
    <rect x="${x-13}" y="${y-13}" width="26" height="26" rx="3" fill="url(#ntAcero)" stroke="#2b3135"/>
    <circle cx="${x}" cy="${y}" r="7" fill="#14181a"/>
    <rect x="${x-52}" y="${y-4}" width="40" height="8" fill="url(#ntRosca)" stroke="#2b3135" stroke-width=".6"/>
    <rect x="${x-34}" y="${y-7}" width="8" height="14" fill="#9aa3a8" stroke="#2b3135"/>
    <path d="M${x-8} ${y+13} v5 M${x} ${y+13} v8 M${x+8} ${y+13} v5" stroke="#f2611d" stroke-width="1.6"/></g>`;
}

/* ---------- campana (12): manzana de la rueda con sus dos pestañas de radios y el tambor del freno atrás ---------- */
function arteCampana(x,y){
  const [tx,ty]=atras(x,y,34);
  let s=`<g filter="url(#ntSombra)">${cil(tx,ty,46,16,"url(#ntNegro)","url(#ntLado)")}
    ${cil(x,y,30,34,"url(#ntNegro)","url(#ntLado)")}
    <circle cx="${x}" cy="${y}" r="26" fill="none" stroke="#6c7479" stroke-width="1.5"/>`;
  for(let k=0;k<6;k++){const a=rad(k*60+30);s+=`<rect x="${f(x+18*Math.cos(a)-4)}" y="${f(y+18*Math.sin(a)-4)}" width="8" height="8" rx="1.5" fill="#0d1012" transform="rotate(${k*60+30} ${f(x+18*Math.cos(a))} ${f(y+18*Math.sin(a))})"/>`}
  return s+`<circle cx="${x}" cy="${y}" r="9" fill="#14181a"/></g>`;
}
/* ---------- radios (13): 36 rayos cruzados del cubo al rin ---------- */
function arteRadios(x,y){
  let d="";for(let k=0;k<36;k++){const a=rad(k*10), b=rad(k*10+(k%2?28:-28));
    d+=`M${f(x+30*Math.cos(a))} ${f(y+30*Math.sin(a))} L${f(x+98*Math.cos(b))} ${f(y+98*Math.sin(b))} `}
  return `<path d="${d}" stroke="#b8bfc3" stroke-width="1.6" fill="none" opacity=".85"/>`;
}
/* ---------- rin (14) ---------- */
function arteRin(x,y){
  return `<g>${extruir(aro(x,y,98,108),10,"#22282b")}<path d="${aro(x,y,98,108)}" fill-rule="evenodd" fill="url(#ntNegro)" stroke="#6c7479" stroke-width="1.2"/>
    <path d="M${x-80} ${y-62} A102 102 0 0 1 ${x+20} ${y-101}" fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="3"/></g>`;
}
/* ---------- neumático (25): el tubo de caucho que va adentro de la llanta ---------- */
function arteNeumatico(x,y){
  return `<g><path d="${aro(x,y,106,116)}" fill-rule="evenodd" fill="#3a2f2a" stroke="#6b5a50" stroke-width="1"/>
    <rect x="${x-3}" y="${y+100}" width="6" height="16" fill="#9aa3a8"/></g>`;
}
/* ---------- llanta (26): la de afuera, con el labrado ---------- */
function arteLlanta(x,y){
  let s=`<g filter="url(#ntSombra)">${extruir(aro(x,y,106,128),14,"#151819")}<path d="${aro(x,y,106,128)}" fill-rule="evenodd" fill="url(#ntCaucho)" stroke="#5a6064" stroke-width="1.2"/>`;
  for(let k=0;k<40;k++){const a=rad(k*9);s+=`<line x1="${f(x+120*Math.cos(a))}" y1="${f(y+120*Math.sin(a))}" x2="${f(x+128*Math.cos(a+.05))}" y2="${f(y+128*Math.sin(a+.05))}" stroke="#0a0b0c" stroke-width="3"/>`}
  return s+`</g>`;
}

/* ---------- porta sprocket (17): la pieza que lleva la corona y entra en la campana sobre los cauchos ---------- */
function artePortaSprocket(x,y){
  let s=`<g filter="url(#ntSombra)">${cil(x,y,40,12,"url(#ntNegro)","url(#ntLado)")}`;
  for(let k=0;k<4;k++){const a=rad(k*90+45);s+=`<circle cx="${f(x+33*Math.cos(a))}" cy="${f(y+33*Math.sin(a))}" r="3.5" fill="#0d1012"/>`}
  return s+`<circle cx="${x}" cy="${y}" r="14" fill="#14181a" stroke="#59646a"/><circle cx="${x}" cy="${y}" r="7" fill="#0b0d0e"/></g>`;
}
/* ---------- corona (20): 38 dientes ---------- */
function arteCorona(x,y){
  const d=dentado(x,y,38,54,61);
  let s=`<g filter="url(#ntSombra)">${extruir(d,5,"#3d454a")}<path d="${d}" fill="url(#ntAcero)" stroke="#262c30" stroke-width=".8"/>
    <circle cx="${x}" cy="${y}" r="44" fill="#262c30"/>`;
  for(let k=0;k<4;k++){const a=rad(k*90);s+=`<ellipse cx="${f(x+28*Math.cos(a))}" cy="${f(y+28*Math.sin(a))}" rx="9" ry="13" fill="#111416" transform="rotate(${k*90} ${f(x+28*Math.cos(a))} ${f(y+28*Math.sin(a))})"/>`}
  return s+`<circle cx="${x}" cy="${y}" r="18" fill="#14181a"/></g>`;
}
/* ---------- cadena y piñón de salida (20): la cadena abraza la corona y el piñón de 15 dientes del motor ---------- */
function arteCadena(x,y,px,py){
  const R=60, r=24, dx=x-px, dy=y-py, L=Math.hypot(dx,dy), ux=dx/L, uy=dy/L, a=Math.asin((R-r)/L);
  const nx1=-uy*Math.cos(a)-ux*Math.sin(a), ny1=ux*Math.cos(a)-uy*Math.sin(a);   // normal tramo de arriba
  const nx2=uy*Math.cos(a)-ux*Math.sin(a), ny2=-ux*Math.cos(a)-uy*Math.sin(a);   // normal tramo de abajo
  const P=(cx,cy,rr,nx,ny)=>[f(cx+rr*nx),f(cy+rr*ny)];
  const [a1x,a1y]=P(px,py,r,nx1,ny1),[b1x,b1y]=P(x,y,R,nx1,ny1),[a2x,a2y]=P(px,py,r,nx2,ny2),[b2x,b2y]=P(x,y,R,nx2,ny2);
  const d=`M${a1x} ${a1y} L${b1x} ${b1y} A${R} ${R} 0 1 1 ${b2x} ${b2y} L${a2x} ${a2y} A${r} ${r} 0 0 1 ${a1x} ${a1y} Z`;
  const pin=dentado(px,py,15,19,25);
  return `<g filter="url(#ntSombra)"><path d="${pin}" fill="url(#ntAcero)" stroke="#262c30" stroke-width=".8"/><circle cx="${px}" cy="${py}" r="9" fill="url(#ntEstrias)"/>
    <path d="${d}" fill="none" stroke="#14181a" stroke-width="9"/><path d="${d}" fill="none" stroke="url(#ntDorado)" stroke-width="6" stroke-dasharray="5 3"/>
    <path d="${d}" fill="none" stroke="#000" stroke-opacity="0" stroke-width="16" pointer-events="stroke"/></g>`;
}
/* ---------- cauchos de la campana (15): seis tacos que amortiguan el tirón de la cadena ---------- */
function arteCauchos(x,y){
  let s=`<g>`;for(let k=0;k<6;k++){const a=k*60+30, cx=x+22*Math.cos(rad(a)), cy=y+22*Math.sin(rad(a));
    s+=`<rect x="${f(cx-7)}" y="${f(cy-9)}" width="14" height="18" rx="4" fill="url(#ntCaucho)" stroke="#5a6064" transform="rotate(${a} ${f(cx)} ${f(cy)})"/>`}
  return s+`</g>`;
}
/* ---------- portabandas (3): el plato del freno, del lado derecho ---------- */
function artePortaBandas(x,y){
  return `<g filter="url(#ntSombra)">${cil(x,y,48,10,"url(#ntAlumP)","url(#ntLado)")}
    <circle cx="${x}" cy="${y}" r="48" fill="url(#ntAcero)" opacity=".55"/>
    <circle cx="${x}" cy="${y}" r="12" fill="#14181a"/><circle cx="${x}" cy="${y-30}" r="6" fill="#262c30"/>
    <rect x="${x+30}" y="${y+16}" width="34" height="12" rx="5" fill="#59646a" stroke="#2b3135"/></g>`;
}
/* ---------- bandas (8): las dos zapatas con su forro ---------- */
function arteBandas(x,y){
  const z=(s)=>`<path d="M${x-36} ${y+s*4} A36 36 0 0 ${s>0?0:1} ${x+36} ${y+s*4} L${x+28} ${y+s*4} A28 28 0 0 ${s>0?1:0} ${x-28} ${y+s*4} Z" fill="url(#ntAcero)" stroke="#2b3135"/>
    <path d="M${x-36} ${y+s*4} A36 36 0 0 ${s>0?0:1} ${x+36} ${y+s*4} L${x+32} ${y+s*4} A32 32 0 0 ${s>0?1:0} ${x-32} ${y+s*4} Z" fill="url(#ntFric)"/>`;
  return `<g filter="url(#ntSombra)">${z(-1)}${z(1)}</g>`;
}
/* ---------- leva (4): brazo que gira el eje abrebandas cuando tiras de la varilla del freno ---------- */
function arteLeva(x,y){
  return `<g filter="url(#ntSombra)"><path d="M${x-8} ${y-6} L${x+52} ${y+30} L${x+46} ${y+40} L${x-10} ${y+8} Z" fill="url(#ntAcero)" stroke="#2b3135"/>
    <circle cx="${x}" cy="${y}" r="10" fill="url(#ntAcero)" stroke="#2b3135"/><circle cx="${x}" cy="${y}" r="5" fill="url(#ntEstrias)"/>
    <circle cx="${x+48}" cy="${y+34}" r="3" fill="#14181a"/></g>`;
}
/* ---------- indicador de desgaste (6): flecha sobre el eje abrebandas ---------- */
function arteIndicador(x,y){
  return `<g><path d="M${x-6} ${y-6} L${x+6} ${y-6} L${x+3} ${y+18} L${x} ${y+24} L${x-3} ${y+18} Z" fill="#f2611d" stroke="#2b3135"/><circle cx="${x}" cy="${y}" r="5" fill="#14181a"/></g>`;
}

/* ---------- «Cómo funciona» ---------- */
const CY=160;
const FN_SVG=`<svg id="fn" viewBox="0 0 900 320" role="img" aria-labelledby="fnTit">
  <title id="fnTit">Transmisión final de la NKD 125 de lado: el piñón del motor tira de la cadena por arriba y mueve la corona de la rueda; a la derecha, los cauchos de la campana y las marcas de los tensores</title>
  <defs><linearGradient id="ntfOro" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#f3d27a"/><stop offset="1" stop-color="#c4952f"/></linearGradient></defs>
  <circle cx="330" cy="${CY}" r="96" fill="#2a3135" stroke="#59646a" stroke-width="2"/>
  <g class="esq-giro" id="ntf-gcor"><circle cx="330" cy="${CY}" r="88" fill="none" stroke="#b8bfc3" stroke-width="9" stroke-dasharray="6 6"/></g>
  <circle cx="330" cy="${CY}" r="30" fill="#14181a" stroke="#59646a"/>
  <circle cx="80" cy="${CY}" r="36" fill="#2a3135" stroke="#59646a" stroke-width="2"/>
  <g class="esq-giro" id="ntf-gpin"><circle cx="80" cy="${CY}" r="30" fill="none" stroke="#b8bfc3" stroke-width="8" stroke-dasharray="5 5"/></g>
  <path id="ntf-arriba" d="M80 ${CY-36} L330 ${CY-96}" stroke="url(#ntfOro)" stroke-width="7" fill="none"/>
  <path id="ntf-abajo" d="" stroke="url(#ntfOro)" stroke-width="7" fill="none"/>
  <rect x="150" y="${CY+60}" width="120" height="10" rx="4" fill="#59646a" id="ntf-desl"/>
  <text class="esq-fn-et" x="80" y="${CY+70}" text-anchor="middle">Piñón</text>
  <text class="esq-fn-et" x="80" y="${CY+94}" text-anchor="middle">(motor)</text>
  <text class="esq-fn-et" x="330" y="${CY+122}" text-anchor="middle" data-ym="${CY+120}">Corona (rueda)</text>
  <text class="esq-fn-et" x="190" y="${CY-82}" text-anchor="middle" id="ntf-etarr">Cadena</text>
  <text class="esq-fn-et esq-claro" x="330" y="${CY+7}" text-anchor="middle" id="ntf-rpm">0</text>
  <g id="fnCorte">
    <rect x="490" y="44" width="400" height="266" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="504" y="68">Campana por dentro</text>
    <circle cx="590" cy="190" r="62" fill="#262c30" stroke="#6c7479" stroke-width="2"/>
    <circle cx="590" cy="190" r="16" fill="#0d1012"/>
    <g id="ntf-cauchos"></g>
    <text class="esq-fn-et" x="590" y="282" text-anchor="middle">Cauchos</text>
    <text class="esq-fn-et esq-claro" x="760" y="100" text-anchor="middle">Tensores</text>
    <rect x="700" y="130" width="50" height="14" fill="#3a4246"/><rect x="770" y="130" width="50" height="14" fill="#3a4246"/>
    <path d="M705 128v-6M715 128v-6M725 128v-6M735 128v-6M745 128v-6M775 128v-6M785 128v-6M795 128v-6M805 128v-6M815 128v-6" stroke="#9aa3a8" stroke-width="1.5"/>
    <path id="ntf-mi" d="" fill="#f2611d"/><path id="ntf-md" d="" fill="#f2611d"/>
    <text class="esq-fn-et" x="725" y="170" text-anchor="middle">Izq.</text><text class="esq-fn-et" x="795" y="170" text-anchor="middle">Der.</text>
    <text class="esq-fn-et esq-claro" id="ntf-juego" x="680" y="214">Juego: correcto</text>
    <text class="esq-fn-et esq-claro" id="ntf-estado" x="680" y="244">Moto quieta</text>
  </g>
</svg>`;
function fnAplicar(s,$){
  const juego={ok:22,flojo:58,tenso:4}[s.juego];
  // tramo de abajo: cuelga según el juego
  $("ntf-abajo").setAttribute("d",`M80 ${CY+36} Q205 ${CY+66+juego} 330 ${CY+96}`);
  $("ntf-arriba").setAttribute("stroke",s.tiro?"#f2611d":"url(#ntfOro)");
  $("ntf-desl").setAttribute("fill",s.juego==="flojo"?"#f2611d":"#59646a");
  const vel=(id,v)=>{const e=$(id);e.classList.remove("esq-lento","esq-quieto");if(v)e.classList.add("esq-"+v)};
  vel("ntf-gcor",s.gira);vel("ntf-gpin",s.gira);
  $("ntf-rpm").textContent=s.km;
  let c="";const ap=s.tiro?(s.cauchos==="gastados"?.5:.75):1;
  for(let k=0;k<6;k++){const a=k*60+30, cx=590+40*Math.cos(rad(a)), cy=190+40*Math.sin(rad(a));
    c+=`<rect x="${f(cx-9)}" y="${f(cy-11*ap)}" width="18" height="${f(22*ap)}" rx="5" fill="${s.cauchos==="gastados"?"#7a3b2a":"#3e4447"}" stroke="#6c7479" transform="rotate(${a} ${f(cx)} ${f(cy)})"/>`}
  $("ntf-cauchos").innerHTML=c;
  const mi=s.marcas==="distintas"?735:725, md=795;
  $("ntf-mi").setAttribute("d",`M${mi-6} 156 L${mi+6} 156 L${mi} 146 Z`);$("ntf-md").setAttribute("d",`M${md-6} 156 L${md+6} 156 L${md} 146 Z`);
  $("ntf-juego").textContent="Juego: "+{ok:"correcto",flojo:"flojo",tenso:"muy tenso"}[s.juego];
  $("ntf-juego").setAttribute("fill",s.juego==="ok"?"#e8eef0":"#f2611d");
  $("ntf-estado").textContent=s.estado;
}
return {defs:DEFS,arteTijera,arteEje,arteTensor,arteCampana,arteRadios,arteRin,arteNeumatico,arteLlanta,artePortaSprocket,arteCorona,arteCadena,arteCauchos,artePortaBandas,arteBandas,arteLeva,arteIndicador,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
