"""Guías de las piezas del despiece: qué hacen, cada cuánto revisarlas, señales de falla y consejos.

Escritas para motociclistas: lenguaje sencillo, sin tecnicismos innecesarios. Los intervalos son
orientativos; cuando la pieza está en el plan de mantenimiento se muestran los de ese plan.

ficha_para(descripcion, pieza) → dict con: que_hace, cada_cuanto, senales, tips, dificultad, dificultad_texto.
"""
import re

# Dificultad: "facil" (lo puedes hacer tú), "media" (con herramienta y algo de práctica), "taller".
DIFICULTAD = {
    "facil": "Lo puedes hacer tú",
    "media": "Con herramienta y algo de práctica",
    "taller": "Mejor en el taller",
}


def _f(que_hace, cada_cuanto, senales, tips, dificultad, nota=""):
    return {"que_hace": que_hace, "cada_cuanto": cada_cuanto, "senales": senales, "tips": tips,
            "dificultad": dificultad, "dificultad_texto": nota or DIFICULTAD[dificultad]}


# Guías por pieza (clave = descripción normalizada del catálogo; se busca la coincidencia más larga).
FICHAS = {
    # ---------------- Frenos ----------------
    "BRAKE PAD KIT": _f(
        "Son las piezas que aprietan el disco para frenar. Tienen un material de fricción que se va gastando con cada frenada.",
        "Revísalas cada 3.000 km y cámbialas cuando les queden unos 2 mm de material. En ciudad, con mucho pare y arranque, se gastan más rápido.",
        ["Chillido metálico al frenar", "La manigueta llega más cerca del puño", "La moto tarda más en detenerse", "Rayas profundas en el disco"],
        ["Cambia siempre el juego completo, nunca una sola pastilla", "Después de cambiarlas, frena suave los primeros 100 km para que asienten",
         "Si llegan al metal dañan el disco y la reparación sale mucho más cara", "Prefiere repuesto original o de marca reconocida"],
        "media", "Con herramienta básica; si no estás seguro, mejor en el taller"),
    "DISK, BRAKE": _f(
        "Es el disco que gira con la rueda. Las pastillas lo aprietan y así la moto frena.",
        "Revisa su grosor cada vez que cambies pastillas. Se cambia cuando llega al grosor mínimo marcado en el disco o si está torcido.",
        ["Vibración en la manigueta al frenar", "Ruido de roce constante", "Surcos profundos o color azulado por recalentamiento"],
        ["No lo toques con grasa ni con los dedos sucios: pierde frenado", "Si cambias el disco, cambia también las pastillas",
         "Lávalo solo con agua y jabón o limpiador de frenos"],
        "taller"),
    "CALIPER ASSY": _f(
        "Es la pinza que sostiene las pastillas. Cuando frenas, el líquido empuja su pistón y las pastillas aprietan el disco.",
        "Límpialo en cada cambio de pastillas. Revisa que el pistón no esté pegado ni tenga fugas.",
        ["La moto se va hacia un lado al frenar", "Una pastilla se gasta mucho más que la otra", "La rueda queda frenada o caliente después de rodar", "Manchas de líquido alrededor"],
        ["Mantenlo limpio de barro: la suciedad hace que el pistón se pegue", "Si ves fugas, no sigas rodando: el freno puede fallar"],
        "taller"),
    "PISTON ASSY, CALIPER": _f(
        "Es el émbolo dentro del caliper que empuja las pastillas cuando aprietas el freno.",
        "Se revisa al limpiar el caliper. Se cambia si está rayado, oxidado o pegado.",
        ["Freno que no suelta del todo", "Fugas de líquido por el caliper"],
        ["Se cambia junto con los empaques del caliper"], "taller"),
    "CALIPER SEAL KIT": _f(
        "Son los empaques que evitan que el líquido de frenos se salga del caliper y ayudan a que el pistón regrese.",
        "Cada vez que se repara o se limpia a fondo el caliper, o si hay fugas.",
        ["Fugas de líquido", "El freno queda pegado"], ["Siempre se cambian todos los del kit a la vez"], "taller"),
    "BLEED SCREW KIT": _f(
        "Es el tornillo por donde se saca el aire y el líquido viejo del sistema de frenos.",
        "Se usa en cada cambio de líquido de frenos (cada 2 años aprox.).",
        ["Freno esponjoso o que se va al fondo (puede haber aire en el sistema)"],
        ["Mantén su tapita de caucho puesta para que no entre mugre", "No lo aprietes de más: se puede romper"], "taller"),
    "MASTER CYLINDER ASSY": _f(
        "Es la bomba del freno: cuando aprietas la manigueta, empuja el líquido hacia el caliper.",
        "Revisa el nivel de líquido cada semana por la mirilla. El líquido se cambia cada 2 años.",
        ["Manigueta esponjosa o que se va al fondo", "Fugas en la manigueta o en el depósito", "El nivel de líquido baja sin razón"],
        ["Si el nivel baja mucho, revisa las pastillas: al gastarse, el nivel baja", "No mezcles tipos de líquido (DOT 4 con DOT 5)"],
        "taller"),
    "RR. MASTER CYLINDER ASSY": _f(
        "Es la bomba del freno trasero: empuja el líquido cuando aprietas la manigueta izquierda.",
        "Revisa el nivel cada semana. El líquido se cambia cada 2 años.",
        ["Manigueta esponjosa", "Fugas en el depósito o la manigueta"], ["Usa el líquido que indica la tapa del depósito"], "taller"),
    "CAP, RESERVOIR": _f(
        "Cierra el depósito del líquido de frenos y lo protege del polvo y la humedad.",
        "El líquido de frenos se cambia cada 2 años o 20.000 km, porque absorbe humedad y pierde eficacia.",
        ["Líquido oscuro en la mirilla (debería verse claro)", "Freno que se siente largo o esponjoso"],
        ["Revisa el nivel con la moto derecha y el manubrio recto", "El líquido de frenos daña la pintura: límpialo de inmediato si cae",
         "No abras el depósito en días de lluvia"],
        "taller"),
    "DIAPHRAGM, RESERVOIR": _f(
        "Es un caucho bajo la tapa del depósito que evita que entre aire y humedad al líquido de frenos.",
        "Se revisa en cada cambio de líquido de frenos (cada 2 años).",
        ["Caucho cuarteado o deformado", "Líquido que se ensucia rápido"], ["Cámbialo si está roto: es barato y protege todo el sistema"], "media"),
    "HOSE, BRAKE": _f(
        "Lleva el líquido de frenos desde la bomba hasta el caliper.",
        "Revísala cada año. Se recomienda cambiarla cada 4 años o si está agrietada.",
        ["Grietas o hinchazón en la manguera", "Freno esponjoso", "Fugas en las uniones"],
        ["Verifica que no roce con nada al girar el manubrio"], "taller"),
    "LEVER": _f(
        "Es la manigueta con la que accionas el freno.",
        "Engrasa su pivote cada 6 meses. Se cambia si está doblada o rota.",
        ["Manigueta dura o que no regresa", "Juego excesivo"], ["Después de una caída revisa que no esté doblada"], "facil"),
    "ROTOR, SENSOR": _f(
        "Es el anillo dentado que lee el sensor del ABS para saber si la rueda se está bloqueando.",
        "Revísalo al limpiar la moto; no tiene cambio periódico.",
        ["Luz de ABS encendida en el tablero"], ["Mantenlo limpio de barro y piedritas", "No lo golpees al quitar la rueda"], "taller"),

    # ---------------- Transmisión CVT y clutch ----------------
    "V-BELT": _f(
        "Es la correa de la transmisión automática: lleva la fuerza del motor hasta la rueda trasera.",
        "Revísala cada 6.000 km y cámbiala cada 12.000 a 20.000 km o antes si está cuarteada o delgada.",
        ["La moto arranca con tirones o le cuesta salir", "Pierde velocidad máxima", "Chillido al acelerar", "Olor a caucho quemado"],
        ["Si se revienta te deja varado: no la lleves al límite", "Cambia la correa junto con los rodillos si están gastados",
         "Mantén limpia la caja del variador"],
        "taller"),
    "WEIGHT SET": _f(
        "Son los rodillos del variador. Con la velocidad se abren y hacen que la moto cambie de relación, como si pasara cambios sola.",
        "Revísalos cada 6.000 km y cámbialos cada 12.000 km aprox. o si están ovalados.",
        ["Arranque lento o con tirones", "La moto no alcanza su velocidad normal", "Ruido de golpeteo en el variador"],
        ["Se cambian todos a la vez", "Usa el peso correcto: rodillos más pesados o livianos cambian cómo responde la moto"],
        "taller"),
    "SLIDER": _f(
        "Son guías plásticas que ayudan a que la polea del variador se deslice suave.",
        "Se revisan junto con los rodillos, cada 12.000 km aprox.",
        ["Ruido en el variador", "Desgaste visible en las guías"], ["Se cambian junto con los rodillos"], "taller"),
    "CAM": _f(
        "Es la rampa sobre la que ruedan los rodillos del variador.",
        "Se revisa al cambiar rodillos.", ["Marcas o surcos donde ruedan los rodillos"], ["Si está marcada, los rodillos nuevos se gastan rápido"], "taller"),
    "PRIMARY SLIDING SHEAVE": _f(
        "Es la polea móvil del variador: se abre y se cierra para cambiar la relación de la transmisión.",
        "Se revisa al cambiar la correa o los rodillos.",
        ["Surcos donde roza la correa", "Arranque irregular"], ["Límpiala de polvo de correa en cada revisión del variador"], "taller"),
    "CLUTCH WEIGHT SHOE SET": _f(
        "Son las zapatas del clutch automático: se abren con las revoluciones y hacen que la moto empiece a andar suavemente.",
        "Revísalas cada 12.000 km. Se cambian cuando el material está delgado o vidriado.",
        ["La moto vibra o tiembla al arrancar", "Patina al salir", "Arranca de golpe"],
        ["Evita salir siempre acelerando a fondo: las gasta más rápido", "Revisa también la campana del clutch"],
        "taller"),
    "CLUTCH CARRIER ASSY": _f(
        "Es el clutch automático completo: une el motor con la rueda cuando aceleras.",
        "Se revisa cada 12.000 km junto con la correa.", ["Vibración al arrancar", "La moto patina"], ["Muchas veces solo hay que cambiar las zapatas"], "taller"),
    "CLUTCH HOUSING": _f(
        "Es la campana del clutch: las zapatas se abren y la agarran para mover la rueda.",
        "Se revisa al cambiar zapatas.", ["Vibración al arrancar", "Superficie interior rayada o con escalón"], ["Si está muy marcada, las zapatas nuevas no agarran bien"], "taller"),
    "SPRING, SECONDARY": _f(
        "Es el resorte de torque del clutch trasero: ayuda a que la correa tenga la tensión correcta.",
        "Se revisa al cambiar la correa.", ["Arranque débil", "La moto pierde fuerza en subidas"], ["Un resorte más duro cambia la respuesta de la moto"], "taller"),

    # ---------------- Motor ----------------
    "PLUG, SPARK": _f(
        "Produce la chispa que enciende la mezcla de aire y gasolina dentro del motor.",
        "Revísala cada 4.000 km y cámbiala cada 8.000 km aprox.",
        ["La moto prende con dificultad", "Se apaga en ralentí o tiene tirones", "Consume más gasolina"],
        ["Usa siempre la referencia indicada para tu moto", "El color de la punta dice mucho: café claro es lo normal; negra indica mezcla rica",
         "Aprieta con la mano y luego un cuarto de vuelta con la llave"],
        "facil", "Lo puedes hacer tú con una llave de bujías"),
    "VALVE, INTAKE": _f(
        "Abre y cierra el paso de la mezcla de aire y gasolina hacia el cilindro.",
        "La calibración se revisa cada 6.000 km aprox. La válvula como tal solo se cambia si se daña.",
        ["Golpeteo metálico en el motor (\"suena a máquina de coser\")", "Pérdida de fuerza", "Arranque difícil en frío"],
        ["La calibración se hace con el motor frío", "Una válvula muy apretada se puede quemar"], "taller"),
    "VALVE, EXHAUST": _f(
        "Abre y cierra la salida de los gases quemados del cilindro.",
        "La calibración se revisa cada 6.000 km aprox.",
        ["Golpeteo en el motor", "Pérdida de fuerza", "Explosiones por el exosto"],
        ["Es la válvula que más calor soporta: una mala calibración la daña"], "taller"),
    "SCREW, VALVE ADJUSTING": _f(
        "Es el tornillo con el que se calibra la holgura de las válvulas.",
        "Se usa en cada calibración de válvulas (cada 6.000 km aprox.).",
        ["Golpeteo en la culata"], ["Se ajusta con calibrador de láminas y el motor frío"], "taller"),
    "SEAL, VALVE STEM": _f(
        "Es un pequeño caucho que evita que el aceite baje por la válvula hacia la cámara de combustión.",
        "Se cambia cuando se repara la culata.",
        ["Humo azul al prender en la mañana", "La moto consume aceite"], ["Si ves humo azul, revisa el nivel de aceite con más frecuencia"], "taller"),
    "RING, PISTON": _f(
        "Son los anillos del pistón: sellan la compresión y controlan el aceite en el cilindro.",
        "Se cambian cuando el motor se repara (generalmente después de muchos miles de km).",
        ["Humo azul constante", "Consumo de aceite", "Pérdida de fuerza"], ["Cambiar el aceite a tiempo es lo que más alarga su vida"], "taller"),
    "GASKET, HEAD COVER": _f(
        "Sella la tapa de válvulas para que no se salga el aceite.",
        "Se cambia cuando se destapa la culata (por ejemplo, al calibrar válvulas) o si hay fuga.",
        ["Manchas de aceite en la parte alta del motor"], ["Es económico: cámbialo cada vez que se abra la tapa"], "taller"),
    "GASKET, CYLINDER HEAD": _f(
        "Sella la unión entre la culata y el cilindro.",
        "Se cambia siempre que se desarma el motor.", ["Pérdida de refrigerante o compresión", "Humo blanco"], ["Nunca se reutiliza"], "taller"),
    "CYLINDER HEAD ASSY": _f(
        "Es la parte de arriba del motor donde están las válvulas y la bujía.",
        "No tiene cambio periódico; se revisa si hay pérdida de compresión.", ["Pérdida de fuerza", "Fugas de aceite o refrigerante"],
        ["El mejor cuidado es no recalentar el motor"], "taller"),

    # ---------------- Lubricación ----------------
    "PLUG,DRAIN": _f(
        "Es el tapón por donde se saca el aceite viejo del motor.",
        "Se quita en cada cambio de aceite (cada 2.500 km o 4 meses aprox.).",
        ["Goteo de aceite debajo del motor"],
        ["Cambia su arandela de sello si está aplastada", "No lo aprietes de más: puedes dañar la rosca del cárter",
         "Saca el aceite con el motor tibio: sale mejor"],
        "facil", "Lo puedes hacer tú con una llave y una vasija"),
    "STRAINER, OIL": _f(
        "Es una malla que atrapa partículas metálicas y suciedad del aceite antes de que lleguen al motor.",
        "Límpiala en cada cambio de aceite.",
        ["Mucho residuo metálico en la malla (avísale al taller)"],
        ["Lávala con gasolina o limpiador y sécala antes de instalarla", "Revisa el O-ring de la tapa"],
        "media"),
    "OIL PUMP ASSY": _f(
        "Hace circular el aceite por todo el motor para lubricarlo y enfriarlo.",
        "No tiene cambio periódico; dura muchos años si cambias el aceite a tiempo.",
        ["Luz de aceite encendida", "Ruido fuerte en el motor"], ["El aceite sucio o viejo es lo que más la daña"], "taller"),

    # ---------------- Admisión e inyección ----------------
    "ELEMENT, AIR CLEANER": _f(
        "Filtra el aire que entra al motor para que no le llegue polvo ni tierra.",
        "Revísalo cada 3.000 km y cámbialo cada 6.000 km aprox. Si ruedas por destapado o con mucho polvo, más seguido.",
        ["La moto pierde fuerza", "Gasta más gasolina", "El filtro se ve negro o con tierra"],
        ["Los filtros de papel no se lavan ni se soplan con aire a presión: se cambian", "Revisa que quede bien asentado: si entra aire sin filtrar, desgasta el motor"],
        "facil", "Lo puedes hacer tú con un destornillador"),
    "CASE, AIR CLEANER": _f(
        "Es la caja que contiene el filtro de aire.", "Límpiala por dentro cada vez que cambies el filtro.",
        ["Grietas que dejan entrar aire sin filtrar"], ["Revisa que su tapa cierre bien"], "facil"),
    "THROTTLE BODY ASSY": _f(
        "Controla cuánto aire entra al motor según cuánto aceleras.",
        "Límpialo cada 10.000 km aprox. o si el ralentí está inestable.",
        ["Ralentí que sube y baja", "La moto se apaga al soltar el acelerador"], ["Usa limpiador específico para cuerpos de aceleración"], "taller"),
    "INJECTOR": _f(
        "Rocía la gasolina dentro del motor en la cantidad exacta.",
        "Limpieza cada 10.000 a 15.000 km aprox. o si hay fallas.",
        ["Tirones", "Consumo alto", "Arranque difícil"], ["Tanquea en estaciones de confianza: la gasolina sucia lo tapa"], "taller"),
    "STEPPING MOTOR": _f(
        "Controla las revoluciones cuando la moto está en ralentí.", "No tiene cambio periódico.",
        ["Ralentí muy alto o muy bajo", "Se apaga al detenerse"], ["Se limpia junto con el cuerpo de aceleración"], "taller"),

    # ---------------- Refrigeración ----------------
    "RADIATOR ASSY": _f(
        "Enfría el líquido refrigerante que circula por el motor.",
        "Revisa el nivel de refrigerante cada semana en el tanque auxiliar. El refrigerante se cambia cada 2 años.",
        ["Temperatura alta en el tablero", "Fugas o manchas verdes/rosadas", "Ventilador prendido todo el tiempo"],
        ["Limpia el panal con agua a baja presión", "Usa refrigerante, nunca solo agua"], "taller"),
    "CAP, RADIATOR": _f(
        "Mantiene el sistema de refrigeración a la presión correcta.",
        "Revísala al cambiar el refrigerante (cada 2 años).",
        ["Pérdida de refrigerante", "Recalentamiento"], ["Nunca la abras con el motor caliente: el líquido sale hirviendo"], "facil"),
    "THERMOSTAT ASSY": _f(
        "Abre o cierra el paso del refrigerante para que el motor llegue rápido a su temperatura ideal.",
        "Se revisa si hay problemas de temperatura.", ["Motor que tarda en calentar", "Recalentamiento"], ["Se prueba en agua caliente con termómetro"], "taller"),
    "FAN": _f(
        "Mueve aire a través del radiador para enfriar el motor.", "Revísalo al limpiar la moto.",
        ["Ruido de roce", "Recalentamiento en trancones"], ["Que no tenga hojas o basura atascada"], "media"),

    # ---------------- Ruedas ----------------
    "TIRE": _f(
        "Es lo único que toca el piso: de la llanta dependen el agarre, el frenado y la estabilidad.",
        "Revisa la presión cada semana (en frío). Cámbiala cuando el labrado llegue al indicador de desgaste o si tiene más de 5 años.",
        ["Labrado liso o al nivel del indicador", "Grietas en los costados", "Chichones o deformaciones", "La moto se siente inestable en curvas"],
        ["Usa la presión de la etiqueta de la moto, no la máxima de la llanta", "En lluvia, una llanta gastada pierde muchísimo agarre",
         "Respeta la medida original"],
        "media", "La presión la revisas tú; el cambio, mejor en el taller"),
    "CAST WHEEL": _f(
        "Es el rin: sostiene la llanta y transmite la fuerza a la rueda.", "Revísalo al cambiar llantas.",
        ["Golpes o fisuras", "Pérdida de aire sin pinchazo", "Vibración"], ["Después de un hueco fuerte, revisa que no esté doblado"], "taller"),
    "VALVE, RIM": _f(
        "Es la válvula por donde se infla la llanta.", "Cámbiala cada vez que cambies la llanta.",
        ["Pérdida lenta de aire"], ["Mantén puesta su tapita"], "taller"),
    "BEARING": _f(
        "Es el rodamiento (balinera) que permite que la rueda gire suave sobre su eje.",
        "Revisa el juego cada 10.000 km. Se cambia si suena o tiene juego.",
        ["Ruido o zumbido que aumenta con la velocidad", "Juego al mover la rueda de lado a lado"],
        ["Evita lavar con agua a presión directo en los ejes"], "taller"),

    "WHEEL OIL SEAL": _f(
        "Es el retenedor de la rueda: protege los rodamientos del agua, el barro y el polvo.",
        "Se cambia junto con los rodamientos o si está roto.",
        ["Rodamientos que se dañan seguido", "Óxido o agua en el eje"],
        ["No lances agua a presión directo al eje de la rueda"], "taller"),

    # ---------------- Suspensión y dirección ----------------
    "FRONT FORK ASSY": _f(
        "Es la suspensión delantera: absorbe los huecos y mantiene la llanta pegada al piso.",
        "El aceite de las barras se cambia cada 20.000 km aprox.; los retenedores, si hay fugas.",
        ["Aceite en las barras", "Se hunde mucho al frenar", "Rebota o golpea en los huecos"],
        ["Limpia las barras después de rodar en barro o polvo"], "taller"),
    "INNER TUBE": _f(
        "Es la barra cromada de la suspensión, por donde se deslizan los retenedores.",
        "Revísala en cada lavada.", ["Rayas, óxido o golpes en el cromo"], ["Un rayón en la barra daña los retenedores nuevos"], "taller"),
    "OIL SEAL": _f(
        "Es el retenedor: un sello de caucho que evita que se salga el aceite.",
        "Se cambia cuando hay fuga.", ["Aceite en la barra o alrededor del sello"],
        ["Si ves aceite en el disco, no ruedes así: el freno pierde agarre"], "taller"),
    "SEAL, DUST": _f(
        "Es el guardapolvo de la barra: evita que el barro y el polvo lleguen al retenedor.",
        "Se cambia junto con los retenedores.", ["Guardapolvo roto o salido"], ["Límpialo después de rodar en destapado"], "taller"),
    "SPRING, FRONT FORK": _f(
        "Es el resorte que sostiene el peso de la moto adelante.",
        "Se revisa cuando se cambia el aceite de las barras (cada 20.000 km aprox.).",
        ["La moto se hunde mucho al frenar", "Queda más baja adelante"], ["Si llevas parrillero seguido, puede convenir un resorte más firme"], "taller"),
    "SHOCK ABSORBER": _f(
        "Es el amortiguador trasero: absorbe los golpes y controla que la moto no rebote.",
        "Revísalo cada 10.000 km; dura entre 20.000 y 40.000 km según el uso.",
        ["La moto rebota después de un hueco", "Aceite en el cuerpo del amortiguador", "Golpe seco al pasar resaltos"],
        ["Ajusta la precarga si llevas parrillero o carga", "Cambia los dos al tiempo si la moto tiene doble amortiguador"],
        "media"),
    "ARM, REAR": _f(
        "Es el basculante: une la rueda trasera con la moto y le permite subir y bajar.",
        "Engrasa sus bujes cada 10.000 km aprox.", ["Juego al mover la rueda trasera de lado", "Ruidos en curvas"], ["Revisa los bujes si la moto se siente floja atrás"], "taller"),
    "BEARING, STEERING": _f(
        "Son los rodamientos de la dirección: permiten girar el manubrio suave.",
        "Revísalos y engrásalos cada 10.000 a 15.000 km.",
        ["La dirección se siente pesada o \"con puntos\"", "Golpe al frenar fuerte", "La moto se va de lado en recta"],
        ["Si al girar el manubrio se siente un punto duro en el centro, revísalos"], "taller"),
    "RACE, BALL": _f(
        "Son las tazas donde ruedan los rodamientos de la dirección.", "Se revisan con los rodamientos de dirección.",
        ["Dirección con \"puntos\""], ["Se cambian junto con los rodamientos"], "taller"),

    # ---------------- Eléctrico ----------------
    "BATTERY ASSY": _f(
        "Guarda la energía para el arranque, la inyección y las luces.",
        "Revisa sus bornes cada 6 meses. Suele durar entre 2 y 3 años.",
        ["Arranque lento o sin fuerza", "Luces débiles con el motor apagado", "Tablero que se reinicia al prender"],
        ["Si no vas a usar la moto por semanas, desconéctala o usa un mantenedor de carga", "Mantén los bornes limpios y apretados",
         "Las baterías de gel no se les echa agua"],
        "facil", "La puedes cambiar tú; quita primero el borne negativo"),
    "FUSE": _f(
        "Protege los circuitos eléctricos: se quema antes de que se dañe algo más caro.",
        "Solo se cambia cuando se quema.", ["Algo deja de funcionar de repente (luces, pito, tablero)"],
        ["Reemplázalo por uno del mismo amperaje, nunca mayor", "Si se quema seguido, hay un corto: llévala al taller", "Lleva fusibles de repuesto"],
        "facil"),
    "XMTR. COMP": _f(
        "Es la llave inteligente: la moto la reconoce cuando está cerca y te deja prender sin meter la llave.",
        "Su pila se cambia cada 1 a 2 años, o cuando el tablero avise batería baja de la llave.",
        ["La moto no reconoce la llave", "Aviso de batería baja en el tablero"],
        ["Lleva siempre la llave de repuesto en un lugar seguro, fuera de la moto", "No la dejes cerca de celulares o imanes"],
        "facil", "La pila la cambias tú"),
    "REMOTE CONTROL UNIT ASSY": _f(
        "Es el módulo que reconoce la llave inteligente y permite el encendido.", "No tiene cambio periódico.",
        ["La moto no reconoce ninguna llave"], ["Revisa primero la pila de la llave"], "taller"),
    "RELAY ASSY": _f(
        "Es un interruptor eléctrico que activa circuitos de alto consumo, como el arranque.",
        "No tiene cambio periódico.", ["Clic al dar arranque pero el motor no gira"], ["Revisa primero la batería antes de cambiarlo"], "media"),
    "SWITCH, SIDE STAND": _f(
        "Es el sensor que apaga el motor si arrancas con la pata lateral abajo, para evitar accidentes.",
        "Límpialo cada vez que laves la moto.", ["La moto se apaga al meter cambio o no prende"],
        ["No lo anules: es un elemento de seguridad"], "media"),
    "STOP SWITCH": _f(
        "Prende la luz de freno cuando aprietas la manigueta.", "Revisa la luz de freno cada semana.",
        ["La luz de freno no prende o queda prendida"], ["Pídele a alguien que te mire la luz mientras frenas"], "media"),
}

# Guías genéricas por tipo de pieza (palabra principal de la descripción).
CATEGORIAS = {
    "tornilleria": _f(
        "Sujeta y une las piezas de la moto.",
        "No tiene cambio periódico. Revisa su ajuste en cada mantenimiento.",
        ["Piezas flojas o que vibran", "Cabeza barrida o rosca dañada"],
        ["Aprieta con la fuerza indicada: de más se rompe o daña la rosca", "Los tornillos de frenos y suspensión llevan torque exacto",
         "Reemplázalo por uno igual (mismo largo y dureza)"], "media"),
    "empaques": _f(
        "Sella la unión entre dos piezas para que no se salgan líquidos ni entre aire.",
        "Se cambia cada vez que se desarma esa unión o si hay fuga.",
        ["Goteo o manchas de aceite o refrigerante"], ["Los empaques y O-rings casi nunca se reutilizan: son baratos y evitan fugas"], "media"),
    "seguros": _f(
        "Asegura que una pieza no se salga de su sitio.", "Se cambia si se deforma o al desarmar.",
        ["Pieza con juego o que se sale"], ["Un pin seguro deformado pierde fuerza: cámbialo"], "media"),
    "bujes": _f(
        "Sirve de guía o separador para que las piezas queden alineadas y giren bien.",
        "Se revisa al desarmar la pieza donde va.", ["Juego o ruido en la unión"], ["Engrásalo al instalar si lo indica el manual"], "media"),
    "resortes": _f(
        "Hace que una pieza regrese a su posición o mantenga presión.", "Se revisa al desarmar; se cambia si está vencido o roto.",
        ["La pieza no regresa sola", "Resorte deformado"], ["Compara su largo con uno nuevo"], "media"),
    "cauchos": _f(
        "Amortigua vibraciones y evita que las piezas se golpeen o rocen.", "Se cambia si está cuarteado o endurecido.",
        ["Vibraciones o ruidos de golpeteo", "Caucho agrietado"], ["El sol y la gasolina los resecan más rápido"], "facil"),
    "mangueras": _f(
        "Conduce líquidos, aire o vapores entre las piezas.", "Revísala cada año; se cambia si está agrietada o endurecida.",
        ["Grietas, fugas o manguera aplastada"], ["Verifica que sus abrazaderas estén bien apretadas"], "media"),
    "soportes": _f(
        "Sostiene una pieza en su lugar.", "No tiene cambio periódico.", ["Pieza floja o que vibra", "Soporte doblado o fisurado"],
        ["Después de una caída, revisa que no esté doblado"], "media"),
    "tapas": _f(
        "Cubre y protege una parte de la moto.", "Se cambia si está rota o no cierra bien.", ["Tapa suelta, rota o con fugas"],
        ["Revisa que su empaque esté en buen estado"], "facil"),
    "general": _f(
        "Es una pieza del conjunto que ves en el dibujo.", "No tiene un cambio periódico definido: se revisa cuando se trabaja en esta parte de la moto.",
        ["Ruidos, juego o fugas en esta zona"], ["Si notas algo raro en esta parte, menciónaselo al taller con el código de la pieza"], "taller"),
}

_CATEGORIA_POR_PALABRA = {
    "BOLT": "tornilleria", "SCREW": "tornilleria", "NUT": "tornilleria", "WASHER": "tornilleria", "PIN": "tornilleria",
    "GASKET": "empaques", "O-RING": "empaques", "SEAL": "empaques",
    "CLIP": "seguros", "CIRCLIP": "seguros", "RING": "seguros", "RETAINER": "seguros", "LOCK": "seguros",
    "COLLAR": "bujes", "BUSH": "bujes", "SPACER": "bujes",
    "SPRING": "resortes",
    "DAMPER": "cauchos", "GROMMET": "cauchos", "BOOT": "cauchos",
    "HOSE": "mangueras", "PIPE": "mangueras", "CLAMP": "mangueras", "BAND": "mangueras",
    "HOLDER": "soportes", "BRACKET": "soportes", "STAY": "soportes", "SUPPORT": "soportes", "PLATE": "soportes",
    "COVER": "tapas", "CAP": "tapas", "PLUG": "tapas",
}

# Ajustes según el sistema (la misma pieza cumple funciones distintas según dónde está).
_POR_SISTEMA = {
    ("OIL SEAL", "llanta_del"): "WHEEL OIL SEAL", ("OIL SEAL", "llanta_tras"): "WHEEL OIL SEAL",
}


def _normalizar(texto):
    t = re.sub(r"\s*\(.*?\)", "", texto.upper()).strip()
    t = re.sub(r"[\s.]*\d+$", "", t)
    return t.lstrip(". ").rstrip(". ").strip()


_FICHAS = {_normalizar(k): v for k, v in FICHAS.items()}


def ficha_para(descripcion, pieza=""):
    clave = _normalizar(descripcion)
    clave = _POR_SISTEMA.get((clave, pieza), clave)
    if clave in _FICHAS:
        return dict(_FICHAS[clave])
    candidatos = [k for k in _FICHAS if clave.startswith(k)]
    if candidatos:
        return dict(_FICHAS[max(candidatos, key=len)])
    palabra = re.split(r"[ ,]", clave, maxsplit=1)[0]
    return dict(CATEGORIAS[_CATEGORIA_POR_PALABRA.get(palabra, "general")])


# ---------------------------------------------------------------------------
# Información adicional: cómo revisarla, qué pasa si no se atiende y qué tener en cuenta al comprar.
# ---------------------------------------------------------------------------
def _x(como_revisar, si_no, al_comprar):
    return {"como_revisar": como_revisar, "si_no": si_no, "al_comprar": al_comprar}


EXTRAS = {
    "BRAKE PAD KIT": _x(
        ["Mira por el caliper, desde abajo o de lado: debe quedar material de fricción visible (más de 2 mm).",
         "Si la pastilla tiene una ranura en el centro y ya no se ve, está gastada.",
         "Aprieta la manigueta: debe sentirse firme y frenar antes de llegar al puño."],
        "Al llegar al metal, la pastilla raya el disco, el freno pierde fuerza y el arreglo pasa de unas pastillas a pastillas más disco.",
        ["Pide el juego para tu moto (delantero o trasero, no son iguales).",
         "Prefiere originales o marcas reconocidas; las muy baratas chillan y se gastan rápido.",
         "Lleva el código de repuesto para no equivocarte."]),
    "DISK, BRAKE": _x(
        ["Pasa la uña por la superficie: si se traba en surcos profundos, está muy gastado.",
         "Busca el grosor mínimo grabado en el disco (dice MIN TH) y pídele al taller que lo mida.",
         "Si la manigueta vibra al frenar, el disco puede estar torcido."],
        "Un disco delgado o torcido frena peor, se calienta más y gasta las pastillas nuevas muy rápido.",
        ["Compra el disco del lado correcto (en algunas motos hay derecho e izquierdo).", "Cámbialo junto con pastillas nuevas."]),
    "CALIPER ASSY": _x(
        ["Gira la rueda con la mano después de frenar: debe girar libre, sin quedarse pegada.",
         "Busca manchas de líquido o humedad alrededor del caliper.",
         "Compara el desgaste de las dos pastillas: deberían gastarse parejo."],
        "Un caliper pegado deja el freno rozando: calienta la rueda, gasta pastillas y puede bloquear la frenada.",
        ["Muchas veces basta con el kit de empaques y una limpieza; no siempre hay que cambiarlo completo."]),
    "MASTER CYLINDER ASSY": _x(
        ["Revisa el nivel en la mirilla con la moto derecha y el manubrio recto.",
         "Aprieta la manigueta varias veces: no debe ir bajando hasta el puño.",
         "Busca humedad debajo de la manigueta o del depósito."],
        "Si la bomba pierde presión, el freno se va al fondo de repente; es una de las fallas más peligrosas.",
        ["Antes de cambiarla completa, pregunta por el kit de reparación de la bomba."]),
    "CAP, RESERVOIR": _x(
        ["Mira el color del líquido por la mirilla: claro está bien; oscuro o turbio toca cambiarlo.",
         "Revisa que el nivel esté entre las marcas MIN y MAX."],
        "El líquido viejo absorbe humedad: con el calor de frenadas largas puede hervir y el freno se queda sin fuerza.",
        ["Usa el tipo de líquido que dice la tapa (normalmente DOT 4).",
         "Compra un envase nuevo y sellado: uno abierto hace tiempo ya absorbió humedad."]),
    "HOSE, BRAKE": _x(
        ["Recorre la manguera con la vista buscando grietas, hinchazones o roces.",
         "Gira el manubrio a ambos lados: no debe estirarse ni quedar apretada."],
        "Una manguera vieja se hincha al frenar (el freno se siente esponjoso) y puede romperse.",
        ["Respeta el largo original para que no quede tensa al girar."]),
    "LEVER": _x(
        ["Acciónala: debe moverse suave y regresar sola.", "Mueve la manigueta hacia los lados: no debe tener juego."],
        "Una manigueta floja o doblada hace que el freno se sienta impreciso.",
        ["Revisa si es la del freno delantero o la del trasero; son distintas."]),
    "V-BELT": _x(
        ["Pídele al taller que mida el ancho: cada correa tiene un ancho mínimo.",
         "Busca grietas entre los dientes, bordes desgastados o brillo de patinamiento.",
         "Fíjate si la moto tarda más en arrancar o pierde velocidad final."],
        "Una correa al límite puede reventarse en plena vía y dejarte varado.",
        ["Usa la referencia exacta: una correa más larga o angosta cambia cómo arranca la moto.",
         "Aprovecha y revisa rodillos y deslizadores."]),
    "WEIGHT SET": _x(
        ["Los rodillos deben ser redondos: si tienen partes planas, están gastados.",
         "Un golpeteo en el variador al soltar el acelerador suele venir de los rodillos."],
        "Rodillos gastados hacen que la moto arranque a tirones, gaste más gasolina y no llegue a su velocidad normal.",
        ["Compra el juego completo con el peso original (viene marcado en gramos).", "Cámbialos junto con los deslizadores."]),
    "CLUTCH WEIGHT SHOE SET": _x(
        ["Si al arrancar la moto vibra o tiembla, las zapatas pueden estar vidriadas.",
         "El taller revisa el grosor del material de fricción."],
        "Las zapatas gastadas hacen que la moto patine al salir y desgastan la campana.",
        ["Revisa la campana al mismo tiempo; si está marcada, las zapatas nuevas no agarran bien."]),
    "CLUTCH HOUSING": _x(
        ["El taller mira el interior: debe estar parejo, sin escalón ni rayas profundas."],
        "Una campana marcada hace vibrar la moto al arrancar aunque las zapatas sean nuevas.",
        ["Se cambia casi siempre junto con las zapatas."]),
    "PLUG, SPARK": _x(
        ["Sácala con el motor frío y mira la punta: café claro es lo normal.",
         "Negra y con hollín indica mezcla rica o filtro sucio; blanca, mezcla pobre o recalentamiento.",
         "Revisa que el electrodo no esté redondeado ni demasiado separado."],
        "Una bujía gastada hace que la moto prenda mal, pierda fuerza y gaste más gasolina.",
        ["Pide la referencia exacta de tu moto (en la NMAX viene en la descripción del catálogo).",
         "No cambies a una bujía más caliente o más fría sin consultar."]),
    "VALVE, INTAKE": _x(
        ["Escucha el motor en frío: un golpeteo metálico rítmico suele ser válvulas descalibradas.",
         "La calibración se mide con calibrador de láminas, con el motor frío."],
        "Una válvula muy ajustada no cierra bien: pierde compresión, se calienta y se puede quemar.",
        ["Normalmente solo se calibra; cambiar la válvula es una reparación mayor."]),
    "VALVE, EXHAUST": _x(
        ["Escucha el motor en frío por golpeteos.", "Pérdida de fuerza o explosiones en el exosto pueden indicar mala calibración."],
        "La válvula de escape es la que más calor recibe: mal calibrada se quema y obliga a reparar la culata.",
        ["Pide la calibración en cada mantenimiento mayor."]),
    "PLUG,DRAIN": _x(
        ["Mira debajo del motor: no debe haber gotas de aceite.",
         "Al sacarlo, revisa que la rosca y la arandela estén en buen estado."],
        "Un tapón flojo o con la rosca dañada puede botar el aceite y fundir el motor.",
        ["Compra también la arandela o el O-ring del tapón: es muy barato y evita fugas."]),
    "STRAINER, OIL": _x(
        ["En el cambio de aceite, sácala y mírala: debe estar limpia, sin pedazos metálicos.",
         "Unos pocos residuos finos son normales; pedazos grandes no."],
        "Si se tapa, el aceite circula menos y el motor se desgasta más rápido.",
        ["Normalmente se limpia y se reutiliza; se cambia si está rota o deformada."]),
    "ELEMENT, AIR CLEANER": _x(
        ["Abre la caja del filtro y míralo a contraluz: si no pasa luz o está negro, cámbialo.",
         "Revisa que no tenga roturas ni que entre tierra por los bordes."],
        "Un filtro tapado ahoga el motor: pierde fuerza y gasta más. Uno roto deja entrar polvo que desgasta el cilindro.",
        ["Usa la medida exacta para tu moto; uno que no sella bien es peor que uno sucio."]),
    "THROTTLE BODY ASSY": _x(
        ["Si el ralentí sube y baja solo o la moto se apaga al soltar el acelerador, puede estar sucio."],
        "Un cuerpo de aceleración sucio da ralentí inestable y respuesta lenta.",
        ["Primero se limpia; cambiarlo es raro."]),
    "INJECTOR": _x(
        ["Tirones al acelerar, consumo alto o arranque difícil pueden venir de un inyector sucio."],
        "Un inyector tapado deja la mezcla pobre: el motor se calienta y pierde fuerza.",
        ["La limpieza con equipo de ultrasonido suele ser suficiente."]),
    "RADIATOR ASSY": _x(
        ["Con el motor frío, revisa el nivel en el tanque auxiliar (entre MIN y MAX).",
         "Mira el panal: debe estar limpio, sin hojas ni barro, y sin aletas aplastadas.",
         "Busca manchas verdes o rosadas debajo de la moto."],
        "Sin buen enfriamiento el motor se recalienta y se puede dañar el empaque de la culata.",
        ["Usa refrigerante listo para usar o mezclado como indica el envase; nunca solo agua."]),
    "CAP, RADIATOR": _x(
        ["Con el motor frío, revisa que el caucho de la tapa no esté cuarteado."],
        "Una tapa que no sella deja escapar refrigerante y el motor se recalienta.",
        ["Compra la de la presión correcta (viene marcada en la tapa)."]),
    "THERMOSTAT ASSY": _x(
        ["Si el motor tarda mucho en calentar o se recalienta rápido, el termostato puede estar pegado."],
        "Pegado cerrado recalienta el motor; pegado abierto lo deja trabajar frío y gastar más.",
        ["Cámbialo junto con el refrigerante para aprovechar el vaciado."]),
    "TIRE": _x(
        ["Mide la presión en frío, cada semana, con un manómetro.",
         "Busca los testigos de desgaste (pequeños topes en el labrado): si el labrado llegó a ellos, toca cambiarla.",
         "Revisa grietas en los costados y la fecha de fabricación (4 números en el costado: semana y año)."],
        "Una llanta lisa o con poca presión pierde agarre, sobre todo con lluvia, y aumenta el riesgo de caída.",
        ["Respeta la medida original (en la NMAX viene en la descripción).",
         "No mezcles llantas muy diferentes adelante y atrás.",
         "Evita llantas con más de 5 años de fabricación aunque estén nuevas."]),
    "CAST WHEEL": _x(
        ["Gira la rueda y mírala de frente: no debe bailar.", "Busca golpes o fisuras en el borde, sobre todo después de un hueco fuerte."],
        "Un rin golpeado puede perder aire lentamente y causar vibraciones a velocidad.",
        ["Un rin fisurado no se suelda: se cambia."]),
    "BEARING": _x(
        ["Con la rueda levantada, muévela de lado a lado: no debe tener juego.", "Gírala con la mano: debe girar suave y sin ruido."],
        "Un rodamiento dañado se recalienta, hace ruido y en casos extremos puede trabar la rueda.",
        ["Cambia los dos rodamientos de la rueda al tiempo, con sus retenedores."]),
    "FRONT FORK ASSY": _x(
        ["Limpia las barras y mira si después de rodar aparece aceite.",
         "Frena y suelta varias veces con la moto quieta: debe bajar y subir suave, sin rebotar."],
        "Sin aceite o con retenedores dañados, la moto se hunde al frenar y pierde estabilidad.",
        ["Usa el aceite de barras del grado indicado y la cantidad exacta por barra."]),
    "OIL SEAL": _x(
        ["Mira la parte superior de la botella: no debe haber un anillo de aceite ni suciedad pegada."],
        "Si el aceite cae al freno o a la llanta, la moto pierde agarre al frenar.",
        ["Cambia los retenedores y guardapolvos de las dos barras al mismo tiempo."]),
    "SPRING, FRONT FORK": _x(
        ["Con la moto quieta, empuja el manubrio hacia abajo: si se hunde demasiado, los resortes pueden estar vencidos."],
        "Resortes vencidos hacen que la moto se hunda al frenar y toque fondo en los huecos.",
        ["Si llevas parrillero o carga seguido, pregunta por resortes más firmes."]),
    "SHOCK ABSORBER": _x(
        ["Empuja la parte trasera hacia abajo y suelta: debe subir una vez y quedarse quieta.",
         "Mira el cuerpo del amortiguador: no debe tener aceite."],
        "Un amortiguador vencido hace rebotar la moto, cansa al conductor y gasta más la llanta trasera.",
        ["Si tu moto tiene dos, cámbialos en pareja."]),
    "BATTERY ASSY": _x(
        ["Si tienes multímetro: con la moto apagada debe marcar unos 12,6 V; con el motor encendido, entre 13,5 y 14,5 V.",
         "Revisa que los bornes estén limpios y apretados.",
         "Si la moto prende lento en las mañanas, es la primera señal."],
        "Una batería débil puede dejarte sin arranque y afectar la inyección y el tablero.",
        ["Compra la referencia exacta (tamaño y capacidad).",
         "Fíjate en la fecha de fabricación: que no tenga muchos meses en bodega."]),
    "FUSE": _x(
        ["Saca el fusible y míralo a contraluz: si el hilo de adentro está cortado, está quemado."],
        "Un fusible mal reemplazado (de más amperaje) puede quemar cables o el arnés.",
        ["Respeta el amperaje: viene marcado en el fusible y en la tapa de la caja de fusibles."]),
    "SWITCH, SIDE STAND": _x(
        ["Con la pata abajo, la moto no debe dejar arrancar o debe apagarse al meter marcha."],
        "Si falla, la moto puede apagarse sola o no prender.",
        ["Límpialo antes de cambiarlo: muchas fallas son por suciedad."]),
    "XMTR. COMP": _x(
        ["Si la moto tarda en reconocer la llave o el tablero avisa batería baja, cambia la pila."],
        "Con la pila agotada, la moto no reconoce la llave y no te deja prender.",
        ["La pila es tipo moneda (normalmente CR2032); revisa la que trae la tuya antes de comprar."]),
}

EXTRAS_CATEGORIA = {
    "tornilleria": _x(
        ["Revisa que estén completos y apretados; en frenos y suspensión no los aprietes a ojo."],
        "Un tornillo flojo puede hacer vibrar o soltar una pieza; uno apretado de más puede dañar la rosca.",
        ["Pide el tornillo por su código: largo, rosca y dureza deben ser iguales al original."]),
    "empaques": _x(
        ["Busca goteos o manchas de aceite, líquido o refrigerante alrededor de la unión."],
        "Un empaque vencido causa fugas que ensucian, bajan el nivel de aceite o refrigerante y pueden recalentar el motor.",
        ["Compra empaques nuevos cada vez que se destape esa parte; no se reutilizan."]),
    "seguros": _x(
        ["Cuando se desarma la pieza, revisa que el seguro no esté abierto ni deformado."],
        "Un seguro vencido puede dejar que una pieza se salga de su sitio.",
        ["Son muy baratos: cámbialos al desarmar."]),
    "bujes": _x(
        ["Mueve la pieza donde va: no debe tener juego ni hacer ruido."],
        "Un buje gastado deja juego y desgasta las piezas vecinas.",
        ["Pide la medida exacta por el código."]),
    "resortes": _x(
        ["Compáralo con uno nuevo: si está más corto o deformado, perdió fuerza."],
        "Un resorte vencido hace que la pieza no regrese bien a su posición.",
        ["Usa el original: uno más duro o más blando cambia el funcionamiento."]),
    "cauchos": _x(
        ["Mira si está cuarteado, endurecido o fuera de su sitio."],
        "Sin el caucho, las piezas vibran, suenan y se desgastan entre sí.",
        ["Son económicos; cámbialos al primer signo de resequedad."]),
    "mangueras": _x(
        ["Revisa grietas, partes aplastadas y que las abrazaderas estén firmes."],
        "Una manguera rota puede causar fugas o que el sistema deje de funcionar.",
        ["Respeta el diámetro y el largo original."]),
    "soportes": _x(
        ["Revisa que esté derecho y bien sujeto, sobre todo después de una caída."],
        "Un soporte doblado o roto deja la pieza floja y puede romperla.",
        ["Pídelo por código: los soportes cambian entre versiones."]),
    "tapas": _x(
        ["Revisa que cierre bien y no tenga grietas."],
        "Una tapa rota deja entrar agua y polvo o permite fugas.",
        ["Revisa el color y la versión de tu moto antes de comprar."]),
    "general": _x(
        ["Si notas ruidos, juego o fugas en esta zona, menciónaselo al taller."],
        "Las piezas de esta zona trabajan juntas: una dañada puede afectar a las demás.",
        ["Lleva el código de repuesto: es la forma más segura de pedir la pieza correcta."]),
}

SISTEMAS = {
    "freno_del": "el freno delantero", "freno_tras": "el freno trasero",
    "correa": "la transmisión automática (variador y clutch)", "aceite": "la lubricación del motor",
    "filtro_aire": "la admisión de aire y la inyección", "bujia": "el cilindro y la culata",
    "motor": "las válvulas del motor", "refrigeracion": "el sistema de refrigeración",
    "llanta_del": "la rueda delantera", "llanta_tras": "la rueda trasera",
    "suspension_del": "la suspensión delantera y la dirección", "suspension_tras": "el basculante y los amortiguadores",
    "bateria": "el sistema eléctrico",
}
_SEGURIDAD = {"freno_del", "freno_tras", "llanta_del", "llanta_tras", "suspension_del", "suspension_tras"}
_EXTRAS = {_normalizar(k): v for k, v in EXTRAS.items()}


def _categoria(clave):
    return _CATEGORIA_POR_PALABRA.get(re.split(r"[ ,]", clave, maxsplit=1)[0], "general")


def ficha_completa(descripcion, pieza=""):
    """Guía completa: ficha base + cómo revisarla, consecuencias, consejos de compra y contexto del sistema."""
    alias = _ALIAS.get(_normalizar(descripcion))
    ficha = ficha_para(alias or descripcion, pieza)
    clave = alias or _POR_SISTEMA.get((_normalizar(descripcion), pieza), _normalizar(descripcion))
    if ficha["que_hace"] in _GENERICOS:
        # En vez del texto genérico de la categoría, una descripción propia de la pieza.
        que_hace, cada_cuanto = que_hace_especifico(descripcion, pieza)
        if que_hace:
            ficha["que_hace"] = que_hace
        if cada_cuanto:
            ficha["cada_cuanto"] = cada_cuanto
    especifica = _EXTRAS.get(clave)
    if not especifica:
        candidatos = [k for k in _EXTRAS if clave.startswith(k)]
        especifica = _EXTRAS[max(candidatos, key=len)] if candidatos else None
    categoria = _categoria(clave)
    ficha.update(especifica or EXTRAS_CATEGORIA.get(categoria, EXTRAS_CATEGORIA["general"]))
    sistema = SISTEMAS.get(pieza)
    de_sistema = ("del " + sistema[3:]) if sistema and sistema.startswith("el ") else f"de {sistema}"
    contexto = f"En tu moto hace parte {de_sistema}." if sistema else ""
    if sistema and categoria == "tornilleria" and pieza in _SEGURIDAD:
        contexto += (" Como es una parte de seguridad, sus tornillos llevan un apriete (torque) exacto: "
                     "si se aflojan o se aprietan de más, es un riesgo.")
    ficha["contexto"] = contexto
    return ficha


# ---------------------------------------------------------------------------
# "¿Qué hace?" específico para cada pieza (en vez del texto genérico de su categoría).
# ---------------------------------------------------------------------------
def _q(que_hace, cada_cuanto=None):
    return {"que_hace": que_hace, "cada_cuanto": cada_cuanto}


QUE_HACE = {
    "AXLE, WHEEL": _q("Es el eje que atraviesa la rueda y la sujeta a la suspensión; sobre él giran los rodamientos.",
                      "Se revisa y se engrasa cada vez que se desmonta la rueda (por ejemplo, al cambiar la llanta)."),
    "BUZZER": _q("Es el pito de alerta del sistema eléctrico: suena con algunos avisos, como los de la llave inteligente.", "No tiene mantenimiento."),
    "CASE, FAN": _q("Es la carcasa que rodea el ventilador del radiador y dirige el aire a través del panal.", "Se revisa al limpiar el radiador."),
    "COCK, DRAIN": _q("Es el tornillo de drenaje del sistema de refrigeración: por ahí se saca el refrigerante viejo.",
                      "Se usa en cada cambio de refrigerante (cada 2 años aprox.)."),
    "COVER, BALL RACE": _q("Es el guardapolvo de la dirección: protege los rodamientos de la dirección del agua y la tierra.",
                           "Se revisa cuando se engrasa la dirección (cada 10.000 a 15.000 km)."),
    "COVER, CYLINDER HEAD": _q("Es la tapa de válvulas: cierra la parte de arriba del motor y protege el mecanismo de las válvulas.",
                               "Se destapa para calibrar las válvulas (cada 6.000 km aprox.)."),
    "COVER, MAIN SWITCH": _q("Es la tapa que protege el switch de encendido del agua y la suciedad."),
    "COVER, RADIATOR": _q("Es la rejilla que protege el radiador de piedras e insectos sin bloquear el paso del aire.", "Límpiala cada vez que laves la moto."),
    "COVER, UNDER": _q("Es una tapa inferior que cubre y protege la parte baja de la dirección."),
    "CYLINDER": _q("Es el cilindro del motor: por dentro sube y baja el pistón, y ahí ocurre la combustión.",
                   "No tiene cambio periódico; se revisa si el motor pierde fuerza o empieza a consumir aceite."),
    "CYLINDER COMP., FRONT FORK": _q("Es el cilindro amortiguador dentro de la barra: usando el aceite, controla qué tan rápido se hunde y regresa la suspensión.",
                                     "Se revisa cuando se cambia el aceite de las barras (cada 20.000 km aprox.)."),
    "CYLINDER KIT, MASTER": _q("Es el kit de reparación de la bomba de freno: trae el pistón y los empaques internos.",
                               "Se usa cuando la bomba pierde presión o tiene fugas."),
    "DAMPER ASSY": _q("Es el conjunto amortiguador de una de las barras de la suspensión delantera (izquierda o derecha).",
                      "Se revisa cuando se cambia el aceite de las barras."),
    "DAMPER, CLUTCH WEIGHT": _q("Son cauchos que amortiguan las zapatas del clutch para que la moto arranque más suave.", "Se cambian junto con las zapatas."),
    "DIODE ASSY": _q("Es un diodo: un componente eléctrico que deja pasar la corriente en un solo sentido y protege los circuitos.", "No tiene mantenimiento."),
    "DUCT": _q("Es un ducto que conduce el aire de afuera hacia la caja del filtro."),
    "GASKET, BREATHER COVER": _q("Sella la tapa del respiradero del motor para que no salgan vapores ni aceite.", "Se cambia si hay fuga o al destapar esa tapa."),
    "GASKET, CYLINDER": _q("Sella la unión entre el cilindro y el cárter del motor.", "Se cambia siempre que se desarma el motor."),
    "GASKET, MANIFOLD": _q("Sella la unión del múltiple de admisión con la culata para que no entre aire por donde no debe.",
                           "Se cambia al desmontar el múltiple o si el motor tiene ralentí inestable por entrada de aire."),
    "GUIDE, VALVE": _q("Es el tubo por donde se desliza la válvula: la mantiene centrada al abrir y cerrar.", "Se revisa cuando se repara la culata."),
    "HOLDER, BRAKE HOSE": _q("Es la grapa que sujeta la manguera de freno a lo largo de su recorrido, para que no roce con la rueda ni se enrede con la suspensión.",
                             "Revisa que esté en su sitio después de cualquier reparación de frenos o suspensión."),
    "JOINT, AIR CLEANER": _q("Es el ducto de caucho que une la caja del filtro de aire con el cuerpo de aceleración.",
                             "Revísalo cuando cambies el filtro: no debe estar cuarteado."),
    "KNOB COMP": _q("Es la perilla del switch de encendido: en las motos con llave inteligente se gira para prender y apagar."),
    "LOCK, VALVE SPRING RETAINER": _q("Son las cuñas: dos piezas pequeñas que aseguran el platillo y el resorte a la válvula.", "Se revisan cuando se repara la culata."),
    "MAIN SWITCH STEERING LOCK": _q("Es el switch de encendido: prende y apaga la moto, y en la posición de bloqueo traba el manubrio para dificultar un robo.",
                                    "No tiene mantenimiento; si se pone duro o falla a veces, haz que lo revisen antes de que te deje varado."),
    "MANIFOLD": _q("Es el múltiple de admisión: une el cuerpo de aceleración con la culata y lleva la mezcla de aire y gasolina al motor."),
    "PIN, DOWEL": _q("Son guías de centrado: aseguran que el cilindro y la culata queden perfectamente alineados al armar el motor."),
    "PIN, GUIDE": _q("Es un pasador guía que mantiene alineadas las poleas traseras de la transmisión."),
    "PIN, PAD": _q("Es el pasador que sostiene las pastillas dentro del caliper y les permite moverse.", "Se limpia y se revisa en cada cambio de pastillas."),
    "PIPE, BREATHER": _q("Es la manguera del respiradero: lleva los vapores del motor hacia la caja del filtro para que no salgan al ambiente."),
    "PIPE, DRAIN": _q("Es la manguera de drenaje de la caja del filtro: deja salir el agua o el aceite que se acumula ahí.",
                      "Revísala y vacíala cada vez que cambies el filtro de aire."),
    "PLATE, BREATHER": _q("Es una placa del respiradero que ayuda a separar el aceite de los vapores del motor."),
    "PLATE, DIAPHRAGM": _q("Es la placa que mantiene el diafragma del depósito de frenos en su lugar."),
    "PLUG, HOLE": _q("Es un tapón que cierra un agujero de acceso para que no entre agua ni suciedad."),
    "PLUG, STRAIGHT SCREW": _q("Es un tapón roscado que cierra un conducto del motor."),
    "RETAINER, BALL BEARING": _q("Es el seguro que mantiene en su sitio el rodamiento de la dirección."),
    "RETAINER, VALVE SPRING": _q("Es el platillo que sostiene por arriba el resorte de la válvula."),
    "ROD": _q("Es una varilla del conjunto: sirve de guía o de unión entre piezas de esta parte de la moto."),
    "SEAT, SECONDARY SPRING": _q("Es la base sobre la que se apoya el resorte de torque del clutch."),
    "SEAT, VALVE SPRING": _q("Es la base sobre la que se apoya el resorte de la válvula en la culata."),
    "SECONDARY FIXED SHEAVE COMP": _q("Es la polea fija trasera de la transmisión: junto con la polea móvil forma el canal donde corre la correa atrás.",
                                      "Se revisa al cambiar la correa: no debe tener surcos donde roza."),
    "SECONDARY SLIDING SHEAVE": _q("Es la polea móvil trasera: con ayuda del resorte de torque se abre y se cierra para mantener la correa tensa.",
                                   "Se revisa al cambiar la correa."),
    "SHAFT, ROCKER": _q("Es el eje sobre el que pivotan los balancines de las válvulas.", "Se revisa al calibrar o reparar las válvulas."),
    "SHEAVE, PRIMARY FIXED": _q("Es la polea fija delantera del variador; sus aletas mueven aire para refrescar la transmisión.",
                                "Se revisa al cambiar la correa o los rodillos."),
    "SHIM, CALIPER": _q("Es una lámina que va detrás de las pastillas para reducir chillidos y vibraciones al frenar.", "Se revisa en cada cambio de pastillas."),
    "SPINDLE, TAPER": _q("Es el eje de la dirección: une la tijera inferior con la superior y permite que el manubrio gire.",
                         "Se revisa y se engrasa junto con los rodamientos de la dirección."),
    "SPRING, CLUTCH WEIGHT": _q("Son los resortes que mantienen cerradas las zapatas del clutch hasta que el motor sube de revoluciones.",
                                "Se revisan junto con las zapatas (cada 12.000 km aprox.)."),
    "SPRING, COIL": _q("Es un resorte del mecanismo de las válvulas."),
    "SPRING, COMPRESSION": _q("Es el resorte que mantiene la malla del aceite apretada en su lugar.", "Se revisa al limpiar la malla en el cambio de aceite."),
    "SPRING, PLUNGER": _q("Es un resorte del émbolo del cuerpo de aceleración."),
    "SPRING, SUB": _q("Es un resorte auxiliar dentro de la barra que ayuda a absorber el final del recorrido de la suspensión."),
    "SPRING, VALVE INNER": _q("Es el resorte que vuelve a cerrar la válvula después de que el árbol de levas la abre.", "Se revisa cuando se repara la culata."),
    "STOPPER": _q("Es un tope que limita hasta dónde se mueve una pieza."),
    "SUPPORT, PAD": _q("Es la lámina-resorte que mantiene las pastillas en posición y evita que vibren dentro del caliper.", "Se revisa en cada cambio de pastillas."),
    "SUPT. BRKT. ASSY": _q("Es el soporte del caliper: lo fija a la barra de la suspensión o al basculante."),
    "TERMINAL COMP": _q("Es un terminal eléctrico: la punta metálica que conecta un cable con un componente."),
    "TUBE, OUTER": _q("Es la botella de la suspensión: el tubo externo donde se desliza la barra cromada y donde va el aceite de la barra.",
                      "El aceite de las barras se cambia cada 20.000 km aprox."),
    "UNDER BRACKET COMP": _q("Es la tijera inferior: une las dos barras de la suspensión con el eje de la dirección."),
    "VALVE ROCKER ARM ASSY": _q("Es el balancín: la palanca que empuja la válvula para abrirla cuando el árbol de levas la acciona.",
                                "Se revisa al calibrar las válvulas (cada 6.000 km aprox.)."),
    "WIRE HARNESS ASSY": _q("Es el arnés eléctrico: el conjunto de cables que conecta todos los componentes eléctricos de la moto.",
                            "No tiene cambio; revisa que no esté pelado ni aplastado, sobre todo después de una caída."),
    "BOOT": _q("Es el guardapolvo de caucho de los pasadores del caliper: evita que entre agua y que se oxiden.", "Se revisa en cada cambio de pastillas."),
    "BRACKET, MASTER CYLINDER": _q("Es la abrazadera que sujeta la bomba de freno al manubrio."),
    "CAP, CLEANER CASE": _q("Es la tapa de la caja del filtro de aire: se quita para revisar o cambiar el filtro.", "Se abre cada 3.000 km para revisar el filtro."),
    "BAND": _q("Es una abrazadera plástica que mantiene los cables organizados y sujetos al chasis."),
    "BOLT, STUD": _q("Es un espárrago: una varilla roscada en los dos extremos que une el cilindro y la culata con el cárter.",
                     "No tiene cambio; se revisa la rosca cuando se desarma el motor."),
    "BOLT, CAP": _q("Es el tapón superior de la barra: la cierra arriba y sostiene el resorte.", "Se quita al cambiar el aceite de las barras."),
    "BOLT, LEVER": _q("Es el tornillo sobre el que gira la manigueta del freno.", "Engrásalo cada 6 meses para que la manigueta se mueva suave."),
    "BOLT, UNION": _q("Es el tornillo banjo: une la manguera de freno con la bomba o el caliper y deja pasar el líquido por dentro.",
                      "Cada vez que se afloja, se ponen arandelas de cobre nuevas para que no haya fugas."),
    "NUT, SELF-LOCKING": _q("Es una tuerca de seguridad: tiene un anillo que impide que se afloje con la vibración.",
                            "Se recomienda cambiarla cada vez que se desmonta, porque pierde su efecto de seguridad."),
}

# Piezas comunes que se explican según el sistema donde están.
_PIEZAS_SISTEMA = {
    "freno_del": "piezas del freno delantero, como el caliper, la bomba o sus soportes",
    "freno_tras": "piezas del freno trasero, como el caliper y sus soportes",
    "correa": "las piezas del variador y del clutch",
    "aceite": "la bomba de aceite y las tapas del sistema de lubricación",
    "filtro_aire": "la caja del filtro, los ductos y el cuerpo de aceleración",
    "bujia": "la culata, el cilindro y sus tapas",
    "motor": "el mecanismo de las válvulas",
    "refrigeracion": "el radiador, sus mangueras y protecciones",
    "llanta_del": "la rueda delantera y sus accesorios, como el sensor del ABS",
    "llanta_tras": "la rueda trasera y sus accesorios",
    "suspension_del": "la suspensión delantera y la dirección",
    "suspension_tras": "el basculante, los amortiguadores y sus soportes",
    "bateria": "los componentes eléctricos y sus soportes",
}


def _de(sistema):
    if not sistema:
        return "de esta parte de la moto"
    return ("del " + sistema[3:]) if sistema.startswith("el ") else f"de {sistema}"


def _comunes(clave, pieza):
    """Descripción de piezas comunes (tornillería, empaques, etc.) según su tipo y su sistema."""
    piezas = _PIEZAS_SISTEMA.get(pieza, "piezas de esta parte de la moto")
    de_sis = _de(SISTEMAS.get(pieza))
    palabra = re.split(r"[ ,]", clave, maxsplit=1)[0]
    if palabra == "BOLT":
        texto = f"Es un tornillo que sujeta {piezas}."
        if "FLANGE" in clave:
            texto += " Trae la arandela incorporada para repartir la fuerza del apriete."
        if "HEXAGON SOCKET" in clave:
            texto += " Se aprieta con llave Allen, por eso se usa donde hay poco espacio."
        return texto
    if palabra.startswith("SCREW"):
        texto = f"Es un tornillo pequeño que fija {piezas}."
        if "TAPPING" in clave:
            texto += " Es autorroscante: abre su propia rosca, por eso se usa en piezas plásticas."
        if "FLAT HEAD" in clave:
            texto += " Su cabeza queda al ras de la superficie."
        if "WASHER" in clave:
            texto += " Trae la arandela incorporada."
        return texto
    if palabra == "NUT":
        return f"Es una tuerca que asegura {piezas}."
    if palabra == "WASHER":
        texto = "Es una arandela: va entre el tornillo o la tuerca y la pieza, reparte la fuerza del apriete y protege la superficie."
        return texto + (" Tiene una forma especial para esta posición." if "SPECIAL" in clave else "")
    if palabra == "O-RING":
        return f"Es un anillo de caucho que sella la unión entre dos piezas {de_sis}, para que no haya fugas."
    if palabra == "GASKET":
        return f"Es un empaque que sella la unión entre dos piezas {de_sis}, para que no haya fugas."
    if palabra == "SEAL":
        return f"Es un sello que evita que entre suciedad o que se salga el lubricante en {piezas}."
    if palabra == "CLIP":
        return f"Es una grapa que mantiene fija en su lugar una pieza {de_sis}."
    if palabra in ("CIRCLIP", "RING"):
        return f"Es un pin seguro: un anillo elástico que evita que una pieza {de_sis} se salga de su eje."
    if palabra in ("COLLAR", "BUSH", "SPACER"):
        return f"Es un buje: un separador que mantiene la distancia correcta entre piezas {de_sis} y les sirve de guía."
    if palabra == "CLAMP" or clave.startswith("HOSE CLAMP"):
        return f"Es una abrazadera que sujeta una manguera o un cable {de_sis} para que no se suelte."
    if palabra in ("GROMMET", "DAMPER"):
        return f"Es un caucho que amortigua vibraciones y evita que las piezas {de_sis} se golpeen o rocen."
    if palabra == "PIPE":
        return {"refrigeracion": "Es una manguera del sistema de refrigeración: lleva el refrigerante entre el motor y el radiador.",
                "filtro_aire": "Es una manguera del sistema de admisión de aire."}.get(pieza, f"Es una manguera {de_sis}.")
    if palabra == "HOLDER":
        return f"Es un soporte o grapa que mantiene en su sitio un componente {de_sis}."
    if palabra in ("PLATE", "STAY", "BRACKET"):
        return f"Es una placa o soporte metálico que sujeta un componente {de_sis}."
    if palabra in ("CAP", "COVER", "PLUG"):
        return f"Es una tapa que cubre y protege una parte {de_sis}."
    return None


_QUE_HACE = {_normalizar(k): v for k, v in QUE_HACE.items()}
_ALIAS = {"DISK, REAR BRAKE": "DISK, BRAKE", "FRONT STOP SWITCH ASSY": "STOP SWITCH"}
_GENERICOS = {v["que_hace"] for v in CATEGORIAS.values()}


def que_hace_especifico(descripcion, pieza=""):
    """Devuelve (que_hace, cada_cuanto) específicos, o (None, None) si la pieza ya tiene guía propia."""
    clave = _normalizar(descripcion)
    if clave in _QUE_HACE:
        dato = _QUE_HACE[clave]
    else:
        candidatos = [k for k in _QUE_HACE if clave.startswith(k + ",") or clave.startswith(k + " ") or clave == k]
        dato = _QUE_HACE[max(candidatos, key=len)] if candidatos else None
    if dato:
        return dato["que_hace"], dato["cada_cuanto"]
    return _comunes(clave, pieza), None
