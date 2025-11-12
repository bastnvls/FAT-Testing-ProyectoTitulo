from funcionalidades.colores import resaltado_fallido, resaltado_na, resaltado_ok, resaltado_opcional
from ..list_fallidas import fallidas

def prueba_1_ie3300():
    mapa_colores = {}
    pt_todas = [
        'PID:',
        'SN:',
    ]
    pt_unicas = [
        'Inicio Prueba 1',
        'show version',
        'show ver',
        'sh version',
        'sh ver',
        'Version',
        'uptime is',
        'Model number',
        'System serial number',
        'show inventory',
        'show inv',
        'sh inventory',
        'sh inv',
        'Fin Prueba 1',
    ]
    pt_linea = [
        'uptime is',
        'Model number',
        'System serial number',
    ]
    pt_to_end = [
        'Version',
        'SN:',
    ]
    pt_until_comma = [
        'PID:',
    ]
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


def prueba_2_ie3300():
    mapa_colores = {}
    pt_todas = [
        '  OK',
        'Disabled',
    ]
    pt_unicas = [
        'Inicio Prueba 2',
        'show environment power',
        'show env power',
        'sh env power',
        'sh environment power',
        'Fin prueba 2',
    ]
    pt_linea = [
        'Disabled',
        '  OK',
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
    mapa_colores['disabled'] = resaltado_na

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

def prueba_3_ie3300():
    mapa_colores = {}
    pt_todas = []
    pt_unicas = [
        'Inicio Prueba 3',
        'Fin prueba 3',
    ]
    pt_linea = [
        'Inicio Prueba 3',
        'Fin prueba 3',
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
        'Inicio Prueba 3',
        'Fin prueba 3',
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

def prueba_4_ie3300():
    mapa_colores = {}
    pt_todas = []
    pt_unicas = [
        'Inicio Prueba 4',
        'show environment temperature',
        'show env temp',
        'sh env temp',
        'sh environment temperature',
        'Temperature state',
        'Fin prueba 4',
    ]
    pt_linea = [
        'Temperature state',
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


def prueba_5_ie3300():
    mapa_colores = {}
    pt_todas = ['uptime is',]
    pt_unicas = [
        'Inicio Prueba 5',
        'reload',
        'Initializing file systems',
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
        'Fin prueba 5',
    ]
    pt_linea = [
        'Initializing file systems',
        'uptime is',
        'Model Number',
        'System Serial Number',
    ]
    pt_to_end = []
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = [
        ('Model Number',2),
        ('System Serial Number',2)
    ]
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

def prueba_6_ie3300():
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
        'INICIO PRUEBA 6',
        'show inventory all',
        'show inv all',
        'sh inventory all',
        'sh inv all',
        'show interface ethernet',
        'sh int eth',
        'sh int ethernet',
        'show int eth',
        'show int ethernet',
        'FIN PRUEBA 6',
    ]
    pt_linea = [
        'PID: SFP',
    ]
    pt_to_end = [
        'show interface ethernet',
        'sh int eth',
        'sh int ethernet',
        'show int eth',
        'show int ethernet',
    ]
    pt_until_comma = [
        'Name: Ethernet',
        'Name: GigabitEthernet',
        'Name: TenGigabitEthernet',
        'Name: TwentyFiveGigE',
        'Name: FortyGigE',
        'PID: SFP',
    ]
    pt_derecha_excluyendo =[]
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