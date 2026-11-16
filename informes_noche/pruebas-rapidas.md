# Pruebas rápidas

| | Antes | Después |
|---|---|---|
| Completa (526) | 15 m 28 s, serie | ~30-45 s (paralelo + MD5) |
| Rápida `--exclude-tag=lenta` (485) | — | ~30-48 s (medida con la máquina cargada) |
| Solo MD5, serie | — | 1 m 00 s |

Causa de la lentitud: el hash PBKDF2 en cada `create_user` (suma 917 s en serie). Top antes: LoginLimiteTests.test_bloquea_tras_10_fallos (27 s), SinNmasUnoTests (69 s), TramitesTests (57 s), ReglasTests (53 s).

Cambios: `config/settings.py` (solo con `test`: MD5 + TEST_RUNNER), `config/test_runner.py` (paralelo por defecto, `TEST_TIMING`), `@tag("lenta")` en DespieceTests, DiagramasPropiosTests (garaje/tests.py), VistaDiagnosticoTests y EsquemaPorLaminaTests (garaje/tests_diagnostico.py), CLAUDE.md.
No hizo falta: setUpTestData (tras MD5 ninguna clase pasa de 3 s en serie), ni arreglar pruebas para paralelo (todas pasan; usan mkdtemp). `--keepdb` sin beneficio con SQLite en memoria. Código de la app: sin tocar. Sin commit.
