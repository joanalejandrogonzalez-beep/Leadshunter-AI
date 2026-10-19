"""Ejecuta todas las búsquedas guardadas. Pensado para el Programador de tareas de Windows."""
from leadhunter import pipeline

for s, (new, old, errs) in pipeline.run_saved():
    print(f"[{s['business']}] {s['sector']} {s['city']}: {new} nuevos, {old} existentes, {len(errs)} errores")
