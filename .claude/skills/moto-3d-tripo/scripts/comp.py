import sys; sys.path.insert(0, sys.argv[1])
import rend, numpy as np
def componentes(nv, I):
    padre = np.arange(nv)
    def raiz(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]; a = padre[a]
        return a
    for a, b, c in I.tolist():
        ra, rb, rc = raiz(a), raiz(b), raiz(c)
        m = min(ra, rb, rc); padre[ra] = m; padre[rb] = m; padre[rc] = m
    r = np.array([raiz(i) for i in range(nv)])
    return r[I[:, 0]]
if __name__ == '__main__':
    d = sys.argv[2]; P, N, C, I = rend.cargar(d)
    cf = componentes(len(P), I)
    ids, cnt = np.unique(cf, return_counts=True)
    orden = np.argsort(-cnt)
    print('componentes', len(ids), 'caras en las 10 mayores', cnt[orden][:10].sum(), 'de', len(I))
    cen = P[I].mean(1); lum = C[I].mean(1).mean(1)
    for k in orden[:45]:
        m = cf == ids[k]
        print(cnt[k], 'min', cen[m].min(0).round(2), 'max', cen[m].max(0).round(2), 'lum', lum[m].mean().round(2))
    np.save(f'{d}/s_comp.npy', cf)
