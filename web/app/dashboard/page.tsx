"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, UploadCloud } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

import {
  analyzeProfile,
  analyzeProfileIncremental,
  getApiErrorMessage,
  getMyProfile,
  saveProfile,
} from "@/lib/api";
import {
  clearDashboardDraft,
  getDashboardDraft,
  getStoredEmail,
  getStoredRollNo,
  getStoredStudentId,
  getStoredToken,
  setAuth,
  setDashboardDraft,
} from "@/lib/auth-storage";
import type {
  AnalyzeResponse,
  BranchOption,
  DashboardDraftData,
  FormDataState,
  StudentProfileDetail,
  StudentProfilePayload,
} from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const BRANCHES: BranchOption[] = [
  "CSE",
  "IT",
  "ECE",
  "EEE",
  "ME",
  "CE",
  "AIML",
  "DS",
  "Other",
];

const initialFormData: FormDataState = {
  resumeFile: null,
  marksheetFile: null,
  githubUsername: "",
  leetcodeUsername: "",
  codeforcesUsername: "",
  name: "",
  email: "",
  rollNo: "",
  phone: "",
  branch: "CSE",
  cgpa: "",
};

function isValidResume(file: File) {
  const name = file.name.toLowerCase();
  return name.endsWith(".pdf") || name.endsWith(".docx");
}

function isValidMarksheet(file: File) {
  return file.name.toLowerCase().endsWith(".pdf");
}

function parseGithubStats(github: Record<string, unknown>) {
  const repos = Number(github.repos ?? 0);
  const commits = Number(github.last_30_day_commits ?? github.commits_30d ?? 0);
  return { repos, commits };
}

function parseLeetcodeStats(leetcode: Record<string, unknown>) {
  return {
    totalSolved: Number(leetcode.total_solved ?? 0),
    easy: Number(leetcode.easy ?? 0),
    medium: Number(leetcode.medium ?? 0),
    hard: Number(leetcode.hard ?? 0),
  };
}

function extractUsername(value: unknown): string {
  if (typeof value === "string") return value.trim();
  if (value && typeof value === "object") {
    const candidate = value as Record<string, unknown>;
    const direct =
      candidate.username ??
      candidate.handle ??
      candidate.user ??
      candidate.profile ??
      candidate.id;
    if (typeof direct === "string") return direct.trim();
  }
  return "";
}

function extractFileName(value: unknown): string {
  if (!value || typeof value !== "object") return "";
  const fileName = (value as Record<string, unknown>).file_name;
  return typeof fileName === "string" ? fileName.trim() : "";
}

function getGithubUsername(profile: Awaited<ReturnType<typeof getMyProfile>>): string {
  const fromGithubData = extractUsername(profile.github_data);
  if (fromGithubData) return fromGithubData;
  const fromCodingGithub = extractUsername(profile.coding.github);
  if (fromCodingGithub) return fromCodingGithub;
  return "";
}

function getLeetcodeUsername(profile: Awaited<ReturnType<typeof getMyProfile>>): string {
  const fromLeetcodeData = extractUsername(profile.leetcode_data);
  if (fromLeetcodeData) return fromLeetcodeData;
  const fromCodingLeetcode = extractUsername(profile.coding.leetcode);
  if (fromCodingLeetcode) return fromCodingLeetcode;
  return "";
}

export default function DashboardPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<FormDataState>(initialFormData);
  const [analysisResult, setAnalysisResult] = useState<AnalyzeResponse | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [draftStudentId, setDraftStudentId] = useState<number | null>(null);
  const [draftHydrated, setDraftHydrated] = useState(false);
  const [isFileDialogOpen, setIsFileDialogOpen] = useState(false);
  const [existingResumeFileName, setExistingResumeFileName] = useState("");
  const [existingMarksheetFileName, setExistingMarksheetFileName] = useState("");
  const [pendingResumeFile, setPendingResumeFile] = useState<File | null>(null);
  const [pendingMarksheetFile, setPendingMarksheetFile] = useState<File | null>(null);
  const [profileSnapshot, setProfileSnapshot] = useState<StudentProfileDetail | null>(null);
  const [hasExistingProfile, setHasExistingProfile] = useState(false);
  const [baselineGithubUsername, setBaselineGithubUsername] = useState("");
  const [baselineLeetcodeUsername, setBaselineLeetcodeUsername] = useState("");

  useEffect(() => {
    const token = getStoredToken();
    const studentId = getStoredStudentId();
    if (!token || !studentId) {
      router.replace("/login");
      return;
    }
    setDraftStudentId(studentId);

    const rawDraft = getDashboardDraft(studentId);
    const hydrate = async () => {
      if (rawDraft) {
        try {
          const draft = JSON.parse(rawDraft) as DashboardDraftData;
          setFormData((prev) => ({ ...prev, ...draft }));
        } catch {
          // Ignore malformed drafts and continue with server/account prefill.
        }
      }

      try {
        const profile = await getMyProfile(token);
        setProfileSnapshot(profile);
        setHasExistingProfile(true);
        const branchValue = BRANCHES.includes(profile.student.branch as BranchOption)
          ? (profile.student.branch as BranchOption)
          : "Other";
        setExistingResumeFileName(extractFileName(profile.resume_data));
        setExistingMarksheetFileName(extractFileName(profile.academic_data));
        const githubBaseline = getGithubUsername(profile);
        const leetcodeBaseline = getLeetcodeUsername(profile);
        setBaselineGithubUsername(githubBaseline);
        setBaselineLeetcodeUsername(leetcodeBaseline);
        setFormData((prev) => ({
          ...prev,
          name: profile.student.name || prev.name,
          email: profile.student.email || prev.email,
          rollNo: profile.student.roll_no ?? prev.rollNo,
          phone: profile.student.phone || prev.phone,
          branch: prev.branch || branchValue,
          cgpa:
            profile.student.cgpa !== null && profile.student.cgpa !== undefined
              ? String(profile.student.cgpa)
              : prev.cgpa,
          githubUsername: prev.githubUsername || githubBaseline,
          leetcodeUsername: prev.leetcodeUsername || leetcodeBaseline,
        }));
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          setHasExistingProfile(false);
        }
        const storedRoll = getStoredRollNo();
        const storedEmail = getStoredEmail();
        setFormData((prev) => ({
          ...prev,
          email: prev.email || storedEmail || "",
          rollNo: prev.rollNo || storedRoll || "",
        }));
      }

      setDraftHydrated(true);
    };

    void hydrate();
  }, [router]);

  useEffect(() => {
    if (!draftHydrated || draftStudentId === null) return;
    const timer = window.setTimeout(() => {
      const draft: DashboardDraftData = {
        githubUsername: formData.githubUsername,
        leetcodeUsername: formData.leetcodeUsername,
        codeforcesUsername: formData.codeforcesUsername,
        name: formData.name,
        email: formData.email,
        rollNo: formData.rollNo,
        phone: formData.phone,
        branch: formData.branch,
        cgpa: formData.cgpa,
      };
      setDashboardDraft(draftStudentId, JSON.stringify(draft));
    }, 300);
    return () => window.clearTimeout(timer);
  }, [draftHydrated, draftStudentId, formData]);

  const githubStats = useMemo(
    () =>
      analysisResult
        ? parseGithubStats(analysisResult.coding.github)
        : { repos: 0, commits: 0 },
    [analysisResult],
  );

  const leetcodeStats = useMemo(
    () =>
      analysisResult
        ? parseLeetcodeStats(analysisResult.coding.leetcode)
        : { totalSolved: 0, easy: 0, medium: 0, hard: 0 },
    [analysisResult],
  );

  const currentResumeFileName = formData.resumeFile?.name || existingResumeFileName;
  const currentMarksheetFileName = formData.marksheetFile?.name || existingMarksheetFileName;

  const setField = <K extends keyof FormDataState>(
    key: K,
    value: FormDataState[K],
  ) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const openFileDialog = () => {
    setPendingResumeFile(formData.resumeFile);
    setPendingMarksheetFile(formData.marksheetFile);
    setIsFileDialogOpen(true);
  };

  const closeFileDialog = () => {
    setPendingResumeFile(null);
    setPendingMarksheetFile(null);
    setIsFileDialogOpen(false);
  };

  const saveFileDialogChanges = () => {
    setFormData((prev) => ({
      ...prev,
      resumeFile: pendingResumeFile ?? prev.resumeFile,
      marksheetFile: pendingMarksheetFile ?? prev.marksheetFile,
    }));
    if (pendingResumeFile) setExistingResumeFileName(pendingResumeFile.name);
    if (pendingMarksheetFile) setExistingMarksheetFileName(pendingMarksheetFile.name);
    closeFileDialog();
  };

  const codingDirty =
    formData.githubUsername.trim() !== baselineGithubUsername ||
    formData.leetcodeUsername.trim() !== baselineLeetcodeUsername;
  const hasPendingReanalysis =
    Boolean(formData.resumeFile) ||
    Boolean(formData.marksheetFile) ||
    codingDirty ||
    !analysisResult;

  const handleAnalyze = async () => {
    setErrorMessage(null);

    const token = getStoredToken();
    if (!token) {
      setErrorMessage("Please sign in again.");
      router.replace("/login");
      return;
    }

    const resumeDirty = Boolean(formData.resumeFile);
    const marksheetDirty = Boolean(formData.marksheetFile);
    const shouldRunIncremental = hasExistingProfile && (resumeDirty || marksheetDirty || codingDirty);

    if (formData.resumeFile && !isValidResume(formData.resumeFile)) {
      setErrorMessage("Resume must be PDF or DOCX.");
      return;
    }
    if (formData.marksheetFile && !isValidMarksheet(formData.marksheetFile)) {
      setErrorMessage("Marksheet must be a PDF file.");
      return;
    }
    if (!formData.githubUsername.trim() || !formData.leetcodeUsername.trim()) {
      setErrorMessage("GitHub and LeetCode usernames are required.");
      return;
    }

    if (!hasExistingProfile) {
      if (!formData.resumeFile || !formData.marksheetFile) {
        setErrorMessage("For first-time setup, upload both resume and marksheet before analyzing.");
        return;
      }
    } else if (!shouldRunIncremental) {
      setErrorMessage("No analysis inputs changed. Update a file or coding profile first.");
      return;
    }

    setAnalyzing(true);
    try {
      let data: AnalyzeResponse;
      if (!hasExistingProfile) {
        const payload = new FormData();
        payload.append("resume_file", formData.resumeFile as File);
        payload.append("marksheet_file", formData.marksheetFile as File);
        payload.append("branch", formData.branch);
        payload.append("github_username", formData.githubUsername.trim());
        payload.append("leetcode_username", formData.leetcodeUsername.trim());
        if (formData.codeforcesUsername.trim()) {
          payload.append("codeforces_username", formData.codeforcesUsername.trim());
        }
        data = await analyzeProfile(payload);
      } else {
        const payload = new FormData();
        payload.append("branch", formData.branch);
        payload.append("github_username", formData.githubUsername.trim());
        payload.append("leetcode_username", formData.leetcodeUsername.trim());
        payload.append("resume_changed", String(resumeDirty));
        payload.append("marksheet_changed", String(marksheetDirty));
        payload.append("coding_changed", String(codingDirty));
        if (formData.resumeFile) payload.append("resume_file", formData.resumeFile);
        if (formData.marksheetFile) payload.append("marksheet_file", formData.marksheetFile);
        data = await analyzeProfileIncremental(payload, token);
      }

      setAnalysisResult(data);
      setFormData((prev) => ({
        ...prev,
        name: data.student.name || prev.name,
        email: data.student.email || prev.email,
        rollNo: data.student.roll_no ?? prev.rollNo,
        phone: data.student.phone || prev.phone,
        branch: (data.student.branch || prev.branch) as BranchOption,
        cgpa: data.student.cgpa !== null ? String(data.student.cgpa) : prev.cgpa,
      }));
      toast.success("Analysis completed.");
    } catch (error) {
      const message = getApiErrorMessage(error);
      setErrorMessage(message);
      toast.error(message);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSave = async () => {
    const token = getStoredToken();
    if (!token) {
      setErrorMessage("Please sign in again.");
      router.replace("/login");
      return;
    }

    setSaving(true);
    setErrorMessage(null);
    try {
      const resumeDirty = Boolean(formData.resumeFile);
      const marksheetDirty = Boolean(formData.marksheetFile);
      const shouldRunIncremental = hasExistingProfile && (resumeDirty || marksheetDirty || codingDirty || !analysisResult);
      const shouldRunFullAnalyze = !hasExistingProfile && !analysisResult;

      let effectiveAnalysis = analysisResult;

      if (shouldRunFullAnalyze) {
        if (!formData.resumeFile || !formData.marksheetFile) {
          setErrorMessage("For first-time setup, upload both resume and marksheet before saving.");
          return;
        }
        if (!isValidResume(formData.resumeFile)) {
          setErrorMessage("Resume must be PDF or DOCX.");
          return;
        }
        if (!isValidMarksheet(formData.marksheetFile)) {
          setErrorMessage("Marksheet must be a PDF file.");
          return;
        }
        if (!formData.githubUsername.trim() || !formData.leetcodeUsername.trim()) {
          setErrorMessage("GitHub and LeetCode usernames are required.");
          return;
        }

        const payload = new FormData();
        payload.append("resume_file", formData.resumeFile);
        payload.append("marksheet_file", formData.marksheetFile);
        payload.append("branch", formData.branch);
        payload.append("github_username", formData.githubUsername.trim());
        payload.append("leetcode_username", formData.leetcodeUsername.trim());
        if (formData.codeforcesUsername.trim()) {
          payload.append("codeforces_username", formData.codeforcesUsername.trim());
        }

        const analyzed = await analyzeProfile(payload);
        effectiveAnalysis = analyzed;
        setAnalysisResult(analyzed);
      } else if (shouldRunIncremental) {
        const incrementalPayload = new FormData();
        incrementalPayload.append("branch", formData.branch);
        incrementalPayload.append("github_username", formData.githubUsername.trim());
        incrementalPayload.append("leetcode_username", formData.leetcodeUsername.trim());
        incrementalPayload.append("resume_changed", String(resumeDirty));
        incrementalPayload.append("marksheet_changed", String(marksheetDirty));
        incrementalPayload.append("coding_changed", String(codingDirty));
        if (formData.resumeFile) incrementalPayload.append("resume_file", formData.resumeFile);
        if (formData.marksheetFile) {
          incrementalPayload.append("marksheet_file", formData.marksheetFile);
        }

        const analyzed = await analyzeProfileIncremental(incrementalPayload, token);
        effectiveAnalysis = analyzed;
        setAnalysisResult(analyzed);
      }

      if (!effectiveAnalysis && profileSnapshot) {
        effectiveAnalysis = {
          student: profileSnapshot.student,
          skills: profileSnapshot.skills,
          coding: profileSnapshot.coding,
          academics: profileSnapshot.academics,
          overall_score: profileSnapshot.overall_score,
          resume_url: profileSnapshot.resume_url ?? null,
        };
      }

      if (!effectiveAnalysis) {
        throw new Error("No analysis available. Please upload files and analyze.");
      }

      const resolvedName = formData.name.trim() || effectiveAnalysis.student.name?.trim() || "";
      const resolvedEmail = formData.email.trim() || effectiveAnalysis.student.email?.trim() || "";
      const resolvedRollNo = formData.rollNo.trim() || effectiveAnalysis.student.roll_no?.trim() || "";
      const resolvedPhone = formData.phone.trim() || effectiveAnalysis.student.phone?.trim() || "";
      const resolvedBranch = formData.branch.trim() || effectiveAnalysis.student.branch?.trim() || "";

      if (!resolvedName || !resolvedEmail || !resolvedRollNo || !resolvedPhone || !resolvedBranch) {
        setErrorMessage("Name, email, AKTU roll no, phone, and branch are required.");
        return;
      }

      const cgpaValue =
        formData.cgpa.trim().length > 0 ? Number(formData.cgpa.trim()) : null;
      const payload: StudentProfilePayload = {
        student: {
          name: resolvedName,
          email: resolvedEmail,
          roll_no: resolvedRollNo.toUpperCase(),
          phone: resolvedPhone,
          branch: resolvedBranch,
          cgpa: Number.isNaN(cgpaValue) ? null : cgpaValue,
          cgpa_verified: effectiveAnalysis.academics.verified,
        },
        skills: effectiveAnalysis.skills,
        coding: effectiveAnalysis.coding,
        academics: {
          cgpa: Number.isNaN(cgpaValue) ? null : cgpaValue,
          verified: effectiveAnalysis.academics.verified,
          score: effectiveAnalysis.academics.score,
        },
        overall_score: effectiveAnalysis.overall_score,
        resume_url: effectiveAnalysis.resume_url,
        marksheet_url: null,
        resume_data: {
          file_name: currentResumeFileName || null,
        },
        academic_data: {
          file_name: currentMarksheetFileName || null,
        },
        github_data: effectiveAnalysis.coding.github,
        leetcode_data: effectiveAnalysis.coding.leetcode,
      };

      const response = await saveProfile(payload, token);
      if (draftStudentId !== null) {
        clearDashboardDraft(draftStudentId);
        setAuth(token, draftStudentId, payload.student.email, payload.student.roll_no);
      }
      setHasExistingProfile(true);
      setBaselineGithubUsername(formData.githubUsername.trim());
      setBaselineLeetcodeUsername(formData.leetcodeUsername.trim());
      setFormData((prev) => ({
        ...prev,
        name: payload.student.name,
        email: payload.student.email,
        rollNo: payload.student.roll_no || prev.rollNo,
        phone: payload.student.phone,
        branch: (payload.student.branch as BranchOption) || prev.branch,
        resumeFile: null,
        marksheetFile: null,
      }));
      toast.success(response.message);
    } catch (error) {
      const message = getApiErrorMessage(error);
      setErrorMessage(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="min-h-screen px-4 py-10 md:px-6">
      <div className="mx-auto w-full max-w-4xl space-y-6">
        <header className="space-y-1">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h1 className="text-3xl font-semibold tracking-tight">VerifAI Dashboard</h1>
            <Link
              href="/profile"
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
            >
              View profile
            </Link>
          </div>
          <p className="text-sm text-muted-foreground">
            Analyze your profile, review details, and save your student profile.
          </p>
        </header>

        {errorMessage ? (
          <Card className="border-destructive/40 bg-destructive/5">
            <CardContent className="pt-6 text-sm text-destructive">
              {errorMessage}
            </CardContent>
          </Card>
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle>File Upload</CardTitle>
            <CardDescription>
              Review current files and update them from the popup.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-md border p-3">
                <p className="text-sm font-medium">Resume (PDF/DOCX)</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {currentResumeFileName || "No file uploaded"}
                </p>
              </div>
              <div className="rounded-md border p-3">
                <p className="text-sm font-medium">Marksheet (PDF)</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {currentMarksheetFileName || "No file uploaded"}
                </p>
              </div>
            </div>
            <Button type="button" variant="outline" onClick={openFileDialog}>
              Update Files
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Coding Profiles</CardTitle>
            <CardDescription>
              Provide coding profile usernames for analysis.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            <Input
              placeholder="GitHub username"
              value={formData.githubUsername}
              onChange={(e) => setField("githubUsername", e.target.value)}
            />
            <Input
              placeholder="LeetCode username"
              value={formData.leetcodeUsername}
              onChange={(e) => setField("leetcodeUsername", e.target.value)}
            />
            <Input
              placeholder="Codeforces username (optional)"
              value={formData.codeforcesUsername}
              onChange={(e) => setField("codeforcesUsername", e.target.value)}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>
              Auto-filled after analysis and editable before saving.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <Input
              placeholder="Name"
              value={formData.name}
              onChange={(e) => setField("name", e.target.value)}
            />
            <Input
              placeholder="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setField("email", e.target.value)}
            />
            <Input
              placeholder="AKTU roll no"
              value={formData.rollNo}
              onChange={(e) => setField("rollNo", e.target.value)}
            />
            <Input
              placeholder="Phone"
              value={formData.phone}
              onChange={(e) => setField("phone", e.target.value)}
            />
            <Select
              value={formData.branch}
              onValueChange={(value) => setField("branch", value as BranchOption)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select branch" />
              </SelectTrigger>
              <SelectContent>
                {BRANCHES.map((branch) => (
                  <SelectItem key={branch} value={branch}>
                    {branch}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              placeholder="CGPA"
              value={formData.cgpa}
              onChange={(e) => setField("cgpa", e.target.value)}
            />
          </CardContent>
        </Card>

        <div className="space-y-2">
          <div className="flex flex-wrap gap-3">
            <Button onClick={handleAnalyze} disabled={analyzing || saving}>
              {analyzing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <UploadCloud className="mr-2 h-4 w-4" />
                  Analyze Profile
                </>
              )}
            </Button>
            <Button
              variant="secondary"
              onClick={handleSave}
              disabled={saving || analyzing}
            >
              {saving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Profile"
              )}
            </Button>
          </div>
          {hasPendingReanalysis ? (
            <p className="text-sm text-muted-foreground">
              Save will run analysis for changed inputs before storing your profile.
            </p>
          ) : (
            <p className="text-sm text-muted-foreground">
              No analysis changes pending. Save will store profile details directly.
            </p>
          )}
        </div>

        {analysisResult ? (
          <section className="space-y-4">
            <h2 className="text-xl font-semibold tracking-tight">Analysis Result</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Skills</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-2">
                  {analysisResult.skills.length > 0 ? (
                    analysisResult.skills.map((skill) => (
                      <Badge key={skill} variant="secondary">
                        {skill}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No skills extracted.</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Coding</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">Persona</span>
                    <Badge>{analysisResult.coding.persona || "N/A"}</Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>GitHub Repos: {githubStats.repos}</div>
                    <div>Commits (30d): {githubStats.commits}</div>
                    <div>Solved: {leetcodeStats.totalSolved}</div>
                    <div>
                      E/M/H: {leetcodeStats.easy}/{leetcodeStats.medium}/
                      {leetcodeStats.hard}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Academics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div>CGPA: {analysisResult.academics.cgpa ?? "N/A"}</div>
                  <div className="flex items-center gap-2">
                    Status:
                    {analysisResult.academics.verified ? (
                      <Badge>Verified</Badge>
                    ) : (
                      <Badge variant="secondary">Unverified</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Overall Score</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="text-2xl font-semibold">
                    {analysisResult.overall_score.toFixed(1)} / 100
                  </div>
                  <Progress value={analysisResult.overall_score} />
                </CardContent>
              </Card>
            </div>
          </section>
        ) : null}
      </div>

      {isFileDialogOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-lg rounded-lg border bg-background p-6 shadow-lg">
            <h2 className="text-lg font-semibold">Update files</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Replace resume or marksheet. You can update one or both.
            </p>

            <div className="mt-5 space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Resume (PDF/DOCX)</label>
                <Input
                  type="file"
                  accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={(e) => setPendingResumeFile(e.target.files?.[0] ?? null)}
                />
                <p className="text-xs text-muted-foreground">
                  Current: {pendingResumeFile?.name || currentResumeFileName || "No file uploaded"}
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Marksheet (PDF)</label>
                <Input
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={(e) => setPendingMarksheetFile(e.target.files?.[0] ?? null)}
                />
                <p className="text-xs text-muted-foreground">
                  Current: {pendingMarksheetFile?.name || currentMarksheetFileName || "No file uploaded"}
                </p>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" onClick={closeFileDialog}>
                Cancel
              </Button>
              <Button onClick={saveFileDialogChanges}>Save file changes</Button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}
