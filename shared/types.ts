export interface ClubProfile {
  id: string;
  name: string;
  mission: string;
  description?: string;
  university: string;
  websiteUrl?: string;
  socialLinks?: Record<string, string>;
  contactEmail: string;
  eboardAvailability: Record<string, unknown>;
  preferredIndustries: string[];
  requestedSupportTypes: string[];
  memberCount?: number;
  budgetGoalCents?: number;
  createdAt: string;
  updatedAt: string;
}

export interface Sponsor {
  id: string;
  name: string;
  mission: string;
  description?: string;
  industries: string[];
  supportTypes: string[];
  budgetMinCents?: number;
  budgetMaxCents?: number;
  contactName?: string;
  contactEmail?: string;
  websiteUrl?: string;
  locations?: string[];
  metadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface EventSuggestion {
  id: string;
  clubId: string;
  sponsorId: string;
  title: string;
  summary: string;
  rationale: string;
  proposedDate?: string;
  estimatedAttendees?: number;
  supportRequested: string[];
  sponsorMatchScore: number;
  sponsorMatchBreakdown: Record<string, number>;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface OutreachDraft {
  id: string;
  clubId: string;
  sponsorId: string;
  eventSuggestionId?: string;
  subject: string;
  body: string;
  personalizationTokens?: Record<string, string>;
  status: "draft" | "ready" | "sent";
  reviewerNotes?: string;
  scheduledSendAt?: string;
  createdAt: string;
  updatedAt: string;
}

/** Minimal sponsor context for LLM agents (match result or full Sponsor). */
export interface SponsorBrief {
  id: string;
  name: string;
  mission: string;
  description?: string;
  industries?: string[];
  supportTypes?: string[];
}

/** One proposed event from EventStrategyAgent (before persisting as EventSuggestion). */
export interface EventStrategyIdea {
  title: string;
  summary: string;
  rationale: string;
  estimatedAttendees?: number;
  supportRequested: string[];
  tags?: string[];
}

export interface EventStrategyAgentResponse {
  ideas: [EventStrategyIdea, EventStrategyIdea, EventStrategyIdea];
}

export interface EventStrategyAgentRequest {
  club: ClubProfile;
  sponsor: SponsorBrief;
}

export interface EmailPitchResponse {
  subject: string;
  body: string;
}

export interface EmailAgentRequest {
  club: ClubProfile;
  sponsor: SponsorBrief;
  eventIdea: EventStrategyIdea;
}

export interface MatchSponsorsResult {
  sponsorId: string;
  sponsorName: string;
  mission: string;
  description?: string;
  score: number;
}

export interface MatchSponsorsResponse {
  matches: MatchSponsorsResult[];
}
