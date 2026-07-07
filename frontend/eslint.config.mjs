import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({ baseDirectory: __dirname });

const eslintConfig = [
  // Generierte/vendorte Artefakte nie linten (H-003/H-039): der Next.js-
  // Build-Output (.next) und node_modules sind kein Projektcode.
  { ignores: [".next/**", "node_modules/**"] },
  { ignores: ["src/components/ui/**", "src/lib/utils.ts"] },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
];

export default eslintConfig;
