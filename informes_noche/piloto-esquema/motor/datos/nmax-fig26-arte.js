/* Arte de la lámina 26 de la NMAX 155 (bombas de freno, mangueras y soportes): dibujos propios de TallerYa.
   Vista desde el puesto del piloto: la bomba delantera va en el manubrio derecho y la trasera en el izquierdo.
   Exporta las funciones que nombra datos/nmax-fig26.json, las defs y el esquema de «Cómo funciona». */
window.ESQ_ARTE=window.ESQ_ARTE||{};
ESQ_ARTE["nmax-fig26"]=(function(){
"use strict";
const f=n=>Math.round(n*10)/10;
// origen de cada bomba (centro de la abrazadera sobre el manubrio); s=1 derecha (delantera), s=-1 izquierda (trasera)
const O={1:[770,175],"-1":[330,175]};
const G=s=>`translate(${O[s][0]} ${O[s][1]}) scale(${s} 1)`;
const ATRAS=[3,-5];
function extruir(d,pasos,fill,k=1){let r="";for(let i=pasos;i>=1;i--)r+=`<path d="${d}" transform="translate(${f(ATRAS[0]*i*k/pasos)} ${f(ATRAS[1]*i*k/pasos)})" fill="${fill}"/>`;return r}
// curva suave por los puntos (Catmull-Rom → Bézier)
function suave(p){let d=`M${p[0][0]},${p[0][1]}`;for(let i=0;i<p.length-1;i++){const a=p[i-1]||p[i],b=p[i],c=p[i+1],e=p[i+2]||c;
  d+=` C${f(b[0]+(c[0]-a[0])/6)},${f(b[1]+(c[1]-a[1])/6)} ${f(c[0]-(e[0]-b[0])/6)},${f(c[1]-(e[1]-b[1])/6)} ${c[0]},${c[1]}`}return d}

const DEFS=`
<linearGradient id="b26Cuerpo" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5b6268"/><stop offset=".45" stop-color="#33393e"/><stop offset="1" stop-color="#1a1d20"/></linearGradient>
<linearGradient id="b26Lado" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#121416"/><stop offset="1" stop-color="#25292d"/></linearGradient>
<linearGradient id="b26Tapa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4a5055"/><stop offset=".5" stop-color="#25292c"/><stop offset="1" stop-color="#141618"/></linearGradient>
<linearGradient id="b26Alum" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#eef0f1"/><stop offset=".4" stop-color="#a9b0b4"/><stop offset=".6" stop-color="#d7dbde"/><stop offset="1" stop-color="#6e767b"/></linearGradient>
<linearGradient id="b26Acero" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef0f1"/><stop offset=".5" stop-color="#a7aeb2"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
<linearGradient id="b26Cromo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6f8f9"/><stop offset=".35" stop-color="#a3abb0"/><stop offset=".55" stop-color="#eef1f2"/><stop offset="1" stop-color="#5d656a"/></linearGradient>
<linearGradient id="b26Cobre" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f0b98a"/><stop offset=".5" stop-color="#c27a45"/><stop offset="1" stop-color="#7d4522"/></linearGradient>
<linearGradient id="b26Caucho" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a3a3a"/><stop offset=".5" stop-color="#1c1c1c"/><stop offset="1" stop-color="#0c0c0c"/></linearGradient>
<linearGradient id="b26Chapa" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8e969b"/><stop offset=".5" stop-color="#596166"/><stop offset="1" stop-color="#363c40"/></linearGradient>
<linearGradient id="b26Puno" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2c2c2c"/><stop offset=".5" stop-color="#151515"/><stop offset="1" stop-color="#070707"/></linearGradient>
<pattern id="b26Rosca" width="4" height="12" patternUnits="userSpaceOnUse"><rect width="4" height="12" fill="#a7aeb2"/><line x1="0" y1="0" x2="0" y2="12" stroke="#5e666b" stroke-width="1.6"/></pattern>
<pattern id="b26Grano" width="5" height="5" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".6" fill="#fff" opacity=".07"/><circle cx="3.5" cy="3" r=".5" fill="#000" opacity=".18"/></pattern>
<filter id="b26Sombra" x="-20%" y="-20%" width="150%" height="150%"><feDropShadow dx="4" dy="7" stdDeviation="5" flood-color="#000" flood-opacity=".55"/></filter>
<mask id="b26mBarra" maskUnits="userSpaceOnUse" x="0" y="0" width="1100" height="900"><rect width="1100" height="900" fill="#fff"/><rect x="190" y="160" width="720" height="30" fill="#000"/></mask>
`;

/* ---------- contexto: manubrio con puños y unidad ABS (otras láminas) ---------- */
function arteManubrio(){
  const puno=(x0,x1)=>{let r=`<rect x="${x0}" y="157" width="${x1-x0}" height="36" rx="16" fill="url(#b26Puno)"/>`;
    for(let x=x0+10;x<x1-6;x+=9)r+=`<line x1="${x}" y1="160" x2="${x}" y2="190" stroke="#2f2f2f" stroke-width="2"/>`;return r};
  return `<g class="esq-ctx">
    <rect x="186" y="${O[1][1]-13}" width="728" height="26" rx="13" fill="#3b4246"/>
    <rect x="186" y="${O[1][1]-11}" width="728" height="6" rx="3" fill="#fff" opacity=".12"/>
    ${puno(898,1012)}${puno(88,202)}
    <rect x="510" y="150" width="80" height="50" rx="10" fill="#22272b" stroke="#454c51" stroke-dasharray="4 3"/>
    <text class="esq-ctx-txt" x="550" y="214" text-anchor="middle">Manubrio</text>
  </g>`;
}
function arteABS(){
  const boca=(x,y)=>`<circle cx="${x}" cy="${y}" r="14" fill="#3a4246" stroke="#5a646a"/>`;
  return `<g class="esq-ctx" data-ctx="abs" filter="url(#b26Sombra)">
    <rect x="462" y="420" width="176" height="104" rx="10" fill="#262c30" stroke="#59646a" stroke-dasharray="5 4"/>
    <rect x="474" y="432" width="152" height="80" rx="6" fill="#30373b"/>
    ${boca(510,428)}${boca(590,428)}${boca(500,514)}${boca(600,514)}
    <text class="esq-ctx-txt" x="550" y="468" text-anchor="middle">Unidad ABS</text>
    <text class="esq-ctx-txt" x="550" y="486" text-anchor="middle">(otra lámina)</text>
  </g>`;
}

/* ---------- bomba (1, 21): cuerpo con depósito, saliente del pivote y salida de la manguera ---------- */
const P_CIL="M-72,-24 L-72,-48 Q-72,-60 -60,-60 L38,-60 Q50,-60 50,-48 L50,-26 Q50,-14 38,-14 L-60,-14 Q-72,-14 -72,-24 Z";
const P_DEP="M-66,-58 L-62,-122 Q-61,-131 -52,-131 L18,-131 Q27,-131 28,-122 L32,-58 Z";
const P_PIV="M44,-62 L58,-64 A18,18 0 0 1 58,-28 L44,-26 Z";
const P_SAL="M-70,-50 L-84,-52 A16,16 0 0 0 -84,-20 L-70,-22 Z";
function arteBomba(s){
  return `<g transform="${G(s)}" filter="url(#b26Sombra)">
    ${extruir(P_CIL,6,"url(#b26Lado)")}${extruir(P_DEP,6,"url(#b26Lado)")}
    <path d="M-34,-16 L-34,-4 L34,-4 L34,-16 Z" fill="#202427"/>
    <path d="${P_SAL}" fill="#2a2f33"/><circle cx="-84" cy="-36" r="12" fill="#3b4247"/>
    <path d="${P_CIL}" fill="url(#b26Cuerpo)"/><path d="${P_CIL}" fill="url(#b26Grano)"/>
    <path d="${P_PIV}" fill="url(#b26Cuerpo)"/><circle cx="60" cy="-46" r="12" fill="#2b3034"/>
    <path d="${P_DEP}" fill="url(#b26Cuerpo)"/><path d="${P_DEP}" fill="url(#b26Grano)"/>
    <ellipse cx="-16" cy="-72" rx="11" ry="7" fill="#1a1d20" stroke="#6b7379" stroke-width="1.2"/>
    <ellipse cx="-16" cy="-72" rx="8" ry="4.5" fill="#c99a3a" opacity=".85"/>
    <line x1="-26" y1="-67" x2="-6" y2="-67" stroke="#f3efe6" stroke-width="1" opacity=".7"/>
    <path d="M-60,-58 L38,-58" stroke="#fff" stroke-opacity=".22" stroke-width="1.6"/>
    <path d="M-62,-122 Q-61,-131 -52,-131 L18,-131" fill="none" stroke="#fff" stroke-opacity=".25" stroke-width="1.6"/>
    <ellipse cx="50" cy="-37" rx="4" ry="11" fill="#141618"/>
  </g>`;
}
/* kit (2, 22): pistón, copa primaria y secundaria, resorte, seguro y guardapolvo; sale del cilindro hacia afuera */
function arteKit(s){
  let r="";for(let k=0;k<6;k++)r+=`<ellipse cx="${-46+k*7}" cy="-37" rx="2.4" ry="9" fill="none" stroke="#c9ced1" stroke-width="2"/>`;
  return `<g class="esq-oculto-arm" transform="${G(s)}" filter="url(#b26Sombra)">
    ${r}
    <rect x="-6" y="-46" width="8" height="18" rx="2" fill="#151515"/>
    <rect x="2" y="-44" width="34" height="14" rx="3" fill="url(#b26Cromo)"/>
    <rect x="14" y="-46" width="5" height="18" rx="1.5" fill="#151515"/>
    <rect x="34" y="-46" width="6" height="18" rx="2" fill="#151515"/>
    <path d="M42,-45 L58,-43 Q62,-37 58,-31 L42,-29 Z" fill="url(#b26Caucho)"/>
    <rect x="58" y="-39" width="12" height="4" rx="2" fill="url(#b26Acero)"/>
    <path d="M44,-49 A12,12 0 0 1 44,-25" fill="none" stroke="#a7aeb2" stroke-width="2"/>
  </g>`;
}
/* tapa (3, 23), placa (4, 24) y diafragma (5, 25) */
const P_TAPA="M-62,-128 Q-62,-136 -54,-136 L20,-136 Q28,-136 28,-128 L28,-100 Q28,-94 22,-94 L-56,-94 Q-62,-94 -62,-100 Z";
const arteTapa=s=>`<g transform="${G(s)}" filter="url(#b26Sombra)">${extruir(P_TAPA,3,"#0f1112",.6)}<path d="${P_TAPA}" fill="url(#b26Tapa)"/>
    <path d="M-54,-133 L20,-133" stroke="#fff" stroke-opacity=".28" stroke-width="1.4"/>
    <rect x="-34" y="-122" width="36" height="14" rx="3" fill="none" stroke="#3d4448" stroke-width="1.2"/>
    <text x="-16" y="-111.5" font-size="8" font-family="Archivo" font-weight="700" fill="#7c858a" text-anchor="middle" transform="scale(${s} 1)" style="transform-box:fill-box;transform-origin:center">DOT 4</text></g>`;
const artePlaca=s=>`<g class="esq-oculto-arm" transform="${G(s)}"><path d="M-58,-126 L24,-126 L24,-104 L-58,-104 Z" fill="url(#b26Chapa)" stroke="#2b3034"/>
    <circle cx="-50" cy="-115" r="4" fill="#1b1f22"/><circle cx="16" cy="-115" r="4" fill="#1b1f22"/></g>`;
function arteDiafragma(s){
  let r="";for(let k=0;k<4;k++)r+=`<rect x="${-50+k*4}" y="${-124+k*4}" width="${66-k*8}" height="${26-k*8}" rx="${6-k}" fill="none" stroke="#3c3c3c" stroke-width="1.6"/>`;
  return `<g class="esq-oculto-arm" transform="${G(s)}"><rect x="-54" y="-128" width="74" height="34" rx="7" fill="url(#b26Caucho)"/>${r}</g>`;
}
/* manigueta (7 delantera, 27 trasera): brazo de aluminio delante del puño, con su ojo de pivote y la nariz que empuja el pistón */
const P_MAN="M48,-58 Q60,-66 74,-60 L118,-58 Q160,-58 200,-50 Q214,-47 214,-38 Q213,-30 200,-32 Q156,-38 118,-40 L80,-38 Q70,-32 60,-34 L46,-40 Z";
const arteManigueta=s=>`<g transform="${G(s)}" filter="url(#b26Sombra)">${extruir(P_MAN,3,"#4f575c",.7)}
    <path d="${P_MAN}" fill="url(#b26Alum)" stroke="#40474c" stroke-width="1"/>
    <path d="M80,-56 L118,-55 Q160,-55 200,-47" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="1.4"/>
    <circle cx="60" cy="-46" r="10" fill="#9aa2a7" stroke="#40474c"/><circle cx="60" cy="-46" r="5" fill="#2a2f33"/>
    <circle cx="${f(160)}" cy="-46" r="3" fill="#6e767b"/><circle cx="174" cy="-44" r="3" fill="#6e767b"/><circle cx="188" cy="-42" r="3" fill="#6e767b"/></g>`;
/* abrazadera (10, 30): media luna que aprieta la bomba contra el manubrio */
const P_ABR="M-36,4 Q-36,-2 -30,-2 L30,-2 Q36,-2 36,4 L36,26 Q36,34 28,34 L-28,34 Q-36,34 -36,26 Z";
const arteAbrazadera=s=>`<g transform="${G(s)}" filter="url(#b26Sombra)">${extruir(P_ABR,4,"url(#b26Lado)",.8)}
    <path d="${P_ABR}" fill="url(#b26Cuerpo)"/><path d="M-30,2 L30,2" stroke="#fff" stroke-opacity=".2" stroke-width="1.4"/>
    <path d="M-8,30 L8,30 L4,20 L-4,20 Z" fill="#7c858a"/><circle cx="-22" cy="16" r="9" fill="#1b1f22"/><circle cx="22" cy="16" r="9" fill="#1b1f22"/></g>`;
/* interruptor del freno (12, 32): cajita negra con el émbolo que toca la manigueta, y su cable */
const arteInterruptor=s=>`<g transform="${G(s)}" filter="url(#b26Sombra)">
    <path d="M40,-10 C30,6 18,14 2,18" fill="none" stroke="#111" stroke-width="5" stroke-linecap="round"/>
    <path d="M40,-10 C30,6 18,14 2,18" fill="none" stroke="#7a2a20" stroke-width="2" stroke-linecap="round"/>
    <rect x="38" y="-14" width="28" height="22" rx="4" fill="#181a1c" stroke="#3b4246"/>
    <rect x="62" y="-8" width="8" height="8" rx="2" fill="#9aa2a7"/>
    <circle cx="56" cy="-3" r="5" fill="#2b3034"/></g>`;

/* ---------- mangueras (15, 18, 34, 38): caucho negro, casquillos y ojos de unión ---------- */
const H={15:[[686,139],[652,152],[618,205],[602,285],[594,360],[590,428]],
         34:[[414,139],[448,152],[482,205],[498,285],[506,360],[510,428]],
         18:[[600,514],[606,566],[652,622],[760,680],[880,742],[950,800]],
         38:[[500,514],[494,565],[455,615],[395,652],[330,685],[260,718],[195,752],[140,800]]};
function ojo(p,q){const a=Math.atan2(q[1]-p[1],q[0]-p[0])*180/Math.PI;
  return `<g transform="translate(${p[0]} ${p[1]}) rotate(${f(a)})"><rect x="10" y="-6.5" width="22" height="13" rx="3" fill="url(#b26Acero)" stroke="#3a4144" stroke-width=".8"/>
    <line x1="18" y1="-6" x2="18" y2="6" stroke="#5e666b"/><line x1="24" y1="-6" x2="24" y2="6" stroke="#5e666b"/>
    <circle r="13" fill="url(#b26Acero)" stroke="#3a4144"/><circle r="6" fill="#20262a"/></g>`}
function manguera(k,bajoBarra,texto){
  const p=H[k],d=suave(p),n=p.length;
  return `<g filter="url(#b26Sombra)"><g${bajoBarra?' mask="url(#b26mBarra)"':""}>
    <path d="${d}" fill="none" stroke="#050505" stroke-width="14" stroke-linecap="round"/>
    <path d="${d}" fill="none" stroke="#262626" stroke-width="9" stroke-linecap="round"/>
    <path d="${d}" fill="none" stroke="#5a5a5a" stroke-width="1.6" stroke-linecap="round" transform="translate(-2 -2)" opacity=".7"/></g>
    ${ojo(p[0],p[1])}${ojo(p[n-1],p[n-2])}${texto||""}</g>`}
const arteManguera1=()=>manguera(15,true);
const arteManguera3=()=>manguera(34,true);
const arteManguera2=()=>manguera(18,false,`<text class="esq-ctx-txt" x="1040" y="838" text-anchor="end">Al cáliper delantero (lám. 22)</text>`);
const arteManguera4=()=>manguera(38,false,`<text class="esq-ctx-txt" x="60" y="838">Al cáliper trasero</text>`);

/* ---------- tope (14), abrazaderas (37, 41, 45) y soportes (42, 44, 46, 48) ---------- */
const arteTope=()=>`<g filter="url(#b26Sombra)">
    <path d="M484,338 L616,338 Q622,338 622,344 L622,350 Q622,356 616,356 L484,356 Q478,356 478,350 L478,344 Q478,338 484,338 Z" fill="url(#b26Chapa)" stroke="#2b3034"/>
    <circle cx="504" cy="347" r="11" fill="none" stroke="#1a1a1a" stroke-width="5"/><circle cx="596" cy="347" r="11" fill="none" stroke="#1a1a1a" stroke-width="5"/>
    <circle cx="550" cy="347" r="5" fill="#1b1f22"/></g>`;
const grapa=(x,y,a)=>`<g transform="translate(${x} ${y}) rotate(${a})" filter="url(#b26Sombra)">
    <rect x="-5" y="-12" width="10" height="24" rx="3" fill="#1d2023" stroke="#5a646a"/><rect x="-2" y="-16" width="4" height="8" rx="1.5" fill="#7c858a"/></g>`;
const arteGrapa37=()=>grapa(482,205,-30);
const arteGrapa41=()=>grapa(455,615,40);
const arteGrapa45=()=>grapa(330,685,62);
function soporte(x,y,bx,by){return `<g filter="url(#b26Sombra)">
    <path d="M${x-9},${y} L${bx-11},${by-2} Q${bx},${by+14} ${bx+11},${by-2} L${x+9},${y} Z" fill="url(#b26Chapa)" stroke="#2b3034"/>
    <circle cx="${x}" cy="${y}" r="13" fill="#26292b" stroke="#55606a"/><circle cx="${x}" cy="${y}" r="8" fill="#0d0d0d"/>
    <circle cx="${bx}" cy="${by}" r="6" fill="#15181a"/></g>`}
const arteSoporte42=()=>soporte(395,652,403,682);
const arteSoporte44=()=>soporte(330,685,322,716);
const arteSoporte48=()=>soporte(195,752,203,782);
const P_BASE="M222,736 L300,742 Q308,743 307,751 L304,764 Q302,771 294,770 L220,762 Q212,761 213,753 L214,744 Q215,736 222,736 Z";
const arteBase46=()=>`<g filter="url(#b26Sombra)">${extruir(P_BASE,3,"#2b3135",.6)}<path d="${P_BASE}" fill="url(#b26Chapa)" stroke="#2b3034"/>
    <path d="M262,738 L270,700 L284,702 L278,742 Z" fill="url(#b26Chapa)" stroke="#2b3034"/>
    <circle cx="232" cy="752" r="6" fill="#15181a"/><circle cx="288" cy="757" r="6" fill="#15181a"/></g>`;

/* ============================================================
   «Cómo funciona»: bomba cortada (depósito, orificios, pistón con sus copas, resorte, manigueta e interruptor)
   y, a la derecha (abajo en el celular), la manguera, la unidad ABS y el cáliper.
   ============================================================ */
let burb="";[[110,196],[132,210],[150,192],[90,206]].forEach(([x,y])=>burb+=`<circle cx="${x}" cy="${y}" r="5" fill="#fff8e6" stroke="#b07a1e"/>`);
let res="";for(let k=0;k<8;k++){const x=66+k*17;res+=`${k?"L":"M"}${x},184 L${x+8.5},216 `}res+="L202,184";
const FN_SVG=`<svg id="fn" viewBox="0 0 900 440" role="img" aria-labelledby="fnTit">
  <title id="fnTit">Esquema de la bomba de freno cortada: depósito con diafragma, orificio de compensación, pistón con copas, resorte, manigueta e interruptor de la luz; a la derecha, la manguera, la unidad ABS y el cáliper</title>
  <defs><linearGradient id="fn26Cromo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f3f5f6"/><stop offset=".45" stop-color="#9aa3a8"/><stop offset=".6" stop-color="#e2e6e8"/><stop offset="1" stop-color="#6c7479"/></linearGradient>
  <linearGradient id="fn26Cuerpo" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#555b61"/><stop offset="1" stop-color="#2a2e32"/></linearGradient>
  <pattern id="fn26Fric" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#4d3f33"/><circle cx="1.5" cy="2" r=".8" fill="#6d5a49"/></pattern></defs>
  <!-- cuerpo cortado -->
  <path d="M40,160 L150,160 L150,30 L330,30 L330,160 L420,160 L420,240 L40,240 Z" fill="url(#fn26Cuerpo)" stroke="#6c7479" stroke-width="1.5"/>
  <rect x="160" y="40" width="160" height="112" fill="#191c1f"/>
  <g id="fn26Liq" style="transition:transform .7s"><rect x="160" y="74" width="160" height="80" fill="#e8a92a" opacity=".85"/></g>
  <g id="fn26Diaf" style="transition:transform .7s"><path d="M160,74 Q180,64 200,74 T240,74 T280,74 T320,74 L320,66 Q300,56 280,66 T240,66 T200,66 T160,66 Z" fill="#141414" stroke="#3c3c3c"/></g>
  <rect x="152" y="24" width="176" height="14" rx="4" fill="#111315" stroke="#59646a"/>
  <rect x="194" y="152" width="4" height="30" fill="#e8a92a"/><rect x="258" y="152" width="10" height="30" fill="#e8a92a"/>
  <rect x="60" y="180" width="350" height="40" fill="#121416"/>
  <rect id="fn26Camara" x="60" y="182" width="150" height="36" fill="#e8a92a" opacity=".9" style="transition:fill .4s"/>
  <rect x="210" y="182" width="190" height="36" fill="#e8a92a" opacity=".55"/>
  <path id="fn26Res" d="${res}" fill="none" stroke="#c9ced1" stroke-width="3" style="transition:transform .7s"/>
  <g id="fn26Burb" opacity="0" style="transition:opacity .5s">${burb}</g>
  <g id="fn26Pist" style="transition:transform .7s cubic-bezier(.5,0,.3,1)">
    <rect x="202" y="181" width="10" height="38" rx="2" fill="#0d0d0d"/>
    <rect x="212" y="186" width="88" height="28" rx="3" fill="url(#fn26Cromo)"/>
    <rect x="238" y="192" width="40" height="16" fill="#7d868b"/>
    <rect x="300" y="181" width="12" height="38" rx="2" fill="#0d0d0d"/>
    <rect x="312" y="194" width="44" height="12" rx="3" fill="#9aa3a8"/>
  </g>
  <path d="M404,178 L420,184 L420,216 L404,222 Z" fill="#1c1c1c"/>
  <rect x="40" y="220" width="20" height="12" fill="#e8a92a"/>
  <g id="esq-fn26-flecha" opacity="0" style="transition:opacity .4s"><path id="esq-fn26-flechaP" d="M196,170 L196,120" stroke="#fff3d6" stroke-width="3" marker-end="url(#fn26Punta)"/></g>
  <defs><marker id="fn26Punta" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#fff3d6"/></marker></defs>
  <!-- manigueta e interruptor -->
  <rect x="404" y="252" width="34" height="24" rx="4" fill="#181a1c" stroke="#59646a"/>
  <rect id="fn26Emb" x="416" y="238" width="8" height="16" fill="#9aa2a7" style="transition:transform .5s"/>
  <g id="fn26Lever" style="transform-origin:372px 160px;transition:transform .7s cubic-bezier(.5,0,.3,1)">
    <path d="M356,148 Q372,138 386,150 L460,170 Q472,174 470,184 Q466,192 456,188 L384,172 L358,206 Q352,212 348,204 Z" fill="#a9b0b4" stroke="#2b3135" stroke-width="2"/>
    <circle cx="372" cy="160" r="7" fill="#2b3135" stroke="#9aa3a8"/>
  </g>
  <circle id="fn26Luz" cx="452" cy="300" r="10" fill="#3a1d1a" stroke="#7a2a20" style="transition:fill .3s"/>
  <!-- manguera de salida -->
  <path class="esq-solo-pc" d="M50,232 L50,282 Q50,296 64,296 L480,296" fill="none" stroke="#151515" stroke-width="12" stroke-linecap="round"/>
  <path class="esq-solo-pc esq-fn26-fl" d="M50,232 L50,282 Q50,296 64,296 L480,296" fill="none" stroke="#e8a92a" stroke-width="4" stroke-linecap="round"/>
  <path class="esq-solo-movil" d="M50,232 L50,300" fill="none" stroke="#151515" stroke-width="12" stroke-linecap="round"/>
  <path class="esq-solo-movil esq-fn26-fl" d="M50,232 L50,300" fill="none" stroke="#e8a92a" stroke-width="4" stroke-linecap="round"/>
  <!-- etiquetas de la bomba -->
  <text class="esq-fn-et esq-claro" x="160" y="18" data-ym="16">Depósito y tapa</text>
  <text class="esq-fn-et" x="336" y="64" data-xm="334">Diafragma</text>
  <text class="esq-fn-et" x="336" y="80" data-xm="334" data-ym="86">(sigue el nivel)</text>
  <text class="esq-fn-et" x="64" y="138" data-ym="128">Orificio de</text>
  <text class="esq-fn-et" x="64" y="158" data-ym="154">compensación ↘</text>
  <text class="esq-fn-et" x="96" y="262" data-xm="70" data-ym="266">Resorte</text>
  <text class="esq-fn-et" x="214" y="262" data-ym="266">Pistón y copas</text>
  <text class="esq-fn-et esq-claro" x="380" y="134" data-xm="350" data-ym="128">Manigueta</text>
  <text class="esq-fn-et" x="300" y="286" data-xm="300" data-ym="296" text-anchor="end">Interruptor →</text>
  <text class="esq-fn-et" x="380" y="326" data-xm="300" data-ym="320">Luz de freno</text>
  <!-- rueda: manguera, ABS y cáliper (en el celular baja debajo de la bomba) -->
  <g id="fnCorte">
    <path class="esq-solo-movil" d="M520,38 L520,90" fill="none" stroke="#151515" stroke-width="12"/>
    <path class="esq-solo-movil esq-fn26-fl" d="M520,38 L520,90" fill="none" stroke="#e8a92a" stroke-width="4"/>
    <rect x="490" y="90" width="110" height="62" rx="8" fill="#2b3135" stroke="#59646a" stroke-dasharray="4 3"/>
    <text class="esq-fn-et esq-claro" x="545" y="118" data-ym="112" text-anchor="middle">Unidad ABS</text>
    <text class="esq-fn-et" x="545" y="138" data-ym="140" text-anchor="middle">(otra lámina)</text>
    <path class="esq-solo-pc" d="M480,296 L520,296 L520,152" fill="none" stroke="#151515" stroke-width="12"/>
    <path class="esq-solo-pc esq-fn26-fl" d="M480,296 L520,296 L520,152" fill="none" stroke="#e8a92a" stroke-width="4"/>
    <path d="M570,152 L570,250 Q570,262 582,262 L640,262" fill="none" stroke="#151515" stroke-width="12"/>
    <path class="esq-fn26-fl" d="M570,152 L570,250 Q570,262 582,262 L640,262" fill="none" stroke="#e8a92a" stroke-width="4"/>
    <text class="esq-fn-et" x="528" y="324" data-xm="478" data-ym="232">Manguera</text>
    <path d="M640,200 L800,200 Q812,200 812,212 L812,342 Q812,352 800,352 L760,352 L760,226 L700,226 L700,352 L652,352 Q640,352 640,340 Z" fill="url(#fn26Cuerpo)" stroke="#6c7479" stroke-width="1.5"/>
    <rect x="652" y="236" width="48" height="96" fill="#e8a92a" opacity=".9"/>
    <g id="fn26Cal" style="transition:transform .7s cubic-bezier(.5,0,.3,1)">
      <rect x="664" y="240" width="36" height="88" rx="4" fill="url(#fn26Cromo)"/>
      <rect x="700" y="236" width="7" height="96" rx="2" fill="#8f979b"/><rect x="707" y="240" width="16" height="88" rx="3" fill="url(#fn26Fric)"/>
    </g>
    <rect x="726" y="196" width="12" height="190" fill="#c9ced1"/>
    <rect x="741" y="240" width="16" height="88" rx="3" fill="url(#fn26Fric)"/><rect x="757" y="236" width="3" height="96" fill="#8f979b"/>
    <text class="esq-fn-et esq-claro" x="640" y="186">Cáliper</text>
    <text class="esq-fn-et" x="744" y="412" text-anchor="middle">Disco y pastillas</text>
  </g>
</svg>`;
function fnAplicar(s,$){
  $("fn26Lever").style.transform=`rotate(${s.lever}deg)`;
  $("fn26Pist").style.transform=`translateX(${-s.pist}px)`;
  $("fn26Res").style.transform=`translateX(0) scaleX(${(140-s.pist)/140})`;$("fn26Res").style.transformOrigin="66px 200px";
  $("fn26Emb").style.transform=`translateY(${s.luz?-8:0}px)`;
  $("fn26Luz").setAttribute("fill",s.luz?"#ff4b2b":"#3a1d1a");
  $("fn26Camara").setAttribute("fill",s.presion?"#ff9a3c":"#e8a92a");
  $("fn26Liq").style.transform=`translateY(${s.nivel}px)`;$("fn26Diaf").style.transform=`translateY(${s.nivel}px)`;
  $("fn26Cal").style.transform=`translateX(${s.cal}px)`;
  $("fn26Burb").style.opacity=s.aire?1:0;
  const fl=$("esq-fn26-flecha"),fp=$("esq-fn26-flechaP");fl.style.opacity=s.flujo?1:0;fp.setAttribute("d",s.flujo==="sube"?"M196,176 L196,128":"M196,128 L196,176");
  document.querySelectorAll("#fn .esq-fn26-fl").forEach(e=>{e.classList.toggle("esq-pulso",!!s.presion);e.setAttribute("stroke",s.presion?"#ff9a3c":"#e8a92a")});
}
return {defs:DEFS,arteABS,arteAbrazadera,arteBase46,arteBomba,arteDiafragma,arteGrapa37,arteGrapa41,arteGrapa45,arteInterruptor,arteKit,arteManguera1,arteManguera2,arteManguera3,arteManguera4,arteManigueta,arteManubrio,artePlaca,arteSoporte42,arteSoporte44,arteSoporte48,arteTapa,arteTope,funciona:{svg:FN_SVG,aplicar:fnAplicar}};
})();
