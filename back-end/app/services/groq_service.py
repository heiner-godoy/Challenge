from typing import List, Dict
import groq
from app.config import settings

class GroqService:
    """
    =============================================================================
    SERVICIO DE INFERENCIA LLM CON GROQ API (CON GOBERNANZA DE DATOS)
    =============================================================================
    Integra los metadatos de Categoría y Responsable de Área (Ownership) en el
    prompt de contexto para garantizar la trazabilidad corporativa en las respuestas.
    """

    def __init__(self):
        self.client = None
        if settings.GROQ_API_KEY:
            try:
                self.client = groq.Groq(api_key=settings.GROQ_API_KEY)
                print("[GroqService] ✅ Cliente de Groq API inicializado correctamente.")
            except Exception as e:
                print(f"[GroqService] ❌ Error inicializando cliente Groq: {e}")
        else:
            print("[GroqService] ⚠️ ATENCIÓN: GROQ_API_KEY no encontrada en .env")

    def generate_answer(self, query: str, context_chunks: List[Dict], history: List[Dict] = None) -> str:
        """
        Construye el prompt estructurado con las instrucciones de comportamiento corporativo
        y los fragmentos enriquecidos con su Área y Responsable (Ownership).
        """
        if not self.client:
            return (
                "⚠️ La GROQ_API_KEY no está configurada o no es válida. "
                "Por favor, configure las variables de entorno en el archivo .env para habilitar la síntesis del agente corporativo."
            )

        if context_chunks:
            context_text = "\n\n".join([
                f"--- DOCUMENTO OFICIAL FUENTE: {chunk['source']} | Ubicación: {chunk.get('location', 'General')} | Área: {chunk['category']} | Responsable: {chunk['owner']} | Fecha: {chunk.get('modified_at', 'N/A')} (Relevancia: {chunk['score']}) ---\n{chunk['content']}"
                for chunk in context_chunks
            ])
        else:
            context_text = "No se encontraron documentos internos relevantes en la base de conocimientos."

        system_prompt = f"""Eres un Agente de Inteligencia Artificial Corporativo diseñado para ayudar a los colaboradores de la empresa a resolver dudas sobre políticas, procesos y documentación interna.

PRINCIPIOS DE GOBERNANZA DE DATOS Y CALIDAD:
1. Responde de forma clara, profesional, concisa y amable.
2. Basate ÚNICAMENTE en la siguiente información de contexto recuperada de los documentos oficiales vigentes de la empresa.
3. Si la información está disponible en el contexto, cítala indicando la fuente, ubicación exacta (Página, Diapositiva, Sección o Hoja) y el Área/Departamento responsable.
4. Si la consulta requiere una aclaración más profunda o la respuesta NO está en el contexto, aconseja educadamente al colaborador contactar al Responsable del Área citada.
5. NO inventes políticas corporativas ni asumas datos que no estén sustentados en las fuentes oficiales ("Garbage in, garbage out").

CONTEXTO RECUPERADO DE DOCUMENTOS OFICIALES:
{context_text}
"""


        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            for msg in history[-4:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": query})

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=0.2,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[GroqService] ❌ Error en llamada a Groq API: {e}")
            return f"Lo sentimos, ocurrió un error al procesar tu solicitud con el modelo Groq: {str(e)}"
