import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/+$/, "");
const API_PREFIX = API_BASE_URL.endsWith("/api/v1") ? "" : "/api/v1";

const buildApiUrl = (path: string) => {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${API_PREFIX}${normalizedPath}`;
};

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

const parseErrorResponse = async (response: Response): Promise<string> => {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string" && data.detail.trim()) {
      return data.detail;
    }
    if (typeof data?.error === "string" && data.error.trim()) {
      return data.error;
    }
  } catch {
    // Fall back to generic status text when response is not JSON.
  }

  return `${response.status} ${response.statusText}`;
};

const toUserFacingError = (error: unknown, fallback: string): string => {
  if (error instanceof TypeError) {
    const text = error.message.toLowerCase();
    if (text.includes("failed to fetch") || text.includes("networkerror")) {
      return `Unable to reach backend at ${API_BASE_URL}. Start backend and retry.`;
    }
  }

  return error instanceof Error ? error.message : fallback;
};

const Ingestion = () => {
  const [smsInput, setSmsInput] = useState("");
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [statementPassword, setStatementPassword] = useState("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pdfPassword, setPdfPassword] = useState("");

  const [smsResult, setSmsResult] = useState<SmsResponse | null>(null);
  const [csvResult, setCsvResult] = useState<UploadResponse | null>(null);
  const [pdfResult, setPdfResult] = useState<UploadResponse | null>(null);
  const [csvError, setCsvError] = useState<string | null>(null);

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
      const response = await fetch(buildApiUrl("/ingestion/sms/import?persist=true"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages }),
      });

      if (!response.ok) {
        throw new Error(await parseErrorResponse(response));
      }

      const data = (await response.json()) as UploadResponse;
      setSmsResult({ parsed_count: data.parsed_count, transactions: data.preview });
    } catch (err) {
      setError(toUserFacingError(err, "SMS parse failed"));
    } finally {
      setLoading(null);
    }
  };

  const uploadCsv = async () => {
    if (!csvFile) return;

    setLoading("csv");
    setError(null);
    setCsvError(null);
    setCsvResult(null);
    try {
      const formData = new FormData();
      formData.append("file", csvFile);
      const trimmedPassword = statementPassword.trim();
      if (trimmedPassword) {
        formData.append("password", trimmedPassword);
      }

      const response = await fetch(buildApiUrl("/ingestion/upload/csv?persist=true"), {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(await parseErrorResponse(response));
      }

      const data = (await response.json()) as UploadResponse;
      setCsvResult(data);
    } catch (err) {
      const message = toUserFacingError(err, "CSV upload failed");
      setCsvError(message);
      setError(message);
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
      const trimmedPassword = pdfPassword.trim();
      if (trimmedPassword) {
        formData.append("password", trimmedPassword);
      }

      const response = await fetch(buildApiUrl("/ingestion/upload/pdf?persist=false"), {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(await parseErrorResponse(response));
      }

      const data = (await response.json()) as UploadResponse;
      setPdfResult(data);
    } catch (err) {
      setError(toUserFacingError(err, "PDF upload failed"));
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
          <h3 className="text-base font-semibold text-foreground mb-2">Statement Upload (CSV/XLS/XLSX)</h3>
          <p className="text-xs text-muted-foreground mb-3">Upload a bank statement file and import rows. For password-protected Excel files, enter password below.</p>
          <input
            type="file"
            accept=".csv,.xls,.xlsx"
            onChange={(e) => setCsvFile(e.target.files?.[0] ?? null)}
            className="w-full text-sm text-muted-foreground"
          />
          <input
            type="password"
            value={statementPassword}
            onChange={(e) => setStatementPassword(e.target.value)}
            placeholder="Excel password (optional)"
            className="mt-3 w-full bg-surface-3 border border-gold-muted rounded-lg p-2.5 text-sm text-foreground placeholder:text-muted-foreground"
          />
          <button
            onClick={uploadCsv}
            disabled={loading === "csv" || !csvFile}
            className="mt-3 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm disabled:opacity-60"
          >
            {loading === "csv" ? "Uploading..." : "Upload Statement"}
          </button>

          {csvError && <p className="text-xs text-error mt-2">{csvError}</p>}

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
          <p className="text-xs text-muted-foreground mb-3">Upload PDF statements for extraction preview. If your statement is locked, enter the password below.</p>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setPdfFile(e.target.files?.[0] ?? null)}
            className="w-full text-sm text-muted-foreground"
          />
          <input
            type="password"
            value={pdfPassword}
            onChange={(e) => setPdfPassword(e.target.value)}
            placeholder="PDF password (optional)"
            className="mt-3 w-full bg-surface-3 border border-gold-muted rounded-lg p-2.5 text-sm text-foreground placeholder:text-muted-foreground"
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
