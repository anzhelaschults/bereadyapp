import js from "@eslint/js";
import nextVitals from "eslint-config-next/core-web-vitals";
import tseslint from "typescript-eslint";

const config = [...nextVitals, js.configs.recommended, ...tseslint.configs.recommended, { ignores: [".next/**", "node_modules/**", "playwright-report/**"] }];
export default config;
