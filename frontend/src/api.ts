let csrf = "";
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
export function setCsrf(token: string) {
  csrf = token;
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api/v1/${path}`, {
    ...options,
    credentials: "same-origin",
    headers: {
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      "X-CSRFToken": csrf,
      ...options.headers,
    },
  });
  if (!response.ok) {
    const data = await response
      .json()
      .catch(() => ({ detail: `Request failed (${response.status})` }));
    throw new ApiError(
      data.detail ||
        Object.entries(data)
          .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
          .join(" · "),
      response.status,
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export function mutation<T>(path: string, data: unknown, method = "POST") {
  return api<T>(path, { method, body: JSON.stringify(data) });
}
