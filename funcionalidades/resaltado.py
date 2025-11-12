from docx.oxml.ns import qn
import re
from copy import deepcopy
from .colores import resaltado_fallido, resaltado_na, resaltado_ok, resaltado_opcional
from .modelos._9200 import prueba_1_9200, prueba_2_9200,prueba_3_9200,prueba_4_9200, prueba_5_9200
from .modelos._9300 import prueba_1_9300, prueba_2_9300, prueba_3_9300, prueba_4_9300, prueba_5_9300
from .modelos.checkpoint_6600p import prueba_1_6600, prueba_2_6600, prueba_3_6600, prueba_4_6600, prueba_5_6600, prueba_6_6600, prueba_7_6600, prueba_8_6600, prueba_9_6600
from .modelos._9500 import prueba_1_9500, prueba_2_9500, prueba_3_9500, prueba_4_9500, prueba_5_9500
from .modelos.IE4010 import prueba_1_ie4010, prueba_2_ie4010, prueba_3_ie4010, prueba_4_ie4010,prueba_5_ie4010, prueba_6_ie4010
from .modelos.IE3300 import prueba_1_ie3300, prueba_2_ie3300,prueba_3_ie3300, prueba_4_ie3300, prueba_5_ie3300,prueba_6_ie3300
from .modelos.c9130axi import prueba_1_c9130axi, prueba_2_c9130axi
from .modelos.C9348GC import prueba_1_C9348GC, prueba_2_C9348GC, prueba_3_C9348GC, prueba_4_C9348GC, prueba_5_C9348GC
from .modelos.C93180YC import prueba_1_C93180YC, prueba_2_C93180YC, prueba_3_C93180YC, prueba_4_C93180YC, prueba_5_C93180YC
from .modelos.c9115axi import prueba_1_c9115axi, prueba_2_c9115axi
from .modelos.c9120axe import prueba_1_c9120axe, prueba_2_c9120axe  
from .modelos.ISR4431 import prueba_1_ISR4431, prueba_2_ISR4431, prueba_3_ISR4431, prueba_4_ISR4431, prueba_5_ISR4431
from .modelos.C8500 import prueba_1_C8500, prueba_2_C8500, prueba_3_C8500, prueba_4_C8500, prueba_5_C8500
from .modelos.checkpoint_6200p import prueba_1_6200, prueba_2_6200, prueba_3_6200, prueba_4_6200, prueba_5_6200, prueba_6_6200, prueba_7_6200, prueba_8_6200, prueba_9_6200
# --------------------------------------
# Helpers de resaltado
# --------------------------------------

def ya_procesado(run):
    rpr = run._element.get_or_add_rPr()
    return rpr.find(qn('w:highlight')) is not None

def highlight_partial(run, match, shading_func):
    text = run.text or ""
    start, end = match.span(1)
    before, middle, after = text[:start], text[start:end], text[end:]
    elm = run._element
    parent = elm.getparent()
    if parent is None:
        return
    idx = list(parent).index(elm)
    # 1) Antes
    elm_before = deepcopy(elm)
    elm_before.text = before
    parent.insert(idx, elm_before)
    # 2) Medio resaltado
    elm_mid = deepcopy(elm)
    elm_mid.text = middle
    shaded_run = run.__class__(elm_mid, run._parent)
    shading_func(shaded_run)
    parent.insert(idx+1, elm_mid)
    # 3) Después
    elm_after = deepcopy(elm)
    elm_after.text = after
    parent.insert(idx+2, elm_after)
    # Eliminar run original
    parent.remove(elm)

def highlight_line(run, shading_func):
    shading_func(run)

def highlight_to_end(run, match, shading_func):
    text = run.text or ""
    try:
        start = match.span(1)[0]
    except IndexError:
        start = match.span(0)[0]
    class DummyMatch:
        def span(self, grp):
            return (start, len(text))
    highlight_partial(run, DummyMatch(), shading_func)

def highlight_right_excluding(run, match, shading_func):
    text = run.text or ""
    _, end = match.span(1)
    if end >= len(text):
        return
    class DummyMatch:
        def span(self, grp):
            return (end, len(text))
    highlight_partial(run, DummyMatch(), shading_func)

def highlight_until(run, match, end_word, shading_func):
    text = run.text or ""
    start = match.span(1)[0]
    idx_rel = re.search(re.escape(end_word), text[start:], re.IGNORECASE)
    if idx_rel:
        end = start + idx_rel.start()
    else:
        end = len(text)
    class DummyMatch:
        def span(self, grp):
            return (start, end)
    highlight_partial(run, DummyMatch(), shading_func)

# --------------------------------------
# Lógica de aplicación de estilo
# --------------------------------------

def apply_behavior(run, match, word,
                   pt_linea, pt_to_end, pt_until_comma,
                   pt_derecha_excluyendo, pt_until_next,
                   shading_func=resaltado_ok):

    if word in pt_linea:
        highlight_line(run, shading_func)
        return

    if word in pt_to_end:
        highlight_to_end(run, match, shading_func)
        return

    if word in pt_until_comma:
        highlight_partial(run, match, shading_func)
        return

    if word in pt_derecha_excluyendo:
        highlight_right_excluding(run, match, shading_func)
        return

    for start_word, end_word in pt_until_next:
        if word.lower() == start_word.lower():
            highlight_until(run, match, end_word, shading_func)
            return

    highlight_partial(run, match, shading_func)

# --------------------------------------
# Patrones especiales
# --------------------------------------

pattern_na   = re.compile(r'\bprueba\b.*\bN/A\b', re.IGNORECASE)
pattern_fail = re.compile(r'\bprueba\b.*\bfallida\b', re.IGNORECASE)
pattern_optional  = re.compile(r'\bprueba\b.*\bopcional\b', re.IGNORECASE)
# --------------------------------------
# Función principal de subrayado
# --------------------------------------

def subrayar_texto(paragraphs, file_type, contador):
    # 1) Obtener configuraciones, incluido pt_until_next y pt_nth
    (pt_todas, pt_unicas, pt_linea,
     pt_to_end, pt_until_comma,
     pt_derecha_excluyendo,
     shading_map,
     pt_until_next,
     pt_nth) = seleccion_modelos(file_type, contador)

    # -----------------------------------------
    # Primera pasada: bloques "hasta next"
    # -----------------------------------------
    for start_word, end_word in pt_until_next:
        for para in paragraphs:
            found = False
            for run in para.runs:
                if ya_procesado(run):
                    continue
                text = run.text or ""
                if not found:
                    m0 = re.search(r'(' + re.escape(start_word) + r')', text, re.IGNORECASE)
                    if m0:
                        highlight_to_end(run, m0, shading_map[start_word.lower()])
                        found = True
                    continue
                m1 = re.search(re.escape(end_word), text, re.IGNORECASE)
                if m1:
                    class DummyMatchEnd:
                        def span(self, grp): return (0, m1.start())
                    highlight_partial(run, DummyMatchEnd(), shading_map[start_word.lower()])
                    break
                else:
                    highlight_line(run, shading_map[start_word.lower()])

    # -----------------------------------------
    # Segunda pasada: lógica normal pt_todas/pt_unicas
    # -----------------------------------------
    # 1) Claves de pt_todas que usan resaltado_na
    na_todas    = [w for w in pt_todas if shading_map.get(w.lower()) == resaltado_na]
    # 2) El resto de pt_todas
    other_todas = [w for w in pt_todas if shading_map.get(w.lower()) != resaltado_na]
    # 3) Ensamblar el orden final
    ordered_keys = na_todas + other_todas + pt_unicas

    for para in paragraphs:
        unicas_done = set()
        while True:
            changed = False
            for run in list(para.runs):
                if ya_procesado(run):
                    continue
                txt = run.text or ""
                low = txt.lower()
                # Casos especiales 
                if pattern_na.search(low):
                    resaltado_na(run)
                    changed = True
                    continue
                if pattern_fail.search(low):
                    resaltado_fallido(run)
                    changed = True
                    continue
                if pattern_optional.search(low):
                    resaltado_opcional(run)
                    changed = True
                    continue
                # Procesar el orden forzado
                for palabra in ordered_keys:
                    if palabra in pt_unicas and palabra in unicas_done:
                        continue
                    regex = (
                        r'(' + re.escape(palabra) + r'[^,]*)'
                        if palabra in pt_until_comma
                        else r'(' + re.escape(palabra) + r')'
                    )
                    m = re.search(regex, txt, re.IGNORECASE)
                    if m:
                        func = shading_map.get(palabra.lower(), resaltado_ok)
                        apply_behavior(
                            run, m, palabra,
                            pt_linea, pt_to_end, pt_until_comma,
                            pt_derecha_excluyendo,
                            [],  # omitimos pt_until_next aquí
                            shading_func=func
                        )
                        changed = True
                        if palabra in pt_unicas:
                            unicas_done.add(palabra)
                        break
            if not changed:
                break

    # -----------------------------------------
    # Tercera pasada: N-ésima ocurrencia pt_nth
    # -----------------------------------------
    for palabra, target in pt_nth:
        count = 0
        patron = re.compile(r'(' + re.escape(palabra) + r')', re.IGNORECASE)
        for para in paragraphs:
            for run in para.runs:
                if ya_procesado(run):
                    continue
                txt = run.text or ""
                for m in patron.finditer(txt):
                    count += 1
                    if count == target:
                        func = shading_map.get(palabra.lower(), resaltado_ok)
                        apply_behavior(
                            run, m, palabra,
                            pt_linea, pt_to_end, pt_until_comma,
                            pt_derecha_excluyendo,
                            [],            # pt_until_next ya no aplica aquí
                            shading_func=func
                        )
                        break
                if count == target:
                    break
            if count == target:
                break

def seleccion_modelos(file_type, contador):
    key = (file_type, contador)
    if key not in CONFIGS:
        return [], [], [], [], [], [], {}, [], []
    return CONFIGS[key]()

CONFIGS = {
    # MODELOS 9200
    ("SW L2 9200", 1): prueba_1_9200,
    ("SW L2 9200", 2): prueba_2_9200,
    ("SW L2 9200", 3): prueba_3_9200,
    ("SW L2 9200", 4): prueba_4_9200,
    ("SW L2 9200", 5): prueba_5_9200,
    # MODELOS 9300
    ("SW L2 9300", 1): prueba_1_9300,
    ("SW L2 9300", 2): prueba_2_9300,
    ("SW L2 9300", 3): prueba_3_9300,
    ("SW L2 9300", 4): prueba_4_9300,
    ("SW L2 9300", 5): prueba_5_9300,
    # Modelos 9500
    ("SW L2 9500", 1): prueba_1_9500,
    ("SW L2 9500", 2): prueba_2_9500,
    ("SW L2 9500", 3): prueba_3_9500,
    ("SW L2 9500", 4): prueba_4_9500,
    ("SW L2 9500", 5): prueba_5_9500,
    # Checkpoint
    ("Check Point 6600", 1): prueba_1_6600,
    ("Check Point 6600", 2): prueba_2_6600,
    ("Check Point 6600", 3): prueba_3_6600,
    ("Check Point 6600", 4): prueba_4_6600,
    ("Check Point 6600", 5): prueba_5_6600,
    ("Check Point 6600", 6): prueba_6_6600,
    ("Check Point 6600", 7): prueba_7_6600,
    ("Check Point 6600", 8): prueba_8_6600,
    ("Check Point 6600", 9): prueba_9_6600,
    # Switch Industriales IE4010
    ("SW IE4010", 1): prueba_1_ie4010,
    ("SW IE4010", 2): prueba_2_ie4010,
    ("SW IE4010", 3): prueba_3_ie4010,
    ("SW IE4010", 4): prueba_4_ie4010,
    ("SW IE4010", 5): prueba_5_ie4010,
    ("SW IE4010", 6): prueba_6_ie4010,
    # Switch Industriales IE3300
    ("SW IE3300", 1): prueba_1_ie3300,
    ("SW IE3300", 2): prueba_2_ie3300,
    ("SW IE3300", 3): prueba_3_ie3300,
    ("SW IE3300", 4): prueba_4_ie3300,
    ("SW IE3300", 5): prueba_5_ie3300,
    ("SW IE3300", 6): prueba_6_ie3300,
    # Access Point C9130AXI
    ("AP C9130AXI", 1): prueba_1_c9130axi,
    ("AP C9130AXI", 2): prueba_2_c9130axi,
    # SW L3 
    ("SW L3 9348GC", 1): prueba_1_C9348GC,
    ("SW L3 9348GC", 2): prueba_2_C9348GC,
    ("SW L3 9348GC", 3): prueba_3_C9348GC,
    ("SW L3 9348GC", 4): prueba_4_C9348GC,
    ("SW L3 9348GC", 5): prueba_5_C9348GC,
    # SW L3 93180YC
    ("SW L3 C93180YC", 1): prueba_1_C93180YC,
    ("SW L3 C93180YC", 2): prueba_2_C93180YC,
    ("SW L3 C93180YC", 3): prueba_3_C93180YC,
    ("SW L3 C93180YC", 4): prueba_4_C93180YC,
    ("SW L3 C93180YC", 5): prueba_5_C93180YC,
    # ROUTER ISR4431
    ("Router ISR4431", 1): prueba_1_ISR4431,
    ("Router ISR4431", 2): prueba_2_ISR4431,
    ("Router ISR4431", 3): prueba_3_ISR4431,
    ("Router ISR4431", 4): prueba_4_ISR4431,
    ("Router ISR4431", 5): prueba_5_ISR4431,
    # ROUTER ISR4431
    ("Router C8500", 1): prueba_1_C8500,
    ("Router C8500", 2): prueba_2_C8500,
    ("Router C8500", 3): prueba_3_C8500,
    ("Router C8500", 4): prueba_4_C8500,
    ("Router C8500", 5): prueba_5_C8500,
    # Access Point C9115AXI
    ("AP C9115AXI", 1): prueba_1_c9115axi,
    ("AP C9115AXI", 2): prueba_2_c9115axi,
    # Access Point C9120AXE
    ("AP C9120AXE", 1): prueba_1_c9120axe,
    ("AP C9120AXE", 2): prueba_2_c9120axe,
    # Checkpoint 6200P
    ("Check Point 6200", 1): prueba_1_6200,
    ("Check Point 6200", 2): prueba_2_6200,
    ("Check Point 6200", 3): prueba_3_6200,
    ("Check Point 6200", 4): prueba_4_6200,
    ("Check Point 6200", 5): prueba_5_6200,
    ("Check Point 6200", 6): prueba_6_6200,
    ("Check Point 6200", 7): prueba_7_6200,
    ("Check Point 6200", 8): prueba_8_6200,
    ("Check Point 6200", 9): prueba_9_6200,
}