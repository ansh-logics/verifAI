"use client";

import * as React from "react";
import { useCallback, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { Loader2, Search, Zap, AlertCircle, X } from "lucide-react";

import { searchCandidates, getApiErrorMessage } from "@/lib/api";
import type { SearchResponse } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

function scoreBadge(score: number) {
  if (score >= 80) return { bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-300" };
  if (score >= 60) return { bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-300" };
  return { bg: "bg-rose-100", text: "text-rose-700", border: "border-rose-300" };
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

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
      if (response.total_results === 0) {
        toast.info(`No results found for "${searchQuery}"`);
      } else {
        toast.success(`Found ${response.total_results} candidate${response.total_results !== 1 ? "s" : ""}`);
      }
    } catch (err) {
      const errorMsg = getApiErrorMessage(err);
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, []);

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
    <div className="flex-1 flex flex-col p-6 lg:p-8 gap-6 overflow-auto">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold text-slate-900">Resume Search</h1>
        <p className="text-slate-600">Find candidates by skills, name, or technologies with instant results</p>
      </div>

      {/* Search Box */}
      <Card className="border-2 border-slate-200 shadow-sm">
        <CardContent className="p-6 space-y-4">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                placeholder="Search: react developer, node mongodb, python ml, amit..."
                value={query}
                onChange={handleQueryChange}
                disabled={isLoading}
                className="pl-10 h-11 text-base"
              />
              {query && (
                <button
                  onClick={handleClear}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
            <Button
              onClick={() => handleSearch(query)}
              disabled={isLoading || !query.trim()}
              size="lg"
              className="gap-2"
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

          {/* Quick Search Examples */}
          {!hasSearched && (
            <div className="space-y-2">
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
        </CardContent>
      </Card>

      {/* Error State */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Card className="border-2 border-red-200 bg-red-50">
              <CardContent className="p-4 flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                <p className="text-red-700">{error}</p>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Skeleton Loading State */}
      {isLoading && (
        <Card className="border-2 border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50 hover:bg-slate-50">
                  <TableHead className="font-semibold text-slate-700">Rank</TableHead>
                  <TableHead className="font-semibold text-slate-700">Name</TableHead>
                  <TableHead className="font-semibold text-slate-700">Match Score</TableHead>
                  <TableHead className="font-semibold text-slate-700">Overall Score</TableHead>
                  <TableHead className="font-semibold text-slate-700">Matched Terms</TableHead>
                  <TableHead className="font-semibold text-slate-700">Quality</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i} className="border-t border-slate-200">
                    <TableCell><Skeleton className="h-8 w-8 rounded-full" /></TableCell>
                    <TableCell>
                      <div className="space-y-1.5">
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="h-3 w-44" />
                      </div>
                    </TableCell>
                    <TableCell><Skeleton className="h-6 w-14 rounded-full" /></TableCell>
                    <TableCell><Skeleton className="h-6 w-14 rounded-full" /></TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Skeleton className="h-5 w-14 rounded-full" />
                        <Skeleton className="h-5 w-14 rounded-full" />
                      </div>
                    </TableCell>
                    <TableCell><Skeleton className="h-5 w-16 rounded-full" /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </Card>
      )}

      {/* Results */}
      <AnimatePresence>
        {hasSearched && results && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="space-y-4"
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
              <Card className="border-2 border-slate-200 overflow-hidden">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-slate-50 hover:bg-slate-50">
                        <TableHead className="font-semibold text-slate-700">Rank</TableHead>
                        <TableHead className="font-semibold text-slate-700">Name</TableHead>
                        <TableHead className="font-semibold text-slate-700">Match Score</TableHead>
                        <TableHead className="font-semibold text-slate-700">Overall Score</TableHead>
                        <TableHead className="font-semibold text-slate-700">Matched Terms</TableHead>
                        <TableHead className="font-semibold text-slate-700">Quality</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {results.results.map((candidate, idx) => {
                        const matchScoreBadge = scoreBadge(candidate.match_score);
                        const overallScoreBadge = scoreBadge(candidate.overall_score);

                        return (
                          <motion.tr
                            key={candidate.candidate_id}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                            className="border-t border-slate-200 hover:bg-slate-50 transition"
                          >
                            <TableCell className="font-semibold text-slate-700 w-12">
                              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-medium">
                                {idx + 1}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="space-y-1">
                                <p className="font-semibold text-slate-900">{candidate.name}</p>
                                <p className="text-xs text-slate-500">{candidate.email}</p>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className={cn("px-3 py-1 rounded-full border text-sm font-semibold inline-block", matchScoreBadge.bg, matchScoreBadge.text, matchScoreBadge.border)}>
                                {candidate.match_score.toFixed(1)}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className={cn("px-3 py-1 rounded-full border text-sm font-semibold inline-block", overallScoreBadge.bg, overallScoreBadge.text, overallScoreBadge.border)}>
                                {candidate.overall_score.toFixed(1)}
                              </div>
                            </TableCell>
                            <TableCell>
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
                            <TableCell>
                              <Badge
                                variant={
                                  candidate.match_quality === "exact"
                                    ? "default"
                                    : candidate.match_quality === "fuzzy"
                                      ? "secondary"
                                      : "outline"
                                }
                              >
                                {candidate.match_quality}
                              </Badge>
                            </TableCell>
                          </motion.tr>
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
        <Card className="border-2 border-dashed border-slate-300 bg-gradient-to-br from-slate-50 to-blue-50 flex-1">
          <CardContent className="flex flex-col items-center justify-center h-full text-center space-y-4 py-12">
            <Search className="w-16 h-16 text-slate-300" />
            <div className="space-y-2">
              <h3 className="text-xl font-semibold text-slate-900">Start searching</h3>
              <p className="text-slate-600 max-w-sm">
                Enter skills, name, or technologies to find the best-matched candidates from your pool
              </p>
            </div>
            <div className="space-y-3 pt-4">
              <p className="text-sm text-slate-600 font-medium">Example searches:</p>
              <ul className="text-sm text-slate-600 space-y-2">
                <li>🔹 Skills: "react", "python", "node.js"</li>
                <li>🔹 Combined: "react node", "python ml"</li>
                <li>🔹 Names: "amit", "john"</li>
                <li>🔹 Typo-tolerant: "raect" → finds "react"</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
