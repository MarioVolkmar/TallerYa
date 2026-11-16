# uso: medir.sh [?calidad=baja] claves...   → tri/calls/mallas tras 6 s y tiempos del primer cuadro
S="/c/Users/volkm/AppData/Local/Temp/claude/7ac1c0565177d901/875f8961-3274-4cc7-bda0-1ec938816206/scratchpad"
Q="$1"; shift; L=$(printf '"%s",' "$@")
Q="$Q" node "$S/cdp.mjs" - "(async()=>{const o=[]; for (const k of [${L%,}]) { const r = await __probar(k); await new Promise(r=>setTimeout(r,6000)); __visor.cuadro(); const i=__visor.info(); const t=i.tiempos||{}; o.push(r.split(':')[0]+' | tri '+i.triangulos+' calls '+i.llamadas+' prog '+(i.programas??'-')+' | armada '+Math.round(t.armada-t.arranca)+' 1er cuadro '+Math.round(t.primerCuadro-t.arranca)+' ms'); } return o.join('\n')})()"
