# Scrapers - Proyecto Primer Empleo

Módulo de extracción multi-portal.

## Asignaciones según Gantt (T5.5.*)

| Portal        | Código   | Responsable   | Estado actual                  |
|---------------|-----------|---------------|--------------------------------|
| **Bumeran**   | T5.5.BUM  | **Néstor**    | **Completo (parte entregada)** |
| Computrabajo  | T5.5.COM  | Emerson       | Plantilla colaborativa         |
| Indeed        | T5.5.IND  | Pedro         | Plantilla colaborativa         |
| Jobsora       | T5.5.JOB  | Arleth        | Plantilla colaborativa         |
| BeBee         | T5.5.BEB  | Juan Carlos   | Plantilla colaborativa         |
| Practicas.pe  | T5.5.PRA  | Emerson       | Plantilla colaborativa         |

## Nota

La versión completa y robusta corresponde al scraper de **Bumeran** (T5.5.BUM).  
Los demás portales tienen una estructura base lista para que cada responsable la complete y mejore.

## Ejecutar

```bash
# Solo Bumeran (parte principal)
cd bumeran && python bumeran_scraper_sync.py

# Todos (plantillas)
python run_all.py
```

## Esquema y métricas

Unificados para facilitar la integración en la tabla `scraper_runs`.
