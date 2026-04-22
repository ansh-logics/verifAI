"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence, LayoutGroup } from "framer-motion";
import { Search, Upload, ArrowRight, Sparkles, CheckCircle2, FileText, BrainCircuit, ListChecks } from "lucide-react";

const TYPING_TEXT = "Need 5 Frontend interns with React, HTML, CSS above 7 CGPA and no backlogs";

const ANALYZING_PHRASES = [
  "Parsing JD...",
  "Checking Profiles...",
  "Matching Skills...",
  "Ranking Students...",
  "Finalizing Results..."
];

export function Hero() {
  const [phase, setPhase] = useState(0); 
  const [typedText, setTypedText] = useState("");
  const [analyzingStep, setAnalyzingStep] = useState(0);
  const [mousePosition, setMousePosition] = useState({ x: -1000, y: -1000 });

  const handleMouseMove = (e: React.MouseEvent) => {
    setMousePosition({ x: e.clientX, y: e.clientY });
  };

  useEffect(() => {
    let active = true;

    const runSequence = async () => {
      setPhase(0);
      setTypedText("");
      setAnalyzingStep(0);
      
      await new Promise(r => setTimeout(r, 1200));
      if (!active) return;
      
      // Typing Effect
      setPhase(1);
      for (let i = 0; i <= TYPING_TEXT.length; i++) {
        if (!active) return;
        setTypedText(TYPING_TEXT.substring(0, i));
        await new Promise(r => setTimeout(r, 45)); 
      }
      
      await new Promise(r => setTimeout(r, 600)); 
      if (!active) return;
      
      // Auto Click
      setPhase(2);
      await new Promise(r => setTimeout(r, 400)); 
      if (!active) return;
      
      // Analyzing State
      setPhase(3);
      for(let i=0; i<ANALYZING_PHRASES.length; i++) {
        if (!active) return;
        setAnalyzingStep(i);
        await new Promise(r => setTimeout(r, 800));
      }
      
      if (!active) return;
      // Workflow Reveal
      setPhase(4);
    };

    runSequence();
    return () => { active = false; };
  }, []);

  return (
    <div
      id="home"
      className="relative min-h-[100vh] w-full bg-[#f5f5f7] overflow-hidden flex flex-col items-center pt-48 pb-12 font-sans tracking-tight"
      onMouseMove={handleMouseMove}
    >
      {/* Background Ambience */}
      <motion.div 
        className="pointer-events-none absolute inset-0 z-0 transition-opacity duration-100"
        animate={{ background: `radial-gradient(800px circle at ${mousePosition.x}px ${mousePosition.y}px, rgba(139,92,246,0.06), transparent 100%)` }}
      />
      
      <LayoutGroup>
        {/* Top Headline Text & Buttons */}
        <motion.div 
          layout="position"
          className="relative z-20 px-6 text-center mt-2"
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 1, ease: [0.16, 1, 0.3, 1] }}
        >
          <h1 className="text-5xl md:text-6xl lg:text-[76px] font-bold tracking-tighter text-[#1d1d1f] max-w-5xl mx-auto leading-[0.95]">
            Build smarter campus placements <br className="hidden md:block" />using <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-500 pb-2 pr-2">AI.</span>
          </h1>
          
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/tpo/login" className="bg-[#1d1d1f] text-white px-8 py-4 rounded-full font-semibold text-lg transition-transform hover:scale-[1.02] active:scale-[0.98] shadow-[0_8px_20px_rgba(0,0,0,0.12)]">
              For Placement Cells
            </Link>
            <Link href="/login" className="bg-white text-[#1d1d1f] ring-1 ring-black/[0.06] hover:bg-zinc-50 px-8 py-4 rounded-full font-semibold text-lg transition-transform hover:scale-[1.02] active:scale-[0.98] shadow-[0_4px_12px_rgba(0,0,0,0.02)]">
              For Students
            </Link>
          </div>
        </motion.div>

        {/* Center Animation Wrapper */}
        <div className="relative w-full max-w-6xl flex flex-col items-center justify-start mt-20 min-h-[400px]">
          
          {/* Search Bar / Input Area */}
          <motion.div
            layout
            initial={{ y: 0, scale: 0.95 }}
            animate={{ 
              y: phase >= 3 ? -30 : 0, 
              scale: phase >= 3 ? 0.75 : 0.95,
              opacity: phase === 4 ? 0 : 1
            }}
            transition={{ type: "spring", damping: 25, stiffness: 120 }}
            className="absolute z-20 w-full max-w-4xl px-4"
          >
            <motion.div layout className={`flex items-center h-[80px] bg-white/95 backdrop-blur-2xl rounded-full p-2.5 shadow-[0_8px_30px_rgb(0,0,0,0.06)] ring-1 ring-black/[0.04] transition-all duration-300 ${phase === 2 ? 'ring-4 ring-purple-500/10 shadow-[0_16px_60px_rgba(139,92,246,0.15)]' : ''}`}>
              <div className="ml-5 mr-3 shrink-0">
                <Search className="text-zinc-400 w-6 h-6" />
              </div>
              <motion.div layout className="flex-1 px-4 text-zinc-700 text-[22px] font-medium tracking-tight whitespace-nowrap overflow-hidden">
                {phase === 0 ? (
                  <span className="text-[#86868b] font-normal">Paste a JD or ask &quot;Find top React students&quot;</span>
                ) : (
                  <span>
                    {typedText}
                    <motion.span 
                      animate={{ opacity: [0, 1, 0] }} 
                      transition={{ repeat: Infinity, duration: 0.8 }}
                      className="inline-block w-[2px] h-[22px] bg-purple-500 ml-1 -mb-0.5"
                    />
                  </span>
                )}
              </motion.div>
              <motion.div layout className="flex items-center gap-2 shrink-0">
                <AnimatePresence mode="popLayout">
                  {phase < 3 && (
                    <motion.div
                      key="actions"
                      initial={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8, width: 0, paddingLeft: 0, ObjectWidth: 0 }}
                      className="flex gap-2 items-center"
                    >
                      <motion.button 
                         animate={{ scale: phase === 2 ? [1, 1.2, 1] : 1, color: phase >= 2 ? '#8b5cf6' : '#a1a1aa' }}
                         transition={{ duration: 0.3 }}
                         className="w-14 h-14 flex items-center justify-center rounded-full hover:bg-zinc-100 transition-colors"
                      >
                        <Upload className="w-6 h-6" />
                      </motion.button>
                      <motion.button 
                         layoutId="analyze-pill"
                         animate={{ scale: phase === 2 ? 0.95 : 1 }}
                         className="h-14 px-8 rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-lg font-semibold flex items-center gap-2 transition-all whitespace-nowrap"
                      >
                        <motion.span layout="position">Analyze</motion.span> 
                        <ArrowRight className="w-5 h-5 ml-1 inline-block" />
                      </motion.button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </motion.div>
          </motion.div>

          {/* Analyzing Pulsing State */}
          <AnimatePresence>
            {phase === 3 && (
              <motion.div
                layoutId="analyze-pill"
                className="absolute z-10 bg-white/90 backdrop-blur-2xl border border-purple-500/20 px-10 py-5 rounded-full flex flex-col items-center justify-center gap-3 shadow-sm mt-12"
              >
                <div className="flex items-center gap-3">
                  <motion.div initial={{ opacity: 0, scale: 0 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2 }}>
                    <Sparkles className="text-purple-500 w-6 h-6 animate-pulse" />
                  </motion.div>
                  <motion.span layout="position" className="text-xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 text-transparent bg-clip-text whitespace-nowrap">
                    Analyzing Candidates
                  </motion.span>
                </div>
                
                <motion.div 
                   initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                   className="absolute top-full mt-6 h-8 w-64 flex justify-center overflow-hidden"
                >
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={analyzingStep}
                        initial={{ opacity: 0, y: 15 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -15 }}
                        className="absolute text-zinc-500 font-semibold tracking-wide"
                      >
                         {ANALYZING_PHRASES[analyzingStep]}
                      </motion.div>
                    </AnimatePresence>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Premium Workflow Reveal */}
          <AnimatePresence>
            {phase === 4 && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute w-full flex items-center justify-center z-10 scale-[0.45] sm:scale-[0.55] md:scale-[0.65] lg:scale-[0.75] mt-12"
              >
                {/* SVG Connecting Lines Behind Cards */}
                <svg className="absolute w-[900px] h-[300px] pointer-events-none" style={{ zIndex: -1 }}>
                  <motion.path 
                     initial={{ pathLength: 0, opacity: 0 }} 
                     animate={{ pathLength: 1, opacity: 1 }} 
                     transition={{ duration: 1.5, ease: "easeInOut", delay: 0.5 }}
                     d="M 120 150 C 250 150 250 50 380 50 M 120 150 C 250 150 250 250 380 250 M 520 50 C 650 50 650 150 780 150 M 520 250 C 650 250 650 150 780 150" 
                     fill="none" stroke="rgba(139,92,246,0.15)" strokeWidth="3" strokeDasharray="8 8" 
                  />
                </svg>
                
                <div className="relative w-[1000px] h-[400px]">
                  {/* Left Card: Input */}
                  <motion.div 
                     initial={{ opacity: 0, x: -40 }} animate={{ opacity: 1, x: 0 }}
                     transition={{ type: "spring", delay: 0.2, damping: 20 }}
                     className="absolute left-0 top-[90px] w-64 bg-white/80 backdrop-blur-2xl border border-zinc-200/60 shadow-sm rounded-3xl p-6"
                  >
                    <div className="w-14 h-14 bg-green-100/80 text-green-600 rounded-2xl flex items-center justify-center mb-5"><FileText className="w-6 h-6" /></div>
                    <h3 className="font-bold text-zinc-900 text-xl tracking-tight">Input</h3>
                    <p className="text-zinc-500 font-medium text-sm mt-1">Job Description + Filters</p>
                  </motion.div>

                  {/* Center Top Card: AI Engine */}
                  <motion.div 
                     initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                     transition={{ type: "spring", delay: 0.6, damping: 20 }}
                     className="absolute left-[300px] top-[-10px] w-64 bg-white/80 backdrop-blur-2xl border border-zinc-200/60 shadow-sm rounded-3xl p-6"
                  >
                    <div className="w-14 h-14 bg-blue-100/80 text-blue-600 rounded-2xl flex items-center justify-center mb-5"><BrainCircuit className="w-6 h-6" /></div>
                    <h3 className="font-bold text-zinc-900 text-xl tracking-tight">AI Engine</h3>
                    <p className="text-zinc-500 font-medium text-sm mt-1">Resume + GitHub + Marksheet Analysis</p>
                  </motion.div>

                  {/* Center Bottom Card: Ranking Output */}
                  <motion.div 
                     initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                     transition={{ type: "spring", delay: 0.8, damping: 20 }}
                     className="absolute left-[300px] top-[190px] w-64 bg-white/80 backdrop-blur-2xl border border-zinc-200/60 shadow-sm rounded-3xl p-6"
                  >
                    <div className="w-14 h-14 bg-teal-100/80 text-teal-600 rounded-2xl flex items-center justify-center mb-5"><ListChecks className="w-6 h-6" /></div>
                    <h3 className="font-bold text-zinc-900 text-xl tracking-tight">Ranking Output</h3>
                    <p className="text-zinc-500 font-medium text-sm mt-1">Verified Scoring Engine</p>
                  </motion.div>

                  {/* Right Large Card: Top Matches */}
                  <motion.div 
                     initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }}
                     transition={{ type: "spring", delay: 1.2, damping: 20 }}
                     className="absolute right-[40px] top-[15px] w-80 bg-white/95 backdrop-blur-3xl border border-zinc-200/60 shadow-sm rounded-[2rem] p-6 flex flex-col"
                  >
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="font-bold text-zinc-900 px-1 text-xl tracking-tight">Top Matches</h3>
                      <span className="text-[10px] font-bold uppercase tracking-wider bg-green-100/80 text-green-700 px-3 py-1.5 rounded-full flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Verified
                      </span>
                    </div>
                    <div className="space-y-3">
                       {[
                         { n: "Ansh Bhatt", s: "94%" },
                         { n: "Priya Sharma", s: "91%" },
                         { n: "Rahul Verma", s: "88%" },
                         { n: "Sneha", s: "86%" },
                         { n: "Arjun", s: "84%" },
                       ].map((m, i) => (
                          <motion.div 
                            key={i}
                            initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 1.5 + i*0.1 }}
                            className="flex items-center justify-between p-3.5 rounded-2xl bg-zinc-50/80 hover:bg-zinc-100 transition-colors border border-zinc-100"
                          >
                            <div className="flex items-center gap-3">
                              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${i===0 ? 'bg-purple-600 text-white' : 'bg-zinc-200 text-zinc-600'}`}>{i+1}</div>
                              <span className="font-bold text-zinc-800 text-[15px]">{m.n}</span>
                            </div>
                            <span className="font-bold text-purple-600 tracking-tight">{m.s}</span>
                          </motion.div>
                       ))}
                    </div>
                    <motion.div
                      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 2.2 }}
                    >
                      <Link
                        href="/tpo"
                        className="block w-full mt-6 bg-zinc-950 text-white rounded-2xl py-4 text-center font-semibold text-[15px] hover:bg-zinc-800 transition-colors"
                      >
                        View Dashboard
                      </Link>
                    </motion.div>
                  </motion.div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </LayoutGroup>
    </div>
  );
}
