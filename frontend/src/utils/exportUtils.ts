/**
 * Export utilities for Grid-Guard inspection tickets and queues.
 * Adheres to RFC 4180 CSV specifications and clean structured JSON output.
 */

import type { InspectionTicketResponse } from '../types/api';

/**
 * Trigger a browser download of a given string content.
 */
export function triggerFileDownload(
  content: string,
  filename: string,
  mimeType: string = 'text/plain;charset=utf-8'
): boolean {
  try {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    return true;
  } catch (err) {
    console.error('File download failed:', err);
    return false;
  }
}

/**
 * Escapes a single value for RFC 4180 CSV compliance.
 */
export function escapeCsvCell(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }
  const str = String(value);
  // If the cell contains quotes, commas, or newlines, quote it and escape internal quotes
  if (/[",\n\r]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

/**
 * Exports a single inspection ticket as structured, human-readable JSON.
 */
export function exportTicketAsJson(ticket: InspectionTicketResponse): boolean {
  if (!ticket || !ticket.meter_id) {
    console.warn('Cannot export invalid ticket');
    return false;
  }

  const filename = `inspection-ticket-${ticket.meter_id}-${ticket.evaluation_period || 'snapshot'}.json`;
  const jsonContent = JSON.stringify(ticket, null, 2);
  return triggerFileDownload(jsonContent, filename, 'application/json;charset=utf-8');
}

/**
 * Exports an array of inspection queue tickets as a standard CSV file.
 */
export function exportQueueAsCsv(
  tickets: InspectionTicketResponse[],
  customFilename?: string
): boolean {
  if (!tickets || tickets.length === 0) {
    console.warn('Cannot export empty tickets queue');
    return false;
  }

  const headers = [
    'priority_rank',
    'ticket_id',
    'meter_id',
    'feeder_id',
    'customer_type',
    'evaluation_period',
    'tamper_probability',
    'calibrated_probability',
    'estimated_leakage_kwh',
    'estimated_recoverable_revenue',
    'dispatch_cost',
    'expected_gross_recovery',
    'expected_net_value',
    'inspection_recommended',
    'active_threshold',
    'decision_rule',
    'data_quality_status',
    'signatures_summary',
  ];

  const rows: string[] = [headers.map(escapeCsvCell).join(',')];

  for (const t of tickets) {
    const rowValues = [
      t.priority_rank ?? '',
      t.ticket_id,
      t.meter_id,
      t.feeder_id,
      t.customer_type,
      t.evaluation_period,
      t.tamper_probability,
      t.calibrated_probability,
      t.estimated_leakage_kwh,
      t.estimated_recoverable_revenue,
      t.dispatch_cost,
      t.expected_gross_recovery,
      t.env,
      t.inspection_recommended ? 'true' : 'false',
      t.active_threshold,
      t.decision_rule,
      t.data_quality_status,
      t.signatures_summary,
    ];
    rows.push(rowValues.map(escapeCsvCell).join(','));
  }

  const csvContent = rows.join('\r\n');
  const dateStr = new Date().toISOString().split('T')[0];
  const filename = customFilename || `grid-guard-inspection-queue-${dateStr}.csv`;

  return triggerFileDownload(csvContent, filename, 'text/csv;charset=utf-8');
}
