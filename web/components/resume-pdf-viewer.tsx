"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import { Document, Page, pdfjs } from "react-pdf";

import { Button } from "@/components/ui/button";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.js",
  import.meta.url,
).toString();

type ResumePdfViewerProps = {
  url: string;
  className?: string;
};

export default function ResumePdfViewer({ url, className }: ResumePdfViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [pageWidth, setPageWidth] = useState<number>(900);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const file = useMemo(() => ({ url, withCredentials: false }), [url]);

  const prevDisabled = pageNumber <= 1;
  const nextDisabled = numPages === 0 || pageNumber >= numPages;

  useEffect(() => {
    if (!containerRef.current) return;

    const updateWidth = () => {
      if (!containerRef.current) return;
      setPageWidth(Math.max(280, Math.floor(containerRef.current.clientWidth - 24)));
    };

    updateWidth();

    const observer = new ResizeObserver(() => updateWidth());
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div className={`flex flex-col space-y-3 ${className ?? ""}`}>
      <div
        ref={containerRef}
        className="flex-1 overflow-auto rounded-md border bg-muted/20 p-2 flex justify-center"
      >
        <Document
          file={file}
          loading={
            <div className="flex min-h-[56vh] items-center justify-center text-sm text-muted-foreground">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Loading PDF...
            </div>
          }
          onLoadSuccess={({ numPages: pages }) => {
            setNumPages(pages);
            setPageNumber(1);
            setLoadError(null);
          }}
          onLoadError={(error) => {
            setLoadError(error.message || "Failed to load PDF.");
          }}
          error={
            <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
              Unable to render PDF preview from this URL. You can still open it in a
              new tab.
            </div>
          }
        >
          {!loadError ? (
            <Page
              pageNumber={pageNumber}
              renderAnnotationLayer={false}
              renderTextLayer={false}
              width={pageWidth}
            />
          ) : null}
        </Document>
      </div>

      {!loadError && numPages > 0 ? (
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={prevDisabled}
            onClick={() => setPageNumber((p) => Math.max(1, p - 1))}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {pageNumber} of {numPages}
          </span>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={nextDisabled}
            onClick={() => setPageNumber((p) => Math.min(numPages, p + 1))}
          >
            Next
          </Button>
        </div>
      ) : null}
    </div>
  );
}
