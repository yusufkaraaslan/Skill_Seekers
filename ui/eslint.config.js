import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', 'test-results', 'playwright-report']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
  },
  { files: ['src/components/ui/**/*.tsx'], rules: { 'react-refresh/only-export-components': ['error', { allowConstantExport: true, allowExportNames: ['badgeVariants', 'buttonVariants', 'buttonGroupVariants', 'useFormField', 'navigationMenuTriggerStyle', 'useSidebar', 'toggleVariants'] }] } },
  { files: ['src/lib/store.tsx'], rules: { 'react-refresh/only-export-components': ['error', { allowExportNames: ['useStore'] }] } },
])
