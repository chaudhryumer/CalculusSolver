import { fileURLToPath } from "url";
import { dirname } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const serializerPath = new URL(
  "../tokenizer/slang_serializer.js",
  import.meta.url,
);
const { deserializeSlangMath } = await import(serializerPath);

const {
  differentiateFraction,
  integrateFraction,
  definiteIntegrateFraction,
  evaluateFraction,
} = await import(new URL("../slang/slang-basic.js", import.meta.url));
const { gradient, productRuleDifferentiate, quotientRuleDifferentiate } =
  await import(new URL("../slang/slang-advanced.js", import.meta.url));

function testPoints(variables, n = 50) {
  return Array.from({ length: n }, () => {
    const point = {};
    for (const variable of variables) {
      point[variable] = Math.random() * 9.8 - 4.9;
    }
    return point;
  });
}

function compareExpressions(a, b, variables, tol = 1e-6) {
  const points = testPoints(variables, 50);
  let tested = 0;
  let passed = 0;

  for (const point of points) {
    try {
      const va = evaluateFraction(a, point);
      const vb = evaluateFraction(b, point);
      if (!Number.isFinite(va) || !Number.isFinite(vb)) {
        continue;
      }
      tested += 1;
      if (Math.abs(va - vb) <= tol) {
        passed += 1;
      }
    } catch {
      continue;
    }
  }

  return {
    tested,
    passed,
    confidence: tested > 0 ? passed / tested : 0,
    equivalent: tested > 0 && passed === tested,
  };
}

const ORACLE = {
  diff: (inp) => differentiateFraction(inp.expr, inp.var),
  integrate: (inp) => integrateFraction(inp.expr, inp.var),
  def_integrate: (inp) =>
    definiteIntegrateFraction(inp.expr, inp.lower, inp.upper, inp.var),
  gradient: (inp) => gradient(inp.expr, inp.vars),
  product_rule: (inp) => productRuleDifferentiate([inp.u, inp.v], inp.var),
  quotient_rule: (inp) => quotientRuleDifferentiate(inp.u, inp.v, inp.var),
};

function getVariables(input) {
  if (Array.isArray(input.vars) && input.vars.length > 0) {
    return input.vars;
  }
  if (typeof input.var === "string") {
    return [input.var];
  }
  return ["x"];
}

function verify(inputEnv, outputTokens) {
  let output;
  try {
    output = deserializeSlangMath(outputTokens);
  } catch (error) {
    return {
      status: "unverified",
      verified: false,
      confidence: 0,
      error: `Output deserialization failed: ${error.message}`,
    };
  }

  if (inputEnv.op === "undefined") {
    return {
      status: "unsolvable",
      verified: false,
      confidence: 0,
      output,
    };
  }

  const oracleFn = ORACLE[inputEnv.op];
  if (typeof oracleFn !== "function") {
    return {
      status: "unverified",
      verified: false,
      confidence: 0,
      error: `Unsupported operation for verifier: ${inputEnv.op}`,
      output,
    };
  }

  let oracle;
  try {
    oracle = oracleFn(inputEnv);
  } catch (error) {
    return {
      status: "unverified",
      verified: false,
      confidence: 0,
      error: `Oracle execution failed: ${error.message}`,
      output,
    };
  }

  const variables = getVariables(inputEnv);
  if (
    inputEnv.op === "gradient" &&
    typeof oracle === "object" &&
    oracle !== null
  ) {
    const keys = Object.keys(oracle);
    for (const key of keys) {
      const result = compareExpressions(oracle[key], output[key], variables);
      if (!result.equivalent) {
        return {
          status: "unverified",
          verified: false,
          confidence: result.confidence,
          output,
        };
      }
    }
    return {
      status: "solved",
      verified: true,
      confidence: 1,
      output,
    };
  }

  const result = compareExpressions(oracle, output, variables);
  return {
    status: result.equivalent ? "solved" : "unverified",
    verified: result.equivalent,
    confidence: result.confidence,
    output,
  };
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return chunks.join("");
}

async function run() {
  const raw = await readStdin();
  const payload = JSON.parse(raw);
  const result = verify(payload.input, payload.output_tokens);
  process.stdout.write(JSON.stringify(result));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  run().catch((error) => {
    process.stderr.write(error.stack || error.message || String(error));
    process.exit(1);
  });
}

export { verify };
