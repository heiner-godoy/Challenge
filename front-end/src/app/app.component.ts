import { Component, inject } from '@angular/core';
import { RouterOutlet, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { SidebarComponent } from './components/sidebar/sidebar.component';
import { ThemeService } from './core/theme.service';

@Component({
  selector: 'nexus-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, SidebarComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  readonly theme = inject(ThemeService);
  // `collapsed` controla una sidebar reducida (icon-only). No removemos la barra del DOM.
  collapsed = false;

  onCloseSidebar(): void {
    // Al cerrar desde la propia barra la colapsamos en lugar de eliminarla.
    this.collapsed = true;
  }

  onToggleSidebar(): void {
    this.collapsed = !this.collapsed;
  }
}
