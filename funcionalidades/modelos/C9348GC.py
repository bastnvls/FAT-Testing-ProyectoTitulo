from funcionalidades.colores import resaltado_fallido, resaltado_na, resaltado_ok, resaltado_opcional
from ..list_fallidas import fallidas

def prueba_1_C9348GC():
    mapa_colores = {}
    pt_todas = [
        'DESCR: "Nexus9000 ',
        'PID',
        'SN',
        'NAME: "Power Supply ',
        'NAME: "Fan ',
    ]
    pt_unicas = [
        'INICIO PRUEBA 1',
        'show version',
        'show ver',
        'sh version',
        'sh ver',
        'uptime is',
        'NXOS: version',
        'Processor Board ID',
        'show inventory',
        'show inv',
        'sh inventory',
        'sh inv',
        'cisco Nexus9000',
        'FIN PRUEBA 1',
    ]
    pt_linea = [
        'uptime is',
        'Model Number',
        'System Serial Number',
    ]
    pt_to_end = [
        'NXOS: version',
        'Processor Board ID',
        'cisco Nexus9000',
    ]
    pt_until_comma = [
        'DESCR: "Nexus9000 ',
        'PID',
        'SN',
        'NAME: "Power Supply ',
        'NAME: "Fan ',
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


def prueba_2_C9348GC():
    mapa_colores = {}
    pt_todas = [
        '  Ok',
        ' Shutdown',

        #CONECTADA
        'Power supply 1 ok ',
        'Power supply 2 ok ',
        'Power supply 3 ok ',
        'Power supply 4 ok ',
        #DESCONECTADA
        'Power supply 1 removed',
        'Power supply 2 removed',
        'Power supply 3 removed',
        'Power supply 4 removed',
        'Power supply 1 detected but shutdown',
        'Power supply 2 detected but shutdown',
        'Power supply 3 detected but shutdown',
        'Power supply 4 detected but shutdown',
    ]
    pt_unicas = [
        'INICIO PRUEBA 2',
        'show environment power',
        'sh environment power',
        'show env power',
        'sh env power',
        'FIN PRUEBA 2',
    ]
    pt_linea = [
        ' Shutdown',
        '  Ok',
    ]
    pt_to_end = [
        'Power supply 1 removed',
        'Power supply 2 removed',
        'Power supply 3 removed',
        'Power supply 4 removed',
        'Power supply 1 detected but shutdown',
        'Power supply 2 detected but shutdown',
        'Power supply 3 detected but shutdown',
        'Power supply 4 detected but shutdown',
        'Power supply 1 ok ',
        'Power supply 2 ok ',
        'Power supply 3 ok ',
        'Power supply 4 ok ',
    ]
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
    # Definimos explícitamente qué estilo usar por palabra
    for w in pt_todas + pt_unicas:
        mapa_colores[w.lower()] = resaltado_ok

    for clave in [
        'Power supply 1 removed',
        'Power supply 2 removed',
        'Power supply 3 removed',
        'Power supply 4 removed',
        'Power supply 1 detected but shutdown',
        'Power supply 2 detected but shutdown',
        'Power supply 3 detected but shutdown',
        'Power supply 4 detected but shutdown',
        ' Shutdown',
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


def prueba_3_C9348GC():
    mapa_colores = {}
    pt_todas = [
        'Fan1(sys_fan1)  ',
        'Fan2(sys_fan2)  ',
        'Fan3(sys_fan3)  ',
        'Fan4(sys_fan4)  ',
        'Absent',
        'Fantray module slot ',
        'FM0',
        'FM1',
        'FM2',
        'FM3',
        # 'removed',

        'Fan module 1 (Serial number ) Fan1(sys_fan1) removed',
        'Fan module 1 (Fan1(sys_fan1) fan) ok',
        'Fan module 2 (Serial number ) Fan2(sys_fan2) removed',
        'Fan module 2 (Fan2(sys_fan2) fan) ok',
        'Fan module 3 (Serial number ) Fan3(sys_fan3) removed',
        'Fan module 3 (Fan3(sys_fan3) fan) ok',
        'Fan module 4 (Serial number ) Fan4(sys_fan4) removed',
        'Fan module 4 (Fan4(sys_fan4) fan) ok',

    ]
    pt_unicas = [
        'INICIO PRUEBA 3',
        'show environment fan',
        'show env fan',
        'sh environment fan',
        'sh env fan',
        'FIN PRUEBA 3',
    ]
    pt_linea = [
        'Absent',
        # 'removed',
        'Fan1(sys_fan1)  ',
        'Fan2(sys_fan2)  ',
        'Fan3(sys_fan3)  ',
        'Fan4(sys_fan4)  ',
    ]
    pt_to_end = [
        'Fantray module slot ',
    ]
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
    # Definimos explícitamente qué estilo usar por palabra
    for w in pt_todas + pt_unicas:
        mapa_colores[w.lower()] = resaltado_ok

    for clave in [
        # 'removed',
        'Fan module 1 (Serial number ) Fan1(sys_fan1) removed',
        'Fan module 2 (Serial number ) Fan2(sys_fan2) removed',
        'Fan module 3 (Serial number ) Fan3(sys_fan3) removed',
        'Fan module 4 (Serial number ) Fan4(sys_fan4) removed',
        'Absent',
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


def prueba_4_C9348GC():
    mapa_colores = {}
    pt_todas = [
        'login:',
        'Password:',
    ]
    pt_unicas = [
        'INICIO PRUEBA 4',
        'reload',
        'Initializing Hardware',
        'show version',
        'show ver',
        'sh version',
        'sh ver',
        'uptime is',
        'User Access Verification',
        'NXOS: version',
        'Processor Board ID',
        'cisco Nexus9000 C',
        'FIN PRUEBA 4',
    ]
    pt_linea = [
        'Initializing Hardware',
        'uptime is',
        'Model Number',
        'System Serial Number',
        'login:',
    ]
    pt_to_end = [
        'NXOS: version',
        'Processor Board ID',
        'cisco Nexus9000 C',
    ]
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


def prueba_5_C9348GC():
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