"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

import { login, registerAccount, getApiErrorMessage } from "@/lib/api";
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

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    if (!name.trim()) {
      toast.error("Name is required.");
      return;
    }
    setLoading(true);
    try {
      await registerAccount({
        name: name.trim(),
        email: email.trim(),
        password,
        phone: phone.trim(),
      });
      const auth = await login({
        identifier: email.trim(),
        password,
      });
      setAuth(auth.access_token, auth.student_id, auth.email, auth.roll_no);
      toast.success("Account created. Continue to profile setup.");
      router.push("/dashboard");
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        toast.info("Account already exists. Please sign in.");
        router.push(`/login?identifier=${encodeURIComponent(email.trim())}`);
        return;
      }
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Create account</CardTitle>
          <CardDescription>
            Register with basic account details. Academic and profile details
            will be captured in step 2.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="grid gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Name</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Email</label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Phone</label>
              <Input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
                minLength={7}
              />
            </div>
            <div className="flex flex-col gap-3">
              <Button type="submit" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating account…
                  </>
                ) : (
                  "Register and continue"
                )}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                Already registered?{" "}
                <Link href="/login" className="font-medium text-primary underline">
                  Sign in
                </Link>
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
