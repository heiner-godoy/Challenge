import { HttpClient } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';
import { Area, AreaId, AgentStatus, ChatMessage, ConversationSummary } from '../models/models';

declare global {
  interface Window {
    __APP_CONFIG__?: {
      apiBaseUrl?: string;
    };
  }
}

export const AREA_FOLDER_SLUG: Record<AreaId, string> = {
  legal: 'juridico',
  operacional: 'operaciones',
  financiero: 'financiero',
  comunicacion: 'comunicacion',
  logistica: 'logistica',
  rrhh: 'rh',
  marketing: 'marketing',
  datos: 'tecnologia',
  id: 'id',
  calidad: 'calidad',
  estrategico: 'estrategico',
};

export function areaIdToUploadCategory(area: AreaId | 'general' | null): string {
  if (!area || area === 'general') return 'general';
  return AREA_FOLDER_SLUG[area] ?? area;
}

export function areaIdToCategoryFilter(area: AreaId | null): string | undefined {
  if (!area) return undefined;
  return area;
}

export const API_BASE_URL = (typeof window !== 'undefined' && window.__APP_CONFIG__?.apiBaseUrl)
  ? window.__APP_CONFIG__.apiBaseUrl
  : '/';

const API_CHAT = `${API_BASE_URL}api/chat`;
const API_HEALTH = `${API_BASE_URL}api/health`;

export const AREAS: Area[] = [
  { id: 'legal', label: 'Legal', icon: '⚖️' },
  { id: 'operacional', label: 'Operacional', icon: '⚙️' },
  { id: 'financiero', label: 'Financiero', icon: '💰' },
  { id: 'comunicacion', label: 'Comunicación', icon: '📣' },
  { id: 'logistica', label: 'Logística', icon: '🚚' },
  { id: 'rrhh', label: 'RRHH', icon: '🧑\u200d🤝\u200d🧑' },
  { id: 'marketing', label: 'Marketing', icon: '📈' },
  { id: 'datos', label: 'Datos/Sistemas', icon: '🖥️' },
  { id: 'id', label: 'I+D', icon: '🔬' },
  { id: 'calidad', label: 'Calidad', icon: '✅' },
  { id: 'estrategico', label: 'Estratégico', icon: '🧭' },
];

export const QUICK_SUGGESTIONS: string[] = [
  '¿Cómo rastreo mi pedido?',
  'Restaurar pedido',
  'Política de privacidad',
  'Días de vacaciones disponibles',
  'Contacto de soporte IT',
];

@Injectable({ providedIn: 'root' })
export class ChatService {
  readonly messages = signal<ChatMessage[]>([]);
  readonly status = signal<AgentStatus>('idle');
  readonly documentCount = signal(0);
  readonly queriesToday = signal(0);
  readonly lastUpdatedLabel = signal('—');
  readonly history = signal<ConversationSummary[]>([]);
  readonly selectedArea = signal<AreaId | null>(null);

  constructor(private readonly http: HttpClient) {
    this.refreshOperationalStats();
  }

  refreshOperationalStats(): void {
    this.http
      .get<{ documents_on_disk?: number; documents_indexed?: number }>(API_HEALTH)
      .subscribe({
        next: (health) => {
          const count = health.documents_on_disk ?? health.documents_indexed ?? 0;
          this.documentCount.set(count);
          this.lastUpdatedLabel.set('sincronizado con el backend');
        },
        error: () => {
          this.lastUpdatedLabel.set('backend no disponible');
        },
      });
  }

  sendMessage(text: string): void {
    const trimmed = text.trim();
    if (!trimmed) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      text: trimmed,
      timestamp: new Date(),
      status: 'sent',
    };
    this.messages.update((list) => [...list, userMessage]);
    this.history.update((list) => [
      ...list,
      {
        id: userMessage.id,
        title: trimmed.slice(0, 60),
        time: userMessage.timestamp.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }),
        group: 'Hoy',
      },
    ]);
    this.status.set('searching');

    const requestStart = performance.now();
    const requestBody = {
      message: trimmed,
      category: areaIdToCategoryFilter(this.selectedArea()),
      history: this.messages().map((message) => ({
        role: message.role === 'user' ? 'user' : 'assistant',
        content: message.text,
      })),
    };

    this.http.post<{ answer: string; sources?: Array<{ filename: string; score: number; category?: string; owner?: string; location?: string; modified_at?: string | null; excerpt?: string }> }>(API_CHAT, requestBody).subscribe({
      next: (response) => {
        const responseTimeSeconds = Number(((performance.now() - requestStart) / 1000).toFixed(1));
        const sources = response.sources?.map((source) => ({
          fileName: source.filename,
          matchPercent: Math.round((source.score ?? 0) * 100),
          category: source.category,
          owner: source.owner,
          location: source.location,
          modifiedAt: source.modified_at,
          excerpt: source.excerpt,
        })) ?? [];

        const agentMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'agent',
          text: response.answer,
          bulletPoints: [],
          sources,
          responseTimeSeconds,
          timestamp: new Date(),
          feedback: null,
        };
        this.messages.update((list) => [...list, agentMessage]);
        this.status.set('idle');
        this.queriesToday.update((n) => n + 1);
      },
      error: () => {
        const responseTimeSeconds = Number(((performance.now() - requestStart) / 1000).toFixed(1));
        const agentMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'agent',
          text: 'No se pudo conectar con el agente RAG. Verifica que el backend esté disponible e inténtalo de nuevo.',
          bulletPoints: [],
          sources: [],
          responseTimeSeconds,
          timestamp: new Date(),
          feedback: null,
        };
        this.messages.update((list) => [...list, agentMessage]);
        this.status.set('idle');
        this.queriesToday.update((n) => n + 1);
      },
    });
  }

  setFeedback(messageId: string, value: 'up' | 'down'): void {
    this.messages.update((list) =>
      list.map((m) => (m.id === messageId ? { ...m, feedback: value } : m)),
    );
  }

  clearHistory(): void {
    this.history.set([]);
    this.messages.set([]);
  }

}