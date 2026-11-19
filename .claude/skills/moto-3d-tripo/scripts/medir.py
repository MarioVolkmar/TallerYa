import sys; sys.path.insert(0, sys.argv[1])
import rend, numpy as np
P, N, C, I = rend.cargar(sys.argv[2]); x, y, z = P.T.astype(float); az = abs(z)
def circ(cx, cy, R):
    m = (az < 0.02) & (y < cy) & (abs(np.hypot(x-cx, y-cy) - R) < 0.04)
    A = np.c_[2*x[m], 2*y[m], np.ones(m.sum())]; s = np.linalg.lstsq(A, x[m]**2 + y[m]**2, rcond=None)[0]
    return s[0], s[1], np.sqrt(s[2] + s[0]**2 + s[1]**2)
for nom, c in (('del', (0.635, 0.31)), ('tras', (-0.635, 0.32))):
    cx, cy, R = circ(*c, 0.31); r = np.hypot(x-cx, y-cy)
    print(nom, 'centro', round(cx, 3), round(cy, 3), 'R', round(R, 3))
    bajo = y < cy - 0.05
    for a, b in ((0.10, 0.2), (0.2, 0.235), (0.235, 0.26), (0.26, R-0.02), (R-0.02, R+0.02)):
        m = bajo & (r > a) & (r < b); print('   r', a, round(b, 3), 'n', m.sum(), 'az max', az[m].max().round(3) if m.any() else '-', 'p95', np.percentile(az[m], 95).round(3) if m.any() else '-')
    # perfil radial de |z| en la mitad baja (para ver aro/llanta)
    h = [(round(a, 3), int(((r > a) & (r < a+0.01) & bajo).sum())) for a in np.arange(0.18, R+0.02, 0.01)]; print('   hist r', h)
    for sg, lado in ((1, '+z'), (-1, '-z')):
        m = (r < 0.14) & (r > 0.06) & (z*sg > 0.02) & (z*sg < 0.12)
        hz, e = np.histogram(z[m]*sg, bins=np.arange(0.02, 0.125, 0.005)); print('   lado', lado, 'hist z', list(zip(e[:-1].round(3), hz)))
# bultos lejos del plano medio
for nom, m in (('frente y>0.75', (x > 0.3) & (y > 0.75) & (y < 1.0) & (az > 0.14)), ('bajo 0.6-0.7', (x > 0.2) & (x < 0.45) & (y > 0.58) & (y < 0.72) & (az > 0.1)),
               ('cola', (x < -0.7) & (y > 0.6) & (az > 0.09)), ('cola centro', (x < -0.9)), ('manubrio', (y > 0.95) & (az > 0.2)), ('espejos', (y > 1.12))):
    for sg in (1, -1):
        k = m & (z*sg > 0)
        if k.any(): print(nom, '+' if sg > 0 else '-', k.sum(), 'x', x[k].min().round(3), x[k].max().round(3), 'y', y[k].min().round(3), y[k].max().round(3), 'z', z[k].min().round(3), z[k].max().round(3))
