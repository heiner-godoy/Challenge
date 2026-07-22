from typing import List, Dict, Any, Optional
from app.config import settings

class TavilyService:
    """
    =============================================================================
    SERVICIO DE BÚSQUEDA WEB CON TAVILY API & LANGCHAIN
    =============================================================================
    Integra la herramienta de búsqueda de Tavily para LangChain permitiendo al 
    agente consultar información en tiempo real en la web cuando las respuestas
    no se encuentran en los documentos internos de la empresa.
    """

    def __init__(self):
        self.api_key = settings.TAVILY_API_KEY
        self.tool = None
        self._init_tavily_tool()

    def _init_tavily_tool(self):
        """Inicializa la herramienta Tavily Search de LangChain con la API Key configurada."""
        if not self.api_key or self.api_key == "tu_tavily_api_key_aqui":
            print("[TavilyService] ⚠️ ATENCIÓN: TAVILY_API_KEY no configurada en .env. Búsqueda web desactivada.")
            return

        try:
            # Intento de inicialización usando langchain_tavily o langchain_community
            try:
                from langchain_tavily import TavilySearch
                self.tool = TavilySearch(tavily_api_key=self.api_key)
                print("[TavilyService] ✅ Herramienta LangChain TavilySearch inicializada (langchain_tavily).")
            except Exception:
                from langchain_community.tools.tavily_search import TavilySearchResults
                self.tool = TavilySearchResults(tavily_api_key=self.api_key)
                print("[TavilyService] ✅ Herramienta LangChain TavilySearchResults inicializada (langchain_community).")
        except Exception as e:
            print(f"[TavilyService] ❌ Error al inicializar la herramienta Tavily de LangChain: {e}")

    def is_available(self) -> bool:
        """Indica si el servicio de Tavily Search está activo y configurado correctamente."""
        return self.tool is not None

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Ejecuta una búsqueda web utilizando Tavily a través de LangChain.
        
        Args:
            query (str): Término o consulta a buscar en la web.
            max_results (int): Cantidad máxima de resultados a retornar.
            
        Returns:
            List[Dict[str, Any]]: Lista de dicts con información de los resultados web.
        """
        if not self.is_available():
            print("[TavilyService] ⚠️ No se puede realizar la búsqueda web: Tavily API Key no presente.")
            return []

        try:
            # Ejecución según el tipo de herramienta inicializada
            if hasattr(self.tool, "invoke"):
                res = self.tool.invoke({"query": query, "max_results": max_results})
            else:
                res = self.tool.run(query)

            if isinstance(res, list):
                return res
            elif isinstance(res, dict) and "results" in res:
                return res["results"]
            else:
                return [{"content": str(res)}]
        except Exception as e:
            print(f"[TavilyService] ❌ Error ejecutando búsqueda Tavily con LangChain: {e}")
            return []

    def get_tool(self):
        """Retorna la herramienta de LangChain lista para integrarse en un Agente LangChain."""
        return self.tool
