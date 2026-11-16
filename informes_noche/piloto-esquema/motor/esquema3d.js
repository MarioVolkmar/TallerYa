/* Visor 3D de la ficha (prueba de viabilidad). Maqueta simple de la pieza en vista isométrica, 4 vistas con ◀ ▶.
   three.js se importa solo la primera vez que se abre una ficha con «forma3d» (de los estáticos del sitio, o del
   <script type="text/plain" id="esq-three"> en el archivo único). Un solo renderer para toda la página.
   forma3d (eje de la pieza = z; r y z en las unidades del dibujo; el visor encuadra solo):
     {partes:[ {tipo:"torno", perfil:[[r,z],...]}            perfil cerrado, se gira alrededor de z
               {tipo:"sector", r:[ri,ro], ang:[a0,a1], z:[z0,z1]}   trozo de anillo extruido (zapatas)
               {tipo:"cilindro", r, z:[z0,z1], pos:[x,y], esc:[sx,sy]}  (esc: óvalo)
               {tipo:"caja", tam:[x,y,z], pos:[x,y,z], rot:[gx,gy,gz]}
               {tipo:"correa", c1:[x,y], r1, c2:[x,y], r2, seccion:{arriba,abajo,alto}, dientes:{paso,hondo}} ],
      cada parte con color (nombre de PAL o #hex), giro (grados alrededor de z) y repetir (n copias en círculo)} */
(function(){
const PAL={alum:"#b9c0c4",acero:"#c9ced1",aceroOsc:"#8c959a",oscuro:"#181c1f",caucho:"#2e2e2e",friccion:"#6e5646",
  plast:"#e0d0ae",rodillo:"#3a3f43",campana:"#6f777c",campanaClara:"#879095"};
const VISTAS=[45,135,225,315], EL=35.264*Math.PI/180, TINTA=0x15191b;
const URL_THREE="../../../garaje/static/garaje/vendor/three-0.160.0/build/three.module.min.js";
let T=null, prom=null, R=null, actual=null;

function cargar(){
  if(!prom){const t=document.getElementById("esq-three");
    const url=t?URL.createObjectURL(new Blob([t.textContent],{type:"text/javascript"})):(window.ESQ_THREE_URL||URL_THREE);
    prom=import(url).then(m=>(T=m))}
  return prom;
}
const rad=g=>g*Math.PI/180;

/* ---------- geometrías ---------- */
function anilloLinea(r,z,n=64){const p=[];for(let i=0;i<n;i++){const a=i/n*2*Math.PI;p.push(new T.Vector3(r*Math.cos(a),r*Math.sin(a),z))}
  return new T.LineLoop(new T.BufferGeometry().setFromPoints(p),R.linea)}
function torno(P,mat,g){                       // un sólido por tramo del perfil: normales planas en las esquinas
  const n=P.length;
  for(let i=0;i<n;i++){const a=P[i],b=P[(i+1)%n];
    const geo=new T.LatheGeometry([new T.Vector2(a[0],a[1]),new T.Vector2(b[0],b[1])],64);geo.rotateX(Math.PI/2);
    g.add(new T.Mesh(geo,mat));
    const c=P[(i+n-1)%n], u=[a[0]-c[0],a[1]-c[1]], v=[b[0]-a[0],b[1]-a[1]];   // contorno en las esquinas del perfil
    const giro=Math.abs(Math.atan2(u[0]*v[1]-u[1]*v[0],u[0]*v[0]+u[1]*v[1]));
    if(giro>rad(20)&&a[0]>.5)g.add(anilloLinea(a[0],a[1]));}
}
function bordes(geo,g){g.add(new T.LineSegments(new T.EdgesGeometry(geo,30),R.linea))}
function sector(p,mat,g){
  const [ri,ro]=p.r,[a0,a1]=p.ang.map(rad),s=new T.Shape();
  s.absarc(0,0,ro,a0,a1,false);s.absarc(0,0,ri,a1,a0,true);s.closePath();
  const geo=new T.ExtrudeGeometry(s,{depth:p.z[1]-p.z[0],bevelEnabled:false,curveSegments:24});geo.translate(0,0,p.z[0]);
  g.add(new T.Mesh(geo,mat));bordes(geo,g);
}
function cilindro(p,mat,g){
  const geo=new T.CylinderGeometry(p.r,p.r,p.z[1]-p.z[0],40);geo.rotateX(Math.PI/2);
  const e=p.esc||[1,1];geo.scale(e[0],e[1],1);geo.translate((p.pos||[0,0])[0],(p.pos||[0,0])[1],(p.z[0]+p.z[1])/2);
  g.add(new T.Mesh(geo,mat));bordes(geo,g);
}
function caja(p,mat,g){
  const geo=new T.BoxGeometry(...p.tam),m=new T.Mesh(geo,mat);m.position.set(...p.pos);m.rotation.set(...(p.rot||[0,0,0]).map(rad));
  const l=new T.LineSegments(new T.EdgesGeometry(geo),R.linea);l.position.copy(m.position);l.rotation.copy(m.rotation);g.add(m,l);
}
function correa(p,mat,g){                      // barrido de la sección trapezoidal por el recorrido de las dos poleas, con dientes por dentro
  const [x1,y1]=p.c1,[x2,y2]=p.c2,r1=p.r1,r2=p.r2,dx=x2-x1,dy=y2-y1,d=Math.hypot(dx,dy),th=Math.atan2(dy,dx),be=Math.acos((r1-r2)/d);
  const tramos=[{c:[x1,y1],r:r1,a0:th+be,da:2*Math.PI-2*be},{a:th-be,de:[x1,y1,r1],a2:[x2,y2,r2]},{c:[x2,y2],r:r2,a0:th-be,da:2*be},{a:th+be,de:[x2,y2,r2],a2:[x1,y1,r1]}];
  tramos.forEach(t=>t.L=t.c?t.r*t.da:Math.hypot(t.a2[0]+t.a2[2]*Math.cos(t.a)-t.de[0]-t.de[2]*Math.cos(t.a),t.a2[1]+t.a2[2]*Math.sin(t.a)-t.de[1]-t.de[2]*Math.sin(t.a)));
  const L=tramos.reduce((s,t)=>s+t.L,0);
  function en(s){s=((s%L)+L)%L;for(const t of tramos){if(s<=t.L){
      if(t.c){const a=t.a0+s/t.r;return [t.c[0]+t.r*Math.cos(a),t.c[1]+t.r*Math.sin(a),Math.cos(a),Math.sin(a)]}
      const k=s/t.L,ca=Math.cos(t.a),sa=Math.sin(t.a),px=t.de[0]+t.de[2]*ca,py=t.de[1]+t.de[2]*sa,qx=t.a2[0]+t.a2[2]*ca,qy=t.a2[1]+t.a2[2]*sa;
      return [px+(qx-px)*k,py+(qy-py)*k,ca,sa]}s-=t.L}return en(0)}
  const S=p.seccion,D=p.dientes||{paso:L,hondo:0},nd=Math.max(1,Math.round(L/D.paso)),paso=L/nd;
  const FR=[[0,0],[.15,1],[.55,1],[.7,0]];     // fracción del paso → diente (1) o valle (0)
  const pos=[],arm=[];
  for(let i=0;i<nd;i++)for(const [fr,dt] of FR){const [x,y,nx,ny]=en((i+fr)*paso);
    const alto=S.alto-(1-dt)*D.hondo, w=S.arriba+(S.abajo-S.arriba)*(alto/S.alto);   // el valle es más angosto abajo... y menos alto
    const ex=(r,z)=>arm.push([x+nx*r,y+ny*r,z]);
    ex(0,S.arriba/2);ex(0,-S.arriba/2);ex(-alto,-w/2);ex(-alto,w/2);}
  const m=arm.length/4;
  for(let i=0;i<m;i++){const j=(i+1)%m;for(let k=0;k<4;k++){const a=arm[i*4+k],b=arm[i*4+(k+1)%4],c=arm[j*4+(k+1)%4],e=arm[j*4+k];pos.push(...a,...b,...c,...a,...c,...e)}}
  const geo=new T.BufferGeometry();geo.setAttribute("position",new T.Float32BufferAttribute(pos,3));geo.computeVertexNormals();
  g.add(new T.Mesh(geo,mat));
  // contorno: los dos cantos de arriba (lomo) y la línea media del lado
  for(const z of [S.arriba/2,-S.arriba/2]){const q=[];for(let i=0;i<240;i++){const [x,y]=en(i/240*L);q.push(new T.Vector3(x,y,z))}
    g.add(new T.LineLoop(new T.BufferGeometry().setFromPoints(q),R.linea))}
}
// prisma: contorno ({n,r,giro} o [[x,y],...]) extruido en z, con agujeros REALES (círculos, polígonos u óvalos, con repetir)
function contorno(c,cx=0,cy=0){if(Array.isArray(c))return c.map(([x,y])=>new T.Vector2(cx+x,cy+y));
  const n=c.n||32,r=c.r,g=rad(c.giro||0),e=c.ovalo||[1,1],rot=rad(c.rot||0),q=[];
  for(let i=0;i<n;i++){const a=g+i/n*2*Math.PI,x=r*e[0]*Math.cos(a),y=r*e[1]*Math.sin(a);q.push(new T.Vector2(cx+x*Math.cos(rot)-y*Math.sin(rot),cy+x*Math.sin(rot)+y*Math.cos(rot)))}return q}
function prisma(p,mat,g){
  const [px,py]=p.pos||[0,0],s=new T.Shape(contorno(p.contorno,px,py));
  (p.huecos||[]).forEach(h=>{const n=h.repetir||1;for(let k=0;k<n;k++){const a=rad((h.giro0||0)+k*360/n),[hx,hy]=h.pos||[0,0];
    const cx=px+hx*Math.cos(a)-hy*Math.sin(a),cy=py+hx*Math.sin(a)+hy*Math.cos(a);
    s.holes.push(new T.Path(contorno(Object.assign({n:h.n||32},h,{rot:(h.rot||0)+(h.giro0||0)+k*360/n}),cx,cy).reverse()))}});
  const geo=new T.ExtrudeGeometry(s,{depth:p.z[1]-p.z[0],bevelEnabled:false,curveSegments:24});geo.translate(0,0,p.z[0]);
  g.add(new T.Mesh(geo,mat));bordes(geo,g);
}
function esfera(p,mat,g){const geo=new T.SphereGeometry(p.r,14,10);geo.translate((p.pos||[0,0])[0],(p.pos||[0,0])[1],p.z||0);g.add(new T.Mesh(geo,mat))}
function resorte(p,mat,g){
  const v=p.vueltas,L=p.largo,r=p.r,curva=new T.Curve();
  curva.getPoint=(t,o=new T.Vector3())=>o.set(r*Math.cos(t*v*2*Math.PI),r*Math.sin(t*v*2*Math.PI),-t*L);
  const geo=new T.TubeGeometry(curva,v*40,p.alambre/2,8,false);g.add(new T.Mesh(geo,mat));
}
const HACER={torno:(p,m,g)=>torno(p.perfil,m,g),sector,cilindro,caja,correa,prisma,esfera,resorte};
const TIPOS3D=Object.keys(HACER);

function armar(F){
  const pieza=new T.Group();
  F.partes.forEach(p=>{const n=p.repetir||1;
    const mat=new T.MeshLambertMaterial({color:PAL[p.color]||p.color||PAL.alum,side:T.DoubleSide});
    for(let k=0;k<n;k++){const g=new T.Group();HACER[p.tipo](p,mat,g);g.rotation.z=rad((p.giro||0)+k*360/n);pieza.add(g)}});
  const caja3=new T.Box3().setFromObject(pieza),c=caja3.getCenter(new T.Vector3());
  pieza.position.sub(c);
  const raiz=new T.Group();raiz.add(pieza);raiz.rotation.y=Math.PI/2;        // eje de la pieza de lado, como va en la moto
  // radio real (el vértice más lejano del centro): así la pieza llena el visor en las 4 vistas sin cortarse al girar
  let r2=0;const v=new T.Vector3();pieza.updateMatrixWorld(true);
  pieza.traverse(o=>{const p=o.isMesh&&o.geometry.attributes.position;if(!p)return;
    for(let i=0;i<p.count;i++){v.fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld);r2=Math.max(r2,v.lengthSq())}});
  return {raiz,radio:Math.sqrt(r2)};
}

/* ---------- escena compartida ---------- */
function iniciarR(){
  const renderer=new T.WebGLRenderer({antialias:true,alpha:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
  const scene=new T.Scene(), cam=new T.OrthographicCamera(-1,1,1,-1,.1,5000);
  scene.add(new T.HemisphereLight(0xfff4e2,0x2a3236,1.6));
  const luz=new T.DirectionalLight(0xffffff,2.2);luz.position.set(-.6,1,.8);cam.add(luz);scene.add(cam);
  R={renderer,scene,cam,linea:new T.LineBasicMaterial({color:TINTA})};
}
function limpiar(){if(!actual)return;R.scene.remove(actual.raiz);
  actual.raiz.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material&&o.material!==R.linea)o.material.dispose()});
  actual.ro&&actual.ro.disconnect();cancelAnimationFrame(actual.raf);actual=null}

function montar(el,F,nombre){
  const lienzo=el.querySelector(".esq-v3d-lienzo"),estado=el.querySelector(".esq-v3d-estado");
  const t0=performance.now();
  cargar().then(()=>{
    if(!el.isConnected)return;
    if(!R)iniciarR();
    limpiar();
    const {raiz,radio}=armar(F);R.scene.add(raiz);
    const A={raiz,radio,el,az:rad(VISTAS[0]),el_:EL,vista:0,raf:0};actual=A;
    lienzo.appendChild(R.renderer.domElement);R.renderer.domElement.setAttribute("aria-hidden","true");
    const dibujar=()=>{const w=lienzo.clientWidth,h=lienzo.clientHeight;if(!w||!h)return;
      R.renderer.setSize(w,h,false);const s=radio*1.04,asp=w/h;
      Object.assign(R.cam,asp>=1?{left:-s*asp,right:s*asp,top:s,bottom:-s}:{left:-s,right:s,top:s/asp,bottom:-s/asp});
      R.cam.updateProjectionMatrix();
      const d=radio*4;R.cam.position.set(d*Math.cos(A.el_)*Math.sin(A.az),d*Math.sin(A.el_),d*Math.cos(A.el_)*Math.cos(A.az));R.cam.lookAt(0,0,0);
      R.renderer.render(R.scene,R.cam)};
    A.dibujar=dibujar;
    A.ro=new ResizeObserver(dibujar);A.ro.observe(lienzo);
    dibujar();
    el.dataset.ms=Math.round(performance.now()-t0);el.classList.add("esq-v3d-listo");
    const rot=i=>`Vista ${i+1} de 4`;
    const decir=()=>{estado.textContent=A.vista<0?"Vista libre":rot(A.vista);lienzo.setAttribute("aria-label",`Modelo 3D de ${nombre}, ${estado.textContent.toLowerCase()}`)};
    decir();
    function ir(paso){
      const base=A.vista<0?Math.round((A.az*180/Math.PI-45)/90):A.vista;
      const destino=base+paso, a0=A.az, a1=rad(45+destino*90), e0=A.el_;
      A.vista=((destino%4)+4)%4;decir();
      cancelAnimationFrame(A.raf);
      if(matchMedia("(prefers-reduced-motion:reduce)").matches){A.az=a1;A.el_=EL;dibujar();return}
      const t1=performance.now(),dur=650;
      const paso_=t=>{const k=Math.min(1,(t-t1)/dur),e=k<.5?4*k*k*k:1-Math.pow(-2*k+2,3)/2;
        A.az=a0+(a1-a0)*e;A.el_=e0+(EL-e0)*e;dibujar();if(k<1)A.raf=requestAnimationFrame(paso_)};
      A.raf=requestAnimationFrame(paso_);
    }
    el.querySelector(".esq-v3d-ant").onclick=()=>ir(-1);
    el.querySelector(".esq-v3d-sig").onclick=()=>ir(1);
    // arrastrar para girar (en el celular solo de lado: arriba/abajo sigue moviendo la página)
    let arr=null;
    lienzo.onpointerdown=e=>{arr={x:e.clientX,y:e.clientY,az:A.az,el:A.el_,t:e.pointerType};lienzo.setPointerCapture(e.pointerId);cancelAnimationFrame(A.raf)};
    lienzo.onpointermove=e=>{if(!arr)return;const dx=e.clientX-arr.x,dy=e.clientY-arr.y;
      if(Math.abs(dx)<3&&Math.abs(dy)<3)return;
      A.az=arr.az-dx*.012;if(arr.t==="mouse")A.el_=Math.max(-1.2,Math.min(1.2,arr.el+dy*.012));
      A.vista=-1;dibujar()};
    lienzo.onpointerup=lienzo.onpointercancel=()=>{if(arr&&A.vista<0)decir();arr=null};
  }).catch(err=>{el.classList.add("esq-v3d-error");estado.textContent="No se pudo cargar el modelo 3D.";console.warn("3D:",err)});
}
function soltar(){if(actual)limpiar()}
// captura(vista): para las pruebas (dibuja esa vista sin animar y devuelve el PNG)
function captura(v){if(!actual)return null;if(v!=null){actual.az=rad(VISTAS[v]);actual.el_=EL}actual.dibujar();return R.renderer.domElement.toDataURL()}
function medir(n=30){if(!actual)return null;const gl=R.renderer.getContext(),px=new Uint8Array(4),t0=performance.now();
  for(let i=0;i<n;i++){actual.az+=.05;actual.dibujar()}gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,px);   // readPixels espera a la GPU
  const i=R.renderer.info.render;return {msCuadro:+((performance.now()-t0)/n).toFixed(2),llamadas:i.calls,triangulos:i.triangles}}
window.Esquema3D={montar,soltar,captura,medir,TIPOS:TIPOS3D,get estado(){return actual?{az:actual.az,vista:actual.vista}:null}};
})();
