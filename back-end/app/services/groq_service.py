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
    - Prioriza respuestas concisas y útiles; cuando sea apropiado, ofrece un breve paso siguiente (p. ej. dónde o a quién consultar).

    Reglas clave (no remover):
    1. Usa SOLO la información provista en el bloque de contexto a continuación para fundamentar tus respuestas.
    2. Cuando cites información, incluye la fuente y, si está disponible, la ubicación o sección y el Área responsable.
    3. Si no hay suficiente información en el contexto, indícalo claramente y sugiere acciones prácticas (contactar a la persona responsable, revisar X documento, abrir un ticket a it@...).
    4. No inventes políticas, procedimientos ni cifras. Si necesitas suposiciones, márcalas explícitamente como tales.

    Contexto recuperado (fragmentos relevantes):
    {context_text}

    Entrega esperada:
    - Primera línea: resumen breve (1-2 frases) de la respuesta.
    - Seguido: explicación clara y pasos accionables si aplica.
    - Al final: lista de fuentes citadas extraídas del contexto (si las hay).

    Si la consulta es de naturaleza legal o implica riesgos (seguridad, cumplimiento), recomienda contactar al área responsable.
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
