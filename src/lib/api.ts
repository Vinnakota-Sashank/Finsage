const envApiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").trim().replace(/\/+$/, "");
const devApiBaseUrl = import.meta.env.DEV ? "http://127.0.0.1:8000" : "";

const resolvedApiBaseUrl = (envApiBaseUrl || devApiBaseUrl).replace(/\/+$/, "");

export const apiTargetLabel = resolvedApiBaseUrl || "same-origin";

export const apiUrl = (path: string): string => {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return resolvedApiBaseUrl ? `${resolvedApiBaseUrl}${normalizedPath}` : normalizedPath;
};
