import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./components/chat-view/chat-view.component').then((m) => m.ChatViewComponent),
  },
  {
    path: 'documentos',
    loadComponent: () =>
      import('./components/upload-view/upload-view.component').then((m) => m.UploadViewComponent),
  },
  {
    path: 'historial',
    loadComponent: () =>
      import('./components/history-view/history-view.component').then((m) => m.HistoryViewComponent),
  },
  { path: '**', redirectTo: '' },
];
