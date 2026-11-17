/* esquema.js: motor de las láminas del esquema pedagógico de TallerYa (despiece, ficha, «Cómo funciona», «Si falla», «Cuándo»).
   Modelo v2 por defecto (JSON con «v2»): grupos con nombre, lados opcionales, tornillería agrupada, lista con buscador, ficha nueva y hoja inferior en el celular.
   Un JSON sin «v2» se ve con el modelo viejo (números, chips y ficha v1): esa es la opción para el viejo.
   Uso: Esquema.iniciar(datos, arte). datos = JSON de la lámina (datos/*.json); arte = ESQ_ARTE[datos.arte] (datos/*-arte.js).
   La página necesita <div id="esquema"></div>; el motor lo reemplaza por la lámina completa. Clases: todas con esq-. */
(function(){
"use strict";
// [[n|texto]] → enlace sutil a la pieza n (ficha, «Cómo funciona», pasos, cadenas, «Cuándo» y textos de la página)
const ENL=s=>String(s==null?"":s).replace(/\[\[([^|\]]+)\|([^\]]+)\]\]/g,(m,k,t)=>`<button type="button" class="esq-enl" data-k="${k}">${t}</button>`);
// zoom del dibujo: + − y «ajustar» (vuelve al encuadre donde se ve todo); en v2 va en la fila de controles, junto a «Números»
const ZOOM_HTML=`<div class="esq-zoom" role="group" aria-label="Zoom del dibujo">
            <button type="button" class="esq-zoom-b" id="zMas" aria-label="Acercar el dibujo" title="Acercar">+</button>
            <button type="button" class="esq-zoom-b" id="zMenos" aria-label="Alejar el dibujo" title="Alejar" disabled>−</button>
            <button type="button" class="esq-zoom-b" id="zVer" aria-label="Ajustar: ver el dibujo completo" title="Ajustar: ver todo" disabled>⤢</button>
          </div>`;
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
        ${D.v2?`<div class="esq-v2-barra">
          <button type="button" class="esq-btn esq-v2-volver" id="v2Volver" hidden>‹ Vista general</button>
          <p class="esq-v2-tit" id="v2Titulo">Toca un grupo del dibujo</p>
          ${Object.keys(D.v2.lados||{}).length>1?`<div class="esq-visor-modo esq-v2-lado" role="group" aria-label="${D.v2.ladoAria||"Lado"}">
            ${Object.entries(D.v2.lados).map(([l,t])=>`<button type="button" data-lado="${l}" aria-pressed="${l===(D.v2.lado||Object.keys(D.v2.lados)[0])}">${t}</button>`).join("")}
          </div>`:""}
        </div>`:""}
        <div class="esq-vista-fila"${D.v2?" hidden":""}>
          <span class="esq-vista-et" id="vistaEt">Dibujo</span>
          <div class="esq-visor-modo esq-vista-sel" role="group" aria-labelledby="vistaEt">
            <button type="button" id="vNormal" aria-pressed="true">Normal</button>
            <button type="button" id="vTrans" aria-pressed="false">Transparente</button>
          </div>
          <p class="esq-pista" id="pista" aria-hidden="true">👆 Toca una pieza</p>
          ${D.v2?"":ZOOM_HTML}
        </div>
        <div class="esq-herr">
          <button type="button" class="esq-btn esq-btn-lava" id="bTodo">Desarmar</button>
          <button type="button" class="esq-boton-paso" id="bAtras" aria-label="Paso anterior">◀</button>
          <button type="button" class="esq-boton-paso" id="bAdel" aria-label="Paso siguiente">▶</button>
          <button type="button" class="esq-interruptor" id="iNum" aria-pressed="false">Números</button>
          ${D.v2&&(D.carcasas||[]).length?`<button type="button" class="esq-interruptor esq-i-trans" id="iTrans" aria-pressed="false" aria-label="Transparente: ver por dentro" title="Transparente: carcasas y tapas translúcidas para ver lo de adentro"><svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><rect x="2.5" y="4.5" width="15" height="11" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-dasharray="3 2"/><circle cx="10" cy="10" r="3" fill="currentColor"/></svg><span class="esq-i-txt">Transparente</span></button>`:""}
          ${D.v2?ZOOM_HTML:""}
        </div>
        <p class="esq-paso" id="textoPaso" aria-live="polite">${ENL(D.textoArmado)}</p>
        <div class="esq-fichas-chips" id="chips" role="group" aria-label="Piezas de la lámina"${D.v2?" hidden":""}></div>
        ${D.v2?'<div class="esq-v2-lista" id="v2Lista"></div>':""}
      </div>

      <!-- Cómo funciona -->
      <div class="esq-panel esq-func" id="p-funciona" role="tabpanel" aria-labelledby="t-funciona" hidden>
      <p class="esq-intro">${ENL(D.textos.introFunciona)}</p>
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
        <p class="esq-intro">${ENL(D.textos.introCadenas)}</p>
        <div class="esq-cadenas" id="listaCadenas"></div>
      </div>

      <!-- Cuándo revisar y cambiar -->
      <div class="esq-panel" id="p-plan" role="tabpanel" aria-labelledby="t-plan" hidden>
        <p class="esq-intro">${ENL(D.textos.introCuando)}</p>
    <div class="esq-tabla">
      <table>
        <thead><tr><th>Qué</th><th>Cuándo</th><th>De dónde sale</th></tr></thead>
        <tbody>${D.cuando.map(r=>`<tr><td>${ENL(r.que)}</td><td>${ENL(r.cuando)}</td><td>${ENL(r.fuente)}</td></tr>`).join("\n")}</tbody>
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
${D.v2?`<div class="esq-hoja2" id="hoja2" role="region" aria-label="Pieza elegida" hidden>
  <div class="esq-h2-cab" id="h2Cab"><span class="esq-h2-asa" aria-hidden="true"></span>
    <div class="esq-h2-txt"><b id="h2T"></b><p id="h2Q"></p></div>
    <button type="button" class="esq-h2-ver" id="h2Ver" aria-expanded="false">Ver ficha</button>
    <button type="button" class="esq-h2-x" id="h2X" aria-label="Cerrar">✕</button>
  </div>
  <div class="esq-h2-cuerpo" id="h2Cuerpo"></div>
</div>`:""}
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
  if(p.comun&&F&&!F.forma3d&&!p.sin3d&&window.ESQ_COMUN&&(!D.v2||(D.v2.con3d||[]).includes(p.n)))F.forma3d=ESQ_COMUN.forma3d(p.comun,p.p)});
Object.values(D.fichas).forEach(F=>{if(F.forma3d)F.forma3d.partes.forEach(q=>{if(q.perfil)q.perfil=perfilDe(q.perfil)})});
// "oculto":true en una pieza común (resorte, o-ring…) la esconde armada, como esq-oculto-arm en el arte propio
const PIEZAS=D.piezas.map(p=>Object.assign({},p,{arte:()=>p.comun?(p.oculto?`<g class="esq-oculto-arm">${COMUN.arte(p)}</g>`:COMUN.arte(p)):(p.tr?`<g transform="${p.tr}">${A[p.arte](...(p.args||[]))}</g>`:A[p.arte](...(p.args||[])))}));
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
const V2H={}, V2T={};
const nombreDe=k=>V2T[k]?V2T[k].nombre+" ("+V2T[k].cant+")":FICHAS[k]?FICHAS[k].nombre:k;
const etiq=k=>FICHAS[k]&&FICHAS[k].ctx?"·":k;

/* ---------- chips ---------- */
document.getElementById("chips").innerHTML=ORDEN_CHIPS.map(k=>{const c=FICHAS[k].ctx;
  return `<button class="esq-chip${c?' esq-ctx':''}" data-k="${k}" title="${FICHAS[k].nombre}" aria-label="${c?'':k+': '}${FICHAS[k].nombre}"><span class="esq-n">${c?'·':k}</span>${FICHAS[k].nombre}</button>`}).join("");

/* ---------- selección ---------- */
const svg=document.getElementById("lamina");
let seleccion=null;
function seleccionar(k,{desplazar=false}={}){
  if(V2H.sel)return V2H.sel(k,desplazar);
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
  const env=document.querySelector(".esq-envoltura");if(env)env.dataset.tab=tab.id.slice(2);
  if(V2H.alPestana)V2H.alPestana(tab.id);
}
PESTANAS.forEach((t,i)=>{
  t.addEventListener("click",()=>activarPestana(t));
  t.addEventListener("keydown",e=>{const n={ArrowRight:i+1,ArrowLeft:i-1,Home:0,End:PESTANAS.length-1}[e.key];
    if(n===undefined)return;e.preventDefault();activarPestana(PESTANAS[(n+PESTANAS.length)%PESTANAS.length],true)});
});

/* ---------- celular: barra fija con la pieza elegida y «Ver ficha» (sin bajar la página sola) ---------- */
const hoja=document.getElementById("hoja"), fichaEl=document.getElementById("ficha");
let fichaVisible=false;
if("IntersectionObserver" in window){new IntersectionObserver(es=>{fichaVisible=es[0].isIntersecting;if(V2H.hojaVis)return V2H.hojaVis();if(fichaVisible)hoja.hidden=true;else if(seleccion&&innerWidth<960)hoja.hidden=false},{threshold:.15}).observe(fichaEl)}
function mostrarHoja(k){
  if(V2H.hoja)return V2H.hoja(k);
  if(innerWidth>=960||fichaVisible){hoja.hidden=true;return}
  if(!FICHAS[k]&&!V2T[k])return;
  document.getElementById("hojaN").textContent=FICHAS[k]&&FICHAS[k].ctx?"·":k;
  document.getElementById("hojaT").textContent=nombreDe(k);
  hoja.hidden=false;
}
document.getElementById("hojaVer").addEventListener("click",()=>{
  fichaEl.scrollIntoView({behavior:REDUCIDO_SEL()?"auto":"smooth",block:"start"});
  const h=fichaEl.querySelector("h3");if(h)h.focus({preventScroll:true});hoja.hidden=true;
});
function boton(k){return `<button data-k="${k}">${!D.v2&&FICHAS[k]&&!FICHAS[k].ctx?k+" · ":""}${nombreDe(k)}</button>`}
function pintarFicha(k){
  if(V2H.ficha)return V2H.ficha(k);
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
  if(b){if(V2H.catalogo&&V2H.catalogo(b))return;seleccionar(b.dataset.k,{desplazar:!!b.closest("#p-cadenas,#p-funciona,#p-plan")});return}
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
    b.setAttribute("transform",s===1?"":`translate(${x} ${y}) scale(${Math.ceil(s*1000)/1000}) translate(${-x} ${-y})`)});
  radiosToque(s);
  if(V2H.marcas)V2H.marcas();
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
  if(!dur){paso_(t0);return}   // sin animación (movimiento reducido): al instante, sin esperar un cuadro
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
// la fila de controles puede ocupar dos renglones mientras carga la letra (Archivo/Oswald): se vuelve a medir cuando llega y si la fila cambia de tamaño
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(()=>{medirAlto();escalarEtiquetas()});
if(window.ResizeObserver){const herr=document.querySelector("#p-piezas .esq-herr");let hT=0,hA=0;if(herr)new ResizeObserver(es=>{const a=Math.round(es[0].contentRect.height);if(a===hA)return;hA=a;cancelAnimationFrame(hT);hT=requestAnimationFrame(medirAlto)}).observe(herr)}
addEventListener("resize",()=>{if(zoom>1&&innerWidth>700)fijarZoom(1,null,null,true);escalarEtiquetas()});
// el lienzo puede cambiar de tamaño sin «resize» (letra que carga, alto de la columna): se reescalan números y marcas para que el toque siga en 44-46 px
if(window.ResizeObserver){let rzT=0;new ResizeObserver(()=>{cancelAnimationFrame(rzT);rzT=requestAnimationFrame(escalarEtiquetas)}).observe(svg)}

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
  const B=V2H.vb?V2H.vb():(paso===0?VB_ARM:VB_EXP);zoom=Math.min(ZMAX,Math.max(1,z));
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
// v12: también con el mouse (botón principal): con zoom, arrastrar recorre el dibujo, como en el despiece del garaje
svg.addEventListener("pointerdown",e=>{if(!dedos.size)anularClic=false;if(e.pointerType==="mouse"&&e.button!==0)return;dedos.set(e.pointerId,[e.clientX,e.clientY]);iniciarGesto()});
// rueda: acerca o aleja sobre el punto del cursor. Sin zoom, solo con Ctrl (o el pellizco del touchpad) para no atrapar el scroll de la página
svg.addEventListener("wheel",e=>{
  const fac=e.deltaY<0?1.18:1/1.18;
  if(zoom<=1.01&&(fac<1||!e.ctrlKey&&!e.metaKey))return;
  const r=svg.getBoundingClientRect();if(!r.width)return;
  e.preventDefault();
  const B=V2H.vb?V2H.vb():(paso===0?VB_ARM:VB_EXP), a=aDibujo(e.clientX,e.clientY);
  const z=Math.min(ZMAX,Math.max(1,zoom*fac)), w=B[2]/z, h=B[3]/z;
  fijarZoom(z,a[0]-(e.clientX-r.left)*w/r.width+w/2,a[1]-(e.clientY-r.top)*h/r.height+h/2,false);
},{passive:false});
svg.addEventListener("pointermove",e=>{
  if(!dedos.has(e.pointerId))return;
  if(e.pointerType==="mouse"&&!(e.buttons&1)){soltar(e);return}   // se soltó fuera del dibujo antes de arrastrar
  dedos.set(e.pointerId,[e.clientX,e.clientY]);if(!gesto)return;
  const p=[...dedos.values()], r=svg.getBoundingClientRect(), B=V2H.vb?V2H.vb():(paso===0?VB_ARM:VB_EXP);
  if(gesto.tipo===2&&p.length>=2){
    const z=Math.min(ZMAX,Math.max(1,gesto.z0*Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1])/gesto.d0)), w=B[2]/z, h=B[3]/z;
    const m=[(p[0][0]+p[1][0])/2,(p[0][1]+p[1][1])/2];
    // el punto del dibujo que estaba bajo los dedos sigue bajo los dedos
    const x0=gesto.ancla[0]-(m[0]-r.left)*w/r.width, y0=gesto.ancla[1]-(m[1]-r.top)*h/r.height;
    fijarZoom(z,x0+w/2,y0+h/2,false);anularClic=true;
  }else if(gesto.tipo===1){
    const dx=p[0][0]-gesto.ini[0], dy=p[0][1]-gesto.ini[1];
    if(!anularClic&&Math.hypot(dx,dy)<8)return;
    if(!anularClic){try{svg.setPointerCapture(e.pointerId)}catch(_){}svg.classList.add("esq-arrastrando")}
    anularClic=true;const v=gesto.vb0;fijarZoom(zoom,v[0]+v[2]/2-dx*v[2]/r.width,v[1]+v[3]/2-dy*v[3]/r.height,false);
  }
});
const soltar=e=>{if(dedos.delete(e.pointerId))iniciarGesto();if(!dedos.size)svg.classList.remove("esq-arrastrando")};
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
  document.getElementById("textoPaso").innerHTML=ENL(k===0?TXT_ARMADO:PASOS[k-1].t);
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
  vNormal.setAttribute("aria-pressed",!trans);vTrans.setAttribute("aria-pressed",trans);const it=document.getElementById("iTrans");if(it)it.setAttribute("aria-pressed",trans);
  svg.classList.toggle("esq-transparente",trans);if(trans)svg.classList.remove("esq-rayosx");focoNumeros();escalarEtiquetas();
  if(guardar){try{localStorage.setItem("esqVista",trans?"t":"n")}catch(e){}}
}
vNormal.addEventListener("click",()=>ponerVista(false,true));
vTrans.addEventListener("click",()=>ponerVista(true,true));
// v2: el interruptor chico «Transparente» (junto a «Números») hace lo mismo en la vista general y dentro de los grupos
if(document.getElementById("iTrans"))document.getElementById("iTrans").addEventListener("click",()=>{ponerVista(!svg.classList.contains("esq-transparente"),true);if(V2H.marcas)V2H.marcas()});
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
  $("fnTexto").innerHTML=ENL(FN[i].t);
  $("fnAtras").disabled=i===0;$("fnAdel").disabled=i===FN.length-1;
}
// v11: el texto de «Cómo funciona» toma el alto del paso más largo, para que ◀ ▶ no salten al cambiar de paso.
// Se mide de nuevo cuando cambia el ancho (giro del celular, pestaña que se abre).
let fnAncho=-1;
function fnAltoFijo(){const el=$("fnTexto");if(!el||!el.offsetWidth||el.offsetWidth===fnAncho)return;
  fnAncho=el.offsetWidth;const antes=el.innerHTML;el.style.minHeight="0";let m=0;
  FN.forEach(p=>{el.innerHTML=ENL(p.t);m=Math.max(m,el.offsetHeight)});el.innerHTML=antes;el.style.minHeight=m+"px"}
if(window.ResizeObserver&&$("fnTexto"))new ResizeObserver(()=>requestAnimationFrame(fnAltoFijo)).observe($("fnTexto"));
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
$("listaCadenas").innerHTML=CADENAS.map(c=>`<div class="esq-tarjeta esq-cadena"><h3>${ENL(c.t)}</h3><ol>${c.p.map(([k,t])=>`<li>${boton(k)} ${ENL(t)}</li>`).join("")}</ol></div>`).join("");
/* ============================================================
   v2: subconjuntos con nombre, lado Delantera | Trasera, tornillería por punto, lista plegable y ficha nueva
   ============================================================ */
if(D.v2){
const V2=D.v2, GR=V2.grupos, G_ID={};
const ICONO={desgaste:"⚙️",calor:"🔥",humedad:"💧",maluso:"✋",golpe:"💥",edad:"⏳"};
// los lados (conjuntos repetidos, p. ej. freno delantero | trasero) son opcionales: sin «lados», todo es del lado «unico» y no hay selector
const LADOS=V2.lados||{unico:""}, LADO_TXT=V2.ladoTxt||{}, VARIOS=Object.keys(LADOS).length>1;
GR.forEach(g=>{g.lado=g.lado||"unico"});
const gTxt=(g,sep=", ")=>g.nombre+(LADO_TXT[g.lado]?sep+LADO_TXT[g.lado]:"");
let lado=V2.lado||Object.keys(LADOS)[0], grupo=null, gPaso=0, VB_G=null, tempG=null;
svg.classList.add("esq-v2","esq-l-"+lado);
const grupoDeId={}, tornDeId={};
GR.forEach(g=>{G_ID[g.id]=g;g.piezas.forEach(i=>grupoDeId[i]=g);g.ks=[...new Set(g.piezas.map(i=>(PIEZAS.find(p=>p.id===i)||{n:i}).n))];   // piezas = ids del dibujo; ks = fichas (9a y 9b son la ficha 9)

  g.torn.forEach((t,j)=>{t.k="t:"+g.id+":"+j;t.g=g;V2T[t.k]=t;t.ids.forEach(i=>{grupoDeId[i]=g;tornDeId[i]=t})})});
const idsDe=g=>g.piezas.concat(...g.torn.map(t=>t.ids));
const pzEl=id=>document.getElementById("pz-"+id);
document.querySelectorAll("#capas .esq-pz").forEach(el=>{const g=grupoDeId[el.id.slice(3)];if(g){el.classList.add("esq-lado-"+g.lado);el.dataset.g=g.id}});
function grupoDe(k){if(V2T[k])return V2T[k].g;const p=PIEZAS.find(p=>p.n===k);return p?grupoDeId[p.id]:null}
// pieza equivalente del otro lado (misma posición en el grupo hermano)
function contraparte(k){const g=grupoDe(k);if(!g)return k;const h=GR.find(x=>x.lado!==g.lado&&x.nombre===g.nombre);if(!h)return null;
  if(V2T[k]){const j=g.torn.indexOf(V2T[k]);return h.torn[j]?h.torn[j].k:null}
  const i=g.ks.indexOf(k);return i>=0&&h.ks[i]?h.ks[i]:null}
const orden=()=>GR.filter(g=>g.lado===lado).flatMap(g=>g.ks.concat(g.torn.map(t=>t.k)));

/* ---------- marcas: grupos (vista general) y tornillería (dentro del grupo) ---------- */
function pildora(txt,largo,x,y,attrs,clase){const w=txt.length*6.3+14, wl=largo.length*6.3+16, tw=Math.max(44,w+8);
  const cara=(t,a,h,c)=>`<g class="${c}"><rect class="esq-pildora" x="${f(x-a/2)}" y="${f(y-h/2)}" width="${f(a)}" height="${h}" rx="${h/2}"/><text x="${f(x)}" y="${f(y+4)}">${t}</text></g>`;
  return `<g class="esq-marca ${clase}" data-x="${f(x)}" data-y="${f(y)}" data-w="${f(w+6)}" tabindex="0" role="button" ${attrs}><rect class="esq-toque" x="${f(x-tw/2)}" y="${f(y-23)}" width="${f(tw)}" height="46"/>${cara(txt,w,20,"esq-m-min")}${largo!==txt?cara(largo,wl,22,"esq-m-full"):""}</g>`}
let mg="";
GR.forEach(g=>{let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;
  g.piezas.forEach(i=>{const el=pzEl(i);if(!el)return;const b=el.querySelector(".esq-arte").getBBox();
    x0=Math.min(x0,b.x);y0=Math.min(y0,b.y);x1=Math.max(x1,b.x+b.width);y1=Math.max(y1,b.y+b.height)});
  const [x,y]=g.marca||[(x0+x1)/2,(y0+y1)/2];
  mg+=pildora(g.corto||g.nombre,g.nombre,x,y,`data-g="${g.id}" aria-label="Acercar: ${gTxt(g)}"`,"esq-marca-g esq-lado-"+g.lado);
  g.torn.forEach(t=>{const p=PIEZAS.find(p=>p.id===t.ids[0]), el=pzEl(p.id), [ax,ay]=t.marca||[p.anc[0]+p.et[0],p.anc[1]+p.et[1]];
    el.insertAdjacentHTML("beforeend",pildora(`${t.corto||"Tornillería"} (${t.cant})`,`${t.nombre} (${t.cant})`,ax,ay,`data-k="${t.k}" aria-label="${t.nombre}, ${t.cant} piezas"`,"esq-marca-t"))})});
capas.insertAdjacentHTML("beforeend",`<g id="guiasG" aria-hidden="true"></g><g id="marcasG">${mg}</g>`);
const guiasG=$("guiasG");
// tornillería: el punto que señala su guía es el ancla de la primera pieza
GR.forEach(g=>g.torn.forEach(t=>{const p=PIEZAS.find(p=>p.id===t.ids[0]),m=pzEl(p.id).querySelector(`.esq-marca-t[data-k="${t.k}"]`);if(m){m.dataset.ax=p.anc[0];m.dataset.ay=p.anc[1]}}));

const offPz=el=>{const g=el.closest(".esq-pz"),m=g&&/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(g.style.transform||"");return m?[+m[1],+m[2]]:[0,0]};
V2H.marcas=()=>{const rr=svg.getBoundingClientRect();if(!rr.width)return;const sm=Math.max(vbActual[2]/rr.width,vbActual[3]/rr.height), [v0,v1,vw,vh]=vbActual, numeros=svg.classList.contains("esq-numeros");
  // tornillería que ya salió en el desarme: su píldora se esconde (la pieza ya se ve y se toca sola) y no tapa a las vecinas
  svg.querySelectorAll(".esq-marca-t").forEach(m=>{m.style.display=grupo&&m.closest(".esq-pz").classList.contains("esq-fuera")?"none":""});
  svg.classList.toggle("esq-marcas-min",numeros&&!grupo);
  const vis=[...svg.querySelectorAll(grupo?".esq-pz.esq-engr .esq-marca-t":".esq-marca-g.esq-lado-"+lado)].filter(m=>!(grupo&&numeros)&&!(!grupo&&gPaso>0)&&m.style.display!=="none");
  const red=grupo?.85:numeros?.8:1;   // tornillería y modo «Números»: píldoras más chicas
  const cajas=vis.map(m=>{const o=m.classList.contains("esq-marca-t")?offPz(m):[0,0],x=+m.dataset.x,y=+m.dataset.y,hw=+m.dataset.w/2*sm*red,hh=13*sm*red;
    let cx=x+o[0],cy=y+o[1];cx=Math.min(Math.max(cx,v0+hw+4*sm),v0+vw-hw-4*sm);cy=Math.min(Math.max(cy,v1+23*sm),v1+vh-23*sm);   /* el área de toque (46 px) entera dentro del lienzo, no solo la píldora */return {m,o,x,y,hw,hh,cx,cy}});
  cajas.sort((a,b)=>a.cy-b.cy);
  for(let it=0;it<10;it++)for(let i=0;i<cajas.length;i++)for(let j=i+1;j<cajas.length;j++){const a=cajas[i],b=cajas[j];
    const sx=a.hw+b.hw-Math.abs(a.cx-b.cx), sy=a.hh+b.hh-Math.abs(a.cy-b.cy);if(sx<=0||sy<=0)continue;
    const m=2*sm, der=b.cx>=a.cx, hx=der?b.cx+sx+m:b.cx-sx-m;   // primero al lado (hay sitio en la mitad atenuada), si no abajo o arriba
    if(hx-b.hw>=v0&&hx+b.hw<=v0+vw)b.cx=hx;else if(b.cy+sy+m<=v1+vh-b.hh)b.cy+=sy+m;else if(a.cy-sy-m>=v1+a.hh)a.cy-=sy+m;else{const d=der?1:-1;b.cx+=d*sx/2;a.cx-=d*sx/2}}
  // reubicar: la tornillería (vista de grupo) va a la zona libre más cercana a su punto; en «Números», ninguna píldora encima de un número
  const ocupa=(c,x,y,B)=>{let A=0;B.forEach(b=>{const ox=Math.min(x+c.hw,b[2])-Math.max(x-c.hw,b[0]),oy=Math.min(y+c.hh,b[3])-Math.max(y-c.hh,b[1]);if(ox>0&&oy>0)A+=ox*oy});return A};
  const enVB=(c,x,y)=>[Math.min(Math.max(x,v0+c.hw+4*sm),v0+vw-c.hw-4*sm),Math.min(Math.max(y,v1+23*sm),v1+vh-23*sm)];
  const reubicar=(obst,peso,pend)=>{const hechas=[];cajas.forEach(c=>{
      const otras=hechas.map(h=>[h.cx-h.hw-2*sm,h.cy-h.hh-2*sm,h.cx+h.hw+2*sm,h.cy+h.hh+2*sm]),ax=c.ax==null?c.cx:c.ax,ay=c.ay==null?c.cy:c.ay;
      const nota=(x,y)=>ocupa(c,x,y,obst)*peso+ocupa(c,x,y,otras)*4+Math.hypot(x-c.cx,y-c.cy)*pend*c.hh;
      let mejor=[c.cx,c.cy],mn=nota(c.cx,c.cy);
      if(mn>0)for(const r of [1,2,3,4,5,6,8,10,13,17])for(let a=0;a<16;a++){const [x,y]=enVB(c,ax+Math.cos(a*Math.PI/8)*r*20*sm,ay+Math.sin(a*Math.PI/8)*r*20*sm),v=nota(x,y);if(v<mn-.01){mn=v;mejor=[x,y]}}
      [c.cx,c.cy]=mejor;hechas.push(c)})};
  const M=capas.getScreenCTM().inverse(),aVB=(x,y)=>{const p=new DOMPoint(x,y).matrixTransform(M);return [p.x,p.y]};
  const visible=e=>{const r=e.getBoundingClientRect();if(!r.width)return false;for(let x=e;x&&x!==svg;x=x.parentElement){const c=getComputedStyle(x);if(c.display==="none"||c.visibility==="hidden"||+c.opacity<.15)return false}return true};
  if(grupo&&cajas.length){const s=sumaG(grupo,gPaso),B=[];
    T_INFO.forEach(t=>{if(!t.el.classList.contains("esq-engr"))return;const d=s[t.id]||[0,0];(t.racimos||t.zonas.slice(0,1)).forEach(z=>B.push([z.cx-z.w/2+d[0],z.cy-z.h/2+d[1],z.cx+z.w/2+d[0],z.cy+z.h/2+d[1]]))});
    cajas.forEach(c=>{c.ax=+c.m.dataset.ax+c.o[0];c.ay=+c.m.dataset.ay+c.o[1]});reubicar(B,1,.5)}
  else if(numeros&&cajas.length){const N=[...svg.querySelectorAll(".esq-et .esq-disco")].filter(visible).map(e=>{const r=e.getBoundingClientRect(),a=aVB(r.left,r.top),b=aVB(r.right,r.bottom);return [a[0]-3*sm,a[1]-3*sm,b[0]+3*sm,b[1]+3*sm]});
    reubicar(N,50,.3)}
  cajas.forEach(c=>c.m.setAttribute("transform",`translate(${f(c.cx-c.o[0]-c.x)} ${f(c.cy-c.o[1]-c.y)}) translate(${c.x} ${c.y}) scale(${Math.ceil(sm*1000)/1000}) translate(${-c.x} ${-c.y})`));
  // líneas guía: de la tornillería a su punto; de la píldora de grupo a su capa cuando la píldora no queda encima de ella (puesta a mano o apartada)
  guiasG.innerHTML="";clearTimeout(V2H.tGuias);
  const linea=(c,ax,ay)=>{const dx=ax-c.cx,dy=ay-c.cy,L=Math.hypot(dx,dy);if(L<6*sm)return "";const t=Math.min(1,Math.min(c.hw/Math.abs(dx||1e-9),c.hh/Math.abs(dy||1e-9)));if(L*(1-t)<8*sm)return "";
    return `<line class="esq-guia" x1="${f(c.cx+dx*t)}" y1="${f(c.cy+dy*t)}" x2="${f(ax)}" y2="${f(ay)}"/><circle class="esq-guia-p" cx="${f(ax)}" cy="${f(ay)}" r="${f(2.2*sm)}"/>`};
  if(grupo)guiasG.innerHTML=cajas.map(c=>Math.hypot(c.ax-c.cx,c.ay-c.cy)>16*sm?linea(c,c.ax,c.ay):"").join("");
  else if(gPaso===0&&cajas.length)V2H.tGuias=setTimeout(()=>{   // se mide cuando el encuadre deja de moverse
    const M2=capas.getScreenCTM();if(!M2||!svg.getBoundingClientRect().width)return;const aPant=(x,y)=>{const p=new DOMPoint(x,y).matrixTransform(M2);return [p.x,p.y]};
    const capaEn=(x,y)=>{const [sx,sy]=aPant(x,y);for(const e of document.elementsFromPoint(sx,sy)){if(e.closest(".esq-marca")||e.closest("#guiasG"))continue;const p=e.closest("#capas .esq-pz");if(p&&e.closest(".esq-arte"))return p.dataset.g||"";if(e===svg)return null}return null};
    guiasG.innerHTML=cajas.map(c=>{const g=G_ID[c.m.dataset.g];if(!g||[[0,0],[-.6,0],[.6,0],[0,-.6],[0,.6]].some(([u,v])=>capaEn(c.cx+u*c.hw,c.cy+v*c.hh)===g.id))return "";
      let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;g.piezas.forEach(i=>{const el=pzEl(i);if(!el)return;const b=el.querySelector(".esq-arte").getBBox();x0=Math.min(x0,b.x);y0=Math.min(y0,b.y);x1=Math.max(x1,b.x+b.width);y1=Math.max(y1,b.y+b.height)});
      let mejor=null,dm=1e9;for(let i=0;i<=10;i++)for(let j=0;j<=10;j++){const x=x0+(x1-x0)*i/10,y=y0+(y1-y0)*j/10,d=Math.hypot(x-c.cx,y-c.cy);if(d<dm&&capaEn(x,y)===g.id){dm=d;mejor=[x,y]}}
      return mejor&&dm>14*sm?linea(c,mejor[0],mejor[1]):""}).join("")},160);
  svg.querySelectorAll(".esq-toque-pz:not(.esq-toque-auto)").forEach(c=>{const g=c.closest(".esq-pz");c.setAttribute("r",grupo&&g.classList.contains("esq-engr")?f(Math.max(+c.dataset.r,15*sm)):0)});
  if(V2H.toquesAuto)V2H.toquesAuto(sm)};
// piezas chicas (abrazaderas, arandelas de los soportes): un círculo invisible les da al menos 32 px de toque
(V2.toqueExtra||[]).forEach(id=>{const a=pzEl(id).querySelector(".esq-arte"),b=a.getBBox();
  a.querySelector(".esq-esc").insertAdjacentHTML("beforeend",`<circle class="esq-toque-pz" cx="${f(b.x+b.width/2)}" cy="${f(b.y+b.height/2)}" r="0" data-r="${f(Math.min(b.width,b.height)/2)}"/>`)});
// área de toque mínima automática (vista de grupo): una pieza cuya caja mide menos de 24 px en pantalla recibe un círculo
// invisible de 24-30 px, recortado a la mitad de la distancia a la pieza vecina para no taparla. Se crea solo cuando hace falta.
const T_MAN=new Set(V2.toqueExtra||[]);
// racimos: las partes de la pieza que se tocan entre sí (los 6 rodillos de un variador son 6 racimos), en coordenadas de la pieza
function racimos(esc){const inv=esc.getCTM().inverse(),R=[];
  esc.querySelectorAll("path,rect,circle,ellipse,polygon,line,polyline").forEach(e=>{if(e.closest(".esq-marca"))return;let b;try{b=e.getBBox()}catch(_){return}
    if(b.width*b.height<1&&Math.max(b.width,b.height)<2)return;const m=inv.multiply(e.getCTM());
    const q=[[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].map(([x,y])=>[m.a*x+m.c*y+m.e,m.b*x+m.d*y+m.f]);
    R.push([Math.min(...q.map(v=>v[0])),Math.min(...q.map(v=>v[1])),Math.max(...q.map(v=>v[0])),Math.max(...q.map(v=>v[1]))])});
  let cambio=true;while(cambio&&R.length>1){cambio=false;
    for(let a=0;a<R.length&&!cambio;a++)for(let b=a+1;b<R.length;b++){const A=R[a],B=R[b];
      if(A[0]<=B[2]+1&&B[0]<=A[2]+1&&A[1]<=B[3]+1&&B[1]<=A[3]+1){R[a]=[Math.min(A[0],B[0]),Math.min(A[1],B[1]),Math.max(A[2],B[2]),Math.max(A[3],B[3])];R.splice(b,1);cambio=true;break}}}
  return R.map(r=>({cx:(r[0]+r[2])/2,cy:(r[1]+r[3])/2,w:r[2]-r[0],h:r[3]-r[1],c:null}))}
// área dibujada aproximada, en unidades de la pieza: trazos sin relleno = largo × grosor; con relleno = su caja (sobrestima, a propósito)
function areaDib(esc){const inv=esc.getCTM().inverse();let A=0;
  esc.querySelectorAll("path,rect,circle,ellipse,polygon,line,polyline").forEach(e=>{if(e.closest(".esq-marca")||e.classList.contains("esq-toque-pz"))return;let b;try{b=e.getBBox()}catch(_){return}
    const m=inv.multiply(e.getCTM()),k=Math.sqrt(Math.abs(m.a*m.d-m.b*m.c)),cs=getComputedStyle(e),sin=/none|transparent/.test(cs.fill)||cs.fillOpacity==="0";
    if(sin&&e.getTotalLength){let L=0;try{L=e.getTotalLength()}catch(_){}A+=L*(parseFloat(cs.strokeWidth)||1)*k*k}else A+=b.width*b.height*k*k});return A}
const T_INFO=PIEZAS.map(p=>{const el=pzEl(p.id),a=el.querySelector(".esq-arte"),b=a.getBBox(),esc=a.querySelector(".esq-esc");
  const t={id:p.id,el,esc,oculta:!!a.querySelector(".esq-esc>.esq-oculto-arm"),man:T_MAN.has(p.id),zonas:[{cx:b.x+b.width/2,cy:b.y+b.height/2,w:b.width,h:b.height,c:null}],todo:b};
  t.area=areaDib(esc);const rc=racimos(esc);if(rc.length>1&&rc.length<=12)t.racimos=rc;return t});
V2H.toquesAuto=sm=>{const s=grupo?sumaG(grupo,gPaso):{}, act=grupo?T_INFO.filter(t=>t.el.classList.contains("esq-engr")):[], chico=z=>Math.sqrt(z.w*z.h)/sm<24;
  // 1.º las piezas enteras chicas (círculo de 13-15 px de radio, recortado solo entre ellas); 2.º los racimos de las piezas hechas de partes
  // sueltas, recortados contra los círculos y el dibujo de las piezas enteras (un racimo nunca achica a otra pieza). Una pieza con un
  // racimo de 24 px o más no recibe círculos.
  const quedan=new Set(),puede=t=>!t.man&&!(t.oculta&&!t.el.classList.contains("esq-fuera"));
  const subir=new Set(act.filter(t=>t.man));
  const pon=(t,z,r)=>{subir.add(t);if(!z.c){t.esc.insertAdjacentHTML("beforeend",`<circle class="esq-toque-pz esq-toque-auto" cx="${f(z.cx)}" cy="${f(z.cy)}"/>`);z.c=t.esc.lastElementChild}z.c.setAttribute("cx",f(z.cx));z.c.setAttribute("cy",f(z.cy));z.c.setAttribute("r",f(r));quedan.add(z)};
  const centros=act.map(t=>{const d=s[t.id]||[0,0],z=t.zonas[0];return {t,z,d,x:z.cx+d[0],y:z.cy+d[1]}});
  // entera chica: su caja mide < 24 px, o es delgada (resorte, alambre, aro): caja < 48 px y lo dibujado equivale a un círculo de < 36 px
  // (areaDib suma trazos encimados, así que sobrestima: 36 px estimados son ≈ 18-24 px reales de toque)
  const delgada=C=>Math.sqrt(C.z.w*C.z.h)/sm<48&&2*Math.sqrt(C.t.area/Math.PI)/sm<36;
  const enteras=centros.filter(C=>chico(C.z)||delgada(C)),circ=[];
  enteras.forEach(C=>{if(!puede(C.t))return;
    // si el centro de la caja cae sobre otra pieza (aro alrededor de un eje), el círculo va al borde de la caja más lejos de las vecinas
    const otros=centros.filter(Q=>Q!==C),lejos=(x,y)=>Math.min(1e9,...otros.map(Q=>Math.hypot(Q.x-x,Q.y-y)));
    let z=C.z,x=C.x,y=C.y;if(!chico(C.z)&&lejos(x,y)<13*sm){const op=[[0,-1],[0,1],[-1,0],[1,0]].map(([u,v])=>[C.z.cx+u*C.z.w/2,C.z.cy+v*C.z.h/2]).sort((a,b)=>lejos(b[0]+C.d[0],b[1]+C.d[1])-lejos(a[0]+C.d[0],a[1]+C.d[1]))[0];
      z=C.t.zonas[1]||(C.t.zonas[1]={w:0,h:0,c:null});z.cx=op[0];z.cy=op[1];x=op[0]+C.d[0];y=op[1]+C.d[1]}
    let r=15*sm;otros.forEach(Q=>r=Math.min(r,Math.hypot(Q.x-x,Q.y-y)/2));
    r=Math.max(r,13*sm);if(chico(C.z)&&r<=Math.min(z.w,z.h)/2)return;
    // con el mínimo de 13 px puede encimarse con un círculo ya puesto: este se pinta después y le quitaría toque,
    // así que se corre lo que se encima, alejándose de él (el anterior conserva sus 26 px)
    let mov=false;circ.forEach(K=>{const dx=x-K.x,dy=y-K.y,dd=Math.hypot(dx,dy)||1,s=K.r+r-dd;if(s>.5){x+=dx/dd*s;y+=dy/dd*s;mov=true}});
    if(mov){z=C.t.zonas[2]||(C.t.zonas[2]={w:z.w,h:z.h,c:null});z.cx=x-C.d[0];z.cy=y-C.d[1]}
    pon(C.t,z,r);circ.push({x,y,r})});
  const conRac=centros.filter(C=>!chico(C.z)&&!delgada(C)&&C.t.racimos&&puede(C.t)&&C.t.racimos.every(chico));
  const rz=[];conRac.forEach(C=>C.t.racimos.forEach(z=>rz.push({C,z,x:z.cx+C.d[0],y:z.cy+C.d[1]})));
  const cajaD=(E,x,y)=>{const b=E.t.todo,x0=b.x+E.d[0],y0=b.y+E.d[1];return Math.hypot(Math.max(x0-x,0,x-x0-b.width),Math.max(y0-y,0,y-y0-b.height))};
  conRac.forEach(C=>{const mios=rz.filter(R=>R.C===C).sort((a,b)=>b.z.w*b.z.h-a.z.w*a.z.h);
    for(const R of mios){let r=15*sm;
      circ.forEach(K=>r=Math.min(r,Math.hypot(K.x-R.x,K.y-R.y)-K.r));
      enteras.forEach(E=>r=Math.min(r,cajaD(E,R.x,R.y)));
      centros.forEach(Q=>{if(Q!==C&&!chico(Q.z))r=Math.min(r,Math.hypot(Q.x-R.x,Q.y-R.y)/2)});
      rz.forEach(Q=>{if(Q.C!==C)r=Math.min(r,Math.hypot(Q.x-R.x,Q.y-R.y)/2)});
      if(r<=Math.min(R.z.w,R.z.h)/2)continue;pon(C.t,R.z,r);if(r>=12*sm)break}});
  T_INFO.forEach(t=>t.zonas.concat(t.racimos||[]).forEach(z=>{if(z.c&&!quedan.has(z)){z.c.remove();z.c=null}}));
  // ronda 7: los círculos de toque que se enciman (los puestos a mano con toqueExtra y los automáticos) se separan entre sí,
  // sin que el centro salga de la caja de su pieza; así dos piezas vecinas se reparten el espacio en vez de taparse.
  const K=[];act.forEach(t=>{const d=s[t.id]||[0,0],b=t.todo;t.esc.querySelectorAll(".esq-toque-pz").forEach(c=>{const r=+c.getAttribute("r");
    if(!c.classList.contains("esq-toque-auto")){if(c.dataset.cx0==null){c.dataset.cx0=c.getAttribute("cx");c.dataset.cy0=c.getAttribute("cy")}c.setAttribute("cx",c.dataset.cx0);c.setAttribute("cy",c.dataset.cy0)}   // a mano: parte siempre de su lugar
    if(r>0)K.push({c,d,r,x:+c.getAttribute("cx")+d[0],y:+c.getAttribute("cy")+d[1],b:[b.x+d[0],b.y+d[1],b.x+b.width+d[0],b.y+b.height+d[1]]})})});
  for(let it=0;it<16;it++){let hubo=false;
    for(let i=0;i<K.length;i++)for(let j=i+1;j<K.length;j++){const A=K[i],B=K[j];if(A.c.closest(".esq-pz")===B.c.closest(".esq-pz"))continue;
      let dx=B.x-A.x,dy=B.y-A.y,dd=Math.hypot(dx,dy);if(dd<1e-3){dx=1;dy=0;dd=1}const sobra=A.r+B.r-dd;if(sobra<=.5)continue;hubo=true;
      [[A,-1],[B,1]].forEach(([Q,sg])=>{Q.x+=sg*dx/dd*sobra/2;Q.y+=sg*dy/dd*sobra/2;Q.x=Math.min(Math.max(Q.x,Q.b[0]),Q.b[2]);Q.y=Math.min(Math.max(Q.y,Q.b[1]),Q.b[3])})}
    if(!hubo)break}
  K.forEach(Q=>{Q.c.setAttribute("cx",f(Q.x-Q.d[0]));Q.c.setAttribute("cy",f(Q.y-Q.d[1]))});
  // ronda 7: dentro del grupo, las piezas chicas (con círculo de toque) se pintan encima de las demás, para que una pieza grande
  // pintada después no les tape el toque; fuera del grupo todo vuelve al orden original (la vista general no cambia).
  if(!V2H.orden){V2H.orden=new Map();T_INFO.forEach(t=>{const pa=t.el.parentNode;if(pa&&!V2H.orden.has(pa))V2H.orden.set(pa,[...pa.children])})}
  const sube=[...subir].sort((u,v)=>v.todo.width*v.todo.height-u.todo.width*u.todo.height).map(t=>t.el);   // la más chica, arriba de todo
  V2H.orden.forEach((orig,pa)=>{const u=orig.map(e=>e.classList&&e.classList.contains("esq-pz")).lastIndexOf(true),mias=sube.filter(e=>orig.includes(e));
    const quiero=orig.slice(0,u+1).filter(e=>!mias.includes(e)).concat(mias,orig.slice(u+1));   // antes de guiasG/marcasG
    const hoy=[...pa.children].filter(e=>orig.includes(e));if(hoy.some((e,i)=>e!==quiero[i]))quiero.forEach(e=>pa.appendChild(e))})};
$("iNum").addEventListener("click",()=>V2H.marcas());

/* ---------- encuadre y desarme del grupo ---------- */
function sumaG(g,k){const s={},ids=new Set(idsDe(g));
  for(let i=0;i<k;i++)for(const [id,[dx,dy]] of Object.entries(PASOS[g.pasos[i]].m))if(ids.has(id)){s[id]=s[id]||[0,0];s[id][0]+=dx;s[id][1]+=dy}return s}
// encuadre según el estado: al entrar, solo lo armado; con cada paso se amplía hasta lo desarmado (k = pasos hechos)
function encuadreGrupo(g,k=g.pasos.length){let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;
  [{},sumaG(g,k)].forEach(s=>idsDe(g).forEach(i=>{const el=pzEl(i);if(!el)return;const b=el.querySelector(".esq-arte").getBBox(),d=s[i]||[0,0];
    x0=Math.min(x0,b.x+d[0]);y0=Math.min(y0,b.y+d[1]);x1=Math.max(x1,b.x+b.width+d[0]);y1=Math.max(y1,b.y+b.height+d[1])}));
  x0-=36;y0-=46;x1+=36;y1+=36;let w=x1-x0,h=y1-y0;const asp=900/700, minW=220;   // grupos chicos (un tapón) se acercan más en el celular
  if(w<minW){x0-=(minW-w)/2;w=minW}
  if(w/h<asp){const nw=h*asp;x0-=(nw-w)/2;w=nw}else{const nh=w/asp;y0-=(nh-h)/2;h=nh}
  return [x0,y0,w,h].map(f)}
let TODO=[], VB_T=null;
const pasosLado=()=>{const u=new Set(GR.filter(g=>g.lado===lado).flatMap(g=>g.pasos));return PASOS.map((_,i)=>i).filter(i=>u.has(i))};
const grupoDePaso=i=>GR.find(g=>g.lado===lado&&g.pasos.includes(i));
// «Desarmar todo» en la vista general: el paso 1 (SEP) separa los grupos como bloques, cada uno en su dirección y lejos de los
// demás; después las piezas de cada grupo se abren dentro de su zona (la caja de sus piezas ya desarmadas), sin tapar a otro grupo.
const SEP="sep";let OFF=null,OFF_LADO=null;
function cajaIds(ids,s){let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;ids.forEach(i=>{const el=pzEl(i);if(!el)return;const b=el.querySelector(".esq-arte").getBBox(),d=s[i]||[0,0];
  x0=Math.min(x0,b.x+d[0]);y0=Math.min(y0,b.y+d[1]);x1=Math.max(x1,b.x+b.width+d[0]);y1=Math.max(y1,b.y+b.height+d[1])});return [x0,y0,x1,y1]}
function calcularOFF(){if(OFF&&OFF_LADO===lado)return OFF;OFF={};OFF_LADO=lado;
  const gs=GR.filter(g=>g.lado===lado), enG=new Set(gs.flatMap(idsDe)), MG=V2.margenGrupos||22;
  // la dirección de cada grupo: desde el centro del sistema hacia su centro, más hacia donde salen sus piezas
  const arm=cajaIds([...enG],{}), cx=(arm[0]+arm[2])/2, cy=(arm[1]+arm[3])/2;
  const B=gs.map((g,n)=>{const s=sumaG(g,g.pasos.length),z=cajaIds(idsDe(g),s),a=cajaIds(g.piezas,{});let dx=0,dy=0,m=0;
    Object.values(s).forEach(d=>{dx+=d[0];dy+=d[1];m++});m=m||1;
    let ux=((a[0]+a[2])/2-cx)/Math.max(1,arm[2]-arm[0])+dx/m/200, uy=((a[1]+a[3])/2-cy)/Math.max(1,arm[3]-arm[1])+dy/m/200;
    if(Math.hypot(ux,uy)<.02){ux=Math.cos(n*2.4);uy=Math.sin(n*2.4)}
    return {g,z,o:[0,0],u:[ux,uy],fija:false}});
  // piezas sin grupo (del mismo lado o comunes): obstáculos fijos
  PIEZAS.forEach(p=>{const el=pzEl(p.id);if(enG.has(p.id)||!el||el.classList.contains("esq-lado-"+(Object.keys(LADOS).find(l=>l!==lado)||"-")))return;B.push({z:cajaIds([p.id],{}),o:[0,0],u:[0,0],fija:true})});
  const caja=b=>[b.z[0]+b.o[0]-MG/2,b.z[1]+b.o[1]-MG/2,b.z[2]+b.o[0]+MG/2,b.z[3]+b.o[1]+MG/2];
  for(let it=0;it<400;it++){let hubo=false;
    for(let i=0;i<B.length;i++)for(let j=i+1;j<B.length;j++){const A=B[i],C=B[j];if(A.fija&&C.fija)continue;const a=caja(A),c=caja(C);
      const ox=Math.min(a[2],c[2])-Math.max(a[0],c[0]), oy=Math.min(a[3],c[3])-Math.max(a[1],c[1]);if(ox<=0||oy<=0)continue;hubo=true;
      // se empuja por el eje más corto (el horizontal pesa menos: el lienzo es más ancho que alto), en el sentido de sus centros o de sus direcciones
      const ejeX=ox<=oy*1.15, k=ejeX?0:1, dc=((c[k]+c[k+2])-(a[k]+a[k+2]))/2, du=C.u[k]-A.u[k], sg=Math.abs(dc)>2?Math.sign(dc):Math.abs(du)>.01?Math.sign(du):1;
      const p=(ejeX?ox:oy)+.5, pa=A.fija?0:C.fija?p:p/2, pc=p-pa;A.o[k]-=sg*pa;C.o[k]+=sg*pc}
    if(!hubo)break}
  B.forEach(b=>{if(b.g)OFF[b.g.id]=b.o.map(v=>Math.round(v))});return OFF}
// por/dentro: desplazamiento total de cada pieza y solo el de sus pasos (sin el del bloque: el bloque no «saca» la pieza de su lugar)
function sumaTodo(k,dentro){const s={};if(k>0&&!dentro){const O=calcularOFF();GR.filter(g=>g.lado===lado).forEach(g=>{const o=O[g.id];if(o&&(o[0]||o[1]))idsDe(g).forEach(id=>{s[id]=[o[0],o[1]]})})}
  for(let i=0;i<k;i++){if(TODO[i]===SEP)continue;for(const [id,[dx,dy]] of Object.entries(PASOS[TODO[i]].m)){s[id]=s[id]||[0,0];s[id][0]+=dx;s[id][1]+=dy}}return s}
function encuadreTodo(k){const s=sumaTodo(k),ids=GR.filter(g=>g.lado===lado).flatMap(idsDe);let [x0,y0,x1,y1]=cajaIds(ids,s);
  if(k<=1){const [a,b,c,d]=VB_ARM;x0=Math.min(x0,a);y0=Math.min(y0,b);x1=Math.max(x1,a+c);y1=Math.max(y1,b+d)}   // al separar, se aleja desde el armado
  else{const z=cajaIds(ids,sumaTodo(TODO.length));x0=Math.min(x0,z[0]);y0=Math.min(y0,z[1]);x1=Math.max(x1,z[2]);y1=Math.max(y1,z[3])}   // y luego queda fijo en todo lo abierto: no salta en cada paso
  x0-=28;y0-=28;x1+=28;y1+=28;
  let w=x1-x0,h=y1-y0;const asp=900/700;if(w/h<asp){const nw=h*asp;x0-=(nw-w)/2;w=nw}else{const nh=w/asp;y0-=(nh-h)/2;h=nh}return [x0,y0,w,h].map(f)}
// cortes de grupo en la lista de pasos de todo el sistema: ◀ ▶ saltan de un grupo al siguiente
const cortes=()=>{const c=[0];for(let j=1;j<TODO.length;j++)if(grupoDePaso(TODO[j])!==grupoDePaso(TODO[j-1]))c.push(j);c.push(TODO.length);return c};
const nPasos=()=>grupo?grupo.pasos.length:TODO.length;
V2H.vb=()=>grupo?VB_G:(gPaso>0&&VB_T?VB_T:VB_ARM);
const reemplazar=id=>{const b=document.getElementById(id),n=b.cloneNode(true);b.replaceWith(n);return n};
const bTodo=reemplazar("bTodo"), bAtras=reemplazar("bAtras"), bAdel=reemplazar("bAdel");
function aplicarG(k){const antes=gPaso;if(!grupo&&!k)TODO=[SEP,...pasosLado()];gPaso=k;const s=grupo?sumaG(grupo,k):sumaTodo(k),sd=grupo?s:sumaTodo(k,true);
  if(grupo&&k!==antes){VB_G=encuadreGrupo(grupo,k);if(zoom===1)encuadrar(VB_G)}
  if(!grupo&&k!==antes){VB_T=k?encuadreTodo(k):null;zoom=1;encuadrar(VB_T||VB_ARM);estadoZoom()}
  svg.classList.toggle("esq-todo-fuera",!grupo&&k>0);
  PIEZAS.forEach(p=>{const el=pzEl(p.id),d=s[p.id]||[0,0];el.style.transform=`translate(${d[0]}px,${d[1]}px)`;const e=sd[p.id]||[0,0];el.classList.toggle("esq-fuera",e[0]!==0||e[1]!==0)});
  svg.classList.toggle("esq-explotado",k>0);focoNumeros();
  const n=nPasos();
  bTodo.hidden=bAtras.hidden=bAdel.hidden=!n;bAtras.disabled=k===0;bAdel.disabled=k===n;
  bAtras.setAttribute("aria-label",grupo?"Paso anterior":"Grupo anterior");bAdel.setAttribute("aria-label",grupo?"Paso siguiente":"Grupo siguiente");
  if(!grupo)bTodo.textContent=k===n?"Armar todo":(tempG?"Pausa":"Desarmar todo");
  if(grupo){bTodo.textContent=k===n?"Armar":(tempG?"Pausa":"Desarmar");
    textoPaso.innerHTML=k===0?`<b>${gTxt(grupo)}.</b> Toca una pieza para ver su ficha, o «Desarmar» para ver lo de adentro.`
      :`<span class="esq-v2-pason">Paso ${k} de ${n}</span> ${ENL(PASOS[grupo.pasos[k-1]].t)}`}
  else if(k>0&&TODO[k-1]===SEP)textoPaso.innerHTML=`<span class="esq-v2-pason">Paso 1 de ${n}</span> <b>Se separan los grupos.</b> Cada uno se aparta de los demás; luego sus piezas se abren dentro de su zona.`;
  else if(k>0){const g=grupoDePaso(TODO[k-1]);textoPaso.innerHTML=`<span class="esq-v2-pason">Paso ${k} de ${n}${g?" · "+gTxt(g):""}</span> ${ENL(PASOS[TODO[k-1]].t)}`}
  else textoPaso.innerHTML=`Toca un grupo para acercarte, o «Desarmar todo» para ver el sistema abierto.${VARIOS?` Cambia de lado con <b>${Object.values(LADOS).join(" | ")}</b>.`:""}`;
  escalarEtiquetas()}
function pararG(){clearInterval(tempG);tempG=null}
bTodo.addEventListener("click",()=>{const n=nPasos();
  if(tempG){pararG();aplicarG(gPaso);return}
  if(gPaso===n||REDUCIDO){aplicarG(gPaso===n?0:n);return}
  aplicarG(gPaso+1);tempG=setInterval(()=>{if(gPaso>=n){pararG();aplicarG(n);return}aplicarG(gPaso+1);if(gPaso>=n){pararG();aplicarG(n)}},Math.min(1300,Math.max(650,4800/n)));aplicarG(gPaso)});
bAtras.addEventListener("click",()=>{pararG();if(gPaso>0)aplicarG(grupo?gPaso-1:Math.max(...cortes().filter(c=>c<gPaso)))});
bAdel.addEventListener("click",()=>{pararG();if(gPaso<nPasos())aplicarG(grupo?gPaso+1:Math.min(...cortes().filter(c=>c>gPaso)))});

const volver=$("v2Volver"), titulo=$("v2Titulo"), BL=[...document.querySelectorAll(".esq-v2-lado [data-lado]")];
function quitarSel(){seleccion=null;document.querySelectorAll(".esq-pz.esq-sel").forEach(x=>x.classList.remove("esq-sel"));svg.classList.remove("esq-haysel")}
function entrarGrupo(g){pararG();grupo=g;V2H.tocado=true;const ids=new Set(idsDe(g));
  document.querySelectorAll("#capas .esq-pz").forEach(el=>el.classList.toggle("esq-engr",ids.has(el.id.slice(3))));
  svg.classList.add("esq-engrupo");gPaso=0;VB_G=encuadreGrupo(g,0);zoom=1;aplicarG(0);encuadrar(VB_G);estadoZoom();
  volver.hidden=false;titulo.textContent=gTxt(g," · ");
  quitarSel();refrescarLista();pintarInicio();requestAnimationFrame(medirAlto)}   // ronda 7: la fila de controles cambia («‹ Vista general»): «Desarmar» no queda bajo el borde
function salirGrupo(){pararG();grupo=null;document.querySelectorAll(".esq-pz.esq-engr").forEach(el=>el.classList.remove("esq-engr"));
  svg.classList.remove("esq-engrupo");zoom=1;aplicarG(0);encuadrar(VB_ARM);estadoZoom();
  volver.hidden=true;titulo.textContent="Toca un grupo del dibujo";quitarSel();refrescarLista();pintarInicio();cerrarHoja2();requestAnimationFrame(medirAlto)}
function ponerLado(l,interno){const k=seleccion&&!interno?contraparte(seleccion):null;lado=l;
  Object.keys(LADOS).forEach(x=>svg.classList.toggle("esq-l-"+x,x===l));
  BL.forEach(b=>b.setAttribute("aria-pressed",b.dataset.lado===l));
  if(V2H.marcas)V2H.marcas();
  if(interno)return;
  if(grupo){const h=GR.find(x=>x.lado===l&&x.nombre===grupo.nombre);if(h)entrarGrupo(h);else salirGrupo()}else{pararG();aplicarG(0);refrescarLista();pintarInicio()}
  if(k)seleccionar(k)}
volver.addEventListener("click",salirGrupo);
BL.forEach(b=>b.addEventListener("click",()=>{if(lado!==b.dataset.lado)ponerLado(b.dataset.lado)}));

/* ---------- selección ---------- */
V2H.sel=(k,desplazar)=>{
  if(desplazar&&k!=null)activarPestana(document.getElementById("t-piezas"));   // antes de medir: con la pestaña oculta el dibujo no tiene tamaño
  if(k==null){quitarSel();pintarInicio();marcarLista();cerrarHoja2();return}
  V2H.tocado=true;
  const g=grupoDe(k);
  if(g&&g.lado!==lado)ponerLado(g.lado,true);
  if(g&&grupo!==g)entrarGrupo(g);
  seleccion=k;
  const ids=V2T[k]?V2T[k].ids:PIEZAS.filter(p=>p.n===k).map(p=>p.id);
  document.querySelectorAll(".esq-pz").forEach(el=>el.classList.toggle("esq-sel",ids.includes(el.id.slice(3))));
  svg.classList.toggle("esq-haysel",ids.length>0);
  if(g&&!V2T[k]&&OCULTAS.includes(k)&&gPaso<g.pasos.length)aplicarG(g.pasos.length);   // pieza de adentro: se desarma el grupo para verla
  pintarFicha(k);mostrarHoja(k);marcarLista();
  if(desplazar)centrarDibujo();
};

/* ---------- catálogo (lista y ficha de la derecha) → panel izquierdo ----------
   Regla (mezcla, decidida por el usuario el 16-nov-2026):
   - desde «Piezas» o «Cómo funciona»: la izquierda pasa a «Piezas» con el grupo o la pieza elegidos (igual que al tocarlos en el dibujo),
     centrados en la pantalla y sin que los tape la cabecera;
   - desde «Si falla» o «Cuándo»: se queda en la pestaña, filtra la lista a esa pieza o grupo y ofrece «Ver en el dibujo» (lleva a «Piezas» centrado). */
const tabActual=()=>(PESTANAS.find(t=>t.getAttribute("aria-selected")==="true")||PESTANAS[0]).id;
function cabeceraAlto(){let b=0;const vistos=new Set();
  for(const e of document.elementsFromPoint(innerWidth/2,2))for(let x=e;x&&x!==document.body&&!vistos.has(x);x=x.parentElement){vistos.add(x);
    const p=getComputedStyle(x).position;if(p!=="fixed"&&p!=="sticky")continue;const r=x.getBoundingClientRect();if(r.top<=2&&r.height<innerHeight/3)b=Math.max(b,r.bottom)}
  return b}
let tCentrar=0;
function centrarDibujo(){if(h2Abierta)bajarHoja2();clearTimeout(tCentrar);
  // se espera a que termine el encuadre del grupo (650 ms; al instante con «reducir movimiento»)
  tCentrar=setTimeout(()=>{const lz=lienzoEl.getBoundingClientRect();if(!lz.width)return;
    const arriba=cabeceraAlto()+8,abajo=(!h2.hidden?h2.getBoundingClientRect().top:innerHeight)-8;
    let r=lz;if(lz.height>abajo-arriba){const sel=[...document.querySelectorAll("#capas .esq-pz.esq-sel")].map(e=>e.getBoundingClientRect()).filter(q=>q.width);
      if(sel.length){const t=Math.min(...sel.map(q=>q.top)),bt=Math.max(...sel.map(q=>q.bottom));r={top:t,bottom:bt,height:bt-t}}}
    if(r.top>=arriba&&r.bottom<=abajo)return;   // ya se ve entero: no se mueve la página
    let d=(r.top+r.bottom)/2-(arriba+abajo)/2;d=Math.min(d,lz.top-arriba);   // el borde de arriba del lienzo nunca bajo la cabecera
    scrollBy({top:d,behavior:REDUCIDO_SEL()?"auto":"smooth"})},REDUCIDO_SEL()?30:700)}
let filtro=null;   // {k} o {g}: lo elegido en el catálogo mientras se ve «Si falla» o «Cuándo»
const FILTRO_HTML=`<div class="esq-filtro" hidden><span class="esq-filtro-t"></span><button type="button" class="esq-filtro-ver">Ver en el dibujo</button><button type="button" class="esq-filtro-todo">Ver todo</button></div><p class="esq-filtro-nada" hidden></p>`;
["p-cadenas","p-plan"].forEach(id=>{const p=$(id),i=p.querySelector(".esq-intro");(i||p.firstChild).insertAdjacentHTML(i?"afterend":"beforebegin",FILTRO_HTML)});
const ksDe=f=>f.k?[f.k].concat(V2T[f.k]?V2T[f.k].ids.map(i=>(PIEZAS.find(p=>p.id===i)||{}).n):[]):f.g.ks.concat(f.g.torn.map(t=>t.k));
function pintarFiltro(){
  [["p-cadenas",".esq-cadena","Esta pieza no tiene cadenas de falla propias."],["p-plan","tbody tr","Esta pieza no tiene una fila propia: sigue el plan de su grupo."]].forEach(([id,sel,nada])=>{
    const p=$(id),bar=p.querySelector(".esq-filtro"),vac=p.querySelector(".esq-filtro-nada"),ks=filtro?ksDe(filtro):null;let n=0;
    // «Cuándo» casi no lleva enlaces: también vale la primera palabra del nombre de la pieza (sin plural), p. ej. «Pastilla…» → «Pastillas: revisar»
    const raiz=k=>{const w=sinTilde(nombreDe(k)).split(/[^a-zñ]+/).find(x=>x.length>2)||"";return w.replace(/(es|s)$/,"")};
    const raices=ks&&id==="p-plan"?[...new Set(ks.filter(Boolean).map(raiz))].filter(x=>x.length>2):[];
    p.querySelectorAll(sel).forEach(el=>{const si=!ks||[...el.querySelectorAll("button[data-k]")].some(b=>ks.includes(b.dataset.k))||raices.some(r=>new RegExp("(^|[^a-z])"+r).test(sinTilde(el.cells?el.cells[0].textContent:el.textContent)));el.hidden=!si;if(si)n++});
    bar.hidden=!filtro;vac.hidden=!filtro||n>0;vac.textContent=nada;
    if(filtro)bar.querySelector(".esq-filtro-t").innerHTML=`Solo: <b>${filtro.k?nombreDe(filtro.k):filtro.g.nombre}</b>`})}
function filtrar(f){filtro=f;pintarFiltro()}
V2H.alPestana=id=>{if(id==="t-piezas"&&filtro)filtrar(null)};
function verEnDibujo(){const f=filtro;filtrar(null);activarPestana($("t-piezas"));
  if(f.k)seleccionar(f.k,{desplazar:true});else{if(f.g.lado!==lado)ponerLado(f.g.lado,true);entrarGrupo(f.g);centrarDibujo()}}
V2H.catalogo=b=>{if(!b.closest("#ficha"))return false;const t=tabActual(),k=b.dataset.k;
  if(t==="t-cadenas"||t==="t-plan"){pintarFicha(k);mostrarHoja(k);filtrar({k});return true}
  seleccionar(k,{desplazar:true});return true};
document.addEventListener("click",e=>{
  if(e.target.closest(".esq-filtro-ver")){verEnDibujo();return}
  if(e.target.closest(".esq-filtro-todo")){filtrar(null);return}
  // abrir un grupo en la lista (la de la ficha o la de debajo del dibujo) = tocar ese grupo en el dibujo
  const sm=e.target.closest(".esq-v2-grupo>summary");if(!sm)return;const det=sm.parentElement,g=G_ID[det.dataset.g];if(!g||det.open)return;
  const t=tabActual();if(sm.closest("#ficha")&&(t==="t-cadenas"||t==="t-plan")){filtrar({g});return}
  activarPestana($("t-piezas"));if(grupo!==g){e.preventDefault();if(g.lado!==lado)ponerLado(g.lado,true);entrarGrupo(g)}centrarDibujo()});

/* ---------- lista plegable y buscador ---------- */
const botonLista=k=>`<button type="button" class="esq-v2-item" data-k="${k}"><span class="esq-v2-num">${V2T[k]?"":k}</span>${nombreDe(k)}</button>`;
function listaHTML(){
  return `<div class="esq-v2-buscar"><input type="search" class="esq-v2-q" placeholder="Buscar una pieza" aria-label="Buscar una pieza"></div><div class="esq-v2-res" hidden></div>`+
  GR.filter(g=>g.lado===lado).map(g=>`<details class="esq-v2-grupo" data-g="${g.id}"${grupo===g?" open":""}><summary>${g.nombre}<span class="esq-v2-cuenta">${g.ks.length+g.torn.length}</span></summary><ul>${g.ks.map(k=>`<li>${botonLista(k)}</li>`).join("")}${g.torn.length?`<li><details class="esq-v2-torn"><summary>Tornillería (${g.torn.reduce((a,t)=>a+t.cant,0)})</summary><ul>${g.torn.map(t=>`<li>${botonLista(t.k)}</li>`).join("")}</ul></details></li>`:""}</ul></details>`).join("")}
function refrescarLista(){$("v2Lista").innerHTML=listaHTML();marcarLista()}
function marcarLista(){document.querySelectorAll(".esq-v2-item").forEach(b=>b.classList.toggle("esq-sel",b.dataset.k===seleccion))}
const sinTilde=s=>s.normalize("NFD").replace(/[̀-ͯ]/g,"").toLowerCase();
document.addEventListener("input",e=>{const q=e.target.closest&&e.target.closest(".esq-v2-q");if(!q)return;const caja=q.closest(".esq-v2-buscar").parentElement, t=sinTilde(q.value.trim());
  const res=caja.querySelector(".esq-v2-res");caja.querySelectorAll(".esq-v2-grupo").forEach(d=>d.hidden=!!t);res.hidden=!t;if(!t)return;
  const ks=Object.keys(FICHAS).concat(Object.keys(V2T)).filter(k=>sinTilde(nombreDe(k)).includes(t)||k===t);
  res.innerHTML=ks.length?`<ul>${ks.slice(0,12).map(k=>`<li>${botonLista(k)}</li>`).join("")}</ul>`:'<p class="esq-vacia">Ninguna pieza con ese nombre.</p>'});

/* ---------- ficha ---------- */
const enl=ENL;
// v3 (opciones 7, 8, 9 y 12): semáforo «¿puedes seguir rodando?», herramientas y tiempo, glosario al tocar y última pieza vista
const RODAR={sigue:"Si falla: puedes seguir, con cuidado",pronto:"Si falla: llévala pronto al taller",no:"Si falla: no ruedes así"};
const semaforo=F=>RODAR[F.rodar]?`<p class="esq-v2-rodar esq-r-${F.rodar}"><span class="esq-r-punto" aria-hidden="true"></span>${RODAR[F.rodar]}</p>`:"";
const hazlo=F=>F.dif==="facil"&&F.hazlo?`<p class="esq-v2-hazlo">Necesitas: ${F.hazlo.herr} · unos ${F.hazlo.min} min (aprox.)</p>`:"";
// glosario: los primeros de garaje/despiece_glosario.py (ayudas); los marcados «+» son nuevos, para revisar
const GLOSARIO=[
  [/c[áa]liper/i,"Sostiene las pastillas y las empuja contra el disco cuando frenas."],
  [/diafragma/i,"Evita que entre humedad al líquido de frenos."],
  [/rodillos/i,"Hacen que el variador cambie de relación."],
  [/zapatas/i,"Hacen que la moto arranque suave."],
  [/tamiz|malla del aceite/i,"Atrapa partículas del aceite. Se limpia en cada cambio de aceite."],
  [/ret[ée]n(es)?\b|retenedor/i,"Evita que se salga el aceite."],
  [/purga(r|do)?\b/i,"+Sacar el aire del circuito por el purgador, hasta que salga solo líquido."],
  [/DOT ?4/,"+El tipo de líquido de frenos que pide la moto. Absorbe agua con el tiempo: por eso se cambia cada 2 años."],
  [/holgura/i,"+El espacio pequeño que debe quedar entre dos piezas para que trabajen bien. Se mide con calibrador de láminas."],
  [/(?<!(resortes?|leva) de (la )?)torque\b/i,"+La fuerza exacta con la que se aprieta un tornillo. Se da con llave de torque."],
  [/ralent[íi]/i,"+Las vueltas del motor en mínimo, sin acelerar."],
  [/junta t[óo]rica|o-ring/i,"+Anillo de caucho que sella la unión entre dos piezas."],
  [/manigueta/i,"+La palanca del freno que aprietas con la mano."]];
function glosar(raiz,propio){let n=0;const usados=new Set(),prop=sinTilde(propio||"");
  const nodos=[];const w=document.createTreeWalker(raiz,NodeFilter.SHOW_TEXT,{acceptNode:x=>x.parentElement.closest("button,h3,h4,summary,.esq-glos-def,.esq-v2-pedir,.esq-v2-hazlo,.esq-v2-rodar")?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT});
  while(w.nextNode())nodos.push(w.currentNode);
  for(const nd of nodos){if(n>=2)break;
    for(const [re,def] of GLOSARIO){if(usados.has(re))continue;const m=nd.textContent.match(re);if(!m)continue;
      if(prop.includes(sinTilde(m[0])))continue;   // la pieza no se define a sí misma
      usados.add(re);n++;const r=document.createRange();r.setStart(nd,m.index);r.setEnd(nd,m.index+m[0].length);
      const b=document.createElement("button");b.type="button";b.className="esq-glos";b.setAttribute("aria-expanded","false");b.textContent=m[0];
      // la definición va al final del renglón (párrafo o ítem), para no cortar la frase
      const d=document.createElement("span");d.className="esq-glos-def";d.hidden=true;d.id="glos-"+n;d.textContent=m[0][0].toUpperCase()+m[0].slice(1)+": "+def.replace(/^\+/,"");b.setAttribute("aria-controls",d.id);
      const blk=nd.parentElement.closest("p,li")||nd.parentElement;r.deleteContents();r.insertNode(b);blk.appendChild(d);break}}}
// kits de venta (D.kits = {"ref": [refs que trae]}): sin dibujo; el nombre sale del «cat» de las piezas («… kit ref. 1 (clutch completo, código)»)
const KITS=(()=>{const k=D.kits||{};return Array.isArray(k)?Object.fromEntries(k.map(r=>[String(r),[]])):Object.fromEntries(Object.entries(k).map(([r,v])=>[String(r),v.map(String)]))})();
const nombreKit=r=>{for(const F of Object.values(FICHAS)){const m=String(F.cat||"").match(new RegExp("kit ref\\. "+r+" \\(([^,)]+)"));if(m)return m[1]}return "kit ref. "+r};
const kitLinea=k=>{const rs=Object.keys(KITS).filter(r=>KITS[r].includes(String(k)));return rs.length?`<p class="esq-v2-kit">Se vende en kit: ${rs.map(r=>`${nombreKit(r)} (ref. ${r})`).join(" · ")}</p>`:""};
const kitsInicio=()=>{const rs=Object.keys(KITS);return rs.length?`<p class="esq-v2-kit">Se vende en kit: ${rs.map(r=>`${nombreKit(r)} (ref. ${r}${KITS[r].length?`, ${KITS[r].length} piezas`:""})`).join(" · ")}. Lo dice «Para pedirla» en cada pieza.</p>`:""};
const ULT="esq-ultima:"+(D.lamina||D.arte);
const guardarUlt=k=>{try{localStorage.setItem(ULT,k)}catch(_){}};
const leerUlt=()=>{try{return localStorage.getItem(ULT)}catch(_){return null}};
const QUIEN={facil:"Lo puedes hacer tú",media:"Mejor en el taller",taller:"Mejor en el taller"};
const sec=(t,c,cl)=>c?`<section class="esq-v2-sec${cl?" "+cl:""}"><h4>${t}</h4>${c}</section>`:"";
const CERT={ok:["✓ manual","Sale del catálogo de partes o del manual de servicio de la moto."],ap:["≈ aprox.","Práctica de taller: es lo normal, pero puede variar en tu moto."]};
// marca chica de certeza al final del dato; al tocarla, una línea explica de dónde sale
const cm=(F,campo)=>{const s=F.certezaDe&&F.certezaDe[campo];return CERT[s]?` <button type="button" class="esq-cert esq-cert-${s}" aria-expanded="false">${CERT[s][0]}</button><span class="esq-cert-def" hidden>${CERT[s][1]}</span>`:""};
const pc=(F,campo,t)=>t?`<p>${enl(t)}${cm(F,campo)}</p>`:"";
const ulc=(F,campo,a)=>a&&a.length?`<ul>${a.map((x,i)=>`<li>${enl(x)}${i===a.length-1?cm(F,campo):""}</li>`).join("")}</ul>`:"";
const ul=a=>a&&a.length?`<ul>${a.map(x=>`<li>${enl(x)}</li>`).join("")}</ul>`:"";
const DECISION={repara:['esq-d-repara','Se repara'],reutiliza:['esq-d-repara','Se reutiliza'],cambia:['esq-d-cambia','Se cambia']};
const etDecision=F=>F.decision&&DECISION[F.decision]?`<span class="esq-decision ${DECISION[F.decision][0]}">${DECISION[F.decision][1]}</span>`:"";
const acciones=F=>`<p class="esq-v2-pedir">Para pedirla: ${F.cat.split(" · ")[0]}${F.codigo?" · "+F.codigo:""}<span class="esq-v2-acc"><a class="esq-v2-a" href="#pedir-repuesto" data-codigo="${F.codigo||""}"><span aria-hidden="true">🛒</span> Pedir repuesto</a><a class="esq-v2-a" href="#talleres"><span aria-hidden="true">🔧</span> Talleres</a></span></p>`;
const v3d=nombre=>window.Esquema3D?`<div class="esq-v3d"><div class="esq-v3d-lienzo" role="img" aria-label="Modelo 3D de ${nombre}"></div><div class="esq-v3d-barra"><button type="button" class="esq-v3d-ant" aria-label="Girar a la vista anterior">◀</button><span class="esq-v3d-estado" aria-live="polite">Cargando el modelo 3D…</span><button type="button" class="esq-v3d-sig" aria-label="Girar a la vista siguiente">▶</button></div></div>`:"";
function montar3d(forma,nombre){if(!window.Esquema3D)return;const v=fichaEl.querySelector(".esq-v3d");if(v&&forma)Esquema3D.montar(v,forma,nombre);else Esquema3D.soltar()}
function cabecera(k,nombre,g){const o=orden();let i=o.indexOf(k);
  if(i<0){const t=Object.values(V2T).find(t=>t.ids.some(id=>PIEZAS.find(p=>p.id===id).n===k));if(t)i=o.indexOf(t.k)}   // pieza de una tornillería: sus flechas son las de su punto
  const ant=i>0?o[i-1]:null,sig=i>=0&&i<o.length-1?o[i+1]:null;
  return `<div class="esq-v2-nav"><button type="button" class="esq-v2-flecha"${ant?` data-k="${ant}" aria-label="Anterior: ${nombreDe(ant)}"`:" disabled"}>‹ anterior</button><button type="button" class="esq-v2-alista">lista</button><button type="button" class="esq-v2-flecha"${sig?` data-k="${sig}" aria-label="Siguiente: ${nombreDe(sig)}"`:" disabled"}>siguiente ›</button></div>
  <div class="esq-cab"><div><h3 tabindex="-1">${nombre}</h3><div class="esq-v2-sub">${g?gTxt(g," · "):""}${V2T[k]?"":`<span class="esq-v2-num"> · n.º ${k}</span>`}</div></div></div>`}
function pintarInicio(){
  const conj=grupo&&V2.conjunto3d&&V2.conjunto3d[grupo.id.split("-")[0]];
  fichaEl.innerHTML=`<div class="esq-v2-inicio"><h3 tabindex="-1">${grupo?gTxt(grupo," · "):LADO_TXT[lado]?`Piezas del ${LADO_TXT[lado]}`:(V2.inicio||"Piezas de la lámina")}</h3>
    ${conj?`<p class="esq-v2-sub">${conj.titulo}: gírala con las flechas.</p>${v3d(conj.titulo)}`:""}
    <p class="esq-vacia">${grupo?"Toca una pieza del dibujo o de la lista.":"Toca un grupo del dibujo o una pieza de la lista."}</p>
    ${(()=>{const u=!grupo&&V2H.tocado&&leerUlt();   /* ronda 9: solo después de elegir una pieza o un grupo en esta visita */return u&&(FICHAS[u]||V2T[u])?`<p class="esq-v2-seguir">Seguir con: <button type="button" class="esq-enl" data-k="${u}">${nombreDe(u)}</button></p>`:""})()}
    ${grupo?"":kitsInicio()}<div class="esq-ficha-lista">${listaHTML()}</div></div>`;
  montar3d(conj?{partes:conj.partes}:null,conj&&conj.titulo);marcarLista();
  if(innerWidth>=960){const d=fichaEl.querySelector(".esq-v2-grupo[open]");fichaEl.scrollTop=d?Math.max(0,d.getBoundingClientRect().top-fichaEl.getBoundingClientRect().top+fichaEl.scrollTop-56):0}}
function pintarTorn(k){const t=V2T[k], ns=[...new Set(t.ids.map(i=>PIEZAS.find(p=>p.id===i).n))];
  fichaEl.innerHTML=cabecera(k,`${t.nombre} (${t.cant})`,t.g)+`<p class="esq-v2-intro">Lo que sujeta este punto. Sale junto al desarmar.</p>`+
    ns.map(n=>{const F=FICHAS[n];return `<section class="esq-v2-tpieza"><h4>${F.nombre}</h4><p>${enl(F.que)}</p><p>${etDecision(F)} <span class="esq-v2-quien">${QUIEN[F.dif]||""}</span></p><p>${enl(F.porque)}</p><p>${enl(F.cuando)}</p>${acciones(F)}${kitLinea(n)}<button type="button" class="esq-v2-completa" data-k="${n}">Ver ficha completa ›</button></section>`}).join("");
  montar3d(null)}
V2H.ficha=k=>{
  if(k==null){pintarInicio();return}
  if(V2T[k]){pintarTorn(k);return}
  const F=FICHAS[k];if(!F){fichaEl.innerHTML='<p class="esq-vacia">Sin ficha.</p>';return}
  const fallas=(F.fallas||[]).length?`<ul class="esq-v2-fallas">${F.fallas.map(([c,t],i)=>`<li><button type="button" class="esq-causa esq-c-${c}" aria-expanded="false"><span aria-hidden="true">${ICONO[c]}</span> ${CAUSA[c]}</button> ${enl(t)}${i===F.fallas.length-1?cm(F,"fallas"):""}<span class="esq-causa-def" hidden>${CAUSA[c]}: ${CAUSA_DEF[c]}.</span></li>`).join("")}</ul>`:"";
  const dec=F.decision?`<p>${etDecision(F)} <span class="esq-v2-quien">${QUIEN[F.dif]||""}</span></p>${hazlo(F)}${pc(F,"porque",F.porque||F.compra||"")}`:"";
  const cuando=F.cuando?`${pc(F,"cuando",F.cuando)}${F.ctx||!F.cat?"":acciones(F)}${kitLinea(k)}`:"";
  const rel=(F.conecta||[]).length?`<div class="esq-v2-chips">${F.conecta.map(c=>`<button type="button" class="esq-v2-chip" data-k="${c}" title="${nombreDe(c)}" aria-label="${nombreDe(c)}"><span>${(FICHAS[c]&&FICHAS[c].corto)||nombreDe(c)}</span></button>`).join("")}</div>`:"";
  const arr=F.arrastra||(F.efectos||[]).map(([o,t])=>`[[${o}|${nombreDe(o)}]] → ${t}`);
  const cert=(F.certeza||[]).length?`<details class="esq-v2-fuentes"><summary><svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true"><path d="M2 3.2c2-.9 4-.9 6 .4 2-1.3 4-1.3 6-.4v9.6c-2-.9-4-.9-6 .4-2-1.3-4-1.3-6-.4z M8 3.6v9.6" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>Fuentes</summary><div class="esq-certeza">${F.certeza.map(([s,t])=>`<div><span class="${s==='ok'?'esq-s-ok':'esq-s-ap'}">${s==='ok'?'Seguro':'Aproximado'}:</span> ${t}</div>`).join("")}</div></details>`:"";
  const con3d=F.forma3d&&(V2.con3d||[]).includes(k);
  fichaEl.innerHTML=cabecera(k,F.nombre,grupoDe(k))+(con3d?v3d(F.nombre):"")+
    `<div class="esq-v2-cuerpo">`+semaforo(F)+sec("Qué es",pc(F,"que",F.que),"esq-o-que")+sec("Para qué sirve",pc(F,"sirve",F.sirve),"esq-o-sirve")+sec("Señales de que falla",ulc(F,"sintomas",F.sintomas),"esq-o-senal")+
    sec("Por qué falla",fallas,"esq-o-falla")+sec("¿Se repara o se cambia?",dec,"esq-o-dec")+sec("Cuándo revisarla o cambiarla",cuando,"esq-o-cuando")+`</div>`+
    `<details class="esq-v2-mas"${innerWidth>=960?" open":""}><summary>Piezas relacionadas y qué arrastra si falla</summary>${sec("Piezas relacionadas",rel)}${sec("Si falla, qué arrastra",arr.length?`<ul class="esq-v2-arrastra">${arr.map(x=>`<li>${enl(x)}</li>`).join("")}</ul>`:"")}</details>${cert}`;
  glosar(fichaEl.querySelector(".esq-v2-cuerpo"),F.nombre);guardarUlt(k);
  montar3d(con3d?F.forma3d:null,F.nombre);fichaEl.scrollTop=0};
document.addEventListener("click",e=>{
  const ce=e.target.closest(".esq-cert[aria-expanded]");
  if(ce){const d=ce.nextElementSibling,on=ce.getAttribute("aria-expanded")!=="true";ce.setAttribute("aria-expanded",on);d.hidden=!on;return}
  const gl=e.target.closest(".esq-glos");
  if(gl){const d=document.getElementById(gl.getAttribute("aria-controls")),on=gl.getAttribute("aria-expanded")!=="true";gl.setAttribute("aria-expanded",on);d.hidden=!on;return}
  const c=e.target.closest(".esq-causa[aria-expanded]");
  if(c){const d=c.parentElement.querySelector(".esq-causa-def"),on=c.getAttribute("aria-expanded")!=="true";c.setAttribute("aria-expanded",on);d.hidden=!on;return}
  if(e.target.closest(".esq-v2-alista")){seleccionar(null);if(innerWidth<960)$("v2Lista").scrollIntoView({behavior:REDUCIDO_SEL()?"auto":"smooth",block:"start"})}
  if(e.target.closest('a[href="#pedir-repuesto"],a[href="#talleres"]'))e.preventDefault();
});

/* ---------- dibujo: tocar grupos y piezas, nombre al pasar ---------- */
const tip=document.createElement("div");tip.className="esq-v2-nombre";tip.hidden=true;tip.setAttribute("aria-hidden","true");lienzoEl.appendChild(tip);
let tipT=null, hovG=null;
function etiquetaDe(el){if(!el||!el.classList.contains("esq-pz"))return null;const id=el.id.slice(3),g=grupoDeId[id];if(!g||g.lado!==lado)return null;
  if(!grupo)return {g,t:g.nombre};if(g!==grupo)return null;return {g,t:tornDeId[id]?`${tornDeId[id].nombre} (${tornDeId[id].cant})`:nombreDe(el.dataset.n)}}
function mostrarTip(t,x,y){const r=lienzoEl.getBoundingClientRect();tip.textContent=t;tip.hidden=false;
  tip.style.left=Math.min(r.width-8,Math.max(8,x-r.left))+"px";tip.style.top=Math.max(4,y-r.top-18)+"px"}
function resaltarGrupo(g){if(hovG===g)return;hovG=g;document.querySelectorAll(".esq-pz").forEach(el=>el.classList.toggle("esq-hov",!!g&&el.dataset.g===g.id));
  document.querySelectorAll(".esq-marca-g").forEach(m=>{const si=!!g&&m.dataset.g===g.id;m.classList.toggle("esq-crece",si);if(si)m.parentNode.appendChild(m)})}
svg.addEventListener("pointermove",e=>{if(e.pointerType!=="mouse")return;const el=e.target.closest(".esq-pz");
  const mk=e.target.closest(".esq-marca");
  if(mk){tip.hidden=true;resaltarGrupo(null);if(mk.parentNode.lastElementChild!==mk&&mk.classList.contains("esq-marca-g"))mk.parentNode.appendChild(mk);return}
  const q=etiquetaDe(el);if(!q){tip.hidden=true;resaltarGrupo(null);return}
  if(!grupo&&!gPaso){tip.hidden=true;resaltarGrupo(q.g);return}
  mostrarTip(q.t,e.clientX,e.clientY);resaltarGrupo(null)});
svg.addEventListener("pointerleave",()=>{tip.hidden=true;resaltarGrupo(null)});
svg.addEventListener("click",e=>{
  const m=e.target.closest(".esq-marca");
  if(m){e.stopPropagation();if(m.dataset.g)entrarGrupo(G_ID[m.dataset.g]);else seleccionar(m.dataset.k);return}
  const el=e.target.closest(".esq-pz");if(!el)return;e.stopPropagation();
  const id=el.id.slice(3),g=grupoDeId[id];if(!g||g.lado!==lado)return;
  if(grupo!==g){if(!grupo)entrarGrupo(g);return}
  const q=etiquetaDe(el);seleccionar(tornDeId[id]?tornDeId[id].k:el.dataset.n);
  if(e.pointerType&&e.pointerType!=="mouse"&&q){mostrarTip(q.t,e.clientX,e.clientY);clearTimeout(tipT);tipT=setTimeout(()=>tip.hidden=true,1800)}
});
svg.addEventListener("keydown",e=>{const m=e.target.closest(".esq-marca");if(m&&(e.key==="Enter"||e.key===" ")){e.preventDefault();m.dispatchEvent(new MouseEvent("click",{bubbles:true}))}});
// «Números»: también muestra los números en la lista y en la ficha
$("iNum").addEventListener("click",()=>document.querySelector(".esq-envoltura").classList.toggle("esq-v2-numeros",$("iNum").getAttribute("aria-pressed")==="true"));
/* ---------- celular: hoja inferior ---------- */
const h2=$("hoja2"), h2Cab=$("h2Cab"), h2Ver=$("h2Ver"), h2Cuerpo=$("h2Cuerpo"), lugarFicha=document.createComment("ficha");
let h2Abierta=false;
const textoPlano=s=>String(s||"").replace(/\[\[[^|\]]+\|([^\]]+)\]\]/g,"$1").replace(/<[^>]+>/g,"");
function abrirHoja2(){if(h2Abierta)return;h2Abierta=true;fichaEl.before(lugarFicha);h2Cuerpo.appendChild(fichaEl);h2.classList.add("esq-h2-abierta");
  h2Ver.setAttribute("aria-expanded","true");h2Ver.textContent="Bajar";h2Cuerpo.scrollTop=0;const h=fichaEl.querySelector("h3");if(h)h.focus({preventScroll:true})}
function bajarHoja2(){if(!h2Abierta)return;h2Abierta=false;lugarFicha.replaceWith(fichaEl);h2.classList.remove("esq-h2-abierta");
  h2Ver.setAttribute("aria-expanded","false");h2Ver.textContent="Ver ficha"}
function cerrarHoja2(){bajarHoja2();h2.hidden=true;document.documentElement.classList.remove("esq-con-hoja")}
V2H.hoja=k=>{
  if(innerWidth>=960||k==null||(!FICHAS[k]&&!V2T[k])){cerrarHoja2();return}
  $("h2T").textContent=nombreDe(k);
  $("h2Q").textContent=V2T[k]?"Lo que sujeta este punto. Sale junto al desarmar.":textoPlano(FICHAS[k].que);
  if(!h2Abierta&&fichaVisible){h2.hidden=true;return}
  const nueva=h2.hidden;h2.hidden=false;document.documentElement.classList.add("esq-con-hoja");
  // que la hoja no tape el dibujo: si el borde de abajo del lienzo queda debajo de la hoja, se sube la página lo justo
  if(nueva)requestAnimationFrame(()=>{const r=lienzoEl.getBoundingClientRect(),t=h2.getBoundingClientRect().top,d=Math.min(r.bottom-t+8,r.top-8);if(d>0)scrollBy({top:d,behavior:REDUCIDO_SEL()?"auto":"smooth"})})};
V2H.hojaVis=()=>{if(h2Abierta)return;if(fichaVisible)h2.hidden=true;else if(seleccion&&innerWidth<960)V2H.hoja(seleccion)};
h2Ver.addEventListener("click",()=>h2Abierta?bajarHoja2():abrirHoja2());
$("h2X").addEventListener("click",cerrarHoja2);
let h2y=null;
h2Cab.addEventListener("pointerdown",e=>{if(e.target.closest("button"))return;h2y=e.clientY;h2Cab.setPointerCapture(e.pointerId)});
h2Cab.addEventListener("pointermove",e=>{if(h2y==null)return;const d=e.clientY-h2y;h2.style.transform=d>0?`translateY(${d}px)`:""});
h2Cab.addEventListener("pointerup",e=>{if(h2y==null)return;const d=e.clientY-h2y;h2y=null;h2.style.transform="";
  if(d<-30)abrirHoja2();else if(d>30){h2Abierta?bajarHoja2():cerrarHoja2()}else if(Math.abs(d)<6)h2Abierta?bajarHoja2():abrirHoja2()});
h2Cab.addEventListener("pointercancel",()=>{h2y=null;h2.style.transform=""});
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&h2Abierta)bajarHoja2()});
addEventListener("resize",()=>{if(innerWidth>=960)cerrarHoja2()});
aplicarG(0);refrescarLista();pintarInicio();
}

// para las pruebas en el navegador (medir toques sin esperar animaciones)
window.__esq={aplicar,ponerVista,escalarEtiquetas,VB_ARM,get VB_EXP(){return VB_EXP},fijarVB(vb){cancelAnimationFrame(vbAnim);vbActual=vb.slice();svg.setAttribute("viewBox",vb.join(" "));escalarEtiquetas()}};
}};
})();
