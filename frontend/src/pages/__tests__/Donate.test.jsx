import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi, beforeEach, afterEach } from 'vitest'

vi.mock('../../api', () => ({
  animaisApi: {
    create: vi.fn(() => Promise.resolve({ ok: true })),
  },
}))

import Donate from '../Donate'
import * as api from '../../api'

describe('Donate (page)', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ secure_url: 'https://cdn.example/pet.jpg' }),
      })
    )
  })

  afterEach(() => {
    global.fetch = originalFetch
  })

  async function selectOption(labelPattern, optionName) {
    fireEvent.mouseDown(screen.getByRole('combobox', { name: labelPattern }))
    const listbox = await screen.findByRole('listbox')
    fireEvent.click(within(listbox).getByRole('option', { name: optionName }))
  }

  async function fillRequiredFields() {
    await screen.findByText(/Cadastrar animal para adoção/i)

    fireEvent.change(screen.getByRole('textbox', { name: /Nome do animal/i }), {
      target: { value: 'Thor' },
    })
    await selectOption(/Espécie/i, 'Gato')
    fireEvent.change(screen.getByRole('spinbutton', { name: /Idade \(em anos\)/i }), {
      target: { value: '3' },
    })
    await selectOption(/Porte/i, 'Médio')
    fireEvent.change(screen.getByRole('textbox', { name: /^Descrição/i }), {
      target: { value: 'Animal dócil e brincalhão' },
    })
    fireEvent.change(screen.getByRole('textbox', { name: /Cidade/i }), {
      target: { value: 'Joinville - SC' },
    })
    fireEvent.change(screen.getByRole('textbox', { name: /Seu Nome/i }), {
      target: { value: 'Ana' },
    })
    fireEvent.change(screen.getByRole('textbox', { name: /WhatsApp/i }), {
      target: { value: '47999999999' },
    })
  }

  it(
    'preenche campos, faz upload mockado e submete o formulário',
    async () => {
      const user = userEvent.setup()

      render(
        <MemoryRouter>
          <Routes>
            <Route path="/" element={<Donate />} />
            <Route path="/animais" element={<div>Página animais</div>} />
          </Routes>
        </MemoryRouter>
      )

      await fillRequiredFields()

      const fileInput = document.querySelector('input[type="file"]')
      const file = new File(['img'], 'pet.png', { type: 'image/png' })
      fireEvent.change(fileInput, { target: { files: [file] } })

      await waitFor(() => {
        expect(screen.getByText(/Foto selecionada com sucesso/i)).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /Anunciar para Adoção/i }))

      await waitFor(() => {
        expect(api.animaisApi.create).toHaveBeenCalled()
        expect(screen.getByText(/Página animais/i)).toBeInTheDocument()
      })
    },
    15000
  )

  it('exibe erro ao submeter sem foto', async () => {
    render(
      <MemoryRouter>
        <Donate />
      </MemoryRouter>
    )

    await fillRequiredFields()
    fireEvent.submit(document.querySelector('form'))

    expect(await screen.findByText(/adicione uma foto do animal/i)).toBeInTheDocument()
    expect(api.animaisApi.create).not.toHaveBeenCalled()
  }, 10000)

  it('altera espécie para Outro e exige espécie customizada', async () => {
    render(
      <MemoryRouter>
        <Donate />
      </MemoryRouter>
    )

    await screen.findByText(/Cadastrar animal para adoção/i)
    await selectOption(/Espécie/i, 'Outro')
    expect(await screen.findByRole('textbox', { name: /Qual espécie/i })).toBeInTheDocument()

    fireEvent.change(screen.getByRole('textbox', { name: /Nome do animal/i }), {
      target: { value: 'Piu' },
    })
    await selectOption(/Porte/i, 'Pequeno')
    fireEvent.change(screen.getByRole('textbox', { name: /^Descrição/i }), {
      target: { value: 'Ave amigável' },
    })
    fireEvent.change(screen.getByRole('textbox', { name: /Cidade/i }), {
      target: { value: 'Curitiba - PR' },
    })

    const fileInput = document.querySelector('input[type="file"]')
    const file = new File(['img'], 'pet.png', { type: 'image/png' })
    fireEvent.change(fileInput, { target: { files: [file] } })
    await waitFor(() => {
      expect(screen.getByText(/Foto selecionada com sucesso/i)).toBeInTheDocument()
    })

    fireEvent.submit(document.querySelector('form'))

    expect(
      await screen.findByText(/especifique qual é a espécie do animal/i)
    ).toBeInTheDocument()
  }, 10000)

  it('altera campos opcionais, energia, crianças e submete espécie Outro customizada', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <Routes>
          <Route path="/" element={<Donate />} />
          <Route path="/animais" element={<div>Lista animais</div>} />
        </Routes>
      </MemoryRouter>
    )

    await screen.findByText(/Cadastrar animal para adoção/i)
    fireEvent.change(screen.getByRole('textbox', { name: /Nome do animal/i }), {
      target: { value: 'Coelho' },
    })
    await selectOption(/Espécie/i, 'Outro')
    fireEvent.change(screen.getByRole('textbox', { name: /Qual espécie/i }), {
      target: { value: 'Coelho' },
    })
    fireEvent.change(screen.getByRole('textbox', { name: /Raça/i }), {
      target: { value: 'Angorá' },
    })
    await selectOption(/Porte/i, 'Pequeno')
    await selectOption(/Nível de Energia/i, /Baixa/i)
    await selectOption(/Bom com Crianças/i, 'Sim')
    fireEvent.change(screen.getByRole('textbox', { name: /^Descrição/i }), {
      target: { value: 'Coelho dócil' },
    })
    fireEvent.change(screen.getByRole('textbox', { name: /Cidade/i }), {
      target: { value: 'Florianópolis - SC' },
    })

    const fileInput = document.querySelector('input[type="file"]')
    fireEvent.change(fileInput, { target: { files: [new File(['img'], 'pet.png', { type: 'image/png' })] } })
    await waitFor(() => expect(screen.getByText(/Foto selecionada com sucesso/i)).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: /Anunciar para Adoção/i }))

    await waitFor(() => {
      expect(api.animaisApi.create).toHaveBeenCalledWith(
        expect.objectContaining({ especie: 'Coelho', raca: 'Angorá', energia: 'Baixa', bom_com_criancas: 1 })
      )
      expect(screen.getByText(/Lista animais/i)).toBeInTheDocument()
    })
  }, 15000)

  it('volta de Outro para Cachorro e oculta campo customizado', async () => {
    render(
      <MemoryRouter>
        <Donate />
      </MemoryRouter>
    )

    await screen.findByText(/Cadastrar animal para adoção/i)
    await selectOption(/Espécie/i, 'Outro')
    expect(screen.getByRole('textbox', { name: /Qual espécie/i })).toBeInTheDocument()

    await selectOption(/Espécie/i, 'Cachorro')
    expect(screen.queryByRole('textbox', { name: /Qual espécie/i })).not.toBeInTheDocument()
  })

  it('exibe erro quando upload no Cloudinary falha', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ error: { message: 'Upload rejeitado' } }),
      })
    )

    render(
      <MemoryRouter>
        <Donate />
      </MemoryRouter>
    )

    await screen.findByText(/Cadastrar animal para adoção/i)
    const fileInput = document.querySelector('input[type="file"]')
    fireEvent.change(fileInput, { target: { files: [new File(['img'], 'pet.png', { type: 'image/png' })] } })

    expect(await screen.findByText(/Upload rejeitado/i)).toBeInTheDocument()
  })

  it('exibe erro de API ao cadastrar animal', async () => {
    api.animaisApi.create.mockRejectedValueOnce(new Error('Falha no servidor'))

    render(
      <MemoryRouter>
        <Donate />
      </MemoryRouter>
    )

    await fillRequiredFields()
    const fileInput = document.querySelector('input[type="file"]')
    fireEvent.change(fileInput, { target: { files: [new File(['img'], 'pet.png', { type: 'image/png' })] } })
    await waitFor(() => expect(screen.getByText(/Foto selecionada com sucesso/i)).toBeInTheDocument())

    fireEvent.submit(document.querySelector('form'))

    expect(await screen.findByText(/Falha no servidor/i)).toBeInTheDocument()
  }, 10000)
})
