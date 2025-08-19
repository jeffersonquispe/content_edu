import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from collections import Counter
import os
from dotenv import load_dotenv

load_dotenv()

# Importar el DynamoDBManager
from core.database_management import DynamoDBManager
# Inicializar DynamoDB Manager
db_manager = DynamoDBManager()

# --- Funciones de Utilidad para el Dashboard ---


sentiment_map = {
    'POSITIVE': 5,
    'NEUTRAL': 3,
    'NEGATIVE': 1,
    'MIXED': 2 
}

# --- Funciones de Utilidad para el Dashboard ---

def calculate_average_sentiment_score(comments_df):
    """Calcula el puntaje promedio de sentimiento (1-5) a partir de los puntajes de Comprehend."""
    if comments_df.empty:
        return 0.0
    
    # Aquí ya no necesitas definir sentiment_map, solo usarlo
    comments_df['sentiment_score_numeric'] = comments_df['sentiment'].map(sentiment_map).fillna(0)
    
    return comments_df['sentiment_score_numeric'].mean()


def create_word_cloud_data(comments_df):
    """Prepara datos para una nube de palabras (simplificado para Streamlit)."""
    if comments_df.empty:
        return []
    
    all_words = ' '.join(comments_df['text']).lower().split()
    stopwords = set(["el", "la", "los", "las", "un", "una", "unos", "unas", "de", "con", "en", "para", "por", "es", "no", "y", "pero", "que", "muy", "me", "su", "mi", "se"])
    filtered_words = [word for word in all_words if word.isalpha() and word not in stopwords]
    
    word_counts = Counter(filtered_words)
    # Retorna los N más comunes
    return [{'text': word, 'value': count} for word, count in word_counts.most_common(50)]

# --- Interfaz de Streamlit ---

st.set_page_config(layout="wide", page_title="Dashboard de Análisis de Comentarios de Snacks")

st.title("Dashboard de Análisis de Comentarios de Clientes")
st.markdown("Visualización en tiempo real del sentimiento y las tendencias de los comentarios sobre los nuevos snacks.")

# Sidebar para acciones
st.sidebar.header("Acciones")
if st.sidebar.button("Refrescar Datos"):
    st.cache_data.clear() # Limpiar caché para forzar recarga de datos
    st.experimental_rerun() # Volver a ejecutar la app

# --- Cargar datos ---
@st.cache_data(ttl=60) # Cachea los datos por 60 segundos
def load_data():
    data = db_manager.get_all_comments()
    df = pd.DataFrame(data)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp', ascending=True)
    return df

comments_df = load_data()

if comments_df.empty:
    st.warning("No hay comentarios disponibles en la base de datos de DynamoDB. Asegúrate de que tu Lambda esté procesando datos en S3.")
else:
    # Sección 1: Rendimiento General de los Comentarios
    st.header("Rendimiento General de los Comentarios")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Volumen de Comentarios Totales")
        comments_by_time = comments_df.set_index('timestamp').resample('H').size().reset_index(name='count')
        fig_volume = px.line(comments_by_time, x='timestamp', y='count', title='Comentarios por Hora')
        st.plotly_chart(fig_volume, use_container_width=True)

    with col2:
        st.subheader("Distribución del Sentimiento")
        sentiment_counts = comments_df['sentiment'].value_counts().reset_index()
        sentiment_counts.columns = ['Sentimiento', 'Cantidad']
        fig_sentiment = px.pie(sentiment_counts, values='Cantidad', names='Sentimiento', 
                               title='Porcentaje de Sentimientos', hole=0.3)
        st.plotly_chart(fig_sentiment, use_container_width=True)

    with col3:
        st.subheader("Puntaje de Sentimiento Promedio")
        avg_sentiment_kpi = calculate_average_sentiment_score(comments_df)
        st.metric(label="Puntaje Promedio (1-5)", value=f"{avg_sentiment_kpi:.2f}")

    st.subheader("Nube de Palabras Clave")
    word_cloud_data = create_word_cloud_data(comments_df)
    if word_cloud_data:
        st.write("Las palabras más frecuentes son:")
        st.write(", ".join([f"**{w['text']}** ({w['value']})" for w in word_cloud_data]))
    else:
        st.info("No hay palabras clave para mostrar.")

    st.markdown("<br>", unsafe_allow_html=True) # Espacio

    # Sección 2: Resúmenes de Bedrock y Detalles
    st.header("📝 Resúmenes de Bedrock y Detalles")
    st.markdown("---")


    # Para un dashboard real-time, estos resúmenes serían generados por la Lambda y almacenados en DynamoDB.
    st.subheader("Últimos Resúmenes de IAGen")
    # st.table(comments_df[['timestamp', 'text', 'summary_bedrock']].tail(5))
    
    latest_comments_display = db_manager.get_latest_comments(limit=5)
    if latest_comments_display:
        st.dataframe(pd.DataFrame(latest_comments_display)[['timestamp', 'text', 'sentiment', 'entities']])
        st.info("Nota: Para resúmenes generados por IAGen, la Lambda debería almacenarlos en DynamoDB junto con el comentario.")
    else:
        st.info("No hay comentarios recientes para mostrar.")


    st.subheader("Comentarios Detallados")
    # Filtros para comentarios
    selected_sentiment = st.multiselect("Filtrar por Sentimiento", comments_df['sentiment'].unique(), comments_df['sentiment'].unique())
    filtered_comments_df = comments_df[comments_df['sentiment'].isin(selected_sentiment)]
    
    st.dataframe(filtered_comments_df[['timestamp', 'text', 'sentiment', 'entities']].sort_values(by='timestamp', ascending=False))
    
    st.markdown("<br>", unsafe_allow_html=True) # Espacio

    # Sección 3: Tendencias en el Tiempo
    st.header("📉 Tendencias en el Tiempo")
    st.markdown("---")

    st.subheader("Tendencia del Sentimiento Promedio")
    sentiment_trend_df = comments_df.copy()
    # Aquí sentiment_map ya estará definido globalmente
    sentiment_trend_df['sentiment_score_numeric'] = sentiment_trend_df['sentiment'].map(sentiment_map).fillna(0)
    sentiment_daily_avg = sentiment_trend_df.set_index('timestamp').resample('D')['sentiment_score_numeric'].mean().reset_index()
    sentiment_daily_avg.columns = ['Fecha', 'Puntaje Promedio']
    fig_sentiment_trend = px.line(sentiment_daily_avg, x='Fecha', y='Puntaje Promedio', 
                                title='Evolución del Puntaje de Sentimiento Promedio')
    st.plotly_chart(fig_sentiment_trend, use_container_width=True)

    # Comparación de Productos (Placeholder - Requiere datos de otros productos)
    st.subheader("Comparación de Productos (Ejemplo)")
    st.info("Esta sección compara el sentimiento del nuevo snack con otros productos existentes. Se necesitan datos adicionales de otros productos para esta funcionalidad.")
    # Ejemplo de datos para comparación (reemplazar con datos reales de DynamoDB)
    comparison_data = {
        'Producto': ['Nuevo Snack', 'Snack A (Existente)', 'Snack B (Existente)'],
        'Puntaje Sentimiento Promedio': [avg_sentiment_kpi, 4.2, 3.5]
    }
    comparison_df = pd.DataFrame(comparison_data)
    fig_comparison = px.bar(comparison_df, x='Producto', y='Puntaje Sentimiento Promedio',
                            title='Comparación de Sentimiento entre Productos')
    st.plotly_chart(fig_comparison, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True) # Espacio

    # Sección 4: Métricas de Valor para el Negocio
    st.header("🚀 Métricas de Valor para el Negocio")
    st.markdown("---")

    st.subheader("Puntaje de Valor del Producto (PVG)")
    # Simulación de PVG: Ponderar positivos en base a entidades clave
    positive_comments = comments_df[comments_df['sentiment'] == 'POSITIVE']
    # En un caso real, esto sería más complejo, por ejemplo, buscando menciones de 'sabor', 'textura', 'nutritivo'
    if not positive_comments.empty:
        pvg_score = positive_comments['sentiment_score_numeric'].mean() * 1.2 # Ejemplo de ponderación
        st.metric(label="Puntaje de Valor del Producto (PVG)", value=f"{pvg_score:.2f}")
    else:
        st.info("No hay suficientes comentarios positivos para calcular el PVG.")

    st.subheader("Alerta de Problema Recurrente")
    # Buscar entidades negativas recurrentes
    negative_comments = comments_df[comments_df['sentiment'] == 'NEGATIVE']
    all_negative_entities = [entity['Text'].lower() for comment in negative_comments['entities'] for entity in comment]
    negative_entity_counts = Counter(all_negative_entities)

    alert_threshold = 3 # Si un tema negativo se repite X veces
    recurrent_issues = {entity: count for entity, count in negative_entity_counts.items() if count >= alert_threshold}

    if recurrent_issues:
        st.error("🚨 Alerta: ¡Problemas recurrentes detectados!")
        for issue, count in recurrent_issues.items():
            st.write(f"- El tema **'{issue}'** se repite **{count}** veces en comentarios negativos.")
        st.warning("Se recomienda investigar estos temas de inmediato.")
    else:
        st.success("🎉 No se detectaron problemas recurrentes significativos.")