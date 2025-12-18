import { Extraction, ExtractionType, GlossaryTerm } from '@/types';
import { areTermsEquivalent, normalizeTermKey } from './term-utils';

export function mockProcessTranscript(
  transcript: string,
  glossary: GlossaryTerm[],
  maxTerms?: number
) {
  const sentences = splitTranscript(transcript);
  const extracted: Extraction[] = [];

  sentences.forEach((sentence, idx) => {
    const parsed = classifySentence(sentence, glossary, idx);
    if (parsed) {
      extracted.push(parsed);
    }
  });

  const suggestedTerms = buildGlossarySuggestions(transcript, glossary, maxTerms);

  return {
    extractions: extracted,
    suggestedTerms
  };
}

function splitTranscript(transcript: string): string[] {
  return transcript
    .split(/\n+|(?<=[.!?])\s+/)
    .map(part => part.trim())
    .filter(Boolean);
}

function classifySentence(
  sentence: string,
  glossary: GlossaryTerm[],
  index: number
): Extraction | null {
  let working = sentence;
  let speaker: string | undefined;

  const speakerMatch = working.match(/^([A-Za-z][A-Za-z\s]{1,30}):\s*(.+)$/);
  if (speakerMatch) {
    speaker = speakerMatch[1].trim();
    working = speakerMatch[2].trim();
  }

  const lowered = working.toLowerCase();

  let type: ExtractionType | null = null;
  let confidence = 65;

  if (/[?？]$/.test(working)) {
    type = 'question';
    confidence = 90;
  } else if (/\b(decision|decide|agreed|agreement|approve)\b/.test(lowered)) {
    type = 'decision';
    confidence = 80;
  } else if (/\b(action item|follow up|will|need to|let's|assign|task)\b/.test(lowered)) {
    type = 'action';
    confidence = 78;
  } else if (/\b(i think|i believe|feels like|i guess|should)\b/.test(lowered)) {
    type = 'opinion';
    confidence = 70;
  }

  if (!type) {
    return null;
  }

  const related = glossary
    .filter(term => containsTerm(lowered, term.term))
    .map(term => term.term);

  return {
    id: `mock-ext-${index}`,
    type,
    content: working,
    confidence,
    speaker,
    sourceSnippet: working.slice(0, 200),
    relatedTerms: related
  };
}

function containsTerm(content: string, term: string) {
  return content.includes(term.toLowerCase());
}

export function buildGlossarySuggestions(
  transcript: string,
  glossary: GlossaryTerm[],
  maxTerms?: number
): GlossaryTerm[] {
  const existingLabels: string[] = [];
  glossary.forEach(term => {
    existingLabels.push(term.term);
    term.aliases?.forEach(alias => existingLabels.push(alias));
  });

  const tokens = transcript.match(/\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)?\b/g) || [];
  const aggregates: { label: string; count: number }[] = [];

  tokens.forEach(token => {
    const normalized = token.trim();
    if (normalized.length < 3) return;
    if (!normalizeTermKey(normalized)) return;

    if (existingLabels.some(label => areTermsEquivalent(label, normalized))) {
      return;
    }

    const entry = aggregates.find(item => areTermsEquivalent(item.label, normalized));
    if (entry) {
      entry.count += 1;
    } else {
      aggregates.push({ label: normalized, count: 1 });
    }
  });

  const sorted = aggregates.sort((a, b) => b.count - a.count);
  const limit = typeof maxTerms === 'number' && maxTerms > 0 ? maxTerms : 5;

  return sorted.slice(0, limit).map((info, idx) => ({
    id: `mock-term-${idx}`,
    term: info.label,
    definition: deriveDefinition(info.label, transcript),
    aliases: [],
    firstMentioned: 'mock',
    frequency: info.count,
    approved: false
  }));
}

function deriveDefinition(term: string, transcript: string): string {
  const pattern = new RegExp(`[^.!?]*${escapeRegExp(term)}[^.!?]*[.!?]`, 'i');
  const match = transcript.match(pattern);
  if (match) {
    return match[0].trim();
  }
  return `Term mentioned in transcript context as "${term}".`;
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
