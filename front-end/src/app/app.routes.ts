import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./components/chat-view/chat-view.component').then((m) => m.ChatViewComponent),
  },
  {
    path: 'history',
    loadComponent: () =>
      import('./components/history-view/history-view.component').then((m) => m.HistoryViewComponent),
  },
  { path: '**', redirectTo: '' },
];
