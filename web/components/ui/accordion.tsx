"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

type AccordionType = "single" | "multiple"

type AccordionContextValue = {
  type: AccordionType
  collapsible: boolean
  openValues: string[]
  toggleValue: (value: string) => void
}

const AccordionContext = React.createContext<AccordionContextValue | null>(null)
const AccordionItemValueContext = React.createContext<string | null>(null)

function useAccordionContext() {
  const ctx = React.useContext(AccordionContext)
  if (!ctx) throw new Error("Accordion components must be used within <Accordion />")
  return ctx
}

function Accordion({
  type = "single",
  collapsible = true,
  value,
  defaultValue,
  onValueChange,
  className,
  children,
}: {
  type?: AccordionType
  collapsible?: boolean
  value?: string | undefined
  defaultValue?: string | undefined
  onValueChange?: (value: string | undefined) => void
  className?: string
  children: React.ReactNode
}) {
  const [uncontrolledValue, setUncontrolledValue] = React.useState<
    string | undefined
  >(defaultValue)

  const selected = value !== undefined ? value : uncontrolledValue
  const openValues = selected ? [selected] : []

  const toggleValue = (nextValue: string) => {
    if (type === "single") {
      const isOpen = openValues.includes(nextValue)
      if (isOpen) {
        if (!collapsible) return
        setUncontrolledValue(undefined)
        onValueChange?.(undefined)
        return
      }
      setUncontrolledValue(nextValue)
      onValueChange?.(nextValue)
      return
    }

    // This project only needs single-open behavior for the candidate details UI.
    // Keeping this for API compatibility if future sections are added.
    setUncontrolledValue(nextValue)
    onValueChange?.(nextValue)
  }

  return (
    <AccordionContext.Provider
      value={{
        type,
        collapsible,
        openValues,
        toggleValue,
      }}
    >
      <div className={cn("space-y-2", className)}>{children}</div>
    </AccordionContext.Provider>
  )
}

function AccordionItem({
  value,
  className,
  children,
}: {
  value: string
  className?: string
  children: React.ReactNode
}) {
  const { openValues } = useAccordionContext()
  const isOpen = openValues.includes(value)

  return (
    <AccordionItemValueContext.Provider value={value}>
      <div
        data-state={isOpen ? "open" : "closed"}
        className={cn(
          "rounded-xl border bg-card/50 ring-1 ring-foreground/10 transition-colors",
          className,
        )}
      >
        {children}
      </div>
    </AccordionItemValueContext.Provider>
  )
}

function AccordionTrigger({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  const { toggleValue, openValues } = useAccordionContext()
  const itemValue = React.useContext(AccordionItemValueContext)
  if (!itemValue) throw new Error("AccordionTrigger must be used within an AccordionItem")

  const isOpen = openValues.includes(itemValue)

  return (
    <button
      type="button"
      className={cn(
        "flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm font-medium transition-colors hover:bg-muted/40",
        className,
      )}
      aria-expanded={isOpen}
      onClick={() => toggleValue(itemValue)}
    >
      <span className="truncate">{children}</span>
      <span
        className={cn(
          "inline-flex size-8 items-center justify-center rounded-lg bg-muted/30 text-muted-foreground transition-transform",
          isOpen && "rotate-180",
        )}
        aria-hidden
      >
        ˅
      </span>
    </button>
  )
}

function AccordionContent({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  const { openValues } = useAccordionContext()
  const itemValue = React.useContext(AccordionItemValueContext)
  if (!itemValue) throw new Error("AccordionContent must be used within an AccordionItem")

  const isOpen = openValues.includes(itemValue)

  if (!isOpen) return null

  return (
    <div
      data-slot="accordion-content"
      className={cn("px-4 pb-4 pt-2 text-sm text-foreground", className)}
    >
      {children}
    </div>
  )
}

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent }

