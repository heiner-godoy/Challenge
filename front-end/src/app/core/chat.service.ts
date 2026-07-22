import { Injectable, signal } from '@angular/core';
import { Area, AgentStatus, ChatMessage, ConversationSummary, SourceRef } from '../models/models';

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
  'Política de privacidad',
  'Días de vacaciones disponibles',
  'Contacto de soporte IT',
];

const MOCK_HISTORY: ConversationSummary[] = [
  { id: 'c1', title: 'Política de reembolso', time: '10:42', group: 'Hoy' },
  { id: 'c2', title: 'Días de vacaciones disponibles', time: '09:15', group: 'Hoy' },
  { id: 'c3', title: 'Arquitectura de sistemas', time: '16:30', group: 'Ayer' },
  { id: 'c4', title: 'Calendario de campañas Q1', time: '14:20', group: 'Ayer' },
];

interface MockAnswer {
  text: string;
  bulletPoints?: string[];
  sources: SourceRef[];
}

const FALLBACK_ANSWER: MockAnswer = {
  text: 'No encontré documentos relacionados con tu pregunta en la base de conocimiento actual.',
  sources: [],
};

const MOCK_ANSWERS: Record<string, MockAnswer> = {
  reembolso: {
    text: 'Aquí tienes la información sobre la política de reembolso:',
    bulletPoints: [
      'Plazo máximo: 30 días calendario desde la recepción del producto',
      'Condiciones: producto sin uso, empaque original, etiquetas intactas',
      'Reembolso: se procesa en 5-7 días hábiles',
    ],
    sources: [
      { fileName: 'política_reembolso.docx', matchPercent: 95 },
      { fileName: 'faq_clientes.md', matchPercent: 78 },
    ],
  },
  pedido: {
    text: 'Para rastrear tu pedido:',
    bulletPoints: [
      'Ingresa a "Mis pedidos" con tu número de orden',
      'Recibirás notificaciones automáticas en cada cambio de estado',
      'El tiempo estimado de entrega aparece en el detalle del pedido',
    ],
    sources: [{ fileName: 'guia_envios.pdf', matchPercent: 91 }],
  },
  privacidad: {
    text: 'Sobre nuestra política de privacidad:',
    bulletPoints: [
      'Tus datos se usan únicamente para procesar pedidos y mejorar el servicio',
      'No compartimos información personal con terceros sin tu consentimiento',
      'Puedes solicitar la eliminación de tus datos en cualquier momento',
    ],
    sources: [{ fileName: 'política_privacidad.pdf', matchPercent: 97 }],
  },
  vacaciones: {
    text: 'Según la política de beneficios vigente:',
    bulletPoints: [
      'Los colaboradores acumulan 15 días hábiles de vacaciones al año',
      'Las solicitudes se aprueban con mínimo 2 semanas de anticipación',
      'Los días no tomados pueden acumularse hasta por un año adicional',
    ],
    sources: [{ fileName: 'manual_rrhh.docx', matchPercent: 89 }],
  },
  soporte: {
    text: 'Para contactar al soporte de IT:',
    bulletPoints: [
      'Canal interno: #soporte-it en el chat corporativo',
      'Correo: soporte.it@empresa.com',
      'Horario de atención: lunes a viernes, 8:00 a.m. – 6:00 p.m.',
    ],
    sources: [{ fileName: 'directorio_ti.xlsx', matchPercent: 84 }],
  },
};

@Injectable({ providedIn: 'root' })
export class ChatService {
  readonly messages = signal<ChatMessage[]>([]);
  readonly status = signal<AgentStatus>('idle');
  readonly documentCount = signal(47);
  readonly queriesToday = signal(12);
  readonly lastUpdatedLabel = signal('hace 2 horas');
  readonly history = signal<ConversationSummary[]>(MOCK_HISTORY);
  readonly selectedArea = signal<string | null>(null);

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
    this.status.set('searching');

    const delay = 900 + Math.random() * 700;
    window.setTimeout(() => {
      const answer = this.resolveAnswer(trimmed);
      const agentMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'agent',
        text: answer.text,
        bulletPoints: answer.bulletPoints,
        sources: answer.sources,
        responseTimeSeconds: Number((delay / 1000).toFixed(1)),
        timestamp: new Date(),
        feedback: null,
      };
      this.messages.update((list) => [...list, agentMessage]);
      this.status.set('idle');
      this.queriesToday.update((n) => n + 1);
    }, delay);
  }

  setFeedback(messageId: string, value: 'up' | 'down'): void {
    this.messages.update((list) =>
      list.map((m) => (m.id === messageId ? { ...m, feedback: value } : m)),
    );
  }

  clearHistory(): void {
    this.history.set([]);
  }

  private resolveAnswer(question: string): MockAnswer {
    const q = question.toLowerCase();
    if (q.includes('reembolso') || q.includes('devol')) return MOCK_ANSWERS['reembolso'];
    if (q.includes('rastre') || q.includes('pedido') || q.includes('envío') || q.includes('envio'))
      return MOCK_ANSWERS['pedido'];
    if (q.includes('privacidad') || q.includes('datos personales')) return MOCK_ANSWERS['privacidad'];
    if (q.includes('vacacion')) return MOCK_ANSWERS['vacaciones'];
    if (q.includes('soporte') || q.includes(' ti') || q.includes('it ')) return MOCK_ANSWERS['soporte'];
    return FALLBACK_ANSWER;
  }
}
