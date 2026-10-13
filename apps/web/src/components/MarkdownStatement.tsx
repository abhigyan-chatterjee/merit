import React from 'react';

interface MarkdownStatementProps {
  statement: string;
  className?: string;
  stripHeading?: boolean;
}

export function renderInlineMarkdown(text: string): React.ReactNode {
  // Regex to match inline code (`...`) or bold (**...**) or italic (*...*)
  const regex = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const token = match[0];
    if (token.startsWith('`') && token.endsWith('`')) {
      parts.push(
        <code
          key={`code-${match.index}`}
          className="px-1.5 py-0.5 mx-0.5 rounded bg-canvas border border-line font-mono text-[12px] text-mint inline-block align-baseline"
        >
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith('**') && token.endsWith('**')) {
      parts.push(
        <strong key={`bold-${match.index}`} className="font-semibold text-ink">
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith('*') && token.endsWith('*')) {
      parts.push(
        <em key={`italic-${match.index}`} className="italic text-ink/90">
          {token.slice(1, -1)}
        </em>
      );
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

export const MarkdownStatement: React.FC<MarkdownStatementProps> = ({
  statement,
  className = 'text-sm text-ink leading-relaxed space-y-3',
  stripHeading = true,
}) => {
  if (!statement) return null;

  let cleaned = statement.trim();
  if (stripHeading && cleaned.startsWith('#')) {
    // Strip leading `# Title\n` or `# Title`
    cleaned = cleaned.replace(/^#\s+[^\n]+(?:\n+|$)/, '').trim();
  }

  // Split into paragraph blocks on two or more newlines
  const blocks = cleaned.split(/\n{2,}/);

  return (
    <div className={className}>
      {blocks.map((block, idx) => {
        const trimmed = block.trim();
        if (!trimmed) return null;

        // Subheadings
        if (trimmed.startsWith('### ') || trimmed.startsWith('## ')) {
          const headingText = trimmed.replace(/^#{2,3}\s+/, '');
          return (
            <h4
              key={idx}
              className="text-xs font-mono uppercase tracking-wider text-muted pt-2 font-semibold"
            >
              {renderInlineMarkdown(headingText)}
            </h4>
          );
        }

        const lines = trimmed.split('\n');

        // Bullet lists
        const isBulletList = lines.every((l) => {
          const t = l.trim();
          return t.startsWith('- ') || t.startsWith('* ');
        });

        if (isBulletList) {
          return (
            <ul key={idx} className="list-disc list-inside space-y-1.5 pl-1 text-ink">
              {lines.map((line, lIdx) => (
                <li key={lIdx} className="leading-relaxed">
                  {renderInlineMarkdown(line.trim().replace(/^[-*]\s+/, ''))}
                </li>
              ))}
            </ul>
          );
        }

        // Numbered lists
        const isNumberedList = lines.every((l) => /^\d+\.\s+/.test(l.trim()));
        if (isNumberedList) {
          return (
            <ol key={idx} className="list-decimal list-inside space-y-1.5 pl-1 text-ink">
              {lines.map((line, lIdx) => (
                <li key={lIdx} className="leading-relaxed">
                  {renderInlineMarkdown(line.trim().replace(/^\d+\.\s+/, ''))}
                </li>
              ))}
            </ol>
          );
        }

        // Standard paragraph
        return (
          <p key={idx} className="leading-relaxed">
            {lines.map((line, lIdx) => (
              <React.Fragment key={lIdx}>
                {lIdx > 0 && <br />}
                {renderInlineMarkdown(line)}
              </React.Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
};
