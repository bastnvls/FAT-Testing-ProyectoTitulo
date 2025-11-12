from funcionalidades.colores import resaltado_fallido, resaltado_na, resaltado_ok, resaltado_opcional
from ..list_fallidas import fallidas

def prueba_1_c9115axi():
    mapa_colores = {}  
    pt_todas = []
    pt_unicas = [
        'Inicio Prueba 1',
        'show version',
        'show ver',
        'sh version',
        'sh ver',
        'uptime is',
        'cisco C9115AXI-A',
        'cisco C9115AXE-A',
        'Assembly Serial Number',
        'Product/Model Number',
        'Running Image',
        'Fin Prueba 1',
        ]
    pt_linea = [
        'uptime is',
        'Running Image',
        'Assembly Serial Number',
        'Product/Model Number',
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


def prueba_2_c9115axi():
    mapa_colores = {}  
    pt_todas = []
    pt_unicas = [
        'Inicio Prueba 2',
        'reload',
        'show version',
        'sh version',
        'show ver',
        'sh ver',
        'Fin Prueba 2',
        'Product/Model Number',
        ]
    pt_linea = [
        'uptime',
        'Processor board ID',
        'Assembly Serial Number',
        'Product/Model Number',
        ]
    pt_to_end = []
    pt_until_comma  =[]
    pt_derecha_excluyendo =[]
    pt_entre_dos = []
    pt_n_coincidencia = [
        ('uptime',1),
        ('Processor board ID',1),
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