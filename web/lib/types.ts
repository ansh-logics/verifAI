export type BranchOption =
  | "CSE"
  | "IT"
  | "ECE"
  | "EEE"
  | "ME"
  | "CE"
  | "AIML"
  | "DS"
  | "Other";

export interface AnalyzeResponse {
  student: {
    name: string;
    email: string;
    roll_no?: string | null;
    phone: string;
    branch: string;
    cgpa: number | null;
    gender: "women" | "men" | "other";
    cgpa_verified: boolean;
  };
  skills: string[];
  coding: {
    persona: string;
    score: number;
    github: Record<string, unknown>;
    leetcode: Record<string, unknown>;
  };
  academics: {
    cgpa: number | null;
    verified: boolean;
    score: number;
  };
  overall_score: number;
  resume_url: string | null;
}

export interface StudentProfilePayload {
  student: {
    name: string;
    email: string;
    roll_no?: string | null;
    phone: string;
    branch: string;
    cgpa: number | null;
    gender: "women" | "men" | "other";
    cgpa_verified: boolean;
  };
  skills: string[];
  coding: {
    persona: string;
    score: number;
    github: Record<string, unknown>;
    leetcode: Record<string, unknown>;
  };
  academics: {
    cgpa: number | null;
    verified: boolean;
    score: number;
  };
  overall_score: number;
  resume_url: string | null;
  marksheet_url: string | null;
  resume_data: Record<string, unknown>;
  academic_data: Record<string, unknown>;
  github_data: Record<string, unknown>;
  leetcode_data: Record<string, unknown>;
}

export interface SaveProfileResponse {
  success: boolean;
  student_id: number;
  profile_id: number;
  message: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  student_id: number;
  email: string;
  roll_no: string | null;
}

export interface TpoLoginRequestBody {
  username: string;
  password: string;
}

export interface TpoAuthTokenResponse {
  access_token: string;
  token_type: string;
  username: string;
}

export interface RegisterRequestBody {
  name: string;
  email: string;
  password: string;
  phone: string;
}

export interface RegisterResponseBody {
  success: boolean;
  student_id: number;
  message: string;
}

export interface LoginRequestBody {
  identifier: string;
  password: string;
}

export interface StudentProfileDetail {
  id: number;
  student_id: number;
  student: {
    name: string;
    email: string;
    roll_no: string | null;
    phone: string;
    branch: string;
    cgpa: number | null;
    gender: "women" | "men" | "other";
    cgpa_verified: boolean;
  };
  skills: string[];
  coding: {
    persona: string;
    score: number;
    github: Record<string, unknown>;
    leetcode: Record<string, unknown>;
  };
  academics: {
    cgpa: number | null;
    verified: boolean;
    score: number;
  };
  overall_score: number;
  resume_url?: string | null;
  resume_data: Record<string, unknown>;
  academic_data: Record<string, unknown>;
  github_data: Record<string, unknown>;
  leetcode_data: Record<string, unknown>;
  last_analyzed_at: string;
  created_at: string;
  placement?: {
    company_name: string;
    offer_type: "internship" | "job";
    pay_amount: number | null;
    notes: string | null;
    is_active: boolean;
    created_at: string;
    updated_at: string;
  } | null;
}

export interface TpoGroupMember {
  student_id: number;
  name: string;
  email: string;
  roll_no: string | null;
  branch: string;
  placement?: StudentProfileDetail["placement"];
}

export interface TpoGroup {
  id: number;
  title: string;
  jd_summary: string | null;
  created_by: string;
  created_at: string;
  company_name: string | null;
  role_type: "internship" | "job" | null;
  pay_or_stipend: string | null;
  duration: string | null;
  bond_details: string | null;
  interview_timezone: string | null;
  members: TpoGroupMember[];
}

export interface TpoCreateGroupRequest {
  title: string;
  jd_summary?: string | null;
  student_ids: number[];
  company_name?: string | null;
  role_type?: "internship" | "job" | null;
  pay_or_stipend?: string | null;
  duration?: string | null;
  bond_details?: string | null;
  interview_timezone?: string | null;
}

export interface TpoPlacementRequest {
  student_id: number;
  group_id?: number;
  company_name?: string | null;
  offer_type?: "internship" | "job" | null;
  pay_amount?: number | null;
  notes?: string | null;
}

export type TpoMailType =
  | "shortlist_notice"
  | "prep_topics"
  | "interview_schedule"
  | "process_custom";

export interface TpoMailActionRequest {
  group_id: number;
  mode: "bulk" | "individual";
  mail_type: TpoMailType;
  subject?: string;
  body?: string;
  student_id?: number;
  prep_topics?: string[];
  interview_date?: string;
  interview_time_start?: string;
  interview_time_end?: string;
  additional_note?: string;
}

export interface TpoMailActionResponse {
  success: boolean;
  message: string;
}

export interface FormDataState {
  resumeFile: File | null;
  marksheetFile: File | null;
  githubUsername: string;
  leetcodeUsername: string;
  codeforcesUsername: string;
  name: string;
  email: string;
  rollNo: string;
  phone: string;
  branch: BranchOption;
  cgpa: string;
}

export interface DashboardDraftData {
  githubUsername: string;
  leetcodeUsername: string;
  codeforcesUsername: string;
  name: string;
  email: string;
  rollNo: string;
  phone: string;
  branch: BranchOption;
  cgpa: string;
}

export type PlacementFilter = "unplaced_only" | "placed_or_unplaced";
export type GenderFilter = "women_only" | "men_only" | "all_genders" | "custom_text";

export interface JDMatchRequestBody {
  jd_text: string;
  student_ids?: number[];
  top_k?: number;
}

export interface JDMatchSubmitInput {
  jdText?: string;
  jdFile?: File | null;
  studentIds?: number[];
  topK?: number;
}

export interface JDMatchScoreBreakdown {
  resume: number;
  github: number;
  leetcode: number;
  academics: number;
  total: number;
}

export interface JDMatchCandidate {
  student_id: number;
  email: string;
  name: string;
  roll_no: string | null;
  gender: "women" | "men" | "other";
  branch: string;
  cgpa: number | null;
  skills: string[];
  resume_url: string | null;
  coding_persona: string | null;
  is_placed: boolean;
  has_active_backlog: boolean;
  score_breakdown: JDMatchScoreBreakdown;
}

export interface JDMatchFilters {
  total_considered: number;
  passed_filters: number;
  rejected_min_cgpa: number;
  rejected_branch: number;
  rejected_gender: number;
  rejected_backlog: number;
  rejected_placement: number;
}

export interface JDParsedConstraints {
  company_name?: string | null;
  pay_or_stipend?: string | null;
  bond_details?: string | null;
  jd_summary?: string | null;
  job_title: string | null;
  role_type: "full_time" | "internship" | "contract" | "part_time" | "unknown";
  required_skills: string[];
  preferred_skills: string[];
  tools_and_technologies: string[];
  responsibilities: string[];
  min_experience_years: number | null;
  accepts_freshers: boolean;
  key_traits: string[];
  education_requirements: string[];
  location: string | null;
  domain: string | null;
  duration: string | null;
  work_type: string | null;
  target_student_count: number | null;
  exclude_active_backlogs: boolean;
  placement_filter: PlacementFilter;
  placement_exception_roll_nos: string[];
  min_cgpa: number | null;
  allowed_branches: string[];
  gender_filter: GenderFilter;
  gender_filter_raw: string | null;
  branch_constraint_raw: string | null;
  branch_inference_reason: string | null;
}

export interface JDMatchResponseBody {
  jd: JDParsedConstraints;
  filters: JDMatchFilters;
  candidates: JDMatchCandidate[];
}

// Search API Types
export interface SearchResultCandidate {
  candidate_id: number;
  name: string;
  email: string;
  branch: string;
  cgpa: number | null;
  match_score: number;
  overall_score: number;
  matched_terms: string[];
  match_quality: "exact" | "fuzzy" | "mixed";
}

export interface SearchResponse {
  query: string;
  total_results: number;
  results: SearchResultCandidate[];
}
