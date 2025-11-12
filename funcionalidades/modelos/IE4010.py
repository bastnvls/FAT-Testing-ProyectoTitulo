from funcionalidades.colores import resaltado_fallido, resaltado_na, resaltado_ok, resaltado_opcional
from ..list_fallidas import fallidas

def prueba_1_ie4010():
    mapa_colores = {}
    pt_todas = [
        'Name:',
        'PID',
        'SN'
    ]
    pt_unicas = [
        'Inicio Prueba 1',
        'show version',
        'show ver',
        'sh version',
        'sh ver',
        'uptime is',
        'Model Number',
        'System Serial Number',
        ', Version',
        'show inventory',
        'show inv',
        'sh inventory',
        'sh inv',
        'Fin Prueba 1',
    ]
    pt_linea = [
        'uptime is',
        'Model Number',
        'System Serial Number',
    ]
    pt_to_end = [
        'SN'
    ]
    pt_until_comma = [
        'Name:',
        'PID',
        ', Version',
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


def prueba_2_ie4010():
    mapa_colores = {}
    pt_todas = [
        '1A',
        '1B',
        '1C',
        '1D',
        ' OK  ',
        ' Disabled  ',
    ]
    pt_unicas = [
        'Inicio Prueba 2',
        'show environment power',
        'show env power',
        'sh environment power',
        'sh env power',
        'FRU Power Supply 1 powered off',
        'Power supply 1 is functioning',
        'FRU Power Supply 2 powered off',
        'Power supply 2 is functioning',
        'FRU Power Supply 3 powered off',
        'Power supply 3 is functioning',
        'FRU Power Supply 4 powered off',
        'Power supply 4 is functioning',
        'Fin Prueba 2',
    ]
    pt_linea = [
        ' Disabled  ',
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
        ' Disabled  ',
        'FRU Power Supply 1 powered off',
        'FRU Power Supply 2 powered off',
        'FRU Power Supply 3 powered off',
        'FRU Power Supply 4 powered off',
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

def prueba_3_ie4010():
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

def prueba_4_ie4010():
    mapa_colores = {}
    pt_todas = [
        'Power Supply'
    ]
    pt_unicas = [
        'Inicio Prueba 4',
        'show environment temperature',
        'show env temperature',
        'show env temp',
        'sh env temp',
        'sh environment temperature',
        'Fin Prueba 4',
    ]
    pt_linea = [
        'Power Supply'
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


def prueba_5_ie4010():
    mapa_colores = {}
    pt_todas = []
    pt_unicas = [
        'Inicio Prueba 5',
        'Fin Prueba 5',
        'reload',
        'Initializing Flash',
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
    ]
    pt_linea = [
        'Initializing Flash',
        'uptime is',
        'Model Number',
        'System Serial Number',
    ]
    pt_to_end = []
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia     = [
        ('Model Number',2),
        ('System Serial Number',2),
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


def prueba_6_ie4010():
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