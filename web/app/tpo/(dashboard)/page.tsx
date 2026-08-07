"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { AlertCircle, ArrowRight, CheckCircle2, Clock3, FolderKanban, Loader2, Users } from "lucide-react";

import { getApiErrorMessage, getTpoOverview, listTpoGroups } from "@/lib/api";
import { clearTpoAuth } from "@/lib/auth-storage";
import type { TpoGroup, TpoOverviewResponse } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type QueueItem = {
  id: string;
  title: string;
  detail: string;
  actionLabel: string;
  onClick: () => void;
};

export default function TpoDashboardRootPage() {
  const router = useRouter();
  const [overview, setOverview] = useState<TpoOverviewResponse | null>(null);
  const [groups, setGroups] = useState<TpoGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    Promise.all([getTpoOverview(), listTpoGroups()])
      .then(([overviewData, groupsData]) => {
        if (!mounted) return;
        setOverview(overviewData);
        setGroups(groupsData);
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
  }, [router]);

  const sortedGroups = useMemo(
    () => [...groups].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
    [groups],
  );

  const recentGroups = sortedGroups.slice(0, 5);

  const queueItems = useMemo<QueueItem[]>(() => {
    const items: QueueItem[] = [];

    const staleGroup = sortedGroups.find((group) => {
      const createdAt = new Date(group.created_at).getTime();
      const ageDays = (Date.now() - createdAt) / (1000 * 60 * 60 * 24);
      const hasPlaced = group.members.some((member) => member.placement?.is_active);
      return ageDays >= 7 && !hasPlaced;
    });
    if (staleGroup) {
      items.push({
        id: `stale-${staleGroup.id}`,
        title: "Stale group needs follow-up",
        detail: `${staleGroup.title} has no active placement updates in 7+ days.`,
        actionLabel: "Open Group",
        onClick: () => router.push(`/tpo/placement-groups/${staleGroup.id}`),
      });
    }

    items.push({
      id: "manual-review",
      title: "Review manual additions",
      detail: "Use AI Search to add candidates not captured by JD shortlist.",
      actionLabel: "Go to AI Search",
      onClick: () => router.push("/tpo/ai-search"),
    });

    if ((overview?.unplaced_eligible_students ?? 0) > 0) {
      items.push({
        id: "eligible-pool",
        title: "Unplaced pool available",
        detail: `${overview?.unplaced_eligible_students ?? 0} eligible students can be targeted in next drive.`,
        actionLabel: "Run AI Search",
        onClick: () => router.push("/tpo/ai-search"),
      });
    }

    if ((overview?.recent_placements.length ?? 0) > 0) {
      items.push({
        id: "placement-updates",
        title: "Recent placements recorded",
        detail: "Verify pay/offer details are complete for recent updates.",
        actionLabel: "View Groups",
        onClick: () => router.push("/tpo/placement-groups"),
      });
    }

    return items.slice(0, 4);
  }, [overview, sortedGroups, router]);

  return (
    <div className="flex-1 overflow-y-auto p-8 rounded-[2rem] w-full h-full pb-10">
      <div className="mx-auto w-full max-w-7xl space-y-8">
        <section className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Overview</h1>
          <p className="text-sm text-slate-600">Operations hub for all-time placement workflow monitoring and actions.</p>
        </section>

        {loading ? (
          <div className="h-52 flex items-center justify-center text-slate-500">
            <Loader2 className="size-5 mr-2 animate-spin" />
            Loading overview...
          </div>
        ) : error ? (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="py-6 flex items-center gap-2 text-red-700">
              <AlertCircle className="size-5" />
              {error}
            </CardContent>
          </Card>
        ) : (
          <>
            <section className="grid gap-4 md:grid-cols-4">
              <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
                <CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between">
                  <CardTitle className="text-sm font-medium text-slate-500">Total Students</CardTitle>
                  <Users className="size-4 text-slate-400" />
                </CardHeader>
                <CardContent className="px-5 pb-5">
                  <div className="text-4xl font-semibold tracking-tight text-slate-900">{overview?.total_students ?? 0}</div>
                </CardContent>
              </Card>
              <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
                <CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between">
                  <CardTitle className="text-sm font-medium text-slate-500">Unplaced Eligible</CardTitle>
                  <Clock3 className="size-4 text-slate-400" />
                </CardHeader>
                <CardContent className="px-5 pb-5">
                  <div className="text-4xl font-semibold tracking-tight text-slate-900">{overview?.unplaced_eligible_students ?? 0}</div>
                </CardContent>
              </Card>
              <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
                <CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between">
                  <CardTitle className="text-sm font-medium text-slate-500">Active Groups</CardTitle>
                  <FolderKanban className="size-4 text-slate-400" />
                </CardHeader>
                <CardContent className="px-5 pb-5">
                  <div className="text-4xl font-semibold tracking-tight text-slate-900">{overview?.active_groups ?? 0}</div>
                </CardContent>
              </Card>
              <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
                <CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between">
                  <CardTitle className="text-sm font-medium text-slate-500">Placed Students</CardTitle>
                  <CheckCircle2 className="size-4 text-slate-400" />
                </CardHeader>
                <CardContent className="px-5 pb-5">
                  <div className="text-4xl font-semibold tracking-tight text-slate-900">{overview?.placed_students ?? 0}</div>
                </CardContent>
              </Card>
            </section>

            <section className="grid gap-6 lg:grid-cols-3">
              <Card className="lg:col-span-2 bg-white rounded-3xl border border-slate-200/60 shadow-sm">
                <CardHeader className="pb-3 border-b border-slate-100">
                  <CardTitle className="text-base text-slate-900">Action Queue</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {queueItems.length === 0 ? (
                    <div className="text-sm text-slate-500 py-4">No pending actions. You are up to date.</div>
                  ) : (
                    queueItems.map((item) => (
                      <div key={item.id} className="rounded-2xl border border-slate-200/80 bg-slate-50/60 px-4 py-3 flex items-center justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-slate-900">{item.title}</p>
                          <p className="text-xs text-slate-600">{item.detail}</p>
                        </div>
                        <Button size="sm" variant="outline" onClick={item.onClick} className="shrink-0 h-8 rounded-full border-slate-200 text-slate-700 hover:bg-white">
                          {item.actionLabel}
                        </Button>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

              <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
                <CardHeader className="pb-3 border-b border-slate-100">
                  <CardTitle className="text-base text-slate-900">Workflow Shortcuts</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <Button className="w-full justify-between rounded-full h-9 px-4 bg-blue-600 hover:bg-blue-700 text-white" onClick={() => router.push("/tpo/ai-search")}>
                    Run AI Search <ArrowRight className="size-4" />
                  </Button>
                  <Button variant="outline" className="w-full justify-between rounded-full h-9 px-4 border-slate-200 text-slate-700 hover:bg-slate-50" onClick={() => router.push("/tpo/ai-search")}>
                    Create Placement Group <ArrowRight className="size-4" />
                  </Button>
                  <Button variant="outline" className="w-full justify-between rounded-full h-9 px-4 border-slate-200 text-slate-700 hover:bg-slate-50" onClick={() => router.push("/tpo/placement-groups")}>
                    View Placement Groups <ArrowRight className="size-4" />
                  </Button>
                  <Button variant="outline" className="w-full justify-between rounded-full h-9 px-4 border-slate-200 text-slate-700 hover:bg-slate-50" onClick={() => router.push("/tpo/reports")}>
                    Go to Reports <ArrowRight className="size-4" />
                  </Button>
                </CardContent>
              </Card>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
                <CardHeader className="pb-3 border-b border-slate-100">
                  <CardTitle className="text-base text-slate-900">Recent Placement Groups</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {recentGroups.length === 0 ? (
                    <div className="text-sm text-slate-500 py-2">No groups yet. Create one from AI Search.</div>
                  ) : (
                    recentGroups.map((group) => (
                      <button
                        key={group.id}
                        className="w-full rounded-2xl border border-slate-200/80 bg-slate-50/60 px-4 py-3 text-left hover:bg-slate-50 transition-colors"
                        onClick={() => router.push(`/tpo/placement-groups/${group.id}`)}
                      >
                        <p className="text-sm font-semibold text-slate-900">{group.title}</p>
                        <p className="text-xs text-slate-600">{group.members.length} members · {new Date(group.created_at).toLocaleDateString()}</p>
                      </button>
                    ))
                  )}
                </CardContent>
              </Card>

              <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
                <CardHeader className="pb-3 border-b border-slate-100">
                  <CardTitle className="text-base text-slate-900">Recent Placements</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {(overview?.recent_placements.length ?? 0) === 0 ? (
                    <div className="text-sm text-slate-500 py-2">No placement records yet.</div>
                  ) : (
                    overview!.recent_placements.map((placement) => (
                      <div key={`${placement.student_id}-${placement.updated_at}`} className="rounded-2xl border border-slate-200/80 bg-slate-50/60 px-4 py-3">
                        <p className="text-sm font-semibold text-slate-900">{placement.name}</p>
                        <p className="text-xs text-slate-600">{placement.company_name} · {placement.offer_type}</p>
                        <p className="text-xs text-slate-500">
                          {placement.pay_amount !== null ? `Pay ${placement.pay_amount}` : "Pay not captured"} ·{" "}
                          {new Date(placement.updated_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
