"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { getApiErrorMessage, tpoLogin } from "@/lib/api";
import { getStoredTpoToken, setTpoAuth } from "@/lib/auth-storage";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function TpoLoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("tpo");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (getStoredTpoToken()) {
      router.replace("/tpo/candidates");
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      toast.error("Enter TPO username and password.");
      return;
    }
    setLoading(true);
    try {
      const data = await tpoLogin({ username: username.trim(), password });
      setTpoAuth(data.access_token, data.username);
      toast.success("TPO login successful.");
      router.replace("/tpo/candidates");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>TPO Dashboard Login</CardTitle>
          <CardDescription>Sign in with TPO credentials to access hiring dashboard.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Username</label>
              <Input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                placeholder="tpo"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign in as TPO"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
