"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ChevronDown, Mail, ShieldCheck, Puzzle } from "lucide-react";
import { SponsorMatchMark } from "@/components/brand/SponsorMatchMark";
import { cn } from "@/lib/utils";

const FOCUS_OPTIONS = [
  { value: "", label: "All focus areas" },
  { value: "stem", label: "STEM & tech" },
  { value: "service", label: "Service & impact" },
  { value: "arts", label: "Arts & culture" },
  { value: "sports", label: "Sports & wellness" },
  { value: "greek", label: "Greek life" },
];

const WHEN_OPTIONS = [
  { value: "", label: "Any timeline" },
  { value: "semester", label: "This semester" },
  { value: "term", label: "Next term" },
  { value: "year", label: "This academic year" },
];

const BUDGET_OPTIONS = [
  { value: "", label: "Any support level" },
  { value: "starter", label: "Under \$500" },
  { value: "mid", label: "\$500 – \$2,000" },
  { value: "big", label: "\$2,000+" },
];

function SelectLike({
  value,
  onChange,
  options,
  className,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  className?: string;
}) {
  return (
    <div className={cn("relative", className)}>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full cursor-pointer appearance-none rounded-full border-2 border-neutral-200 bg-white py-3 pl-4 pr-10 text-sm font-semibold text-neutral-800 shadow-inner outline-none transition hover:border-neutral-300 focus:border-neutral-900/30 focus:ring-2 focus:ring-neutral-900/10"
      >
        {options.map((o) => (
          <option key={o.value || "all"} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <ChevronDown
        className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500"
        aria-hidden
      />
    </div>
  );
}

const fadeUp = {
  initial: { opacity: 0, y: 28 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-60px" },
  transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] as const },
};

export function SponsorshipLanding() {
  const [intent, setIntent] = useState<"club" | "sponsor">("club");
  const [orgKind, setOrgKind] = useState<"campus" | "community">("campus");
  const [focus, setFocus] = useState("");
  const [when, setWhen] = useState("");
  const [budget, setBudget] = useState("");

  const qs = new URLSearchParams();
  if (focus) qs.set("focus", focus);
  if (when) qs.set("when", when);
  if (budget) qs.set("budget", budget);
  qs.set("intent", intent);
  qs.set("org", orgKind);
  const wizardHref = `/wizard${qs.toString() ? `?${qs.toString()}` : ""}`;

  return (
    <div className="scroll-smooth">
      <div className="wickret-mesh-bg relative min-h-screen">
        <header className="sticky top-0 z-50 border-b border-neutral-200/60 bg-[hsl(40_33%_98%_/0.72)] px-4 py-4 backdrop-blur-xl md:px-10">
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
            <div className="flex items-center gap-3 font-display text-lg font-bold tracking-tight text-neutral-900">
              <SponsorMatchMark size="md" priority className="shrink-0" />
              <span className="leading-none">SponsorMatch</span>
            </div>
            <nav
              className="hidden items-center gap-8 text-sm font-semibold text-neutral-600 md:flex"
              aria-label="Primary"
            >
              <a href="#benefits" className="transition hover:text-neutral-900">
                Benefits
              </a>
              <a href="#match" className="transition hover:text-neutral-900">
                Match
              </a>
            </nav>
            <Link
              href={wizardHref}
              className="rounded-full bg-neutral-900 px-4 py-2.5 text-sm font-semibold text-white shadow-md transition hover:bg-neutral-800"
            >
              Start
            </Link>
          </div>
        </header>

        <section className="relative mx-auto flex max-w-6xl flex-col gap-12 px-4 pb-24 pt-16 md:flex-row md:items-end md:gap-16 md:px-8 md:pb-32 md:pt-24 lg:pt-28">
          <motion.div
            className="max-w-2xl flex-1"
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
          >
            <p className="mb-6 text-xs font-bold uppercase tracking-[0.2em] text-neutral-500">
              Club × sponsor workspace
            </p>
            <h1 className="font-display text-[clamp(2.75rem,8vw,5.25rem)] font-medium leading-[0.95] tracking-tight text-neutral-900">
              Sponsorship
              <br />
              <span className="text-gradient font-semibold">reimagined</span>
            </h1>
            <p className="mt-8 max-w-md text-lg leading-relaxed text-neutral-600 md:text-xl">
              <span className="font-semibold text-neutral-800">
                From pitch to partners.
              </span>{" "}
              Fewer tabs, fewer templates—one flow that turns your story into
              sponsor-ready ideas and outreach.
            </p>
            <div className="mt-10 flex flex-wrap items-center gap-4">
              <Link
                href={wizardHref}
                className="inline-flex items-center justify-center rounded-full bg-neutral-900 px-8 py-4 text-base font-semibold text-white shadow-[0_20px_50px_-12px_rgba(0,0,0,0.35)] transition hover:-translate-y-0.5 hover:bg-neutral-800"
              >
                Get a sponsor match
              </Link>
              <a
                href="#match"
                className="inline-flex items-center gap-2 rounded-full border-2 border-neutral-300 bg-white/80 px-6 py-3.5 text-sm font-semibold text-neutral-800 backdrop-blur transition hover:border-neutral-400"
              >
                Refine in the widget
              </a>
            </div>
          </motion.div>

          <motion.div
            className="relative flex-1 md:max-w-sm"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.12, duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="absolute -right-6 -top-6 h-40 w-40 rounded-full bg-gradient-to-br from-violet-200/80 to-fuchsia-200/50 blur-2xl" />
            <div className="absolute -bottom-8 -left-4 h-32 w-32 rounded-full bg-gradient-to-tr from-amber-200/70 to-transparent blur-2xl" />
            <div className="relative rounded-[2rem] border border-white/80 bg-white/90 p-8 shadow-[0_40px_100px_-40px_rgba(15,23,42,0.35)] backdrop-blur-sm">
              <p className="text-sm font-semibold text-neutral-500">
                Built for outreach—not spam
              </p>
              <p className="mt-2 font-display text-2xl font-semibold leading-snug text-neutral-900">
                Stop wasting time on hundreds of cold emails to random sponsors—find
                the right matches here.
              </p>
              <ul className="mt-6 space-y-4 text-sm leading-relaxed text-neutral-600">
                <li className="flex gap-3">
                  <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-violet-100 text-violet-700">
                    <Puzzle className="h-4 w-4" />
                  </span>
                  <span>
                    <strong className="text-neutral-800">Semantic matching</strong>{" "}
                    — we read your mission, not just keywords.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
                    <Mail className="h-4 w-4" />
                  </span>
                  <span>
                    <strong className="text-neutral-800">Human-sounding drafts</strong>{" "}
                    — edit once, send with confidence.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-sky-100 text-sky-700">
                    <ShieldCheck className="h-4 w-4" />
                  </span>
                  <span>
                    <strong className="text-neutral-800">Campus-first</strong> — built
                    for real org budgets and timelines.
                  </span>
                </li>
              </ul>
            </div>
          </motion.div>
        </section>
      </div>

      <section
        id="benefits"
        className="border-t border-neutral-200/80 bg-[hsl(260_25%_97%)] px-4 py-24 md:px-10"
      >
        <div className="mx-auto max-w-6xl">
          <motion.div {...fadeUp}>
            <h2 className="font-display text-3xl font-semibold tracking-tight text-neutral-900 md:text-5xl md:leading-tight">
              Outreach
              <br />
              <span className="text-neutral-500">on your terms</span>
            </h2>
            <p className="mt-6 max-w-2xl text-lg text-neutral-600">
              Real-time ideas, next-step clarity, flexible tone—whether you&apos;re a
              five-person club or a whole council.
            </p>
          </motion.div>

          <div className="mt-16 grid gap-6 md:grid-cols-3">
            {[
              {
                title: "Get matched faster",
                body: "Vector search over real sponsor profiles—less spray-and-pray.",
              },
              {
                title: "Events that make sense",
                body: "Activation ideas grounded in what you already run.",
              },
              {
                title: "Security-minded copy",
                body: "Drafts you can review; nothing auto-sent without you.",
              },
            ].map((item, i) => (
              <motion.div
                key={item.title}
                {...fadeUp}
                transition={{ ...fadeUp.transition, delay: i * 0.08 }}
                className="rounded-3xl border border-neutral-200/80 bg-white p-8 shadow-sm"
              >
                <h3 className="font-display text-xl font-semibold text-neutral-900">
                  {item.title}
                </h3>
                <p className="mt-3 text-neutral-600">{item.body}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section
        id="match"
        className="scroll-mt-24 border-t border-neutral-200/80 bg-[hsl(40_33%_98%)] px-4 py-20 md:px-10"
      >
        <div className="mx-auto max-w-6xl">
          <motion.div
            {...fadeUp}
            className="mx-auto mb-12 max-w-2xl text-center"
          >
            <h2 className="font-display text-3xl font-semibold tracking-tight text-neutral-900 md:text-4xl">
              Match before you message
            </h2>
            <p className="mt-4 text-lg text-neutral-600">
              Set intent, scope, and filters—then jump into club intake with one tap.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.45 }}
            className="mx-auto w-full max-w-md"
          >
            <div className="overflow-hidden rounded-3xl border border-neutral-200/90 bg-white shadow-[0_24px_80px_-32px_rgba(15,23,42,0.25)]">
              <div className="grid grid-cols-2 gap-0 p-1">
                <button
                  type="button"
                  onClick={() => setIntent("club")}
                  className={cn(
                    "rounded-2xl py-3 text-center text-sm font-bold transition md:text-base",
                    intent === "club"
                      ? "bg-neutral-900 text-white shadow-md"
                      : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200/80"
                  )}
                >
                  I&apos;m a club
                </button>
                <button
                  type="button"
                  onClick={() => setIntent("sponsor")}
                  className={cn(
                    "rounded-2xl py-3 text-center text-sm font-bold transition md:text-base",
                    intent === "sponsor"
                      ? "bg-neutral-900 text-white shadow-md"
                      : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200/80"
                  )}
                >
                  I&apos;m a sponsor
                </button>
              </div>

              <div className="space-y-4 px-4 pb-4 pt-4">
                <div className="flex rounded-full border border-neutral-200 bg-neutral-50 p-1">
                  <button
                    type="button"
                    onClick={() => setOrgKind("campus")}
                    className={cn(
                      "flex-1 rounded-full py-2 text-center text-xs font-semibold md:text-sm",
                      orgKind === "campus"
                        ? "bg-white text-neutral-900 shadow-sm"
                        : "text-neutral-600"
                    )}
                  >
                    On campus
                  </button>
                  <button
                    type="button"
                    onClick={() => setOrgKind("community")}
                    className={cn(
                      "flex-1 rounded-full py-2 text-center text-xs font-semibold md:text-sm",
                      orgKind === "community"
                        ? "bg-white text-neutral-900 shadow-sm"
                        : "text-neutral-600"
                    )}
                  >
                    Community
                  </button>
                </div>

                <SelectLike
                  value={focus}
                  onChange={setFocus}
                  options={FOCUS_OPTIONS}
                />
                <SelectLike value={when} onChange={setWhen} options={WHEN_OPTIONS} />
                <SelectLike
                  value={budget}
                  onChange={setBudget}
                  options={BUDGET_OPTIONS}
                />

                <Link
                  href={wizardHref}
                  className="mt-2 flex w-full items-center justify-center rounded-full bg-neutral-900 py-4 text-center text-base font-semibold tracking-wide text-white shadow-md transition hover:bg-neutral-800"
                >
                  I want a sponsor match →
                </Link>
                <p className="pb-1 text-center text-[11px] font-medium text-neutral-500">
                  Opens the club intake wizard. Optional filters help tune ideas later.
                </p>
              </div>
            </div>
          </motion.div>

        </div>
      </section>
    </div>
  );
}
