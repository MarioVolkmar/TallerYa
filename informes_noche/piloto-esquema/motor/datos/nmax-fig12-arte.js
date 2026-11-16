/* Arte de la lámina 12 de la NMAX 155 (variador, correa y clutch): dibujos propios de TallerYa.
   Vista «caballera»: las caras de las poleas se ven de frente (círculos) y la profundidad del eje
   va hacia arriba a la derecha (vector B). Cada función recibe (x,y) = centro de su cara de adelante;
   las posiciones salen de datos/nmax-fig12.json (piezas[].args), así el despiece solo traslada.
   Exporta las funciones que nombra el JSON, las defs y «Cómo funciona» con aplicar(s,$). */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["nmax-fig12"]=(function(){
"use strict";
const B=[0.5,-0.32];                       // un milímetro hacia adentro del motor, en pantalla
const BL=Math.hypot(B[0],B[1]), N=[-B[1]/BL,B[0]/BL];   // normal del eje en pantalla
const f=n=>Math.round(n*10)/10;
const atras=(x,y,d)=>[x+B[0]*d,y+B[1]*d];
const F=[300,400], RC=[610,385];            // centros de las poleas en el plano de la correa (z=0)

/* ---------- ayudas de dibujo ---------- */
// cilindro o disco: cara de atrás, costado (casco) y cara de adelante
function cil(x,y,r,d,cara,lado,extra=""){
  const [bx,by]=atras(x,y,d), nx=N[0]*r, ny=N[1]*r;
  return `<circle cx="${f(bx)}" cy="${f(by)}" r="${r}" fill="${lado}"/>
  <path d="M${f(x+nx)} ${f(y+ny)} L${f(bx+nx)} ${f(by+ny)} L${f(bx-nx)} ${f(by-ny)} L${f(x-nx)} ${f(y-ny)} Z" fill="${lado}"/>
  <circle cx="${f(x)}" cy="${f(y)}" r="${r}" fill="${cara}" ${extra}/>`;
}
const aro=(x,y,r,ri)=>`M${f(x+r)} ${f(y)} A${r} ${r} 0 1 0 ${f(x-r)} ${f(y)} A${r} ${r} 0 1 0 ${f(x+r)} ${f(y)} Z M${f(x+ri)} ${f(y)} A${ri} ${ri} 0 1 1 ${f(x-ri)} ${f(y)} A${ri} ${ri} 0 1 1 ${f(x+ri)} ${f(y)} Z`;
// arandela o anillo con espesor
function anillo(x,y,r,ri,d,cara,lado){
  let s="";for(let k=d;k>0;k-=1.5){const [bx,by]=atras(x,y,k);s+=`<path d="${aro(bx,by,r,ri)}" fill="${lado}" fill-rule="evenodd"/>`}
  return s+`<path d="${aro(x,y,r,ri)}" fill="${cara}" fill-rule="evenodd" stroke="#1b2023" stroke-width=".8"/>`;
}
const junta=(dx,dy,s)=>`<g class="esq-junta" style="--jx:${f(-dx*.66)}px;--jy:${f(-dy*.66)}px">${s}</g>`;
function hexa(cx,cy,r,rot=0){let p=[];for(let i=0;i<6;i++){const a=(i*60+rot)*Math.PI/180;p.push(f(cx+r*Math.cos(a))+","+f(cy+r*Math.sin(a)))}return p.join(" ")}
function tuerca(x,y,r,d){
  let s="";for(let k=d;k>0;k-=1.5){const [bx,by]=atras(x,y,k);s+=`<polygon points="${hexa(bx,by,r,15)}" fill="#3e464b"/>`}
  return s+`<polygon points="${hexa(x,y,r,15)}" fill="url(#cvAcero)" stroke="#262c30" stroke-width="1"/><circle cx="${f(x)}" cy="${f(y)}" r="${f(r*.62)}" fill="#20262a"/><circle cx="${f(x)}" cy="${f(y)}" r="${f(r*.62)}" fill="url(#cvRosca)" opacity=".7"/>`;
}
// trayecto de una correa entre dos círculos (tangentes exteriores)
function correaD(c1,r1,c2,r2){
  const dx=c2[0]-c1[0], dy=c2[1]-c1[1], d=Math.hypot(dx,dy), t=Math.atan2(dy,dx), p=Math.acos((r1-r2)/d);
  const P=(c,r,a)=>f(c[0]+r*Math.cos(a))+" "+f(c[1]+r*Math.sin(a));
  return `M${P(c1,r1,t+p)} L${P(c2,r2,t+p)} A${r2} ${r2} 0 ${2*p>Math.PI?1:0} 0 ${P(c2,r2,t-p)} L${P(c1,r1,t-p)} A${r1} ${r1} 0 ${2*p>Math.PI?0:1} 0 ${P(c1,r1,t+p)} Z`;
}

/* ---------- definiciones ---------- */
const DEFS=`
<radialGradient id="gFondo" cx="48%" cy="48%" r="70%"><stop offset="0" stop-color="#232c2f"/><stop offset="1" stop-color="#111517"/></radialGradient>
<radialGradient id="cvCono" cx="42%" cy="40%" r="62%"><stop offset="0" stop-color="#f2f4f5"/><stop offset=".35" stop-color="#c3c9cd"/><stop offset=".7" stop-color="#8c959a"/><stop offset="1" stop-color="#d4d9dc"/></radialGradient>
<radialGradient id="cvConoOsc" cx="42%" cy="40%" r="62%"><stop offset="0" stop-color="#b9c0c4"/><stop offset=".45" stop-color="#7b858b"/><stop offset=".8" stop-color="#4f585e"/><stop offset="1" stop-color="#9aa3a8"/></radialGradient>
<linearGradient id="cvLado" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5d666b"/><stop offset="1" stop-color="#262c30"/></linearGradient>
<linearGradient id="cvAcero" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef0f1"/><stop offset=".5" stop-color="#a7aeb2"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
<linearGradient id="cvCromo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6f8f9"/><stop offset=".35" stop-color="#a3abb0"/><stop offset=".55" stop-color="#eef1f2"/><stop offset="1" stop-color="#5d656a"/></linearGradient>
<linearGradient id="cvAlum" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d9dde0"/><stop offset=".5" stop-color="#9ea6ab"/><stop offset="1" stop-color="#5f676c"/></linearGradient>
<radialGradient id="cvCampana" cx="38%" cy="36%" r="70%"><stop offset="0" stop-color="#8a9297"/><stop offset=".55" stop-color="#4a5257"/><stop offset="1" stop-color="#262b2f"/></radialGradient>
<linearGradient id="cvCaucho" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3a3a3a"/><stop offset="1" stop-color="#101010"/></linearGradient>
<linearGradient id="cvPlast" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f0e2c4"/><stop offset="1" stop-color="#a8977a"/></linearGradient>
<linearGradient id="cvRodillo" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4b4f53"/><stop offset=".5" stop-color="#22262a"/><stop offset="1" stop-color="#0f1214"/></linearGradient>
<pattern id="cvFric" width="7" height="7" patternUnits="userSpaceOnUse"><rect width="7" height="7" fill="#4e4035"/><circle cx="1.6" cy="2" r=".9" fill="#7a6553"/><circle cx="5" cy="5.2" r=".8" fill="#2c231c"/><circle cx="5.4" cy="1.4" r=".5" fill="#9a8570"/></pattern>
<pattern id="cvRosca" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="3" fill="#2a3034"/><line x1="0" y1="0" x2="3" y2="3" stroke="#59646a" stroke-width=".8"/></pattern>
<pattern id="cvEstrias" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="#5d666b"/><rect width="2" height="4" fill="#2f363a"/></pattern>
<filter id="cvSombra" x="-20%" y="-20%" width="150%" height="150%"><feDropShadow dx="4" dy="7" stdDeviation="5" flood-color="#000" flood-opacity=".55"/></filter>
`;
/* ---------- contexto: tapa de la CVT (otra lámina) ---------- */
function arteTapa(){
  const d="M150 300 Q150 250 200 245 L470 228 Q560 214 650 236 Q752 262 760 340 Q768 440 690 492 Q620 530 520 520 L250 530 Q160 532 150 470 Z";
  return `<g class="esq-ctx esq-ctx-barra" data-ctx="tapa">
    <path d="${d}" fill="#b9c2c7" fill-opacity=".05" stroke="#c9bfa7" stroke-opacity=".5" stroke-width="1.6" stroke-dasharray="7 5" pointer-events="visibleStroke"/>
    <text class="esq-ctx-txt" x="170" y="238">Tapa de la CVT (otra lámina)</text>
  </g>`;
}

/* ---------- trasera: polea fija (12) con su eje ---------- */
function artePoleaFijaTr(x,y){
  const [hx,hy]=atras(x,y,-72);
  return `<g filter="url(#cvSombra)">
    ${cil(x,y,108,12,"url(#cvConoOsc)","url(#cvLado)")}
    <circle cx="${x}" cy="${y}" r="98" fill="none" stroke="#fff" stroke-opacity=".08" stroke-width="10"/>
    <path d="M${x-80} ${y-62} A100 100 0 0 1 ${x+30} ${y-100}" fill="none" stroke="#fff" stroke-opacity=".25" stroke-width="7" stroke-linecap="round"/>
    ${cil(hx,hy,18,72,"url(#cvCromo)","#7b858b")}
    <circle cx="${f(hx)}" cy="${f(hy)}" r="10" fill="url(#cvEstrias)"/>
    ${[0,1,2].map(k=>{const [px,py]=atras(hx,hy,18+k*14);return `<circle cx="${f(px+N[0]*17)}" cy="${f(py+N[1]*17)}" r="3.4" fill="url(#cvAcero)" stroke="#2b3135" stroke-width=".8"/>`}).join("")}
  </g>`;
}

/* ---------- correa (25) ---------- */
function arteCorrea(fx,fy,rx,ry,rf,rr){
  const d=correaD([fx,fy],rf,[rx,ry],rr), [bx,by]=atras(0,0,22);
  return `<g>
    <path d="${d}" transform="translate(${f(bx)} ${f(by)})" fill="none" stroke="#0b0b0b" stroke-width="12" stroke-linejoin="round"/>
    <path d="${d}" transform="translate(${f(bx/2)} ${f(by/2)})" fill="none" stroke="#151515" stroke-width="12" stroke-linejoin="round"/>
    <path d="${d}" fill="none" stroke="url(#cvCaucho)" stroke-width="12" stroke-linejoin="round"/>
    <path d="${d}" fill="none" stroke="#000" stroke-width="5" stroke-dasharray="3 3" transform="translate(${f(bx/2)} ${f(by/2)})" opacity=".8"/>
    <path d="${d}" fill="none" stroke="#e8e2d0" stroke-opacity=".55" stroke-width="1" stroke-dasharray="26 140"/>
    <text x="${f((fx+rx)/2)}" y="${f(Math.min(fy-rf,ry-rr)+30)}" font-family="Archivo" font-size="8" font-weight="700" fill="#e8e2d0" fill-opacity=".55" text-anchor="middle" letter-spacing="1">V-BELT</text>
  </g>`;
}

/* ---------- trasera: polea móvil (13) y sus pequeñas ---------- */
function artePoleaMovTr(x,y){
  const [hx,hy]=atras(x,y,-18);
  let s=`<g filter="url(#cvSombra)">${cil(x,y,108,10,"url(#cvConoOsc)","url(#cvLado)")}
    <circle cx="${x}" cy="${y}" r="70" fill="none" stroke="#000" stroke-opacity=".2" stroke-width="2"/>
    <path d="M${x-86} ${y-50} A100 100 0 0 1 ${x+20} ${y-98}" fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="7" stroke-linecap="round"/>
    ${cil(hx,hy,34,18,"url(#cvAlum)","#4f585e")}
    <circle cx="${f(hx)}" cy="${f(hy)}" r="19" fill="#22282c"/>`;
  // ranuras inclinadas del cuello: la leva de torque (los pasadores 16, fijos en el eje de la polea 12, asoman por ellas)
  for(let k=0;k<3;k++){const a=(k*120-30)*Math.PI/180, cx=hx+27*Math.cos(a), cy=hy+27*Math.sin(a);
    s+=`<rect x="${f(cx-7)}" y="${f(cy-2.6)}" width="14" height="5.2" rx="2.6" fill="#1a1f22" transform="rotate(${k*120+30} ${f(cx)} ${f(cy)})"/>`}
  return s+`</g>`;
}
const arteOrings=(x,y)=>`<g>${anillo(x+8,y-5,19,16,2,"#1d1d1d","#0a0a0a")}${anillo(x-8,y+5,19,16,2,"#262626","#0a0a0a")}</g>`;
/* ---------- asiento del resorte de torque (19); el resorte (18) sale de la biblioteca ---------- */
const arteAsiento=(x,y)=>`<g>${anillo(x,y,44,22,4,"url(#cvAcero)","#4f585e")}<circle cx="${x}" cy="${y}" r="36" fill="none" stroke="#3a4246" stroke-width="1.2"/></g>`;
function arteSeguro(x,y,r){return `<g><path d="M${f(x+r*Math.cos(1.2))} ${f(y+r*Math.sin(1.2))} A${r} ${r} 0 1 1 ${f(x+r*Math.cos(1.94))} ${f(y+r*Math.sin(1.94))}" fill="none" stroke="#2a3034" stroke-width="5.5" stroke-linecap="round"/><path d="M${f(x+r*Math.cos(1.2))} ${f(y+r*Math.sin(1.2))} A${r} ${r} 0 1 1 ${f(x+r*Math.cos(1.94))} ${f(y+r*Math.sin(1.94))}" fill="none" stroke="url(#cvAcero)" stroke-width="3" stroke-linecap="round"/></g>`}

/* ---------- clutch: portazapatas (7), zapatas (8), pasadores (9), resortes (10), seguros (11), placa (20) ---------- */
const ANG_Z=[-90,30,150];                      // posición de las tres zapatas
function arteCarrier(x,y){
  let lobos="";ANG_Z.forEach(g=>{const a=(g+60)*Math.PI/180;lobos+=`<circle cx="${f(x+52*Math.cos(a))}" cy="${f(y+52*Math.sin(a))}" r="26"/>`});
  let s=`<g filter="url(#cvSombra)">`;
  for(let k=8;k>0;k-=2){const [bx,by]=atras(x,y,k);s+=`<g transform="translate(${f(bx-x)} ${f(by-y)})" fill="#30373b"><circle cx="${x}" cy="${y}" r="56"/>${lobos}</g>`}
  s+=`<g fill="url(#cvAlum)" stroke="#2b3135" stroke-width="1"><circle cx="${x}" cy="${y}" r="56"/>${lobos}</g>`;
  s+=`<circle cx="${x}" cy="${y}" r="56" fill="url(#cvAlum)"/><circle cx="${x}" cy="${y}" r="22" fill="#2b3135"/><circle cx="${x}" cy="${y}" r="14" fill="url(#cvEstrias)"/>`;
  ANG_Z.forEach(g=>{const a=(g+60)*Math.PI/180;s+=`<circle cx="${f(x+62*Math.cos(a))}" cy="${f(y+62*Math.sin(a))}" r="6" fill="#1d2225" stroke="#9aa3a8"/>`});
  return s+`</g>`;
}
function zapata(x,y,g){                        // una zapata con su forro, girada g grados
  const ri=58, ro=82, a0=-46, a1=46, P=(r,a)=>{const t=(g+a)*Math.PI/180;return f(x+r*Math.cos(t))+" "+f(y+r*Math.sin(t))};
  const cuerpo=`M${P(ri,a0)} A${ri} ${ri} 0 0 1 ${P(ri,a1)} L${P(76,a1)} A76 76 0 0 0 ${P(76,a0)} Z`;
  const forro=`M${P(76,a0+6)} A76 76 0 0 1 ${P(76,a1-2)} L${P(ro,a1-4)} A${ro} ${ro} 0 0 0 ${P(ro,a0+8)} Z`;
  return `<path d="${cuerpo}" fill="url(#cvAlum)" stroke="#2b3135" stroke-width="1"/><path d="${forro}" fill="url(#cvFric)" stroke="#2b2119" stroke-width=".8"/><circle cx="${P(66,a0+12).split(" ")[0]}" cy="${P(66,a0+12).split(" ")[1]}" r="5" fill="#1d2225"/>`;
}
function arteZapatas(x,y){let s="";ANG_Z.forEach(g=>{const [bx,by]=atras(x,y,6);s+=`<g opacity=".7" transform="translate(${f(bx-x)} ${f(by-y)})">${zapata(x,y,g).replace(/url\(#cv(Alum|Fric)\)/g,"#2b3135")}</g>`+zapata(x,y,g)});return `<g filter="url(#cvSombra)">${s}</g>`}
function arteResZap(x,y){                       // tres resortes cortos entre las zapatas
  let s="";[-30,90,210].forEach(g=>{const t=g*Math.PI/180, cx=x+60*Math.cos(t), cy=y+60*Math.sin(t), ux=-Math.sin(t), uy=Math.cos(t);
    let d=`M${f(cx-ux*13)} ${f(cy-uy*13)}`;for(let k=1;k<=8;k++){const s2=-13+k*26/8, o=(k%2?4:-4);d+=` L${f(cx+ux*s2+Math.cos(t)*o)} ${f(cy+uy*s2+Math.sin(t)*o)}`}
    s+=junta(cx-x,cy-y,`<path d="${d}" fill="none" stroke="#1e2326" stroke-width="3.6"/><path d="${d}" fill="none" stroke="#c9a23a" stroke-width="1.8"/>`)});
  return `<g class="esq-oculto-arm">${s}</g>`;   // dentro de las zapatas: no se ve armado
}
function artePinZap(x,y){let s="";ANG_Z.forEach(g=>{const a=(g+60)*Math.PI/180;s+=junta(62*Math.cos(a),62*Math.sin(a),cil(x+62*Math.cos(a),y+62*Math.sin(a),5,14,"url(#cvAcero)","#6c7479"))});return `<g>${s}</g>`}
// amortiguadores de caucho (9): uno en cada pasador del portazapatas
function arteDamper(x,y){let s="";ANG_Z.forEach(g=>{const a=(g+60)*Math.PI/180;s+=junta(62*Math.cos(a),62*Math.sin(a),cil(x+62*Math.cos(a),y+62*Math.sin(a),8,10,"url(#cvCaucho)","#0c0c0c",'stroke="#4a4a4a" stroke-width=".8"')+'<circle cx="'+f(x+62*Math.cos(a))+'" cy="'+f(y+62*Math.sin(a))+'" r="3.4" fill="#2a3034"/>')});return `<g>${s}</g>`}
function arteClips(x,y){let s="";ANG_Z.forEach(g=>{const a=(g+60)*Math.PI/180;s+=junta(62*Math.cos(a),62*Math.sin(a),arteSeguro(x+62*Math.cos(a),y+62*Math.sin(a),6.5))});return `<g class="esq-oculto-arm">${s}</g>`}
const artePlaca20=(x,y)=>`<g>${anillo(x,y,13,6,3,"url(#cvAcero)","#4f585e")}<path d="M${x-20} ${y} L${x} ${y-12} L${x+20} ${y} L${x} ${y+12} Z" fill="url(#cvAcero)" stroke="#2b3135" stroke-width=".8" opacity=".9"/><circle cx="${x}" cy="${y}" r="6" fill="#20262a"/></g>`;

/* ---------- campana del clutch (24) ---------- */
function arteCampana(x,y){
  let s=`<g filter="url(#cvSombra)">${cil(x,y,92,36,"url(#cvCampana)","url(#cvLado)")}
    <circle cx="${x}" cy="${y}" r="86" fill="none" stroke="#1c2124" stroke-width="2"/>
    <circle cx="${x}" cy="${y}" r="78" fill="none" stroke="#fff" stroke-opacity=".06" stroke-width="8"/>`;
  for(let k=0;k<5;k++){const a=(k*72-90)*Math.PI/180;
    s+=`<ellipse cx="${f(x+50*Math.cos(a))}" cy="${f(y+50*Math.sin(a))}" rx="13" ry="8" transform="rotate(${k*72} ${f(x+50*Math.cos(a))} ${f(y+50*Math.sin(a))})" fill="#15191b"/>`;
    const b=(k*72-54)*Math.PI/180;s+=`<line x1="${f(x+26*Math.cos(b))}" y1="${f(y+26*Math.sin(b))}" x2="${f(x+80*Math.cos(b))}" y2="${f(y+80*Math.sin(b))}" stroke="#6f787d" stroke-width="3" stroke-linecap="round" opacity=".6"/>`}
  s+=`<circle cx="${x}" cy="${y}" r="22" fill="url(#cvAlum)"/><circle cx="${x}" cy="${y}" r="12" fill="url(#cvEstrias)"/>
    <path d="M${x-70} ${y-46} A84 84 0 0 1 ${x+10} ${y-84}" fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="6" stroke-linecap="round"/>`;
  return s+`</g>`;
}

/* ---------- delantera: arandela (26), rampa (3), deslizadores (4), rodillos (2) ---------- */
const ANG_R=[-90,30,150];
function arteRampa(x,y){
  let brazos="";ANG_R.forEach(g=>{const a=g*Math.PI/180, ux=Math.cos(a), uy=Math.sin(a), vx=-uy, vy=ux;
    brazos+=`<path d="M${f(x+vx*16)} ${f(y+vy*16)} L${f(x+ux*52+vx*13)} ${f(y+uy*52+vy*13)} Q${f(x+ux*60)} ${f(y+uy*60)} ${f(x+ux*52-vx*13)} ${f(y+uy*52-vy*13)} L${f(x-vx*16)} ${f(y-vy*16)} Z"/>`});
  let s=`<g filter="url(#cvSombra)">`;
  for(let k=6;k>0;k-=2){const [bx,by]=atras(x,y,k);s+=`<g transform="translate(${f(bx-x)} ${f(by-y)})" fill="#30373b"><circle cx="${x}" cy="${y}" r="30"/>${brazos}</g>`}
  s+=`<g fill="url(#cvAcero)" stroke="#2b3135" stroke-width="1"><circle cx="${x}" cy="${y}" r="30"/>${brazos}</g>`;
  // rampas de los rodillos (entre los brazos)
  [-30,90,210].forEach(g=>{const a=g*Math.PI/180;s+=`<path d="M${f(x+20*Math.cos(a-.35))} ${f(y+20*Math.sin(a-.35))} L${f(x+34*Math.cos(a))} ${f(y+34*Math.sin(a))} L${f(x+20*Math.cos(a+.35))} ${f(y+20*Math.sin(a+.35))}" fill="none" stroke="#59646a" stroke-width="2"/>`});
  return s+`<circle cx="${x}" cy="${y}" r="13" fill="url(#cvEstrias)" stroke="#2b3135"/></g>`;
}
function arteDeslizadores(x,y){let s="";ANG_R.forEach(g=>{const a=g*Math.PI/180, cx=x+55*Math.cos(a), cy=y+55*Math.sin(a);
  s+=junta(cx-x,cy-y,`<rect x="${f(cx-9)}" y="${f(cy-6)}" width="18" height="12" rx="3" fill="url(#cvPlast)" stroke="#5b5040" stroke-width="1" transform="rotate(${g+90} ${f(cx)} ${f(cy)})"/>`)});return `<g>${s}</g>`}
function arteRodillos(x,y){let s="";for(let k=0;k<6;k++){const a=(k*60-60)*Math.PI/180;s+=cil(x+42*Math.cos(a),y+42*Math.sin(a),10,15,"url(#cvRodillo)","#0c0e10",`stroke="#4b4f53" stroke-width="1"`)+`<circle cx="${f(x+42*Math.cos(a))}" cy="${f(y+42*Math.sin(a))}" r="4" fill="#9aa3a8"/>`}return `<g filter="url(#cvSombra)">${s}</g>`}

/* ---------- delantera: polea móvil (1), buje (5), polea fija con aletas (6) ---------- */
function artePoleaMov(x,y){
  return `<g filter="url(#cvSombra)">${cil(x,y,100,16,"url(#cvCono)","url(#cvLado)")}
    <circle cx="${x}" cy="${y}" r="90" fill="none" stroke="#fff" stroke-opacity=".1" stroke-width="8"/>
    <circle cx="${x}" cy="${y}" r="28" fill="#5d666b"/><circle cx="${x}" cy="${y}" r="17" fill="#20262a"/>
    <path d="M${x-78} ${y-50} A92 92 0 0 1 ${x+18} ${y-90}" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="7" stroke-linecap="round"/></g>`;
}
function artePoleaFija(x,y){
  let s=`<g filter="url(#cvSombra)">${cil(x,y,100,22,"url(#cvAlum)","url(#cvLado)")}
    <circle cx="${x}" cy="${y}" r="100" fill="url(#cvCono)" opacity=".35"/>`;
  for(let k=0;k<18;k++){const a=k*20*Math.PI/180, b=a+.32;
    const p=(r,t)=>f(x+r*Math.cos(t))+" "+f(y+r*Math.sin(t));
    s+=`<path d="M${p(36,a)} Q${p(70,a+.05)} ${p(95,b)}" fill="none" stroke="#2a3034" stroke-width="6" stroke-linecap="round" transform="translate(2.5 -1.6)"/><path d="M${p(36,a)} Q${p(70,a+.05)} ${p(95,b)}" fill="none" stroke="#c9ced1" stroke-width="3.6" stroke-linecap="round"/>`}
  s+=`<circle cx="${x}" cy="${y}" r="34" fill="url(#cvAlum)" stroke="#2b3135"/><circle cx="${x}" cy="${y}" r="20" fill="#3a4246"/><circle cx="${x}" cy="${y}" r="13" fill="url(#cvEstrias)"/>
    <circle cx="${x}" cy="${y}" r="100" fill="none" stroke="#2c3336" stroke-width="1.2"/>`;
  return s+`</g>`;
}

/* ============================================================
   «Cómo funciona»: izquierda, la correa vista de lado (variador y polea trasera);
   derecha arriba, el variador cortado (rodillos, rampa y las dos mitades);
   derecha abajo, el clutch de frente (zapatas y campana). Tacómetro arriba a la izquierda.
   En el celular la columna derecha baja debajo de la vista lateral (estilo propio del esquema).
   ============================================================ */
const VF=[120,250], VR=[355,250];
const rfDe=s=>34+s.rf*42, rrDe=s=>84-s.rf*40;
const FN_SVG=`<svg id="fn" viewBox="0 0 900 440" role="img" aria-labelledby="fnTit">
  <title id="fnTit">Esquema de la transmisión CVT: correa entre el variador y la polea trasera, el variador cortado con rodillos y rampa, y el clutch con zapatas y campana</title>
  <style>
    #cvf-movil,#cvf-correa-blq,.esq-cvf-rod,.esq-cvf-zap{transition:transform .8s cubic-bezier(.5,0,.3,1)}
    #cvf-aguja{transition:transform .8s cubic-bezier(.5,0,.3,1);transform-origin:90px 92px}
    .esq-cvf-forro{transition:fill .5s}
    @media(max-width:700px){#cvf-der{transform:translate(-470px,452px)}}
  </style>
  <defs>
    <linearGradient id="cvfMitad" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6c7479"/><stop offset=".5" stop-color="#c9ced1"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
    <linearGradient id="cvfCampana" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5d666b"/><stop offset="1" stop-color="#262c30"/></linearGradient>
    <pattern id="cvfFric" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#4d3f33"/><circle cx="1.5" cy="2" r=".8" fill="#6d5a49"/><circle cx="4.5" cy="4.6" r=".7" fill="#2f261f"/></pattern>
  </defs>
  <!-- tacómetro -->
  <g>
    <path d="M30 92 A60 60 0 0 1 150 92" fill="none" stroke="#2b3135" stroke-width="12"/>
    <path d="M128 50 A60 60 0 0 1 150 92" fill="none" stroke="#f2611d" stroke-width="12" opacity=".75"/>
    <g id="cvf-aguja"><line x1="90" y1="92" x2="90" y2="44" stroke="#f2e6c8" stroke-width="4" stroke-linecap="round"/></g>
    <circle cx="90" cy="92" r="7" fill="#9aa3a8"/>
    <text class="esq-fn-et esq-claro" id="cvf-rpm" x="90" y="124" text-anchor="middle">1.600 rpm</text>
  </g>
  <!-- vista lateral: correa entre las dos poleas -->
  <circle cx="${VF[0]}" cy="${VF[1]}" r="82" fill="#20272b" stroke="#3a4246" stroke-width="2"/>
  <circle cx="${VR[0]}" cy="${VR[1]}" r="90" fill="#20272b" stroke="#3a4246" stroke-width="2"/>
  <g class="esq-giro" id="cvf-girof"><circle cx="${VF[0]}" cy="${VF[1]}" r="80" fill="none" stroke="#3a4246" stroke-width="3" stroke-dasharray="6 18"/></g>
  <g class="esq-giro" id="cvf-giror"><circle cx="${VR[0]}" cy="${VR[1]}" r="88" fill="none" stroke="#3a4246" stroke-width="3" stroke-dasharray="6 18"/></g>
  <path id="cvf-correa" d="" fill="none" stroke="#0e0e0e" stroke-width="11" stroke-linejoin="round"/>
  <path id="cvf-correa2" d="" fill="none" stroke="#e8a92a" stroke-width="2" stroke-dasharray="10 14" class="esq-pulso" opacity=".8"/>
  <circle cx="${VF[0]}" cy="${VF[1]}" r="9" fill="#9aa3a8"/><circle cx="${VR[0]}" cy="${VR[1]}" r="9" fill="#9aa3a8"/>
  <text class="esq-fn-et esq-claro" x="${VF[0]}" y="364" text-anchor="middle">Variador</text>
  <text class="esq-fn-et" x="${VF[0]}" y="382" text-anchor="middle" data-ym="388">(adelante, motor)</text>
  <text class="esq-fn-et esq-claro" x="${VR[0]}" y="364" text-anchor="middle">Polea trasera</text>
  <text class="esq-fn-et" x="${VR[0]}" y="382" text-anchor="middle" data-ym="388">(atrás, rueda)</text>
  <text class="esq-fn-et" id="cvf-rel" x="238" y="420" text-anchor="middle" data-ym="430">Relación corta</text>
  <g id="cvf-der">
    <!-- variador cortado: mitad fija (6) a la izquierda, mitad móvil (1) a la derecha, empujada por los rodillos -->
    <rect x="500" y="12" width="390" height="202" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="514" y="34">El variador, cortado</text>
    <rect x="514" y="186" width="250" height="10" rx="5" fill="#59646a"/>
    <text class="esq-fn-et" x="770" y="196" data-ym="200">Cigüeñal</text>
    <path d="M560 186 L560 60 L586 60 L640 176 L640 186 Z" fill="url(#cvfMitad)" stroke="#2b3135"/>
    <text class="esq-fn-et" x="520" y="58" data-ym="64">Fija (6)</text>
    <g id="cvf-movil">
      <path d="M716 186 L716 60 L690 60 L644 176 L644 186 Z" fill="url(#cvfMitad)" stroke="#2b3135"/>
      <path d="M716 60 L792 70 L761 186 L716 186 Z" fill="#3a4246" stroke="#2b3135"/><path d="M792 70 L761 186" stroke="#9aa3a8" stroke-width="2"/>
      <text class="esq-fn-et" x="720" y="56" data-ym="64">Móvil (1)</text>
    </g>
    <!-- placa de atrás (3), fija y casi plana, y rodillo (2) entre ella y la rampa de la polea móvil -->
    <rect x="792" y="62" width="12" height="124" rx="2" fill="#59646a" stroke="#2b3135"/>
    <text class="esq-fn-et" x="818" y="100" data-xm="814">Placa (3)</text>
    <g class="esq-cvf-rod" id="cvf-rod"><circle cx="778" cy="168" r="12" fill="#1a1d20" stroke="#6c7479" stroke-width="2"/></g>
    <text class="esq-fn-et" x="818" y="172" data-xm="814">Rodillo (2)</text>
    <g id="cvf-correa-blq"><path d="M624 168 L660 168 L668 148 L616 148 Z" fill="#111" stroke="#e8a92a" stroke-width="1.5"/></g>
    <text class="esq-fn-et" x="600" y="210" data-ym="214" text-anchor="middle">Correa</text>
    <!-- clutch de frente: zapatas (8) en el portazapatas y la campana (24) -->
    <rect x="500" y="226" width="390" height="208" rx="10" fill="#161b1e" stroke="#2b3135"/>
    <text class="esq-fn-et esq-claro" x="514" y="248">El clutch, de frente</text>
    <g class="esq-giro esq-quieto" id="cvf-campana">
      <circle cx="660" cy="334" r="92" fill="url(#cvfCampana)"/><circle cx="660" cy="334" r="80" fill="#14181a"/>
      <circle cx="660" cy="250" r="4" fill="#f2611d"/>
    </g>
    <g class="esq-giro" id="cvf-zapatas">
      <circle cx="660" cy="334" r="80" fill="none"/>
      <circle cx="660" cy="334" r="30" fill="#59646a"/>
      ${[-90,30,150].map((g,i)=>{const t=g*Math.PI/180,P=(r,a)=>f(660+r*Math.cos(t+a))+" "+f(334+r*Math.sin(t+a));
        return `<g class="esq-cvf-zap" id="cvf-zap${i}"><path d="M${P(36,-.7)} A36 36 0 0 1 ${P(36,.7)} L${P(66,.62)} A66 66 0 0 0 ${P(66,-.62)} Z" fill="#9aa3a8" stroke="#2b3135"/><path class="esq-cvf-forro" d="M${P(66,-.6)} A66 66 0 0 1 ${P(66,.6)} L${P(74,.56)} A74 74 0 0 0 ${P(74,-.56)} Z" fill="url(#cvfFric)"/></g>`}).join("")}
    </g>
    <text class="esq-fn-et" x="770" y="290" data-ym="284" data-xm="758">Campana (24)</text>
    <text class="esq-fn-et" x="770" y="308" data-ym="310" data-xm="758">va con la rueda</text>
    <text class="esq-fn-et" x="770" y="384" data-ym="378" data-xm="758">Zapatas (8)</text>
    <text class="esq-fn-et" x="770" y="402" data-ym="404" data-xm="758">van con la polea</text>
    <text class="esq-fn-et esq-claro" id="cvf-estado" x="514" y="424" data-ym="426">Suelto: la rueda no gira</text>
  </g>
</svg>`;
let anim=null, actual={rf:0};
function fnAplicar(s,$){
  const quieto=matchMedia("(prefers-reduced-motion:reduce)").matches;
  // tacómetro (0 a 10.000 rpm en 180°)
  $("cvf-aguja").style.transform=`rotate(${f(-90+180*Math.min(1,s.rpm/10000))}deg)`;
  $("cvf-rpm").textContent=s.rpm.toLocaleString("es-CO")+" rpm";
  $("cvf-rel").textContent=s.rel;
  // variador cortado: el rodillo sube por la rampa de la polea móvil, apoyado en la placa fija; la móvil se acerca y la correa sube
  $("cvf-movil").style.transform=`translate(${f(-s.rf*26)}px,0)`;
  $("cvf-correa-blq").style.transform=`translate(${f(-s.rf*13)}px,${f(-s.rf*86)}px)`;
  $("cvf-rod").style.transform=`translate(0px,${f(-s.rf*86)}px)`;
  // clutch: las zapatas salen por fuerza centrífuga
  [-90,30,150].forEach((g,i)=>{const t=g*Math.PI/180;$("cvf-zap"+i).style.transform=`translate(${f(Math.cos(t)*s.zap*6)}px,${f(Math.sin(t)*s.zap*6)}px)`;
    $("cvf-zap"+i).querySelector(".esq-cvf-forro").setAttribute("fill",s.agarra?"#f2611d":"url(#cvfFric)")});
  $("cvf-estado").textContent=s.estado;
  const vel=(id,v)=>{const e=$(id);e.classList.remove("esq-lento","esq-quieto");if(v)e.classList.add("esq-"+v)};
  vel("cvf-girof",s.motor);vel("cvf-giror",s.rueda==="quieto"?s.motor:s.polea);vel("cvf-zapatas",s.polea);vel("cvf-campana",s.rueda);
  // correa vista de lado: se recalcula el trayecto. Temporizador y no requestAnimationFrame: así termina aunque la pestaña esté oculta o sin ventana
  clearTimeout(anim);
  const ini=actual.rf, fin=s.rf, t0=performance.now(), dur=quieto?0:800;
  const paso=()=>{const p=dur?Math.min(1,(performance.now()-t0)/dur):1, e=p<.5?2*p*p:1-Math.pow(-2*p+2,2)/2, rf=ini+(fin-ini)*e;actual.rf=rf;
    const d=correaD(VF,rfDe({rf}),VR,rrDe({rf}));$("cvf-correa").setAttribute("d",d);$("cvf-correa2").setAttribute("d",d);
    if(p<1)anim=setTimeout(paso,16)};
  paso();
}
return {defs:DEFS,arteAsiento,arteCampana,arteCarrier,arteClips,arteCorrea,arteDamper,arteDeslizadores,arteOrings,artePinZap,artePlaca20,artePoleaFija,artePoleaFijaTr,artePoleaMov,artePoleaMovTr,arteRampa,arteResZap,arteRodillos,arteTapa,arteZapatas,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
