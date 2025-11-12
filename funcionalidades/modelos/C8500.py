from funcionalidades.colores import resaltado_fallido, resaltado_na, resaltado_ok, resaltado_opcional
from ..list_fallidas import fallidas

def prueba_1_C8500():
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
        'cisco C8500',
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
        'Version',
    ]
    pt_until_comma  = [
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

def prueba_2_C8500():
    mapa_colores = {}  
    pt_todas = [
    ' P0          Vin',
    ' P0          Iin',
    ' P0          Vout',
    ' P0          Iout',
    ' P1          Vin',
    ' P1          Iin',
    ' P1          Vout',
    ' P1          Iout',
    ' P2          Vin',
    ' P2          Iin',
    ' P2          Vout',
    ' P2          Iout',
    ' P3          Vin',
    ' P3          Iin',
    ' P3          Vout',
    ' P3          Iout',
    'The PEM in slot P0 is switched off',
    'The PEM in slot P1 is switched off',
    'The PEM in slot P2 is switched off',
    'The PEM in slot P3 is switched off',
    'The Power Supply in slot P0 is switched off',
    'The Power Supply in slot P1 is switched off',
    'The Power Supply in slot P2 is switched off',
    'The Power Supply in slot P3 is switched off',
    'The PEM in slot P0 is functioning properly',
    'The PEM in slot P1 is functioning properly',
    'The PEM in slot P2 is functioning properly',
    'The PEM in slot P3 is functioning properly',
    ]
    pt_unicas = [
        'INICIO PRUEBA 2',
        'show environment summary',
        'show env summary',
        'sh env summary',
        'sh environment summary',
        'FIN PRUEBA 2',
    ]
    pt_linea = [
    ' P0          Vin',
    ' P0          Iin',
    ' P0          Vout',
    ' P0          Iout',
    ' P1          Vin',
    ' P1          Iin',
    ' P1          Vout',
    ' P1          Iout',
    ' P2          Vin',
    ' P2          Iin',
    ' P2          Vout',
    ' P2          Iout',
    ' P3          Vin',
    ' P3          Iin',
    ' P3          Vout',
    ' P3          Iout',
    ]
    pt_to_end = [
    'The PEM in slot P0 is switched off',
    'The PEM in slot P1 is switched off',
    'The PEM in slot P2 is switched off',
    'The PEM in slot P3 is switched off',
    'The Power Supply in slot P0 is switched off',
    'The Power Supply in slot P1 is switched off',
    'The Power Supply in slot P2 is switched off',
    'The Power Supply in slot P3 is switched off',
    'The PEM in slot P0 is functioning properly',
    'The PEM in slot P1 is functioning properly',
    'The PEM in slot P2 is functioning properly',
    'The PEM in slot P3 is functioning properly',
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
        'The PEM in slot P0 is switched off',
        'The PEM in slot P1 is switched off',
        'The PEM in slot P2 is switched off',
        'The PEM in slot P3 is switched off',
        'The Power Supply in slot P0 is switched off',
        'The Power Supply in slot P1 is switched off',
        'The Power Supply in slot P2 is switched off',
        'The Power Supply in slot P3 is switched off',
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

def prueba_3_C8500():
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

def prueba_4_C8500():
    mapa_colores = {}  
    pt_todas = []
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
    pt_n_coincidencia     = [
        ('Processor Board ID',2),
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


def prueba_5_C8500():
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