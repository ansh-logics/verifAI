"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { getApiErrorMessage, login } from "@/lib/api";
import { setAuth } from "@/lib/auth-storage";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
  const router = useRouter();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const pre = new URLSearchParams(window.location.search).get("identifier");
    if (pre) setIdentifier(pre);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim() || !password) {
      toast.error("Enter roll number or email and password.");
      return;
    }
    setLoading(true);
    try {
      const data = await login({
        identifier: identifier.trim(),
        password,
      });
      setAuth(data.access_token, data.student_id, data.email, data.roll_no);
      toast.success("Signed in.");
      router.push("/profile");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center bg-[#f8f9fa] p-6 text-slate-900">
      <Link
        href="/"
        className="absolute left-6 top-6 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
      >
        Back to home
      </Link>
      <Card className="w-full max-w-md rounded-3xl border border-slate-200/80 bg-white shadow-xl">
        <CardHeader className="space-y-2">
          <CardTitle className="text-2xl font-semibold tracking-tight">VerifAI</CardTitle>
          <CardDescription>
            Sign in with your roll number or institute email.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Roll number or email</label>
              <Input
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                autoComplete="username"
                placeholder="e.g. AKTU001 or you@institute.edu"
                className="h-11 rounded-xl border-slate-200"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                className="h-11 rounded-xl border-slate-200"
              />
            </div>
            <Button
              type="submit"
              className="h-11 w-full rounded-xl bg-blue-600 text-white hover:bg-blue-700"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in…
                </>
              ) : (
                "Sign in"
              )}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              New here?{" "}
              <Link href="/register" className="font-medium text-primary underline">
                Register
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
