/* esquema.js: motor de las láminas del esquema pedagógico de TallerYa (despiece, ficha, «Cómo funciona», «Si falla», «Cuándo»).
   Uso: Esquema.iniciar(datos, arte). datos = JSON de la lámina (datos/*.json); arte = ESQ_ARTE[datos.arte] (datos/*-arte.js).
   La página necesita <div id="esquema"></div>; el motor lo reemplaza por la lámina completa. Clases: todas con esq-. */
(function(){
"use strict";
function PLANTILLA(D,A){return `<div class="esq-envoltura">
  <header class="esq-cabeza">
    <div class="esq-cinta">${D.cabeza.cinta}</div>
    <h1 class="esq-titular">${D.cabeza.titulo}</h1>
    <p class="esq-aviso">${D.cabeza.aviso}</p>
  </header>

  <div class="esq-escenario" id="despiece">
    <div class="esq-papel esq-visor">
      <div class="esq-visor-barra">
        <div class="esq-visor-tit">
          <p class="esq-titular">${D.visor.titulo}</p>
          <p class="esq-sub">${D.visor.sub}</p>
        </div>
        <div class="esq-visor-modo esq-pestanas" role="tablist" aria-label="${D.textos.pestanasAria}">
          <button type="button" role="tab" id="t-piezas" aria-controls="p-piezas" aria-selected="true">Piezas</button>
          <button type="button" role="tab" id="t-funciona" aria-controls="p-funciona" aria-selected="false" tabindex="-1">Cómo funciona</button>
          <button type="button" role="tab" id="t-cadenas" aria-controls="p-cadenas" aria-selected="false" tabindex="-1">Si falla</button>
          <button type="button" role="tab" id="t-plan" aria-controls="p-plan" aria-selected="false" tabindex="-1">Cuándo</button>
        </div>
      </div>

      <!-- Piezas: armado y despiece -->
      <div class="esq-panel" id="p-piezas" role="tabpanel" aria-labelledby="t-piezas">
        <div class="esq-lienzo">
          <svg id="lamina" viewBox="0 0 900 700" role="group" aria-label="${D.textos.laminaAria}">
            <defs id="defs"></defs>
            <rect x="-300" y="-300" width="1500" height="1300" fill="url(#gFondo)" aria-hidden="true"/>
            <g id="capas"></g>
          </svg>
        </div>
        <div class="esq-vista-fila">
          <span class="esq-vista-et" id="vistaEt">Dibujo</span>
          <div class="esq-visor-modo esq-vista-sel" role="group" aria-labelledby="vistaEt">
            <button type="button" id="vNormal" aria-pressed="true">Normal</button>
            <button type="button" id="vTrans" aria-pressed="false">Transparente</button>
          </div>
          <p class="esq-pista" id="pista" aria-hidden="true">👆 Toca una pieza</p>
          <div class="esq-zoom" role="group" aria-label="Zoom del dibujo">
            <button type="button" class="esq-zoom-b" id="zMas" aria-label="Acercar el dibujo">+</button>
            <button type="button" class="esq-zoom-b" id="zMenos" aria-label="Alejar el dibujo" disabled>−</button>
            <button type="button" class="esq-zoom-b" id="zVer" aria-label="Ver el dibujo completo" disabled>⤢</button>
          </div>
        </div>
        <div class="esq-herr">
          <button type="button" class="esq-btn esq-btn-lava" id="bTodo">Desarmar</button>
          <button type="button" class="esq-boton-paso" id="bAtras" aria-label="Paso anterior">◀</button>
          <button type="button" class="esq-boton-paso" id="bAdel" aria-label="Paso siguiente">▶</button>
          <button type="button" class="esq-interruptor" id="iNum" aria-pressed="false">Números</button>
        </div>
        <p class="esq-paso" id="textoPaso" aria-live="polite">${D.textoArmado}</p>
        <div class="esq-fichas-chips" id="chips" role="group" aria-label="Piezas de la lámina"></div>
      </div>

      <!-- Cómo funciona -->
      <div class="esq-panel esq-func" id="p-funciona" role="tabpanel" aria-labelledby="t-funciona" hidden>
      <p class="esq-intro">${D.textos.introFunciona}</p>
      <div class="esq-desliza" id="fnDesliza">
      ${A.funciona.svg}
      </div>
      <div class="esq-herr">
        <button type="button" class="esq-btn esq-btn-lava" id="fnPlay">▶ Reproducir</button>
        <button type="button" class="esq-boton-paso" id="fnAtras" aria-label="Paso anterior">◀</button>
        <button type="button" class="esq-boton-paso" id="fnAdel" aria-label="Paso siguiente">▶</button>
      </div>
      <p class="esq-texto" id="fnTexto" aria-live="polite"></p>
      </div>

      <!-- Si falla, qué arrastra -->
      <div class="esq-panel" id="p-cadenas" role="tabpanel" aria-labelledby="t-cadenas" hidden>
        <p class="esq-intro">${D.textos.introCadenas}</p>
        <div class="esq-cadenas" id="listaCadenas"></div>
      </div>

      <!-- Cuándo revisar y cambiar -->
      <div class="esq-panel" id="p-plan" role="tabpanel" aria-labelledby="t-plan" hidden>
        <p class="esq-intro">${D.textos.introCuando}</p>
    <div class="esq-tabla">
      <table>
        <thead><tr><th>Qué</th><th>Cuándo</th><th>De dónde sale</th></tr></thead>
        <tbody>${D.cuando.map(r=>`<tr><td>${r.que}</td><td>${r.cuando}</td><td>${r.fuente}</td></tr>`).join("\n")}</tbody>
      </table>
    </div>
      </div>
    </div>
    <aside class="esq-papel esq-fpieza" id="ficha" aria-label="Ficha de la pieza">
      <p class="esq-vacia">Toca una pieza del dibujo (o un número) para ver qué es, cómo falla y qué se cambia de verdad.</p>
    </aside>
  </div>

  <details class="esq-papel esq-fuentes-plegadas">
    <summary>De dónde sale esta información (qué es seguro, qué es aproximado y fuentes)</summary>
    <div class="esq-dos">
      <div class="esq-tarjeta" style="padding:12px 18px">
        <h3>Seguro</h3>
        <ul>${D.fuentes.seguro.map(x=>`<li>${x}</li>`).join("\n")}</ul>
      </div>
      <div class="esq-tarjeta" style="padding:12px 18px">
        <h3>Aproximado</h3>
        <ul>${D.fuentes.aproximado.map(x=>`<li>${x}</li>`).join("\n")}</ul>
      </div>
    </div>
    <div class="esq-tarjeta" style="padding:12px 18px;margin-top:14px">
      <h3>Fuentes</h3>
      <ul class="esq-fuentes">${D.fuentes.lista.map(x=>`<li>${x}</li>`).join("\n")}</ul>
    </div>
  </details>
  <footer>${D.pie}</footer>
<div class="esq-hoja" id="hoja" hidden>
  <span class="esq-n" id="hojaN"></span><span class="esq-t" id="hojaT"></span>
  <button type="button" class="esq-btn esq-btn-lava" id="hojaVer">Ver ficha</button>
</div>
</div>`;}
window.Esquema={iniciar(D,A){
const montaje=document.getElementById("esquema");montaje.outerHTML=PLANTILLA(D,A);
document.getElementById("defs").innerHTML=A.defs;if(A.montar)A.montar();
// carcasas: en Transparente se aclaran (y no se tocan) para ver lo de adentro; en rayos X (pieza oculta elegida) se aclaran más
// formato: [{"id":"3","transparente":0.26,"rayosx":0.22,"brillo":true}]  (brillo = borde naranja en Transparente)
(()=>{const C=D.carcasas||[];if(!C.length)return;const st=document.createElement("style");st.id="esq-carcasas";
  st.textContent=C.map(c=>`#lamina.esq-transparente #pz-${c.id} .esq-arte{opacity:${c.transparente};pointer-events:none${c.brillo?";filter:drop-shadow(0 0 1.5px #ff9a3c)":""}}\n#lamina.esq-rayosx #pz-${c.id} .esq-arte{opacity:${c.rayosx}}`).join("\n");
  document.head.appendChild(st)})();
const f=n=>Math.round(n*10)/10;
// piezas comunes (piezas-comunes.js): arte 2D y forma3d salen de las mismas medidas; perfiles compartidos con «@nombre»
const COMUN=window.ESQ_COMUN&&D.piezas.some(p=>p.comun)?ESQ_COMUN.crear(D.comun,A.marcos):null;
const perfilDe=v=>typeof v==="string"&&v[0]==="@"?(D.perfiles||{})[v.slice(1)]:v;
D.piezas.forEach(p=>{if(p.p&&p.p.perfil)p.p.perfil=perfilDe(p.p.perfil);const F=D.fichas[p.n||p.id];
  if(p.comun&&F&&!F.forma3d&&!p.sin3d&&window.ESQ_COMUN)F.forma3d=ESQ_COMUN.forma3d(p.comun,p.p)});
Object.values(D.fichas).forEach(F=>{if(F.forma3d)F.forma3d.partes.forEach(q=>{if(q.perfil)q.perfil=perfilDe(q.perfil)})});
const PIEZAS=D.piezas.map(p=>Object.assign({},p,{arte:()=>p.comun?COMUN.arte(p):A[p.arte](...(p.args||[]))}));
const PASOS=D.pasos, TXT_ARMADO=D.textoArmado, FICHAS=D.fichas, ORDEN_CHIPS=D.ordenChips, OCULTAS=D.ocultas, VB_ARM=D.encuadreArmado, FN=D.funciona.pasos, CADENAS=D.cadenas;
const NOMBRES_TMP=n=>D.nombres[n]||n;
/* ============================================================
   Construcción del SVG
   ============================================================ */
const capas=document.getElementById("capas");
// contexto «alPrincipio»: se pinta antes de todas las piezas, así no tapa ningún número ni su área de toque
let html=(D.contexto||[]).filter(c=>c.alPrincipio).map(c=>A[c.arte]()).join("");
PIEZAS.forEach(p=>{
  const [ax,ay]=p.anc, lx=ax+p.et[0], ly=ay+p.et[1];
  html+=`<g class="esq-pz" id="pz-${p.id}" data-n="${p.n}">
    <g class="esq-arte"><g class="esq-esc${p.chica?" esq-chica":""}">${p.arte()}</g></g>
    <g class="esq-et esq-et-${p.vis}"><line x1="${f(ax)}" y1="${f(ay)}" x2="${f(lx)}" y2="${f(ly)}"/><g class="esq-bola" data-x="${f(lx)}" data-y="${f(ly)}" tabindex="0" role="button" aria-label="Ver la ficha de la pieza ${p.n}: ${NOMBRES_TMP(p.n)}"><circle class="esq-toque" cx="${f(lx)}" cy="${f(ly)}" r="25"/><circle class="esq-disco" cx="${f(lx)}" cy="${f(ly)}" r="10"/><text x="${f(lx)}" y="${f(ly)}">${p.n}</text></g></g>
  </g>`;
  (D.contexto||[]).forEach(c=>{if(c.despuesDe===p.id)html+=A[c.arte]()});
});
capas.innerHTML=html;
// contexto (piezas de otras láminas): «alFrente» se pasa encima de todo, «alFinal» se agrega al final
(D.contexto||[]).forEach(c=>{if(c.alFrente)capas.appendChild(capas.querySelector("."+c.clase));if(c.alFinal)capas.insertAdjacentHTML("beforeend",A[c.arte]())});

/* ============================================================
   Fichas de cada pieza
   ============================================================ */
const CAUSA={desgaste:"Desgaste",calor:"Calor",humedad:"Humedad",maluso:"Mal uso",golpe:"Golpe",edad:"Edad"};
const CAUSA_DEF={desgaste:"se gasta con el uso normal, frenada tras frenada",calor:"temperatura alta: bajadas largas, freno pegado, frenar mucho",humedad:"agua y óxido: lluvia, lavadas, líquido de frenos viejo",maluso:"montaje o manejo incorrecto: herramienta equivocada, apretar de más, productos que no van",golpe:"caídas, huecos o golpes en la rueda",edad:"el caucho y los materiales envejecen aunque la moto ruede poco"};
const DIF={facil:"Lo puedes hacer tú",media:"Con herramienta y algo de práctica",taller:"Mejor en el taller"};
const nombreDe=k=>FICHAS[k]?FICHAS[k].nombre:k;
const etiq=k=>FICHAS[k]&&FICHAS[k].ctx?"·":k;

/* ---------- chips ---------- */
document.getElementById("chips").innerHTML=ORDEN_CHIPS.map(k=>{const c=FICHAS[k].ctx;
  return `<button class="esq-chip${c?' esq-ctx':''}" data-k="${k}" title="${FICHAS[k].nombre}" aria-label="${c?'':k+': '}${FICHAS[k].nombre}"><span class="esq-n">${c?'·':k}</span>${FICHAS[k].nombre}</button>`}).join("");

/* ---------- selección ---------- */
const svg=document.getElementById("lamina");
let seleccion=null;
function seleccionar(k,{desplazar=false}={}){
  seleccion=k;
  document.querySelectorAll(".esq-pz").forEach(g=>g.classList.toggle("esq-sel",g.dataset.n===k));
  document.querySelectorAll(".esq-chip").forEach(b=>b.classList.toggle("esq-sel",b.dataset.k===k));
  svg.classList.toggle("esq-haysel",!!document.querySelector(".esq-pz.esq-sel"));
  svg.classList.toggle("esq-rayosx",paso===0 && OCULTAS.includes(k));
  pintarFicha(k);
  document.getElementById("pista").classList.add("esq-oculta");
  mostrarHoja(k);
  if(desplazar){activarPestana(document.getElementById("t-piezas"));document.getElementById("despiece").scrollIntoView({behavior:REDUCIDO_SEL()?"auto":"smooth",block:"start"})}
}
function REDUCIDO_SEL(){return matchMedia("(prefers-reduced-motion:reduce)").matches}

/* ---------- pestañas accesibles (flechas, Inicio, Fin) ---------- */
const PESTANAS=[...document.querySelectorAll('.esq-pestanas [role="tab"]')];
function activarPestana(tab,enfocar){
  PESTANAS.forEach(t=>{const si=t===tab;t.setAttribute("aria-selected",si);t.tabIndex=si?0:-1;
    document.getElementById(t.getAttribute("aria-controls")).hidden=!si});
  if(enfocar)tab.focus();
  if(tab.id==="t-piezas")setTimeout(escalarEtiquetas,0);
}
PESTANAS.forEach((t,i)=>{
  t.addEventListener("click",()=>activarPestana(t));
  t.addEventListener("keydown",e=>{const n={ArrowRight:i+1,ArrowLeft:i-1,Home:0,End:PESTANAS.length-1}[e.key];
    if(n===undefined)return;e.preventDefault();activarPestana(PESTANAS[(n+PESTANAS.length)%PESTANAS.length],true)});
});

/* ---------- celular: barra fija con la pieza elegida y «Ver ficha» (sin bajar la página sola) ---------- */
const hoja=document.getElementById("hoja"), fichaEl=document.getElementById("ficha");
let fichaVisible=false;
if("IntersectionObserver" in window){new IntersectionObserver(es=>{fichaVisible=es[0].isIntersecting;if(fichaVisible)hoja.hidden=true;else if(seleccion&&innerWidth<960)hoja.hidden=false},{threshold:.15}).observe(fichaEl)}
function mostrarHoja(k){
  if(innerWidth>=960||fichaVisible){hoja.hidden=true;return}
  const F=FICHAS[k];if(!F)return;
  document.getElementById("hojaN").textContent=F.ctx?"·":k;
  document.getElementById("hojaT").textContent=F.nombre;
  hoja.hidden=false;
}
document.getElementById("hojaVer").addEventListener("click",()=>{
  fichaEl.scrollIntoView({behavior:REDUCIDO_SEL()?"auto":"smooth",block:"start"});
  const h=fichaEl.querySelector("h3");if(h)h.focus({preventScroll:true});hoja.hidden=true;
});
function boton(k){return `<button data-k="${k}">${FICHAS[k]&&!FICHAS[k].ctx?k+" · ":""}${nombreDe(k)}</button>`}
function pintarFicha(k){
  const F=FICHAS[k], el=document.getElementById("ficha");
  if(!F){el.innerHTML='<p class="esq-vacia">Sin ficha.</p>';return}
  const filas=[], mas=[];
  if(F.que)filas.push(`<dt>Qué es</dt><dd>${F.que}</dd>`);
  if(F.sirve)mas.push(`<dt>Para qué sirve</dt><dd>${F.sirve}</dd>`);
  if(F.fallas.length)filas.push(`<dt>Cómo falla y por qué</dt><dd><ul>${F.fallas.map(([c,t])=>`<li><span class="esq-causa esq-c-${c}" title="${CAUSA[c]}: ${CAUSA_DEF[c]}">${CAUSA[c]}</span>${t}</li>`).join("")}</ul><details class="esq-leyenda"><summary>Qué significa cada etiqueta</summary><ul>${[...new Set(F.fallas.map(x=>x[0]))].map(c=>`<li><span class="esq-causa esq-c-${c}">${CAUSA[c]}</span>${CAUSA_DEF[c]}</li>`).join("")}</ul></details></dd>`);
  if(F.sintomas.length)filas.push(`<dt>Síntomas</dt><dd><ul>${F.sintomas.map(s=>`<li>${s}</li>`).join("")}</ul></dd>`);
  if(F.cuando)filas.push(`<dt>Cuándo revisar o cambiar</dt><dd>${F.cuando}</dd>`);
  if(F.decision)filas.push(`<dt>¿Se repara o se cambia?</dt><dd><span class="esq-decision ${F.decision==='repara'?'esq-d-repara':'esq-d-cambia'}">${F.decision==='repara'?'Se repara':'Se cambia'}</span><p style="margin:.4em 0 0">${F.compra}</p></dd>`);
  if(F.conecta.length)mas.push(`<dt>Se conecta con</dt><dd class="esq-enlaces">${F.conecta.map(boton).join("")}</dd>`);
  if(F.efectos.length)mas.push(`<dt>Si falla, ¿qué les pasa a las demás?</dt><dd>${F.efectos.map(([o,t])=>`<div class="esq-efecto">${boton(o)}${t}</div>`).join("")}</dd>`);
  const cert=F.certeza.length?`<div class="esq-certeza">${F.certeza.map(([s,t])=>`<div><span class="${s==='ok'?'esq-s-ok':'esq-s-ap'}">${s==='ok'?'Seguro':'Aproximado'}:</span> ${t}</div>`).join("")}</div>`:"";
  el.innerHTML=`<div class="esq-cab"><div class="esq-badge${F.ctx?' esq-ctx':''}">${F.ctx?'otra':k}</div><div><h3 tabindex="-1">${F.nombre}</h3><div class="esq-cat">${F.cat}</div>${F.dif?`<div class="esq-dif">${DIF[F.dif]}</div>`:""}</div></div>${F.forma3d&&window.Esquema3D?`<div class="esq-v3d"><div class="esq-v3d-lienzo" role="img" aria-label="Modelo 3D de ${F.nombre}"></div><div class="esq-v3d-barra"><button type="button" class="esq-v3d-ant" aria-label="Girar a la vista anterior">◀</button><span class="esq-v3d-estado" aria-live="polite">Cargando el modelo 3D…</span><button type="button" class="esq-v3d-sig" aria-label="Girar a la vista siguiente">▶</button></div></div>`:""}<dl>${filas.join("")}</dl>${mas.length||cert?`<details class="esq-mas"${innerWidth>=960?" open":""}><summary>Para qué sirve, con qué se conecta y qué arrastra si falla</summary><dl>${mas.join("")}</dl>${cert}</details>`:""}`;
  if(window.Esquema3D){const v=el.querySelector(".esq-v3d");if(v)Esquema3D.montar(v,F.forma3d,F.nombre);else Esquema3D.soltar()}
}
document.addEventListener("click",e=>{
  const b=e.target.closest("button[data-k]");
  if(b){seleccionar(b.dataset.k,{desplazar:!!b.closest("#p-cadenas")});return}
  const g=e.target.closest(".esq-pz");
  if(g){seleccionar(g.dataset.n);return}
  const c=e.target.closest("[data-ctx]");
  if(c){seleccionar(c.dataset.ctx)}
});
document.addEventListener("keydown",e=>{
  const b=e.target.closest&&e.target.closest(".esq-bola");
  if((e.key==="Enter"||e.key===" ")&&b){e.preventDefault();seleccionar(b.closest(".esq-pz").dataset.n);const h=document.querySelector("#ficha h3");if(h)h.focus()}
});

/* ---------- encuadre: armado se ve de cerca, despiece completo ---------- */
let VB_EXP=[0,0,900,700];
// El encuadre del despiece se calcula con las posiciones finales de las piezas y sus números
function calcularVBExp(){
  const suma={};
  PASOS.forEach(P=>{for(const [id,[dx,dy]] of Object.entries(P.m)){suma[id]=suma[id]||[0,0];suma[id][0]+=dx;suma[id][1]+=dy}});
  let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;
  PIEZAS.forEach(p=>{const g=document.getElementById("pz-"+p.id), s=suma[p.id]||[0,0];
    const b=g.querySelector(".esq-arte").getBBox(), m=p.chica?Math.max(b.width,b.height)*.25:0;
    const lx=p.anc[0]+p.et[0], ly=p.anc[1]+p.et[1];
    x0=Math.min(x0,b.x-m+s[0],lx-20+s[0]);y0=Math.min(y0,b.y-m+s[1],ly-20+s[1]);
    x1=Math.max(x1,b.x+b.width+m+s[0],lx+20+s[0]);y1=Math.max(y1,b.y+b.height+m+s[1],ly+20+s[1]);});
  x0-=14;y0-=14;x1+=14;y1+=14;
  let w=x1-x0,h=y1-y0;const asp=900/700;
  if(w/h<asp){const nw=h*asp;x0-=(nw-w)/2;w=nw}else{const nh=w/asp;y0-=(nh-h)/2;h=nh}
  VB_EXP=[x0,y0,w,h].map(f);
}
let vbActual=VB_ARM.slice(), vbAnim=null;
function escalarEtiquetas(){
  const px=svg.getBoundingClientRect().width||900;
  const s=Math.max(.8,(vbActual[2]/px)*9/10);                 // número de ~18 px en pantalla; su área de toque (círculo invisible) mide ~45 px
  document.querySelectorAll(".esq-bola").forEach(b=>{const x=+b.dataset.x,y=+b.dataset.y;
    b.setAttribute("transform",s===1?"":`translate(${x} ${y}) scale(${f(s)}) translate(${-x} ${-y})`)});
  radiosToque(s);
}
// v8: el área de toque de cada número (círculo invisible) no pasa de la mitad de la distancia a su vecino tocable más cercano
function radiosToque(s){
  const abiertos=svg.classList.contains("esq-explotado")||svg.classList.contains("esq-transparente"), pts=[];
  document.querySelectorAll(".esq-pz").forEach(g=>{const e=g.querySelector(".esq-et");
    if(!abiertos&&e.classList.contains("esq-et-exp"))return;
    const m=/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(g.style.transform||""), b=e.querySelector(".esq-bola");
    pts.push({c:b.querySelector(".esq-toque"),x:+b.dataset.x+(m?+m[1]:0),y:+b.dataset.y+(m?+m[2]:0)})});
  pts.forEach(p=>{let d=1e9;pts.forEach(q=>{if(q!==p)d=Math.min(d,Math.hypot(p.x-q.x,p.y-q.y))});
    p.c.setAttribute("r",f(Math.min(25,d/2/s)))});
}
function encuadrar(destino,ms=650){
  cancelAnimationFrame(vbAnim);
  const ini=vbActual.slice(), t0=performance.now(), dur=matchMedia("(prefers-reduced-motion:reduce)").matches?0:ms;
  const paso_=t=>{const p=dur?Math.min(1,(t-t0)/dur):1, e=p<.5?2*p*p:1-Math.pow(-2*p+2,2)/2;
    vbActual=ini.map((v,i)=>v+(destino[i]-v)*e);svg.setAttribute("viewBox",vbActual.map(f).join(" "));escalarEtiquetas();
    if(p<1)vbAnim=requestAnimationFrame(paso_)};
  vbAnim=requestAnimationFrame(paso_);
}
svg.setAttribute("viewBox",VB_ARM.join(" "));
calcularVBExp();
// v9: en computador (≥960 px) el dibujo usa el alto que deja la pantalla bajo el lienzo, menos la fila de controles (≈76 px)
const lienzoEl=svg.closest(".esq-lienzo");
function medirAlto(){if(innerWidth<960){document.documentElement.style.removeProperty("--esq-alto");return}
  const lr=lienzoEl.getBoundingClientRect(),arriba=lr.top+scrollY;
  // v10: se reserva lo que mide de verdad la fila de controles bajo el dibujo (antes 76 px fijos): a 1280×800 el dibujo pasa de 453 a ~462 px
  const fila=[...document.querySelectorAll("#p-piezas .esq-herr>*,#p-piezas .esq-vista-sel,#p-piezas .esq-zoom")].map(e=>e.getBoundingClientRect()).filter(r=>r.height);
  const reserva=fila.length?Math.max(...fila.map(r=>r.bottom))-lr.bottom+6:76;
  document.documentElement.style.setProperty("--esq-alto",Math.max(340,innerHeight-arriba-reserva)+"px")}
medirAlto();addEventListener("resize",()=>{medirAlto();escalarEtiquetas()});
addEventListener("resize",()=>{if(zoom>1&&innerWidth>700)fijarZoom(1,null,null,true);escalarEtiquetas()});

/* ---------- v8: zoom del dibujo en el celular (+ − ⤢ y pellizco; con zoom, un dedo arrastra el dibujo) ---------- */
let zoom=1;
const ZMAX=4, zMas=document.getElementById("zMas"), zMenos=document.getElementById("zMenos"), zVer=document.getElementById("zVer");
function estadoZoom(){zMas.disabled=zoom>=ZMAX-.01;zMenos.disabled=zVer.disabled=zoom<=1.01;svg.classList.toggle("esq-ampliado",zoom>1.01);sugerirZoom()}
// v10: en el celular, si en el despiece quedan números a menos de 24 px, el botón + se resalta y dice por qué
function sugerirZoom(){
  let sug=false;
  if(innerWidth<=700&&zoom<=1.01&&paso>0){const c=[...svg.querySelectorAll(".esq-bola")].map(b=>b.getBoundingClientRect()).filter(r=>r.width).map(r=>[r.x+r.width/2,r.y+r.height/2]);
    for(let i=0;i<c.length&&!sug;i++)for(let j=i+1;j<c.length;j++)if(Math.hypot(c[i][0]-c[j][0],c[i][1]-c[j][1])<24){sug=true;break}}
  zMas.classList.toggle("esq-zoom-sugerido",sug);
  // v11: con más de 20 números, además la pista lo dice en palabras (y vuelve a lo que decía al dejar de sugerir)
  const pz=document.getElementById("pista"), muchos=new Set(D.piezas.map(p=>p.n)).size>20;
  if(pz&&muchos&&sug&&!pz.dataset.zoom){pz.dataset.zoom=pz.classList.contains("esq-oculta")?"oculta":"visible";pz.dataset.orig=pz.textContent;pz.textContent="Usa + para acercar";pz.classList.remove("esq-oculta")}
  else if(pz&&!sug&&pz.dataset.zoom){pz.textContent=pz.dataset.orig;pz.classList.toggle("esq-oculta",pz.dataset.zoom==="oculta");delete pz.dataset.zoom}
  zMas.setAttribute("aria-label",sug?"Acercar el dibujo: hay números muy juntos":"Acercar el dibujo");zMas.title=sug?"Hay números muy juntos: acerca el dibujo":"";
}
// z = aumento sobre el encuadre del momento (armado o despiece); (cx,cy) = punto del dibujo que queda al centro
function fijarZoom(z,cx,cy,animar){
  const B=paso===0?VB_ARM:VB_EXP;zoom=Math.min(ZMAX,Math.max(1,z));
  if(cx==null){cx=vbActual[0]+vbActual[2]/2;cy=vbActual[1]+vbActual[3]/2}
  const w=B[2]/zoom,h=B[3]/zoom;
  const d=[Math.min(Math.max(cx-w/2,B[0]),B[0]+B[2]-w),Math.min(Math.max(cy-h/2,B[1]),B[1]+B[3]-h),w,h];
  if(animar)encuadrar(d,260);else{cancelAnimationFrame(vbAnim);vbActual=d;svg.setAttribute("viewBox",d.map(f).join(" "));escalarEtiquetas()}
  estadoZoom();
}
zMas.addEventListener("click",()=>fijarZoom(zoom*1.6,null,null,true));
zMenos.addEventListener("click",()=>fijarZoom(zoom/1.6,null,null,true));
zVer.addEventListener("click",()=>fijarZoom(1,null,null,true));
// Pellizco y arrastre con Pointer Events; un gesto que se movió no cuenta como toque de un número
const dedos=new Map();let gesto=null, anularClic=false;
const aDibujo=(x,y)=>{const r=svg.getBoundingClientRect();return[vbActual[0]+(x-r.left)*vbActual[2]/r.width,vbActual[1]+(y-r.top)*vbActual[3]/r.height]};
function iniciarGesto(){
  const p=[...dedos.values()];
  if(p.length>=2){const m=[(p[0][0]+p[1][0])/2,(p[0][1]+p[1][1])/2];gesto={tipo:2,d0:Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1])||1,z0:zoom,ancla:aDibujo(m[0],m[1])}}
  else if(p.length===1&&zoom>1.01)gesto={tipo:1,ini:p[0],vb0:vbActual.slice()};
  else gesto=null;
}
svg.addEventListener("pointerdown",e=>{if(!dedos.size)anularClic=false;if(e.pointerType==="mouse")return;dedos.set(e.pointerId,[e.clientX,e.clientY]);iniciarGesto()});
svg.addEventListener("pointermove",e=>{
  if(!dedos.has(e.pointerId))return;dedos.set(e.pointerId,[e.clientX,e.clientY]);if(!gesto)return;
  const p=[...dedos.values()], r=svg.getBoundingClientRect(), B=paso===0?VB_ARM:VB_EXP;
  if(gesto.tipo===2&&p.length>=2){
    const z=Math.min(ZMAX,Math.max(1,gesto.z0*Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1])/gesto.d0)), w=B[2]/z, h=B[3]/z;
    const m=[(p[0][0]+p[1][0])/2,(p[0][1]+p[1][1])/2];
    // el punto del dibujo que estaba bajo los dedos sigue bajo los dedos
    const x0=gesto.ancla[0]-(m[0]-r.left)*w/r.width, y0=gesto.ancla[1]-(m[1]-r.top)*h/r.height;
    fijarZoom(z,x0+w/2,y0+h/2,false);anularClic=true;
  }else if(gesto.tipo===1){
    const dx=p[0][0]-gesto.ini[0], dy=p[0][1]-gesto.ini[1];
    if(!anularClic&&Math.hypot(dx,dy)<8)return;
    anularClic=true;const v=gesto.vb0;fijarZoom(zoom,v[0]+v[2]/2-dx*v[2]/r.width,v[1]+v[3]/2-dy*v[3]/r.height,false);
  }
});
const soltar=e=>{if(dedos.delete(e.pointerId))iniciarGesto()};
svg.addEventListener("pointerup",soltar);svg.addEventListener("pointercancel",soltar);
svg.addEventListener("click",e=>{if(anularClic){e.stopPropagation();e.preventDefault();anularClic=false}},true);

/* ---------- despiece paso a paso ---------- */
let paso=0, temporizador=null;
function aplicar(k){
  const antes=paso;
  paso=k;
  setTimeout(sugerirZoom,900);
  if((antes===0)!==(k===0)||k===0){zoom=1;encuadrar(k===0?VB_ARM:VB_EXP);estadoZoom()}
  const suma={};
  for(let i=0;i<k;i++){for(const [id,[dx,dy]] of Object.entries(PASOS[i].m)){suma[id]=suma[id]||[0,0];suma[id][0]+=dx;suma[id][1]+=dy}}
  PIEZAS.forEach(p=>{const g=document.getElementById("pz-"+p.id);const s=suma[p.id]||[0,0];
    g.style.transform=`translate(${s[0]}px,${s[1]}px)`;g.classList.toggle("esq-fuera",s[0]!==0||s[1]!==0)});
  svg.classList.toggle("esq-explotado",k>0);
  focoNumeros();
  svg.classList.toggle("esq-sinmanguera",k>=2);
  if(k>0)svg.classList.remove("esq-rayosx"); else if(seleccion&&OCULTAS.includes(seleccion))svg.classList.add("esq-rayosx");
  document.getElementById("textoPaso").innerHTML=k===0?TXT_ARMADO:PASOS[k-1].t;
  document.getElementById("bAtras").disabled=k===0;
  document.getElementById("bAdel").disabled=k===PASOS.length;
  document.getElementById("bTodo").textContent=k===PASOS.length?"Armar":(temporizador?"Pausa":"Desarmar");
  escalarEtiquetas();
}
// «Desarmar»: 1,3 s por paso para alcanzar a leer cada texto (armar de vuelta va más rápido, 0,5 s).
// Durante la reproducción #textoPaso deja de anunciarse y al final se anuncia solo el último paso.
// Con reducción de movimiento salta directo al despiece completo (o al armado).
const REDUCIDO=matchMedia("(prefers-reduced-motion:reduce)").matches;
const textoPaso=document.getElementById("textoPaso");
function parar(){
  clearInterval(temporizador);temporizador=null;
  textoPaso.setAttribute("aria-live","polite");
  textoPaso.innerHTML=textoPaso.innerHTML;          // fuerza un solo anuncio con el paso donde quedó
}
document.getElementById("bTodo").addEventListener("click",()=>{
  if(temporizador){parar();aplicar(paso);return}
  const armar=paso===PASOS.length;
  if(REDUCIDO){aplicar(armar?0:PASOS.length);return}
  textoPaso.setAttribute("aria-live","off");
  temporizador=setInterval(()=>{
    const sig=armar?paso-1:paso+1;
    if(sig<0||sig>PASOS.length){parar();aplicar(paso);return}
    aplicar(sig);
    if(sig===0||sig===PASOS.length){parar();aplicar(sig)}
  },armar?500:1300);
  aplicar(armar?paso-1:paso+1);
});
document.getElementById("bAtras").addEventListener("click",()=>{parar();if(paso>0)aplicar(paso-1)});
document.getElementById("bAdel").addEventListener("click",()=>{parar();if(paso<PASOS.length)aplicar(paso+1)});
/* interruptores: números resaltados y transparencia de las carcasas */
// Una sola parada de tabulador por número: las piezas dobles (9, 5, 10) dejan el segundo número fuera del tabulador.
function focoNumeros(){const abiertos=svg.classList.contains("esq-explotado")||svg.classList.contains("esq-transparente");
  const vistos=new Set();
  document.querySelectorAll(".esq-et").forEach(e=>{const b=e.querySelector(".esq-bola"), n=e.closest(".esq-pz").dataset.n;
    const oculto=e.classList.contains("esq-et-exp")&&!abiertos, repetido=vistos.has(n);
    if(!oculto)vistos.add(n);
    b.setAttribute("tabindex",oculto||repetido?"-1":"0");
    if(repetido)b.setAttribute("aria-hidden","true");else b.removeAttribute("aria-hidden")})}
function interruptor(id,clase){const b=document.getElementById(id);b.addEventListener("click",()=>{const on=b.getAttribute("aria-pressed")!=="true";b.setAttribute("aria-pressed",on);svg.classList.toggle(clase,on);if(clase==="esq-transparente")svg.classList.remove("esq-rayosx");focoNumeros()})}
interruptor("iNum","esq-numeros");
/* Versión del dibujo: Normal o Transparente. Vale en armado y en despiece, se mantiene al cambiar de pestaña y se recuerda en este navegador. */
const vNormal=document.getElementById("vNormal"), vTrans=document.getElementById("vTrans");
function ponerVista(trans,guardar){
  vNormal.setAttribute("aria-pressed",!trans);vTrans.setAttribute("aria-pressed",trans);
  svg.classList.toggle("esq-transparente",trans);if(trans)svg.classList.remove("esq-rayosx");focoNumeros();escalarEtiquetas();
  if(guardar){try{localStorage.setItem("esqVista",trans?"t":"n")}catch(e){}}
}
vNormal.addEventListener("click",()=>ponerVista(false,true));
vTrans.addEventListener("click",()=>ponerVista(true,true));
try{if(localStorage.getItem("esqVista")==="t")ponerVista(true,false)}catch(e){}
aplicar(0);

/* ============================================================
   Cómo funciona (7 pasos)
   ============================================================ */
let fnPaso=0, fnTimer=null;
const $=id=>document.getElementById(id);
function fnAplicar(i){
  fnPaso=i;const s=FN[i].s;
  A.funciona.aplicar(s,$);
  $("fnTexto").innerHTML=FN[i].t;
  $("fnAtras").disabled=i===0;$("fnAdel").disabled=i===FN.length-1;
}
// v11: el texto de «Cómo funciona» toma el alto del paso más largo, para que ◀ ▶ no salten al cambiar de paso.
// Se mide de nuevo cuando cambia el ancho (giro del celular, pestaña que se abre).
let fnAncho=-1;
function fnAltoFijo(){const el=$("fnTexto");if(!el||!el.offsetWidth||el.offsetWidth===fnAncho)return;
  fnAncho=el.offsetWidth;const antes=el.innerHTML;el.style.minHeight="0";let m=0;
  FN.forEach(p=>{el.innerHTML=p.t;m=Math.max(m,el.offsetHeight)});el.innerHTML=antes;el.style.minHeight=m+"px"}
if(window.ResizeObserver&&$("fnTexto"))new ResizeObserver(fnAltoFijo).observe($("fnTexto"));
function fnParar(){clearInterval(fnTimer);fnTimer=null;$("fnPlay").textContent="▶ Reproducir"}
$("fnPlay").addEventListener("click",()=>{
  if(fnTimer){fnParar();return}
  fnAplicar(0);$("fnPlay").textContent="Pausa";
  fnTimer=setInterval(()=>{if(fnPaso>=FN.length-1){fnParar();return}fnAplicar(fnPaso+1)},3600);
});
$("fnAtras").addEventListener("click",()=>{fnParar();if(fnPaso>0)fnAplicar(fnPaso-1)});
$("fnAdel").addEventListener("click",()=>{fnParar();if(fnPaso<FN.length-1)fnAplicar(fnPaso+1)});
const mqFn=matchMedia("(max-width:700px)");
function fnEncuadre(){const m=mqFn.matches;$("fn").setAttribute("viewBox",m?D.funciona.vbCelular:D.funciona.vbEscritorio);
  document.querySelectorAll("#fn [data-ym]").forEach(t=>{if(!t.dataset.yd){t.dataset.yd=t.getAttribute("y");t.dataset.xd=t.getAttribute("x")}
    t.setAttribute("y",m?t.dataset.ym:t.dataset.yd);t.setAttribute("x",m&&t.dataset.xm?t.dataset.xm:t.dataset.xd)})}
mqFn.addEventListener("change",fnEncuadre);fnEncuadre();
fnAplicar(0);

/* ============================================================
   Cadenas de falla
   ============================================================ */
$("listaCadenas").innerHTML=CADENAS.map(c=>`<div class="esq-tarjeta esq-cadena"><h3>${c.t}</h3><ol>${c.p.map(([k,t])=>`<li>${boton(k)} ${t}</li>`).join("")}</ol></div>`).join("");
// para las pruebas en el navegador (medir toques sin esperar animaciones)
window.__esq={aplicar,ponerVista,escalarEtiquetas,VB_ARM,get VB_EXP(){return VB_EXP},fijarVB(vb){cancelAnimationFrame(vbAnim);vbActual=vb.slice();svg.setAttribute("viewBox",vb.join(" "));escalarEtiquetas()}};
}};
})();
