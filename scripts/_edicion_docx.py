"""Utilidad compartida para convertir un .docx REAL (con datos de un caso
ya capturado, o con placeholders tipo "…"/"00") en una plantilla docxtpl,
SIN reconstruir el documento desde cero — se edita el archivo real in situ
para conservar exactamente su formato (fuente, márgenes, membrete, firma).

El problema real: Word fragmenta el texto de un párrafo en muchos `run`
distintos (por autocorrección, ediciones sucesivas, etc.), así que un
placeholder como "Acta MCG/0X/202X" puede estar partido en 4 runs. No se
puede simplemente hacer `run.text = run.text.replace(...)` porque el texto
buscado casi nunca cae limpio dentro de un solo run.
"""


def reemplazar_en_parrafo(paragraph, buscar: str, reemplazar: str) -> bool:
    """Busca `buscar` en el texto COMPLETO del párrafo (concatenando todos
    sus runs) y lo sustituye por `reemplazar`, sin importar cuántos runs
    abarque. El primer run afectado se queda con el formato y el texto
    nuevo; los demás runs consumidos quedan vacíos (no se borran como
    elementos XML, para no arriesgar romper la estructura, solo se vacía
    su texto). Devuelve True si encontró y reemplazó algo."""
    runs = paragraph.runs
    texto_completo = "".join(r.text for r in runs)
    inicio = texto_completo.find(buscar)
    if inicio == -1:
        return False
    fin = inicio + len(buscar)

    pos = 0
    primer_run_afectado = None
    for run in runs:
        largo = len(run.text)
        run_inicio, run_fin = pos, pos + largo
        if run_fin <= inicio or run_inicio >= fin:
            pos += largo
            continue  # este run no toca el rango buscado

        prefijo = run.text[: max(0, inicio - run_inicio)]
        sufijo = run.text[max(0, fin - run_inicio):]

        if primer_run_afectado is None:
            run.text = prefijo + reemplazar + sufijo
            primer_run_afectado = run
        else:
            run.text = prefijo + sufijo  # ya no se repite `reemplazar`

        pos += largo

    return True


def reemplazar_todas(paragraph, reemplazos: list[tuple[str, str]]) -> None:
    for buscar, reemplazar in reemplazos:
        reemplazar_en_parrafo(paragraph, buscar, reemplazar)


def quitar_numeracion(paragraph) -> None:
    """Quita el numPr (viñeta/numeración) de un párrafo. Necesario en los
    párrafos que se convierten en la etiqueta de apertura {%for%} de un
    loop multi-párrafo de docxtpl: ese párrafo queda vacío al renderizar,
    pero si originalmente tenía viñeta, Word muestra una viñeta vacía
    antes de la lista real."""
    pPr = paragraph._p.pPr
    if pPr is not None and pPr.numPr is not None:
        pPr.numPr.getparent().remove(pPr.numPr)
