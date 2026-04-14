"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2, Sparkles, Mail, PartyPopper } from "lucide-react";
import { SponsorMatchMark } from "@/components/brand/SponsorMatchMark";
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

/** Bold, readable inputs */
const fieldClass =
  "w-full rounded-xl border-2 border-input bg-background/80 px-3 py-2.5 text-sm transition-[border-color,box-shadow] placeholder:text-muted-foreground focus-visible:outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20";

function scoreToPercent(score: number): number {
  return Math.round(Math.min(100, Math.max(0, score * 100)));
}

interface PastEvent {
  name: string;
  description: string;
  attendees: string;
}

const EMPTY_EVENT: PastEvent = { name: "", description: "", attendees: "" };

export function SponsorshipWizard() {
  const [step, setStep] = useState(1);
  const [clubName, setClubName] = useState("");
  const [clubMission, setClubMission] = useState("");
  const [university, setUniversity] = useState("");
  const [memberCount, setMemberCount] = useState("");
  const [pastEvents, setPastEvents] = useState<PastEvent[]>([
    { ...EMPTY_EVENT }, { ...EMPTY_EVENT }, { ...EMPTY_EVENT },
  ]);
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

  function buildRawText(): string {
    const lines: string[] = [];
    lines.push(`Club Name: ${clubName.trim()}`);
    lines.push(`Mission: ${clubMission.trim()}`);
    lines.push(`University / Location: ${university.trim()}`);
    if (memberCount.trim()) lines.push(`Number of Members: ${memberCount.trim()}`);
    const filledEvents = pastEvents.filter((e) => e.name.trim());
    if (filledEvents.length > 0) {
      lines.push("\nPast Events:");
      filledEvents.forEach((e, i) => {
        lines.push(`  Event ${i + 1}: ${e.name.trim()}`);
        if (e.description.trim()) lines.push(`  Description: ${e.description.trim()}`);
        if (e.attendees.trim()) lines.push(`  Attendees: ${e.attendees.trim()}`);
      });
    }
    return lines.join("\n");
  }

  const runAnalysis = useCallback(async () => {
    setError(null);
    setStep(2);
    setAnalyzePhase("profile");
    const composed = buildRawText();
    try {
      const profile = await parseClubProfile(composed);
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
  }, [clubName, clubMission, university, memberCount, pastEvents]);

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

  const canSubmitIntake = clubName.trim().length > 0 && clubMission.trim().length > 0 && university.trim().length > 0;

  function updatePastEvent(index: number, field: keyof PastEvent, value: string) {
    setPastEvents((prev) => prev.map((e, i) => (i === index ? { ...e, [field]: value } : e)));
  }

  return (
    <div className="relative mx-auto flex min-h-screen max-w-5xl flex-col px-4 pb-20 pt-8 md:px-10">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-2 bg-gradient-to-r from-primary via-secondary to-[hsl(320_90%_60%)] opacity-90"
      />

      <header className="mb-10 md:mb-12">
        <div className="inline-flex items-center gap-2 rounded-full border-2 border-primary/25 bg-secondary/90 px-3 py-1.5 text-xs font-bold uppercase tracking-wider text-secondary-foreground shadow-sm">
          <SponsorMatchMark size="sm" alt="" className="opacity-90" />
          Club → sponsors → event → Luma
        </div>
        <h1 className="font-display mt-4 max-w-3xl text-4xl font-bold leading-[1.1] tracking-tight md:text-5xl">
          <span className="text-gradient">From pitch</span>
          <span className="text-foreground"> to partners</span>
        </h1>
        <p className="mt-3 max-w-2xl text-base text-muted-foreground md:text-lg">
          Clear steps from intake to outreach. Tell us about your club—we&apos;ll
          handle the match flow.
        </p>

        <ol className="mt-8 flex flex-wrap gap-2.5 md:gap-3">
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
                    "flex items-center gap-2 rounded-full border-2 px-3.5 py-2 text-xs font-semibold transition-all md:text-sm",
                    active &&
                      "border-primary bg-primary text-primary-foreground shadow-md shadow-primary/30",
                    done && !active && "border-primary/30 bg-primary/10 text-primary",
                    !active && !done && "border-dashed border-border text-muted-foreground/80",
                    n < step && "cursor-pointer hover:-translate-y-0.5 hover:border-primary/60"
                  )}
                >
                  <span
                    className={cn(
                      "flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold",
                      active && "bg-primary-foreground/20 text-primary-foreground",
                      done && !active && "bg-primary text-primary-foreground",
                      !active && !done && "bg-muted text-muted-foreground"
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
        <div className="mb-6 rounded-2xl border-2 border-destructive/50 bg-destructive/10 px-4 py-3 text-sm font-medium text-destructive shadow-sm">
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
                  <CardTitle className="font-display text-2xl font-bold">
                    Club intake
                  </CardTitle>
                  <CardDescription className="text-base">
                    The more real detail you add—especially past events—the sharper
                    your sponsor fit.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                  <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-foreground">Club information</h3>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-1.5">
                        <label htmlFor="clubName" className="text-sm font-medium">Club name <span className="text-destructive">*</span></label>
                        <input
                          id="clubName"
                          type="text"
                          placeholder="e.g. Robotics Club"
                          value={clubName}
                          onChange={(e) => setClubName(e.target.value)}
                          className={fieldClass}
                        />
                      </div>
                      <div className="space-y-1.5">
                        <label htmlFor="university" className="text-sm font-medium">University / location <span className="text-destructive">*</span></label>
                        <input
                          id="university"
                          type="text"
                          placeholder="e.g. State University, Boston"
                          value={university}
                          onChange={(e) => setUniversity(e.target.value)}
                          className={fieldClass}
                        />
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <label htmlFor="clubMission" className="text-sm font-medium">Club mission <span className="text-destructive">*</span></label>
                      <Textarea
                        id="clubMission"
                        placeholder="1–2 sentences describing your club's purpose and goals. e.g. We compete in FIRST Robotics and run outreach workshops for local high schools."
                        value={clubMission}
                        onChange={(e) => setClubMission(e.target.value)}
                        className="min-h-[80px] resize-y"
                      />
                    </div>
                    <div className="space-y-1.5 sm:w-1/2">
                      <label htmlFor="memberCount" className="text-sm font-medium">Number of members</label>
                      <input
                        id="memberCount"
                        type="number"
                        min="1"
                        placeholder="e.g. 45"
                        value={memberCount}
                        onChange={(e) => setMemberCount(e.target.value)}
                        className={fieldClass}
                      />
                    </div>
                  </div>

                  <div className="space-y-4 border-t pt-5">
                    <div>
                      <h3 className="text-sm font-semibold text-foreground">Past events</h3>
                      <p className="mt-0.5 text-xs text-muted-foreground">Up to 3 previous events. Used to inform sponsor matching and avoid duplicate ideas.</p>
                    </div>
                    {pastEvents.map((event, i) => (
                      <div
                        key={i}
                        className="space-y-3 rounded-2xl border-2 border-primary/15 bg-gradient-to-br from-muted/40 to-background p-4 shadow-sm"
                      >
                        <p className="text-xs font-bold uppercase tracking-wide text-primary/80">
                          Event {i + 1}
                        </p>
                        <div className="space-y-1.5">
                          <label className="text-sm font-medium">Event name</label>
                          <input
                            type="text"
                            placeholder="e.g. Spring Robotics Showcase"
                            value={event.name}
                            onChange={(e) => updatePastEvent(i, "name", e.target.value)}
                            className={fieldClass}
                          />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-sm font-medium">Event description</label>
                          <Textarea
                            placeholder="Briefly describe what happened at this event."
                            value={event.description}
                            onChange={(e) => updatePastEvent(i, "description", e.target.value)}
                            className="min-h-[64px] resize-y"
                          />
                        </div>
                        <div className="space-y-1.5 sm:w-1/3">
                          <label className="text-sm font-medium">Number of attendees</label>
                          <input
                            type="number"
                            min="1"
                            placeholder="e.g. 120"
                            value={event.attendees}
                            onChange={(e) => updatePastEvent(i, "attendees", e.target.value)}
                            className={fieldClass}
                          />
                        </div>
                      </div>
                    ))}
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
              <div className="flex items-center gap-2 font-display text-xl font-bold md:text-2xl">
                <Sparkles className="h-6 w-6 text-primary" />
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
                <h2 className="font-display text-2xl font-bold tracking-tight md:text-3xl">
                  Sponsor matches
                </h2>
                <p className="mt-1 text-sm text-muted-foreground md:text-base">
                  Ranked by fit. Pick one—we&apos;ll spin up ideas + email for that
                  partner.
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
                        "text-left rounded-2xl border-2 bg-background/60 p-5 transition-all hover:-translate-y-0.5",
                        selected
                          ? "border-primary shadow-lg shadow-primary/20 ring-2 ring-primary/25"
                          : "border-border/80 hover:border-primary/50 hover:shadow-md"
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
                <h2 className="font-display text-2xl font-bold tracking-tight md:text-3xl">
                  Event ideas &amp; email
                </h2>
                <p className="mt-1 text-sm text-muted-foreground md:text-base">
                  Three angles for{" "}
                  <span className="font-semibold text-primary">
                    {selectedMatch?.sponsorName}
                  </span>{" "}
                  — plus a draft you can send as-is or tweak.
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
              <Card className="overflow-hidden border-2 border-primary/25">
                <div className="bg-gradient-to-br from-primary/15 via-secondary/30 to-transparent px-6 py-8">
                  <PartyPopper className="mb-3 h-10 w-10 text-primary" />
                  <CardTitle className="font-display text-2xl md:text-3xl">
                    Ready to publish
                  </CardTitle>
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
