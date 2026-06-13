import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'

vi.mock('../../api', () => ({
  animaisApi: {
    adoptionMetrics: vi.fn(() =>
      Promise.resolve({
        days: [
          { day: '2024-06-01', count: 2 },
          { day: '2024-06-02', count: 1 },
        ],
      })
    ),
  },
}))

vi.mock('@nivo/line', () => ({
  ResponsiveLine: () => <div data-testid="adoption-chart-mock" />,
}))

import AdoptionChart from '../AdoptionChart'

describe('AdoptionChart', () => {
  it('renderiza sem erro com dados mockados', async () => {
    render(<AdoptionChart />)

    expect(screen.getByText(/Adoções realizadas nos últimos 7 dias/i)).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByTestId('adoption-chart-mock')).toBeInTheDocument()
    })
  })
})
