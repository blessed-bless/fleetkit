import { ApiError } from "../api";

export function humanApiError(err: unknown, fallback = "Что-то пошло не так"): string {
  if (err instanceof ApiError) {
    if (err.status === 401) return "Сессия истекла — войди снова";
    if (err.status === 403) return "Недостаточно прав";
    if (err.status === 404) return "Не найдено";
    if (err.status === 409) return "Конфликт данных — проверь уникальные поля";
    if (err.status === 429) return "Слишком много запросов, подожди чуть-чуть";
    return err.message || fallback;
  }
  if (err instanceof Error) return err.message || fallback;
  return fallback;
}

export function isAuthError(err: unknown): boolean {
  return err instanceof ApiError && err.status === 401;
}
