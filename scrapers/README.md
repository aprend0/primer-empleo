# Scrapers - Proyecto Primer Empleo

Módulos de extracción para los principales portales de empleo en Perú.

| Portal | Carpeta | Estado | Prioridad |
|--------|---------|--------|-----------|
| **Computrabajo** | `computrabajo/` | Completo | #1 |
| **Bumeran** | `bumeran/` | Completo | #2 |
| **Indeed** | `indeed/` | Completo | #4 |

## Ejecutar todos

```bash
cd scrapers
python run_all.py
```

## Integración en el pipeline

Cada scraper retorna `(jobs, metrics)` compatible con la tabla `scraper_runs`.

## Plan B

Si un portal falla (`estado == "failed"`), continuar con los demás.
