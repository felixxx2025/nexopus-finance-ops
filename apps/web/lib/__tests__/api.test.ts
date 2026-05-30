import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchApprovedEntries, fetchCompliance } from '../api';

// Mock fetch globally
global.fetch = vi.fn();

describe('API Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetchCompliance', () => {
    it('fetches compliance data successfully', async () => {
      const mockData = { compliance: { equacao_patrimonial: true, partida_dobrada: true } };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await fetchCompliance('test-company');
      expect(result).toEqual(mockData);
    });

    it('handles fetch errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      await expect(fetchCompliance('test-company')).rejects.toThrow('Network error');
    });
  });

  describe('fetchApprovedEntries', () => {
    it('fetches approved entries with parameters', async () => {
      const mockData = { entries: [{ id: '1', date: '2024-01-01' }] };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await fetchApprovedEntries('test-id');
      expect(result).toEqual(mockData);
    });
  });
});
