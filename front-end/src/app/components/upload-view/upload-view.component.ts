import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { KnowledgeDoc, AreaId } from '../../models/models';
import { AREAS, ChatService, areaIdToUploadCategory } from '../../core/chat.service';

interface DocumentInventoryResponse {
  documents: Array<{
    filename: string;
    relative_path: string;
    category: string;
    owner: string;
    modified_at: string;
  }>;
  total: number;
}

@Component({
  selector: 'nexus-upload-view',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './upload-view.component.html',
  styleUrl: './upload-view.component.scss',
})
export class UploadViewComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly chat = inject(ChatService);

  readonly docs = signal<KnowledgeDoc[]>([]);
  readonly isDragging = signal(false);
  readonly isProcessing = signal(false);
  readonly areas = AREAS;
  readonly uploadCategory = signal<AreaId | 'general'>('general');

  readonly alertMessage = signal<string | null>(null);
  readonly alertType = signal<'success' | 'error' | 'info' | null>(null);

  private readonly pendingFiles = new Map<string, File>();

  ngOnInit(): void {
    const selected = this.chat.selectedArea();
    if (selected) {
      this.uploadCategory.set(selected as AreaId);
    }
    this.loadInventory();
  }

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

  onCategoryChange(event: Event): void {
    const value = (event.target as HTMLSelectElement).value as AreaId | 'general';
    this.uploadCategory.set(value);
  }

  processAll(): void {
    this.alertMessage.set(null);
    this.alertType.set(null);

    if (this.pendingFiles.size === 0) {
      void this.triggerIngestOnly();
      return;
    }

    this.isProcessing.set(true);
    const fileCount = this.pendingFiles.size;
    this.docs.update((list) =>
      list.map((d) => (d.status === 'procesando' ? { ...d, status: 'procesando', progress: 40 } : d)),
    );

    const form = new FormData();
    form.append('category', areaIdToUploadCategory(this.uploadCategory()));
    for (const file of this.pendingFiles.values()) {
      form.append('files', file, file.name);
    }

    const processingIds = new Set(this.pendingFiles.keys());
    this.http.post<{ status: string; message: string }>('/api/upload', form).subscribe({
      next: (res) => {
        this.docs.update((list) =>
          list.map((d) =>
            processingIds.has(d.id)
              ? { ...d, status: 'procesando', progress: 80 }
              : d,
          ),
        );
        this.pendingFiles.clear();
        this.alertMessage.set(`✅ Archivo(s) guardados correctamente. Indexando en la base de conocimientos...`);
        this.alertType.set('info');
        this.triggerIngestOnly(fileCount, processingIds);
      },
      error: (err) => {
        this.isProcessing.set(false);
        const detail = err.error?.detail || 'No se pudieron subir los archivos. Verifica que el formato sea soportado y no sea un borrador.';
        this.alertMessage.set(`⚠️ Error al subir archivo: ${detail}`);
        this.alertType.set('error');
        this.docs.update((list) =>
          list.map((d) =>
            processingIds.has(d.id) ? { ...d, status: 'error', progress: 0 } : d,
          ),
        );
      },
    });
  }

  private triggerIngestOnly(uploadedCount?: number, processingIds?: Set<string>): void {
    this.http.post<{ status: string; message: string }>('/api/ingest', {}).subscribe({
      next: () => {
        this.isProcessing.set(false);
        this.chat.refreshOperationalStats();
        if (processingIds) {
          this.docs.update((list) =>
            list.map((d) =>
              processingIds.has(d.id)
                ? { ...d, status: 'listo', progress: 100 }
                : d,
            ),
          );
        }
        this.loadInventory();
        const msg = uploadedCount
          ? `🎉 ¡Éxito! Se guardaron e indexaron ${uploadedCount} archivo(s). El agente ya puede responder preguntas sobre esta información.`
          : '🔄 Base de conocimientos reindexada correctamente.';
        this.alertMessage.set(msg);
        this.alertType.set('success');
      },
      error: () => {
        this.isProcessing.set(false);
        this.alertMessage.set('⚠️ Los archivos se guardaron pero ocurrió un error al reindexar la base de datos.');
        this.alertType.set('error');
        if (processingIds) {
          this.docs.update((list) =>
            list.map((d) =>
              processingIds.has(d.id) ? { ...d, status: 'listo', progress: 100 } : d,
            ),
          );
        }
      },
    });
  }

  private loadInventory(): void {
    this.http.get<DocumentInventoryResponse>('/api/documents').subscribe({
      next: (response) => {
        const mapped: KnowledgeDoc[] = response.documents.map((doc, index) => ({
          id: `inv-${index}-${doc.filename}`,
          name: doc.filename,
          area: doc.category,
          status: 'listo',
        }));
        this.docs.set(mapped);
      },
      error: () => {
        this.docs.set([]);
      },
    });
  }

  private addFiles(files: FileList): void {
    const added: KnowledgeDoc[] = Array.from(files).map((f, i) => {
      const id = `new-${Date.now()}-${i}`;
      this.pendingFiles.set(id, f);
      return {
        id,
        name: f.name,
        area: this.areas.find((a) => a.id === this.uploadCategory())?.label ?? 'General',
        status: 'procesando',
        progress: 10,
      };
    });
    this.docs.update((list) => [...added, ...list]);
  }
}
