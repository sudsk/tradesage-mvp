// utils/textUtils.js - Add this new file in frontend/src/utils/
export const cleanMarkdownText = (text) => {
  if (!text) return '';
  
  // Convert markdown to HTML
  let cleaned = text
    // Bold text (**text** -> <strong>text</strong>)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Italic text (*text* -> <em>text</em>)
    .replace(/(?<!\*)\*(?!\*)(.*?)\*(?!\*)/g, '<em>$1</em>')
    // Headers (## text -> <h2>text</h2>)
    .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
    .replace(/^## (.*?)$/gm, '<h2>$1</h2>')
    .replace(/^# (.*?)$/gm, '<h1>$1</h1>')
    // Line breaks
    .replace(/\n/g, '<br>');
  
  return cleaned;
};

export const extractQuoteAndReason = (text) => {
  // Don't truncate quote or reason by default
  if (!text) return { quote: '', reason: '' };
  
  // Extract quote and reason from contradiction/confirmation text
  const quoteMatch = text.match(/["'""]([^"'""]*)["'""]/);
  const quote = quoteMatch ? quoteMatch[1] : text;
  
  // Extract analysis/reason part
  const analysisMatch = text.match(/Analysis:\s*(.*)/i) || text.match(/Reason:\s*(.*)/i);
  const reason = analysisMatch ? analysisMatch[1] : 'Market analysis provides this insight';
  
  return { quote, reason };
};

export const formatHypothesisTitle = (title) => {
  if (!title) return 'Untitled Hypothesis';
  
  // Remove markdown formatting
  let cleaned = title
    .replace(/\*+/g, '')
    .replace(/#+\s*/g, '')
    .replace(/["'""]([^"'""]*)["'""]/g, '$1');
  
  // Take only the first sentence if it's a long response
  const sentences = cleaned.split(/[.!?]\s+/);
  if (sentences[0] && sentences[0].length > 10) {
    return sentences[0].trim();
  }
  
  // Fallback to first 100 characters
  return cleaned.substring(0, 100).trim() + (cleaned.length > 100 ? '...' : '');
};
