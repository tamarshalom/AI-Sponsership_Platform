import type {
  ClubProfile,
  EmailAgentRequest,
  EmailPitchResponse,
  EventStrategyAgentRequest,
  EventStrategyAgentResponse,
  MatchSponsorsResponse,
  MatchSponsorsResult,
  SponsorBrief,
} from "@shared/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api/backend";

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export async function parseClubProfile(rawText: string): Promise<ClubProfile> {
  return jsonFetch("/agents/profile/parse", {
    method: "POST",
    body: JSON.stringify({ rawText }),
  });
}

export async function matchSponsors(
  club: ClubProfile
): Promise<MatchSponsorsResponse> {
  return jsonFetch("/match-sponsors", {
    method: "POST",
    body: JSON.stringify(club),
  });
}

export async function fetchEventStrategies(
  club: ClubProfile,
  sponsor: SponsorBrief
): Promise<EventStrategyAgentResponse> {
  const body: EventStrategyAgentRequest = { club, sponsor };
  return jsonFetch("/agents/event-strategy", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function fetchEmailPitch(
  payload: EmailAgentRequest
): Promise<EmailPitchResponse> {
  return jsonFetch("/agents/email-pitch", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function matchToSponsorBrief(m: MatchSponsorsResult): SponsorBrief {
  return {
    id: m.sponsorId,
    name: m.sponsorName,
    mission: m.mission,
    description: m.description,
    industries: [],
    supportTypes: [],
  };
}
