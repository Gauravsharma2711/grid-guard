import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

describe('Design Tokens Validation', () => {
  const tokensFilePath = path.resolve(__dirname, 'tokens.css');
  const tokensContent = fs.readFileSync(tokensFilePath, 'utf-8');

  const expectedPaletteTokens: Record<string, string> = {
    '--gg-canvas': '#fbfbf7',
    '--gg-surface': '#ffffff',
    '--gg-ink': '#121512',
    '--gg-ink-soft': '#344038',
    '--gg-muted': '#737b74',
    '--gg-rule': '#e1e5dd',
    '--gg-signal': '#d9ff4a',
    '--gg-signal-ink': '#3f4b08',
    '--gg-evidence': '#7d6db2',
    '--gg-safe': '#3f8b61',
    '--gg-warning': '#b88418',
    '--gg-danger': '#c45646',
    '--gg-code': '#151a16',
    '--gg-code-ink': '#e7eee7',
  };

  const expectedGeometryTokens = [
    '--gg-radius-xs',
    '--gg-radius-sm',
    '--gg-radius-lg',
    '--gg-rule-width',
    '--gg-header-height',
    '--gg-content-width',
    '--gg-drawer-width',
    '--gg-control-height',
    '--gg-page-max-width',
  ];

  const expectedSpacingTokens = [
    '--gg-space-1',
    '--gg-space-2',
    '--gg-space-3',
    '--gg-space-4',
    '--gg-space-6',
    '--gg-space-8',
    '--gg-space-12',
    '--gg-space-16',
    '--gg-space-20',
  ];

  it('contains all required authoritative palette tokens with exact hex values', () => {
    for (const [token, hex] of Object.entries(expectedPaletteTokens)) {
      expect(tokensContent).toContain(token);
      const regex = new RegExp(`${token}:\\s*${hex}`, 'i');
      expect(regex.test(tokensContent)).toBe(true);
    }
  });

  it('contains all required geometry tokens', () => {
    for (const token of expectedGeometryTokens) {
      expect(tokensContent).toContain(token);
    }
  });

  it('contains all required spacing tokens', () => {
    for (const token of expectedSpacingTokens) {
      expect(tokensContent).toContain(token);
    }
  });

  it('defines the specified font families for display, body, and mono', () => {
    expect(tokensContent).toContain("'Space Grotesk'");
    expect(tokensContent).toContain("'Inter'");
    expect(tokensContent).toContain("'IBM Plex Mono'");
  });
});
