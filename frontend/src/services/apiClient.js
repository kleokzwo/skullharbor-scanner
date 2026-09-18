export const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function apiJson(path, options){
  const response = await fetch(`${API}${path}`, options);
  const data = await response.json();
  if(!response.ok){
    const detail = data?.detail;
    throw new Error(typeof detail === "string" ? detail : (detail?.message || "Request failed"));
  }
  return data;
}
