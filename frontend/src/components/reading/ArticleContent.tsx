import { useEffect, useRef } from 'react';
import hljs from 'highlight.js/lib/core';
import javascript from 'highlight.js/lib/languages/javascript';
import typescript from 'highlight.js/lib/languages/typescript';
import python from 'highlight.js/lib/languages/python';
import xml from 'highlight.js/lib/languages/xml';
import css from 'highlight.js/lib/languages/css';
import bash from 'highlight.js/lib/languages/bash';
import json from 'highlight.js/lib/languages/json';
import 'highlight.js/styles/github.css';
import { sanitizeHtml } from '@/lib/sanitize';

hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('python', python);
hljs.registerLanguage('xml', xml);
hljs.registerLanguage('html', xml);
hljs.registerLanguage('css', css);
hljs.registerLanguage('bash', bash);
hljs.registerLanguage('json', json);

interface ArticleContentProps {
  content: string;
}

export function ArticleContent({ content }: ArticleContentProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.querySelectorAll('pre code[class*="language-"]').forEach((block) => {
        hljs.highlightElement(block as HTMLElement);
      });
    }
  }, [content]);

  const isPlainText = content.trimStart().startsWith('<pre>');

  return (
    <div
      ref={contentRef}
      className={`prose prose-sm dark:prose-invert max-w-none [&_table]:!table-auto [&_td]:!p-0 [&_th]:!p-0 [&_img]:!m-0 [&_table]:!w-auto${isPlainText ? ' email-plaintext' : ''}`}
      dangerouslySetInnerHTML={{ __html: sanitizeHtml(content) }}
    />
  );
}
