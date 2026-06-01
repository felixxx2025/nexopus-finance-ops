import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Sidebar } from '../Sidebar';

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

  it('renders user menu with username', () => {
    render(<Sidebar />);
    expect(screen.getByText('test-user')).toBeInTheDocument();
  });
});
