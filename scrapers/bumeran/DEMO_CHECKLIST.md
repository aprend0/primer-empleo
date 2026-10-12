# Checklist Pre-Demo (10 minutos antes)

1. **Activar entorno virtual**
   ```bash
   cd scrapers/bumeran
   source .venv/bin/activate   # o .venv\Scripts\activate en Windows
   ```

2. **Verificar dependencias**
   ```bash
   pip list | grep -E "requests|beautifulsoup4|playwright"
   ```

3. **Limpiar terminal**
   ```bash
   clear   # o cls en Windows
   ```

4. **Probar el script de demo**
   ```bash
   python demo_bumeran.py
   ```

5. **Tener abierto el README** (por si preguntan detalles técnicos)

---
Si la extracción real falla, el script usa datos simulados automáticamente.
La demo nunca se rompe.
