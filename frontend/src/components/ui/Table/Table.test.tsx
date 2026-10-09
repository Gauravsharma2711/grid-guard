import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DataTable, Column } from './DataTable';

interface TestItem {
  id: string;
  meterId: string;
  probability: string;
  env: string;
}

describe('DataTable Component', () => {
  const columns: Column<TestItem>[] = [
    { key: 'meterId', header: 'Meter ID', mono: true },
    { key: 'probability', header: 'Risk Score', align: 'right' },
    { key: 'env', header: 'Expected Net Value', align: 'right' },
  ];

  const mockData: TestItem[] = [
    { id: '1', meterId: 'CONS_1042', probability: '84.2%', env: '₹14,200' },
    { id: '2', meterId: 'CONS_2091', probability: '71.5%', env: '₹8,450' },
  ];

  it('renders columns and data rows with proper headers and alignment', () => {
    render(
      <DataTable
        columns={columns}
        data={mockData}
        keyExtractor={(item) => item.id}
      />
    );

    expect(screen.getByText('Meter ID')).toBeInTheDocument();
    expect(screen.getByText('Risk Score')).toBeInTheDocument();
    expect(screen.getByText('Expected Net Value')).toBeInTheDocument();
    expect(screen.getByText('CONS_1042')).toBeInTheDocument();
    expect(screen.getByText('₹14,200')).toBeInTheDocument();
  });

  it('renders loading indicator when loading is true', () => {
    render(
      <DataTable
        columns={columns}
        data={[]}
        keyExtractor={(item) => item.id}
        loading
      />
    );

    expect(screen.getByText('Loading records...')).toBeInTheDocument();
  });

  it('renders empty message when data is empty and not loading', () => {
    render(
      <DataTable
        columns={columns}
        data={[]}
        keyExtractor={(item) => item.id}
        emptyMessage="No inspection candidates found."
      />
    );

    expect(screen.getByText('No inspection candidates found.')).toBeInTheDocument();
  });

  it('handles row selection via click and keyboard Enter', () => {
    const handleRowClick = vi.fn();
    render(
      <DataTable
        columns={columns}
        data={mockData}
        keyExtractor={(item) => item.id}
        onRowClick={handleRowClick}
        selectedKey="1"
      />
    );

    const firstRow = screen.getByText('CONS_1042').closest('tr');
    expect(firstRow).toHaveClass('gg-table__row--selected');

    const secondRow = screen.getByText('CONS_2091').closest('tr');
    fireEvent.click(secondRow!);
    expect(handleRowClick).toHaveBeenCalledWith(mockData[1]);

    fireEvent.keyDown(firstRow!, { key: 'Enter', code: 'Enter' });
    expect(handleRowClick).toHaveBeenCalledWith(mockData[0]);
  });
});
