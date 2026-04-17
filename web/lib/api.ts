import axios from "axios";
import type {
  AnalyzeResponse,
  AuthTokenResponse,
  JDMatchRequestBody,
  JDMatchResponseBody,
  LoginRequestBody,
  RegisterRequestBody,
  RegisterResponseBody,
  SaveProfileResponse,
  StudentProfileDetail,
  StudentProfilePayload,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000,
});

function detailToMessage(detail: unknown): string | null {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (
    detail &&
    typeof detail === "object" &&
    "message" in detail &&
    typeof (detail as { message: unknown }).message === "string"
  ) {
    return String((detail as { message: string }).message);
  }
  return null;
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const fromDetail = detailToMessage(error.response?.data?.detail);
    if (fromDetail) return fromDetail;
    if (typeof error.message === "string" && error.message.trim()) {
      return error.message;
    }
  }
  return "Something went wrong. Please try again.";
}

export async function analyzeProfile(formData: FormData): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>("/student/analyze", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function saveProfile(
  payload: StudentProfilePayload,
  accessToken: string | null,
): Promise<SaveProfileResponse> {
  const headers =
    accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined;
  const { data } = await api.post<SaveProfileResponse>(
    "/student/profile",
    payload,
    { headers },
  );
  return data;
}

export async function login(body: LoginRequestBody): Promise<AuthTokenResponse> {
  const { data } = await api.post<AuthTokenResponse>("/student/login", body);
  return data;
}

export async function registerAccount(
  body: RegisterRequestBody,
): Promise<RegisterResponseBody> {
  const { data } = await api.post<RegisterResponseBody>("/student/register", body);
  return data;
}

export async function getMyProfile(
  accessToken: string,
): Promise<StudentProfileDetail> {
  const { data } = await api.get<StudentProfileDetail>("/student/profile/me", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return data;
}

export async function analyzeProfileIncremental(
  formData: FormData,
  accessToken: string,
): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>(
    "/student/analyze-incremental",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );
  return data;
}

export async function matchCandidatesWithJd(
  body: JDMatchRequestBody,
): Promise<JDMatchResponseBody> {
  const { data } = await api.post<JDMatchResponseBody>("/student/match-jd", body);
  return data;
}

export async function matchCandidatesWithJdMultipart(
  formData: FormData,
): Promise<JDMatchResponseBody> {
  const { data } = await api.post<JDMatchResponseBody>("/student/match-jd", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
