import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Surface, Divider, CodeSurface } from './Surface';

describe('Surface & Divider Components', () => {
  it('renders Surface container with children', () => {
    render(<Surface>Operational Content</Surface>);
    expect(screen.getByText('Operational Content')).toBeInTheDocument();
  });

  it('renders Divider with correct spacing class', () => {
    const { container } = render(<Divider spacing="lg" />);
    const hr = container.querySelector('hr');
    expect(hr).toHaveClass('gg-divider--lg');
  });

  it('renders CodeSurface with caption and formatted snippet', () => {
    render(
      <CodeSurface caption="FASTAPI_RESPONSE">
        {JSON.stringify({ status: 'ok' }, null, 2)}
      </CodeSurface>
    );
    expect(screen.getByText('FASTAPI_RESPONSE')).toBeInTheDocument();
    expect(screen.getByText(/"status": "ok"/)).toBeInTheDocument();
  });
});
