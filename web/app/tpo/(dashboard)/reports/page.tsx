"use client";

import { useEffect, useMemo, useState } from "react";
import { Download, FileSpreadsheet, FileText, Loader2 } from "lucide-react";
import { toast } from "sonner";

import {
  downloadTpoReport,
  getApiErrorMessage,
  getTpoReportPreview,
  listTpoGroups,
  updateReportPlacementPay,
} from "@/lib/api";
import type { TpoGroup, TpoReportFormat, TpoReportPreviewResponse } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

export default function TpoReportsPage() {
  const [reportData, setReportData] = useState<TpoReportPreviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [exportingFormat, setExportingFormat] = useState<TpoReportFormat | null>(null);
  const [groups, setGroups] = useState<TpoGroup[]>([]);
  const [groupSearch, setGroupSearch] = useState("");
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [branch, setBranch] = useState("");
  const [placedOnly, setPlacedOnly] = useState(false);
  const [payDrafts, setPayDrafts] = useState<Record<number, string>>({});
  const [savingPayByStudent, setSavingPayByStudent] = useState<Record<number, boolean>>({});

  async function loadPreview() {
    setLoading(true);
    try {
      const data = await getTpoReportPreview({
        group_id: selectedGroupId ?? undefined,
        branch: branch || undefined,
        placed_only: placedOnly,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      });
      setReportData(data);
    } catch (error) {
      toast.error(getApiErrorMessage(error));
      setReportData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadPreview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    void listTpoGroups()
      .then((rows) => setGroups(rows))
      .catch(() => {
        setGroups([]);
      });
  }, []);

  async function handleExport(format: TpoReportFormat) {
    setExportingFormat(format);
    try {
      const { blob, filename } = await downloadTpoReport(format, {
        group_id: selectedGroupId ?? undefined,
        branch: branch || undefined,
        placed_only: placedOnly,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      });
      saveBlob(blob, filename);
      toast.success(`Exported ${format.toUpperCase()} successfully.`);
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setExportingFormat(null);
    }
  }

  const overview = reportData?.overview;
  const topPlacements = useMemo(() => reportData?.placements.slice(0, 30) ?? [], [reportData?.placements]);
  const internshipCount = useMemo(() => {
    if (typeof overview?.internships_count === "number") return overview.internships_count;
    const internshipIds = new Set<number>();
    for (const row of reportData?.placements ?? []) {
      if (row.offer_type?.toLowerCase() === "internship") {
        internshipIds.add(row.student_id);
      }
    }
    return internshipIds.size;
  }, [overview?.internships_count, reportData?.placements]);
  const branchOptions = useMemo(() => {
    const set = new Set<string>(["CSE", "IT", "ECE", "EEE", "ME", "CE", "AIML", "DS"]);
    for (const row of reportData?.placements ?? []) {
      if (row.branch?.trim()) set.add(row.branch.trim());
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [reportData?.placements]);
  const filteredGroups = useMemo(() => {
    const q = groupSearch.trim().toLowerCase();
    if (!q) return groups.slice(0, 8);
    return groups.filter((g) => g.title.toLowerCase().includes(q)).slice(0, 8);
  }, [groups, groupSearch]);

  useEffect(() => {
    const nextDrafts: Record<number, string> = {};
    for (const row of topPlacements) {
      nextDrafts[row.student_id] = row.pay_amount !== null ? String(row.pay_amount) : "";
    }
    setPayDrafts(nextDrafts);
  }, [topPlacements]);

  async function handleSavePay(studentId: number) {
    const raw = (payDrafts[studentId] ?? "").trim();
    if (raw && Number.isNaN(Number(raw))) {
      toast.error("Pay must be a valid number.");
      return;
    }
    const payAmount = raw === "" ? null : Number(raw);
    if (payAmount !== null && payAmount < 0) {
      toast.error("Pay cannot be negative.");
      return;
    }
    setSavingPayByStudent((prev) => ({ ...prev, [studentId]: true }));
    try {
      const updated = await updateReportPlacementPay(studentId, { pay_amount: payAmount });
      setReportData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          placements: prev.placements.map((row) =>
            row.student_id === studentId
              ? {
                  ...row,
                  pay_amount: updated.pay_amount,
                  updated_at: updated.updated_at,
                }
              : row,
          ),
        };
      });
      setPayDrafts((prev) => ({
        ...prev,
        [studentId]: updated.pay_amount !== null ? String(updated.pay_amount) : "",
      }));
      toast.success("Pay updated.");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setSavingPayByStudent((prev) => ({ ...prev, [studentId]: false }));
    }
  }

  return (
    <div className="flex-1 overflow-y-auto p-8 rounded-[2rem] w-full h-full pb-10">
      <div className="mx-auto w-full max-w-7xl space-y-8">
        <div className="rounded-3xl border border-slate-200/60 bg-white p-6 shadow-sm">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">TPO Reports</h1>
          <p className="mt-1 text-sm text-slate-600">
            Generate authority-ready reports and export in PDF, DOCX, CSV, or XLSX.
          </p>
          <div className="mt-5 grid gap-3 md:grid-cols-2 lg:grid-cols-6">
            <div className="relative">
              <Input
                value={groupSearch}
                onChange={(e) => {
                  setGroupSearch(e.target.value);
                  setSelectedGroupId(null);
                }}
                placeholder="Search group by name"
                className="h-9 rounded-full bg-slate-50 border-transparent hover:bg-slate-100 px-4 text-sm font-medium text-slate-700 placeholder:text-slate-400"
              />
              {groupSearch.trim() ? (
                <div className="absolute z-20 mt-1 max-h-48 w-full overflow-y-auto rounded-2xl border border-slate-200/80 bg-white shadow-sm">
                  {filteredGroups.length === 0 ? (
                    <p className="px-3 py-2 text-xs text-slate-500">No groups found</p>
                  ) : (
                    filteredGroups.map((group) => (
                      <button
                        key={group.id}
                        type="button"
                        className="block w-full px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
                        onClick={() => {
                          setGroupSearch(group.title);
                          setSelectedGroupId(group.id);
                        }}
                      >
                        {group.title}
                      </button>
                    ))
                  )}
                </div>
              ) : null}
            </div>
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="h-9 rounded-full bg-slate-50 border-transparent hover:bg-slate-100 px-4 text-sm font-medium text-slate-700"
            />
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="h-9 rounded-full bg-slate-50 border-transparent hover:bg-slate-100 px-4 text-sm font-medium text-slate-700"
            />
            <select
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              className="h-9 w-full rounded-full bg-slate-50 border border-transparent hover:bg-slate-100 px-4 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
            >
              <option value="">All Branches</option>
              {branchOptions.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </select>
            <Button
              onClick={() => void loadPreview()}
              disabled={loading}
              className="h-9 rounded-full px-5 bg-blue-600 hover:bg-blue-700 text-white"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Refresh Preview
            </Button>
          </div>
        </div>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
            <CardHeader className="pb-2 pt-5 px-5">
              <CardTitle className="text-sm font-medium text-slate-500">Total Students</CardTitle>
            </CardHeader>
            <CardContent className="px-5 pb-5">
              <p className="text-4xl font-semibold tracking-tight text-slate-900">{overview?.total_students ?? 0}</p>
            </CardContent>
          </Card>
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
            <CardHeader className="pb-2 pt-5 px-5">
              <CardTitle className="text-sm font-medium text-slate-500">Unplaced Eligible</CardTitle>
            </CardHeader>
            <CardContent className="px-5 pb-5">
              <p className="text-4xl font-semibold tracking-tight text-slate-900">{overview?.unplaced_eligible_students ?? 0}</p>
            </CardContent>
          </Card>
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
            <CardHeader className="pb-2 pt-5 px-5">
              <CardTitle className="text-sm font-medium text-slate-500">Active Groups</CardTitle>
            </CardHeader>
            <CardContent className="px-5 pb-5">
              <p className="text-4xl font-semibold tracking-tight text-slate-900">{overview?.active_groups ?? 0}</p>
            </CardContent>
          </Card>
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
            <CardHeader className="pb-2 pt-5 px-5">
              <CardTitle className="text-sm font-medium text-slate-500">Placed Students</CardTitle>
            </CardHeader>
            <CardContent className="px-5 pb-5">
              <p className="text-4xl font-semibold tracking-tight text-slate-900">{overview?.placed_students ?? 0}</p>
            </CardContent>
          </Card>
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
            <CardHeader className="pb-2 pt-5 px-5">
              <CardTitle className="text-sm font-medium text-slate-500">Internships</CardTitle>
            </CardHeader>
            <CardContent className="px-5 pb-5">
              <p className="text-4xl font-semibold tracking-tight text-slate-900">{internshipCount}</p>
            </CardContent>
          </Card>
        </section>

        <div className="rounded-3xl border border-slate-200/60 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center gap-2">
            <Button
              onClick={() => void handleExport("pdf")}
              disabled={Boolean(exportingFormat)}
              className="h-9 rounded-full px-4 bg-blue-600 hover:bg-blue-700 text-white"
            >
              {exportingFormat === "pdf" ? <Loader2 className="mr-2 size-4 animate-spin" /> : <FileText className="mr-2 size-4" />}
              Export PDF
            </Button>
            <Button
              variant="outline"
              onClick={() => void handleExport("docx")}
              disabled={Boolean(exportingFormat)}
              className="h-9 rounded-full px-4 border-slate-200 text-slate-700 hover:bg-slate-50"
            >
              {exportingFormat === "docx" ? <Loader2 className="mr-2 size-4 animate-spin" /> : <FileText className="mr-2 size-4" />}
              Export DOCX
            </Button>
            <Button
              variant="outline"
              onClick={() => void handleExport("csv")}
              disabled={Boolean(exportingFormat)}
              className="h-9 rounded-full px-4 border-slate-200 text-slate-700 hover:bg-slate-50"
            >
              {exportingFormat === "csv" ? <Loader2 className="mr-2 size-4 animate-spin" /> : <Download className="mr-2 size-4" />}
              Export CSV
            </Button>
            <Button
              variant="outline"
              onClick={() => void handleExport("xlsx")}
              disabled={Boolean(exportingFormat)}
              className="h-9 rounded-full px-4 border-slate-200 text-slate-700 hover:bg-slate-50"
            >
              {exportingFormat === "xlsx" ? <Loader2 className="mr-2 size-4 animate-spin" /> : <FileSpreadsheet className="mr-2 size-4" />}
              Export XLSX
            </Button>
            <Badge variant="secondary" className="ml-auto">
              {reportData ? `Generated for ${reportData.institute_name}` : "No report loaded"}
            </Badge>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200/60 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-6 py-4">
            <h2 className="text-base font-semibold text-slate-900">Placement Data Preview</h2>
          </div>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Roll No</TableHead>
                  <TableHead>Branch</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Offer</TableHead>
                  <TableHead>Pay</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {topPlacements.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="h-24 text-center text-slate-500">
                      {loading ? "Loading report data..." : "No placement rows available for selected filters."}
                    </TableCell>
                  </TableRow>
                ) : (
                  topPlacements.map((row) => (
                    <TableRow key={`${row.student_id}-${row.updated_at}`}>
                      <TableCell>{row.name}</TableCell>
                      <TableCell>{row.roll_no}</TableCell>
                      <TableCell>{row.branch}</TableCell>
                      <TableCell>{row.company_name}</TableCell>
                      <TableCell className="capitalize">{row.offer_type}</TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          min={0}
                          step="0.01"
                          value={payDrafts[row.student_id] ?? ""}
                          onChange={(e) =>
                            setPayDrafts((prev) => ({
                              ...prev,
                              [row.student_id]: e.target.value,
                            }))
                          }
                          placeholder="Enter pay"
                          className="h-8 w-32 rounded-full bg-slate-50 border-transparent px-3 text-sm font-medium text-slate-700 placeholder:text-slate-400"
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => void handleSavePay(row.student_id)}
                          disabled={Boolean(savingPayByStudent[row.student_id])}
                          className="h-8 rounded-full px-3 border-slate-200 text-slate-700 hover:bg-slate-50"
                        >
                          {savingPayByStudent[row.student_id] ? <Loader2 className="size-4 animate-spin" /> : "Save"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </div>
  );
}
