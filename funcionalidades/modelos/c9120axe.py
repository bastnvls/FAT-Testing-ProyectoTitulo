from funcionalidades.colores import resaltado_fallido, resaltado_na, resaltado_ok, resaltado_opcional
from ..list_fallidas import fallidas

def prueba_1_c9120axe():
    mapa_colores = {}  
    pt_todas = []
    pt_unicas = [
        'Inicio Prueba 1',
        'show version',
        'show ver',
        'sh version',
        'sh ver',
        'uptime is',
        'cisco C9120AXI-A',
        'cisco C9120AXE-A',
        'Running Image',
        'Assembly Serial Number',
        'Product/Model Number',
        'Fin Prueba 1',
        ]
    pt_linea = [
        'uptime is',
        'Running Image',
        'Product/Model Number',
        'Assembly Serial Number',
        ]
    pt_to_end = []
    pt_until_comma  =[]
    pt_derecha_excluyendo =[]
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

def prueba_2_c9120axe():
    mapa_colores = {}  
    pt_todas = [
        'Password:',
        ]
    pt_unicas = [
        'Inicio Prueba 2',
        'reload',
        'Username: cisco',
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
        'Fin Prueba 2',
        ]
    pt_linea = [
        'Username: cisco',
        'Username: Cisco',
        'Username:cisco',
        'Username:Cisco',
        'Password:',
        'uptime is',
        'Assembly Serial Number',
        'Product/Model Number',
        ]
    pt_to_end = [
        '>ena',
        '> ena',
        ]
    pt_until_comma  =[]
    pt_derecha_excluyendo =[]
    pt_entre_dos = []
    pt_n_coincidencia = [
        ('uptime is',1),
        ('Assembly Serial Number',1),
        ('Product/Model Number',1),
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