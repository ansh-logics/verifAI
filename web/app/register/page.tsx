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
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [rollNo, setRollNo] = useState("");
  const [branch, setBranch] = useState("");
  const [cgpa, setCgpa] = useState("");
  const [gender, setGender] = useState<"women" | "men" | "other">("other");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cgpaValue = Number.parseFloat(cgpa);
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    if (!Number.isFinite(cgpaValue) || cgpaValue < 0 || cgpaValue > 10) {
      toast.error("CGPA must be a number between 0 and 10.");
      return;
    }
    setLoading(true);
    try {
      await registerAccount({
        email: email.trim(),
        password,
        phone: phone.trim(),
        roll_no: rollNo.trim().toUpperCase(),
        branch: branch.trim(),
        cgpa: cgpaValue,
        gender,
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
            Register with your core profile fields so JD matching can work
            immediately.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="grid gap-4">
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
            <div className="space-y-2">
              <label className="text-sm font-medium">Roll Number</label>
              <Input
                value={rollNo}
                onChange={(e) => setRollNo(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Branch</label>
              <Input
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">CGPA</label>
              <Input
                type="number"
                inputMode="decimal"
                min={0}
                max={10}
                step="0.01"
                value={cgpa}
                onChange={(e) => setCgpa(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Gender</label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={gender}
                onChange={(e) => setGender(e.target.value as "women" | "men" | "other")}
                required
              >
                <option value="women">Women</option>
                <option value="men">Men</option>
                <option value="other">Other</option>
              </select>
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
