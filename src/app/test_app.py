# test_app.py - Versión mínima para probar
import streamlit as st
import sys
import os

st.title("🧪 Test de Conexión")
st.write("Si ves esto, Streamlit funciona correctamente")

# Test 1: Verificar python-docx
try:
    from docx import Document
    st.success("✅ python-docx importado correctamente")
    docx_ok = True
except ImportError as e:
    st.error(f"❌ python-docx no disponible: {e}")
    docx_ok = False

# Test 2: Verificar path
current_path = os.path.abspath(__file__)
parent_path = os.path.dirname(os.path.dirname(current_path))
st.write(f"**Archivo actual:** {current_path}")
st.write(f"**Directorio padre:** {parent_path}")

# Test 3: Intentar importar servicios
try:
    sys.path.append(parent_path)
    st.write(f"**Paths en sys.path:** {sys.path[-3:]}")
    
    # Mostrar archivos en el directorio
    if os.path.exists(os.path.join(parent_path, 'core')):
        core_files = os.listdir(os.path.join(parent_path, 'core'))
        st.write(f"**Archivos en core/:** {core_files}")
        
        # Intentar importar
        from core.bedrock_services import generar_programacion_curricular
        st.success("✅ Servicios importados correctamente")
        services_ok = True
    else:
        st.error("❌ Directorio 'core' no encontrado")
        services_ok = False
        
except Exception as e:
    st.error(f"❌ Error importando servicios: {e}")
    services_ok = False

# Test simple de formulario
with st.form("test_form"):
    test_input = st.text_input("Campo de prueba", "Hola mundo")
    submitted = st.form_submit_button("Probar")
    
    if submitted:
        st.write(f"Input recibido: {test_input}")

# Resumen
st.write("---")
st.write("**Resumen de tests:**")
st.write(f"- Streamlit: ✅ Funcionando")
st.write(f"- python-docx: {'✅' if docx_ok else '❌'}")
st.write(f"- Servicios Bedrock: {'✅' if 'services_ok' in locals() and services_ok else '❌'}")

if docx_ok and 'services_ok' in locals() and services_ok:
    st.balloons()
    st.success("🎉 Todo listo para usar la aplicación completa!")