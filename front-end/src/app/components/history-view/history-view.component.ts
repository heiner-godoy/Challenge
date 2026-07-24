import { Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ChatService } from '../../core/chat.service';

@Component({
  selector: 'nexus-history-view',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './history-view.component.html',
  styleUrl: './history-view.component.scss',
})
export class HistoryViewComponent {
  private readonly chat = inject(ChatService);
  readonly history = this.chat.history;

  readonly today = computed(() => this.history().filter((c) => c.group === 'Hoy'));
  readonly yesterday = computed(() => this.history().filter((c) => c.group === 'Ayer'));

  clear(): void {
    this.chat.clearHistory();
  }
}
