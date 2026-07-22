import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { KnowledgeDoc } from '../../models/models';

const SEED_DOCS: KnowledgeDoc[] = [
  { id: 'd1', name: 'política_privacidad.pdf', area: 'Legal', status: 'listo' },
  { id: 'd2', name: 'tarifas_envio.xlsx', area: 'Financiero', status: 'listo' },
  { id: 'd3', name: 'onboarding_nuevos.pptx', area: 'RRHH', status: 'procesando', progress: 62 },
];

@Component({
  selector: 'nexus-upload-view',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './upload-view.component.html',
  styleUrl: './upload-view.component.scss',
})
export class UploadViewComponent {
  readonly docs = signal<KnowledgeDoc[]>(SEED_DOCS);
  readonly isDragging = signal(false);

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(true);
  }

  onDragLeave(): void {
    this.isDragging.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(false);
    const files = event.dataTransfer?.files;
    if (files) this.addFiles(files);
  }

  onFilePicked(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files) this.addFiles(input.files);
    input.value = '';
  }

  processAll(): void {
    this.docs.update((list) =>
      list.map((d) => (d.status === 'procesando' ? { ...d, status: 'listo', progress: 100 } : d)),
    );
  }

  private addFiles(files: FileList): void {
    const added: KnowledgeDoc[] = Array.from(files).map((f, i) => ({
      id: `new-${Date.now()}-${i}`,
      name: f.name,
      area: 'Sin clasificar',
      status: 'procesando',
      progress: 10,
    }));
    this.docs.update((list) => [...list, ...added]);
  }
}
