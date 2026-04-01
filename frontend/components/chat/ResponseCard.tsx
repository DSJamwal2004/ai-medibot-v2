"use client";
import { useState } from "react";
import {
  AlertTriangle, Lightbulb, Stethoscope, BookOpen,
  ChevronDown, ChevronUp, Activity, Zap, Info
} from "lucide-react";
import type { ChatResponse } from "@/lib/api";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { ConfidenceBar } from "@/components/ui/ConfidenceBar";
import clsx from "clsx";

interface Props {
  data: ChatResponse;
}

export function ResponseCard({ data }: Props) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [showCitations, setShowCitations] = useState(false);

  const isEmergency = data.urgency === "emergency";
  const hasConditions = data.conditions.length > 0;
  const hasSymptoms = data.symptoms.length > 0;
  const hasCitations = data.citations.length > 0;
  const hasSteps = data.immediate_steps.length > 0;

  // Plain text — split on markdown paragraphs
  const adviceLines = data.advice
    .replace(/\n\n---\n\*.*\*/, "") // remove disclaimer suffix (rendered separately)
    .split(/\n\n+/)
    .map(l => l.trim())
    .filter(Boolean);

  return (
    <div className={clsx(
      "rounded-2xl border overflow-hidden animate-fade-up",
      isEmergency
        ? "border-red-500/40 bg-red-950/20 glow-emergency"
        : "border-[#1e2535] bg-[#161b27]"
    )}>
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className={clsx(
        "flex items-center justify-between px-4 py-3 border-b",
        isEmergency ? "border-red-500/30 bg-red-900/20" : "border-[#1e2535]"
      )}>
        <div className="flex items-center gap-2.5">
          <div className={clsx(
            "w-7 h-7 rounded-lg flex items-center justify-center",
            isEmergency ? "bg-red-500/20" : "bg-blue-500/15"
          )}>
            <Activity className={clsx("w-4 h-4", isEmergency ? "text-red-400" : "text-blue-400")} />
          </div>
          <span className="text-sm font-semibold text-slate-200">
            {isEmergency ? "⚠️ Emergency Detected" : "Medical Assessment"}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <RiskBadge riskLevel={data.risk_level} urgency={data.urgency} />
        </div>
      </div>

      <div className="p-4 space-y-4">

        {/* ── Symptoms detected ────────────────────────────────────────── */}
        {hasSymptoms && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <Stethoscope className="w-3.5 h-3.5" /> Symptoms Identified
            </p>
            <div className="flex flex-wrap gap-1.5">
              {data.symptoms.map((s, i) => (
                <span key={i} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs bg-[#1e2535] border border-[#252d3d] text-slate-300">
                  {s.name}
                  {s.severity && (
                    <span className="text-slate-500">· {s.severity}</span>
                  )}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ── Conditions ───────────────────────────────────────────────── */}
        {hasConditions && !isEmergency && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5" /> Possible Conditions
            </p>
            <div className="space-y-2">
              {data.conditions.map((c, i) => (
                <div key={i} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-200">{c.name}</span>
                    <span className="text-xs text-slate-500 font-mono">{Math.round(c.confidence * 100)}%</span>
                  </div>
                  <ConfidenceBar score={c.confidence} size="sm" />
                  {c.reasoning && (
                    <p className="text-xs text-slate-500 leading-relaxed">{c.reasoning}</p>
                  )}
                </div>
              ))}
            </div>
            <p className="text-xs text-slate-600 italic mt-1">
              These are general possibilities — not a diagnosis. Only a doctor can diagnose.
            </p>
          </div>
        )}

        {/* ── Advice ───────────────────────────────────────────────────── */}
        <div className={clsx(
          "rounded-xl p-3.5 space-y-2 border",
          isEmergency
            ? "bg-red-950/30 border-red-500/25"
            : "bg-[#0f1117]/60 border-[#1e2535]"
        )}>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <Lightbulb className="w-3.5 h-3.5" /> Guidance
          </p>
          {adviceLines.map((line, i) => (
            <p key={i} className="text-sm text-slate-300 leading-relaxed">{line}</p>
          ))}
        </div>

        {/* ── Immediate steps ───────────────────────────────────────────── */}
        {hasSteps && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Immediate Steps
            </p>
            <ol className="space-y-1.5">
              {data.immediate_steps.map((step, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[#1e2535] border border-[#252d3d] text-xs text-slate-400 flex items-center justify-center font-mono mt-0.5">
                    {i + 1}
                  </span>
                  <span className="text-sm text-slate-300 leading-relaxed">{step}</span>
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* ── When to seek care ─────────────────────────────────────────── */}
        {data.when_to_seek_care && (
          <div className="flex items-start gap-2.5 p-3 rounded-lg bg-amber-500/5 border border-amber-500/15">
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-200/80 leading-relaxed">{data.when_to_seek_care}</p>
          </div>
        )}

        {/* ── Confidence ───────────────────────────────────────────────── */}
        {!isEmergency && (
          <div className="pt-1">
            <ConfidenceBar score={data.confidence_score} label="Assessment confidence" />
          </div>
        )}

        {/* ── Explanation toggle ────────────────────────────────────────── */}
        {data.explanation && (
          <div className="border-t border-[#1e2535] pt-3">
            <button
              onClick={() => setShowExplanation(v => !v)}
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              <Info className="w-3.5 h-3.5" />
              {showExplanation ? "Hide" : "Show"} reasoning
              {showExplanation ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
            {showExplanation && (
              <div className="mt-2.5 space-y-2 animate-fade-up">
                <p className="text-xs text-slate-400 leading-relaxed">{data.explanation}</p>
                {data.key_factors.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {data.key_factors.map((f, i) => (
                      <span key={i} className="text-xs px-2 py-0.5 rounded bg-[#1e2535] text-slate-500">
                        {f}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ── Citations toggle ──────────────────────────────────────────── */}
        {hasCitations && (
          <div className={clsx("border-t border-[#1e2535] pt-3", !data.explanation && "")}>
            <button
              onClick={() => setShowCitations(v => !v)}
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              <BookOpen className="w-3.5 h-3.5" />
              {data.citations.length} source{data.citations.length !== 1 ? "s" : ""}
              {showCitations ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
            {showCitations && (
              <div className="mt-2.5 space-y-1.5 animate-fade-up">
                {data.citations.map((c, i) => (
                  <div key={i} className="flex items-center justify-between py-1.5 border-b border-[#1e2535] last:border-0">
                    <div>
                      <p className="text-xs text-slate-300 font-medium">{c.title}</p>
                      {c.source && <p className="text-xs text-slate-600">{c.source}</p>}
                    </div>
                    <span className="text-xs text-slate-600 font-mono ml-3">
                      {Math.round(c.score * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Footer disclaimer ─────────────────────────────────────────── */}
        <p className="text-xs text-slate-600 border-t border-[#1e2535] pt-3">
          For general guidance only · Not a substitute for professional medical advice
        </p>
      </div>
    </div>
  );
}
