import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatMessage } from '../../models/models';

@Component({
  selector: 'nexus-chat-message',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './chat-message.component.html',
  styleUrl: './chat-message.component.scss',
})
export class ChatMessageComponent {
  @Input({ required: true }) message!: ChatMessage;
  @Output() feedback = new EventEmitter<'up' | 'down'>();

  readonly downReasons = [
    'La respuesta no era útil',
    'Era incorrecta',
    'No entendió mi pregunta',
  ];
  showReasons = false;

  timeLabel(date: Date): string {
    return date.toLocaleTimeString('es-CO', { hour: 'numeric', minute: '2-digit' });
  }

  onFeedback(value: 'up' | 'down'): void {
    this.feedback.emit(value);
    this.showReasons = value === 'down';
  }
}
