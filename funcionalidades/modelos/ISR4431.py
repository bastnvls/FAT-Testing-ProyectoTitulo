from funcionalidades.colores import resaltado_fallido, resaltado_na, resaltado_ok, resaltado_opcional
from ..list_fallidas import fallidas

def prueba_1_ISR4431():
    mapa_colores = {}  
    pt_todas = [
        'NAME: "Power Supply ',
        'NAME: "Fan Tray',
        'PID: ',
        'SN: ',
    ]
    pt_unicas = [
        'INICIO PRUEBA 1',
        'show version',
        'show ver',
        'sh version',
        'sh ver',
        'Version',
        'uptime is',
        'cisco ISR4431',
        'Processor board ID ',
        'show inventory',
        'show inv',
        'sh inventory',
        'sh inv',
        'FIN PRUEBA 1',
    ]
    pt_linea = [
        'uptime is',
        'Processor board ID ',
    ]
    pt_to_end = [
        'SN: ',
    ]
    pt_until_comma  = [
        'Version',
        'NAME: "Power Supply ',
        'NAME: "Fan Tray',
        'PID: ',
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

def prueba_2_ISR4431():
    mapa_colores = {}  
    pt_todas = [
        'RPM: fan0        P0',
        'RPM: fan0        P1',
        'RPM: fan0        P2',
        'RPM: fan0        P3',
        'RPM: fan1        P0',
        'RPM: fan1        P1',
        'RPM: fan1        P2',
        'RPM: fan1        P3',
        'RPM: fan2        P0',
        'RPM: fan2        P1',
        'RPM: fan2        P2',
        'RPM: fan2        P3',
        'RPM: fan3        P0',
        'RPM: fan3        P1',
        'RPM: fan3        P2',
        'RPM: fan3        P3',
    ]
    pt_unicas = [
        'INICIO PRUEBA 2',
        'show environment all',
        'show env all',
        'sh environment all',
        'sh env all',
        'FIN PRUEBA 2',
    ]
    pt_linea = [
        'RPM: fan0        P0',
        'RPM: fan0        P1',
        'RPM: fan0        P2',
        'RPM: fan0        P3',
        'RPM: fan1        P0',
        'RPM: fan1        P1',
        'RPM: fan1        P2',
        'RPM: fan1        P3',
        'RPM: fan2        P0',
        'RPM: fan2        P1',
        'RPM: fan2        P2',
        'RPM: fan2        P3',
        'RPM: fan3        P0',
        'RPM: fan3        P1',
        'RPM: fan3        P2',
        'RPM: fan3        P3',
    ]
    pt_to_end = []
    pt_until_comma  = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
    # Definimos explícitamente qué estilo usar por palabra
    for w in pt_todas + pt_unicas:
        mapa_colores[w.lower()] = resaltado_ok
    clave = ' Shutdown'.lower()
    mapa_colores[clave] = resaltado_na

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

def prueba_3_ISR4431():
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
    pt_to_end = [
    ]
    pt_until_comma  = []
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

def prueba_4_ISR4431():
    mapa_colores = {}  
    pt_todas = [
        'Processor Board ID',
    ]
    pt_unicas = [
        'INICIO PRUEBA 4',
        'reload',
        '>enable',
        '>ena',
        '>en',
        '> en',
        '> enable',
        '> ena',
        'Initializing Hardware',
        'show version',
        'show ver',
        'sh version',
        'sh ver',
        'uptime is',
        'FIN PRUEBA 4',
    ]
    pt_linea = [
        'Initializing Hardware',
        'uptime is',
        'Processor Board ID',
    ]
    pt_to_end = [
        '>enable',
        '>ena',
        '>en',
        '> en',
        '> enable',
        '> ena',
    ]
    pt_until_comma  = []
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


def prueba_5_ISR4431():
    mapa_colores = {}  
    pt_todas = [
        'Name: Ethernet',
        'Name: GigabitEthernet',
        'Name: TenGigabitEthernet',
        'Name: TwentyFiveGigE',
        'Name: FortyGigE',
        'PID: SFP'
        ]
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
    pt_until_comma  = [
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