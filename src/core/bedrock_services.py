import boto3
import json
import os

from core.rag_service import generar_programacion_curricular_rag

def generar_programacion_curricular_2(grado, competencia, capacidades, contenidos):
    return generar_programacion_curricular_rag(grado, competencia, capacidades, contenidos)

# Función alternativa con mejor manejo de respuestas
def generar_programacion_curricular(grado_secundaria, competencia, capacidades, contenidos, num_iteraciones=3):
    """
    Genera una programación curricular completa para Ciencia y Tecnología 
    utilizando un modelo de lenguaje de Bedrock con técnica de auto-crítica
    y llamadas iterativas a la API.
    """
    try:
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ['AWS_REGION']
        )
       
        # --- PASO 1: Generar la programación inicial ---
        prompt_inicial = f"""
Actúa como especialista en programación curricular. Tu tarea es crear una tabla de programación educativa para estudiantes de {grado_secundaria}º de secundaria del área de Ciencia y Tecnología.

Genera una tabla completa con las siguientes columnas: COMPETENCIA, CAPACIDADES, CONTENIDOS, DESEMPEÑOS, CRITERIOS DE EVALUACIÓN, INSTRUMENTOS DE EVALUACIÓN.

INFORMACIÓN BASE:
---
GRADO: {grado_secundaria}º de secundaria
COMPETENCIA: {competencia}
CAPACIDADES: {capacidades}
CONTENIDOS: {contenidos}
---

INSTRUCCIONES PARA COMPLETAR:
1. Transcribe exactamente la COMPETENCIA y CAPACIDADES proporcionadas
2. Organiza los CONTENIDOS por bloques temáticos (Física, Química)
3. Genera DESEMPEÑOS específicos para {grado_secundaria}º de secundaria que sean:
   - Observables y medibles en el aula
   - Relacionados directamente con los contenidos
   - Apropiados para la edad de los estudiantes
   - Que reflejen las 5 capacidades de indagación científica
   - Entre 12-15 desempeños específicos
4. Crea CRITERIOS DE EVALUACIÓN que permitan medir cada desempeño (2-3 criterios por desempeño)
5. Propón INSTRUMENTOS DE EVALUACIÓN variados:
   - Rúbricas de indagación científica
   - Listas de cotejo para experimentos
   - Escalas de valoración para informes
   - Evaluaciones escritas
   - Portafolios de evidencias
   - Prácticas de laboratorio
6. Presenta todo en formato de tabla clara y organizada
7. Al final incluye:
   - COMPETENCIAS TRANSVERSALES (Se desenvuelve en entornos virtuales y Gestiona su aprendizaje)
   - ENFOQUES TRANSVERSALES (con valores y comportamientos observables)
   - SECUENCIA DE 6 SESIONES DE APRENDIZAJE (con títulos y actividades principales)

CONSIDERACIONES IMPORTANTES:
- Los desempeños deben ser actuaciones específicas que demuestren progreso en el aprendizaje
- Considera la progresión del aprendizaje según el grado educativo
- Incluye aspectos de indagación científica apropiados para la edad
- Los instrumentos deben ser prácticos de implementar en el aula

FORMATO REQUERIDO:
Quiero que me presentes la siguiente información en un formato de texto plano y muy ordenado, 
sin usar tablas ni formato Markdown. Organiza la información en secciones claras con títulos y/0 listas con viñetas.
"""
        
        # Ajustar parámetros del modelo
        body = json.dumps({
            "prompt": f"Human: {prompt_inicial}\n\nAssistant:",
            "max_tokens_to_sample": 4000,  # Aumentar límite de tokens
            "temperature": 0.7,
            "top_p": 0.9,
            "stop_sequences": ["Human:"]  # Evitar que se corte prematuramente
        })
       
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId='anthropic.claude-v2',
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        ultima_programacion = response_body.get('completion')
        
        # Agregar logging para debug
        print(f"Respuesta inicial - Longitud: {len(ultima_programacion) if ultima_programacion else 0}")
        print(f"Primeros 500 caracteres: {ultima_programacion[:500] if ultima_programacion else 'None'}")
       
        # --- PASO 2: Bucle de mejora recursiva (llamadas iterativas) ---
        for i in range(num_iteraciones):
            criterios = [
                "Revisa la programación anterior y mejora la especificidad de los desempeños para que sean más observables y medibles en el contexto educativo. Cada desempeño debe describir claramente qué hará el estudiante.",
                "Analiza la coherencia entre contenidos, desempeños y criterios de evaluación. Verifica que cada criterio permita evaluar efectivamente el desempeño correspondiente y que estén perfectamente alineados.",
                "Revisa y mejora los instrumentos de evaluación para que sean variados, pertinentes y prácticos de implementar en el aula. Incluye tanto instrumentos formativos como sumativos."
            ]
            criterio_actual = criterios[i % len(criterios)]
           
            # El prompt de cada iteración incluye la programación anterior
            prompt_mejora = f"""
Eres un especialista en programación curricular y evaluación educativa. 

Aquí tienes la programación curricular que necesita mejoras:
---
{ultima_programacion}
---

Basándote en la programación anterior, genera una nueva y mejorada versión. Enfócate específicamente en: "{criterio_actual}"

MANTENER:
- El formato de tabla exacto con las 6 columnas
- Todas las secciones adicionales (competencias transversales, enfoques, sesiones)
- La estructura general del documento

MEJORAR:
- La calidad pedagógica del contenido según el criterio especificado
- La pertinencia para estudiantes de {grado_secundaria}º de secundaria
- La claridad y precisión de los elementos a evaluar
- La viabilidad de implementación práctica

Conserva el formato de tabla completo y mejora la calidad del contenido educativo.
"""
           
            body_mejora = json.dumps({
                "prompt": f"Human: {prompt_mejora}\n\nAssistant:",
                "max_tokens_to_sample": 4000,  # Aumentar límite de tokens
                "temperature": 0.7,
                "top_p": 0.9,
                "stop_sequences": ["Human:"]
            })
           
            response_mejora = bedrock_runtime.invoke_model(
                body=body_mejora,
                modelId='anthropic.claude-v2',
                accept='application/json',
                contentType='application/json'
            )
            
            response_body_mejora = json.loads(response_mejora.get('body').read())
            nueva_programacion = response_body_mejora.get('completion')
            
            # Verificar que la nueva respuesta sea válida antes de actualizar
            if nueva_programacion and len(nueva_programacion) > len(ultima_programacion) * 0.5:
                ultima_programacion = nueva_programacion
                print(f"Iteración {i+1} completada - Longitud: {len(ultima_programacion)}")
            else:
                print(f"Iteración {i+1} descartada - Respuesta incompleta")
                break
           
        return ultima_programacion
        
    except Exception as e:
        print(f"Error detallado: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return f"Error al generar la programación curricular: {e}"

def generar_imagen_promocional(prompt_imagen):
    """
    Genera una imagen promocional utilizando un modelo de difusión de Bedrock.
    """
    try:
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ['AWS_REGION']
        )
        prompt = f'''
        Generate a high-quality, professional educational image for a high school.
        The image should be visually appealing and focus on the prompt:
        '{prompt_imagen}'
        '''
        body = json.dumps({
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 10,
            "seed": 0,
            "steps": 50,
        })
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId='stability.stable-diffusion-xl-v1',
            accept='application/json',
            contentType='application/json'
        )
        response_body = json.loads(response.get('body').read())
        image_base64 = response_body.get('artifacts')[0].get('base64')
        return f"data:image/png;base64,{image_base64}"
    except Exception as e:
        return f"Error al generar la imagen: {e}"

def generar_resumen_comentarios(comentarios):
    """
    Genera un resumen de comentarios de clientes utilizando un modelo de lenguaje de Bedrock.
    """
    try:
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ['AWS_REGION']
        )
        
        # Formato de prompt correcto para el modelo de Bedrock
        prompt = f"""
Human: Actúa como un especialista de educacion, experto en calidad educativa. Lee los siguientes comentarios de estudaintes sobre las sesiones y genera un resumen conciso que destaque las opiniones clave, tanto positivas como negativas.
--- Comentarios ---
{comentarios}
---
Resumen:
Assistant:
"""

        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 500,
            "temperature": 0.5,
        })

        response = bedrock_runtime.invoke_model(
            body=body,
            modelId='anthropic.claude-v2',
            accept='application/json',
            contentType='application/json'
        )

        response_body = json.loads(response.get('body').read())
        return response_body.get('completion')

    except Exception as e:
        return f"Error al generar el resumen: {e}"