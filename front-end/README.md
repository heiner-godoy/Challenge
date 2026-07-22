# Nexus — Frontend del Agente de IA Corporativo

Implementación en Angular 18 (standalone components + signals) del diseño
"Nexus" para NexusShop: sidebar con áreas y estadísticas, chat con burbujas,
fuentes y feedback, pantalla de bienvenida, subida/indexado de documentos
e historial. Incluye modo oscuro con la paleta exacta del brief.

## Cómo correrlo

```bash
ñ
npm start        # ng serve → http://localhost:4200
```

Build de producción:

```bash
npm run build
```

## Estructura

```
src/
  styles.scss                     Tokens de diseño (colores, tipografía, dark mode)
  app/
    app.component.*               Shell: sidebar + topbar móvil + router-outlet
    app.routes.ts                 Rutas: /, /documentos, /historial
    core/
      theme.service.ts            Toggle de modo oscuro (persistido en localStorage)
      chat.service.ts             Estado del chat + datos simulados (áreas, respuestas)
    models/models.ts               Interfaces (ChatMessage, Area, KnowledgeDoc, etc.)
    components/
      sidebar/                    Logo, áreas, estadísticas, footer (config/ayuda)
      chat-view/                  Header, bienvenida, mensajes, sugerencias, input
        chat-message.component.*  Burbuja individual (usuario/agente + fuentes + 👍👎)
      upload-view/                Drag&drop de documentos + lista con estado
      history-view/                Historial agrupado por día
```

## Notas de implementación

- **Datos simulados**: `ChatService` responde con contenido mock (política de
  reembolso, envíos, privacidad, vacaciones, soporte IT) según palabras clave,
  simulando latencia y el estado "🔍 Nexus está buscando en 47 documentos...".
  Sustituye `resolveAnswer()` por una llamada real a tu backend/RAG.
- **Accesibilidad**: foco visible (`:focus-visible`), `aria-live` en el log de
  mensajes, `aria-pressed` en toggles, `prefers-reduced-motion` respetado,
  tipografía base de 16px.
- **Modo oscuro**: clase `.dark` en `<html>`, con las variables CSS exactas
  de la tabla de colores del brief.
- **Responsive**: por debajo de 860px el sidebar se convierte en un panel
  deslizante activado por el botón ≡ del topbar móvil.
