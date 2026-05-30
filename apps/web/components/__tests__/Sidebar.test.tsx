import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Sidebar } from '../Sidebar';

// Mock useCompany context
vi.mock('@/contexts/CompanyContext', () => ({
  useCompany: vi.fn(() => ({
    selectedCompanyId: 'test-id',
    setSelectedCompanyId: vi.fn(),
    companies: [{ id: '1', name: 'Test Company' }],
  })),
}));

// Mock useAuth context
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    user: 'test-user',
    isAuthenticated: true,
    logout: vi.fn(),
  })),
}));

describe('Sidebar Component', () => {
  it('renders navigation links', () => {
    render(<Sidebar />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Relatórios')).toBeInTheDocument();
  });

  it('shows company selector', () => {
    render(<Sidebar />);
    const selector = screen.getByRole('combobox');
    expect(selector).toBeInTheDocument();
  });
});
