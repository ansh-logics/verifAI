"use client";

import { ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "./sidebar";
import { getStoredTpoToken } from "@/lib/auth-storage";

export default function TpoLayout({ children }: { children: ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    const token = getStoredTpoToken();
    if (!token) {
      router.replace("/tpo/login");
    }
  }, [router]);

  return (
    <div className="flex h-screen w-full bg-[#0f111a] text-white font-sans selection:bg-blue-500/30 overflow-hidden">
      <Sidebar />
      <main className="flex-1 bg-[#f8f9fa] text-slate-900 rounded-[2rem] flex flex-col relative z-50 shadow-[-20px_0_50px_rgba(0,0,0,0.7)] ring-1 ring-black/5 my-2.5 mr-2.5 overflow-hidden">
        {children}
      </main>
    </div>
  );
}
