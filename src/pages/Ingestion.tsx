import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type ParsedTransaction = {
  amount: number;
  category: string;
  merchant?: string | null;
  transaction_type: string;
  payment_mode: string;
  timestamp: string;
  description?: string | null;
};

type UploadResponse = {
  file_name: string;
  parsed_count: number;
  imported_count: number;
  preview: ParsedTransaction[];
};

type SmsResponse = {
  parsed_count: number;
  transactions: ParsedTransaction[];
};

const formatCurrency = (value: number) => `₹${Math.round(value).toLocaleString("en-IN")}`;

const Ingestion = () => {
  const [smsInput, setSmsInput] = useState("");
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);

  const [smsResult, setSmsResult] = useState<SmsResponse | null>(null);
  const [csvResult, setCsvResult] = useState<UploadResponse | null>(null);
  const [pdfResult, setPdfResult] = useState<UploadResponse | null>(null);

  const [loading, setLoading] = useState<"sms" | "csv" | "pdf" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const parseSms = async () => {
    const messages = smsInput
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);

    if (!messages.length) return;

    setLoading("sms");
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/ingestion/sms/import?persist=true`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages }),
      });

      if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
      }

      const data = (await response.json()) as UploadResponse;
      setSmsResult({ parsed_count: data.parsed_count, transactions: data.preview });
    } catch (err) {
      setError(err instanceof Error ? err.message : "SMS parse failed");
    } finally {
      setLoading(null);
    }
  };

  const uploadCsv = async () => {
    if (!csvFile) return;

    setLoading("csv");
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", csvFile);

      const response = await fetch(`${API_BASE_URL}/api/v1/ingestion/upload/csv?persist=true`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
      }

      const data = (await response.json()) as UploadResponse;
      setCsvResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSV upload failed");
    } finally {
      setLoading(null);
    }
  };

  const uploadPdf = async () => {
    if (!pdfFile) return;

    setLoading("pdf");
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", pdfFile);

      const response = await fetch(`${API_BASE_URL}/api/v1/ingestion/upload/pdf?persist=false`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
      }

      const data = (await response.json()) as UploadResponse;
      setPdfResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF upload failed");
    } finally {
      setLoading(null);
    }
  };

  const renderPreview = (rows: ParsedTransaction[]) => {
    if (!rows.length) {
      return <p className="text-sm text-muted-foreground">No parsed transactions yet.</p>;
    }

    return (
      <div className="space-y-2">
        {rows.slice(0, 6).map((row, index) => (
          <div key={index} className="bg-surface-3 rounded-lg p-3 flex items-center justify-between gap-3">
            <div>
              <p className="text-sm text-foreground font-medium">
                {row.merchant || row.category.replace("_", " ")} · {row.transaction_type}
              </p>
              <p className="text-xs text-muted-foreground">{row.description || row.timestamp}</p>
            </div>
            <p className="text-sm text-primary font-semibold">{formatCurrency(row.amount)}</p>
          </div>
        ))}
      </div>
    );
  };

  return (
    <DashboardLayout title="Data Ingestion" subtitle="SMS parsing and statement uploads (CSV/PDF)">
      {error && (
        <div className="glass-card p-4 mb-6 border border-error/40">
          <p className="text-sm text-error">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-2">SMS Parser</h3>
          <p className="text-xs text-muted-foreground mb-3">Paste one SMS per line to parse and import.</p>
          <textarea
            value={smsInput}
            onChange={(e) => setSmsInput(e.target.value)}
            rows={8}
            placeholder="Your account is debited by INR 420.00 at Swiggy via UPI on 2026-04-16"
            className="w-full bg-surface-3 border border-gold-muted rounded-lg p-3 text-sm text-foreground placeholder:text-muted-foreground"
          />
          <button
            onClick={parseSms}
            disabled={loading === "sms"}
            className="mt-3 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm disabled:opacity-60"
          >
            {loading === "sms" ? "Parsing..." : "Parse & Import SMS"}
          </button>

          <div className="mt-4">
            <p className="text-xs text-muted-foreground mb-2">Parsed Preview ({smsResult?.parsed_count ?? 0})</p>
            {renderPreview(smsResult?.transactions ?? [])}
          </div>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-2">CSV Upload</h3>
          <p className="text-xs text-muted-foreground mb-3">Upload a bank statement CSV and import rows.</p>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setCsvFile(e.target.files?.[0] ?? null)}
            className="w-full text-sm text-muted-foreground"
          />
          <button
            onClick={uploadCsv}
            disabled={loading === "csv" || !csvFile}
            className="mt-3 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm disabled:opacity-60"
          >
            {loading === "csv" ? "Uploading..." : "Upload CSV"}
          </button>

          {csvResult && (
            <p className="text-xs text-muted-foreground mt-3">
              Parsed: {csvResult.parsed_count} · Imported: {csvResult.imported_count}
            </p>
          )}

          <div className="mt-4">
            <p className="text-xs text-muted-foreground mb-2">Parsed Preview</p>
            {renderPreview(csvResult?.preview ?? [])}
          </div>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-2">PDF Upload</h3>
          <p className="text-xs text-muted-foreground mb-3">Upload PDF statements for extraction preview.</p>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setPdfFile(e.target.files?.[0] ?? null)}
            className="w-full text-sm text-muted-foreground"
          />
          <button
            onClick={uploadPdf}
            disabled={loading === "pdf" || !pdfFile}
            className="mt-3 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm disabled:opacity-60"
          >
            {loading === "pdf" ? "Extracting..." : "Upload PDF"}
          </button>

          {pdfResult && (
            <p className="text-xs text-muted-foreground mt-3">
              Parsed: {pdfResult.parsed_count} · Imported: {pdfResult.imported_count}
            </p>
          )}

          <div className="mt-4">
            <p className="text-xs text-muted-foreground mb-2">Parsed Preview</p>
            {renderPreview(pdfResult?.preview ?? [])}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Ingestion;
