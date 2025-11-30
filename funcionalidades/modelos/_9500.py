from funcionalidades.colores import resaltado_fallido, resaltado_na, resaltado_ok, resaltado_opcional
from ..list_fallidas import fallidas

def prueba_1_9500():
    mapa_colores = {}
    pt_todas = [
        'PID',
        'SN',
        'NAME: "Power Supply ',
        'NAME: "Fan Tray ',
    ]
    pt_unicas = [
        'INICIO PRUEBA 1',
        'show version',
        'Version',
        'uptime is',
        'Model Number',
        'System Serial Number',
        'show inventory',
        'FIN PRUEBA 1',
    ]
    pt_linea = [
        'uptime is',
        'Model Number',
        'System Serial Number',
    ]
    pt_to_end = [
        'Version',
    ]
    pt_until_comma  = [
        'PID',
        'SN',
        'NAME: "Power Supply ',
        'NAME: "Fan Tray ',
    ]
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
    # Colores
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


def prueba_2_9500():
    mapa_colores = {}
    pt_todas = [
        ' OK ',
        'PS0',
        'PS1',
        'PS2',
        'PS3',
        '    fail    ',

        #CONECTADA
        'The Power Supply in slot P0 is functioning properly',
        'The Power Supply in slot P1 is functioning properly',
        'The Power Supply in slot P2 is functioning properly',
        'The Power Supply in slot P3 is functioning properly',
        'PEM/FM slot P0 inserted',
        'PEM/FM slot P1 inserted',
        'PEM/FM slot P2 inserted',
        'PEM/FM slot P3 inserted',
        
        #DESCONECTADA
        'The Power Supply in slot P0 is switched off',
        'The Power Supply in slot P1 is switched off',
        'The Power Supply in slot P2 is switched off',
        'The Power Supply in slot P3 is switched off',
        'The Power Supply in slot P0 is switched off or encountering a failure condition',
        'The Power Supply in slot P1 is switched off or encountering a failure condition',
        'The Power Supply in slot P2 is switched off or encountering a failure condition',
        'The Power Supply in slot P3 is switched off or encountering a failure condition',
        'Power Supply/Fantray module slot P0 removed',
        'Power Supply/Fantray module slot P1 removed',
        'Power Supply/Fantray module slot P2 removed',
        'Power Supply/Fantray module slot P3 removed',
    ]
    pt_unicas = [
        'INICIO PRUEBA 2',
        'show environment status',
        'FIN PRUEBA 2',
    ]
    pt_linea = [
        '    fail    ',
    ]
    pt_to_end = [
        'The Power Supply in slot P0 is functioning properly',
        'The Power Supply in slot P1 is functioning properly',
        'The Power Supply in slot P2 is functioning properly',
        'The Power Supply in slot P3 is functioning properly',
        'PEM/FM slot P0 inserted',
        'PEM/FM slot P1 inserted',
        'PEM/FM slot P2 inserted',
        'PEM/FM slot P3 inserted',
        'The Power Supply in slot P0 is switched off',
        'The Power Supply in slot P1 is switched off',
        'The Power Supply in slot P2 is switched off',
        'The Power Supply in slot P3 is switched off',
        'The Power Supply in slot P0 is switched off or encountering a failure condition',
        'The Power Supply in slot P1 is switched off or encountering a failure condition',
        'The Power Supply in slot P2 is switched off or encountering a failure condition',
        'The Power Supply in slot P3 is switched off or encountering a failure condition',
        'Power Supply/Fantray module slot P0 removed',
        'Power Supply/Fantray module slot P1 removed',
        'Power Supply/Fantray module slot P2 removed',
        'Power Supply/Fantray module slot P3 removed',
    ]
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
    # Colores
    for w in pt_todas + pt_unicas:
        mapa_colores[w.lower()] = resaltado_ok
    
    for clave in [
        'The Power Supply in slot P0 is switched off',
        'The Power Supply in slot P1 is switched off',
        'The Power Supply in slot P2 is switched off',
        'The Power Supply in slot P3 is switched off',
        'The Power Supply in slot P0 is switched off or encountering a failure condition',
        'The Power Supply in slot P1 is switched off or encountering a failure condition',
        'The Power Supply in slot P2 is switched off or encountering a failure condition',
        'The Power Supply in slot P3 is switched off or encountering a failure condition',
        'Power Supply/Fantray module slot P0 removed',
        'Power Supply/Fantray module slot P1 removed',
        'Power Supply/Fantray module slot P2 removed',
        'Power Supply/Fantray module slot P3 removed',
        '    fail    ',
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


def prueba_3_9500():
    mapa_colores = {}
    pt_todas = [
        '  OK  ',
        '  N/A         N/A   N/A   N/A   N/A',
        'FM0  ',
        'FM1  ',
        'FM2  ',
        'Fantray module slot FM0 removed',
        'Fantray module slot FM1 removed',
        'Fantray module slot FM2 removed',
        'Fantray module slot FM3 removed',
        'Fantray module slot FM0 inserted',
        'Fantray module slot FM1 inserted',
        'Fantray module slot FM2 inserted',
        'Fantray module slot FM3 inserted',
        'Fantray in slot FM0 removed',
        'Fantray in slot FM0 inserted',
        'Fantray in slot FM1 removed',
        'Fantray in slot FM1 inserted',
        'Fantray in slot FM2 removed',
        'Fantray in slot FM2 inserted',
        'Fantray in slot FM3 removed',
        'Fantray in slot FM3 inserted',
    ]
    
    pt_unicas = [
        'INICIO PRUEBA 3',
        'show environment status',
        'FIN PRUEBA 3',
    ]
    pt_linea = [
        '  N/A         N/A   N/A   N/A   N/A',
    ]
    pt_to_end = [
        'Fantray module slot FM0 removed',
        'Fantray module slot FM1 removed',
        'Fantray module slot FM2 removed',
        'Fantray module slot FM3 removed',
        'Fantray module slot FM0 inserted',
        'Fantray module slot FM1 inserted',
        'Fantray module slot FM2 inserted',
        'Fantray module slot FM3 inserted',
    ]
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
    # Colores
    for w in pt_todas + pt_unicas:
        mapa_colores[w.lower()] = resaltado_ok

    for clave in [
        '  N/A         N/A   N/A   N/A   N/A',
        'Fantray module slot FM0 removed',
        'Fantray module slot FM1 removed',
        'Fantray module slot FM2 removed',
        'Fantray module slot FM3 removed'
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

def prueba_4_9500():
    pt_todas = [
        'NOT PRESENT or FAULTY',
        '  OK  ',
    ]
    pt_unicas = [
        'INICIO PRUEBA 4',
        'reload',
        'Initializing Hardware',
        '>enable',
        '#enable',
        'show version',
        'uptime is',
        'Cisco IOS XE Software,',
        'FIN PRUEBA 4',
    ]
    pt_linea = [
        'Initializing Hardware',
        'uptime is',
        'Model Number',
        'System Serial Number',
    ]
    pt_to_end             = []
    pt_until_comma        = []
    pt_derecha_excluyendo = ['Cisco IOS XE Software,']
    pt_entre_dos          = []
    pt_n_coincidencia     = [
        ('Model Number',2),
        ('System Serial Number',2),
    ]
    pt_todas = fallidas + pt_todas
    mapa_colores = {}
    for palabra in pt_todas:
        mapa_colores[palabra.lower()] = resaltado_ok
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


def prueba_5_9500():
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
        'show interface',
        'FIN PRUEBA 5',
    ]
    pt_linea = [
        'PID: SFP',
    ]
    pt_to_end = [
        'show interface',
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
    # Colores
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