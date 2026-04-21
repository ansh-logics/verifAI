"use client";

import * as React from "react";
import { useCallback, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Search, Zap, AlertCircle, X } from "lucide-react";
import axios from "axios";
import { useRouter } from "next/navigation";

import { searchCandidates, getApiErrorMessage, getSearchCandidateDetails } from "@/lib/api";
import { clearTpoAuth } from "@/lib/auth-storage";
import type { SearchResponse } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

function scoreBadge(score: number) {
  if (score >= 80) return { bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-300" };
  if (score >= 60) return { bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-300" };
  return { bg: "bg-rose-100", text: "text-rose-700", border: "border-rose-300" };
}

function CandidateFullDetails({ candidateId }: { candidateId: number }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  React.useEffect(() => {
    let mounted = true;
    getSearchCandidateDetails(candidateId)
      .then((res) => {
        if (mounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error(err);
        if (axios.isAxiosError(err) && [401, 403].includes(err.response?.status ?? 0)) {
          clearTpoAuth();
          router.replace("/tpo/login");
        }
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [candidateId, router]);

  if (loading) return <div className="text-sm text-slate-500 animate-pulse px-6 py-4">Loading detailed profile...</div>;
  if (!data) return <div className="text-sm text-slate-500 px-6 py-4">Failed to load detailed profile.</div>;

  const hasGithub = data.github_data && Object.keys(data.github_data).length > 0;
  const hasLeetcode = data.leetcode_data && Object.keys(data.leetcode_data).length > 0;

  return (
    <div className="px-10 py-6 bg-slate-50 border-t border-slate-200 grid grid-cols-2 gap-8">
      <div className="space-y-3 col-span-2 md:col-span-1">
        <h4 className="text-sm font-semibold text-slate-900">Candidate Details</h4>
        <div className="text-sm text-slate-700">Email: {data.email}</div>
        <div className="text-sm text-slate-700">Roll No: {data.roll_no || "N/A"}</div>
        <div className="text-sm text-slate-700">Branch: {data.branch || "N/A"}</div>
        <div className="text-sm text-slate-700">CGPA: {data.cgpa !== null ? data.cgpa : "N/A"}</div>
        {data.resume_data?.resume_url && (
          <div className="text-sm mt-2">
            <a href={data.resume_data.resume_url} target="_blank" rel="noreferrer" className="text-blue-600 underline">View Resume</a>
          </div>
        )}
      </div>

      <div className="space-y-3 col-span-2 md:col-span-1">
        {hasGithub && (
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-slate-900">GitHub Stats</h4>
            <div className="text-sm text-slate-700">Followers: {data.github_data.followers || 0}</div>
            <div className="text-sm text-slate-700">Public Repos: {data.github_data.public_repos || 0}</div>
            {data.github_data.languages?.length > 0 && (
              <div className="text-sm text-slate-700">Top Languages: {data.github_data.languages.slice(0, 3).join(", ")}</div>
            )}
          </div>
        )}
        {hasLeetcode && (
          <div>
            <h4 className="text-sm font-semibold text-slate-900">LeetCode Stats</h4>
            <div className="text-sm text-slate-700">Solved: {data.leetcode_data.totalSolved || 0}</div>
            <div className="text-sm text-slate-700">Rating: {Math.round(data.leetcode_data.rating || 0)}</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [expandedKey, setExpandedKey] = useState<number | null>(null);

  const handleSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults(null);
      setError(null);
      setHasSearched(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await searchCandidates(searchQuery.trim(), 0, null, null, 50);
      setResults(response);
      setHasSearched(true);
    } catch (err) {
      if (axios.isAxiosError(err) && [401, 403].includes(err.response?.status ?? 0)) {
        clearTpoAuth();
        router.replace("/tpo/login");
        return;
      }
      const errorMsg = getApiErrorMessage(err);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  const debouncedSearch = useMemo(() => {
    let timeoutId: NodeJS.Timeout;
    return (searchQuery: string) => {
      clearTimeout(timeoutId);
      if (!searchQuery.trim()) {
        setResults(null);
        setHasSearched(false);
        return;
      }
      timeoutId = setTimeout(() => {
        handleSearch(searchQuery);
      }, 500);
    };
  }, [handleSearch]);

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    debouncedSearch(value);
  };

  const handleClear = () => {
    setQuery("");
    setResults(null);
    setError(null);
    setHasSearched(false);
  };

  const handleInstantSearch = (term: string) => {
    setQuery(term);
    handleSearch(term);
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 rounded-[2rem] w-full h-full">
      <div className="mx-auto w-full max-w-7xl space-y-8">
        <section className="space-y-2">
          <h1 className="text-4xl font-bold text-slate-900">Resume Search</h1>
          <p className="text-slate-600">Find candidates by skills, name, or technologies with instant results</p>
        </section>

        <section className="bg-white rounded-[2rem] border border-slate-200/60 shadow-sm overflow-hidden flex flex-col">
          <div className="p-6 border-b border-slate-100">
            <div className="flex gap-2">
              <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                placeholder="Search: react developer, node mongodb, python ml, amit..."
                value={query}
                onChange={handleQueryChange}
                className="pl-10 h-11 text-base bg-slate-50 border-transparent hover:bg-slate-100 focus:bg-white"
              />
              {query && (
                <button
                  onClick={handleClear}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition z-10"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
              </div>
              <Button
                onClick={() => handleSearch(query)}
                disabled={isLoading || !query.trim()}
                size="lg"
                className="gap-2 rounded-full px-5"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Search
                  </>
                )}
              </Button>
            </div>
            {!hasSearched && (
              <div className="space-y-2 mt-4">
                <p className="text-sm text-slate-600 font-medium">Try searching:</p>
                <div className="flex flex-wrap gap-2">
                  {["react developer", "node mongodb", "python ml", "amit", "raect"].map((term) => (
                    <button
                      key={term}
                      onClick={() => handleInstantSearch(term)}
                      className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100 transition border border-blue-200"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

        {/* Error State */}
          <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
            <Card className="m-6 border-2 border-red-200 bg-red-50">
                <CardContent className="p-4 flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                  <p className="text-red-700">{error}</p>
                </CardContent>
              </Card>
            </motion.div>
          )}
          </AnimatePresence>

        {/* Results */}
          <AnimatePresence>
          {hasSearched && results && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="space-y-4 relative z-0 p-6 pt-0"
            >
              {/* Summary */}
              <Card className="bg-blue-50 border-2 border-blue-200">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <p className="text-sm text-slate-600">Search Results for</p>
                      <p className="text-lg font-semibold text-slate-900">"{results.query}"</p>
                    </div>
                    <div className="text-right space-y-1">
                      <p className="text-3xl font-bold text-blue-700">{results.total_results}</p>
                      <p className="text-sm text-slate-600">candidate{results.total_results !== 1 ? "s" : ""} found</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Results Table */}
              {results.total_results === 0 ? (
                <Card className="border-2 border-dashed border-slate-300 bg-slate-50">
                  <CardContent className="p-12 text-center">
                    <Search className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                    <p className="text-lg font-medium text-slate-600 mb-2">No candidates found</p>
                    <p className="text-sm text-slate-500">
                      Try different search terms or check the spelling (typos are automatically corrected)
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <Card className="border border-slate-200/60 overflow-hidden shadow-sm rounded-2xl">
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-100 hover:bg-transparent">
                          <TableHead className="h-12 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Rank</TableHead>
                          <TableHead className="h-12 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Name</TableHead>
                          <TableHead className="h-12 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Match Score</TableHead>
                          <TableHead className="h-12 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Overall Score</TableHead>
                          <TableHead className="h-12 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Matched Terms</TableHead>
                          <TableHead className="h-12 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Quality</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {results.results.map((candidate, idx) => {
                          const matchScoreBadge = scoreBadge(candidate.match_score);
                          const overallScoreBadge = scoreBadge(candidate.overall_score);

                          return (
                            <React.Fragment key={candidate.candidate_id}>
                              <TableRow
                                className="border-slate-50 hover:bg-slate-50/50 transition-colors cursor-pointer"
                                onClick={() => setExpandedKey(expandedKey === candidate.candidate_id ? null : candidate.candidate_id)}
                              >
                                <TableCell className="px-6 py-4 font-semibold text-slate-700 w-12">
                                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-medium">
                                    {idx + 1}
                                  </div>
                                </TableCell>
                                <TableCell className="px-6 py-4">
                                  <div className="space-y-1">
                                    <p className="font-semibold text-slate-900">{candidate.name}</p>
                                    <p className="text-xs text-slate-500">{candidate.email}</p>
                                  </div>
                                </TableCell>
                                <TableCell className="px-6 py-4">
                                  <div className={cn("px-3 py-1 rounded-full border text-sm font-semibold inline-block", matchScoreBadge.bg, matchScoreBadge.text, matchScoreBadge.border)}>
                                    {candidate.match_score.toFixed(1)}
                                  </div>
                                </TableCell>
                                <TableCell className="px-6 py-4">
                                  <div className={cn("px-3 py-1 rounded-full border text-sm font-semibold inline-block", overallScoreBadge.bg, overallScoreBadge.text, overallScoreBadge.border)}>
                                    {candidate.overall_score.toFixed(1)}
                                  </div>
                                </TableCell>
                                <TableCell className="px-6 py-4">
                                  <div className="flex flex-wrap gap-1">
                                    {candidate.matched_terms.slice(0, 3).map((term) => (
                                      <Badge key={term} variant="secondary" className="text-xs">
                                        {term}
                                      </Badge>
                                    ))}
                                    {candidate.matched_terms.length > 3 && (
                                      <Badge variant="outline" className="text-xs">
                                        +{candidate.matched_terms.length - 3}
                                      </Badge>
                                    )}
                                  </div>
                                </TableCell>
                                <TableCell className="px-6 py-4">
                                  <Badge
                                    variant="outline"
                                    className={cn(
                                      "rounded-full px-2.5 py-0.5 font-medium border-transparent",
                                      candidate.match_quality === "exact"
                                        ? "bg-emerald-500/10 text-emerald-700"
                                        : candidate.match_quality === "fuzzy"
                                          ? "bg-amber-500/10 text-amber-700"
                                          : "bg-slate-200/80 text-slate-700",
                                    )}
                                  >
                                    {candidate.match_quality}
                                  </Badge>
                                </TableCell>
                              </TableRow>
                              {expandedKey === candidate.candidate_id && (
                                <TableRow>
                                  <TableCell colSpan={6} className="p-0">
                                    <CandidateFullDetails candidateId={candidate.candidate_id} />
                                  </TableCell>
                                </TableRow>
                              )}
                            </React.Fragment>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>
                </Card>
              )}
            </motion.div>
          )}
          </AnimatePresence>

        {/* Empty State */}
          {!hasSearched && !query && (
            <Card className="m-6 mt-0 border-2 border-dashed border-slate-300 bg-gradient-to-br from-slate-50 to-blue-50">
            <CardContent className="flex flex-col items-center justify-center h-full text-center space-y-4 py-12">
              <Search className="w-16 h-16 text-slate-300" />
              <div className="space-y-2">
                <h3 className="text-xl font-semibold text-slate-900">Start searching</h3>
                <p className="text-slate-600 max-w-sm">
                  Enter skills, name, or technologies to find the best-matched candidates from your pool
                </p>
              </div>
            </CardContent>
            </Card>
          )}
        </section>
      </div>
    </div>
  );
}
