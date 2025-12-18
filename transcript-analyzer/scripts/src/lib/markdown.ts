import { Extraction, GlossaryTerm, ProcessingStats } from '@/types';

export function buildExtractionsMarkdown(extractions: Extraction[]): string {
  if (extractions.length === 0) {
    return '# Extractions\n\nNo extractions available.';
  }

  const grouped = extractions.reduce<Record<string, Extraction[]>>((acc, extraction) => {
    const key = extraction.type;
    acc[key] = acc[key] || [];
    acc[key].push(extraction);
    return acc;
  }, {});

  const sections = Object.entries(grouped)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([type, items]) => {
      const header = `## ${capitalize(type)}`;
      const body = items
        .map((item, idx) => {
          const speaker = item.speaker ? `**Speaker:** ${item.speaker}\n` : '';
          const terms = item.relatedTerms && item.relatedTerms.length > 0
            ? `**Related Terms:** ${item.relatedTerms.join(', ')}\n`
            : '';
          const source = item.sourceSnippet ? `> ${item.sourceSnippet}` : '';
          return `### ${idx + 1}. ${item.content}\n${speaker}${terms}**Confidence:** ${item.confidence}%\n${source}`;
        })
        .join('\n\n');
      return `${header}\n\n${body}`;
    });

  return ['# Extractions', ...sections].join('\n\n');
}

export function buildGlossaryMarkdown(
  approved: GlossaryTerm[],
  suggested: GlossaryTerm[] = []
): string {
  const approvedSection = approved.length > 0
    ? approved
        .map((term, idx) => formatTerm(idx + 1, term))
        .join('\n\n')
    : 'No approved terms available.';

  const suggestedSection = suggested.length > 0
    ? suggested
        .map((term, idx) => formatTerm(idx + 1, term))
        .join('\n\n')
    : 'No suggested terms available.';

  return [
    '# Glossary',
    '## Approved Terms',
    approvedSection,
    '## Suggested Terms',
    suggestedSection
  ].join('\n\n');
}

export function buildCombinedMarkdown(
  extractions: Extraction[],
  approved: GlossaryTerm[],
  suggested: GlossaryTerm[] = []
): string {
  const parts = [
    buildExtractionsMarkdown(extractions),
    buildGlossaryMarkdown(approved, suggested)
  ];
  return parts.join('\n\n---\n\n');
}

export interface FullDocumentOptions {
  transcript: string;
  extractions: Extraction[];
  glossaryTerms: GlossaryTerm[];
  suggestedTerms: GlossaryTerm[];
  stats: ProcessingStats;
  includeTranscript?: boolean;
  includeExtractions?: boolean;
  includeGlossary?: boolean;
}

export function buildFullDocument(options: FullDocumentOptions): string {
  const {
    transcript,
    extractions,
    glossaryTerms,
    suggestedTerms,
    stats,
    includeTranscript = false,
    includeExtractions = true,
    includeGlossary = true
  } = options;

  const parts: string[] = [];

  // Metadata section
  parts.push(buildMetadataSection(stats));

  // Optional transcript section
  if (includeTranscript) {
    parts.push('# Transcript\n\n' + transcript);
  }

  // Optional extractions section
  if (includeExtractions && extractions.length > 0) {
    parts.push(buildExtractionsMarkdown(extractions));
  }

  // Optional glossary section
  if (includeGlossary && (glossaryTerms.length > 0 || suggestedTerms.length > 0)) {
    parts.push(buildGlossaryMarkdown(glossaryTerms, suggestedTerms));
  }

  return parts.join('\n\n---\n\n');
}

function buildMetadataSection(stats: ProcessingStats): string {
  const lines = [
    '---',
    `chunks: ${stats.chunks}`,
    `extractions: ${stats.totalExtractions}`,
    `new_terms: ${stats.newTerms}`,
    `mode: ${stats.mode}`
  ];

  if (stats.model) {
    lines.push(`model: ${stats.model}`);
  }

  if (stats.inputTokens !== undefined) {
    lines.push(`input_tokens: ${stats.inputTokens}`);
  }

  if (stats.outputTokens !== undefined) {
    lines.push(`output_tokens: ${stats.outputTokens}`);
  }

  if (stats.inputTokens && stats.outputTokens) {
    lines.push(`total_tokens: ${stats.inputTokens + stats.outputTokens}`);
  }

  const typeBreakdown = Object.entries(stats.byType)
    .map(([type, count]) => `  ${type}: ${count}`)
    .join('\n');

  if (typeBreakdown) {
    lines.push(`extractions_by_type:\n${typeBreakdown}`);
  }

  lines.push('---');

  return lines.join('\n');
}

function formatTerm(index: number, term: GlossaryTerm) {
  const aliases = term.aliases && term.aliases.length > 0
    ? `**Aliases:** ${term.aliases.join(', ')}\n`
    : '';
  return `### ${index}. ${term.term}\n${term.definition}\n\n${aliases}**First Mentioned:** ${term.firstMentioned || 'n/a'}\n**Frequency:** ${term.frequency}`;
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
