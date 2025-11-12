from funcionalidades.colores import resaltado_fallido, resaltado_na, resaltado_ok, resaltado_opcional
from ..list_fallidas import fallidas

def prueba_1_6600():
    mapa_colores = {}
    pt_todas = []
    pt_unicas = [
        'Inicio Prueba 1',
        'expert',
        'Enter expert password',
        '[Expert@',
        'Login:',
        'Password:',
        'Fin Prueba 1'
    ]
    pt_linea = []
    pt_to_end = [
        '[Expert@',
        'Login:',
        'Password:',
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


def prueba_2_6600():
    mapa_colores = {}
    pt_todas = [
        '|UP ',
        '|Empty ',
        '|Down '
    ]
    pt_unicas = [
        'INICIO PRUEBA 2',
        'FIN PRUEBA 2',
        'cpstat os -f power_supply',
        'cpstat os -f power supply',
    ]
    pt_linea = []
    pt_to_end = []
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
    # Definimos explícitamente qué estilo usar por palabra
    for w in pt_todas + pt_unicas:
        mapa_colores[w.lower()] = resaltado_ok
    mapa_colores['|Empty '.lower()] = resaltado_na
    mapa_colores['|Down '.lower()] = resaltado_na

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


def prueba_3_6600():
    mapa_colores = {}
    pt_todas = []
    pt_unicas = [
        'INICIO PRUEBA 3',
        'FIN PRUEBA 3',
        'cpstat os -f sensors',
        'Temperature Sensors',
        'CPU Temp',
        'CPU PECI Temp',
    ]
    pt_linea = [
        'CPU Temp',
        'CPU PECI Temp',
    ]
    pt_to_end = []
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = [('Temperature Sensors','Fan Speed Sensors')]
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
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


def prueba_4_6600():
    mapa_colores = {}
    pt_todas = []
    pt_unicas = [
        'INICIO PRUEBA 4',
        'FIN PRUEBA 4',
        'cpstat os -f all',
        'Version String',
        'Appliance Name',
        'Interface configuration table',
    ]
    pt_linea = [
        'Version String',
        'Appliance Name',
    ]
    pt_to_end = []
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = [('Interface configuration table','Routing table')]
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
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


def prueba_5_6600():
    mapa_colores = {}
    pt_todas = [
        '10000baseSR/Full',
    ]
    pt_unicas = [
        'INICIO PRUEBA 5',
        'FIN PRUEBA 5',
        'ethtool eth1-01',
        'ethtool eth1',
    ]
    pt_linea = []
    pt_to_end = []
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
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


def prueba_6_6600():
    mapa_colores = {}
    pt_todas = [
        '10000baseLR/Full'
    ]
    pt_unicas = [
        'INICIO PRUEBA 6',
        'FIN PRUEBA 6',
        'ethtool eth1-01',
        'ethtool eth1',
    ]
    pt_linea = []
    pt_to_end = []
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
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


def prueba_7_6600():
    mapa_colores = {}
    pt_todas = [
        '10baseT/Half',
        '10baseT/Full',
        '100baseT/Half',
        '100baseT/Full',
        '1000baseT/Full',
    ]
    pt_unicas = [
        'INICIO PRUEBA 7',
        'FIN PRUEBA 7',
        'ethtool eth1',
        'ethtool eth1-01',
    ]
    pt_linea = []
    pt_to_end = [
        '10baseT/Half',
        '10baseT/Full',
        '100baseT/Half',
        '100baseT/Full',
        '1000baseT/Full',
    ]
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
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


def prueba_8_6600():
    mapa_colores = {}
    pt_todas = [
        '10000base'
    ]
    pt_unicas = [
        'INICIO PRUEBA 8',
        'FIN PRUEBA 8',
        'ethtool eth1-01',
        'ethtool eth1',
    ]
    pt_linea = []
    pt_to_end = [
        '10000base',
    ]
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
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


def prueba_9_6600():
    mapa_colores = {}
    pt_todas = []
    pt_unicas = [
        'INICIO PRUEBA 9',
        'FIN PRUEBA 9',
        'reboot',
        'login',
        'password',
        'Last login',
    ]
    pt_linea = [
        'login',
        'Last login',
    ]
    pt_to_end = []
    pt_until_comma = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
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