"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { Bell, Mail, ShieldCheck, UserCog } from "lucide-react";
import { toast } from "sonner";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { changeTpoPassword, getApiErrorMessage, getTpoSettings, updateTpoSettings } from "@/lib/api";
import { clearTpoAuth } from "@/lib/auth-storage";
import { useRouter } from "next/navigation";

export default function TpoSettingsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);

  const [displayName, setDisplayName] = useState("");
  const [contactNumber, setContactNumber] = useState("");
  const [instituteName, setInstituteName] = useState("");
  const [senderName, setSenderName] = useState("");
  const [replyToEmail, setReplyToEmail] = useState("");
  const [defaultTimezone, setDefaultTimezone] = useState("");
  const [staleGroupReminderEnabled, setStaleGroupReminderEnabled] = useState(true);
  const [dailyQueueSummaryEnabled, setDailyQueueSummaryEnabled] = useState(true);
  const [placementUpdateConfirmationEnabled, setPlacementUpdateConfirmationEnabled] = useState(true);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  useEffect(() => {
    let mounted = true;
    void getTpoSettings()
      .then((data) => {
        if (!mounted) return;
        setDisplayName(data.display_name ?? "");
        setContactNumber(data.contact_number ?? "");
        setInstituteName(data.institute_name ?? "");
        setSenderName(data.sender_name ?? "");
        setReplyToEmail(data.reply_to_email ?? "");
        setDefaultTimezone(data.default_timezone ?? "");
        setStaleGroupReminderEnabled(data.stale_group_reminder_enabled);
        setDailyQueueSummaryEnabled(data.daily_queue_summary_enabled);
        setPlacementUpdateConfirmationEnabled(data.placement_update_confirmation_enabled);
      })
      .catch((err) => {
        if (!mounted) return;
        if (axios.isAxiosError(err) && [401, 403].includes(err.response?.status ?? 0)) {
          clearTpoAuth();
          router.replace("/tpo/login");
          return;
        }
        toast.error(getApiErrorMessage(err));
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [router]);

  async function handleSaveSettings() {
    setSaving(true);
    try {
      await updateTpoSettings({
        display_name: displayName.trim() || null,
        contact_number: contactNumber.trim() || null,
        institute_name: instituteName.trim() || null,
        sender_name: senderName.trim() || null,
        reply_to_email: replyToEmail.trim() || null,
        default_timezone: defaultTimezone.trim() || null,
        stale_group_reminder_enabled: staleGroupReminderEnabled,
        daily_queue_summary_enabled: dailyQueueSummaryEnabled,
        placement_update_confirmation_enabled: placementUpdateConfirmationEnabled,
      });
      toast.success("Settings saved.");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleChangePassword() {
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error("Fill all password fields.");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("New password and confirm password do not match.");
      return;
    }
    setChangingPassword(true);
    try {
      await changeTpoPassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      toast.success("Password updated.");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setChangingPassword(false);
    }
  }

  function handleReset() {
    setLoading(true);
    void getTpoSettings()
      .then((data) => {
        setDisplayName(data.display_name ?? "");
        setContactNumber(data.contact_number ?? "");
        setInstituteName(data.institute_name ?? "");
        setSenderName(data.sender_name ?? "");
        setReplyToEmail(data.reply_to_email ?? "");
        setDefaultTimezone(data.default_timezone ?? "");
        setStaleGroupReminderEnabled(data.stale_group_reminder_enabled);
        setDailyQueueSummaryEnabled(data.daily_queue_summary_enabled);
        setPlacementUpdateConfirmationEnabled(data.placement_update_confirmation_enabled);
      })
      .catch((err) => {
        toast.error(getApiErrorMessage(err));
      })
      .finally(() => setLoading(false));
  }

  return (
    <div className="flex-1 overflow-y-auto p-8 rounded-[2rem] w-full h-full pb-10">
      <div className="mx-auto w-full max-w-7xl space-y-8">
        <section className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Settings</h1>
          <p className="text-sm text-slate-600">Manage dashboard preferences, communication defaults, and access controls.</p>
        </section>

        <section className="grid gap-4 md:grid-cols-4">
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm md:col-span-1">
            <CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium text-slate-500">Profile</CardTitle>
              <UserCog className="size-4 text-slate-400" />
            </CardHeader>
            <CardContent className="px-5 pb-5 text-sm text-slate-700">TPO account defaults</CardContent>
          </Card>
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm md:col-span-1">
            <CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium text-slate-500">Mail</CardTitle>
              <Mail className="size-4 text-slate-400" />
            </CardHeader>
            <CardContent className="px-5 pb-5 text-sm text-slate-700">Email sender defaults</CardContent>
          </Card>
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm md:col-span-1">
            <CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium text-slate-500">Notifications</CardTitle>
              <Bell className="size-4 text-slate-400" />
            </CardHeader>
            <CardContent className="px-5 pb-5 text-sm text-slate-700">Alerts and reminders</CardContent>
          </Card>
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm md:col-span-1">
            <CardHeader className="pb-2 pt-5 px-5 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium text-slate-500">Access</CardTitle>
              <ShieldCheck className="size-4 text-slate-400" />
            </CardHeader>
            <CardContent className="px-5 pb-5 text-sm text-slate-700">Security and permissions</CardContent>
          </Card>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">TPO Profile Defaults</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-5">
              <Input placeholder="Display name" value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="h-10 rounded-xl border-slate-200" disabled={loading || saving} />
              <Input placeholder="Contact number" value={contactNumber} onChange={(e) => setContactNumber(e.target.value)} className="h-10 rounded-xl border-slate-200" disabled={loading || saving} />
              <Input placeholder="Institute name" value={instituteName} onChange={(e) => setInstituteName(e.target.value)} className="h-10 rounded-xl border-slate-200" disabled={loading || saving} />
            </CardContent>
          </Card>

          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Mail Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-5">
              <Input placeholder="Sender name (e.g., TPO Cell)" value={senderName} onChange={(e) => setSenderName(e.target.value)} className="h-10 rounded-xl border-slate-200" disabled={loading || saving} />
              <Input placeholder="Reply-to email" value={replyToEmail} onChange={(e) => setReplyToEmail(e.target.value)} className="h-10 rounded-xl border-slate-200" disabled={loading || saving} />
              <Input placeholder="Default interview timezone (e.g., Asia/Kolkata)" value={defaultTimezone} onChange={(e) => setDefaultTimezone(e.target.value)} className="h-10 rounded-xl border-slate-200" disabled={loading || saving} />
              <div className="rounded-2xl border border-slate-200/80 bg-slate-50/60 px-4 py-3 text-xs text-slate-600">
                Gmail SMTP/app-password and provider credentials are managed via backend environment configuration.
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Notification Preferences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-5">
              <label className="flex items-center justify-between rounded-2xl border border-slate-200/80 bg-slate-50/60 px-4 py-3 text-sm text-slate-700">
                Group stale reminder (7+ days)
                <input type="checkbox" checked={staleGroupReminderEnabled} onChange={(e) => setStaleGroupReminderEnabled(e.target.checked)} className="size-4 accent-blue-600" disabled={loading || saving} />
              </label>
              <label className="flex items-center justify-between rounded-2xl border border-slate-200/80 bg-slate-50/60 px-4 py-3 text-sm text-slate-700">
                Daily queue summary
                <input type="checkbox" checked={dailyQueueSummaryEnabled} onChange={(e) => setDailyQueueSummaryEnabled(e.target.checked)} className="size-4 accent-blue-600" disabled={loading || saving} />
              </label>
              <label className="flex items-center justify-between rounded-2xl border border-slate-200/80 bg-slate-50/60 px-4 py-3 text-sm text-slate-700">
                Placement update confirmations
                <input type="checkbox" checked={placementUpdateConfirmationEnabled} onChange={(e) => setPlacementUpdateConfirmationEnabled(e.target.checked)} className="size-4 accent-blue-600" disabled={loading || saving} />
              </label>
            </CardContent>
          </Card>

          <Card className="bg-white rounded-3xl border border-slate-200/60 shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Access & Security</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-5">
              <Input placeholder="Current password" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} className="h-10 rounded-xl border-slate-200" disabled={loading || changingPassword} />
              <Input placeholder="New password" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="h-10 rounded-xl border-slate-200" disabled={loading || changingPassword} />
              <Input placeholder="Confirm new password" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="h-10 rounded-xl border-slate-200" disabled={loading || changingPassword} />
              <Button className="h-9 rounded-full px-5 bg-blue-600 hover:bg-blue-700 text-white" onClick={() => void handleChangePassword()} disabled={loading || changingPassword}>
                {changingPassword ? "Updating..." : "Update Password"}
              </Button>
              <div className="rounded-2xl border border-slate-200/80 bg-slate-50/60 px-4 py-3 text-xs text-slate-600">
                API key fallback and token policy are enforced server-side for TPO endpoints.
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="flex items-center justify-end gap-2">
          <Button variant="outline" className="h-9 rounded-full px-4 border-slate-200 text-slate-700 hover:bg-slate-50" onClick={handleReset} disabled={loading || saving}>
            Reset
          </Button>
          <Button className="h-9 rounded-full px-5 bg-blue-600 hover:bg-blue-700 text-white" onClick={() => void handleSaveSettings()} disabled={loading || saving}>
            {saving ? "Saving..." : "Save Settings"}
          </Button>
        </section>
      </div>
    </div>
  );
}
