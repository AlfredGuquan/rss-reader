import DOMPurify from 'dompurify';

export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ADD_TAGS: ['iframe', 'center'],
    ADD_ATTR: ['target', 'allowfullscreen', 'frameborder', 'style', 'bgcolor', 'cellpadding', 'cellspacing', 'border', 'width', 'height', 'align', 'valign'],
    FORBID_TAGS: ['script'],
    ALLOW_DATA_ATTR: true,
  });
}
