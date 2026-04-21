"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Users, BarChart3, Settings, Search, FolderKanban } from "lucide-react";
import { useRouter } from "next/navigation";
import { clearTpoAuth, getStoredTpoUsername } from "@/lib/auth-storage";
import { cn } from "@/lib/utils";

const navItems = [
  { name: "Overview", href: "/tpo", icon: Home },
  { name: "Search", href: "/tpo/search", icon: Search },
  { name: "Candidates", href: "/tpo/candidates", icon: Users },
  { name: "Placement Groups", href: "/tpo/placement-groups", icon: FolderKanban },
  { name: "Reports", href: "/tpo/reports", icon: BarChart3 },
  { name: "Settings", href: "/tpo/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const username = getStoredTpoUsername();

  function signOut() {
    clearTpoAuth();
    router.replace("/tpo/login");
  }

  return (
    <aside className="w-64 flex-shrink-0 p-4 border-r border-white/5 flex flex-col gap-6 relative z-0">
      <div className="absolute inset-y-0 right-0 w-32 bg-gradient-to-l from-white/[0.06] to-transparent pointer-events-none" />
      <div className="flex items-center gap-3 px-2 mt-2 relative z-10">
        <div className="size-8 rounded-xl bg-blue-600 flex items-center justify-center font-bold shadow-lg shadow-blue-600/20 text-white">V</div>
        <span className="font-semibold text-lg tracking-tight text-white">VerifAI</span>
      </div>

      <nav className="flex flex-col gap-1 relative z-10 mt-4">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/tpo" && pathname.startsWith(`${item.href}/`));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-600/10 text-blue-400"
                  : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
              )}
            >
              <item.icon className={cn("size-5", isActive ? "text-blue-400" : "text-slate-500")} />
              {item.name}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto relative z-10 px-2 space-y-3">
        <div className="text-xs text-slate-400">
          Signed in as <span className="text-slate-200 font-medium">{username || "tpo"}</span>
        </div>
        <button
          onClick={signOut}
          className="w-full rounded-lg border border-white/10 px-3 py-2 text-sm text-slate-300 hover:bg-white/5 hover:text-white transition"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
