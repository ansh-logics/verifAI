"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Loader2, Users } from "lucide-react";
import axios from "axios";

import { listTpoGroups, getApiErrorMessage, deleteTpoGroup } from "@/lib/api";
import { clearTpoAuth } from "@/lib/auth-storage";
import type { TpoGroup } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function PlacementGroupsPage() {
  const router = useRouter();
  const [groups, setGroups] = useState<TpoGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    void listTpoGroups()
      .then((data) => {
        if (!mounted) return;
        setGroups(data);
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
    () =>
      [...groups].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      ),
    [groups],
  );

  const handleDelete = async (groupId: number) => {
    const ok = window.confirm("Delete this placement group?");
    if (!ok) return;
    try {
      const res = await deleteTpoGroup(groupId);
      setGroups((prev) => prev.filter((g) => g.id !== groupId));
      toast.success(res.message);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 rounded-[2rem] w-full h-full">
      <div className="mx-auto w-full max-w-7xl space-y-6">
        <section>
          <h1 className="text-3xl font-bold text-slate-900">Placement Groups</h1>
          <p className="text-slate-600">
            Review all analysis groups and open any group for detailed member actions.
          </p>
        </section>

        {loading ? (
          <div className="h-48 flex items-center justify-center text-slate-500">
            <Loader2 className="h-5 w-5 mr-2 animate-spin" />
            Loading groups...
          </div>
        ) : error ? (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="py-6 text-red-700">{error}</CardContent>
          </Card>
        ) : sortedGroups.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="py-12 text-center text-slate-500">
              No groups created yet. Create one from the candidates page.
            </CardContent>
          </Card>
        ) : (
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {sortedGroups.map((group) => (
              <Link key={group.id} href={`/tpo/placement-groups/${group.id}`}>
                <Card className="h-full hover:shadow-md transition-shadow border-slate-200/70">
                  <CardHeader className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <CardTitle className="text-lg">{group.title}</CardTitle>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="gap-1">
                          <Users className="h-3.5 w-3.5" />
                          {group.members.length}
                        </Badge>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            void handleDelete(group.id);
                          }}
                        >
                          Delete
                        </Button>
                      </div>
                    </div>
                    <p className="text-xs text-slate-500">
                      Created by {group.created_by} on{" "}
                      {new Date(group.created_at).toLocaleDateString()}
                    </p>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-slate-600 line-clamp-3">
                      {group.jd_summary?.trim() || "No JD summary captured for this group."}
                    </p>
                    <p className="mt-2 text-xs text-slate-500">
                      Company: {group.company_name || "Not captured"} · Role: {group.role_type || "Not captured"}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      Pay/Stipend: {group.pay_or_stipend || "Not captured"} · Duration: {group.duration || "Not captured"}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      Bond: {group.bond_details || "Not captured"}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </section>
        )}
      </div>
    </div>
  );
}
