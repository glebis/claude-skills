export type ExtractionType = 'decision' | 'action' | 'opinion' | 'question' | 'term';

export interface Extraction {
  id: string;
  type: ExtractionType;
  content: string;
  confidence: number; // 0-100
  speaker?: string;
  sourceSnippet: string;
  sourceTimestamp?: string;
  relatedTerms?: string[];
}

export interface GlossaryTerm {
  id: string;
  term: string;
  definition: string;
  aliases: string[];
  firstMentioned: string; // meeting ID
  frequency: number;
  approved: boolean;
}

export interface TranscriptMeeting {
  id: string;
  title: string;
  date: string;
  filePath: string;
  extractions: Extraction[];
  suggestedTerms: GlossaryTerm[];
}

export interface ProcessingResult {
  meeting: TranscriptMeeting;
  glossaryUpdates: GlossaryTerm[];
}

export interface ProcessingStats {
  chunks: number;
  totalExtractions: number;
  byType: Record<string, number>;
  newTerms: number;
  mode: 'live' | 'mock';
  inputTokens?: number;
  outputTokens?: number;
  model?: string;
}
