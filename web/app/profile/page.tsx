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
import { Badge } from "@/components/ui/badge";
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

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </main>
    );
  }

  if (!profile) {
    return (
      <main className="mx-auto max-w-lg space-y-6 px-4 py-12">
        <Card>
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
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-10">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Your profile</h1>
          <p className="text-sm text-muted-foreground">
            {student.name} · {student.email}
            {student.roll_no ? ` · ${student.roll_no}` : ""}
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/dashboard"
            className={cn(buttonVariants({ variant: "outline" }))}
          >
            Update analysis
          </Link>
          <Button variant="secondary" onClick={signOut}>
            Sign out
          </Button>
        </div>
      </header>

      <div className="flex gap-2">
        <Button
          variant={activeTab === "overview" ? "default" : "outline"}
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </Button>
        <Button
          variant={activeTab === "resume" ? "default" : "outline"}
          onClick={() => setActiveTab("resume")}
        >
          Resume
        </Button>
      </div>

      {activeTab === "overview" ? (
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Academics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div>Branch: {student.branch}</div>
              <div>Phone: {student.phone}</div>
              <div>CGPA: {student.cgpa ?? "—"}</div>
              <div className="flex items-center gap-2">
                Marks:
                {student.cgpa_verified ? (
                  <Badge>Verified</Badge>
                ) : (
                  <Badge variant="secondary">Unverified</Badge>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Overall score</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-2xl font-semibold">
                {profile.overall_score.toFixed(1)} / 100
              </div>
              <Progress value={profile.overall_score} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Placement status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {profile.placement?.is_active ? (
                <>
                  <div>Company: {profile.placement.company_name}</div>
                  <div>Type: {profile.placement.offer_type}</div>
                  <div>Pay/Stipend: {profile.placement.pay_amount ?? "—"}</div>
                  <div>Notes: {profile.placement.notes || "—"}</div>
                </>
              ) : (
                <div className="text-muted-foreground">Not placed yet.</div>
              )}
            </CardContent>
          </Card>

          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle className="text-base">Skills</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {profile.skills.length ? (
                profile.skills.map((s) => (
                  <Badge key={s} variant="secondary">
                    {s}
                  </Badge>
                ))
              ) : (
                <span className="text-sm text-muted-foreground">No skills stored.</span>
              )}
            </CardContent>
          </Card>

          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle className="text-base">Coding</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Persona</span>
                <Badge>{profile.coding.persona || "—"}</Badge>
              </div>
              <div>Score: {profile.coding.score.toFixed(1)}</div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(320px,420px)_1fr] lg:h-[calc(100vh-12rem)]">
          <Card className="flex flex-col h-full overflow-auto">
            <CardHeader>
              <CardTitle className="text-base">Resume analysis</CardTitle>
              <CardDescription>
                ATS-focused highlights from your latest submitted resume.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">ATS score</span>
                  <span className="font-medium">{profile.overall_score.toFixed(1)} / 100</span>
                </div>
                <Progress value={profile.overall_score} />
              </div>

              <div className="grid gap-3 rounded-md border p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Coding score</span>
                  <span className="font-medium">{profile.coding.score.toFixed(1)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Persona</span>
                  <Badge variant="secondary">{profile.coding.persona || "—"}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Skills captured</span>
                  <span className="font-medium">{profile.skills.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Last analyzed</span>
                  <span className="font-medium">{lastAnalyzedLabel}</span>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Top extracted skills</p>
                <div className="flex flex-wrap gap-2">
                  {topSkills.length ? (
                    topSkills.map((skill) => (
                      <Badge key={skill} variant="secondary">
                        {skill}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-sm text-muted-foreground">No skills extracted yet.</span>
                  )}
                </div>
              </div>

              <Link href="/dashboard" className={cn(buttonVariants(), "w-full")}>
                Update Resume
              </Link>
            </CardContent>
          </Card>

          <Card className="flex flex-col h-full overflow-hidden">
            <CardHeader>
              <CardTitle className="text-base">Resume preview</CardTitle>
              <CardDescription>
                Preview your saved resume. If the preview is unavailable, open it in a new tab.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col space-y-4 overflow-hidden">
              {resumeUrl ? (
                <>
                  <ResumePdfViewer
                    url={resumeUrl}
                    className="flex-1 min-h-0"
                  />
                  <a
                    href={resumeUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={cn(buttonVariants({ variant: "outline" }), "shrink-0")}
                  >
                    Open in new tab
                  </a>
                </>
              ) : (
                <div className="rounded-md border p-4 text-sm text-muted-foreground">
                  No resume URL found for this profile yet.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </main>
  );
}
