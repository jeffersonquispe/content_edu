# core/rag_service.py
import boto3
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class RAGEducativoService:
    """
    Servicio RAG especializado para contenido educativo peruano
    Integra Amazon Bedrock Knowledge Bases con documentos del MINEDU
    """
    
    def __init__(self):
        self.bedrock_runtime = boto3.client('bedrock-runtime')
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')
        
        # IDs de tu Knowledge Base (configurar después de crear)
        self.knowledge_base_ids = {
            'curriculo_nacional': 'KB-CURRICULO-ID-HERE',
            'rubricas_evaluacion': 'KB-RUBRICAS-ID-HERE', 
            'metodologias': 'KB-METODOLOGIAS-ID-HERE',
            'recursos_educativos': 'KB-RECURSOS-ID-HERE'
        }
    
    def buscar_contexto_curricular(self, query: str, grado: int, area: str = "ciencia_tecnologia") -> Dict:
        """
        Busca contexto relevante en la base de conocimiento curricular
        """
        try:
            # Consulta enriquecida con contexto educativo
            query_enriquecida = f"""
            Buscar información sobre: {query}
            Contexto: Educación secundaria {grado}º grado, área de {area.replace('_', ' ')}
            País: Perú, Currículo Nacional de Educación Básica
            """
            
            response = self.bedrock_agent.retrieve(
                knowledgeBaseId=self.knowledge_base_ids['curriculo_nacional'],
                retrievalQuery={
                    'text': query_enriquecida
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 10,
                        'overrideSearchType': 'HYBRID'  # Combina búsqueda semántica y por palabras clave
                    }
                }
            )
            
            # Procesar resultados
            documentos_relevantes = []
            for result in response.get('retrievalResults', []):
                documentos_relevantes.append({
                    'contenido': result.get('content', {}).get('text', ''),
                    'fuente': result.get('location', {}).get('s3Location', {}).get('uri', ''),
                    'score': result.get('score', 0),
                    'metadata': result.get('metadata', {})
                })
            
            return {
                'documentos': documentos_relevantes,
                'total_encontrados': len(documentos_relevantes)
            }
            
        except Exception as e:
            logger.error(f"Error en búsqueda RAG: {e}")
            return {'documentos': [], 'total_encontrados': 0}
    
    def generar_con_contexto_rag(self, prompt: str, contexto_documentos: List[Dict]) -> str:
        """
        Genera contenido usando RAG con documentos del MINEDU
        """
        try:
            # Construir contexto enriquecido
            contexto_rag = self._construir_contexto_educativo(contexto_documentos)
            
            prompt_con_rag = f"""
Human: Eres un experto en educación peruana especializado en el Currículo Nacional de Educación Básica. 

CONTEXTO OFICIAL DEL MINEDU:
{contexto_rag}

INSTRUCCIONES:
{prompt}

Basa tu respuesta EXCLUSIVAMENTE en el contexto oficial proporcionado. Si no encuentras información suficiente en el contexto, menciona qué información específica faltaría para completar la respuesta.

Estructura tu respuesta de manera profesional y alineada con los documentos oficiales del MINEDU.
Assistant:
"""
            
            body = json.dumps({
                "prompt": prompt_con_rag,
                "max_tokens_to_sample": 2000,
                "temperature": 0.3,  # Más conservador para contenido educativo oficial
                "top_p": 0.9
            })
            
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId='anthropic.claude-v2:1',
                accept='application/json',
                contentType='application/json'
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body.get('completion', '')
            
        except Exception as e:
            logger.error(f"Error en generación RAG: {e}")
            return f"Error al generar contenido con RAG: {e}"
    
    def _construir_contexto_educativo(self, documentos: List[Dict]) -> str:
        """
        Construye el contexto enriquecido para el prompt
        """
        if not documentos:
            return "No se encontró contexto específico en los documentos oficiales."
        
        contexto_partes = []
        for i, doc in enumerate(documentos[:5], 1):  # Limitar a top 5 documentos
            fuente = doc.get('fuente', 'Documento MINEDU')
            contenido = doc.get('contenido', '')
            score = doc.get('score', 0)
            
            contexto_partes.append(f"""
DOCUMENTO {i} (Relevancia: {score:.2f}):
Fuente: {fuente}
Contenido:
{contenido}
---""")
        
        return '\n'.join(contexto_partes)

# Función integrada para programación curricular con RAG
def generar_programacion_curricular_rag(grado: int, competencia: str, capacidades: str, contenidos: str) -> str:
    """
    Genera programación curricular usando RAG con documentos oficiales del MINEDU
    """
    try:
        rag_service = RAGEducativoService()
        
        # 1. Buscar contexto relevante
        query_busqueda = f"""
        programación curricular ciencia y tecnología {grado} grado secundaria
        competencias capacidades desempeños criterios evaluación
        {competencia} {contenidos}
        """
        
        contexto = rag_service.buscar_contexto_curricular(
            query=query_busqueda,
            grado=grado,
            area="ciencia_tecnologia"
        )
        
        # 2. Generar con contexto RAG
        prompt_programacion = f"""
        Genera una programación curricular completa para {grado}º de secundaria en el área de Ciencia y Tecnología.

        DATOS ESPECÍFICOS:
        - Grado: {grado}º de secundaria  
        - Competencia: {competencia}
        - Capacidades: {capacidades}
        - Contenidos: {contenidos}

        FORMATO REQUERIDO:
        Crea una tabla completa con las columnas: COMPETENCIA, CAPACIDADES, CONTENIDOS, DESEMPEÑOS, CRITERIOS DE EVALUACIÓN, INSTRUMENTOS DE EVALUACIÓN.

        REQUISITOS:
        - Usar EXCLUSIVAMENTE la información oficial del contexto proporcionado
        - Los desempeños deben ser específicos, observables y medibles
        - Criterios de evaluación alineados con cada desempeño
        - Instrumentos variados y pertinentes
        - Formato profesional del MINEDU
        """
        
        resultado = rag_service.generar_con_contexto_rag(
            prompt=prompt_programacion,
            contexto_documentos=contexto['documentos']
        )
        
        # 3. Agregar metadatos de las fuentes consultadas
        fuentes_consultadas = [doc['fuente'] for doc in contexto['documentos'][:3]]
        resultado_final = f"""{resultado}

FUENTES OFICIALES CONSULTADAS:
{chr(10).join([f"- {fuente}" for fuente in fuentes_consultadas])}

Total de documentos oficiales analizados: {contexto['total_encontrados']}
"""
        
        return resultado_final
        
    except Exception as e:
        logger.error(f"Error en programación curricular RAG: {e}")
        return f"Error al generar programación curricular con RAG: {e}"

# Configuración de AWS Knowledge Bases - Script de setup
def setup_knowledge_bases():
    """
    Script para configurar las Knowledge Bases necesarias
    """
    setup_script = """
    # 1. Crear bucket S3 para documentos
    aws s3 mb s3://minedu-documentos-educativos-peru
    
    # 2. Subir documentos del MINEDU
    aws s3 sync ./documentos_minedu/ s3://minedu-documentos-educativos-peru/curriculo/
    
    # 3. Crear Knowledge Base via CLI o Console
    # - Currículo Nacional de Educación Básica
    # - Rúbricas de evaluación
    # - Metodologías de enseñanza
    # - Recursos educativos
    
    # 4. Configurar embeddings con Amazon Titan
    # 5. Sincronizar datos
    """
    return setup_script

# Ejemplo de uso
if __name__ == "__main__":
    # Test básico
    rag_service = RAGEducativoService()
    
    test_query = "competencias ciencia tecnología 3 secundaria"
    resultado = rag_service.buscar_contexto_curricular(
        query=test_query,
        grado=3,
        area="ciencia_tecnologia"  
    )
    
    print(f"Documentos encontrados: {resultado['total_encontrados']}")
    for doc in resultado['documentos'][:2]:
        print(f"Score: {doc['score']}")
        print(f"Contenido: {doc['contenido'][:200]}...")
        print("---")