from funcionalidades.colores import resaltado_fallido, resaltado_na, resaltado_ok, resaltado_opcional
from ..list_fallidas import fallidas

def prueba_1_6200():
    mapa_colores = {}  
    pt_todas = []
    pt_unicas = [
        'Inicio Prueba 1',
        'expert',
        'Enter expert password:',
        'Fin Prueba 1',
    ]
    pt_linea = []
    pt_to_end = []
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

def prueba_2_6200():
    mapa_colores = {}  
    pt_todas = [
        '|UP ',
        '|Empty '
    ]
    pt_unicas = [
        'Inicio Prueba 2',
        'cpstat os -f power_supply',
        'cpstat os -f power supply',
        'Fin Prueba 2',
    ]
    pt_linea = []
    pt_to_end = []
    pt_until_comma  = []
    pt_derecha_excluyendo = []
    pt_entre_dos = []
    pt_n_coincidencia = []
    pt_todas = fallidas + pt_todas
    # Definimos explícitamente qué estilo usar por palabra
    for w in pt_todas + pt_unicas:
        mapa_colores[w.lower()] = resaltado_ok
    clave = 'Empty'.lower()
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

def prueba_3_6200(): 
    mapa_colores = {}  
    pt_todas = []
    pt_unicas = [
        'Inicio Prueba 3',
        'cpstat os -f sensors',
        'Fan Speed Sensors',
        'Fin Prueba 3',
    ]
    pt_linea = []
    pt_to_end = []
    pt_until_comma  = []
    pt_derecha_excluyendo = []
    pt_entre_dos = [
        ('Fan Speed Sensors','Voltage Sensors'),
    ]
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


def prueba_4_6200():
    mapa_colores = {}  
    pt_todas = []
    pt_unicas = [
        'Inicio Prueba 4',
        'cpstat os -f all',
        'SVN Foundation Version String',
        'Appliance SN',
        'Appliance Name',
        'Interface configuration table',
        'Fin Prueba 4',
    ]
    pt_linea = [
        'SVN Foundation Version String',
        'Appliance SN',
        'Appliance Name',
    ]
    pt_to_end = []
    pt_until_comma  = []
    pt_derecha_excluyendo = []
    pt_entre_dos = [
        ('Interface configuration table','Routing table'),
    ]
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

def prueba_5_6200():
    mapa_colores = {}  
    pt_todas = [
        '100baseT/Full',
        '10000baseSR/Full',
    ]
    pt_unicas = [
        'Inicio Prueba 5',
        'Fin Prueba 5',
        'ethtool eth1-01',
    ]
    pt_linea = []
    pt_to_end = []
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


def prueba_6_6200():
    mapa_colores = {}  
    pt_todas = [
        '10000baseLR/Full',
    ]
    pt_unicas = [
        'Inicio Prueba 6',
        'Fin Prueba 6',
        'ethtool eth1-01',
        'ethtool eth1',
    ]
    pt_linea = []
    pt_to_end = [
        'ethtool eth1-01',
        'ethtool eth1',
    ]
    pt_until_comma  = []
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

def prueba_7_6200():
    mapa_colores = {}  
    pt_todas = [
        '10baseT/Half',
        '10baseT/Full',
        '100baseT/Half',
        '100baseT/Full',
        '1000baseT/Full'
    ]
    pt_unicas = [
        'Inicio Prueba 7',
        'Fin Prueba 7',
        'ethtool eth1-01',
        'ethtool eth1',
    ]
    pt_linea = []
    pt_to_end = [
        'ethtool eth1-01',
        'ethtool eth1',
    ]
    pt_until_comma  = []
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

def prueba_8_6200():
    mapa_colores = {}  
    pt_todas = [
        '10000baseT/Full',
        '1000baseX/Full',
        '10000baseSR/Full',
        '10000baseLR/Full',  
    ]
    pt_unicas = [
        'Inicio Prueba 8',
        'Fin Prueba 8',
        'ethtool eth1-01',
        'ethtool eth1',
    ]
    pt_linea = []
    pt_to_end = [
        'ethtool eth1-01',
        'ethtool eth1',
    ]
    pt_until_comma  = []
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

def prueba_9_6200():
    mapa_colores = {}  
    pt_todas = []
    pt_unicas = [
        'Inicio Prueba 9',
        'reboot',
        'Fin Prueba 9',
        'login: admin',
        'Password:',
        '> expert',
        '>expert'
        'Enter expert password:',
    ]
    pt_linea = []
    pt_to_end = []
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