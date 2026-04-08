"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2, Sparkles, Mail, PartyPopper } from "lucide-react";
import type {
  ClubProfile,
  EmailPitchResponse,
  EventStrategyIdea,
  MatchSponsorsResult,
} from "@shared/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  fetchEmailPitch,
  fetchEventStrategies,
  matchSponsors,
  matchToSponsorBrief,
  parseClubProfile,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const STEPS = [
  "Club intake",
  "AI analysis",
  "Sponsor matches",
  "Events & email",
  "Publish",
] as const;

const slide = {
  initial: { opacity: 0, x: 48 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -48 },
};

const transition = { duration: 0.38, ease: [0.22, 1, 0.36, 1] as const };

const LUMA_CREATE_URL = "https://luma.com/create";

function scoreToPercent(score: number): number {
  return Math.round(Math.min(100, Math.max(0, score * 100)));
}

export function SponsorshipWizard() {
  const [step, setStep] = useState(1);
  const [rawText, setRawText] = useState("");
  const [clubProfile, setClubProfile] = useState<ClubProfile | null>(null);
  const [matches, setMatches] = useState<MatchSponsorsResult[] | null>(null);
  const [selectedMatch, setSelectedMatch] = useState<MatchSponsorsResult | null>(
    null
  );
  const [eventIdeas, setEventIdeas] = useState<EventStrategyIdea[] | null>(null);
  const [ideaIndex, setIdeaIndex] = useState(0);
  const [emailPitch, setEmailPitch] = useState<EmailPitchResponse | null>(null);
  const [strategiesLoading, setStrategiesLoading] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);
  const [analyzePhase, setAnalyzePhase] = useState<"profile" | "match">("profile");
  const [error, setError] = useState<string | null>(null);

  const runAnalysis = useCallback(async () => {
    setError(null);
    setStep(2);
    setAnalyzePhase("profile");
    try {
      const profile = await parseClubProfile(rawText.trim());
      setClubProfile(profile);
      setAnalyzePhase("match");
      const result = await matchSponsors(profile);
      setMatches(result.matches);
      setSelectedMatch(result.matches[0] ?? null);
      setStep(3);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
      setStep(1);
    }
  }, [rawText]);

  useEffect(() => {
    if (step !== 4 || !clubProfile || !selectedMatch) return;
    if (eventIdeas) return;

    let cancelled = false;
    setStrategiesLoading(true);
    setError(null);
    void (async () => {
      try {
        const res = await fetchEventStrategies(
          clubProfile,
          matchToSponsorBrief(selectedMatch)
        );
        if (cancelled) return;
        setEventIdeas(res.ideas);
      } catch (e) {
        if (!cancelled) {
          setError(
            e instanceof Error ? e.message : "Could not load event ideas."
          );
        }
      } finally {
        if (!cancelled) setStrategiesLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [step, clubProfile, selectedMatch, eventIdeas]);

  useEffect(() => {
    if (step !== 4 || !clubProfile || !selectedMatch || !eventIdeas?.length) {
      return;
    }
    const idea = eventIdeas[ideaIndex];
    if (!idea) return;

    let cancelled = false;
    setEmailLoading(true);
    void (async () => {
      try {
        const pitch = await fetchEmailPitch({
          club: clubProfile,
          sponsor: matchToSponsorBrief(selectedMatch),
          eventIdea: idea,
        });
        if (!cancelled) setEmailPitch(pitch);
      } catch (e) {
        if (!cancelled) {
          setError(
            e instanceof Error ? e.message : "Could not generate email pitch."
          );
        }
      } finally {
        if (!cancelled) setEmailLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [step, clubProfile, selectedMatch, eventIdeas, ideaIndex]);

  const canSubmitIntake = rawText.trim().length >= 10;

  return (
    <div className="mx-auto flex min-h-screen max-w-4xl flex-col px-4 pb-16 pt-10 md:px-8">
      <header className="mb-10">
        <p className="text-sm font-medium text-primary">Sponsorship workspace</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight md:text-4xl">
          From pitch to partners
        </h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Tell us about your club, match with sponsors, shape events, and prep
          your outreach—step by step.
        </p>

        <ol className="mt-8 flex flex-wrap gap-2">
          {STEPS.map((label, i) => {
            const n = i + 1;
            const active = step === n;
            const done = step > n;
            return (
              <li key={label}>
                <button
                  type="button"
                  disabled={n > step}
                  onClick={() => {
                    if (n < step) setStep(n);
                  }}
                  className={cn(
                    "flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                    active &&
                      "border-primary bg-primary/10 text-primary",
                    done && !active && "border-border text-muted-foreground",
                    !active && !done && "border-dashed border-border text-muted-foreground/70",
                    n < step && "cursor-pointer hover:border-primary/50"
                  )}
                >
                  <span
                    className={cn(
                      "flex h-5 w-5 items-center justify-center rounded-full text-[10px]",
                      active && "bg-primary text-primary-foreground",
                      done && "bg-primary/20 text-primary"
                    )}
                  >
                    {done ? "✓" : n}
                  </span>
                  {label}
                </button>
              </li>
            );
          })}
        </ol>
      </header>

      {error && (
        <div className="mb-6 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="relative min-h-[420px] flex-1">
        <AnimatePresence mode="wait">
          {step === 1 && (
            <motion.section
              key="step1"
              variants={slide}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={transition}
              className="space-y-6"
            >
              <Card>
                <CardHeader>
                  <CardTitle>Club intake</CardTitle>
                  <CardDescription>
                    Share your mission, goals, and what you need from sponsors.
                    We use this to structure your profile and find matches.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label htmlFor="intake" className="text-sm font-medium">
                      About your club
                    </label>
                    <Textarea
                      id="intake"
                      placeholder="Example: We are the Robotics Club at State University. Our mission is to compete in FIRST and host outreach workshops for local high schools. We need funding for parts, travel, and venue space for our annual showcase..."
                      value={rawText}
                      onChange={(e) => setRawText(e.target.value)}
                      className="min-h-[200px] resize-y"
                    />
                    <p className="text-xs text-muted-foreground">
                      {rawText.trim().length}/∞ characters (minimum 10 for AI analysis)
                    </p>
                  </div>
                  <Button
                    type="button"
                    disabled={!canSubmitIntake}
                    onClick={() => void runAnalysis()}
                    className="w-full sm:w-auto"
                  >
                    Continue
                  </Button>
                </CardContent>
              </Card>
            </motion.section>
          )}

          {step === 2 && (
            <motion.section
              key="step2"
              variants={slide}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={transition}
              className="flex flex-col items-center justify-center py-16"
            >
              <div className="relative mb-10">
                <motion.div
                  className="h-32 w-32 rounded-full bg-gradient-to-tr from-primary/30 via-primary/10 to-transparent blur-2xl"
                  animate={{ scale: [1, 1.08, 1], opacity: [0.7, 1, 0.7] }}
                  transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="flex h-20 w-20 items-center justify-center rounded-2xl border border-primary/20 bg-background/90 shadow-lg backdrop-blur">
                    <Loader2 className="h-9 w-9 animate-spin text-primary" />
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 text-lg font-medium">
                <Sparkles className="h-5 w-5 text-primary" />
                AI analyzing your club
              </div>
              <p className="mt-2 max-w-md text-center text-sm text-muted-foreground">
                {analyzePhase === "profile"
                  ? "Structuring your club profile from your notes…"
                  : "Matching sponsors with vector similarity…"}
              </p>
              <div className="mt-8 flex gap-2">
                <span
                  className={cn(
                    "h-2 w-12 rounded-full transition-colors",
                    analyzePhase === "profile" ? "bg-primary" : "bg-primary/30"
                  )}
                />
                <span
                  className={cn(
                    "h-2 w-12 rounded-full transition-colors",
                    analyzePhase === "match" ? "bg-primary" : "bg-muted"
                  )}
                />
              </div>
            </motion.section>
          )}

          {step === 3 && matches && (
            <motion.section
              key="step3"
              variants={slide}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={transition}
              className="space-y-6"
            >
              <div>
                <h2 className="text-xl font-semibold">Sponsor matches</h2>
                <p className="text-sm text-muted-foreground">
                  Ranked by semantic fit. Select a sponsor to build event ideas and
                  outreach.
                </p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                {matches.map((m) => {
                  const pct = scoreToPercent(m.score);
                  const selected = selectedMatch?.sponsorId === m.sponsorId;
                  return (
                    <motion.button
                      key={m.sponsorId}
                      type="button"
                      layout
                      whileHover={{ y: -2 }}
                      whileTap={{ scale: 0.99 }}
                      onClick={() => setSelectedMatch(m)}
                      className={cn(
                        "text-left rounded-xl border p-5 transition-shadow",
                        selected
                          ? "border-primary ring-2 ring-primary/30 shadow-md"
                          : "border-border hover:border-primary/40"
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold">{m.sponsorName}</p>
                          <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                            {m.description || m.mission}
                          </p>
                        </div>
                        <div className="flex shrink-0 flex-col items-end">
                          <span className="rounded-full bg-primary/10 px-2.5 py-px text-xs font-semibold text-primary">
                            {pct}%
                          </span>
                          <span className="mt-1 text-[10px] text-muted-foreground">
                            match score
                          </span>
                        </div>
                      </div>
                      <div className="mt-4 h-px w-full bg-border" />
                      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-muted">
                        <motion.div
                          className="h-full rounded-full bg-primary"
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                        />
                      </div>
                    </motion.button>
                  );
                })}
              </div>
              {matches.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No sponsors with embeddings yet. Run the seed script on the backend
                  and try again.
                </p>
              )}
              <div className="flex flex-wrap gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setStep(1)}
                >
                  Back
                </Button>
                <Button
                  type="button"
                  disabled={!selectedMatch}
                  onClick={() => {
                    setIdeaIndex(0);
                    setEventIdeas(null);
                    setEmailPitch(null);
                    setStep(4);
                  }}
                >
                  Continue with selected sponsor
                </Button>
              </div>
            </motion.section>
          )}

          {step === 4 && (
            <motion.section
              key="step4"
              variants={slide}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={transition}
              className="space-y-6"
            >
              <div>
                <h2 className="text-xl font-semibold">Event ideas & email</h2>
                <p className="text-sm text-muted-foreground">
                  Three AI-generated ideas for{" "}
                  <span className="font-medium text-foreground">
                    {selectedMatch?.sponsorName}
                  </span>
                  , plus a tailored pitch draft.
                </p>
              </div>

              {strategiesLoading && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating event strategies…
                </div>
              )}

              {!strategiesLoading && eventIdeas && (
                <div className="flex flex-wrap gap-2">
                  {eventIdeas.map((idea, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setIdeaIndex(i)}
                      className={cn(
                        "rounded-full border px-4 py-2 text-sm font-medium transition-colors",
                        ideaIndex === i
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border hover:border-primary/40"
                      )}
                    >
                      Idea {i + 1}
                    </button>
                  ))}
                </div>
              )}

              {!strategiesLoading && eventIdeas && eventIdeas[ideaIndex] && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">
                      {eventIdeas[ideaIndex].title}
                    </CardTitle>
                    <CardDescription>
                      {eventIdeas[ideaIndex].summary}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm text-muted-foreground">
                    <p>{eventIdeas[ideaIndex].rationale}</p>
                    {eventIdeas[ideaIndex].supportRequested?.length ? (
                      <p className="pt-2">
                        <span className="font-medium text-foreground">
                          Support requested:{" "}
                        </span>
                        {eventIdeas[ideaIndex].supportRequested.join(", ")}
                      </p>
                    ) : null}
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardHeader className="flex flex-row items-center gap-2 space-y-0">
                  <Mail className="h-5 w-5 text-primary" />
                  <div>
                    <CardTitle className="text-base">Email preview</CardTitle>
                    <CardDescription>
                      Professional student-leader tone (generated draft)
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {emailLoading && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Updating email for this idea…
                    </div>
                  )}
                  {!emailLoading && emailPitch && (
                    <>
                      <div>
                        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                          Subject
                        </p>
                        <p className="mt-1 font-medium">{emailPitch.subject}</p>
                      </div>
                      <div>
                        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                          Body
                        </p>
                        <pre className="mt-2 max-h-[320px] overflow-auto whitespace-pre-wrap rounded-lg border bg-muted/30 p-4 text-sm leading-relaxed">
                          {emailPitch.body}
                        </pre>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>

              <div className="flex flex-wrap gap-3">
                <Button type="button" variant="outline" onClick={() => setStep(3)}>
                  Back
                </Button>
                <Button
                  type="button"
                  disabled={!eventIdeas?.length || emailLoading}
                  onClick={() => setStep(5)}
                >
                  Continue
                </Button>
              </div>
            </motion.section>
          )}

          {step === 5 && (
            <motion.section
              key="step5"
              variants={slide}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={transition}
              className="space-y-6"
            >
              <Card className="overflow-hidden border-primary/20">
                <div className="bg-gradient-to-r from-primary/10 to-transparent px-6 py-8">
                  <PartyPopper className="mb-3 h-10 w-10 text-primary" />
                  <CardTitle className="text-2xl">Ready to publish</CardTitle>
                  <CardDescription className="mt-2 max-w-lg text-base">
                    Create your event on Luma to share registration, calendar
                    invites, and reminders—then send your outreach with the draft
                    above.
                  </CardDescription>
                </div>
                <CardContent className="pb-8">
                  <a
                    href={LUMA_CREATE_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex"
                  >
                    <Button type="button" size="lg" className="gap-2">
                      Create on Luma
                      <span aria-hidden>↗</span>
                    </Button>
                  </a>
                  <p className="mt-4 text-xs text-muted-foreground">
                    Opens luma.com in a new tab. You can paste your event title and
                    details from the ideas above.
                  </p>
                </CardContent>
              </Card>
              <Button type="button" variant="outline" onClick={() => setStep(4)}>
                Back
              </Button>
            </motion.section>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
