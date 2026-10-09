import { describe, expect, it, vi } from 'vitest';
import type { InspectionTicketResponse } from '../types/api';
import {
  escapeCsvCell,
  exportQueueAsCsv,
  exportTicketAsJson,
} from './exportUtils';

describe('exportUtils', () => {
  describe('escapeCsvCell', () => {
    it('handles null and undefined', () => {
      expect(escapeCsvCell(null)).toBe('');
      expect(escapeCsvCell(undefined)).toBe('');
    });

    it('returns simple strings and numbers unquoted', () => {
      expect(escapeCsvCell('simple')).toBe('simple');
      expect(escapeCsvCell(123)).toBe('123');
      expect(escapeCsvCell(0)).toBe('0');
    });

    it('quotes strings with commas', () => {
      expect(escapeCsvCell('hello, world')).toBe('"hello, world"');
    });

    it('quotes and escapes strings with internal double quotes', () => {
      expect(escapeCsvCell('hello "world"')).toBe('"hello ""world"""');
    });

    it('quotes strings with newlines', () => {
      expect(escapeCsvCell("line1\nline2")).toBe('"line1\nline2"');
    });
  });

  describe('exportTicketAsJson', () => {
    it('creates a download link and triggers click for valid ticket', () => {
      const mockTicket: InspectionTicketResponse = {
        ticket_id: 'TCK-2016-10-30-EF550F26',
        meter_id: 'TEST_METER_01',
        evaluation_period: '2016-10-30',
        tamper_probability: 0.95,
        calibrated_probability: 0.95,
        estimated_leakage_kwh: 1200.0,
        estimated_recoverable_revenue: 7200.0,
        dispatch_cost: 500.0,
        expected_gross_recovery: 6840.0,
        env: 6340.0,
        tau_cost: 0.065,
        tau_env: 0.069,
        active_threshold: 0.069,
        decision_rule: 'env',
        inspection_recommended: true,
        priority_rank: 1,
        customer_type: 'residential',
        feeder_id: 'FEEDER-01',
        data_quality_status: 'good',
        signatures_summary: 'Sustained Step Down',
        safety_caveat: 'Field inspection required.',
      };

      // Mock createObjectURL & revokeObjectURL
      const mockCreateObjectURL = vi.fn().mockReturnValue('blob:http://localhost/mock-blob');
      const mockRevokeObjectURL = vi.fn();
      globalThis.URL.createObjectURL = mockCreateObjectURL;
      globalThis.URL.revokeObjectURL = mockRevokeObjectURL;

      const clickSpy = vi.fn();
      const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue({
        set href(_val: string) {},
        set download(_val: string) {},
        style: {},
        click: clickSpy,
      } as unknown as HTMLAnchorElement);

      const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation((node) => node);
      const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation((node) => node);

      const success = exportTicketAsJson(mockTicket);

      expect(success).toBe(true);
      expect(clickSpy).toHaveBeenCalled();
      expect(mockCreateObjectURL).toHaveBeenCalled();
      expect(mockRevokeObjectURL).toHaveBeenCalled();

      createElementSpy.mockRestore();
      appendChildSpy.mockRestore();
      removeChildSpy.mockRestore();
    });

    it('returns false for invalid ticket without meter_id', () => {
      const success = exportTicketAsJson({} as unknown as InspectionTicketResponse);
      expect(success).toBe(false);
    });
  });

  describe('exportQueueAsCsv', () => {
    it('creates CSV download with headers and escaped rows', () => {
      const mockTickets: InspectionTicketResponse[] = [
        {
          ticket_id: 'TCK-01',
          meter_id: 'MTR-01',
          evaluation_period: '2016-10-30',
          tamper_probability: 0.9,
          calibrated_probability: 0.9,
          estimated_leakage_kwh: 1000.0,
          estimated_recoverable_revenue: 6000.0,
          dispatch_cost: 500.0,
          expected_gross_recovery: 5400.0,
          env: 4900.0,
          tau_cost: 0.05,
          tau_env: 0.05,
          active_threshold: 0.05,
          decision_rule: 'env',
          inspection_recommended: true,
          priority_rank: 1,
          customer_type: 'commercial',
          feeder_id: 'FEEDER-NORTH',
          data_quality_status: 'good',
          signatures_summary: 'Sustained Step Down, Flatline',
          safety_caveat: 'Field inspection required.',
        },
      ];

      const clickSpy = vi.fn();
      let capturedBlob: Blob | null = null;
      globalThis.URL.createObjectURL = vi.fn().mockImplementation((blob: Blob) => {
        capturedBlob = blob;
        return 'blob:mock-url';
      });
      globalThis.URL.revokeObjectURL = vi.fn();

      vi.spyOn(document, 'createElement').mockReturnValue({
        set href(_val: string) {},
        set download(_val: string) {},
        style: {},
        click: clickSpy,
      } as unknown as HTMLAnchorElement);

      vi.spyOn(document.body, 'appendChild').mockImplementation((node) => node);
      vi.spyOn(document.body, 'removeChild').mockImplementation((node) => node);

      const result = exportQueueAsCsv(mockTickets);

      expect(result).toBe(true);
      expect(clickSpy).toHaveBeenCalled();
      expect(capturedBlob).not.toBeNull();
    });

    it('returns false for empty queue', () => {
      expect(exportQueueAsCsv([])).toBe(false);
    });
  });
});
