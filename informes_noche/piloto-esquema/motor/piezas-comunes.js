/* Biblioteca de piezas comunes del esquema: tornillo, tuerca, arandela, anillo de seguro, retén, O-ring, rodamiento,
   buje, resorte, pasador, pieza de revolución por perfil y formas de lámina: manguera, abrazadera (de oreja o de
   tornillo), caja con tapa, ducto y placa/empaque. Cada pieza sale de sus medidas y da A LA VEZ:
   - su arte 2D en el estilo de los dibujos (cara al lector, espesor hacia «atrás» según la lámina), y
   - su forma3d para el visor de la ficha (eje = z), sin describirla dos veces.
   En el JSON de la lámina, una línea por pieza:
     {"id":"28","comun":"tuerca","p":{"x":278,"y":414.1,"r":14}}
   y una vez por lámina:
     "comun":{"atras":[0.5,-0.32], "colores":{"acero":"url(#cvAcero)",...}, "sombra":"url(#cvSombra)"}
   Opcionales por pieza: "marco" (nombre de un transform que exporta el arte en A.marcos: la pieza se dibuja en ese
   plano), p.copias [[dx,dy],...] (varias iguales), p.sombra (true/false), "sin3d":true.
   Medidas en unidades del dibujo; r = radio exterior, ri = radio del agujero. */
window.ESQ_COMUN=(function(){
"use strict";
const f=n=>Math.round(n*10)/10;
function hexa(cx,cy,r,rot=0){let p=[];for(let i=0;i<6;i++){const a=(i*60+rot)*Math.PI/180;p.push(f(cx+r*Math.cos(a))+","+f(cy+r*Math.sin(a)))}return p.join(" ")}
const aro=(x,y,r,ri)=>`M${f(x+r)} ${f(y)} A${r} ${r} 0 1 0 ${f(x-r)} ${f(y)} A${r} ${r} 0 1 0 ${f(x+r)} ${f(y)} Z M${f(x+ri)} ${f(y)} A${ri} ${ri} 0 1 1 ${f(x-ri)} ${f(y)} A${ri} ${ri} 0 1 1 ${f(x+ri)} ${f(y)} Z`;
// curva suave por los puntos (Catmull-Rom → Bézier), para mangueras
function suave(p){if(p.length<2)return "";let d=`M${f(p[0][0])},${f(p[0][1])}`;for(let i=0;i<p.length-1;i++){const a=p[i-1]||p[i],b=p[i],c=p[i+1],e=p[i+2]||c;
  d+=` C${f(b[0]+(c[0]-a[0])/6)},${f(b[1]+(c[1]-a[1])/6)} ${f(c[0]-(e[0]-b[0])/6)},${f(c[1]-(e[1]-b[1])/6)} ${f(c[0])},${f(c[1])}`}return d}
const COLOR_BASE={acero:"#b9c0c4",cromo:"#d5dadd",rosca:"#2a3034",plast:"#e0d0ae",caucho:"#2a2a2a",estrias:"#4a5257",alum:"#b9c0c4",fibra:"#8c7b5c",plastNegro:"#2b2f33"};

/* ---------- arte 2D ---------- */
function crear(cfg={},marcos={}){
  const B=cfg.atras||[0.5,-0.32], BL=Math.hypot(B[0],B[1])||1, N=[-B[1]/BL,B[0]/BL], C=Object.assign({},COLOR_BASE,cfg.colores||{});
  const SOMBRA=cfg.sombra||"", angAtras=Math.atan2(B[1],B[0])*180/Math.PI;
  const atras=(x,y,d)=>[x+B[0]*d,y+B[1]*d];
  function cil(x,y,r,d,cara,lado,extra=""){
    const [bx,by]=atras(x,y,d), nx=N[0]*r, ny=N[1]*r;
    return `<circle cx="${f(bx)}" cy="${f(by)}" r="${r}" fill="${lado}"/>
  <path d="M${f(x+nx)} ${f(y+ny)} L${f(bx+nx)} ${f(by+ny)} L${f(bx-nx)} ${f(by-ny)} L${f(x-nx)} ${f(y-ny)} Z" fill="${lado}"/>
  <circle cx="${f(x)}" cy="${f(y)}" r="${r}" fill="${cara}" ${extra}/>`;
  }
  function anillo(x,y,r,ri,d,cara,lado){
    let s="";for(let k=d;k>0;k-=1.5){const [bx,by]=atras(x,y,k);s+=`<path d="${aro(bx,by,r,ri)}" fill="${lado}" fill-rule="evenodd"/>`}
    return s+`<path d="${aro(x,y,r,ri)}" fill="${cara}" fill-rule="evenodd" stroke="#1b2023" stroke-width=".8"/>`;
  }
  // vástago visto de lado (tornillo, pasador): sale hacia atrás y solo se ve desarmado
  function vastago(largo,d,desde,relleno,punta){
    const rot=Math.round(angAtras-180)%360, t=rot?` transform="rotate(${rot})"`:"";
    return `<g class="esq-oculto-arm"${t}>${punta==="redonda"
      ?`<rect x="${-desde-largo}" y="${-d/2}" width="${largo}" height="${d}" rx="${d/2}" fill="${relleno}"/>`
      :`<rect x="${-desde-largo}" y="${-d/2}" width="${largo}" height="${d}" fill="${relleno}" stroke="#4b5256" stroke-width=".8"/><path d="M${-desde-largo},${-d/2} L${-desde-largo-4},0 L${-desde-largo},${d/2}" fill="#8a9297"/>`}</g>`;
  }
  const A={
    tuerca:p=>{const r=p.r||14,d=p.alto||8,{x,y}=p;let s="";for(let k=d;k>0;k-=1.5){const [bx,by]=atras(x,y,k);s+=`<polygon points="${hexa(bx,by,r,15)}" fill="#3e464b"/>`}
      return s+`<polygon points="${hexa(x,y,r,15)}" fill="${C.acero}" stroke="#262c30" stroke-width="1"/><circle cx="${f(x)}" cy="${f(y)}" r="${f(r*.62)}" fill="#20262a"/><circle cx="${f(x)}" cy="${f(y)}" r="${f(r*.62)}" fill="${C.rosca}" opacity=".7"/>`},
    arandela:p=>{const m=p.material||"acero";return anillo(p.x,p.y,p.r,p.ri,p.e||3,C[m],p.lado||(m==="plast"?"#7f735b":"#4f585e"))},
    seguro:p=>{const {x,y,r}=p,a=`M${f(x+r*Math.cos(1.2))} ${f(y+r*Math.sin(1.2))} A${r} ${r} 0 1 1 ${f(x+r*Math.cos(1.94))} ${f(y+r*Math.sin(1.94))}`;
      return `<path d="${a}" fill="none" stroke="#2a3034" stroke-width="5.5" stroke-linecap="round"/><path d="${a}" fill="none" stroke="${C.acero}" stroke-width="3" stroke-linecap="round"/>`},
    reten:p=>{const r=p.r||20,ri=p.ri||r-7,{x,y}=p;return anillo(x,y,r,ri,p.ancho||5,p.cara||"#202020","#0c0c0c")+`<circle cx="${x}" cy="${y}" r="${f(r-3.5)}" fill="none" stroke="#5a5a5a" stroke-width="1"/>`},
    oring:p=>anillo(p.x,p.y,p.r,p.r-(p.g||3),p.g||3,"#1d1d1d","#0a0a0a"),
    rodamiento:p=>{const {x,y,r,ri}=p,an=p.ancho||8;
      if(p.tipo==="agujas"){let s=cil(x,y,r,an,"#5c6468","#2c3236")+`<path d="${aro(x,y,r,ri)}" fill="${C.acero}" fill-rule="evenodd"/>`;const m=(r+ri)/2+(p.desfase||0);
        for(let k=0;k<(p.n||12);k++){const a=k*2*Math.PI/(p.n||12);s+=`<circle cx="${f(x+m*Math.cos(a))}" cy="${f(y+m*Math.sin(a))}" r="1.6" fill="#2a3034"/>`}return s}
      const m=(r+ri)/2;return anillo(x,y,r,ri,an,C.acero,"#4f585e")+`<circle cx="${x}" cy="${y}" r="${f(m)}" fill="none" stroke="#2c3236" stroke-width="${p.pista||5}"/>`+(p.bolas===false?"":`<circle cx="${x}" cy="${y}" r="${f(m)}" fill="none" stroke="#c9ced1" stroke-width="2" stroke-dasharray="3 3.2"/>`)},
    buje:p=>cil(p.x,p.y,p.r,p.largo,C[p.material||"cromo"],p.lado||"#7b858b")+`<circle cx="${p.x}" cy="${p.y}" r="${p.ri}" fill="${p.estrias?C.estrias:"#20262a"}"/>`,
    resorte:p=>{let s="";const v=p.vueltas||6,r=p.r,L=p.largo,al=p.alambre||3.2;
      for(let k=0;k<v;k++){const [cx,cy]=atras(p.x,p.y,L-(k+.5)*L/v);
        s+=`<ellipse cx="${f(cx)}" cy="${f(cy)}" rx="${r}" ry="${r}" fill="none" stroke="#1e2326" stroke-width="${f(al+2)}"/><ellipse cx="${f(cx)}" cy="${f(cy)}" rx="${r}" ry="${r}" fill="none" stroke="${C.cromo}" stroke-width="${al}"/>`}return s},
    pasador:p=>p.cuerpo==="lateral"
      ?`<g transform="translate(${p.x} ${p.y})">${vastago(p.largo,p.r*2,4,C.cromo,"redonda")}<circle r="${p.cabeza+1}" fill="#3c4347"/><circle r="${p.cabeza}" fill="${C.acero}"/><polygon points="${hexa(0,0,p.cabeza*.51,0)}" fill="#2a2f33"/></g>`
      :cil(p.x,p.y,p.r,p.largo,C.acero,"#6c7479"),
    tornillo:p=>{const b=p.brida||0,c=p.cabeza||10;
      const cab=p.tipo==="allen"
        ?`<circle r="${c}" fill="${C.acero}" stroke="#4b5256" stroke-width="1.2"/><polygon points="${hexa(0,0,c*.45,0)}" fill="#2a2f33"/>`
        :`<polygon points="${hexa(0,0,c,15)}" fill="${C.acero}" stroke="#4b5256" stroke-width="1.2"/>
    <polygon points="${hexa(0,0,c,15)}" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width=".8" transform="translate(-.8 -.8)"/>`;
      return `<g transform="translate(${p.x} ${p.y})">
    ${vastago(p.largo||46,p.d||12,b?12:c,C.rosca)}
    ${b?`<circle r="${b+1}" fill="#3c4347"/><circle r="${b}" fill="${C.acero}" stroke="#3a4144"/>`:""}
    ${cab}
  </g>`},
    /* formas de lámina (no de revolución): manguera, abrazadera, caja con tapa, ducto y placa/empaque.
       Puntos y contornos relativos a (x,y), que por omisión es 0,0. */
    manguera:p=>{const P=(p.puntos||[]).map(([a,b])=>[a+(p.x||0),b+(p.y||0)]),d=suave(P),g=p.g||9,col=C[p.color]||p.color||"#262626";
      const ext=p.extremos===false?"":[[P[0],P[1]],[P[P.length-1],P[P.length-2]]].map(([a,b])=>{const ang=Math.atan2(b[1]-a[1],b[0]-a[0])*180/Math.PI;
        return `<rect transform="translate(${f(a[0])} ${f(a[1])}) rotate(${f(ang)})" x="0" y="${f(-g/2-1.5)}" width="${f(g*.9)}" height="${f(g+3)}" rx="2" fill="${p.boca||"#3a3a3a"}" stroke="#050505" stroke-width=".8"/>`}).join("");
      return `<path d="${d}" fill="none" stroke="#050505" stroke-width="${f(g+5)}" stroke-linecap="round"/><path d="${d}" fill="none" stroke="${col}" stroke-width="${g}" stroke-linecap="round"/>
  <path d="${d}" fill="none" stroke="#5a5a5a" stroke-width="1.6" stroke-linecap="round" transform="translate(-2 -2)" opacity=".7"/>${ext}`},
    abrazadera:p=>{const {x,y,r}=p,an=p.ancho||2.2,giro=(p.giro===undefined?-90:p.giro)*Math.PI/180,ox=Math.cos(giro),oy=Math.sin(giro),tx=-oy,ty=ox;
      const ox1=x+ox*r,oy1=y+oy*r,L=p.oreja||(p.tipo==="tornillo"?9:7);
      const oreja=p.tipo==="tornillo"
        ?`<rect transform="translate(${f(ox1)} ${f(oy1)}) rotate(${f(giro*180/Math.PI)})" x="-1" y="-6" width="${L}" height="12" rx="2" fill="${C.acero}" stroke="#262c30" stroke-width=".8"/><circle cx="${f(ox1+ox*L*.55)}" cy="${f(oy1+oy*L*.55)}" r="3" fill="#2a2f33"/>`
        :[1,-1].map(k=>{const d=`M${f(ox1+tx*k*2.4)} ${f(oy1+ty*k*2.4)} L${f(ox1+ox*L+tx*k*3.2)} ${f(oy1+oy*L+ty*k*3.2)}`;
          return `<path d="${d}" stroke="#262c30" stroke-width="4.4" stroke-linecap="round"/><path d="${d}" stroke="${C.acero}" stroke-width="2.4" stroke-linecap="round"/>`}).join("");
      return anillo(x,y,r,r-an,p.banda||5,C.acero,"#4f585e")+oreja},
    caja:p=>{const {x,y}=p,w=p.w||80,h=p.h||60,rx=p.rx||8,pr=p.prof||14,x0=x-w/2,y0=y-h/2,cara=p.cara||C.plastNegro,lado=p.lado||"#121416";
      const rr=(a,b,W,H,R)=>`M${f(a+R)} ${f(b)} H${f(a+W-R)} Q${f(a+W)} ${f(b)} ${f(a+W)} ${f(b+R)} V${f(b+H-R)} Q${f(a+W)} ${f(b+H)} ${f(a+W-R)} ${f(b+H)} H${f(a+R)} Q${f(a)} ${f(b+H)} ${f(a)} ${f(b+H-R)} V${f(b+R)} Q${f(a)} ${f(b)} ${f(a+R)} ${f(b)} Z`;
      const D=rr(x0,y0,w,h,rx);let s="";for(let k=pr;k>0;k-=2){const [bx,by]=atras(0,0,k);s+=`<path d="${D}" transform="translate(${f(bx)} ${f(by)})" fill="${lado}"/>`}
      s+=`<path d="${D}" fill="${cara}" stroke="#0b0d0e" stroke-width="1"/><path d="M${f(x0+rx)} ${f(y0+2)} H${f(x0+w-rx)}" stroke="#fff" stroke-opacity=".18" stroke-width="1.4"/>`;
      if(p.tapa){const i=p.tapa===true?6:p.tapa,R2=Math.max(2,rx-i/2);s+=`<path d="${rr(x0+i,y0+i,w-2*i,h-2*i,R2)}" fill="${p.caraTapa||"none"}" stroke="#000" stroke-opacity=".55" stroke-width="1.6"/><path d="${rr(x0+i+1,y0+i+1,w-2*i,h-2*i,R2)}" fill="none" stroke="#fff" stroke-opacity=".12" stroke-width="1"/>`}
      (p.tornillos||[]).forEach(([a,b])=>{s+=`<circle cx="${f(x+a)}" cy="${f(y+b)}" r="3.4" fill="${C.acero}" stroke="#262c30" stroke-width=".7"/><path d="M${f(x+a-1.8)} ${f(y+b)} H${f(x+a+1.8)}" stroke="#262c30" stroke-width=".9"/>`});
      (p.bocas||[]).forEach(([a,b,r])=>{s+=`<circle cx="${f(x+a)}" cy="${f(y+b)}" r="${r}" fill="#0a0b0c" stroke="#45494d" stroke-width="2"/>`});
      return s},
    ducto:p=>{const P=(p.puntos||[[0,0],[60,0]]).map(([a,b])=>[a+(p.x||0),b+(p.y||0)]),r0=p.r0||14,r1=p.r1||r0,cara=p.cara||"#2a2a2a",lado=p.lado||"#121212";
      const L=[0];for(let i=1;i<P.length;i++)L.push(L[i-1]+Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]));const T=L[L.length-1]||1;
      let s="";const n=Math.max(2,Math.ceil(T/3));
      for(let k=0;k<=n;k++){const d=k/n*T;let i=1;while(i<P.length-1&&L[i]<d)i++;const t=(d-L[i-1])/((L[i]-L[i-1])||1);
        const cx=P[i-1][0]+(P[i][0]-P[i-1][0])*t,cy=P[i-1][1]+(P[i][1]-P[i-1][1])*t,r=r0+(r1-r0)*k/n;
        s+=`<circle cx="${f(cx)}" cy="${f(cy)}" r="${f(r)}" fill="${k===n?cara:lado}"${k===n?' stroke="#050505" stroke-width="1"':""}/>`}
      const e=P[P.length-1];if(p.boca!==false)s+=`<circle cx="${f(e[0])}" cy="${f(e[1])}" r="${f(r1*.72)}" fill="#050505" stroke="#4a4a4a" stroke-width="1.2"/>`;
      return s},
    placa:p=>{const {x,y}=p,m=p.material||"fibra",e=p.e||2,cara=C[m]||p.cara||C.fibra,lado=p.lado||(m==="fibra"?"#4e4433":"#3e464b");
      const pts=(p.contorno||[[-30,-20],[30,-20],[30,20],[-30,20]]).map(([a,b])=>f(x+a)+" "+f(y+b));
      const D="M"+pts.join(" L")+" Z"+(p.huecos||[]).map(([a,b,r])=>{const cx=x+a,cy=y+b;return ` M${f(cx+r)} ${f(cy)} A${r} ${r} 0 1 0 ${f(cx-r)} ${f(cy)} A${r} ${r} 0 1 0 ${f(cx+r)} ${f(cy)} Z`}).join("");
      let s="";for(let k=e;k>0;k-=1){const [bx,by]=atras(0,0,k);s+=`<path d="${D}" transform="translate(${f(bx)} ${f(by)})" fill="${lado}" fill-rule="evenodd"/>`}
      return s+`<path d="${D}" fill="${cara}" fill-rule="evenodd" stroke="#1b2023" stroke-width=".8"/>`},
    revolucion:p=>rev2d(p)
  };
  // pieza de revolución por perfil [[r,z],...] (z hacia el lector): discos apilados de atrás hacia adelante; las caras que miran al lector, claras
  function rev2d(p){
    const P=p.perfil, n=P.length, area=P.reduce((s,a,i)=>{const b=P[(i+1)%n];return s+a[0]*b[1]-b[0]*a[1]},0), o=Math.sign(area)||1;
    const capas=[];
    for(let i=0;i<n;i++){const a=P[i],b=P[(i+1)%n],dr=b[0]-a[0],dz=b[1]-a[1],nz=-dr*o;     // normal hacia afuera: (dz,-dr)·o
      if(Math.abs(nz)<1e-6&&Math.abs(dz)<1e-6)continue;
      const pasos=Math.max(1,Math.ceil(Math.abs(dz)/1.5));
      for(let k=0;k<=pasos;k++){const t=k/pasos;capas.push({z:a[1]+dz*t,r:a[0]+dr*t,frente:nz>0,ext:dz*o<0||nz>0})}}
    const zmax=Math.max(...P.map(q=>q[1])), rmin=Math.min(...P.map(q=>q[0]));
    capas.sort((u,v)=>u.z-v.z||v.r-u.r);
    let s="";capas.forEach(c=>{if(c.r<.5)return;const [cx,cy]=atras(p.x,p.y,zmax-c.z);
      s+=`<circle cx="${f(cx)}" cy="${f(cy)}" r="${f(c.r)}" fill="${c.frente?(p.cara||C.acero):(p.lado||"#4f585e")}"${c.frente?' stroke="#1b2023" stroke-width=".6"':""}/>`});
    if(rmin>.5)s+=`<circle cx="${p.x}" cy="${p.y}" r="${rmin}" fill="#20262a"/>`;
    return s;
  }
  return {
    arte(pz){const p=pz.p, fn=A[pz.comun];if(!fn)throw new Error("pieza común desconocida: "+pz.comun);
      const copias=p.copias||[[0,0]];let s=copias.map(([dx,dy])=>fn(Object.assign({},p,{x:(p.x||0)+dx,y:(p.y||0)+dy}))).join("");
      const sombra=p.sombra===undefined?["tuerca","tornillo"].includes(pz.comun):p.sombra;
      const m=pz.marco?` transform="${marcos[pz.marco]}"`:"";
      return `<g${m}${sombra&&SOMBRA?` filter="${SOMBRA}"`:""}>${s}</g>`},
    cil,anillo,atras
  };
}

/* ---------- forma3d (para esquema3d.js) ---------- */
const tubo=(r,ri,z0,z1)=>[[ri,z0],[r,z0],[r,z1],[ri,z1]];
const F3={
  tuerca:p=>[{tipo:"prisma",contorno:{n:6,r:p.r||14,giro:15},huecos:[{r:(p.r||14)*.62}],z:[0,p.alto||8],color:"acero"}],
  arandela:p=>[{tipo:"torno",perfil:tubo(p.r,p.ri,0,p.e||3),color:p.material==="plast"?"plast":"acero"}],
  seguro:p=>{const r=p.r,g=1.2*180/Math.PI,h=1.94*180/Math.PI;
    return [{tipo:"sector",r:[r-1.6,r+1.6],ang:[h-360+8,g-8].map(a=>a),z:[0,1.6],color:"acero"},
      {tipo:"prisma",contorno:{n:20,r:2.6},huecos:[{r:1}],pos:[r*Math.cos(1.2-.07),r*Math.sin(1.2-.07)],z:[0,1.6],color:"acero"},
      {tipo:"prisma",contorno:{n:20,r:2.6},huecos:[{r:1}],pos:[r*Math.cos(1.94+.07),r*Math.sin(1.94+.07)],z:[0,1.6],color:"acero"}]},
  reten:p=>{const r=p.r||20,ri=p.ri||r-7,a=p.ancho||5;
    return [{tipo:"torno",perfil:[[ri+2,0],[r,0],[r,a],[ri+1.5,a],[ri,a*.45]],color:"caucho"},{tipo:"torno",perfil:tubo(r-.6,r-2.2,.6,a-.6),color:"acero"}]},
  oring:p=>{const g=(p.g||3)/2,rc=p.r-g;return [{tipo:"torno",perfil:Array.from({length:14},(_,i)=>{const t=i/14*2*Math.PI;return [rc+g*Math.cos(t),g*Math.sin(t)]}),color:"caucho",suave:true}]},
  rodamiento:p=>{const {r,ri}=p,a=p.ancho||8,m=(r+ri)/2;
    if(p.tipo==="agujas")return [{tipo:"torno",perfil:tubo(r,r-1.6,0,a),color:"acero"},
      {tipo:"cilindro",r:1.6,z:[.4,a-.4],pos:[m+(p.desfase||0),0],repetir:p.n||12,color:"aceroOsc"}];
    const bola=Math.min((r-ri)*.3,a*.42),nb=Math.max(6,Math.floor(2*Math.PI*m/(bola*2.6)));
    return [{tipo:"torno",perfil:tubo(r,m+bola*.6,0,a),color:"acero"},{tipo:"torno",perfil:tubo(m-bola*.6,ri,0,a),color:"acero"},
      {tipo:"esfera",r:bola,pos:[m,0],z:a/2,repetir:nb,color:"aceroOsc"}]},
  buje:p=>[{tipo:"torno",perfil:tubo(p.r,p.ri,0,p.largo),color:p.material==="plast"?"plast":"acero"}],
  resorte:p=>[{tipo:"resorte",r:p.r,largo:p.largo,vueltas:p.vueltas||6,alambre:p.alambre||3.2,color:"acero"}],
  pasador:p=>{const r=p.r,L=p.largo,c=Math.min(r*.25,1.5);
    return p.cuerpo==="lateral"
      ?[{tipo:"torno",perfil:[[0,-L],[r-c,-L],[r,-L+c],[r,0],[0,0]],color:"acero"},{tipo:"prisma",contorno:{n:32,r:p.cabeza},huecos:[{n:6,r:p.cabeza*.51,giro:0,hondo:true}],z:[0,4],color:"acero"}]
      :[{tipo:"torno",perfil:[[0,0],[r-c,0],[r,c],[r,L-c],[r-c,L],[0,L]],color:"acero"}]},
  tornillo:p=>{const c=p.cabeza||10,b=p.brida||0,d=(p.d||12)/2,L=p.largo||46,al=p.alto||c*.7;
    const out=[{tipo:"torno",perfil:[[0,-L],[d-1,-L],[d,-L+1],[d,0],[0,0]],color:"acero",rosca:true}];
    if(b)out.push({tipo:"torno",perfil:[[0,0],[b,0],[b,2],[c,2.6],[0,2.6]],color:"acero"});
    const z0=b?2.6:0;
    out.push(p.tipo==="allen"
      ?{tipo:"prisma",contorno:{n:32,r:c},huecos:[{n:6,r:c*.45,giro:0}],z:[z0,z0+al],color:"acero"}
      :{tipo:"prisma",contorno:{n:6,r:c,giro:15},z:[z0,z0+al],color:"acero"});
    return out},
  manguera:p=>{const P=p.puntos||[[0,0],[60,0]];let L=0;for(let i=1;i<P.length;i++)L+=Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]);
    const g=(p.g||9)/2;return [{tipo:"torno",perfil:tubo(g,g*.55,0,Math.min(L,g*16)),color:"caucho"}]},
  abrazadera:p=>{const r=p.r,b=p.banda||5,L=p.oreja||(p.tipo==="tornillo"?9:7);
    return p.tipo==="tornillo"
      ?[{tipo:"torno",perfil:tubo(r,r-1,0,b),color:"acero"},{tipo:"caja",tam:[L,10,b+4],pos:[r+L/2-1,0,b/2],color:"acero"}]
      :[{tipo:"torno",perfil:tubo(r,r-1,0,b),color:"acero"},{tipo:"caja",tam:[L,2,b],pos:[r+L/2,2.2,b/2],color:"acero"},{tipo:"caja",tam:[L,2,b],pos:[r+L/2,-2.2,b/2],color:"acero"}]},
  caja:p=>{const w=p.w||80,h=p.h||60,pr=p.prof||14,R=Math.min(p.rx||8,w/2,h/2),c=[];
    for(const [cx,cy,a0] of [[w/2-R,h/2-R,0],[-w/2+R,h/2-R,90],[-w/2+R,-h/2+R,180],[w/2-R,-h/2+R,270]])for(let k=0;k<=4;k++){const a=(a0+k*22.5)*Math.PI/180;c.push([cx+R*Math.cos(a),cy+R*Math.sin(a)])}
    const out=[{tipo:"prisma",contorno:c,z:[0,pr],color:"oscuro"}];
    if(p.tapa)out.push({tipo:"prisma",contorno:c.map(([a,b])=>[a*.92,b*.92]),z:[pr,pr+3],color:"rodillo"});
    (p.bocas||[]).forEach(([a,b,r])=>out.push({tipo:"cilindro",r,z:[pr,pr+8],pos:[a,-b],color:"rodillo"}));
    return out},
  ducto:p=>{const P=p.puntos||[[0,0],[60,0]];let L=0;for(let i=1;i<P.length;i++)L+=Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]);
    const r0=p.r0||14,r1=p.r1||r0;return [{tipo:"torno",perfil:[[r0*.75,0],[r0,0],[r1,L],[r1*.72,L]],color:"caucho"}]},
  placa:p=>[{tipo:"prisma",contorno:(p.contorno||[[-30,-20],[30,-20],[30,20],[-30,20]]).map(([a,b])=>[a,-b]),huecos:(p.huecos||[]).map(([a,b,r])=>({r,pos:[a,-b]})),
    z:[0,p.e||2],color:p.material==="acero"?"acero":p.material==="caucho"?"caucho":"#8c7b5c"}],
  revolucion:p=>[{tipo:"torno",perfil:p.perfil,color:p.color3d||"acero"}]
};
function forma3d(comun,p){const g=F3[comun];return g?{partes:g(p)}:null}
return {crear,forma3d,TIPOS:Object.keys(F3)};
})();
