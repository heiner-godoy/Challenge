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
    if (this.pendingFiles.size === 0) {
      void this.triggerIngestOnly();
      return;
    }

    this.isProcessing.set(true);
    this.docs.update((list) =>
      list.map((d) => (d.status === 'procesando' ? { ...d, status: 'procesando', progress: 40 } : d)),
    );

    const form = new FormData();
    form.append('category', areaIdToUploadCategory(this.uploadCategory()));
    for (const file of this.pendingFiles.values()) {
      form.append('files', file, file.name);
    }

    this.http.post<{ status: string; message: string }>('/api/upload', form).subscribe({
      next: () => {
        this.pendingFiles.clear();
        this.triggerIngestOnly();
      },
      error: () => {
        this.isProcessing.set(false);
        this.docs.update((list) =>
          list.map((d) => (d.status === 'procesando' ? { ...d, status: 'error' } : d)),
        );
      },
    });
  }

  private triggerIngestOnly(): void {
    this.http.post('/api/ingest', {}).subscribe({
      next: () => {
        this.isProcessing.set(false);
        this.chat.refreshOperationalStats();
        this.loadInventory();
      },
      error: () => {
        this.isProcessing.set(false);
        this.docs.update((list) =>
          list.map((d) => (d.status === 'procesando' ? { ...d, status: 'error' } : d)),
        );
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
