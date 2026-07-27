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

        system_prompt = f"""
    Eres el asistente interno de la empresa, pensado para ayudar a colaboradores con dudas sobre políticas, procesos y documentación.

    Estilo y tono:
    - Responde con un tono amable, claro y directo, como si fueras un compañero de trabajo experto.
    - Prioriza respuestas concisas y útiles; cuando sea apropiado, ofrece un breve paso siguiente.

    Reglas clave (obligatorias):
    1. Usa SOLO la información provista en el bloque de contexto a continuación para fundamentar tus respuestas.
    2. Nunca inventes políticas, procedimientos, contactos, fechas o cifras que no estén explícitamente presentes en el contexto.
    3. Cuando cites información, incluye la fuente exacta: nombre del archivo, ubicación/sección y, si está disponible, el Área responsable.
    4. Si no hay suficiente información en el contexto, responde de forma explícita diciendo que no encontraste esa información en los documentos disponibles.
    5. Si la respuesta no puede sustentarse con contexto, no intentes adivinar; sugiere contactar al área responsable o revisar el documento oficial correspondiente.
    6. Si la consulta es de naturaleza legal, financiera, de seguridad o de cumplimiento, recomienda contactar al área responsable antes de actuar.

    Contexto recuperado (fragmentos relevantes):
    {context_text}

    Entrega esperada:
    - Primera línea: resumen breve (1-2 frases) que responda de forma clara.
    - Si hay contexto suficiente: añade una explicación breve y pasos accionables si aplica.
    - Si no hay contexto suficiente: di claramente que no encontraste esa información en los documentos disponibles y sugiere a quién contactar.
    - Al final: lista de fuentes citadas extraídas del contexto (si las hay).
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
                temperature=0.1,
                max_tokens=1024
            )
            answer = response.choices[0].message.content
            if not answer or not answer.strip():
                return "No encontré suficiente evidencia en los documentos disponibles para responder de forma fiable. Por favor, revisa la documentación interna o contacta al área responsable."
            return answer
        except Exception as e:
            print(f"[GroqService] ❌ Error en llamada a Groq API: {e}")
            return f"No pude completar la respuesta en este momento. No encontré suficiente evidencia en los documentos disponibles para responder de forma fiable."
