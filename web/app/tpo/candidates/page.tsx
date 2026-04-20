"use client";

import * as React from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "sonner";
import { CheckCircle2, FileText, Loader2, Target, Trophy, UploadCloud, Users, X, Download } from "lucide-react";

import { matchCandidatesWithJd, matchCandidatesWithJdMultipart, getSearchCandidateDetails } from "@/lib/api";
import type { JDMatchCandidate, JDMatchFilters, JDParsedConstraints } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

const BRANCHES = ["CSE", "IT", "ECE", "EEE", "ME", "CE", "AIML", "DS", "Other"] as const;
type BranchFilter = string;
type GenderFilter = "women" | "men" | "other" | "All";

type UICandidate = {
  key: string;
  id: number;
  name: string;
  email: string;
  rollNo: string;
  branch: string;
  gender: "women" | "men" | "other";
  cgpa: number;
  matchScore: number;
  skills: string[];
  codingPersona: string;
  resumeUrl: string | null;
  isPlaced: boolean;
  hasBacklog: boolean;
  score: {
    resume: number;
    github: number;
    leetcode: number;
    academics: number;
    total: number;
  };
};

function scoreTone(score: number) {
  if (score >= 80) return { pill: "border-emerald-500/30 bg-emerald-500/10 text-emerald-700", dot: "bg-emerald-500" };
  if (score >= 60) return { pill: "border-amber-500/30 bg-amber-500/10 text-amber-700", dot: "bg-amber-500" };
  return { pill: "border-rose-500/30 bg-rose-500/10 text-rose-700", dot: "bg-rose-500" };
}

function clamp01(v: number) {
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

function normalizeText(value: string | null | undefined): string {
  return (value ?? "").trim().toLowerCase().replace(/\s+/g, " ");
}

function normalizeBranch(value: string | null | undefined): string {
  const normalized = normalizeText(value);
  if (!normalized) return normalized;
  const compact = normalized.replace(/[^a-z0-9]/g, "");
  if (compact === "computerscienceengineering" || compact === "cse") return "cse";
  if (compact === "informationtechnology" || compact === "it") return "it";
  if (compact === "electronicscommunicationengineering" || compact === "ece") return "ece";
  if (compact === "electricalelectronicsengineering" || compact === "eee") return "eee";
  if (compact === "mechanicalengineering" || compact === "me") return "me";
  if (compact === "civilengineering" || compact === "ce") return "ce";
  if (compact === "aiml" || compact === "artificialintelligencemachinelearning") return "aiml";
  if (compact === "datascience" || compact === "ds") return "ds";
  return compact;
}

function toCandidate(raw: JDMatchCandidate): UICandidate {
  return {
    key: String(raw.student_id),
    id: raw.student_id,
    name: raw.name,
    email: raw.email,
    rollNo: raw.roll_no ?? "-",
    branch: raw.branch,
    gender: raw.gender,
    cgpa: raw.cgpa ?? 0,
    matchScore: raw.score_breakdown.total,
    skills: raw.skills ?? [],
    codingPersona: raw.coding_persona ?? "-",
    resumeUrl: raw.resume_url,
    isPlaced: raw.is_placed,
    hasBacklog: raw.has_active_backlog,
    score: {
      resume: raw.score_breakdown.resume,
      github: raw.score_breakdown.github,
      leetcode: raw.score_breakdown.leetcode,
      academics: raw.score_breakdown.academics,
      total: raw.score_breakdown.total,
    },
  };
}

function CandidateFullDetails({ candidateId }: { candidateId: number }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    getSearchCandidateDetails(candidateId)
      .then((res) => {
        if (mounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error(err);
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [candidateId]);

  if (loading) return <div className="text-sm text-slate-500 animate-pulse">Loading detailed profile...</div>;
  if (!data) return <div className="text-sm text-slate-500">Failed to load detailed profile.</div>;

  const hasGithub = data.github_data && Object.keys(data.github_data).length > 0;
  const hasLeetcode = data.leetcode_data && Object.keys(data.leetcode_data).length > 0;

  return (
    <div className="col-span-3 pt-4 mt-4 border-t border-slate-200 grid grid-cols-2 gap-8">
      {hasGithub && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-900">GitHub Stats</h4>
          <div className="text-sm text-slate-700">Followers: {data.github_data.followers || 0}</div>
          <div className="text-sm text-slate-700">Public Repos: {data.github_data.repos || 0}</div>
          {data.github_data.languages?.length > 0 && (
            <div className="text-sm text-slate-700">Top Languages: {data.github_data.languages.slice(0, 3).join(", ")}</div>
          )}
        </div>
      )}
      {hasLeetcode && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-900">LeetCode Stats</h4>
          <div className="text-sm text-slate-700">Solved: {data.leetcode_data.total_solved || 0}</div>
          <div className="text-sm text-slate-700">Easy: {data.leetcode_data.easy || 0}, Medium: {data.leetcode_data.medium || 0}, Hard: {data.leetcode_data.hard || 0}</div>
          <div className="text-sm text-slate-700">Rating: {Math.round(data.leetcode_data.contest_rating || data.leetcode_data.ranking || 0)}</div>
        </div>
      )}
      {!hasGithub && !hasLeetcode && (
        <div className="text-sm text-slate-500 col-span-2">No connected platforms (GitHub/LeetCode) found for this candidate.</div>
      )}
    </div>
  );
}

export default function TpoDashboardPage() {
  const composerRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const jdTextareaRef = useRef<HTMLTextAreaElement | null>(null);
  const [jdInput, setJdInput] = useState("");
  const [fileUpload, setFileUpload] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [candidates, setCandidates] = useState<UICandidate[]>([]);
  const [parsedJD, setParsedJD] = useState<JDParsedConstraints | null>(null);
  const [filters, setFilters] = useState<JDMatchFilters | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [minCgpa, setMinCgpa] = useState("");
  const [branch, setBranch] = useState<BranchFilter>("All");
  const [gender, setGender] = useState<GenderFilter>("All");
  const [skills, setSkills] = useState<string[]>([]);
  const [sortKey, setSortKey] = useState<"matchScore" | "cgpa" | "name" | "branch" | "gender">("matchScore");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const [isInputExpanded, setIsInputExpanded] = useState(false);
  const [composerInputHeight, setComposerInputHeight] = useState(48);

  const COMPACT_HEIGHT = 48;
  const EXPANDED_MIN_HEIGHT = 200;
  const EXPANDED_MAX_HEIGHT = 360;

  function resizeTextarea(expanded: boolean) {
    const textarea = jdTextareaRef.current;
    if (!expanded) {
      setComposerInputHeight(COMPACT_HEIGHT);
      if (textarea) {
        textarea.style.height = `${COMPACT_HEIGHT}px`;
        textarea.style.overflowY = "hidden";
      }
      return;
    }
    if (!textarea) {
      setComposerInputHeight(EXPANDED_MIN_HEIGHT);
      return;
    }
    textarea.style.height = "auto";
    const minHeight = EXPANDED_MIN_HEIGHT;
    const maxHeight = EXPANDED_MAX_HEIGHT;
    const nextHeight = Math.max(minHeight, Math.min(textarea.scrollHeight, maxHeight));
    setComposerInputHeight(nextHeight);
    textarea.style.height = `${nextHeight}px`;
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
  }

  function handleExpandInput() {
    setIsInputExpanded(true);
  }

  function resetFiltersAndSort() {
    setSkills([]);
    setBranch("All");
    setGender("All");
    setMinCgpa("");
    setExpandedKey(null);
    setSortKey("matchScore");
    setSortDir("desc");
  }

  function exportToCsv() {
    if (filtered.length === 0) {
      toast.error("No candidates to export");
      return;
    }
    
    const headers = ["Name", "Email", "Roll No", "Branch", "Gender", "CGPA", "Match Score", "Skills", "Placed", "Backlog", "Resume URL"];
    const rows = filtered.map(c => [
      c.name,
      c.email,
      c.rollNo,
      c.branch,
      c.gender,
      c.cgpa.toFixed(2),
      c.matchScore.toFixed(2) + "%",
      c.skills.join("; "),
      c.isPlaced ? "Yes" : "No",
      c.hasBacklog ? "Yes" : "No",
      c.resumeUrl || "N/A"
    ]);
    
    const csvContent = [
      headers.join(","),
      ...rows.map(e => e.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    ].join("\n");
    
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `shortlist_${new Date().toISOString().split("T")[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success("Exported CSV successfully");
  }

  async function runMatch() {
    const typedJd = jdInput.trim();
    const hasJdFile = Boolean(fileUpload);
    const hasValidText = typedJd.length >= 20;

    if (!hasJdFile && !hasValidText) {
      toast.error("Provide JD text (min 20 chars) or upload a JD PDF/DOCX file.");
      return;
    }
    setIsInputExpanded(false);
    setLoading(true);
    setErrorMessage(null);
    try {
      const response = hasJdFile
        ? await (async () => {
            const formData = new FormData();
            formData.append("jd_file", fileUpload as File);
            if (typedJd) {
              formData.append("jd_text", typedJd);
            }
            return matchCandidatesWithJdMultipart(formData);
          })()
        : await matchCandidatesWithJd({ jd_text: typedJd });
      setCandidates(response.candidates.map(toCandidate));
      setParsedJD(response.jd);
      setFilters(response.filters);
      const initialSkills = Array.from(
        new Set([
          ...(response.jd.required_skills ?? []),
          ...(response.jd.preferred_skills ?? []),
          ...(response.jd.tools_and_technologies ?? []),
        ].map((s) => s.trim()).filter(Boolean)),
      );
      setSkills(initialSkills);
      setExpandedKey(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to fetch candidates.";
      setErrorMessage(message);
      setCandidates([]);
      setFilters(null);
      setParsedJD(null);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  const filtered = useMemo(() => {
    const min = minCgpa.trim() ? Number(minCgpa.trim()) : NaN;
    const targetBranch = normalizeBranch(branch === "All" ? "" : branch);
    const targetGender = normalizeText(gender === "All" ? "" : gender);
    const out = candidates.filter((c) => {
      if (!Number.isNaN(min) && Number(c.cgpa) < min) return false;
      if (targetBranch && normalizeBranch(c.branch) !== targetBranch) return false;
      if (targetGender && normalizeText(c.gender) !== targetGender) return false;
      if (skills.length > 0) {
        const lower = c.skills.map((s) => normalizeText(s));
        if (!skills.every((s) => lower.includes(normalizeText(s)))) return false;
      }
      return true;
    });
    const dir = sortDir === "asc" ? 1 : -1;
    out.sort((a, b) => {
      if (sortKey === "matchScore") return (a.matchScore - b.matchScore) * dir;
      if (sortKey === "cgpa") return (a.cgpa - b.cgpa) * dir;
      if (sortKey === "branch") return a.branch.localeCompare(b.branch) * dir;
      if (sortKey === "gender") return a.gender.localeCompare(b.gender) * dir;
      return a.name.localeCompare(b.name) * dir;
    });
    return out;
  }, [candidates, minCgpa, branch, gender, skills, sortKey, sortDir]);

  const summary = useMemo(() => {
    const total = filtered.length;
    const qualified = filtered.filter((c) => !c.isPlaced && !c.hasBacklog).length;
    const avg = total ? filtered.reduce((acc, c) => acc + c.matchScore, 0) / total : 0;
    return { total, qualified, avg };
  }, [filtered]);

  const topKeys = useMemo(() => new Set([...filtered].sort((a, b) => b.matchScore - a.matchScore).slice(0, 3).map((c) => c.key)), [filtered]);
  const collapsedPreview = useMemo(() => jdInput.split(/\r?\n/)[0] ?? "", [jdInput]);
  const branchOptions = useMemo(() => {
    const fromCandidates = Array.from(new Set(candidates.map((c) => c.branch).filter(Boolean)));
    const merged = Array.from(new Set([...BRANCHES, ...fromCandidates]));
    return merged.sort((a, b) => a.localeCompare(b));
  }, [candidates]);

  useEffect(() => {
    resizeTextarea(isInputExpanded);
  }, [isInputExpanded, jdInput, loading]);

  useEffect(() => {
    if (isInputExpanded) jdTextareaRef.current?.focus();
  }, [isInputExpanded]);

  useEffect(() => {
    function handlePointerDown(event: MouseEvent | TouchEvent) {
      if (!isInputExpanded) return;
      const target = event.target as Node | null;
      if (!target) return;
      if (composerRef.current?.contains(target)) return;
      setIsInputExpanded(false);
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("touchstart", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("touchstart", handlePointerDown);
    };
  }, [isInputExpanded]);

  return (
    <div className="flex-1 overflow-y-auto p-8 rounded-[2rem] w-full h-full pb-32">
      <div className="mx-auto w-full max-w-7xl space-y-8">
            <section className="grid gap-4 md:grid-cols-4">
              <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm"><CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between"><CardTitle className="text-sm font-medium text-slate-500">Total Students</CardTitle><Users className="size-4 text-slate-400" /></CardHeader><CardContent className="px-5 pb-5"><div className="text-4xl font-semibold tracking-tight text-slate-900">{summary.total}</div></CardContent></Card>
              <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm"><CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between"><CardTitle className="text-sm font-medium text-slate-500">Eligible (unplaced + no backlog)</CardTitle><CheckCircle2 className="size-4 text-slate-400" /></CardHeader><CardContent className="px-5 pb-5"><div className="text-4xl font-semibold tracking-tight text-slate-900">{summary.qualified}</div></CardContent></Card>
              <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm"><CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between"><CardTitle className="text-sm font-medium text-slate-500">Avg Match Score</CardTitle><Target className="size-4 text-slate-400" /></CardHeader><CardContent className="px-5 pb-5"><div className="text-4xl font-semibold tracking-tight text-slate-900">{summary.avg.toFixed(1)}</div></CardContent></Card>
              <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm"><CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between"><CardTitle className="text-sm font-medium text-slate-500">Top Candidates</CardTitle><Trophy className="size-4 text-slate-400" /></CardHeader><CardContent className="px-5 pb-5"><div className="text-4xl font-semibold tracking-tight text-slate-900">{topKeys.size}</div></CardContent></Card>
            </section>

            <section className="bg-white rounded-[2rem] border border-slate-200/60 shadow-sm overflow-hidden flex flex-col">
              <div className="p-6 border-b border-slate-100 flex items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <h2 className="text-lg font-semibold text-slate-900">Live JD shortlist</h2>
                  <select
                    value={branch}
                    onChange={(e) => setBranch(e.target.value as BranchFilter)}
                    className="h-9 rounded-full bg-slate-50 border-transparent hover:bg-slate-100 px-4 text-sm font-medium text-slate-700"
                  >
                    <option value="All">All Branches</option>
                    {branchOptions.map((b) => (
                      <option key={b} value={b}>
                        {b}
                      </option>
                    ))}
                  </select>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value as GenderFilter)}
                    className="h-9 rounded-full bg-slate-50 border-transparent hover:bg-slate-100 px-4 text-sm font-medium text-slate-700"
                  >
                    <option value="All">All Genders</option>
                    <option value="women">Women</option>
                    <option value="men">Men</option>
                    <option value="other">Other</option>
                  </select>
                  <Input value={minCgpa} onChange={(e) => setMinCgpa(e.target.value)} placeholder="Min CGPA" className="h-9 rounded-full bg-slate-50 border-transparent hover:bg-slate-100 px-4 text-sm font-medium text-slate-700 w-32 placeholder:text-slate-400" />
                  {skills.length > 0 && (
                    <div className="flex items-center gap-1.5 pl-2 border-l border-slate-200">
                      {skills.map((s) => (
                        <Badge key={s} variant="secondary" className="h-7 rounded-full px-3 text-xs bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-100">
                          {s}
                          <button onClick={() => setSkills((prev) => prev.filter((v) => v !== s))} className="ml-1.5 hover:text-blue-900"><X className="size-3" /></button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={exportToCsv} className="h-9 rounded-full px-4 border-slate-200 text-slate-600 hover:bg-slate-50 gap-2">
                    <Download className="size-4" />
                    Export CSV
                  </Button>
                  <Button variant="outline" size="sm" onClick={resetFiltersAndSort} className="h-9 rounded-full px-4 border-slate-200 text-slate-600 hover:bg-slate-50">Reset Filters</Button>
                </div>
              </div>

              <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/60 text-xs text-slate-600">
                {filters ? (
                  <div className="flex flex-wrap items-center gap-4">
                    <span>Total: <strong>{filters.total_considered}</strong></span>
                    <span>Passed: <strong>{filters.passed_filters}</strong></span>
                    <span>Rejected CGPA: <strong>{filters.rejected_min_cgpa}</strong></span>
                    <span>Rejected Branch: <strong>{filters.rejected_branch}</strong></span>
                    <span>Rejected Gender: <strong>{filters.rejected_gender}</strong></span>
                    <span>Rejected Backlog: <strong>{filters.rejected_backlog}</strong></span>
                    <span>Rejected Placement: <strong>{filters.rejected_placement}</strong></span>
                  </div>
                ) : (
                  <span>Run JD analyze to see filter summary.</span>
                )}
              </div>
              {parsedJD && (
                <div className="px-6 py-3 border-b border-slate-100 text-xs text-slate-600 bg-white">
                  <span className="font-medium text-slate-700">JD:</span>{" "}
                  {[
                    parsedJD.job_title ? `Role ${parsedJD.job_title}` : null,
                    parsedJD.min_cgpa !== null ? `Min CGPA ${parsedJD.min_cgpa}` : null,
                    parsedJD.allowed_branches.length ? `Branches ${parsedJD.allowed_branches.join(", ")}` : null,
                    parsedJD.gender_filter !== "all_genders" ? `Gender ${parsedJD.gender_filter}` : null,
                  ]
                    .filter(Boolean)
                    .join(" | ") || "Parsed successfully"}
                </div>
              )}

              <div className="overflow-x-auto">
                <Table className="w-full">
                  <TableHeader><TableRow className="border-slate-100 hover:bg-transparent"><TableHead className="h-12 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Candidate</TableHead><TableHead className="h-12 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Branch</TableHead><TableHead className="h-12 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">CGPA</TableHead><TableHead className="h-12 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Match</TableHead><TableHead className="h-12 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Gender</TableHead><TableHead className="h-12 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Skills</TableHead><TableHead className="h-12 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider w-24">Status</TableHead></TableRow></TableHeader>
                  <TableBody>
                    {!filtered.length ? (
                      <TableRow><TableCell colSpan={7} className="h-64 text-center text-slate-400">{errorMessage ?? "No candidates found matching the criteria."}</TableCell></TableRow>
                    ) : (
                      filtered.map((c) => {
                        const isTop = topKeys.has(c.key);
                        const tone = scoreTone(c.matchScore);
                        return (
                          <React.Fragment key={c.key}>
                            <TableRow className="border-slate-50 hover:bg-slate-50/50 transition-colors group cursor-pointer" onClick={() => setExpandedKey(expandedKey === c.key ? null : c.key)}>
                              <TableCell className="px-6 py-4"><div className="flex items-center gap-3">{isTop ? <div className={cn("size-2 rounded-full", tone.dot)} /> : <div className="size-2" />}<span className="font-medium text-slate-900">{c.name}</span></div></TableCell>
                              <TableCell className="px-6 py-4 text-slate-600">{c.branch}</TableCell>
                              <TableCell className="px-6 py-4 text-right tabular-nums text-slate-600">{c.cgpa.toFixed(2)}</TableCell>
                              <TableCell className="px-6 py-4 text-right"><Badge variant="outline" className={cn("rounded-full px-2.5 py-0.5 font-medium border-transparent", tone.pill)}>{c.matchScore.toFixed(1)}%</Badge></TableCell>
                              <TableCell className="px-6 py-4 text-slate-600 capitalize">{c.gender}</TableCell>
                              <TableCell className="px-6 py-4"><div className="flex flex-wrap gap-1.5">{c.skills.slice(0, 3).map((s) => <span key={s} className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">{s}</span>)}{c.skills.length > 3 && <span className="inline-flex items-center rounded-full border border-slate-200 px-2.5 py-0.5 text-xs font-medium text-slate-500">+{c.skills.length - 3}</span>}</div></TableCell>
                              <TableCell className="px-6 py-4">{!c.hasBacklog && !c.isPlaced ? <CheckCircle2 className="size-5 text-emerald-500" /> : <span className="text-slate-300">—</span>}</TableCell>
                            </TableRow>
                            {expandedKey === c.key && (
                              <TableRow className="bg-slate-50/50 hover:bg-slate-50/50">
                                <TableCell colSpan={7} className="p-0 border-b-0">
                                  <div className="px-10 py-6 grid grid-cols-3 gap-8">
                                    <div className="space-y-4">
                                      <h4 className="text-sm font-semibold text-slate-900">Score Breakdown</h4>
                                      {([
                                        ["Resume vs JD", c.score.resume, 40],
                                        ["GitHub", c.score.github, 20],
                                        ["LeetCode", c.score.leetcode, 20],
                                        ["Academics", c.score.academics, 20],
                                        ["Total", c.score.total, 100],
                                      ] as const).map(([label, value, maxValue]) => (
                                        <div key={label} className="space-y-1.5">
                                          <div className="flex items-center justify-between gap-3 text-xs"><span className="text-slate-500">{label}</span><span className="font-medium tabular-nums text-slate-700">{value.toFixed(1)}</span></div>
                                          <Progress value={clamp01(value / maxValue) * 100} className="h-1.5 bg-slate-200" />
                                        </div>
                                      ))}
                                    </div>
                                    <div className="space-y-3">
                                      <h4 className="text-sm font-semibold text-slate-900">Candidate Details</h4>
                                      <div className="text-sm text-slate-700">Email: {c.email}</div>
                                      <div className="text-sm text-slate-700">Roll: {c.rollNo}</div>
                                      <div className="text-sm text-slate-700">Placed: {String(c.isPlaced)}</div>
                                      <div className="text-sm text-slate-700">Backlog: {String(c.hasBacklog)}</div>
                                      <div className="text-sm text-slate-700">Persona: {c.codingPersona}</div>
                                    </div>
                                    <div className="space-y-3">
                                      <h4 className="text-sm font-semibold text-slate-900">Resume Link</h4>
                                      {c.resumeUrl ? (
                                        <a href={c.resumeUrl} target="_blank" rel="noreferrer" className="text-sm text-blue-600 underline break-all">{c.resumeUrl}</a>
                                      ) : (
                                        <div className="text-sm text-slate-400">No resume URL available</div>
                                      )}
                                    </div>
                                    <CandidateFullDetails candidateId={c.id} />
                                  </div>
                                </TableCell>
                              </TableRow>
                            )}
                          </React.Fragment>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </div>
            </section>

            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-full max-w-3xl z-50 px-4">
              {(() => {
                const fileExt = fileUpload ? (fileUpload.name.match(/\.([^.]+)$/)?.[1] || "FILE").toUpperCase() : "";
                const fileBase = fileUpload ? fileUpload.name.replace(/\.[^.]+$/, "") : "";
                return (
                  <motion.div
                    ref={composerRef}
                    layout
                    transition={{ layout: { type: "spring", stiffness: 320, damping: 36, mass: 0.85 } }}
                    className="bg-white shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-slate-200/60 hover:shadow-[0_8px_30px_rgb(0,0,0,0.16)] rounded-[28px] p-3 flex flex-col"
                  >
                    <AnimatePresence initial={false}>
                      {fileUpload && (
                        <motion.div
                          key="file-chip"
                          layout
                          initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                          animate={{ opacity: 1, height: "auto", marginBottom: 8 }}
                          exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                          transition={{ type: "spring", stiffness: 300, damping: 34, mass: 0.9 }}
                          className="flex flex-wrap gap-2 px-1 overflow-hidden"
                        >
                          <div className="flex items-center gap-2.5 bg-slate-50 border border-slate-200/80 rounded-2xl pl-2 pr-2 py-2 max-w-[260px]">
                            <div className="size-9 rounded-lg bg-red-500 text-white flex items-center justify-center shrink-0">
                              <FileText className="size-4" />
                            </div>
                            <div className="min-w-0 pr-1">
                              <div className="text-sm font-medium text-slate-900 truncate leading-tight" title={fileUpload.name}>
                                {fileBase}
                              </div>
                              <div className="text-[11px] text-slate-500 uppercase leading-tight tracking-wide">
                                {fileExt}
                              </div>
                            </div>
                            <button
                              type="button"
                              onClick={() => setFileUpload(null)}
                              className="ml-1 size-5 rounded-full bg-slate-200 hover:bg-slate-300 flex items-center justify-center shrink-0"
                              aria-label="Remove JD file"
                            >
                              <X className="size-3 text-slate-600" />
                            </button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    <motion.div
                      layout
                      className="min-w-0 relative overflow-hidden w-full px-1"
                      animate={{ height: isInputExpanded ? composerInputHeight : COMPACT_HEIGHT }}
                      transition={{ type: "spring", stiffness: 280, damping: 34, mass: 0.9 }}
                    >
                      <AnimatePresence mode="wait" initial={false}>
                        {!isInputExpanded ? (
                          <motion.button
                            key="collapsed-preview"
                            type="button"
                            onClick={handleExpandInput}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.18, ease: "easeInOut" }}
                            className="h-full w-full text-left text-base leading-6 text-slate-700 placeholder:text-slate-400 truncate overflow-hidden pr-4 inline-flex items-center [mask-image:linear-gradient(to_right,black_85%,transparent)]"
                          >
                            {collapsedPreview || "Describe JD and constraints or upload JD file..."}
                          </motion.button>
                        ) : (
                          <motion.textarea
                            key="expanded-textarea"
                            ref={jdTextareaRef}
                            value={jdInput}
                            onChange={(e) => setJdInput(e.target.value)}
                            onFocus={handleExpandInput}
                            onClick={handleExpandInput}
                            placeholder="Describe JD and constraints or upload JD file..."
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.18, ease: "easeInOut" }}
                            className="h-full w-full resize-none bg-transparent border-none focus:outline-none text-slate-700 placeholder:text-slate-400 text-base leading-6 py-1 whitespace-pre-wrap overflow-y-auto"
                            onKeyDown={(e) => {
                              if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                if (!loading) void runMatch();
                              }
                            }}
                          />
                        )}
                      </AnimatePresence>
                    </motion.div>

                    <div className="flex items-center justify-between pt-2">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={loading}
                        className="shrink-0 rounded-full size-10 text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                      >
                        <UploadCloud className="size-5" />
                      </Button>
                      <Button
                        onClick={() => void runMatch()}
                        disabled={loading || (!fileUpload && jdInput.trim().length < 20)}
                        className="rounded-full h-10 px-5 bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-sm"
                      >
                        {loading ? <Loader2 className="size-5 animate-spin" /> : "Analyze"}
                      </Button>
                    </div>

                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                      className="hidden"
                      onChange={(e) => setFileUpload(e.target.files?.[0] ?? null)}
                    />
                  </motion.div>
                );
              })()}
            </div>
            </div>
          </div>
  );
}