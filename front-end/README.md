# Frontend — Agente Corporativo de IA

Aplicación web en Angular 18 para interactuar con el agente RAG corporativo desde un chat simple, accesible y orientado a colaboradores.

## Qué incluye

- Chat conversacional conectado al backend del agente.
- Respuestas con fuentes y metadatos de los documentos recuperados.
- Botones de feedback por mensaje.
- Historial de conversaciones y opción para iniciar una nueva sesión.
- Vista de subida de documentos para re-ingesta del conocimiento.
- Modo claro/oscuro y diseño responsive.

## Requisitos

- Node.js 18 o superior.
- El backend debe estar corriendo en http://localhost:8000.

## Ejecutar localmente

```bash
cd front-end
npm install
npm start
```

La interfaz queda disponible en:

- http://localhost:4200

## Build de producción

```bash
cd front-end
npm run build
```

## Estructura principal

```text
src/
  app/
    app.component.*           Shell principal con sidebar y router outlet
    app.routes.ts             Rutas: chat, documentos e historial
    core/
      chat.service.ts         Comunicación con /api/chat y /api/health
      theme.service.ts        Manejo del modo oscuro
    components/
      chat-view/              Interfaz del chat y mensajes del agente
      upload-view/            Subida e indexado de documentos
      history-view/           Historial de conversaciones
```

## Integración con el backend

El frontend consume directamente los endpoints del backend:

- POST /api/chat: envía el mensaje del usuario y recibe la respuesta con fuentes.
- GET /api/health: obtiene el estado de salud y el número de documentos indexados.

Para que todo funcione correctamente, el backend debe estar levantado antes de abrir la UI.
