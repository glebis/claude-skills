import OpenAI from 'openai';
import { Extraction, ExtractionType, GlossaryTerm } from '@/types';
import { mockProcessTranscript } from './mockExtractor';
import { areTermsEquivalent } from './term-utils';

const cerebrasApiKey = process.env.CEREBRAS_API_KEY;
const cerebras = cerebrasApiKey ? new OpenAI({
  apiKey: cerebrasApiKey,
  baseURL: 'https://api.cerebras.ai/v1'
}) : null;
const forceMock = process.env.MOCK_TRANSCRIPT_PROCESSOR === 'true';

export interface ProcessTranscriptOptions {
  transcript: string;
  glossary?: GlossaryTerm[];
  chunkSize?: number;
  maxTerms?: number;
}

export async function processTranscript({
  transcript,
  glossary = [],
  chunkSize = 3000,
  maxTerms
}: ProcessTranscriptOptions) {
  if (!transcript) {
    throw new Error('Transcript required');
  }

  if (!cerebras || forceMock) {
    const mockResult = mockProcessTranscript(transcript, glossary, maxTerms);
    return {
      ...mockResult,
      stats: {
        chunks: 1,
        totalExtractions: mockResult.extractions.length,
        byType: countByType(mockResult.extractions),
        newTerms: mockResult.suggestedTerms.length,
        mode: 'mock' as const
      }
    };
  }

  const MODEL = 'llama-3.3-70b';
  const chunks = chunkTranscript(transcript, chunkSize);
  const allExtractions: Extraction[] = [];
  const suggestedTerms: GlossaryTerm[] = [];
  let totalInputTokens = 0;
  let totalOutputTokens = 0;

  console.log(`   Split into ${chunks.length} chunk${chunks.length > 1 ? 's' : ''}`);

  for (let i = 0; i < chunks.length; i++) {
    const chunk = chunks[i];
    console.log(`   Processing chunk ${i + 1}/${chunks.length}...`);

    const extractionResponse = await cerebras.chat.completions.create({
      model: MODEL,
      max_tokens: 4096,
      messages: [{
        role: 'user',
        content: buildExtractionPrompt(glossary, chunk, i + 1, chunks.length)
      }]
    });

    totalInputTokens += extractionResponse.usage?.prompt_tokens || 0;
    totalOutputTokens += extractionResponse.usage?.completion_tokens || 0;

    const extractionText = extractionResponse.choices[0]?.message?.content || '';

    const chunkExtractions = parseExtractions(extractionText, i);
    allExtractions.push(...chunkExtractions);
    console.log(`     → Found ${chunkExtractions.length} extractions`);

    const termResponse = await cerebras.chat.completions.create({
      model: MODEL,
      max_tokens: 2048,
      messages: [{
        role: 'user',
        content: buildTermPrompt(chunk)
      }]
    });

    totalInputTokens += termResponse.usage?.prompt_tokens || 0;
    totalOutputTokens += termResponse.usage?.completion_tokens || 0;

    const termText = termResponse.choices[0]?.message?.content || '';

    const chunkTerms = parseTerms(termText, i);
    suggestedTerms.push(...chunkTerms);
    console.log(`     → Found ${chunkTerms.length} terms`);
  }

  const mergedExtractions = deduplicateExtractions(allExtractions);
  const mergedTerms = limitTerms(deduplicateTerms(suggestedTerms, glossary), maxTerms);

  return {
    extractions: mergedExtractions,
    suggestedTerms: mergedTerms,
    stats: {
      chunks: chunks.length,
      totalExtractions: mergedExtractions.length,
      byType: countByType(mergedExtractions),
      newTerms: mergedTerms.length,
      mode: 'live' as const,
      model: MODEL,
      inputTokens: totalInputTokens,
      outputTokens: totalOutputTokens
    }
  };
}

function buildExtractionPrompt(
  glossary: GlossaryTerm[],
  chunk: string,
  index: number,
  total: number
) {
  return `You are analyzing a meeting transcript. Extract the following with confidence scores (0-100):

1. DECISIONS - explicit agreements or choices made (type: "decision")
2. ACTION ITEMS - tasks assigned to people (type: "action")
3. OPINIONS - viewpoints expressed but not agreed upon (type: "opinion")
4. QUESTIONS - unresolved questions raised (type: "question")
5. TERMS - domain-specific terminology that should be in a glossary (type: "term")

For each extraction, provide:
- type: one of decision/action/opinion/question/term
- content: the extracted content
- confidence: 0-100 score (how certain you are this is correctly classified)
- speaker: who said it (if identifiable)
- sourceSnippet: exact quote from transcript (max 200 chars)
- relatedTerms: any domain terms used

GLOSSARY CONTEXT (use these definitions, suggest new terms not in this list):
${formatGlossary(glossary)}

Return JSON array of extractions. Be conservative - only extract clear items with confidence > 60.

TRANSCRIPT CHUNK ${index}/${total}:
${chunk}`;
}

function buildTermPrompt(chunk: string) {
  return `Analyze this transcript chunk for domain-specific terminology that should be in a glossary.

For each term found:
- term: the term or phrase
- definition: inferred definition from context
- aliases: alternative ways it's referred to

Only include terms that are:
1. Domain-specific (not common words)
2. Used multiple times OR defined in context
3. Would help someone new understand the discussion

Return JSON array of terms.

TRANSCRIPT CHUNK:
${chunk}`;
}

function chunkTranscript(text: string, maxChars: number): string[] {
  const chunks: string[] = [];
  const lines = text.split('\n');
  let currentChunk = '';

  for (const line of lines) {
    if (currentChunk.length + line.length > maxChars && currentChunk.length > 0) {
      chunks.push(currentChunk.trim());
      currentChunk = line;
    } else {
      currentChunk += '\n' + line;
    }
  }

  if (currentChunk.trim()) {
    chunks.push(currentChunk.trim());
  }

  return chunks;
}

function formatGlossary(terms: GlossaryTerm[]): string {
  if (terms.length === 0) return 'No existing glossary terms.';
  return terms.map(t => `- ${t.term}: ${t.definition}`).join('\n');
}

function parseExtractions(text: string, chunkIndex: number): Extraction[] {
  try {
    const jsonMatch = text.match(/\[[\s\S]*\]/);
    if (!jsonMatch) return [];

    const parsed = JSON.parse(jsonMatch[0]);
    return parsed.map((item: Record<string, unknown>, idx: number) => ({
      id: `ext-${chunkIndex}-${idx}`,
      type: (item.type as ExtractionType) || 'opinion',
      content: String(item.content || ''),
      confidence: Number(item.confidence) || 50,
      speaker: item.speaker ? String(item.speaker) : undefined,
      sourceSnippet: String(item.sourceSnippet || item.source_snippet || ''),
      relatedTerms: Array.isArray(item.relatedTerms) ? item.relatedTerms : []
    }));
  } catch {
    return [];
  }
}

function parseTerms(text: string, chunkIndex: number): GlossaryTerm[] {
  try {
    const jsonMatch = text.match(/\[[\s\S]*\]/);
    if (!jsonMatch) return [];

    const parsed = JSON.parse(jsonMatch[0]);
    return parsed.map((item: Record<string, unknown>, idx: number) => ({
      id: `term-${chunkIndex}-${idx}`,
      term: String(item.term || ''),
      definition: String(item.definition || ''),
      aliases: Array.isArray(item.aliases) ? item.aliases : [],
      firstMentioned: '',
      frequency: 1,
      approved: false
    }));
  } catch {
    return [];
  }
}

function deduplicateExtractions(extractions: Extraction[]): Extraction[] {
  const seen = new Map<string, Extraction>();

  for (const ext of extractions) {
    const key = `${ext.type}-${ext.content.toLowerCase().slice(0, 50)}`;
    const existing = seen.get(key);

    if (!existing || ext.confidence > existing.confidence) {
      seen.set(key, ext);
    }
  }

  return Array.from(seen.values()).sort((a, b) => b.confidence - a.confidence);
}

function deduplicateTerms(terms: GlossaryTerm[], existingGlossary: GlossaryTerm[]): GlossaryTerm[] {
  const seenLabels: string[] = [];
  existingGlossary.forEach(term => {
    seenLabels.push(term.term);
    term.aliases?.forEach(alias => seenLabels.push(alias));
  });

  const deduped: GlossaryTerm[] = [];

  for (const term of terms) {
    if (!term.term?.trim()) continue;

    if (seenLabels.some(label => areTermsEquivalent(label, term.term))) {
      continue;
    }

    term.frequency = term.frequency ?? 1;

    const existing = deduped.find(t => areTermsEquivalent(t.term, term.term));
    if (existing) {
      existing.frequency += term.frequency;
      continue;
    }

    deduped.push(term);
    seenLabels.push(term.term);
    term.aliases?.forEach(alias => seenLabels.push(alias));
  }

  return deduped.sort((a, b) => b.frequency - a.frequency);
}

function countByType(extractions: Extraction[]): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const ext of extractions) {
    counts[ext.type] = (counts[ext.type] || 0) + 1;
  }
  return counts;
}

function limitTerms(terms: GlossaryTerm[], maxTerms?: number) {
  if (typeof maxTerms !== 'number' || maxTerms <= 0) {
    return terms;
  }
  return terms.slice(0, maxTerms);
}
