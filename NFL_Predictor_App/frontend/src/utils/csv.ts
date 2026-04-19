/**
 * CSV export utilities — download tabular data as a .csv file.
 */

/** Convert an array of objects to a CSV string. */
export function toCSV(rows: Record<string, unknown>[], columns?: string[]): string {
  if (rows.length === 0) return '';
  const keys = columns ?? Object.keys(rows[0]);
  const escape = (v: unknown) => {
    const s = v == null ? '' : String(v);
    return s.includes(',') || s.includes('"') || s.includes('\n')
      ? `"${s.replace(/"/g, '""')}"`
      : s;
  };
  const header = keys.join(',');
  const body = rows.map(r => keys.map(k => escape(r[k])).join(',')).join('\n');
  return `${header}\n${body}`;
}

/** Trigger a browser download of a CSV file. */
export function downloadCSV(
  rows: Record<string, unknown>[],
  filename: string,
  columns?: string[],
): void {
  const csv = toCSV(rows, columns);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename.endsWith('.csv') ? filename : `${filename}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
