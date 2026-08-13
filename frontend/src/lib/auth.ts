const TOKEN_KEY = "deepcite_access_token";

export function saveToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}