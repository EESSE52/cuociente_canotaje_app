import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, asdict

# ========================
# CONFIGURACIÓN STREAMLIT
# ========================

st.set_page_config(
    page_title="Cálculo Posiciones Canotaje",
    page_icon="🚣",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejorar la apariencia
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 12px;
        border-radius: 5px;
        border-left: 4px solid #2196F3;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ========================
# UTILIDADES DE TIEMPO
# ========================

_TIME_RE = re.compile(r"^\s*(?:(\d+):)?(\d{1,2})(?:[.,](\d{1,3}))?\s*$")

def parse_time_to_seconds(text: str) -> float:
    """Convierte tiempo en formato 'm:ss.fff' a segundos"""
    m = _TIME_RE.match(text or "")
    if not m:
        raise ValueError("Formato inválido. Usa 1:45.32 o 105.32")

    minutes = int(m.group(1)) if m.group(1) is not None else 0
    seconds = int(m.group(2))
    frac = m.group(3)

    if m.group(1) is not None and seconds >= 60:
        raise ValueError("Segundos deben ser < 60 si usas m:ss")

    frac_s = 0.0
    if frac is not None:
        frac_norm = frac.ljust(3, "0")[:3]
        frac_s = int(frac_norm) / 1000.0

    return minutes * 60 + seconds + frac_s

def format_seconds_to_time(total_seconds: float) -> str:
    """Convierte segundos a formato 'm:ss.fff'"""
    if total_seconds < 0:
        sign = "-"
        total_seconds = abs(total_seconds)
    else:
        sign = ""

    minutes = int(total_seconds // 60)
    seconds = total_seconds - minutes * 60
    sec_int = int(seconds)
    millis = int(round((seconds - sec_int) * 1000))

    if millis == 1000:
        millis = 0
        sec_int += 1
        if sec_int == 60:
            sec_int = 0
            minutes += 1

    return f"{sign}{minutes}:{sec_int:02d}.{millis:03d}"

# ========================
# DATACLASS
# ========================

@dataclass
class RowCalc:
    category: str
    disciplina: str
    sexo: str
    name: str
    club: str
    time_text: str
    atleta_s: float
    testigo_s: float
    diff_s: float
    pct_vs: float
    pct_slower: float
    selected: bool

# ========================
# INICIALIZAR SESSION STATE
# ========================

if "categories" not in st.session_state:
    st.session_state.categories = {
        "K1 M 1000": {
            "nombre": "Kayak Masculino – 1000 m",
            "disciplina": "Kayak",
            "sexo": "Masculino",
            "testigo": "",
            "cutoff": 105.0,
            "max_selected": 999,
            "data": []
        },
        "C1 M 1000": {
            "nombre": "Canoa Masculino – 1000 m",
            "disciplina": "Canoa",
            "sexo": "Masculino",
            "testigo": "",
            "cutoff": 105.0,
            "max_selected": 999,
            "data": []
        },
        "K1 F 500": {
            "nombre": "Kayak Femenino – 500 m",
            "disciplina": "Kayak",
            "sexo": "Femenino",
            "testigo": "",
            "cutoff": 105.0,
            "max_selected": 999,
            "data": []
        },
        "C1 F 200": {
            "nombre": "Canoa Femenina – 200 m",
            "disciplina": "Canoa",
            "sexo": "Femenino",
            "testigo": "",
            "cutoff": 105.0,
            "max_selected": 999,
            "data": []
        }
    }

# ========================
# FUNCIONES PRINCIPALES
# ========================

def procesar_datos_categoria(cat_key: str) -> List[RowCalc]:
    """Procesa datos de una categoría y retorna lista de RowCalc ordenada"""
    cat = st.session_state.categories[cat_key]
    
    if not cat["testigo"]:
        return []
    
    try:
        testigo_s = parse_time_to_seconds(cat["testigo"])
        if testigo_s <= 0:
            return []
    except:
        return []
    
    results = []
    
    for row in cat["data"]:
        if not row.get("name") or not row.get("time_text"):
            continue
        
        try:
            atleta_s = parse_time_to_seconds(row["time_text"])
            diff_s = atleta_s - testigo_s
            pct_vs = (atleta_s / testigo_s) * 100.0
            pct_slower = (diff_s / testigo_s) * 100.0
            
            results.append(RowCalc(
                category=cat["nombre"],
                disciplina=cat["disciplina"],
                sexo=cat["sexo"],
                name=row["name"],
                club=row["club"],
                time_text=row["time_text"],
                atleta_s=atleta_s,
                testigo_s=testigo_s,
                diff_s=diff_s,
                pct_vs=pct_vs,
                pct_slower=pct_slower,
                selected=False
            ))
        except:
            continue
    
    # Ordenar por % vs
    results.sort(key=lambda x: x.pct_vs)
    
    # Marcar seleccionados según cutoff y max_selected
    cutoff = cat["cutoff"]
    max_sel = cat["max_selected"]
    selected_count = 0
    
    for i, result in enumerate(results):
        if result.pct_vs <= cutoff and selected_count < max_sel:
            results[i].selected = True
            selected_count += 1
    
    return results

def crear_df_categoria(cat_key: str, con_ranking: bool = True) -> pd.DataFrame:
    """Crea DataFrame para una categoría"""
    results = procesar_datos_categoria(cat_key)
    
    if not results:
        return pd.DataFrame()
    
    data = []
    for i, rc in enumerate(results, 1):
        data.append({
            "Rank": i if con_ranking else "-",
            "Nombre": rc.name,
            "Club": rc.club,
            "Tiempo": rc.time_text,
            "Dif": format_seconds_to_time(rc.diff_s),
            "% vs": f"{rc.pct_vs:.2f}%",
            "% + lento": f"{rc.pct_slower:+.2f}%",
            "Seleccionado": "✓" if rc.selected else ""
        })
    
    return pd.DataFrame(data)

def generar_excel_categoria(cat_key: str) -> bytes:
    """Genera archivo Excel para una categoría"""
    cat = st.session_state.categories[cat_key]
    results = procesar_datos_categoria(cat_key)
    
    if not results:
        return None
    
    df = crear_df_categoria(cat_key)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Metadata
        metadata_df = pd.DataFrame({
            "Campo": ["Categoría", "Tiempo testigo", "Corte (%)", "Máx. seleccionados", "Exportado"],
            "Valor": [
                cat["nombre"],
                cat["testigo"],
                cat["cutoff"],
                cat["max_selected"],
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ]
        })
        metadata_df.to_excel(writer, sheet_name='Resultados', startrow=0, index=False)
        df.to_excel(writer, sheet_name='Resultados', startrow=7, index=False)
    
    return output.getvalue()

def generar_excel_ranking(todas_categorias: List[str], disc_filter: str, sexo_filter: str, top_n: int) -> bytes:
    """Genera archivo Excel con ranking global"""
    all_results = []
    
    for cat_key in todas_categorias:
        results = procesar_datos_categoria(cat_key)
        all_results.extend(results)
    
    # Aplicar filtros
    if disc_filter != "Todos":
        all_results = [r for r in all_results if r.disciplina == disc_filter]
    if sexo_filter != "Todos":
        all_results = [r for r in all_results if r.sexo == sexo_filter]
    
    all_results.sort(key=lambda x: x.pct_vs)
    all_results = all_results[:top_n] if top_n > 0 else all_results
    
    if not all_results:
        return None
    
    data = []
    for i, rc in enumerate(all_results, 1):
        data.append({
            "Rank": i,
            "Disciplina": rc.disciplina,
            "Sexo": rc.sexo,
            "Categoría": rc.category,
            "Nombre": rc.name,
            "Club": rc.club,
            "Tiempo": rc.time_text,
            "% vs": f"{rc.pct_vs:.2f}%",
            "Dif": format_seconds_to_time(rc.diff_s),
            "Seleccionado": "✓" if rc.selected else ""
        })
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        filter_info = pd.DataFrame({
            "Campo": ["Filtro Disciplina", "Filtro Sexo", "Top N", "Exportado"],
            "Valor": [disc_filter, sexo_filter, top_n, datetime.now().strftime("%Y-%m-%d %H:%M")]
        })
        filter_info.to_excel(writer, sheet_name='Ranking', startrow=0, index=False)
        df.to_excel(writer, sheet_name='Ranking', startrow=6, index=False)
    
    return output.getvalue()

# ========================
# PÁGINA PRINCIPAL
# ========================

st.title("🚣 Cálculo de Posiciones Canotaje")
st.markdown("Calcula ranking de atletas respecto a tiempo testigo con selección automática.")

# Crear tabs
tabs = st.tabs(["K1 M 1000", "C1 M 1000", "K1 F 500", "C1 F 200", "🏆 RANKING GLOBAL"])

# ========================
# PESTAÑAS DE CATEGORÍAS
# ========================

cat_keys = ["K1 M 1000", "C1 M 1000", "K1 F 500", "C1 F 200"]

for idx, cat_key in enumerate(cat_keys):
    with tabs[idx]:
        cat = st.session_state.categories[cat_key]
        
        st.subheader(cat["nombre"])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cat["testigo"] = st.text_input(
                "Tiempo testigo",
                value=cat["testigo"],
                placeholder="1:45.32 o 105.32",
                key=f"testigo_{cat_key}"
            )
        
        with col2:
            cat["cutoff"] = st.number_input(
                "Corte selección (% vs testigo)",
                min_value=50.0,
                max_value=200.0,
                value=cat["cutoff"],
                step=0.25,
                key=f"cutoff_{cat_key}"
            )
        
        with col3:
            cat["max_selected"] = st.number_input(
                "Máx. seleccionados",
                min_value=1,
                value=cat["max_selected"],
                key=f"max_sel_{cat_key}"
            )
        
        # Tabla editable
        st.markdown("**Datos de atletas**")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Input para agregar nuevo atleta
            col_a, col_b, col_c, col_btn = st.columns([2, 2, 2, 1])
            with col_a:
                new_name = st.text_input("Nombre", key=f"new_name_{cat_key}", placeholder="Nombre")
            with col_b:
                new_club = st.text_input("Club", key=f"new_club_{cat_key}", placeholder="Club")
            with col_c:
                new_time = st.text_input("Tiempo", key=f"new_time_{cat_key}", placeholder="1:45.32")
            with col_btn:
                if st.button("➕", key=f"add_{cat_key}", help="Agregar fila"):
                    if new_name or new_club or new_time:
                        cat["data"].append({
                            "name": new_name,
                            "club": new_club,
                            "time_text": new_time
                        })
                        st.rerun()
        
        # Mostrar datos existentes en tabla editable
        if cat["data"]:
            st.markdown("**Atletas ingresados:**")
            
            # Crear tabla con DataFrame editable
            df_temp = pd.DataFrame(cat["data"])
            
            if not df_temp.empty:
                edited_df = st.data_editor(
                    df_temp,
                    use_container_width=True,
                    hide_index=True,
                    key=f"editor_{cat_key}"
                )
                
                # Actualizar datos desde el editor
                for i, row in edited_df.iterrows():
                    if i < len(cat["data"]):
                        cat["data"][i]["name"] = row["name"]
                        cat["data"][i]["club"] = row["club"]
                        cat["data"][i]["time_text"] = row["time_text"]
            
            # Botón para eliminar todas las filas
            if st.button("🗑️ Limpiar tabla", key=f"clear_{cat_key}"):
                cat["data"] = []
                st.rerun()
        
        st.divider()
        
        # Botones de acción
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Procesar datos", key=f"process_{cat_key}"):
                st.rerun()
        
        with col2:
            csv_data = None
            if cat["data"]:
                # Generar CSV desde datos
                csv_buffer = io.StringIO()
                csv_buffer.write("Nombre,Club,Tiempo\n")
                for row in cat["data"]:
                    csv_buffer.write(f'{row["name"]},{row["club"]},{row["time_text"]}\n')
                csv_data = csv_buffer.getvalue()
            
            if csv_data:
                st.download_button(
                    "📥 Descargar CSV",
                    data=csv_data,
                    file_name=f"atletas_{cat_key}.csv",
                    mime="text/csv",
                    key=f"download_csv_{cat_key}"
                )
        
        with col3:
            excel_data = generar_excel_categoria(cat_key)
            if excel_data:
                st.download_button(
                    "📁 Descargar Excel",
                    data=excel_data,
                    file_name=f"seleccionados_{cat_key}.xlsx",
                    mime="application/vnd.ms-excel",
                    key=f"download_excel_{cat_key}"
                )
        
        # Subir archivo
        uploaded_file = st.file_uploader(
            "📤 Cargar CSV o Excel",
            type=["csv", "xlsx"],
            key=f"upload_{cat_key}"
        )
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                cat["data"] = []
                for _, row in df.iterrows():
                    cat["data"].append({
                        "name": str(row.iloc[0]) if len(row) > 0 else "",
                        "club": str(row.iloc[1]) if len(row) > 1 else "",
                        "time_text": str(row.iloc[2]) if len(row) > 2 else ""
                    })
                
                st.success(f"✓ Cargados {len(cat['data'])} atletas")
                st.rerun()
            except Exception as e:
                st.error(f"Error al cargar archivo: {e}")
        
        st.divider()
        
        # Mostrar resultados
        df_resultado = crear_df_categoria(cat_key)
        
        if not df_resultado.empty:
            st.markdown("**Resultados:**")
            st.dataframe(df_resultado, use_container_width=True, hide_index=True)
            
            # Estadísticas
            results = procesar_datos_categoria(cat_key)
            selected_count = sum(1 for r in results if r.selected)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total atletas", len(results))
            with col2:
                st.metric("Seleccionados", selected_count)
            with col3:
                st.metric("Testigo", cat["testigo"] or "-")
            with col4:
                st.metric("Corte", f"{cat['cutoff']:.1f}%")
        else:
            st.info("Ingresa datos y un tiempo testigo para ver resultados")

# ========================
# PESTAÑA RANKING GLOBAL
# ========================

with tabs[4]:
    st.subheader("🏆 RANKING GLOBAL")
    st.markdown("Ranking ordenado por el mejor % vs su tiempo testigo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        top_n = st.number_input("Mostrar Top N", min_value=1, value=50, step=1)
    
    with col2:
        disc_filter = st.selectbox("Filtrar disciplina", ["Todos", "Kayak", "Canoa"])
    
    with col3:
        sexo_filter = st.selectbox("Filtrar sexo", ["Todos", "Masculino", "Femenino"])
    
    with col4:
        if st.button("🔄 Actualizar Ranking"):
            st.rerun()
    
    st.divider()
    
    # Recopilar todos los resultados
    all_results = []
    for cat_key in cat_keys:
        all_results.extend(procesar_datos_categoria(cat_key))
    
    # Aplicar filtros
    if disc_filter != "Todos":
        all_results = [r for r in all_results if r.disciplina == disc_filter]
    if sexo_filter != "Todos":
        all_results = [r for r in all_results if r.sexo == sexo_filter]
    
    all_results.sort(key=lambda x: x.pct_vs)
    
    if all_results:
        # Crear DataFrame
        data = []
        for i, rc in enumerate(all_results[:top_n], 1):
            data.append({
                "Rank": i,
                "Disciplina": rc.disciplina,
                "Sexo": rc.sexo,
                "Categoría": rc.category,
                "Nombre": rc.name,
                "Club": rc.club,
                "Tiempo": rc.time_text,
                "% vs": f"{rc.pct_vs:.2f}%",
                "Dif": format_seconds_to_time(rc.diff_s)
            })
        
        df_ranking = pd.DataFrame(data)
        st.dataframe(df_ranking, use_container_width=True, hide_index=True)
        
        # Descargar Excel
        excel_data = generar_excel_ranking(cat_keys, disc_filter, sexo_filter, top_n)
        if excel_data:
            st.download_button(
                "📁 Descargar Excel (Ranking)",
                data=excel_data,
                file_name="ranking_global.xlsx",
                mime="application/vnd.ms-excel"
            )
        
        # Estadísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total atletas", len(all_results))
        with col2:
            st.metric("Mostrados (Top N)", min(top_n, len(all_results)))
        with col3:
            st.metric("Seleccionados", sum(1 for r in all_results if r.selected))
    else:
        st.info("No hay datos. Carga datos en las pestañas de categorías.")

# ========================
# FOOTER
# ========================

st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    <p>Cálculo de Posiciones Canotaje | Selecciona atletas automáticamente según el corte de porcentaje</p>
</div>
""", unsafe_allow_html=True)
