import { readFile } from "fs/promises";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const serializerPath = new URL(
  "../tokenizer/slang_serializer.js",
  import.meta.url,
);
const { serializeSlangMath } = await import(serializerPath);

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return chunks.join("");
}

async function run() {
  const inputText = await readStdin();
  const input = JSON.parse(inputText);
  const tokens = serializeSlangMath(input);
  process.stdout.write(JSON.stringify({ tokens }));
}

run().catch((error) => {
  process.stderr.write(error.stack || error.message || String(error));
  process.exit(1);
});
