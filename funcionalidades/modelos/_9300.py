from funcionalidades.colores import resaltado_fallido, resaltado_na, resaltado_ok, resaltado_opcional
from ..list_fallidas import fallidas

def prueba_1_9300():
    """
    Prepara las listas de palabras y el mapa de colores
    para la prueba 1 del dispositivo 9300.
    """
    # 1. Palabras generales a buscar → resaltado OK, full‐line
    pt_todas = [
        'DESCR',
        'PID',
        'SN',
    ]
    # 2. Palabras únicas → resaltado OK, from word to end
    pt_unicas = [
        'INICIO PRUEBA 1',
        'show version',
        'show ver',
        'sh version',
        'sh ver',
        'Version',
        'uptime is',
        'Model Number',
        'System Serial Number',
        'show inventory',
        'show inv',
        'sh inventory',
        'sh inv',
        'FIN PRUEBA 1',
    ]
    # 3. Qué dispara full‐line
    pt_linea = [
        'uptime is',
        'Model Number',
        'System Serial Number',
    ]
    # 4. Comportamientos especiales
    pt_to_end             = ['Version']
    pt_until_comma        = ['DESCR', 'PID', 'SN']
    pt_derecha_excluyendo = []
    pt_entre_dos          = []
    pt_n_coincidencia     = []
    pt_todas = fallidas + pt_todas
    # 6. Mapa de colores (clave=palabra.lower())
    mapa_colores = {}
    # 6.1. OK para todas las palabras de pt_todas
    for palabra in pt_todas:
        mapa_colores[palabra.lower()] = resaltado_ok
    # 6.2. OK para palabras únicas (base)
    for palabra in pt_unicas:
        mapa_colores[palabra.lower()] = resaltado_ok

    for fallo in fallidas:
        mapa_colores[fallo.lower()] = resaltado_fallido

    return (
        pt_todas,
        pt_unicas,
        pt_linea,
        pt_to_end,
        pt_until_comma,
        pt_derecha_excluyendo,
        mapa_colores,
        pt_entre_dos,
        pt_n_coincidencia,

    )

def prueba_2_9300():
    """
    Prepara las listas de palabras y el mapa de colores
    para la prueba 2 del dispositivo 9300.
    """
    # 1. Palabras generales a buscar → resaltado OK, full‐line
    pt_todas = [
        ' OK ',
        '1A',
        '1B',
        '1C',
        '1D',
        #CONECTADA
        'power supply A is responding',
        'power supply B is responding',
        'power supply C is responding',
        'power supply D is responding',
        'signal on power supply A is restored',
        'signal on power supply B is restored',
        'signal on power supply C is restored',
        'signal on power supply D is restored',

        #DESCONECTADA
        'power supply A is not responding',
        'power supply B is not responding',
        'power supply A is not responding',
        'power supply D is not responding',
        'signal on power supply A is faulty',
        'signal on power supply B is faulty',
        'signal on power supply C is faulty',
        'signal on power supply D is faulty',
        ' No Input Power ',
    ]
    # 2. Palabras únicas → resaltado OK, from word to end
    pt_unicas = [
        'INICIO PRUEBA 2',
        'show environment power',
        'show env power',
        'sh env power',
        'sh environment power',
        'FIN PRUEBA 2',
    ]
    # 3. Qué dispara full‐line
    pt_linea = [
        ' No Input Power ',
    ]
    # 4. Comportamientos especiales
    pt_to_end             = []
    pt_until_comma        = []
    pt_derecha_excluyendo = []
    pt_entre_dos          = []
    pt_n_coincidencia     = []
    pt_todas = fallidas + pt_todas
    # 6. Mapa de colores (clave=palabra.lower())
    mapa_colores = {}
    # 6.1. OK para todas las palabras de pt_todas
    for palabra in pt_todas:
        mapa_colores[palabra.lower()] = resaltado_ok
    # 6.2. OK para palabras únicas (base)
    for palabra in pt_unicas:
        mapa_colores[palabra.lower()] = resaltado_ok
    # 6.3. NA para ciertos casos específicos
    for clave in [
        'power supply A is not responding',
        'power supply B is not responding',
        'power supply A is not responding',
        'power supply D is not responding',
        'signal on power supply A is faulty',
        'signal on power supply B is faulty',
        'signal on power supply C is faulty',
        'signal on power supply D is faulty',
        ' No Input Power ',
        ]:
        mapa_colores[clave.lower()] = resaltado_na
    
    for fallo in fallidas:
        mapa_colores[fallo.lower()] = resaltado_fallido
    return (
        pt_todas,
        pt_unicas,
        pt_linea,
        pt_to_end,
        pt_until_comma,
        pt_derecha_excluyendo,
        mapa_colores,
        pt_entre_dos,
        pt_n_coincidencia,
    )

def prueba_3_9300():
    """
    Prepara las listas de palabras y el mapa de colores
    para la prueba 3 del dispositivo 9300.
    """
    # 1. Palabras generales a buscar → resaltado OK, full‐line
    pt_todas = [
        '  NOT PRESENT or FAULTY  ',
        '  OK  ',
        'System fan 1 faulty or removed',
        'System fan 2 faulty or removed',
        'System fan 3 faulty or removed',
        'System fan 4 faulty or removed',
        'System fan 1 inserted or recovered',
        'System fan 2 inserted or recovered',
        'System fan 3 inserted or recovered',
        'System fan 4 inserted or recovered',
    ]
    # 2. Palabras únicas → resaltado OK, from word to end
    pt_unicas = [
        'INICIO PRUEBA 3',
        'show environment fan',
        'show env fan',
        'sh env fan',
        'sh environment fan',
        'FIN PRUEBA 3',
    ]
    # 3. Qué dispara full‐line
    pt_linea = [
        '  NOT PRESENT or FAULTY  ',
    ]
    # 4. Comportamientos especiales
    pt_to_end             = []
    pt_until_comma        = []
    pt_derecha_excluyendo = []
    pt_entre_dos          = []
    pt_n_coincidencia     = []
    pt_todas = fallidas + pt_todas
    # 6. Mapa de colores (clave=palabra.lower())
    mapa_colores = {}
    # 6.1. OK para todas las palabras de pt_todas
    for palabra in pt_todas:
        mapa_colores[palabra.lower()] = resaltado_ok
    # 6.2. OK para palabras únicas (base)
    for palabra in pt_unicas:
        mapa_colores[palabra.lower()] = resaltado_ok
    # 6.3. NA para ciertos casos específicos
    for clave in [
        '  NOT PRESENT or FAULTY  ',
        'System fan 1 faulty or removed',
        'System fan 2 faulty or removed',
        'System fan 3 faulty or removed',
        'System fan 4 faulty or removed',
        ]:
        mapa_colores[clave.lower()] = resaltado_na

    for fallo in fallidas:
        mapa_colores[fallo.lower()] = resaltado_fallido
    return (
        pt_todas,
        pt_unicas,
        pt_linea,
        pt_to_end,
        pt_until_comma,
        pt_derecha_excluyendo,
        mapa_colores,
        pt_entre_dos,
        pt_n_coincidencia,

    )

def prueba_4_9300():
    """
    Prepara las listas de palabras y el mapa de colores
    para la prueba 4 del dispositivo 9300.
    """
    # 1. Palabras generales a buscar → resaltado OK, full‐line
    pt_todas = [
        'NOT PRESENT or FAULTY',
        '  OK  ',
        
    ]
    # 2. Palabras únicas → resaltado OK, from word to end
    pt_unicas = [
        'INICIO PRUEBA 4',
        'reload',
        'Initializing Hardware',
        '>enable',
        '>ena',
        '>en',
        '> en',
        '> enable',
        '> ena',
        'show version',
        'show ver',
        'sh version',
        'sh ver',
        'uptime is',
        'Cisco IOS XE Software,',
        'FIN PRUEBA 4',
    ]
    # 3. Qué dispara full‐line
    pt_linea = [
        'Initializing Hardware',
        'uptime is',
        'Model Number',
        'System Serial Number',
    ]
    # 4. Comportamientos especiales
    pt_to_end             = []
    pt_until_comma        = []
    pt_derecha_excluyendo = ['Cisco IOS XE Software,']
    pt_entre_dos          = []
    pt_n_coincidencia     = [
        ('Model Number',2),
        ('System Serial Number',2),
    ]
    pt_todas = fallidas + pt_todas
    # 6. Mapa de colores (clave=palabra.lower())
    mapa_colores = {}
    # 6.1. OK para todas las palabras de pt_todas
    for palabra in pt_todas:
        mapa_colores[palabra.lower()] = resaltado_ok
    # 6.2. OK para palabras únicas (base)
    for palabra in pt_unicas:
        mapa_colores[palabra.lower()] = resaltado_ok

    for fallo in fallidas:
        mapa_colores[fallo.lower()] = resaltado_fallido
    return (
        pt_todas,
        pt_unicas,
        pt_linea,
        pt_to_end,
        pt_until_comma,
        pt_derecha_excluyendo,
        mapa_colores,
        pt_entre_dos,
        pt_n_coincidencia,

    )

def prueba_5_9300():
    """
    Prepara las listas de palabras y el mapa de colores
    para la prueba 5 del dispositivo 9300.
    """
    # 1. Palabras generales a buscar → resaltado OK, full‐line
    pt_todas = [
        'Name: Ethernet',
        'Name: GigabitEthernet',
        'Name: TenGigabitEthernet',
        'Name: TwentyFiveGigE',
        'Name: FortyGigE',
        'PID: SFP',
    ]
    # 2. Palabras únicas → resaltado OK, from word to end
    pt_unicas = [
        'INICIO PRUEBA 5',
        'show inventory all',
        'show inv all',
        'sh inventory all',
        'sh inv all',
        'show interface ethernet',
        'sh int eth',
        'sh int ethernet',
        'show int eth',
        'show int ethernet',
        'FIN PRUEBA 5',
    ]
    # 3. Qué dispara full‐line
    pt_linea = []
    # 4. Comportamientos especiales
    pt_to_end             = [
        'show interface ethernet',
        'sh int eth',
        'sh int ethernet',
        'show int eth',
        'show int ethernet',
    ]
    pt_until_comma        = [
        'Name: Ethernet',
        'Name: GigabitEthernet',
        'Name: TenGigabitEthernet',
        'Name: TwentyFiveGigE',
        'Name: FortyGigE',
        'PID: SFP',
    ]
    pt_derecha_excluyendo = []
    pt_entre_dos          = []
    pt_n_coincidencia     = []
    pt_todas = fallidas + pt_todas
    # 6. Mapa de colores (clave=palabra.lower())
    mapa_colores = {}
    # 6.1. OK para todas las palabras de pt_todas
    for palabra in pt_todas:
        mapa_colores[palabra.lower()] = resaltado_opcional
    # 6.2. OK para palabras únicas (base)
    for palabra in pt_unicas:
        mapa_colores[palabra.lower()] = resaltado_opcional
    for fallo in fallidas:
        mapa_colores[fallo.lower()] = resaltado_fallido
    return (
        pt_todas,
        pt_unicas,
        pt_linea,
        pt_to_end,
        pt_until_comma,
        pt_derecha_excluyendo,
        mapa_colores,
        pt_entre_dos,
        pt_n_coincidencia,
    )