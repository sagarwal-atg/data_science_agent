import React from 'react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

/**
 * Simple markdown renderer for formatting text with bold, italic, and basic formatting.
 * Handles:
 * - **bold** text
 * - *italic* text
 * - Line breaks
 * - Lists (basic)
 */
export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  // Split content into lines for processing
  const lines = content.split('\n');

  const renderLine = (line: string, index: number): React.ReactNode => {
    // Skip empty lines
    if (!line.trim()) {
      return <br key={index} />;
    }

    // Check for list items (but not if it's part of bold/italic markdown)
    const trimmed = line.trim();
    const isUnorderedList = (trimmed.startsWith('- ') || (trimmed.startsWith('* ') && !trimmed.startsWith('**')));
    if (isUnorderedList) {
      const listContent = trimmed.substring(2);
      return (
        <li key={index} className="ml-6 mb-2">
          {renderInlineMarkdown(listContent)}
        </li>
      );
    }

    // Check for numbered lists
    const numberedMatch = trimmed.match(/^(\d+)\.\s+(.+)$/);
    if (numberedMatch) {
      return (
        <li key={index} className="ml-6 mb-2 list-decimal">
          {renderInlineMarkdown(numberedMatch[2])}
        </li>
      );
    }

    // Regular paragraph
    return (
      <p key={index} className="mb-3 last:mb-0">
        {renderInlineMarkdown(line)}
      </p>
    );
  };

  const renderInlineMarkdown = (text: string): React.ReactNode => {
    const parts: React.ReactNode[] = [];
    let currentIndex = 0;

    // Pattern to match **bold** or *italic*
    const markdownPattern = /(\*\*([^*]+)\*\*|\*([^*]+)\*)/g;
    let match;
    let lastIndex = 0;

    while ((match = markdownPattern.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }

      // Add the formatted text
      if (match[1].startsWith('**')) {
        // Bold
        parts.push(
          <strong key={currentIndex++} className="font-bold text-slate-900">
            {match[2]}
          </strong>
        );
      } else if (match[1].startsWith('*')) {
        // Italic
        parts.push(
          <em key={currentIndex++} className="italic text-slate-800">
            {match[3]}
          </em>
        );
      }

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    // If no markdown found, return plain text
    if (parts.length === 0) {
      return text;
    }

    return <>{parts}</>;
  };

  // Group lines into paragraphs and lists
  const elements: React.ReactNode[] = [];
  let currentList: React.ReactNode[] = [];
  let listType: 'unordered' | 'ordered' | null = null;

  lines.forEach((line, index) => {
    const trimmed = line.trim();

    // Check for list items (avoid conflict with bold markdown **)
    const isUnorderedList = trimmed.startsWith('- ') || (trimmed.startsWith('* ') && !trimmed.startsWith('**'));
    if (isUnorderedList) {
      if (listType !== 'unordered') {
        // Close previous list if different type
        if (currentList.length > 0 && listType === 'ordered') {
          elements.push(
            <ol key={`list-${elements.length}`} className="list-decimal ml-6 mb-3 space-y-1">
              {currentList}
            </ol>
          );
          currentList = [];
        }
        listType = 'unordered';
      }
      const listContent = trimmed.substring(2);
      currentList.push(
        <li key={index} className="mb-1">
          {renderInlineMarkdown(listContent)}
        </li>
      );
    } else if (/^\d+\.\s+/.test(trimmed)) {
      if (listType !== 'ordered') {
        // Close previous list if different type
        if (currentList.length > 0 && listType === 'unordered') {
          elements.push(
            <ul key={`list-${elements.length}`} className="list-disc ml-6 mb-3 space-y-1">
              {currentList}
            </ul>
          );
          currentList = [];
        }
        listType = 'ordered';
      }
      const match = trimmed.match(/^\d+\.\s+(.+)$/);
      if (match) {
        currentList.push(
          <li key={index} className="mb-1">
            {renderInlineMarkdown(match[1])}
          </li>
        );
      }
    } else {
      // Close any open list
      if (currentList.length > 0) {
        if (listType === 'unordered') {
          elements.push(
            <ul key={`list-${elements.length}`} className="list-disc ml-6 mb-3 space-y-1">
              {currentList}
            </ul>
          );
        } else if (listType === 'ordered') {
          elements.push(
            <ol key={`list-${elements.length}`} className="list-decimal ml-6 mb-3 space-y-1">
              {currentList}
            </ol>
          );
        }
        currentList = [];
        listType = null;
      }

      // Add paragraph or break
      if (!trimmed) {
        elements.push(<br key={index} />);
      } else {
        elements.push(
          <p key={index} className="mb-3 last:mb-0">
            {renderInlineMarkdown(line)}
          </p>
        );
      }
    }
  });

  // Close any remaining list
  if (currentList.length > 0) {
    if (listType === 'unordered') {
      elements.push(
        <ul key={`list-${elements.length}`} className="list-disc ml-6 mb-3 space-y-1">
          {currentList}
        </ul>
      );
    } else if (listType === 'ordered') {
      elements.push(
        <ol key={`list-${elements.length}`} className="list-decimal ml-6 mb-3 space-y-1">
          {currentList}
        </ol>
      );
    }
  }

  return (
    <div className={className}>
      {elements}
    </div>
  );
}
