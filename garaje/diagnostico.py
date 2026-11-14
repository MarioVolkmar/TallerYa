"""Diagnóstico guiado: síntoma → 1–3 preguntas → sistema probable, piezas candidatas, urgencia y talleres.

Solo datos (sin modelos). Los sistemas usan los mismos nombres que el despiece (despiece_sistemas.SISTEMAS).
Las únicas diferencias entre motos son de transmisión ("cadena" = de cambios, "cvt" = automática) y, donde
cambia la causa, de refrigeración ("liquido" / "aire").

Cada síntoma tiene:
- "preguntas": lista de {"clave", "texto", "opciones": [(valor, texto, condicion)], "si": {clave: valores}}.
  Una opción o una pregunta con condición solo aparece si se cumple (p. ej. {"t": "cvt"}).
- "reglas": lista de (condicion, clave_resultado); gana la primera que se cumple.
Los resultados dicen el sistema, la causa probable, qué puede revisar uno mismo, la urgencia, las piezas
candidatas (patrones sobre el nombre visible de la pieza en el despiece) y el servicio del directorio.
"""
import re
import unicodedata

URGENCIAS = {
    "seguir": {"texto": "Puedes seguir rodando", "detalle": "No es peligroso, pero no lo dejes pasar."},
    "pronto": {"texto": "Revísalo pronto", "detalle": "Llévala al taller esta semana: si sigue, el daño crece."},
    "parar": {"texto": "No la ruedes", "detalle": "Es un riesgo para ti o para el motor. Llévala en grúa o pide revisión a domicilio."},
}

# Sistema del despiece → servicio del directorio de talleres (por nombre del Servicio en talleres)
SERVICIO_POR_SISTEMA = {
    "Frenos": "Frenos", "Ruedas": "Llantas", "Suspensión": "Suspensión", "Eléctrico": "Sistema eléctrico",
}
SERVICIO_GENERAL = "Mantenimiento general"

CADENA, CVT = {"t": "cadena"}, {"t": "cvt"}

SINTOMAS = {
    "ruido": {
        "nombre": "Ruido extraño", "icono": "ruido",
        "preguntas": [
            {"clave": "donde", "texto": "¿De dónde viene el ruido?", "opciones": [
                ("motor", "Del motor (cambia al acelerar)", None),
                ("arrastre", "De la cadena o la rueda trasera", CADENA),
                ("cvt", "Del lado izquierdo, donde va la correa", CVT),
                ("final", "De la rueda trasera, como engranajes", CVT),
                ("ruedas", "De las ruedas al rodar", None),
                ("frenar", "Al frenar", None),
                ("huecos", "Al pasar huecos o policías acostados", None),
                ("escape", "Del escape (petardeo o soplido)", None),
            ]},
            {"clave": "tipo", "texto": "¿Cómo suena?", "si": {"donde": ["motor"]}, "opciones": [
                ("tic", "Tic-tic metálico y parejo que sube con las revoluciones", None),
                ("traqueteo", "Traqueteo de cadena suelta, más fuerte en frío o al soltar el acelerador", None),
                ("golpe", "Golpe seco y hondo que empeora con carga", None),
            ]},
            {"clave": "tipo", "texto": "¿Cómo suena?", "si": {"donde": ["frenar"]}, "opciones": [
                ("chillido", "Chillido agudo", None),
                ("metal", "Raspado de metal contra metal", None),
            ]},
        ],
        "reglas": [
            ({"donde": "motor", "tipo": "tic"}, "valvulas"),
            ({"donde": "motor", "tipo": "traqueteo"}, "cadenilla"),
            ({"donde": "motor", "tipo": "golpe"}, "biela"),
            ({"donde": "arrastre"}, "kit_arrastre"),
            ({"donde": "cvt"}, "cvt_correa"),
            ({"donde": "final"}, "transmision_final"),
            ({"donde": "ruedas"}, "balineras_rueda"),
            ({"donde": "frenar", "tipo": "metal"}, "frenos_sin_pastilla"),
            ({"donde": "frenar"}, "frenos_chillan"),
            ({"donde": "huecos"}, "suspension"),
            ({"donde": "escape"}, "escape_fuga"),
        ],
    },
    "vibracion": {
        "nombre": "Vibra más de lo normal", "icono": "vibracion",
        "preguntas": [
            {"clave": "cuando", "texto": "¿Cuándo vibra?", "opciones": [
                ("velocidad", "Rodando, desde cierta velocidad", None),
                ("minimo", "Quieta, en mínimo", None),
                ("salir", "Al arrancar desde quieta (tiembla al salir)", CVT),
                ("frenar", "Al frenar (pulsa la manigueta o el pedal)", None),
                ("manubrio", "En el manubrio, sobre todo al frenar o en curvas", None),
            ]},
        ],
        "reglas": [
            ({"cuando": "velocidad"}, "rueda_desbalanceada"),
            ({"cuando": "minimo"}, "minimo_inestable"),
            ({"cuando": "salir"}, "cvt_clutch"),
            ({"cuando": "frenar"}, "disco_torcido"),
            ({"cuando": "manubrio"}, "direccion"),
        ],
    },
    "no_prende": {
        "nombre": "No prende", "icono": "llave",
        "preguntas": [
            {"clave": "arranque", "texto": "¿Qué pasa al darle arranque?", "opciones": [
                ("nada", "No hace nada o solo suena un clic", None),
                ("gira", "El motor gira pero no prende", None),
                ("lento", "Gira muy lento, como sin fuerza", None),
            ]},
            {"clave": "luces", "texto": "¿Prenden las luces del tablero y el pito?", "si": {"arranque": ["nada"]},
             "opciones": [("no", "No, o muy débiles", None), ("si", "Sí, normal", None)]},
        ],
        "reglas": [
            ({"arranque": "nada", "luces": "si"}, "arranque_electrico"),
            ({"arranque": ["nada", "lento"]}, "bateria"),
            ({"arranque": "gira"}, "sin_chispa_gasolina"),
        ],
    },
    "se_apaga": {
        "nombre": "Se apaga", "icono": "apaga",
        "preguntas": [
            {"clave": "cuando", "texto": "¿Cuándo se apaga?", "opciones": [
                ("minimo", "En mínimo o al frenar en un semáforo", None),
                ("frio", "Recién prendida, en frío", None),
                ("andando", "Andando, de repente", None),
                ("caliente", "Después de un rato, cuando está caliente", None),
            ]},
            {"clave": "radiador", "texto": "¿Tu moto tiene radiador (refrigeración líquida)?", "si": {"cuando": ["caliente"], "r": [""]},
             "opciones": [("si", "Sí", None), ("no", "No, es enfriada por aire", None)]},
        ],
        "reglas": [
            ({"cuando": "minimo"}, "minimo_inestable"),
            ({"cuando": "frio"}, "mezcla_frio"),
            ({"cuando": "andando"}, "corte_andando"),
            ({"cuando": "caliente", "r": "liquido"}, "recalienta_liquido"),
            ({"cuando": "caliente", "radiador": "si"}, "recalienta_liquido"),
            ({"cuando": "caliente"}, "recalienta_aire"),
        ],
    },
    "frena_mal": {
        "nombre": "Frena mal", "icono": "freno",
        "preguntas": [
            {"clave": "cual", "texto": "¿Cuál freno?", "opciones": [
                ("del", "El delantero", None), ("tras", "El trasero", None), ("ambos", "Los dos", None),
            ]},
            {"clave": "como", "texto": "¿Qué sientes?", "opciones": [
                ("esponjoso", "La manigueta o el pedal se hunde, esponjoso", None),
                ("poco", "Firme, pero frena poco", None),
                ("pegado", "Se queda frenado o la rueda se calienta", None),
                ("chilla", "Frena bien pero chilla", None),
            ]},
        ],
        "reglas": [
            ({"como": "esponjoso"}, "frenos_aire"),
            ({"como": "poco"}, "frenos_gastados"),
            ({"como": "pegado"}, "freno_pegado"),
            ({"como": "chilla"}, "frenos_chillan"),
        ],
    },
    "humo": {
        "nombre": "Sale humo", "icono": "humo",
        "preguntas": [
            {"clave": "color", "texto": "¿De qué color es y de dónde sale?", "opciones": [
                ("azul", "Azul o gris por el escape", None),
                ("negro", "Negro por el escape", None),
                ("blanco", "Blanco y espeso por el escape", None),
                ("motor", "Del motor, no del escape", None),
            ]},
            {"clave": "frio", "texto": "¿Se quita a los pocos minutos de prendida?", "si": {"color": ["blanco"]},
             "opciones": [("si", "Sí, solo al prenderla en frío", None), ("no", "No, sigue saliendo caliente", None)]},
            {"clave": "radiador", "texto": "¿Tu moto tiene radiador (refrigeración líquida)?", "si": {"color": ["blanco"], "frio": ["no"], "r": [""]},
             "opciones": [("si", "Sí", None), ("no", "No, es enfriada por aire", None)]},
        ],
        "reglas": [
            ({"color": "azul"}, "quema_aceite"),
            ({"color": "negro"}, "mezcla_rica"),
            ({"color": "blanco", "frio": "si"}, "condensacion"),
            ({"color": "blanco", "r": "liquido"}, "empaque_culata"),
            ({"color": "blanco", "radiador": "si"}, "empaque_culata"),
            ({"color": "blanco"}, "quema_aceite"),
            ({"color": "motor"}, "aceite_en_escape"),
        ],
    },
    "fuga": {
        "nombre": "Fuga o goteo", "icono": "gota",
        "preguntas": [
            {"clave": "que", "texto": "¿Qué gotea?", "opciones": [
                ("aceite", "Aceite: café o negro y espeso, debajo del motor", None),
                ("gasolina", "Gasolina: huele fuerte", None),
                ("refrigerante", "Refrigerante: verde o rosado, huele dulce", {"r": ["liquido", ""]}),
                ("frenos", "Líquido de frenos: claro o amarillento, cerca de una rueda o la manigueta", None),
                ("barras", "Aceite en las barras de la suspensión delantera", None),
                ("final", "Aceite cerca del eje de la rueda trasera", CVT),
            ]},
        ],
        "reglas": [
            ({"que": "aceite"}, "fuga_aceite"),
            ({"que": "gasolina"}, "fuga_gasolina"),
            ({"que": "refrigerante"}, "fuga_refrigerante"),
            ({"que": "frenos"}, "fuga_frenos"),
            ({"que": "barras"}, "retenedores_barras"),
            ({"que": "final"}, "transmision_final"),
        ],
    },
    "sin_fuerza": {
        "nombre": "Pierde fuerza", "icono": "fuerza",
        "preguntas": [
            {"clave": "como", "texto": "¿Cómo se nota?", "opciones": [
                ("patina", "El motor sube de vueltas pero la moto no avanza igual", None),
                ("lenta", "Acelera lento en todo momento", None),
                ("pesada", "Se siente frenada o pesada, como arrastrando algo", None),
            ]},
        ],
        "reglas": [
            ({"como": "patina", "t": "cvt"}, "cvt_correa"),
            ({"como": "patina"}, "clutch_patina"),
            ({"como": "lenta"}, "admision_sucia"),
            ({"como": "pesada"}, "freno_pegado"),
        ],
    },
    "electrico": {
        "nombre": "Luces o eléctrico", "icono": "rayo",
        "preguntas": [
            {"clave": "que", "texto": "¿Qué notas?", "opciones": [
                ("debiles", "Las luces bajan o parpadean con las revoluciones", None),
                ("una", "Una luz no prende (farola, stop o direccional)", None),
                ("descarga", "La batería se descarga sola", None),
                ("tablero", "El tablero, el pito o un mando no funciona", None),
            ]},
        ],
        "reglas": [
            ({"que": "debiles"}, "carga"),
            ({"que": "una"}, "bombillo"),
            ({"que": "descarga"}, "bateria"),
            ({"que": "tablero"}, "fusible_mando"),
        ],
    },
    "cambios": {
        "nombre": "Cambios o clutch", "icono": "cambios", "solo": CADENA,
        "preguntas": [
            {"clave": "que", "texto": "¿Qué pasa?", "opciones": [
                ("duro", "Cuesta meter los cambios o suenan al entrar", None),
                ("salen", "Los cambios se salen solos", None),
                ("patina", "El clutch patina: sube de vueltas y no avanza", None),
                ("arrastra", "Con el clutch apretado la moto se quiere ir", None),
                ("neutro", "No encuentra el neutro", None),
            ]},
        ],
        "reglas": [
            ({"que": "duro"}, "clutch_ajuste"),
            ({"que": "salen"}, "caja_desgaste"),
            ({"que": "patina"}, "clutch_patina"),
            ({"que": "arrastra"}, "clutch_no_suelta"),
            ({"que": "neutro"}, "clutch_ajuste"),
        ],
    },
    "cvt": {
        "nombre": "Transmisión CVT", "icono": "cambios", "solo": CVT,
        "preguntas": [
            {"clave": "que", "texto": "¿Qué pasa?", "opciones": [
                ("tiembla", "Tiembla o vibra al arrancar desde quieta", None),
                ("lenta", "Acelera pero sale lenta o no llega a su velocidad", None),
                ("ruido", "Chilla o zumba del lado izquierdo", None),
                ("sola", "En mínimo, la rueda trasera gira o se quiere ir", None),
            ]},
        ],
        "reglas": [
            ({"que": "tiembla"}, "cvt_clutch"),
            ({"que": "lenta"}, "cvt_correa"),
            ({"que": "ruido"}, "cvt_correa"),
            ({"que": "sola"}, "cvt_se_va"),
        ],
    },
}

RESULTADOS = {
    # ---------- Motor ----------
    "valvulas": {
        "sistema": "Motor", "subgrupo": "Válvulas y distribución", "urgencia": "pronto",
        "causa": "Válvulas descalibradas",
        "explicacion": "El tic parejo que sube con las revoluciones suele ser holgura de más entre el balancín y la válvula. "
                       "Se calibra con galgas; si se deja, se gastan el árbol de levas y los balancines.",
        "piezas": [r"v[aá]lvula de (admisi|escape)", r"balanc[ií]n", r"taqu[eé]", r"[aá]rbol de levas", r"tornillo de ajuste", r"v[aá]lvula"],
        "excluir": r"tapa|empaque|sello|gu[ií]a|resorte|cu[nñ]a|platillo|base",
    },
    "cadenilla": {
        "sistema": "Motor", "subgrupo": "Válvulas y distribución", "urgencia": "pronto",
        "causa": "Cadenilla de distribución estirada o tensor gastado",
        "explicacion": "La cadenilla mueve el árbol de levas. Si el tensor ya no la recoge, golpea contra sus guías; "
                       "si salta un diente, las válvulas chocan con el pistón.",
        "piezas": [r"cadenilla", r"tensor de (la )?cadenilla", r"tensor", r"gu[ií]a de (la )?cadenilla", r"pat[ií]n"],
    },
    "biela": {
        "sistema": "Motor", "subgrupo": "Cárter y tapas", "urgencia": "parar",
        "causa": "Desgaste interno: biela o balineras del cigüeñal",
        "explicacion": "Un golpe hondo que crece con la carga viene de abajo del motor. Seguir rodando puede partir la biela "
                       "y dañar el bloque. Revisa primero el nivel de aceite.",
        "revisa": "El nivel de aceite en la mirilla o la varilla.",
        "piezas": [r"biela", r"cig[uü]e[nñ]al", r"balinera", r"rodamiento"],
        "otros_sistemas": ["Lubricación"],
    },
    "quema_aceite": {
        "sistema": "Motor", "subgrupo": "Cilindro y pistón", "urgencia": "pronto",
        "causa": "Quema aceite: anillos, cilindro o sellos de válvula",
        "explicacion": "El humo azul es aceite que entra a la cámara: por anillos gastados (más al acelerar) o por los sellos "
                       "de las válvulas (más al soltar el acelerador o al prender). Vigila el nivel de aceite seguido.",
        "revisa": "El nivel de aceite cada dos o tres días.",
        "piezas": [r"anillo", r"pist[oó]n", r"cilindro", r"sello de v[aá]lvula", r"retenedor de v[aá]lvula", r"gu[ií]a de v[aá]lvula"],
    },
    "empaque_culata": {
        "sistema": "Refrigeración", "urgencia": "parar",
        "causa": "Empaque de culata: el refrigerante pasa a la cámara",
        "explicacion": "Humo blanco espeso con el motor caliente, y el refrigerante que baja sin fuga a la vista, apuntan al "
                       "empaque de la culata. Rodando así se recalienta y se puede torcer la culata.",
        "revisa": "El nivel del depósito de refrigerante con el motor frío.",
        "piezas": [r"empaque de (la )?culata", r"culata", r"refrigerante", r"radiador", r"termostato"],
        "otros_sistemas": ["Motor"],
    },
    # ---------- Lubricación ----------
    "fuga_aceite": {
        "sistema": "Lubricación", "urgencia": "pronto",
        "causa": "Empaque, retenedor o tapón del motor que bota aceite",
        "explicacion": "Limpia la zona y mira de dónde sale: tapón de drenaje, tapas laterales, base del cilindro o el retenedor "
                       "del piñón de salida. Con poco aceite el motor se funde.",
        "revisa": "El nivel de aceite antes de cada salida.",
        "piezas": [r"empaque", r"retenedor", r"tap[oó]n", r"o-?ring", r"anillo de caucho", r"filtro de aceite"],
        "otros_sistemas": ["Motor"],
    },
    "aceite_en_escape": {
        "sistema": "Lubricación", "urgencia": "pronto",
        "causa": "Aceite que cae sobre el motor o el escape caliente",
        "explicacion": "Humo que sale del motor y no del escape suele ser aceite quemándose sobre una pieza caliente. "
                       "Busca la fuga: tapa de válvulas, base del cilindro o el filtro de aceite.",
        "piezas": [r"empaque", r"retenedor", r"tapa", r"filtro de aceite", r"o-?ring"],
        "otros_sistemas": ["Motor"],
    },
    "recalienta_aire": {
        "sistema": "Lubricación", "urgencia": "parar",
        "causa": "Se recalienta: aceite bajo o viejo",
        "explicacion": "En un motor enfriado por aire, el aceite es lo que más saca el calor. Si está bajo o vencido el motor "
                       "se recalienta y se apaga; seguir puede pegar el pistón.",
        "revisa": "El nivel y el color del aceite, con el motor frío.",
        "piezas": [r"aceite", r"filtro de aceite", r"bomba de aceite", r"colador", r"enfriador"],
        "servicio": "Cambio de aceite",
    },
    # ---------- Refrigeración ----------
    "recalienta_liquido": {
        "sistema": "Refrigeración", "urgencia": "parar",
        "causa": "Se recalienta: refrigerante bajo, ventilador o termostato",
        "explicacion": "Si la temperatura sube y se apaga, el líquido no está sacando el calor: falta refrigerante, el "
                       "ventilador no prende o el termostato no abre. Seguir rodando puede torcer la culata.",
        "revisa": "El depósito de refrigerante (con el motor frío) y si el ventilador prende cuando calienta.",
        "piezas": [r"radiador", r"termostato", r"ventilador", r"bomba de agua", r"refrigerante", r"manguera", r"tapa del radiador"],
    },
    "fuga_refrigerante": {
        "sistema": "Refrigeración", "urgencia": "pronto",
        "causa": "Fuga de refrigerante: manguera, radiador o sello de la bomba de agua",
        "explicacion": "Busca humedad en las mangueras y abrazaderas, el radiador y el agujerito de la bomba de agua (si gotea "
                       "ahí, es su sello). Si la temperatura sube, no la ruedes.",
        "revisa": "El nivel del depósito con el motor frío.",
        "piezas": [r"manguera", r"radiador", r"bomba de agua", r"sello", r"tapa del radiador", r"abrazadera"],
    },
    # ---------- Admisión ----------
    "minimo_inestable": {
        "sistema": "Admisión", "urgencia": "seguir",
        "causa": "Mínimo bajo o inestable: filtro de aire, carburación o cuerpo de aceleración sucio",
        "explicacion": "Un filtro de aire tapado, el carburador o el cuerpo de aceleración sucios o el mínimo mal calibrado "
                       "hacen que el motor tiemble o se apague quieto. Suele arreglarse con limpieza y sincronización.",
        "excluir": r"pata|velocidad",
        "piezas": [r"filtro de aire", r"carburador", r"cuerpo de aceleraci[oó]n", r"tornillo de m[ií]nimo", r"chicler", r"inyector", r"sensor"],
        "otros_sistemas": ["Eléctrico"],
    },
    "mezcla_frio": {
        "sistema": "Admisión", "urgencia": "seguir",
        "causa": "Le falta mezcla en frío: choque, carburación o sensor de temperatura",
        "explicacion": "En frío el motor pide más gasolina. Si tiene choque y no lo usas, o el carburador está sucio, o en las "
                       "de inyección falla el sensor de temperatura, se apaga hasta que calienta.",
        "excluir": r"pata|velocidad",
        "piezas": [r"choque", r"starter", r"carburador", r"sensor", r"cuerpo de aceleraci[oó]n", r"filtro de aire"],
    },
    "mezcla_rica": {
        "sistema": "Admisión", "urgencia": "pronto",
        "causa": "Mezcla rica: filtro de aire tapado o carburación",
        "explicacion": "El humo negro es gasolina que no alcanza a quemarse. Lo típico: filtro de aire tapado, choque pegado, "
                       "aguja o chicler gastados, o un inyector que gotea. Gasta más y ensucia la bujía.",
        "excluir": r"pata|velocidad",
        "piezas": [r"filtro de aire", r"carburador", r"chicler", r"aguja", r"inyector", r"choque", r"sensor"],
    },
    "admision_sucia": {
        "sistema": "Admisión", "urgencia": "pronto",
        "causa": "Le falta aire, gasolina o chispa: filtros, bujía o inyección",
        "explicacion": "Si acelera lento en todo, revisa lo que respira y lo que quema: filtro de aire, filtro de gasolina, "
                       "bujía y carburador o inyector. También un escape tapado le quita fuerza.",
        "piezas": [r"filtro de aire", r"buj[ií]a", r"filtro de gasolina", r"inyector", r"carburador", r"silenciador"],
        "otros_sistemas": ["Eléctrico", "Escape"],
    },
    "fuga_gasolina": {
        "sistema": "Admisión", "urgencia": "parar",
        "causa": "Fuga de gasolina: manguera, carburador o inyector",
        "explicacion": "La gasolina sobre un motor caliente puede prenderse. No la prendas: revisa mangueras, abrazaderas, la "
                       "llave de paso, la cuba del carburador o el inyector.",
        "piezas": [r"manguera", r"carburador", r"inyector", r"llave de (paso|gasolina)", r"bomba de gasolina", r"filtro de gasolina", r"tanque"],
    },
    # ---------- Escape ----------
    "escape_fuga": {
        "sistema": "Escape", "urgencia": "pronto",
        "causa": "Fuga en el escape: empaque del múltiple o tubo roto",
        "explicacion": "Un soplido o petardeo cerca del motor suele ser el empaque de la salida del escape. Además del ruido, "
                       "deja entrar aire y el motor trabaja mal.",
        "piezas": [r"empaque", r"exosto", r"silenciador", r"tubo", r"abrazadera", r"protector"],
    },
    "condensacion": {
        "sistema": "Escape", "urgencia": "seguir",
        "causa": "Vapor normal del escape en frío",
        "explicacion": "Al prender en frío o con humedad, el agua que se condensa en el escape sale como vapor blanco y se "
                       "quita en pocos minutos. Es normal.",
        "piezas": [],
    },
    # ---------- Caja de cambios y clutch (de cambios) ----------
    "clutch_patina": {
        "sistema": "Caja de cambios y clutch", "subgrupo": "Clutch", "urgencia": "pronto",
        "causa": "Clutch patinando: discos gastados, resortes vencidos o cable sin juego",
        "explicacion": "Si sube de vueltas y no empuja, los discos de fricción ya no agarran. Primero se revisa el juego del "
                       "cable; si está bien, toca cambiar discos y resortes. Un aceite que no es para moto también lo hace patinar.",
        "revisa": "Que la manigueta del clutch tenga 10 a 20 mm de juego libre.",
        "piezas": [r"disco", r"separador", r"resorte", r"plato", r"cable del clutch", r"canasta", r"centro"],
    },
    "clutch_no_suelta": {
        "sistema": "Caja de cambios y clutch", "subgrupo": "Clutch", "urgencia": "pronto",
        "causa": "El clutch no suelta: cable muy flojo o discos pegados",
        "explicacion": "Si con el clutch apretado la moto se quiere ir, el clutch no se está abriendo del todo: cable con mucho "
                       "juego, discos torcidos o el levantador gastado. Cuesta meter primera y se calienta.",
        "revisa": "El juego del cable del clutch.",
        "piezas": [r"cable del clutch", r"disco", r"separador", r"varilla", r"levantador", r"plato"],
    },
    "clutch_ajuste": {
        "sistema": "Caja de cambios y clutch", "subgrupo": "Clutch", "urgencia": "seguir",
        "causa": "Clutch mal ajustado o aceite vencido",
        "explicacion": "Cambios duros o un neutro difícil casi siempre son el juego del cable del clutch o un aceite viejo. "
                       "Si sigue igual después de ajustar y cambiar aceite, se revisa el selector de la caja.",
        "revisa": "El juego del cable y cuándo fue el último cambio de aceite.",
        "piezas": [r"cable del clutch", r"palanca", r"disco", r"selector", r"tambor"],
        "otros_sistemas": ["Lubricación"],
    },
    "caja_desgaste": {
        "sistema": "Caja de cambios y clutch", "subgrupo": "Caja de cambios", "urgencia": "pronto",
        "causa": "Caja de cambios gastada: horquillas o dientes de enganche de los piñones",
        "explicacion": "Si un cambio se sale con carga, los dientes laterales de los piñones o las horquillas están gastados. "
                       "Cada vez que salta se gastan más; no aceleres a fondo en ese cambio.",
        "piezas": [r"horquilla", r"tambor", r"pi[nñ][oó]n", r"eje", r"selector", r"resorte"],
    },
    # ---------- Kit de arrastre (de cambios) ----------
    "kit_arrastre": {
        "sistema": "Kit de arrastre", "urgencia": "pronto",
        "causa": "Cadena floja, seca o kit de arrastre gastado",
        "explicacion": "Una cadena que golpea o chasquea está floja, seca o estirada. Si los dientes del sprocket están en "
                       "punta, se cambia el kit completo (cadena, piñón y sprocket). Una cadena muy floja se puede salir.",
        "revisa": "Que la cadena tenga 2 a 3 cm de juego y esté lubricada.",
        "piezas": [r"cadena", r"pi[nñ][oó]n", r"sprocket", r"corona", r"tensor", r"gu[ií]a", r"deslizador"],
    },
    # ---------- Transmisión CVT y final (automáticas) ----------
    "cvt_correa": {
        "sistema": "Transmisión CVT", "urgencia": "pronto",
        "causa": "Correa gastada o rodillos planos",
        "explicacion": "La correa se angosta con el uso y los rodillos se aplanan: la moto sube de vueltas y no corre, o chilla. "
                       "Se cambian por kilometraje; si la correa se revienta, la moto se queda.",
        "piezas": [r"correa", r"rodillo", r"polea", r"resorte", r"clutch", r"campana", r"filtro"],
    },
    "cvt_clutch": {
        "sistema": "Transmisión CVT", "urgencia": "pronto",
        "causa": "Clutch centrífugo o campana gastados",
        "explicacion": "El temblor al salir viene de las zapatas del clutch centrífugo o de la campana con huellas. "
                       "Se limpia o se cambia el conjunto.",
        "piezas": [r"zapata", r"campana", r"clutch", r"resorte", r"polea"],
    },
    "cvt_se_va": {
        "sistema": "Transmisión CVT", "urgencia": "parar",
        "causa": "Mínimo muy alto o resortes del clutch centrífugo vencidos",
        "explicacion": "Si la rueda trasera gira en mínimo, el clutch centrífugo está agarrando antes de tiempo. Es peligroso "
                       "en un semáforo: baja el mínimo o cambia los resortes del clutch.",
        "piezas": [r"resorte", r"zapata", r"clutch", r"campana", r"tornillo de m[ií]nimo"],
        "otros_sistemas": ["Admisión"],
    },
    "transmision_final": {
        "sistema": "Transmisión final", "urgencia": "pronto",
        "causa": "Aceite de la transmisión final bajo o vencido, o retenedor que bota",
        "explicacion": "La caja de la rueda trasera lleva su propio aceite. Si zumba o gotea, revisa el nivel y el retenedor "
                       "del eje; sin aceite los engranajes se gastan rápido.",
        "piezas": [r"aceite", r"retenedor", r"engranaje", r"pi[nñ][oó]n", r"eje", r"empaque", r"balinera"],
    },
    # ---------- Frenos ----------
    "frenos_aire": {
        "sistema": "Frenos", "subgrupo": "Bomba y líquido", "urgencia": "parar",
        "causa": "Aire o líquido de frenos vencido, o fuga",
        "explicacion": "Una manigueta esponjosa en freno de disco es aire en el sistema, líquido viejo o una fuga en mangueras "
                       "o caliper. En freno de tambor, es el cable o la varilla estirados, o bandas gastadas.",
        "revisa": "El nivel del depósito del líquido de frenos.",
        "piezas": [r"bomba", r"l[ií]quido", r"manguera", r"caliper", r"pist[oó]n", r"retenedor", r"cable", r"varilla"],
    },
    "frenos_gastados": {
        "sistema": "Frenos", "urgencia": "parar",
        "causa": "Pastillas o bandas gastadas o cristalizadas",
        "explicacion": "Si el freno se siente firme pero no detiene, el material de fricción se acabó o se cristalizó. "
                       "Es lo primero que se revisa: se cambia barato y es tu seguridad.",
        "piezas": [r"pastilla", r"banda", r"zapata", r"disco", r"campana"],
    },
    "frenos_sin_pastilla": {
        "sistema": "Frenos", "urgencia": "parar",
        "causa": "Pastillas acabadas: metal contra el disco",
        "explicacion": "El raspado metálico es la base de la pastilla rozando el disco. Ya casi no frena y cada kilómetro "
                       "raya más el disco.",
        "piezas": [r"pastilla", r"disco", r"banda", r"campana", r"caliper"],
    },
    "frenos_chillan": {
        "sistema": "Frenos", "urgencia": "pronto",
        "causa": "Pastillas cristalizadas, sucias o al límite",
        "explicacion": "El chillido suele ser polvo, pastillas cristalizadas o el aviso de desgaste. Se limpia, se lijan o "
                       "se cambian; revisa también el disco.",
        "piezas": [r"pastilla", r"banda", r"disco", r"campana", r"caliper"],
    },
    "freno_pegado": {
        "sistema": "Frenos", "urgencia": "parar",
        "causa": "Freno pegado: pistón del caliper, pasadores o cable",
        "explicacion": "Si la rueda se calienta o la moto se siente frenada, un pistón o los pasadores del caliper están "
                       "pegados, o el cable del freno trasero no regresa. Se recalienta y deja de frenar. En las de cambios, "
                       "revisa también que la cadena no esté demasiado tensa.",
        "piezas": [r"caliper", r"pist[oó]n", r"pasador", r"retenedor", r"cable", r"leva", r"resorte"],
    },
    "disco_torcido": {
        "sistema": "Frenos", "urgencia": "pronto",
        "causa": "Disco torcido o con desgaste disparejo",
        "explicacion": "Si la manigueta pulsa al frenar, el disco está alabeado (por calor o un golpe) o la campana ovalada. "
                       "Se mide y, si está fuera de límite, se cambia junto con las pastillas.",
        "piezas": [r"disco", r"pastilla", r"campana", r"banda"],
    },
    "fuga_frenos": {
        "sistema": "Frenos", "subgrupo": "Bomba y líquido", "urgencia": "parar",
        "causa": "Fuga de líquido de frenos",
        "explicacion": "Sin líquido el freno se va. Revisa la bomba de la manigueta, las mangueras y sus tornillos huecos, "
                       "y el caliper. Además, el líquido daña la pintura.",
        "piezas": [r"bomba", r"manguera", r"caliper", r"retenedor", r"pist[oó]n", r"tornillo hueco"],
    },
    # ---------- Ruedas ----------
    "balineras_rueda": {
        "sistema": "Ruedas", "urgencia": "pronto",
        "causa": "Balineras de la rueda gastadas",
        "explicacion": "Un zumbido o rumor que cambia con la velocidad (y no con el motor) suele ser una balinera de rueda. "
                       "Con la moto en el gato, mueve la rueda hacia los lados: si tiene juego, hay que cambiarla.",
        "piezas": [r"balinera", r"rodamiento", r"eje", r"separador", r"retenedor"],
        "servicio": SERVICIO_GENERAL,
    },
    "rueda_desbalanceada": {
        "sistema": "Ruedas", "urgencia": "pronto",
        "causa": "Llanta desbalanceada o deformada, rin torcido o balineras",
        "explicacion": "La vibración que aparece desde cierta velocidad viene casi siempre de las ruedas: presión baja, "
                       "llanta deformada, rin torcido o balineras gastadas.",
        "revisa": "La presión de las llantas y si tienen chichones o desgaste disparejo.",
        "piezas": [r"llanta", r"rin", r"balinera", r"eje", r"neum[aá]tico"],
    },
    # ---------- Suspensión ----------
    "suspension": {
        "sistema": "Suspensión", "urgencia": "pronto",
        "causa": "Suspensión gastada: retenedores, bujes o amortiguador",
        "explicacion": "Golpes secos en los huecos suelen ser bujes de la tijera, retenedores sin aceite en las barras o un "
                       "amortiguador que ya no frena el rebote.",
        "piezas": [r"retenedor", r"buje", r"amortiguador", r"barra", r"basculante", r"tijera", r"guardapolvo"],
    },
    "retenedores_barras": {
        "sistema": "Suspensión", "subgrupo": "Delantera y dirección", "urgencia": "pronto",
        "causa": "Retenedores de las barras delanteras",
        "explicacion": "El aceite en la barra viene del retenedor. Si cae al disco, el freno delantero pierde agarre: "
                       "límpialo y llévala pronto.",
        "piezas": [r"retenedor", r"guardapolvo", r"barra", r"buje", r"aceite"],
    },
    "direccion": {
        "sistema": "Suspensión", "subgrupo": "Delantera y dirección", "urgencia": "pronto",
        "causa": "Balineras de la dirección o barras",
        "explicacion": "Si el manubrio vibra o da golpecitos al frenar, las balineras de la dirección están flojas o "
                       "picadas. Con la rueda en el aire, el manubrio no debe quedarse 'trabado' en el centro.",
        "piezas": [r"balinera", r"cuna", r"rodamiento", r"barra", r"tuerca de (la )?direcci[oó]n"],
    },
    # ---------- Eléctrico ----------
    "bateria": {
        "sistema": "Eléctrico", "subgrupo": "Batería y sistema eléctrico", "urgencia": "pronto",
        "causa": "Batería descargada o gastada, o un borne suelto",
        "explicacion": "Sin fuerza en el arranque, lo primero es la batería: bornes sueltos o sulfatados, o una batería que "
                       "ya no retiene carga. Si se descarga seguido, revisa también el regulador.",
        "revisa": "Que los bornes estén apretados y limpios.",
        "piezas": [r"bater[ií]a", r"borne", r"fusible", r"rel[eé]", r"regulador"],
    },
    "arranque_electrico": {
        "sistema": "Eléctrico", "subgrupo": "Arranque", "urgencia": "pronto",
        "causa": "Motor de arranque, relé o un interruptor de seguridad",
        "explicacion": "Si hay luces pero no arranca, revisa que esté en neutro, el clutch apretado y la pata lateral arriba "
                       "(tienen interruptor). Si todo está bien, falla el relé o el motor de arranque.",
        "revisa": "Neutro, clutch o freno apretado y pata lateral arriba.",
        "piezas": [r"motor de arranque", r"rel[eé]", r"interruptor (del clutch|de (la )?pata|de neutro|de arranque)", r"bendix", r"escobilla", r"fusible"],
    },
    "sin_chispa_gasolina": {
        "sistema": "Eléctrico", "subgrupo": "Encendido y bujías", "urgencia": "pronto",
        "causa": "Le falta chispa o gasolina: bujía, bobina o bomba",
        "explicacion": "Si el motor gira pero no prende, falta chispa (bujía, capuchón, bobina, CDI o ECU) o falta gasolina "
                       "(tanque, llave de paso, bomba o inyector). La bujía es lo primero.",
        "revisa": "Que haya gasolina y el interruptor de apagado esté en marcha.",
        "piezas": [r"buj[ií]a", r"bobina", r"capuch[oó]n", r"cdi", r"ecu", r"bomba de gasolina", r"inyector", r"carburador"],
        "otros_sistemas": ["Admisión"],
    },
    "corte_andando": {
        "sistema": "Eléctrico", "urgencia": "parar",
        "causa": "Corte eléctrico o de gasolina: conector, bobina o bomba",
        "explicacion": "Apagarse andando es peligroso en el tráfico. Suele ser un conector flojo, el interruptor de apagado, "
                       "la bobina o el CDI calientes, o la bomba o el filtro de gasolina.",
        "piezas": [r"bobina", r"cdi", r"ecu", r"conector", r"interruptor (de apagado|de parada|de encendido)", r"bomba de gasolina", r"filtro de gasolina", r"rel[eé]"],
        "otros_sistemas": ["Admisión"],
    },
    "carga": {
        "sistema": "Eléctrico", "subgrupo": "Batería y sistema eléctrico", "urgencia": "pronto",
        "causa": "No está cargando bien: regulador, estator o batería",
        "explicacion": "Luces que bajan o parpadean con las revoluciones indican que el regulador o el estator no cargan "
                       "parejo. Si no se arregla, la batería se agota y la moto se apaga.",
        "piezas": [r"regulador", r"rectificador", r"estator", r"bobina de carga", r"bater[ií]a", r"magneto"],
    },
    "bombillo": {
        "sistema": "Eléctrico", "subgrupo": "Batería y sistema eléctrico", "urgencia": "pronto",
        "causa": "Bombillo fundido, fusible o conector",
        "explicacion": "Casi siempre es el bombillo o un conector sulfatado; si no prende nada de ese circuito, el fusible. "
                       "Sin farola, stop o direccionales no es seguro rodar y es causa de multa.",
        "piezas": [r"bombillo", r"farola", r"faro", r"stop", r"direccional", r"fusible", r"conector"],
    },
    "fusible_mando": {
        "sistema": "Eléctrico", "subgrupo": "Batería y sistema eléctrico", "urgencia": "seguir",
        "causa": "Fusible, conector o mando del manubrio",
        "explicacion": "Revisa el fusible del circuito y los conectores del mando. Los mandos se llenan de mugre y humedad.",
        "piezas": [r"fusible", r"mando", r"interruptor del manubrio", r"pito", r"conector", r"tablero", r"veloc[ií]metro"],
    },
}


# ---------------- Lógica ----------------

def _cumple(condicion, respuestas):
    for clave, valor in (condicion or {}).items():
        valores = valor if isinstance(valor, (list, tuple)) else [valor]
        if respuestas.get(clave, "") not in valores:
            return False
    return True


def sintomas_para(transmision):
    """Síntomas que aplican a una transmisión ("cadena" o "cvt")."""
    contexto = {"t": transmision}
    return [(clave, s) for clave, s in SINTOMAS.items() if _cumple(s.get("solo"), contexto)]


def preguntas_visibles(sintoma, contexto):
    """Preguntas (con sus opciones filtradas) que tocan con las respuestas dadas hasta ahora.

    contexto = respuestas + "t" (transmisión) + "r" (refrigeración). Se piden en orden: devuelve la lista completa de
    las que aplican; la vista pregunta la primera que falte."""
    visibles = []
    for p in SINTOMAS[sintoma]["preguntas"]:
        if not _cumple(p.get("si"), contexto):
            continue
        opciones = [(v, t) for v, t, cond in p["opciones"] if _cumple(cond, contexto)]
        if opciones:
            visibles.append({"clave": p["clave"], "texto": p["texto"], "opciones": opciones})
    return visibles


def resultado(sintoma, contexto):
    """Clave del resultado, o None si faltan respuestas."""
    for p in preguntas_visibles(sintoma, contexto):
        if contexto.get(p["clave"]) not in {v for v, _ in p["opciones"]}:
            return None
    for condicion, clave in SINTOMAS[sintoma]["reglas"]:
        if _cumple(condicion, contexto):
            return clave
    return None


def subgrupo_freno(contexto):
    return {"del": "Delantero", "tras": "Trasero"}.get(contexto.get("cual"), "")


def servicio_de(clave):
    r = RESULTADOS[clave]
    return r.get("servicio") or SERVICIO_POR_SISTEMA.get(r["sistema"], SERVICIO_GENERAL)


def _plano(texto):
    texto = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    return texto


HERRAJES = re.compile(r"^(tornillo|tuerca|arandela|perno|remache|grapa|clip|pasador|abrazadera|pin)\b", re.I)
# Accesorios que no causan la falla (soportes, tirantes, cajas, protectores): solo si el patrón los nombra al inicio
ACCESORIOS = re.compile(r"^(tirante|banda|soporte|rejilla|protector|caja de (la )?bater[ií]a|caja del filtro|tapa de la caja|cubierta)\b", re.I)


def piezas_candidatas(clave, laminas, subgrupo="", limite=8):
    """Piezas del despiece de la moto (datos_despiece()['laminas']) que encajan con el resultado.

    Busca en las láminas del sistema del resultado (y sus sistemas vecinos), por orden de los patrones: el primero
    es la pieza más probable. La tornillería solo entra si el patrón la nombra al principio."""
    r = RESULTADOS[clave]
    sistemas = [r["sistema"]] + r.get("otros_sistemas", [])
    patrones = [re.compile(_plano(p), re.I) for p in r.get("piezas", [])]
    excluir = re.compile(_plano(r["excluir"]), re.I) if r.get("excluir") else None
    vistos, salida = set(), []
    for i_patron, patron in enumerate(patrones):
        for i_sis, sistema in enumerate(sistemas):
            for lamina in laminas:
                if lamina.get("sistema") != sistema:
                    continue
                if subgrupo and lamina.get("subgrupo") and lamina["subgrupo"] != subgrupo and sistema == "Frenos":
                    continue
                for parte in lamina.get("partes", []):
                    nombre = parte.get("nombre") or ""
                    plano = _plano(nombre)
                    m = patron.search(plano)
                    if not m or ((HERRAJES.match(plano) or ACCESORIOS.match(plano)) and m.start() > 0):
                        continue
                    if (excluir and excluir.search(plano)) or plano in vistos:
                        continue
                    vistos.add(plano)
                    salida.append({"id": parte["id"], "nombre": nombre, "lamina": lamina["nombre"],
                                   "estado": parte.get("estado"), "orden": (i_sis, m.start() > 0, i_patron)})
                    if len(salida) >= limite * 3:
                        break
    salida.sort(key=lambda p: p["orden"])
    return salida[:limite]
