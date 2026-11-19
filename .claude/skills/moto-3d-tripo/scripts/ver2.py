import sys; sys.path.insert(0, sys.argv[1])
import rend, numpy as np
d, salida, pref = sys.argv[2], sys.argv[3], sys.argv[4]
P, N, C, I = rend.cargar(d, pref)
ims = []
for esp in sys.argv[5:]:
    v, esc, caja = esp.split(';')
    caja = eval(caja)
    cen = P[I].mean(1); m = np.all((cen >= np.array(caja[0]) - 0.02) & (cen <= np.array(caja[1]) + 0.02), axis=1) if caja else np.ones(len(I), bool)
    ims.append(rend.vista(P, N, I[m], None, v, float(esc), caja, colvert=C))
rend.lamina(ims, salida, cols=2)
