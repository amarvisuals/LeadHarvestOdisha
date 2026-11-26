"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, CheckCircle2, AlertCircle, Trash2, FileSpreadsheet, Settings2 } from "lucide-react";

export interface FileAuditCard {
  id: string;
  filename: string;
  file_size_bytes: number;
  total_rows: number;
  valid_rows: number;
  blank_rows: number;
  invalid_phone_rows: number;
  duplicate_rows: number;
  column_mapping: Record<string, string>;
  detected_columns: string[];
  status: "ready" | "needs_attention";
}

interface DuplicateFilterUploadProps {
  auditCards: FileAuditCard[];
  knownRecordsCount: number;
  onFilesSelected: (files: FileList) => Promise<void>;
  onClearKnownRecords: () => Promise<void>;
  onUpdateMapping: (auditId: string, mapping: Record<string, string>) => Promise<void>;
}

export default function DuplicateFilterUpload({
  auditCards,
  knownRecordsCount,
  onFilesSelected,
  onClearKnownRecords,
  onUpdateMapping,
}: DuplicateFilterUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [editingCardId, setEditingCardId] = useState<string | null>(null);
  const [editedMapping, setEditedMapping] = useState<Record<string, string>>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await onFilesSelected(e.dataTransfer.files);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await onFilesSelected(e.target.files);
    }
  };

  const startEditMapping = (card: FileAuditCard) => {
    setEditingCardId(card.id);
    setEditedMapping({ ...card.column_mapping });
  };

  const saveMapping = async (cardId: string) => {
    await onUpdateMapping(cardId, editedMapping);
    setEditingCardId(null);
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <FileSpreadsheet className="w-5 h-5 text-brand-600" />
            <span>3. Skip Data You Already Have (Optional)</span>
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Upload past client lists, exports or lead sheets (.xlsx, .xls, .csv). We will automatically audit and skip them.
          </p>
        </div>

        {/* Known Records Counter & Clear */}
        <div className="flex items-center space-x-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl">
          <div className="text-right">
            <p className="text-[10px] uppercase font-semibold text-slate-400">Known Records</p>
            <p className="text-xs font-bold text-brand-700">{knownRecordsCount.toLocaleString()} indexed</p>
          </div>
          {knownRecordsCount > 0 && (
            <button
              type="button"
              onClick={onClearKnownRecords}
              title="Clear all indexed known records"
              className="p-1 text-slate-400 hover:text-rose-600 transition-colors ml-1"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`mt-4 border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
          isDragging
            ? "border-brand-500 bg-brand-50/60 scale-[0.99]"
            : "border-slate-200 hover:border-brand-400 bg-slate-50/50 hover:bg-slate-50"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".xlsx,.xls,.csv"
          onChange={handleFileChange}
          className="hidden"
        />
        <div className="w-12 h-12 rounded-xl bg-brand-100/70 text-brand-700 flex items-center justify-center mx-auto mb-2">
          <UploadCloud className="w-6 h-6" />
        </div>
        <p className="text-sm font-semibold text-slate-800">
          Drop files here, or <span className="text-brand-600 underline">browse</span>
        </p>
        <p className="text-xs text-slate-400 mt-1">
          Accepts multiple Excel (.xlsx, .xls) and CSV files. Automatic column detection applied.
        </p>
      </div>

      {/* Audited File Cards */}
      {auditCards.length > 0 && (
        <div className="mt-4 space-y-3">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Uploaded Files & Audit Summary ({auditCards.length})
          </p>
          {auditCards.map((card) => {
            const isReady = card.status === "ready";
            const isEditing = editingCardId === card.id;

            return (
              <div
                key={card.id}
                className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 hover:bg-slate-50 transition-all"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200/60">
                  <div className="flex items-center space-x-2.5">
                    <div className="p-2 rounded-lg bg-white border border-slate-200 text-slate-700 shadow-xs">
                      <FileSpreadsheet className="w-4 h-4 text-brand-600" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-slate-800 truncate max-w-xs">{card.filename}</p>
                      <p className="text-[11px] text-slate-400">
                        {(card.file_size_bytes / 1024).toFixed(1)} KB • {card.total_rows} total rows
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span
                      className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                        isReady
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : "bg-amber-50 text-amber-700 border border-amber-200"
                      }`}
                    >
                      {isReady ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                      <span>{isReady ? "Ready to dedupe" : "Needs attention"}</span>
                    </span>

                    <button
                      type="button"
                      onClick={() => (isEditing ? saveMapping(card.id) : startEditMapping(card))}
                      className="p-1.5 rounded-lg border border-slate-200 hover:bg-white text-slate-600 text-xs font-medium flex items-center space-x-1"
                    >
                      <Settings2 className="w-3.5 h-3.5" />
                      <span>{isEditing ? "Done" : "Map Columns"}</span>
                    </button>
                  </div>
                </div>

                {/* Audit Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-3 text-xs">
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70">
                    <span className="text-slate-400 block text-[10px]">Valid Records</span>
                    <span className="font-bold text-slate-800">{card.valid_rows}</span>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70">
                    <span className="text-slate-400 block text-[10px]">Blank Rows</span>
                    <span className="font-bold text-slate-600">{card.blank_rows}</span>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70">
                    <span className="text-slate-400 block text-[10px]">Invalid Phone</span>
                    <span className="font-bold text-amber-600">{card.invalid_phone_rows}</span>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70">
                    <span className="text-slate-400 block text-[10px]">Internal Dupes</span>
                    <span className="font-bold text-slate-600">{card.duplicate_rows}</span>
                  </div>
                </div>

                {/* Column Mapping Editor Drawer */}
                {isEditing && (
                  <div className="mt-3 p-3 bg-white rounded-lg border border-brand-200 text-xs space-y-2">
                    <p className="font-semibold text-slate-700">Customize Detected Column Mapping:</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {["business_name", "phone", "address", "city", "category"].map((stdField) => (
                        <div key={stdField} className="flex items-center justify-between">
                          <span className="capitalize text-slate-500 font-medium">
                            {stdField.replace("_", " ")}:
                          </span>
                          <select
                            value={editedMapping[stdField] || ""}
                            onChange={(e) =>
                              setEditedMapping({ ...editedMapping, [stdField]: e.target.value })
                            }
                            className="text-xs bg-slate-50 border border-slate-200 rounded px-2 py-1"
                          >
                            <option value="">-- None --</option>
                            {card.detected_columns.map((c) => (
                              <option key={c} value={c}>
                                {c}
                              </option>
                            ))}
                          </select>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
