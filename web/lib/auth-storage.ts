const TOKEN_KEY = "verifai_access_token";
const STUDENT_ID_KEY = "verifai_student_id";
const ROLL_KEY = "verifai_roll_no";
const EMAIL_KEY = "verifai_email";
const DASHBOARD_DRAFT_PREFIX = "verifai_dashboard_draft_";
const TPO_TOKEN_KEY = "verifai_tpo_access_token";
const TPO_USERNAME_KEY = "verifai_tpo_username";
const TPO_COOKIE = "verifai_tpo_session";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getStoredStudentId(): number | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(STUDENT_ID_KEY);
  if (!raw) return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

export function getStoredRollNo(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ROLL_KEY);
}

export function getStoredEmail(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(EMAIL_KEY);
}

function getDraftKey(studentId: number): string {
  return `${DASHBOARD_DRAFT_PREFIX}${studentId}`;
}

export function getDashboardDraft(studentId: number): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(getDraftKey(studentId));
}

export function setDashboardDraft(studentId: number, draft: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(getDraftKey(studentId), draft);
}

export function clearDashboardDraft(studentId: number): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(getDraftKey(studentId));
}

export function setAuth(
  token: string,
  studentId: number,
  email?: string | null,
  rollNo?: string | null,
): void {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(STUDENT_ID_KEY, String(studentId));
  if (email) {
    window.localStorage.setItem(EMAIL_KEY, email);
  }
  if (rollNo) {
    window.localStorage.setItem(ROLL_KEY, rollNo);
  }
}

export function clearAuth(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(STUDENT_ID_KEY);
  window.localStorage.removeItem(ROLL_KEY);
  window.localStorage.removeItem(EMAIL_KEY);
}

function setTpoCookie(value: string): void {
  if (typeof document === "undefined") return;
  document.cookie = `${TPO_COOKIE}=${encodeURIComponent(value)}; Path=/; Max-Age=86400; SameSite=Lax`;
}

function clearTpoCookie(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${TPO_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export function getStoredTpoToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TPO_TOKEN_KEY);
}

export function getStoredTpoUsername(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TPO_USERNAME_KEY);
}

export function setTpoAuth(token: string, username: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TPO_TOKEN_KEY, token);
  window.localStorage.setItem(TPO_USERNAME_KEY, username);
  setTpoCookie(token);
}

export function clearTpoAuth(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TPO_TOKEN_KEY);
  window.localStorage.removeItem(TPO_USERNAME_KEY);
  clearTpoCookie();
}
