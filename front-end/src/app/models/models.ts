export type AreaId =
  | 'legal'
  | 'operacional'
  | 'financiero'
  | 'comunicacion'
  | 'logistica'
  | 'rrhh'
  | 'marketing'
  | 'datos'
  | 'id'
  | 'calidad'
  | 'estrategico';

export interface Area {
  id: AreaId;
  label: string;
  icon: string;
}

export interface SourceRef {
  fileName: string;
  matchPercent: number;
  category?: string;
  owner?: string;
  location?: string;
  modifiedAt?: string | null;
  excerpt?: string;
}

export type FeedbackValue = 'up' | 'down' | null;

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  text: string;
  bulletPoints?: string[];
  timestamp: Date;
  sources?: SourceRef[];
  responseTimeSeconds?: number;
  feedback?: FeedbackValue;
  status?: 'sending' | 'sent' | 'error';
}

export type AgentStatus = 'idle' | 'searching' | 'error';

export interface ConversationSummary {
  id: string;
  title: string;
  time: string;
  group: 'Hoy' | 'Ayer';
}

export type DocStatus = 'listo' | 'procesando' | 'error';

export interface KnowledgeDoc {
  id: string;
  name: string;
  area: string;
  status: DocStatus;
  progress?: number;
}
