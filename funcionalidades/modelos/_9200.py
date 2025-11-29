from funcionalidades.colores import resaltado_fallido, resaltado_na, resaltado_ok, resaltado_opcional
from ..list_fallidas import fallidas

def prueba_1_9200():
    mapa_colores = {}
    pt_todas = [
        'DESCR',
        'PID',
        'SN',
    ]
    pt_unicas = [
        'Inicio Prueba 1',
        'show version',
        'Version',
        'uptime is',
        'Model Number',
        'System Serial Number',
        'show inventory',
        'sh inv',
        'Fin Prueba 1',
    ]
    pt_linea = [
        'uptime is',
    ]
    pt_to_end = [
        'Show version',
        'Version',
        'Model Number',
        'System Serial Number',
        'DESCR',
        'SN',
    ]
    pt_until_comma = ['PID', 'DESCR', 'SN']
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
    # Definimos explícitamente qué estilo usar por palabra
    for w in pt_todas + pt_unicas:
        mapa_colores[w.lower()] = resaltado_ok

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


def prueba_2_9200():
    mapa_colores = {}
    pt_todas = [
        '1A',
        '1B',
        '1C',
        '1D',
        ' Not Present',
        ' OK ',
        #CONECTADA
        'FRU power supply A inserted',
        'FRU power supply B inserted',
        'FRU power supply C inserted',
        'FRU power supply D inserted',
        'signal on power supply A is restored',
        'signal on power supply B is restored',
        'signal on power supply C is restored',
        'signal on power supply D is restored',

        #DESCONECTADA
        'FRU power supply A removed',
        'FRU power supply B removed',
        'FRU power supply C removed',
        'FRU power supply D removed',
        'signal on power supply A is faulty',
        'signal on power supply B is faulty',
        'signal on power supply C is faulty',
        'signal on power supply D is faulty',
    ]
    pt_unicas = [
        'INICIO PRUEBA 2',
        'show environment power',
        'FIN PRUEBA 2',
    ]
    pt_linea = [
        ' Not Present',
    ]
    pt_to_end = []
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
    # Definimos explícitamente qué estilo usar por palabra
    for w in pt_todas + pt_unicas:
        mapa_colores[w.lower()] = resaltado_ok
    # Sobrescribimos ciertas claves a NA
    for clave in [
        ' Not Present',
        'FRU power supply A removed',
        'FRU power supply B removed',
        'FRU power supply C removed',
        'FRU power supply D removed',
        'signal on power supply A is faulty',
        'signal on power supply B is faulty',
        'signal on power supply C is faulty',
        'signal on power supply D is faulty',
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


def prueba_3_9200():
    mapa_colores = {}
    pt_todas = [
        ' OK ',
        'NOT PRESENT or FAULTY',
    ]
    pt_unicas = [
        'INICIO PRUEBA 3',
        'show environment fan',
        'System fan 1 failed',
        'System fan 1 recovered to normal status',
        'System fan 2 failed',
        'System fan 2 recovered to normal status',
        'System fan 3 failed',
        'System fan 3 recovered to normal status',
        'System fan 4 failed',
        'System fan 4 recovered to normal status',
        'FIN PRUEBA 3',
    ]
    pt_linea = [
        'NOT PRESENT or FAULTY',
    ]
    pt_to_end = []
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
    # Definimos explícitamente qué estilo usar por palabra
    for w in pt_todas + pt_unicas:
        mapa_colores[w.lower()] = resaltado_ok
    for clave in [
        'NOT PRESENT or FAULTY',
        'System fan 1 failed',
        'System fan 2 failed',
        'System fan 3 failed',
        'System fan 4 failed',
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


def prueba_4_9200():
    mapa_colores = {}
    pt_todas = []
    pt_unicas = [
        'INICIO PRUEBA 4',
        '#reload',
        '>reload',
        'show version',
        'uptime is',
        'Initializing Hardware',
        '>enable',
        'Cisco IOS XE Software, ',
        'FIN PRUEBA 4',
    ]
    pt_linea = [
        'uptime is',
        'Initializing Hardware',
        'Model Number',
        'System Serial Number',
    ]
    pt_to_end = []
    pt_until_comma = []
    pt_derecha_excluyendo = ['Cisco IOS XE Software, ']
    pt_entre_dos = []
    pt_n_coincidencia     = [
        ('Model Number',2),
        ('System Serial Number',2),
    ]
    pt_todas = fallidas + pt_todas
    # Definimos explícitamente qué estilo usar por palabra
    for w in pt_todas + pt_unicas:
        mapa_colores[w.lower()] = resaltado_ok
    mapa_colores['not present'] = resaltado_na

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


def prueba_5_9200():
    mapa_colores = {}
    pt_todas = [
        'Name: Ethernet',
        'Name: GigabitEthernet',
        'Name: TenGigabitEthernet',
        'Name: TwentyFiveGigE',
        'Name: FortyGigE',
        'PID: SFP',
    ]
    pt_unicas = [
        'INICIO PRUEBA 5',
        'show inventory',
        'show interfaces',
        'FIN PRUEBA 5',
    ]
    pt_linea = [
        'PID: SFP',
    ]
    pt_to_end = [
        'show interfaces',
    ]
    pt_until_comma = [
        'Name: Ethernet',
        'Name: GigabitEthernet',
        'Name: TenGigabitEthernet',
        'Name: TwentyFiveGigE',
        'Name: FortyGigE',
        'PID: SFP',
    ]
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
    # Definimos explícitamente qué estilo usar por palabra
    for w in pt_todas + pt_unicas:
        mapa_colores[w.lower()] = resaltado_opcional

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