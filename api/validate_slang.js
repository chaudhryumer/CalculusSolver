import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const { serializeSlangMath } = await import(
  new URL("../tokenizer/slang_serializer.js", import.meta.url)
);

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return chunks.join("");
}

function extractExpression(payload) {
  if (payload && typeof payload === "object" && "expression" in payload) {
    return payload.expression;
  }
  return payload;
}

async function run() {
  const raw = await readStdin();
  const payload = JSON.parse(raw);
  const expression = extractExpression(payload);

  try {
    serializeSlangMath(expression);
    process.stdout.write(JSON.stringify({ valid: true }));
  } catch (error) {
    process.stdout.write(
      JSON.stringify({ valid: false, reason: error.message }),
    );
    process.exitCode = 1;
  }
}

run().catch((error) => {
  process.stderr.write(error.stack || error.message || String(error));
  process.exit(1);
});
