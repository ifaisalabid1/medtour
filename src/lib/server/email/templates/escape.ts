const ENTITIES: Record<string, string> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;"
};

/** Escapes text before putting it into email HTML. Use for anything a visitor typed. */
export const escapeHtml = (text: string) => text.replace(/[&<>"']/g, (char) => ENTITIES[char]!);
