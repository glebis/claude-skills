#!/usr/bin/env node
import path from 'path';
import { promises as fs } from 'fs';
import { processTranscript } from '@/lib/extract-service';
import {
  buildFullDocument
} from '@/lib/markdown';
import { Extraction, GlossaryTerm } from '@/types';

interface CLIOptions {
  file?: string;
  glossaryPath?: string;
  skipGlossary?: boolean;
  includeTranscript?: boolean;
  noExtractions?: boolean;
  noGlossary?: boolean;
  output?: string;
  maxTerms?: number;
  chunkSize?: number;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));

  if (!options.file) {
    printHelp();
    process.exit(1);
  }

  console.log('📄 Reading transcript...');
  const transcriptPath = path.resolve(options.file);
  const transcript = await fs.readFile(transcriptPath, 'utf-8');
  console.log(`   Loaded ${transcript.length} characters`);

  console.log('📚 Loading glossary...');
  const glossary = await loadGlossary(options);
  console.log(`   Found ${glossary.length} existing terms`);

  console.log('🤖 Processing transcript with AI...');
  const result = await processTranscript({
    transcript,
    glossary,
    chunkSize: options.chunkSize,
    maxTerms: options.maxTerms
  });

  console.log(`✓ Processing complete`);
  console.log(`   Chunks: ${result.stats.chunks}`);
  console.log(`   Extractions: ${result.stats.totalExtractions}`);
  console.log(`   New terms: ${result.stats.newTerms}`);
  if (result.stats.inputTokens && result.stats.outputTokens) {
    console.log(`   Tokens: ${result.stats.inputTokens + result.stats.outputTokens} total`);
  }

  console.log('📝 Building markdown document...');
  const markdown = buildFullDocument({
    transcript,
    extractions: result.extractions,
    glossaryTerms: glossary,
    suggestedTerms: result.suggestedTerms,
    stats: result.stats,
    includeTranscript: options.includeTranscript,
    includeExtractions: !options.noExtractions,
    includeGlossary: !options.noGlossary
  });

  if (options.output) {
    const outputPath = path.resolve(options.output);
    await fs.writeFile(outputPath, markdown, 'utf-8');
    console.log(`✓ Exported to ${outputPath}`);
  } else {
    console.log(markdown);
  }
}

function parseArgs(argv: string[]): CLIOptions {
  const options: CLIOptions = {};
  const args = [...argv];

  while (args.length > 0) {
    const arg = args.shift()!;

    if (!arg.startsWith('-') && !options.file) {
      options.file = arg;
      continue;
    }

    switch (arg) {
      case '--file':
      case '-f':
        options.file = args.shift();
        break;
      case '--glossary':
        options.glossaryPath = args.shift();
        break;
      case '--skip-glossary':
        options.skipGlossary = true;
        break;
      case '--include-transcript':
        options.includeTranscript = true;
        break;
      case '--no-extractions':
        options.noExtractions = true;
        break;
      case '--no-glossary':
        options.noGlossary = true;
        break;
      case '--output':
      case '-o':
        options.output = args.shift();
        break;
      case '--max-terms':
        options.maxTerms = Number(args.shift());
        break;
      case '--chunk-size':
        options.chunkSize = Number(args.shift());
        break;
      case '--help':
      case '-h':
        printHelp();
        process.exit(0);
      default:
        if (!options.file) {
          options.file = arg;
        }
        break;
    }
  }

  return options;
}

async function loadGlossary(options: CLIOptions): Promise<GlossaryTerm[]> {
  if (options.skipGlossary) return [];

  const defaultPath = path.join(process.cwd(), 'data', 'glossary.json');
  const target = options.glossaryPath
    ? path.resolve(options.glossaryPath)
    : defaultPath;

  try {
    const data = await fs.readFile(target, 'utf-8');
    return JSON.parse(data);
  } catch {
    return [];
  }
}

function printHelp() {
  console.log(`Usage: npm run cli -- <transcript.txt> -o <output.md> [options]

Outputs a Markdown document with metadata, extractions, and glossary.

Options:
  <file>               Transcript file to analyze (first positional arg)
  -o, --output <path>  Write markdown to a file instead of stdout
  --glossary <path>    Path to glossary JSON (defaults to data/glossary.json)
  --skip-glossary      Do not preload glossary terms
  --include-transcript Include full transcript in output [default: off]
  --no-extractions     Exclude extractions section from output
  --no-glossary        Exclude glossary section from output
  --max-terms <num>    Maximum glossary suggestions
  --chunk-size <num>   Override chunk size for processing
  -h, --help           Show this help message

Examples:
  npm run cli -- transcript.txt -o output.md
  npm run cli -- transcript.txt -o output.md --include-transcript
  npm run cli -- transcript.txt --no-glossary -o output.md

Output includes:
  - YAML frontmatter with processing metadata (chunks, tokens, model)
  - Full transcript [default: off, use --include-transcript]
  - Extractions (decisions, actions, opinions, questions, terms) [default: on]
  - Glossary terms (approved + suggested) [default: on]
`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
