# Checklist Pre-Demo — Bumeran Scraper (T5.5.BUM)

## 10 minutos antes de la reunión

### Paso 1: Verificar Python
```bash
python --version
# Debe ser 3.10 o superior
```

### Paso 2: Activar entorno virtual
```bash
cd scrapers/bumeran
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows
```

### Paso 3: Verificar dependencias
```bash
pip show requests beautifulsoup4 playwright
# Si falta alguna: pip install -r requirements.txt
```

### Paso 4: Verificar Playwright (opcional para demo)
```bash
playwright install chromium
```

### Paso 5: Terminal limpia y prueba
```bash
clear
python demo_bumeran.py
```

---

## Comando final para la demo

```bash
python demo_bumeran.py
```

## Si algo falla

| Problema | Solución |
|----------|----------|
| Terminal con scroll | `clear` antes de ejecutar |
| Colores no se ven | Usar terminal compatible (no cmd de Windows) |
| Error de import | El demo no requiere el scraper real |
