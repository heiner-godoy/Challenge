import {
  AfterViewChecked,
  Component,
  ElementRef,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ChatService, QUICK_SUGGESTIONS } from '../../core/chat.service';
import { ChatMessageComponent } from './chat-message.component';
import { UploadViewComponent } from '../upload-view/upload-view.component';

const MAX_CHARS = 800;

@Component({
  selector: 'nexus-chat-view',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, ChatMessageComponent, UploadViewComponent],
  templateUrl: './chat-view.component.html',
  styleUrl: './chat-view.component.scss',
})
export class ChatViewComponent implements AfterViewChecked {
  private readonly chat = inject(ChatService);

  @ViewChild('scrollAnchor') private scrollAnchor?: ElementRef<HTMLDivElement>;

  readonly messages = this.chat.messages;
  readonly status = this.chat.status;
  readonly documentCount = this.chat.documentCount;
  readonly suggestions = QUICK_SUGGESTIONS;
  readonly maxChars = MAX_CHARS;

  draft = '';
  private lastMessageCount = 0;

  send(): void {
    if (!this.draft.trim() || this.draft.length > this.maxChars) return;
    this.chat.sendMessage(this.draft);
    this.draft = '';
  }

  useSuggestion(text: string): void {
    this.draft = text;
    this.send();
  }

  onFeedback(messageId: string, value: 'up' | 'down'): void {
    this.chat.setFeedback(messageId, value);
  }

  startNewSession(): void {
    this.chat.clearHistory();
    this.draft = '';
  }

  scrollToUpload(): void {
    document.getElementById('upload-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  ngAfterViewChecked(): void {
    if (this.messages().length !== this.lastMessageCount) {
      this.lastMessageCount = this.messages().length;
      this.scrollAnchor?.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }
}
