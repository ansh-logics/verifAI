"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import axios from "axios";

import { getMyProfile, getApiErrorMessage } from "@/lib/api";
import { clearAuth, getStoredToken } from "@/lib/auth-storage";
import type { StudentProfileDetail } from "@/lib/types";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import ResumePdfViewer from "@/components/resume-pdf-viewer";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<StudentProfileDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "resume">("overview");

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    (async () => {
      try {
        const data = await getMyProfile(token);
        setProfile(data);
      } catch (e) {
        if (axios.isAxiosError(e) && e.response?.status === 404) {
          setProfile(null);
        } else {
          toast.error(getApiErrorMessage(e));
          router.replace("/login");
        }
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  const signOut = () => {
    clearAuth();
    router.replace("/login");
  };
  const surfaceCardClass = "rounded-3xl border border-slate-200/60 bg-white shadow-sm";

  if (loading) {
    return (
      <main className="min-h-screen bg-[#f8f9fa] px-4 py-8">
        <div className="mx-auto max-w-6xl space-y-3">
          <header className="flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-2">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-4 w-64" />
            </div>
            <div className="flex gap-2">
              <Skeleton className="h-10 w-32" />
              <Skeleton className="h-10 w-24" />
            </div>
          </header>

          <div className="flex gap-2">
            <Skeleton className="h-10 w-24" />
            <Skeleton className="h-10 w-24" />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card className={surfaceCardClass}>
              <CardHeader>
                <Skeleton className="h-5 w-24" />
              </CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </CardContent>
            </Card>

            <Card className={surfaceCardClass}>
              <CardHeader>
                <Skeleton className="h-5 w-32" />
              </CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-8 w-20" />
                <Skeleton className="h-2 w-full" />
              </CardContent>
            </Card>

            <Card className={`md:col-span-2 ${surfaceCardClass}`}>
              <CardHeader>
                <Skeleton className="h-5 w-16" />
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-6 w-20 rounded-full" />
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    );
  }

  if (!profile) {
    return (
      <main className="min-h-screen bg-[#f8f9fa] px-4 py-8">
        <div className="mx-auto max-w-lg space-y-3">
          <Card className={surfaceCardClass}>
            <CardHeader>
              <CardTitle>No saved profile yet</CardTitle>
              <CardDescription>
                Run analysis and save your profile from the dashboard.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex gap-3">
              <Link href="/dashboard" className={cn(buttonVariants())}>
                Go to dashboard
              </Link>
              <Button variant="outline" onClick={signOut}>
                Sign out
              </Button>
            </CardContent>
          </Card>
        </div>
      </main>
    );
  }

  const { student } = profile;
  const resumeUrl =
    profile.resume_url ||
    (typeof profile.resume_data?.url === "string" ? profile.resume_data.url : null);
  const lastAnalyzedLabel = new Date(profile.last_analyzed_at).toLocaleString();
  const topSkills = profile.skills.slice(0, 8);

  return (
    <main className="min-h-screen bg-[#f8f9fa] px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-3">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900">Your profile</h1>
          <p className="text-sm text-slate-600">
            {student.name} · {student.email}
            {student.roll_no ? ` · ${student.roll_no}` : ""}
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/dashboard"
            className={cn(
              buttonVariants({ variant: "outline" }),
              "rounded-full border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
            )}
          >
            Update analysis
          </Link>
          <Button variant="secondary" className="rounded-full bg-slate-100 text-slate-800 hover:bg-slate-200" onClick={signOut}>
            Sign out
          </Button>
        </div>
      </header>

      <div className="flex gap-2">
        <Button
          variant={activeTab === "overview" ? "default" : "outline"}
          className={cn(
            "rounded-full",
            activeTab === "overview"
              ? "bg-blue-600 text-white hover:bg-blue-700"
              : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
          )}
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </Button>
        <Button
          variant={activeTab === "resume" ? "default" : "outline"}
          className={cn(
            "rounded-full",
            activeTab === "resume"
              ? "bg-blue-600 text-white hover:bg-blue-700"
              : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
          )}
          onClick={() => setActiveTab("resume")}
        >
          Resume
        </Button>
      </div>

      {activeTab === "overview" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card className={surfaceCardClass}>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Academics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm pt-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Branch</span>
                <span className="font-medium text-slate-900">{student.branch}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Phone</span>
                <span className="font-medium text-slate-900">{student.phone}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">CGPA</span>
                <span className="font-medium text-slate-900">{student.cgpa ?? "—"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Marks</span>
                {student.cgpa_verified ? (
                  <span className="text-[10px] font-bold uppercase tracking-wider bg-green-50 text-green-700 px-2 py-1 rounded-md ring-1 ring-green-100">Verified</span>
                ) : (
                  <span className="text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-600 px-2 py-1 rounded-md ring-1 ring-slate-200">Unverified</span>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className={surfaceCardClass}>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Overall score</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-4">
              <div className="text-4xl font-semibold tracking-tight text-slate-900">
                {profile.overall_score.toFixed(1)} <span className="text-xl text-slate-400 font-medium">/ 100</span>
              </div>
              <Progress value={profile.overall_score} className="h-2" />
            </CardContent>
          </Card>

          <Card className={surfaceCardClass}>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Placement status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm pt-4">
              {profile.placement?.is_active ? (
                <>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Company</span>
                    <span className="font-medium text-slate-900">{profile.placement.company_name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Type</span>
                    <span className="font-medium text-slate-900">{profile.placement.offer_type}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Pay/Stipend</span>
                    <span className="font-medium text-slate-900">{profile.placement.pay_amount ?? "—"}</span>
                  </div>
                  {profile.placement.notes && (
                    <div className="pt-2 border-t border-slate-100 text-slate-600 mt-2">
                      {profile.placement.notes}
                    </div>
                  )}
                </>
              ) : (
                <div className="text-slate-500">Not placed yet.</div>
              )}
            </CardContent>
          </Card>

          <Card className={`md:col-span-2 ${surfaceCardClass}`}>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Skills</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2 pt-4">
              {profile.skills.length ? (
                profile.skills.map((s) => (
                  <span key={s} className="bg-slate-100 text-slate-700 text-xs px-3 py-1.5 rounded-md font-medium">
                    {s}
                  </span>
                ))
              ) : (
                <span className="text-sm text-slate-500">No skills stored.</span>
              )}
            </CardContent>
          </Card>

          <Card className={`md:col-span-2 ${surfaceCardClass}`}>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Coding</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm pt-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Persona</span>
                <span className="font-medium text-slate-900">{profile.coding.persona || "—"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Score</span>
                <span className="font-medium text-slate-900">{profile.coding.score.toFixed(1)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="grid gap-3 lg:grid-cols-[minmax(320px,420px)_1fr] lg:h-[calc(100vh-10.5rem)]">
          <Card className={`flex h-full flex-col overflow-auto ${surfaceCardClass}`}>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Resume analysis</CardTitle>
              <CardDescription className="text-slate-500">
                ATS-focused highlights from your latest submitted resume.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5 pt-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-500">ATS score</span>
                  <span className="font-semibold text-slate-900">{profile.overall_score.toFixed(1)} <span className="text-slate-400 font-normal">/ 100</span></span>
                </div>
                <Progress value={profile.overall_score} className="h-2" />
              </div>

              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Coding score</span>
                  <span className="font-medium text-slate-900">{profile.coding.score.toFixed(1)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Persona</span>
                  <span className="font-medium text-slate-900">{profile.coding.persona || "—"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Skills captured</span>
                  <span className="font-medium text-slate-900">{profile.skills.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Last analyzed</span>
                  <span className="font-medium text-slate-900">{lastAnalyzedLabel}</span>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-sm text-slate-500">Top extracted skills</p>
                <div className="flex flex-wrap gap-2">
                  {topSkills.length ? (
                    topSkills.map((skill) => (
                      <span key={skill} className="bg-slate-100 text-slate-700 text-xs px-2.5 py-1 rounded-md font-medium">
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-sm text-slate-500">No skills extracted yet.</span>
                  )}
                </div>
              </div>

              <Link href="/dashboard" className={cn(buttonVariants(), "w-full bg-blue-600 text-white hover:bg-blue-700 rounded-full")}>
                Update Resume
              </Link>
            </CardContent>
          </Card>

          <Card className={`flex h-full flex-col overflow-hidden ${surfaceCardClass}`}>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Resume preview</CardTitle>
              <CardDescription className="text-slate-500">
                Preview your saved resume. If the preview is unavailable, open it in a new tab.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col space-y-4 overflow-hidden pt-4">
              {resumeUrl ? (
                <>
                  <ResumePdfViewer
                    url={resumeUrl}
                    className="flex-1 min-h-0 rounded-xl border border-slate-200 overflow-hidden"
                  />
                  <a
                    href={resumeUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={cn(buttonVariants({ variant: "outline" }), "shrink-0 rounded-full border-slate-200 bg-white text-slate-700 hover:bg-slate-50")}
                  >
                    Open in new tab
                  </a>
                </>
              ) : (
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                  No resume URL found for this profile yet.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
      </div>
    </main>
  );
}
