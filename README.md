# 🚣 Cálculo de Posiciones Canotaje - Versión Web

Aplicación web para calcular rankings de atletas de canotaje respecto a un tiempo testigo con selección automática.

Convertida de aplicación de escritorio (PySide6) a aplicación web con **Streamlit**.

---

## ✨ Características

- ✅ 4 categorías de canotaje (K1 M 1000, C1 M 1000, K1 F 500, C1 F 200)
- ✅ Cálculo automático de % vs tiempo testigo
- ✅ Selección automática según corte de porcentaje
- ✅ Importar/exportar CSV y Excel
- ✅ Ranking global filtrable por disciplina y sexo
- ✅ Estadísticas en tiempo real
- ✅ Interfaz web moderna y responsiva

---

## 🚀 Ejecución Local

### Requisitos
- Python 3.8+
- pip

### Instalación

```bash
# 1. Ir al directorio del proyecto
cd "/home/eesse/Documentos/CALCULO POSICIONES CUOCIENTE"

# 2. Crear entorno virtual (opcional pero recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar la aplicación

```bash
streamlit run app_streamlit.py
```

La aplicación se abrirá en el navegador en `http://localhost:8501`

---

## 🌐 Desplegar en Streamlit Cloud (GRATIS)

### Opción 1: Con GitHub (Recomendado)

#### Paso 1: Crear repositorio en GitHub

```bash
# Inicializar git (si no lo está)
git init

# Agregar archivos
git add .
git commit -m "Initial commit: Streamlit app"

# Crear repositorio en github.com y sube los cambios
git remote add origin https://github.com/TU_USUARIO/nombre-repo.git
git branch -M main
git push -u origin main
```

#### Paso 2: Desplegar en Streamlit Cloud

1. Ve a [https://streamlit.io/cloud](https://streamlit.io/cloud)
2. Haz clic en **"Sign in with GitHub"**
3. Conecta tu cuenta de GitHub
4. Haz clic en **"New app"**
5. Selecciona:
   - **Repository**: el repositorio que creaste
   - **Branch**: `main`
   - **Main file path**: `app_streamlit.py`
6. Haz clic en **"Deploy"**

¡Tu aplicación estará disponible en una URL pública como: `https://nombre-app.streamlit.app`

### Opción 2: Con Alternativos (Heroku, Railway, Render)

#### Alternativamente con **Railway** (más moderno)

1. Sube tu código a GitHub
2. Ve a [https://railway.app](https://railway.app)
3. Haz clic en "New Project" → "Deploy from GitHub repo"
4. Selecciona tu repositorio
5. Agrega variable de entorno: `PORT=8501`
6. Procfile:
   ```
   web: streamlit run app_streamlit.py --server.port=$PORT --server.address=0.0.0.0
   ```

---

## 📁 Estructura de Archivos

```
/home/eesse/Documentos/CALCULO POSICIONES CUOCIENTE/
├── app_streamlit.py          # Aplicación Streamlit
├── requirements.txt          # Dependencias Python
├── .streamlit/
│   └── config.toml          # Configuración de Streamlit
├── README.md                # Este archivo
└── seleccionados_pro_plus.py # (Aplicación de escritorio original)
```

---

## 📊 Uso de la Aplicación

### Para cada categoría:

1. **Ingresa Tiempo Testigo**: En formato `m:ss.fff` (ej: `3:45.320`) o solo segundos (ej: `225.32`)

2. **Configura Corte**: Porcentaje máximo permitido. Por defecto 105% (5% más lento que el testigo)

3. **Agregar Atletas**:
   - Usa los campos de texto para ingresar nombre, club, tiempo
   - O sube un CSV/Excel con las columnas: `Nombre, Club, Tiempo`

4. **Procesar Datos**: Haz clic en "Procesar datos" para ver resultados y ranking

5. **Descargar Resultados**:
   - CSV: datos brutos
   - Excel: con formato y estadísticas

### Ranking Global:

- Filtra por disciplina y sexo
- Ajusta "Top N" para mostrar los mejores
- Descarga el ranking en Excel
- Los "Seleccionados" están marcados con ✓

---

## 📝 Formato de Entrada de Tiempo

La aplicación acepta tiempos en estos formatos:

- `3:45.32` → 3 minutos, 45 segundos, 32 centisegundos
- `225.32` → 225 segundos, 32 centisegundos
- `3:45,32` → Con coma (también válido)
- `3:45` → Solo minutos y segundos

---

## 🔄 Diferencias con la Versión de Escritorio

| Aspecto | Escritorio | Web |
|---------|-----------|-----|
| Interfaz | PySide6 (Qt) | Streamlit |
| Acceso | Solo local | Desde cualquier navegador |
| PDF | Soportado | No (pero Excel sí) |
| Color personalizado | Sí | Tema moderno |
| Colaboración | No | Posible (cada usuario) |

---

## 🛠️ Desarrollo Futuro

Mejoras sugeridas:

- [ ] Dashboard con gráficos (matplotlib/plotly)
- [ ] Exportación a PDF
- [ ] Almacenamiento en base de datos
- [ ] Análisis histórico de rankings
- [ ] API REST para integración
- [ ] Autenticación de usuarios

---

## ❓ Preguntas Frecuentes

**P: ¿Cuánto cuesta?**
> Streamlit Cloud es **completamente gratuito**. Solo se requiere cuenta de GitHub.

**P: ¿Qué tan rápido es?**
> Muy rápido. La aplicación responde en milisegundos (depende de la velocidad de internet).

**P: ¿Mis datos se guardan?**
> Default: No. Los datos se guardan solo durante la sesión. Si quieres persistencia, necesitas una base de datos.

**P: ¿Puedo agregar usuarios?**
> Streamlit Cloud es público por defecto. Puedes añadir autenticación con bibliotecas como `streamlit-authenticator`.

**P: ¿Funciona en móvil?**
> Sí, la interfaz es responsiva.

---

## 📞 Soporte

Para problemas o preguntas:
- Abre un issue en el repositorio GitHub
- Consulta la [documentación oficial de Streamlit](https://docs.streamlit.io)

---

## 📄 Licencia

Uso libre y personal.

---

**Hecho con ❤️ - Cálculo de Posiciones Canotaje**
