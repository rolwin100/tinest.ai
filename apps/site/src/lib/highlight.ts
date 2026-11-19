/**
 * A small tokenizer for the three languages this site shows.
 *
 * Deliberately not Shiki or Prism. The snippets are fixed, short and written by
 * us; a full grammar engine would add a dependency, a build step and a bundle
 * for six hundred characters of code. If arbitrary user code ever needs
 * highlighting — a docs site, say — swap this for Shiki at build time and
 * delete the file.
 */

export type TokenKind =
  | "plain"
  | "comment"
  | "string"
  | "keyword"
  | "number"
  | "fn"
  | "prop"
  | "variable";

export type Token = { text: string; kind: TokenKind };

export type Language = "javascript" | "python" | "bash";

/**
 * Order inside each alternation is the whole trick: comments and strings must
 * match before anything else, or a keyword inside a string gets coloured and a
 * URL's `//` starts a comment.
 */
const GRAMMARS: Record<Language, RegExp> = {
  javascript: new RegExp(
    [
      "(?<comment>//[^\\n]*)",
      "(?<string>\"(?:[^\"\\\\]|\\\\.)*\"|'(?:[^'\\\\]|\\\\.)*'|`(?:[^`\\\\]|\\\\.)*`)",
      "(?<keyword>\\b(?:const|let|var|function|return|if|else|new|await|async|typeof|import|export|from|class|extends|of|in|for|while|try|catch|throw|null|undefined|true|false)\\b)",
      "(?<number>\\b\\d+(?:\\.\\d+)?\\b)",
      "(?<fn>[A-Za-z_$][\\w$]*(?=\\s*\\())",
      "(?<prop>[A-Za-z_$][\\w$]*(?=\\s*:))",
    ].join("|"),
    "g",
  ),
  python: new RegExp(
    [
      "(?<comment>#[^\\n]*)",
      "(?<string>[frb]?\"\"\"[\\s\\S]*?\"\"\"|[frb]?\"(?:[^\"\\\\]|\\\\.)*\"|[frb]?'(?:[^'\\\\]|\\\\.)*')",
      "(?<keyword>\\b(?:async|await|with|as|import|from|for|in|if|elif|else|return|def|class|try|except|finally|break|continue|pass|lambda|not|and|or|is|True|False|None)\\b)",
      "(?<number>\\b\\d+(?:\\.\\d+)?\\b)",
      "(?<fn>[A-Za-z_][\\w]*(?=\\s*\\())",
      "(?<prop>\"[\\w_]+\"(?=\\s*:))",
    ].join("|"),
    "g",
  ),
  bash: new RegExp(
    [
      "(?<comment>#[^\\n]*)",
      "(?<string>\"(?:[^\"\\\\]|\\\\.)*\"|'[^']*')",
      "(?<variable>\\$\\{?[A-Za-z_][\\w]*\\}?)",
      "(?<keyword>(?<=\\s)-{1,2}[A-Za-z][\\w-]*)",
      "(?<fn>^[a-z][\\w-]*)",
    ].join("|"),
    "gm",
  ),
};

const KINDS: Array<TokenKind> = [
  "comment",
  "string",
  "keyword",
  "number",
  "fn",
  "prop",
  "variable",
];

export function tokenize(code: string, language: Language): Array<Token> {
  const pattern = GRAMMARS[language];
  pattern.lastIndex = 0;

  const tokens: Array<Token> = [];
  let cursor = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(code)) !== null) {
    // Zero-length matches would spin forever.
    if (match[0].length === 0) {
      pattern.lastIndex += 1;
      continue;
    }

    if (match.index > cursor) {
      tokens.push({ text: code.slice(cursor, match.index), kind: "plain" });
    }

    const groups = match.groups ?? {};
    const kind = KINDS.find((k) => groups[k] !== undefined) ?? "plain";
    tokens.push({ text: match[0], kind });
    cursor = match.index + match[0].length;
  }

  if (cursor < code.length) {
    tokens.push({ text: code.slice(cursor), kind: "plain" });
  }

  return tokens;
}

export const TOKEN_CLASS: Record<TokenKind, string> = {
  plain: "text-fg-muted",
  comment: "text-[var(--syntax-comment)] italic",
  string: "text-[var(--syntax-string)]",
  keyword: "text-[var(--syntax-keyword)]",
  number: "text-[var(--syntax-number)]",
  fn: "text-[var(--syntax-fn)]",
  prop: "text-[var(--syntax-prop)]",
  variable: "text-[var(--syntax-variable)]",
};
