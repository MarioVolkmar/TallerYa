// Resumen de una lámina del motor en el ancho actual: distribución + toques estrictos + densidad. Usa los tres scripts *_motor.js.
(async()=>{const S=(ms)=>new Promise(r=>setTimeout(r,ms));await S(1000);const g=async(f)=>await eval(await (await fetch('/informes_noche/piloto-esquema/integracion/'+f)).text());
window.scrollTo(0,0);const d=JSON.parse(await g('medir_distribucion_motor.js'));const t=JSON.parse(await g('medir_toques_motor.js'));const n=JSON.parse(await g('medir_densidad_motor.js'));
const c=(o)=>o.centro+(o.roces.length?' R:'+o.roces.join(','):'')+(o.fallas.length?' F:'+o.fallas.join(','):'')+' r'+o.radioMin;
return JSON.stringify({v:d.vista,dib:d.dibujo,desarmar:d.desarmarVisible,apoyo:d.apoyoPct,cols:d.columnas.map(x=>x.top+'/'+x.w+'/'+x.hueco),desb:d.desborde,alto:d.alto,armN:c(t.armN),armT:c(t.armT),desT:c(t.desT),desN:c(t.desN),dmin:n.distMin,p24:n.paresMenos24,disco:n.discoMin,letra:n.letraMin,fuera:n.fueraDelLienzo})})()
