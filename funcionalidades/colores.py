from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def aplicar_resaltado_marcador(run, color_name):
    """
    Aplica un resaltado tipo marcador (editable desde Word) al run.
    color_name: debe ser un valor válido como 'green', 'yellow', 'red', etc.
    """
    rPr = run._element.get_or_add_rPr()

    # Quitar highlight previo si ya existe
    highlight = rPr.find(qn('w:highlight'))
    if highlight is not None:
        rPr.remove(highlight)

    # Agregar nuevo highlight
    hl = OxmlElement('w:highlight')
    hl.set(qn('w:val'), color_name)
    rPr.append(hl)

# Funciones específicas
def resaltado_ok(run):
    aplicar_resaltado_marcador(run, 'green')

def resaltado_na(run):
    aplicar_resaltado_marcador(run, 'yellow')

def resaltado_fallido(run):
    aplicar_resaltado_marcador(run, 'red')

def resaltado_opcional(run):
    aplicar_resaltado_marcador(run, 'magenta')  # o 'pink', 'cyan', etc.