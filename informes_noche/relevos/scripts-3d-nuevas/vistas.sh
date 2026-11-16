# uso: vistas.sh salida.jpg '[["xr 190",0,0.1,3.3],...]' [cols] [ancho]
S="/c/Users/volkm/AppData/Local/Temp/claude/7ac1c0565177d901/875f8961-3274-4cc7-bda0-1ec938816206/scratchpad"
node "$S/cdp.mjs" "$S/$1" "(async()=>{window.__F=0; __vistas($2, ${3:-4}); for(let i=0;i<400&&!window.__F;i++) await new Promise(r=>setTimeout(r,500)); return 'F='+window.__F})()"
/c/dev/TallerYa/venv/Scripts/python.exe -I -c "
from PIL import Image; import sys; p=sys.argv[1]; im=Image.open(p); w=int(sys.argv[2]); im.thumbnail((w,w*3)); im.save(p,quality=80); print(im.size)" "$S/$1" ${4:-900}
