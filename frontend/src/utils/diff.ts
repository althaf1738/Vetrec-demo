export type DiffPieces = { beforeHtml: string; afterHtml: string; changed: boolean };

function escapeHtml(s: string){
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

export function highlightChange(before: string, after: string): DiffPieces {
  if (before === after) {
    const safe = escapeHtml(before);
    return { beforeHtml: safe, afterHtml: safe, changed: false };
  }
  const a = before || "";
  const b = after || "";

  // common prefix
  let i=0;
  while (i < a.length && i < b.length && a[i] === b[i]) i++;

  // common suffix
  let j=0;
  while (j < a.length - i && j < b.length - i && a[a.length-1-j] === b[b.length-1-j]) j++;

  const pre = escapeHtml(a.slice(0,i));
  const suf = escapeHtml(a.slice(a.length-j));
  const preB = escapeHtml(b.slice(0,i));
  const sufB = escapeHtml(b.slice(b.length-j));

  const midA = escapeHtml(a.slice(i, a.length-j));
  const midB = escapeHtml(b.slice(i, b.length-j));

  const beforeHtml = `${pre}<span class="diff-del">${midA}</span>${suf}`;
  const afterHtml  = `${preB}<span class="diff-add">${midB}</span>${sufB}`;
  return { beforeHtml, afterHtml, changed: true };
}
