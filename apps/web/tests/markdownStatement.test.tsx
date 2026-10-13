import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { MarkdownStatement } from '../src/components/MarkdownStatement';

describe('MarkdownStatement', () => {
  it('strips leading # Title header by default', () => {
    const raw = '# Counting Bits\n\nGiven an integer `n`, return an array `ans`.';
    render(<MarkdownStatement statement={raw} />);
    expect(screen.queryByText(/# Counting Bits/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Given an integer/i)).toBeInTheDocument();
    expect(screen.getByText('n')).toBeInTheDocument();
    expect(screen.getByText('ans')).toBeInTheDocument();
  });

  it('renders inline code, bold, and italic properly', () => {
    const raw = 'Variable `x` is **important** and *fast*.';
    render(<MarkdownStatement statement={raw} />);
    const codeEl = screen.getByText('x');
    expect(codeEl.tagName).toBe('CODE');
    const boldEl = screen.getByText('important');
    expect(boldEl.tagName).toBe('STRONG');
    const italicEl = screen.getByText('fast');
    expect(italicEl.tagName).toBe('EM');
  });

  it('renders bullet lists and numbered lists as distinct elements', () => {
    const raw = 'Steps:\n\n- First item `a`\n- Second item `b`\n\n1. Number one\n2. Number two';
    render(<MarkdownStatement statement={raw} />);
    expect(screen.getByText('First item')).toBeInTheDocument();
    expect(screen.getByText('Second item')).toBeInTheDocument();
    expect(screen.getByText('Number one')).toBeInTheDocument();
    expect(screen.getByText('Number two')).toBeInTheDocument();
  });

  it('handles multiline paragraphs with proper spacing', () => {
    const raw = 'Paragraph one.\n\nParagraph two with `k` elements.\n\nConstraints: `0 <= n <= 100`';
    render(<MarkdownStatement statement={raw} />);
    expect(screen.getByText(/Paragraph one/i)).toBeInTheDocument();
    expect(screen.getByText(/Paragraph two/i)).toBeInTheDocument();
    expect(screen.getByText(/Constraints:/i)).toBeInTheDocument();
  });
});
