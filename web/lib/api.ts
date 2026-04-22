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
  SearchResponse,
  StudentProfileDetail,
  StudentProfilePayload,
  TpoCreateGroupRequest,
  TpoChangePasswordRequest,
  TpoOverviewResponse,
  TpoSettingsData,
  TpoSettingsResponse,
  TpoAuthTokenResponse,
  TpoGroup,
  TpoMailActionRequest,
  TpoMailActionResponse,
  TpoMailJobProgressResponse,
  TpoLoginRequestBody,
  TpoPlacementRequest,
} from "@/lib/types";
import { getStoredTpoToken } from "@/lib/auth-storage";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8082";

const TPO_API_KEY =
  process.env.NEXT_PUBLIC_TPO_API_KEY || "default-insecure-tpo-key";

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

export async function tpoLogin(body: TpoLoginRequestBody): Promise<TpoAuthTokenResponse> {
  const { data } = await api.post<TpoAuthTokenResponse>("/student/tpo/login", body);
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
  tpoToken?: string | null,
): Promise<JDMatchResponseBody> {
  const token = tpoToken ?? getStoredTpoToken();
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
  const { data } = await api.post<JDMatchResponseBody>("/student/match-jd", body, { headers });
  return data;
}

export async function matchCandidatesWithJdMultipart(
  formData: FormData,
  tpoToken?: string | null,
): Promise<JDMatchResponseBody> {
  const token = tpoToken ?? getStoredTpoToken();
  const { data } = await api.post<JDMatchResponseBody>("/student/match-jd", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  return data;
}

export async function searchCandidates(
  query: string,
  minScore: number = 0,
  minCgpa: number | null = null,
  branch: string | null = null,
  limit: number = 50,
  tpoToken?: string | null,
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    q: query,
    min_score: minScore.toString(),
    limit: limit.toString(),
  });

  if (minCgpa !== null) {
    params.append("min_cgpa", minCgpa.toString());
  }

  if (branch) {
    params.append("branch", branch);
  }

  const token = tpoToken ?? getStoredTpoToken();
  const headers = token
    ? { Authorization: `Bearer ${token}` }
    : { "x-tpo-api-key": TPO_API_KEY };
  const { data } = await api.get<SearchResponse>(`/search?${params.toString()}`, {
    headers,
  });
  return data;
}

export async function getSearchCandidateDetails(candidateId: number, tpoToken?: string | null): Promise<any> {
  const token = tpoToken ?? getStoredTpoToken();
  const headers = token
    ? { Authorization: `Bearer ${token}` }
    : { "x-tpo-api-key": TPO_API_KEY };
  const { data } = await api.get(`/search/${candidateId}/details`, {
    headers,
  });
  return data;
}

export async function createTpoGroup(body: TpoCreateGroupRequest, tpoToken?: string | null): Promise<TpoGroup> {
  const token = tpoToken ?? getStoredTpoToken();
  const { data } = await api.post<TpoGroup>("/student/tpo/groups", body, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return data;
}

export async function listTpoGroups(tpoToken?: string | null): Promise<TpoGroup[]> {
  const token = tpoToken ?? getStoredTpoToken();
  const { data } = await api.get<TpoGroup[]>("/student/tpo/groups", {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return data;
}

export async function getTpoOverview(tpoToken?: string | null): Promise<TpoOverviewResponse> {
  const token = tpoToken ?? getStoredTpoToken();
  const { data } = await api.get<TpoOverviewResponse>("/student/tpo/overview", {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return data;
}

export async function getTpoSettings(tpoToken?: string | null): Promise<TpoSettingsResponse> {
  const token = tpoToken ?? getStoredTpoToken();
  const { data } = await api.get<TpoSettingsResponse>("/student/tpo/settings", {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return data;
}

export async function updateTpoSettings(
  body: TpoSettingsData,
  tpoToken?: string | null,
): Promise<TpoSettingsResponse> {
  const token = tpoToken ?? getStoredTpoToken();
  const { data } = await api.put<TpoSettingsResponse>("/student/tpo/settings", body, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return data;
}

export async function changeTpoPassword(
  body: TpoChangePasswordRequest,
  tpoToken?: string | null,
): Promise<TpoMailActionResponse> {
  const token = tpoToken ?? getStoredTpoToken();
  const { data } = await api.post<TpoMailActionResponse>("/student/tpo/settings/change-password", body, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return data;
}

export async function deleteTpoGroup(groupId: number, tpoToken?: string | null): Promise<TpoMailActionResponse> {
  const token = tpoToken ?? getStoredTpoToken();
  const { data } = await api.delete<TpoMailActionResponse>(`/student/tpo/groups/${groupId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return data;
}

export async function markStudentPlacement(body: TpoPlacementRequest, tpoToken?: string | null): Promise<SaveProfileResponse> {
  const token = tpoToken ?? getStoredTpoToken();
  const { data } = await api.post<SaveProfileResponse>("/student/tpo/placement", body, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return data;
}

export async function triggerTpoMailAction(
  body: TpoMailActionRequest,
  tpoToken?: string | null,
): Promise<TpoMailActionResponse> {
  const token = tpoToken ?? getStoredTpoToken();
  const { data } = await api.post<TpoMailActionResponse>("/student/tpo/mail", body, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return data;
}

export async function getTpoMailJobProgress(
  jobId: number,
  tpoToken?: string | null,
): Promise<TpoMailJobProgressResponse> {
  const token = tpoToken ?? getStoredTpoToken();
  const { data } = await api.get<TpoMailJobProgressResponse>(`/student/tpo/mail/${jobId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return data;
}

export async function sendCandidateEmail(
  candidateId: number,
  subject?: string,
  body?: string
): Promise<{ success: boolean; message: string }> {
  const formData = new FormData();
  if (subject) formData.append("subject", subject);
  if (body) formData.append("body", body);

  const { data } = await api.post<{ success: boolean; message: string }>(
    `/student/${candidateId}/send-email`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}
