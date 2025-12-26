export function normalizeTermKey(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')
    .trim();
}

export function areTermsEquivalent(a: string, b: string): boolean {
  const normA = normalizeTermKey(a);
  const normB = normalizeTermKey(b);

  if (!normA || !normB) return false;
  if (normA === normB) return true;

  return levenshtein(normA, normB) <= 2;
}

function levenshtein(a: string, b: string): number {
  const aLen = a.length;
  const bLen = b.length;

  if (aLen === 0) return bLen;
  if (bLen === 0) return aLen;

  const prev = new Array(bLen + 1).fill(0);
  const curr = new Array(bLen + 1).fill(0);

  for (let j = 0; j <= bLen; j++) {
    prev[j] = j;
  }

  for (let i = 1; i <= aLen; i++) {
    curr[0] = i;

    for (let j = 1; j <= bLen; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      curr[j] = Math.min(
        prev[j] + 1,
        curr[j - 1] + 1,
        prev[j - 1] + cost
      );
    }

    for (let j = 0; j <= bLen; j++) {
      prev[j] = curr[j];
    }
  }

  return curr[bLen];
}
