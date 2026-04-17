import React from "react";
import { CheckCircle2, LayoutDashboard, BrainCircuit, FileText } from "lucide-react";

export function Navbar() {
  return (
    <header className="fixed top-2 left-0 right-0 z-50 flex justify-between items-center px-8 h-16 bg-white/60 dark:bg-zinc-900/60 backdrop-blur-3xl rounded-full mt-4 mx-auto w-[92%] max-w-7xl shadow-[0_4px_24px_rgba(0,0,0,0.02)] ring-1 ring-black/[0.04]">
      <div className="flex items-center gap-2">
        <BrainCircuit className="text-purple-600 w-6 h-6" />
        <span className="text-xl font-bold tracking-tighter text-[#1d1d1f] dark:text-zinc-50 font-sans">VerifAI</span>
      </div>
      <nav className="hidden md:flex items-center gap-8">
        <a className="font-sans tracking-tight text-sm font-semibold text-[#1d1d1f] dark:text-purple-400" href="#">Home</a>
        <a className="font-sans tracking-tight text-sm font-semibold text-[#86868b] dark:text-zinc-400 hover:text-[#1d1d1f] transition-colors duration-300" href="#">Case Studies</a>
        <a className="font-sans tracking-tight text-sm font-semibold text-[#86868b] dark:text-zinc-400 hover:text-[#1d1d1f] transition-colors duration-300" href="#">About Us</a>
      </nav>
      <div className="flex items-center gap-4">
        <button className="font-sans tracking-tight text-sm font-semibold text-[#86868b] hover:text-[#1d1d1f] transition-colors duration-300 hidden sm:block">Login</button>
        <button className="bg-[#1d1d1f] text-white font-sans tracking-tight text-sm font-semibold px-6 py-2 rounded-full hover:scale-[1.02] active:scale-[0.98] transition-transform shadow-md">Sign Up</button>
      </div>
    </header>
  );
}

export function Features() {
  return (
    <section className="space-y-16 py-24 px-6 sm:px-12 max-w-7xl mx-auto w-full bg-[#f5f5f7]">
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <h2 className="text-4xl sm:text-5xl font-bold tracking-tighter text-[#1d1d1f]">Intelligence at every step.</h2>
        <p className="text-[#86868b] font-medium text-xl tracking-tight">Designed to bring clarity and precision to the complex placement process.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Feature 1 */}
        <div className="md:col-span-8 bg-white rounded-[2.5rem] p-12 flex flex-col md:flex-row gap-10 items-center ring-1 ring-black/[0.04] shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:-translate-y-1 transition-transform duration-500">
          <div className="flex-1 space-y-4 relative z-10">
            <div className="bg-zinc-50/80 w-12 h-12 rounded-full flex items-center justify-center ring-1 ring-black/5 mb-8">
              <CheckCircle2 className="text-purple-600 w-6 h-6" />
            </div>
            <h3 className="text-2xl font-bold tracking-tight text-[#1d1d1f]">Verified Profiles</h3>
            <p className="text-[#86868b] text-base leading-relaxed font-medium">We cross-reference institutional records, GitHub repositories, and assessment scores to ensure every claim on a resume is authentic before it reaches recruiters.</p>
          </div>
          <div className="flex-1 w-full bg-white rounded-3xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.06)] ring-1 ring-black/[0.04] relative z-10 hover:scale-[1.02] transition-transform duration-500">
            <div className="space-y-4">
              {/* Profile Card Header */}
              <div className="flex items-center justify-between border-b border-zinc-100 pb-4">
                 <div className="flex items-center gap-4">
                   <div className="w-12 h-12 bg-indigo-50/50 rounded-full flex items-center justify-center text-indigo-700 font-bold text-lg ring-1 ring-indigo-100">AB</div>
                   <div>
                     <div className="font-bold tracking-tight text-[#1d1d1f] text-sm">Ansh Bhatt</div>
                     <div className="text-xs text-[#86868b] font-medium mt-0.5">B.Tech Computer Science</div>
                   </div>
                 </div>
                 <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider bg-green-50 text-green-700 px-3 py-1.5 rounded-full ring-1 ring-green-100"><CheckCircle2 className="w-3 h-3"/> Verified</span>
              </div>
              {/* Profile Stats */}
              <div className="grid grid-cols-2 gap-3 pt-1">
                 <div className="bg-zinc-50/50 rounded-2xl p-4 ring-1 ring-black/[0.03]">
                    <div className="text-xs text-[#86868b] font-semibold mb-1">Academic CGPA</div>
                    <div className="text-xl font-bold tracking-tight text-[#1d1d1f]">9.42</div>
                 </div>
                 <div className="bg-zinc-50/50 rounded-2xl p-4 ring-1 ring-black/[0.03]">
                    <div className="text-xs text-[#86868b] font-semibold mb-1">GitHub Repos</div>
                    <div className="text-xl font-bold tracking-tight text-[#1d1d1f]">42 verified</div>
                 </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Feature 2 */}
        <div className="md:col-span-4 bg-[#1d1d1f] rounded-[2.5rem] p-12 text-white flex flex-col justify-between relative overflow-hidden ring-1 ring-black/[0.04] shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:-translate-y-1 transition-transform duration-500">
          <div className="relative z-10 space-y-4 mb-16">
            <div className="bg-white/10 w-12 h-12 rounded-full flex items-center justify-center backdrop-blur-md mb-8 ring-1 ring-white/10">
              <BrainCircuit className="text-white w-6 h-6" />
            </div>
            <h3 className="text-2xl font-bold tracking-tight">AI Matching</h3>
            <p className="text-[#86868b] text-base leading-relaxed font-medium">Semantic matching goes beyond keywords to find true skill alignment.</p>
          </div>
          <div className="relative z-10 bg-white/5 backdrop-blur-3xl rounded-3xl p-6 ring-1 ring-white/10 flex justify-between items-end hover:scale-[1.02] transition-transform duration-500">
             <div>
               <div className="text-[11px] text-white/50 uppercase tracking-widest mb-1.5 font-bold">Match Score</div>
               <div className="text-5xl font-bold tracking-tighter">94%</div>
             </div>
          </div>
        </div>

        {/* Feature 3 */}
        <div className="md:col-span-12 bg-white rounded-[2.5rem] p-12 ring-1 ring-black/[0.04] shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:-translate-y-1 transition-transform duration-500">
           <div className="flex flex-col md:flex-row gap-16 items-center">
             <div className="flex-1 space-y-4">
               <div className="bg-zinc-50 w-12 h-12 rounded-full flex items-center justify-center ring-1 ring-black/5 mb-8">
                 <LayoutDashboard className="text-purple-600 w-6 h-6" />
               </div>
               <h3 className="text-2xl font-bold tracking-tight text-[#1d1d1f]">TPO Dashboard</h3>
               <p className="text-[#86868b] text-base leading-relaxed font-medium max-w-lg">A centralized command center for Training and Placement Officers. Track overall campus performance, upcoming drives, and student readiness metrics at a glance.</p>
               <button className="mt-6 bg-white text-[#1d1d1f] px-8 py-3 rounded-full font-semibold ring-1 ring-black/[0.06] shadow-[0_4px_12px_rgba(0,0,0,0.02)] hover:bg-zinc-50 hover:scale-[1.02] active:scale-[0.98] transition-transform duration-300">
                 View Dashboard
               </button>
             </div>
             <div className="flex-[1.5] w-full bg-white rounded-3xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.06)] ring-1 ring-black/[0.04] overflow-hidden relative hover:scale-[1.02] transition-transform duration-500">
               <div className="flex justify-between items-center mb-6">
                 <h4 className="font-bold tracking-tight text-[#1d1d1f] text-base">Active Campus Drives</h4>
                 <div className="text-[11px] font-bold text-[#86868b] bg-zinc-50 border border-zinc-100 px-3 py-1.5 rounded-md">2024 BATCH</div>
               </div>
               
               <div className="flex gap-4 mb-6">
                 {/* Stat 1 */}
                 <div className="flex-1 bg-purple-50/30 rounded-2xl p-4 ring-1 ring-purple-100">
                    <div className="text-[11px] text-purple-600 font-bold mb-1 uppercase tracking-widest">Eligible</div>
                    <div className="text-3xl font-bold tracking-tighter text-purple-900">425</div>
                 </div>
                 {/* Stat 2 */}
                 <div className="flex-1 bg-zinc-50/50 rounded-2xl p-4 ring-1 ring-black/[0.03]">
                    <div className="text-[11px] text-[#86868b] font-bold mb-1 uppercase tracking-widest">Placed</div>
                    <div className="text-3xl font-bold tracking-tighter text-[#1d1d1f]">284</div>
                 </div>
                 {/* Stat 3 */}
                 <div className="flex-1 bg-zinc-50/50 rounded-2xl p-4 ring-1 ring-black/[0.03]">
                    <div className="text-[11px] text-[#86868b] font-bold mb-1 uppercase tracking-widest">Average</div>
                    <div className="text-3xl font-bold tracking-tighter text-[#1d1d1f]">14LPA</div>
                 </div>
               </div>
               
               {/* Trend Chart Mock */}
               <div className="w-full h-[80px] bg-zinc-50/50 rounded-2xl ring-1 ring-black/[0.03] flex items-end px-4 py-3 gap-2 opacity-90">
                  <div className="w-full bg-indigo-100 rounded-t border-t border-indigo-200" style={{height: "40%"}}></div>
                  <div className="w-full bg-indigo-200 rounded-t border-t border-indigo-300" style={{height: "60%"}}></div>
                  <div className="w-full bg-indigo-300 rounded-t border-t border-indigo-400" style={{height: "30%"}}></div>
                  <div className="w-full bg-purple-500 rounded-t-lg relative shadow-[0_4px_20px_rgba(139,92,246,0.25)] shadow-purple-500" style={{height: "80%"}}>
                     <div className="absolute -top-7 left-1/2 -translate-x-1/2 text-[10px] font-bold tracking-wide text-purple-600 bg-white ring-1 ring-purple-100 px-2 py-1 rounded-md shadow-sm">Peak</div>
                  </div>
                  <div className="w-full bg-indigo-200 rounded-t border-t border-indigo-300" style={{height: "50%"}}></div>
                  <div className="w-full bg-indigo-300 rounded-t border-t border-indigo-400" style={{height: "90%"}}></div>
                  <div className="w-full bg-indigo-400 rounded-t border-t border-indigo-500" style={{height: "100%"}}></div>
               </div>
             </div>
           </div>
        </div>
      </div>
    </section>
  );
}

export function LiveUseCase() {
  return (
    <section className="max-w-6xl mx-auto w-full my-12 bg-white rounded-[3rem] p-16 ring-1 ring-black/[0.04] shadow-[0_8px_30px_rgb(0,0,0,0.04)] relative overflow-hidden">
      <div className="text-center mb-16 relative z-10">
        <span className="text-[#86868b] font-bold tracking-widest uppercase text-xs mb-3 block">Live Demo</span>
        <h2 className="text-4xl sm:text-5xl font-bold tracking-tighter text-[#1d1d1f]">See it in action.</h2>
      </div>
      
      <div className="flex flex-col gap-6 max-w-4xl mx-auto relative z-10">
        <div className="bg-zinc-50/50 rounded-3xl p-8 flex items-start gap-6 ring-1 ring-black/[0.03]">
           <div className="bg-white w-12 h-12 rounded-full flex items-center justify-center shrink-0 ring-1 ring-black/5 shadow-sm">
             <FileText className="text-zinc-500 w-5 h-5" />
           </div>
           <div className="space-y-3 w-full mt-1">
             <div className="text-sm font-bold tracking-tight text-[#1d1d1f]">Recruiter Prompt</div>
             <div className="bg-white rounded-2xl p-5 text-[#86868b] font-mono text-[13px] leading-relaxed ring-1 ring-black/[0.04] shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
               "Find top 5 students for a React Frontend Intern role. Must have &gt;8 CGPA, completed at least one full-stack project, and have an active GitHub. Rank by technical assessment score."
             </div>
           </div>
        </div>

        <div className="bg-white rounded-3xl p-8 flex items-start gap-6 ring-1 ring-black/[0.04] shadow-[0_4px_24px_rgba(0,0,0,0.04)] hover:-translate-y-1 transition-transform duration-500">
           <div className="bg-gradient-to-r from-purple-600 to-indigo-600 w-12 h-12 rounded-full flex items-center justify-center shrink-0 shadow-md shadow-purple-500/20">
             <BrainCircuit className="text-white w-6 h-6" />
           </div>
           <div className="space-y-4 w-full mt-1">
             <div className="text-sm font-bold tracking-tight text-[#1d1d1f]">VerifAI Engine Output</div>
             <p className="text-sm text-[#86868b] font-medium">Analyzed 450 profiles. Found 12 matches. Here are the top ranked candidates based on your criteria:</p>
             
             <div className="space-y-3 pt-2">
               <div className="bg-zinc-50/80 rounded-2xl p-4 flex justify-between items-center ring-1 ring-black/[0.03] hover:scale-[1.01] transition-transform">
                 <div className="flex items-center gap-4">
                   <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center text-xs font-bold text-[#1d1d1f] ring-1 ring-black/5 shadow-sm">1</div>
                   <div>
                     <div className="font-bold tracking-tight text-[#1d1d1f] text-sm">Sarah Jenkins</div>
                     <div className="text-xs text-[#86868b] font-medium mt-0.5">CS &bull; 8.9 CGPA &bull; 3 React Projects</div>
                   </div>
                 </div>
                 <div className="bg-green-50 text-green-700 text-xs px-3 py-1.5 rounded-full font-bold tracking-tight ring-1 ring-green-100">98% Match</div>
               </div>
             </div>
           </div>
        </div>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="w-full py-20 px-12 flex flex-col md:flex-row justify-between items-center max-w-7xl mx-auto bg-[#f5f5f7] text-purple-600 font-sans text-xs uppercase tracking-widest rounded-t-[3rem] opacity-90 hover:opacity-100 border-t border-zinc-200">
      <div className="flex items-center gap-2 mb-8 md:flex-row md:mb-0">
        <BrainCircuit className="text-purple-600 w-6 h-6" />
        <span className="text-lg font-bold text-zinc-900 tracking-normal normal-case">VerifAI</span>
      </div>
      <div className="flex flex-wrap justify-center gap-8 mb-8 md:mb-0 font-semibold">
        <a className="text-zinc-500 hover:text-purple-600 transition-colors" href="#">Product</a>
        <a className="text-zinc-500 hover:text-purple-600 transition-colors" href="#">Intelligence</a>
        <a className="text-zinc-500 hover:text-purple-600 transition-colors" href="#">Privacy</a>
        <a className="text-zinc-500 hover:text-purple-600 transition-colors" href="#">Terms</a>
      </div>
      <div className="text-zinc-400 normal-case tracking-normal text-sm font-medium">
         © 2024 VerifAI Intelligence. All rights reserved.
      </div>
    </footer>
  );
}
