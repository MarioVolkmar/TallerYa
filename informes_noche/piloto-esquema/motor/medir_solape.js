// Solapamiento en el «Desarmar todo» de la vista general (modelo v2): qué parte de cada pieza queda tapada por otras.
// Lo usa medir_lamina.py (a 1280) y se puede correr a mano en la consola de la lámina: await (medir_solape)().
// Muestrea una rejilla de puntos sobre cada pieza; en cada punto donde la pieza está dibujada (y se ve: opacidad > 0,15),
// cuenta si encima hay dibujo de otra pieza. tapado = puntos con otra pieza encima / puntos donde la pieza está dibujada.
// Devuelve {lados:{lado:{piezas:[{id,tapado,pts}], peor, invisibles:[ids]}}}. No deja la lámina cambiada: vuelve a armar.
async function medir_solape(N){N=N||14;const S=ms=>new Promise(r=>setTimeout(r,ms)),svg=document.getElementById("lamina");
  const st=document.createElement("style");
  st.textContent="#lamina,#lamina *{transition:none!important;animation:none!important}#lamina .esq-pz .esq-arte,#lamina .esq-pz .esq-arte *{pointer-events:visiblePainted!important}"+
    "#lamina .esq-marca,#lamina .esq-marca *,#lamina #guiasG,#lamina #guiasG *,#lamina .esq-toque-pz,#lamina .esq-et,#lamina .esq-et *{pointer-events:none!important}";
  document.head.appendChild(st);
  const op=new Map(),opac=e=>{if(!e||e===svg)return 1;if(op.has(e))return op.get(e);const c=getComputedStyle(e);const v=c.display==="none"||c.visibility==="hidden"?0:(+c.opacity)*opac(e.parentElement);op.set(e,v);return v};
  // se mide en Normal, sin «Números» (la medición anterior o el navegador pueden haber dejado Transparente puesto)
  ["iTrans","iNum"].forEach(id=>{const b=document.getElementById(id);if(b&&b.getAttribute("aria-pressed")==="true")b.click()});
  const volver=document.getElementById("v2Volver");if(volver&&!volver.hidden){volver.click();await S(80)}
  const lados=[...document.querySelectorAll(".esq-v2-lado [data-lado]")],R={lados:{}};
  for(const bl of (lados.length?lados:[null])){if(bl){bl.click();await S(80)}
    const ad=document.getElementById("bAdel");let g=0;while(ad&&!ad.disabled&&!ad.hidden&&g++<120){ad.click();await S(15)}
    // la lámina puede reencuadrarse al terminar de cargar (letras, tamaño): se repite el último paso para fijar su encuadre
    await document.fonts.ready;await S(600);const bt0=document.getElementById("bAtras");if(bt0&&!bt0.disabled){bt0.click();await S(60);ad.click()}
    svg.scrollIntoView({block:"center"});await S(900);op.clear();
    const pz=[...svg.querySelectorAll("#capas .esq-pz")].filter(e=>{const a=e.querySelector(".esq-arte");return a&&opac(a)>.15&&a.getBoundingClientRect().width>0&&(!bl||e.classList.contains("esq-lado-"+bl.dataset.lado))});   // con lados, solo las del lado elegido (las otras quedan atenuadas de contexto)
    const out=[],inv=[];
    for(const p of pz){const r=p.querySelector(".esq-arte").getBoundingClientRect();let pts=0,tap=0;const por={};const nx=Math.min(40,Math.max(N,Math.ceil(r.width/3))),ny=Math.min(40,Math.max(N,Math.ceil(r.height/3)));
      for(let i=0;i<nx;i++)for(let j=0;j<ny;j++){const x=r.left+(i+.5)*r.width/nx,y=r.top+(j+.5)*r.height/ny;if(x<0||y<0||x>innerWidth||y>innerHeight)continue;
        let encima=false,esta=false;
        for(const e of document.elementsFromPoint(x,y)){const a=e.closest("#capas .esq-pz .esq-arte");if(!a||opac(e)<=.15)continue;const q=a.closest(".esq-pz");
          if(q===p){esta=true;break}if(opac(e)<.5)continue;   // una pieza atenuada de contexto (el otro lado) encima no tapa: se ve a través
          if(!encima)por[q.id.slice(3)]=(por[q.id.slice(3)]||0)+1;encima=true}
        if(esta){pts++;if(encima)tap++}}
      if(!pts&&!R.dbg){const x=r.left+r.width/2,y=r.top+r.height/2;R.dbg={vb:svg.getAttribute("viewBox"),sr:[...Object.values(svg.getBoundingClientRect().toJSON())].map(Math.round),tr:p.style.transform,k:document.getElementById("textoPaso").textContent.slice(0,40),id:p.id,r:[r.left,r.top,r.width,r.height].map(Math.round),pila:document.elementsFromPoint(x,y).slice(0,6).map(e=>e.tagName+"."+(e.getAttribute("class")||"")+" pe="+getComputedStyle(e).pointerEvents+" op="+opac(e).toFixed(2))}}
      if(!pts)inv.push(p.id.slice(3));else out.push({id:p.id.slice(3),tapado:Math.round(100*tap/pts),pts,por:Object.entries(por).sort((a,b)=>b[1]-a[1]).slice(0,2).map(x=>x[0]).join("+")})}
    out.sort((a,b)=>b.tapado-a.tapado);
    // cajas (unidades del dibujo, ya desplazadas) de las piezas tapadas y de las que las tapan, para corregir los pasos
    const cj=id=>{const e=document.getElementById("pz-"+id);if(!e)return null;const b=e.querySelector(".esq-arte").getBBox(),m=/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform||"")||[0,0,0];return [b.x+ +m[1],b.y+ +m[2],b.width,b.height].map(Math.round)};
    out.filter(o=>o.tapado>8).forEach(o=>{o.caja=cj(o.id);o.cajasPor=o.por.split("+").map(i=>[i,cj(i)])});
    R.lados[bl?bl.dataset.lado:"unico"]={piezas:out.slice(0,8),peor:out.length?out[0].tapado:0,invisibles:inv};
    const bt=document.getElementById("bAtras");g=0;while(bt&&!bt.disabled&&g++<120){bt.click();await S(10)}}
  st.remove();return R}
