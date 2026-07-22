import { Component, EventEmitter, Output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AREAS, ChatService } from '../../core/chat.service';
import { ThemeService } from '../../core/theme.service';

@Component({
  selector: 'nexus-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss',
})
export class SidebarComponent {
  private readonly chat = inject(ChatService);
  readonly theme = inject(ThemeService);

  @Output() navigate = new EventEmitter<void>();

  readonly areas = AREAS;
  readonly documentCount = this.chat.documentCount;
  readonly lastUpdatedLabel = this.chat.lastUpdatedLabel;
  readonly queriesToday = this.chat.queriesToday;
  readonly selectedArea = this.chat.selectedArea;

  selectArea(id: string): void {
    this.selectedArea.set(this.selectedArea() === id ? null : id);
    this.navigate.emit();
  }
}
