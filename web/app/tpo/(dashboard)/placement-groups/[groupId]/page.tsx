"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

import { clearTpoAuth } from "@/lib/auth-storage";
import {
  getTpoMailJobProgress,
  getApiErrorMessage,
  listTpoGroups,
  markStudentPlacement,
  triggerTpoMailAction,
} from "@/lib/api";
import type { TpoGroup, TpoMailJobProgressResponse, TpoMailType } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";

export default function PlacementGroupDetailPage() {
  const params = useParams<{ groupId: string }>();
  const router = useRouter();
  const [group, setGroup] = useState<TpoGroup | null>(null);
  const [loading, setLoading] = useState(true);
  const [mailing, setMailing] = useState(false);
  const [bulkMailJob, setBulkMailJob] = useState<TpoMailJobProgressResponse | null>(null);
  const [bulkPolling, setBulkPolling] = useState(false);
  const [placingStudentId, setPlacingStudentId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mailType, setMailType] = useState<TpoMailType>("shortlist_notice");
  const [customSubject, setCustomSubject] = useState("");
  const [customBody, setCustomBody] = useState("");
  const [additionalNote, setAdditionalNote] = useState("");
  const [prepTopicsText, setPrepTopicsText] = useState("");
  const [interviewDate, setInterviewDate] = useState("");
  const [interviewStart, setInterviewStart] = useState("");
  const [interviewEnd, setInterviewEnd] = useState("");

  const groupId = useMemo(() => Number(params.groupId), [params.groupId]);
  const bulkStatusLabel = useMemo(() => {
    if (!bulkMailJob) return "";
    if (bulkMailJob.status === "queued") return "Queued";
    if (bulkMailJob.status === "running") return "Sending";
    if (bulkMailJob.status === "completed") return "Completed";
    return bulkMailJob.failure_count > 0 ? "Completed with failures" : "Failed";
  }, [bulkMailJob]);

  useEffect(() => {
    let mounted = true;
    if (!Number.isFinite(groupId)) {
      setError("Invalid group id.");
      setLoading(false);
      return;
    }
    void listTpoGroups()
      .then((groups) => {
        if (!mounted) return;
        const selected = groups.find((item) => item.id === groupId) || null;
        if (!selected) {
          setError("Group not found.");
          setGroup(null);
          return;
        }
        setGroup(selected);
      })
      .catch((err) => {
        if (!mounted) return;
        if (axios.isAxiosError(err) && [401, 403].includes(err.response?.status ?? 0)) {
          clearTpoAuth();
          router.replace("/tpo/login");
          return;
        }
        setError(getApiErrorMessage(err));
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [groupId, router]);

  const sendBulkMail = async () => {
    if (!group) return;
    setMailing(true);
    try {
      const result = await triggerTpoMailAction({
        group_id: group.id,
        mode: "bulk",
        mail_type: mailType,
        subject: customSubject || undefined,
        body: customBody || undefined,
        additional_note: additionalNote || undefined,
        prep_topics: prepTopicsText
          .split(",")
          .map((topic) => topic.trim())
          .filter(Boolean),
        interview_date: interviewDate || undefined,
        interview_time_start: interviewStart || undefined,
        interview_time_end: interviewEnd || undefined,
      });
      if (typeof result.job_id !== "number") {
        throw new Error("Bulk mail job could not be started.");
      }
      setBulkPolling(true);
      setBulkMailJob({
        job_id: result.job_id,
        group_id: group.id,
        mail_type: mailType,
        status: result.status ?? "queued",
        total_recipients: result.total_recipients ?? group.members.length,
        processed_count: result.processed_count ?? 0,
        success_count: result.success_count ?? 0,
        failure_count: result.failure_count ?? 0,
        progress_percent: 0,
        last_error: null,
        started_at: null,
        finished_at: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
      toast.success(result.message);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setMailing(false);
    }
  };

  const sendIndividualMail = async (studentId: number) => {
    if (!group) return;
    setMailing(true);
    try {
      const result = await triggerTpoMailAction({
        group_id: group.id,
        mode: "individual",
        mail_type: mailType,
        student_id: studentId,
        subject: customSubject || undefined,
        body: customBody || undefined,
        additional_note: additionalNote || undefined,
        prep_topics: prepTopicsText
          .split(",")
          .map((topic) => topic.trim())
          .filter(Boolean),
        interview_date: interviewDate || undefined,
        interview_time_start: interviewStart || undefined,
        interview_time_end: interviewEnd || undefined,
      });
      toast.success(result.message);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setMailing(false);
    }
  };

  const markPlaced = async (studentId: number) => {
    setPlacingStudentId(studentId);
    try {
      await markStudentPlacement({
        student_id: studentId,
        group_id: group.id,
        pay_amount: null,
        notes: `Marked from Placement Group #${groupId}`,
      });
      setGroup((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          members: prev.members.map((member) =>
            member.student_id === studentId
              ? {
                  ...member,
                  placement: {
                    company_name: group.company_name || "N/A",
                    offer_type: (group.role_type || "job") as "internship" | "job",
                    pay_amount: null,
                    notes: `Marked from Placement Group #${groupId}`,
                    is_active: true,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                  },
                }
              : member,
          ),
        };
      });
      toast.success("Student marked as placed.");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setPlacingStudentId(null);
    }
  };

  useEffect(() => {
    if (!bulkPolling || !bulkMailJob?.job_id) return;

    let cancelled = false;
    const poll = async () => {
      try {
        const progress = await getTpoMailJobProgress(bulkMailJob.job_id);
        if (cancelled) return;
        setBulkMailJob(progress);
        if (progress.status === "completed" || progress.status === "failed") {
          setBulkPolling(false);
          if (progress.failure_count > 0) {
            toast.warning(
              `Bulk mail finished with ${progress.success_count} success and ${progress.failure_count} failure(s).`,
            );
          } else {
            toast.success(`Bulk mail completed for ${progress.success_count} recipient(s).`);
          }
          return;
        }
        setTimeout(() => {
          void poll();
        }, 1000);
      } catch (err) {
        if (cancelled) return;
        setBulkPolling(false);
        toast.error(getApiErrorMessage(err));
      }
    };

    void poll();
    return () => {
      cancelled = true;
    };
  }, [bulkPolling, bulkMailJob?.job_id]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center text-slate-500">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Loading group details...
      </div>
    );
  }

  if (error || !group) {
    return (
      <div className="flex-1 p-8">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-6 text-red-700">{error || "Group not found."}</CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-8 rounded-[2rem] w-full h-full">
      <div className="mx-auto w-full max-w-7xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">{group.title}</h1>
            <p className="text-sm text-slate-600">
              Created by {group.created_by} on {new Date(group.created_at).toLocaleString()}
            </p>
            <p className="text-sm text-slate-600">
              Company: <span className="font-medium">{group.company_name || "Not captured"}</span> · Role type:{" "}
              <span className="font-medium">{group.role_type || "Not captured"}</span>
            </p>
            <p className="text-sm text-slate-600">
              Pay/Stipend: <span className="font-medium">{group.pay_or_stipend || "Not captured"}</span> · Duration:{" "}
              <span className="font-medium">{group.duration || "Not captured"}</span>
            </p>
            <p className="text-sm text-slate-600">
              Bond: <span className="font-medium">{group.bond_details || "Not captured"}</span>
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/tpo/placement-groups">
              <Button variant="outline">Back to groups</Button>
            </Link>
            <Button onClick={() => void sendBulkMail()} disabled={mailing || bulkPolling}>
              Bulk mail
            </Button>
          </div>
        </div>

        {bulkMailJob ? (
          <Card>
            <CardHeader>
              <CardTitle>Bulk Mail Progress</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between text-sm text-slate-600">
                <span>Status: {bulkStatusLabel}</span>
                <span>
                  {bulkMailJob.processed_count}/{bulkMailJob.total_recipients} processed
                </span>
              </div>
              <Progress value={bulkMailJob.progress_percent} className="h-2 bg-slate-200" />
              <div className="grid grid-cols-3 gap-2 text-sm">
                <p>Success: {bulkMailJob.success_count}</p>
                <p>Failed: {bulkMailJob.failure_count}</p>
                <p>Progress: {Math.round(bulkMailJob.progress_percent)}%</p>
              </div>
              {bulkMailJob.last_error ? (
                <p className="text-xs text-red-600">Last error: {bulkMailJob.last_error}</p>
              ) : null}
            </CardContent>
          </Card>
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle>JD Summary</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-slate-700 whitespace-pre-wrap">
            {group.jd_summary?.trim() || "No JD summary provided."}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Mail Composer</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 md:grid-cols-2">
              <select
                value={mailType}
                onChange={(e) => setMailType(e.target.value as TpoMailType)}
                className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="shortlist_notice">Shortlist notice</option>
                <option value="prep_topics">Preparation topics</option>
                <option value="interview_schedule">Interview schedule</option>
                <option value="process_custom">Custom process mail</option>
              </select>
              <Input
                placeholder="Additional note (optional)"
                value={additionalNote}
                onChange={(e) => setAdditionalNote(e.target.value)}
              />
            </div>
            {mailType === "prep_topics" ? (
              <Input
                placeholder="Prep topics (comma separated)"
                value={prepTopicsText}
                onChange={(e) => setPrepTopicsText(e.target.value)}
              />
            ) : null}
            {mailType === "interview_schedule" ? (
              <div className="grid gap-3 md:grid-cols-3">
                <Input type="date" value={interviewDate} onChange={(e) => setInterviewDate(e.target.value)} />
                <Input type="time" value={interviewStart} onChange={(e) => setInterviewStart(e.target.value)} />
                <Input type="time" value={interviewEnd} onChange={(e) => setInterviewEnd(e.target.value)} />
              </div>
            ) : null}
            {mailType === "process_custom" ? (
              <div className="space-y-2">
                <Input
                  placeholder="Custom subject"
                  value={customSubject}
                  onChange={(e) => setCustomSubject(e.target.value)}
                />
                <textarea
                  value={customBody}
                  onChange={(e) => setCustomBody(e.target.value)}
                  placeholder="Custom body (supports {student_name}, {company_name})"
                  className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Group Members ({group.members.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Roll</TableHead>
                  <TableHead>Branch</TableHead>
                  <TableHead>Placement</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {group.members.map((member) => (
                  <TableRow key={member.student_id}>
                    <TableCell className="font-medium">{member.name}</TableCell>
                    <TableCell>{member.email}</TableCell>
                    <TableCell>{member.roll_no || "—"}</TableCell>
                    <TableCell>{member.branch}</TableCell>
                    <TableCell>
                      {member.placement?.is_active
                        ? `${member.placement.offer_type} @ ${member.placement.company_name}`
                        : "Not placed"}
                    </TableCell>
                    <TableCell className="text-right space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => void sendIndividualMail(member.student_id)}
                        disabled={mailing || bulkPolling}
                      >
                        Mail
                      </Button>
                      {!member.placement?.is_active ? (
                        <Button
                          size="sm"
                          onClick={() => void markPlaced(member.student_id)}
                          disabled={placingStudentId === member.student_id}
                        >
                          Mark placed
                        </Button>
                      ) : null}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
