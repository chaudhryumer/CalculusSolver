import readline from "readline";
import { fileURLToPath } from "url";
import { dirname } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const serializerPath = new URL(
  "../tokenizer/slang_serializer.js",
  import.meta.url,
);
const {
  OPEN,
  CLOSE,
  SEP,
  NUMI,
  DENO,
  FRAC,
  TERM,
  serializeSlangMath,
  deserializeSlangMath,
} = await import(serializerPath);

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false,
});

function parseTerm(tokens, index) {
  if (index >= tokens.length) return { status: "incomplete" };
  if (tokens[index] !== TERM) return { status: "invalid" };
  index += 1;

  if (index >= tokens.length) return { status: "incomplete" };
  if (!tokens[index].startsWith("COEF:")) return { status: "invalid" };
  index += 1;

  while (index < tokens.length) {
    const token = tokens[index];
    if (token.startsWith("VAR:")) {
      index += 1;
      if (index >= tokens.length) return { status: "incomplete" };
      if (!tokens[index].startsWith("EXP:")) return { status: "invalid" };
      index += 1;
      continue;
    }
    break;
  }

  return { status: "complete", next: index };
}

function parseTermList(tokens, index) {
  if (index >= tokens.length) return { status: "incomplete" };
  if (tokens[index] === CLOSE) return { status: "complete", next: index };

  let current = index;
  while (true) {
    const node = parseNode(tokens, current);
    if (node.status === "invalid") return { status: "invalid" };
    if (node.status === "incomplete") return { status: "incomplete" };
    current = node.next;
    if (current >= tokens.length) return { status: "incomplete" };
    if (tokens[current] === SEP) {
      current += 1;
      continue;
    }
    if (tokens[current] === CLOSE) {
      return { status: "complete", next: current };
    }
    return { status: "invalid" };
  }
}

function parseFraction(tokens, index) {
  if (index >= tokens.length) return { status: "incomplete" };
  if (tokens[index] !== FRAC) return { status: "invalid" };
  index += 1;
  if (index >= tokens.length) return { status: "incomplete" };
  if (tokens[index] !== OPEN) return { status: "invalid" };
  index += 1;
  if (index >= tokens.length) return { status: "incomplete" };
  if (tokens[index] !== NUMI) return { status: "invalid" };
  index += 1;
  if (index >= tokens.length) return { status: "incomplete" };
  if (tokens[index] !== OPEN) return { status: "invalid" };
  index += 1;

  const numerator = parseTermList(tokens, index);
  if (numerator.status !== "complete") return numerator;
  index = numerator.next;
  if (index >= tokens.length) return { status: "incomplete" };
  if (tokens[index] !== CLOSE) return { status: "invalid" };
  index += 1;
  if (index >= tokens.length) return { status: "incomplete" };
  if (tokens[index] !== SEP) return { status: "invalid" };
  index += 1;
  if (index >= tokens.length) return { status: "incomplete" };
  if (tokens[index] !== DENO) return { status: "invalid" };
  index += 1;
  if (index >= tokens.length) return { status: "incomplete" };
  if (tokens[index] !== OPEN) return { status: "invalid" };
  index += 1;

  const denominator = parseTermList(tokens, index);
  if (denominator.status !== "complete") return denominator;
  index = denominator.next;
  if (index >= tokens.length) return { status: "incomplete" };
  if (tokens[index] !== CLOSE) return { status: "invalid" };
  index += 1;
  if (index >= tokens.length) return { status: "incomplete" };
  if (tokens[index] !== CLOSE) return { status: "invalid" };
  index += 1;

  return { status: "complete", next: index };
}

function parseOpNode(tokens, index) {
  if (index >= tokens.length) return { status: "incomplete" };
  const token = tokens[index];
  if (typeof token !== "string" || !token.startsWith("OP:"))
    return { status: "invalid" };
  index += 1;

  while (
    index < tokens.length &&
    typeof tokens[index] === "string" &&
    tokens[index].startsWith("OPVAR:")
  ) {
    index += 1;
  }

  if (index >= tokens.length) return { status: "incomplete" };
  if (tokens[index] !== OPEN) return { status: "invalid" };
  index += 1;

  let seenChild = false;
  while (true) {
    const node = parseNode(tokens, index);
    if (node.status === "invalid") return { status: "invalid" };
    if (node.status === "incomplete") return { status: "incomplete" };
    seenChild = true;
    index = node.next;
    if (index >= tokens.length) return { status: "incomplete" };
    if (tokens[index] === SEP) {
      index += 1;
      continue;
    }
    if (tokens[index] === CLOSE) {
      if (!seenChild) return { status: "invalid" };
      index += 1;
      return { status: "complete", next: index };
    }
    return { status: "invalid" };
  }
}

function parseNode(tokens, index) {
  if (index >= tokens.length) return { status: "incomplete" };
  const token = tokens[index];
  if (token === TERM) {
    return parseTerm(tokens, index);
  }
  if (token === FRAC) {
    return parseFraction(tokens, index);
  }
  if (typeof token === "string" && token.startsWith("OP:")) {
    return parseOpNode(tokens, index);
  }
  return { status: "invalid" };
}

function isValidPrefix(tokens) {
  if (!Array.isArray(tokens) || tokens.length === 0) return true;
  const result = parseNode(tokens, 0);
  if (result.status === "invalid") return false;
  if (result.status === "incomplete") return true;
  return result.status === "complete" && result.next === tokens.length;
}

rl.on("line", (line) => {
  if (!line.trim()) return;
  try {
    const request = JSON.parse(line);
    const tokens = request.tokens || [];
    const candidate_tokens = request.candidate_tokens || [];
    const mask = candidate_tokens.map((candidate) => {
      return isValidPrefix(tokens.concat([candidate]));
    });
    process.stdout.write(JSON.stringify({ mask }) + "\n");
  } catch (error) {
    process.stdout.write(
      JSON.stringify({ error: error.message, mask: [] }) + "\n",
    );
  }
});
