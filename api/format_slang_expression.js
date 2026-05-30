import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const { slangToLatex } = await import(
  new URL("../slang/src/convertor.js", import.meta.url)
);

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return chunks.join("");
}

function expressionToLatex(value) {
  if (value === null || value === undefined) {
    return null;
  }
  if (Array.isArray(value)) {
    return value.map(expressionToLatex);
  }
  if (typeof value === "object") {
    if (
      value.op !== undefined ||
      value.numi !== undefined ||
      value.coeff !== undefined ||
      value.terms !== undefined
    ) {
      return slangToLatex(value);
    }
    const mapped = {};
    for (const [key, child] of Object.entries(value)) {
      mapped[key] = expressionToLatex(child);
    }
    return mapped;
  }
  return String(value);
}

async function run() {
  const raw = await readStdin();
  const payload = JSON.parse(raw);
  const expression = payload.expression;

  try {
    const latex = expressionToLatex(expression);
    process.stdout.write(JSON.stringify({ latex }));
  } catch (error) {
    process.stdout.write(JSON.stringify({ latex: null, error: error.message }));
    process.exitCode = 1;
  }
}

run().catch((error) => {
  process.stderr.write(error.stack || error.message || String(error));
  process.exit(1);
});
