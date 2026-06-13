import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi, beforeEach, afterEach } from 'vitest'
import Animals from '../Animals'
import * as api from '../../api'

const allAnimals = [
  {
    id: 1,
    nome: 'Rex',
    especie: 'Cachorro',
    porte: 'Médio',
    cidade: 'São Paulo',
    idade: '2',
    energia: 'Média',
    bom_com_criancas: 1,
    descricao: 'Cachorro amigável',
    photo_url: 'https://example.com/rex.jpg',
    doador_id: 1,
  },
  {
    id: 2,
    nome: 'Luna',
    especie: 'Gato',
    porte: 'Pequeno',
    cidade: 'Curitiba',
    idade: '1',
    energia: 'Baixa',
    bom_com_criancas: 0,
    descricao: 'Gata tranquila',
    photo_url: 'https://example.com/luna.jpg',
    doador_id: 99,
    donor_whatsapp: '5511999999999',
  },
]

const mineAnimals = [allAnimals[0]]
const recItems = [{ id: 2, nome: 'Luna', especie: 'Gato', porte: 'Pequeno', cidade: 'Curitiba', idade: '1' }]

async function selectFilter(labelPattern, optionName) {
  fireEvent.mouseDown(screen.getByRole('combobox', { name: labelPattern }))
  const listbox = await screen.findByRole('listbox')
  fireEvent.click(within(listbox).getByRole('option', { name: optionName }))
}

describe('Animals (page)', () => {
  beforeEach(() => {
    vi.spyOn(api.animaisApi, 'list').mockResolvedValue(allAnimals)
    vi.spyOn(api.animaisApi, 'mine').mockResolvedValue(mineAnimals)
    vi.spyOn(api.recApi, 'list').mockResolvedValue({ items: recItems, ids: [2] })
    vi.spyOn(api.authApi, 'me').mockResolvedValue({ authenticated: true, user: { id: 1, nome: 'Ana' } })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  async function renderAnimals() {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<Animals user={{ id: 1, nome: 'Ana' }} />} />
          <Route path="/doar" element={<div>Página doar</div>} />
          <Route path="/animais/editar/:id" element={<div>Editar animal</div>} />
        </Routes>
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByText('Animais para adoção')).toBeInTheDocument()
      expect(screen.getByText('Rex')).toBeInTheDocument()
    })
    return user
  }

  it('alterna entre tabs Meus anúncios, Recomendados e Quero doar', async () => {
    const user = await renderAnimals()

    await user.click(screen.getByRole('button', { name: /Meus anúncios/i }))
    expect(screen.getByText('Rex')).toBeInTheDocument()
    expect(screen.queryByText('Luna')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Recomendados/i }))
    await waitFor(() => {
      expect(screen.getByText('Luna')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /Quero doar/i }))
    expect(screen.getByText(/Página doar/i)).toBeInTheDocument()
  }, 10000)

  it('aplica filtros de espécie, idade, porte e limpa filtros', async () => {
    const user = await renderAnimals()

    await selectFilter(/espécie/i, 'Gato')
    await waitFor(() => {
      expect(screen.getByText('Luna')).toBeInTheDocument()
      expect(screen.queryByText('Rex')).not.toBeInTheDocument()
    })

    await selectFilter(/idade/i, 'Filhote')
    await selectFilter(/porte/i, 'Pequeno')

    await user.click(screen.getByRole('button', { name: /LIMPAR FILTROS/i }))

    await waitFor(() => {
      expect(screen.getByText('Rex')).toBeInTheDocument()
      expect(screen.getByText('Luna')).toBeInTheDocument()
    })
  }, 10000)

  it('visitante vê botão Adotar / Interesse com link WhatsApp', async () => {
    await renderAnimals()

    const adoptBtn = await screen.findByRole('link', { name: /Adotar \/ Interesse/i })
    expect(adoptBtn).toHaveAttribute('href', expect.stringContaining('5511999999999'))
  })

  it('dono pode editar o próprio anúncio', async () => {
    const user = await renderAnimals()
    await user.click(screen.getByRole('button', { name: /Meus anúncios/i }))
    await user.click(screen.getByRole('button', { name: /^Editar$/i }))
    expect(screen.getByText(/Editar animal/i)).toBeInTheDocument()
  })

  it('dono pode marcar animal como adotado', async () => {
    const user = await renderAnimals()
    vi.spyOn(api.animaisApi, 'adopt').mockResolvedValue({
      animal: { ...mineAnimals[0], adotado_em: '2024-06-01' },
    })
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    await user.click(screen.getByRole('button', { name: /Meus anúncios/i }))
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Marcar como adotado/i })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /Marcar como adotado/i }))

    await waitFor(() => {
      expect(api.animaisApi.adopt).toHaveBeenCalledWith(1, { action: 'mark' })
    })
  })

  it('dono pode excluir o próprio anúncio', async () => {
    const user = await renderAnimals()
    vi.spyOn(api.animaisApi, 'remove').mockResolvedValue({ ok: true })
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    await user.click(screen.getByRole('button', { name: /Meus anúncios/i }))
    await user.click(screen.getByRole('button', { name: /^Excluir$/i }))

    await waitFor(() => {
      expect(api.animaisApi.remove).toHaveBeenCalledWith(1)
    })
  })

  it('volta para tab Todos e filtra por cidade', async () => {
    const user = await renderAnimals()

    await user.click(screen.getByRole('button', { name: /Meus anúncios/i }))
    await user.click(screen.getByRole('button', { name: /^Todos$/i }))

    await waitFor(() => {
      expect(screen.getByText('Rex')).toBeInTheDocument()
      expect(screen.getByText('Luna')).toBeInTheDocument()
    })

    const cidadeInput = screen.getByPlaceholderText('Cidade')
    fireEvent.change(cidadeInput, { target: { value: 'Curitiba' } })

    await waitFor(() => {
      expect(screen.getByText('Luna')).toBeInTheDocument()
      expect(screen.queryByText('Rex')).not.toBeInTheDocument()
    })
  }, 10000)

  it('não marca adotado quando usuário cancela confirmação', async () => {
    const user = await renderAnimals()
    vi.spyOn(api.animaisApi, 'adopt').mockResolvedValue({ animal: mineAnimals[0] })
    vi.spyOn(window, 'confirm').mockReturnValue(false)

    await user.click(screen.getByRole('button', { name: /Meus anúncios/i }))
    await user.click(screen.getByRole('button', { name: /Marcar como adotado/i }))

    expect(api.animaisApi.adopt).not.toHaveBeenCalled()
  })

  it('desfaz adoção e usa fallback local quando API não retorna animal', async () => {
    const adopted = { ...mineAnimals[0], adotado_em: '2024-01-01' }
    vi.spyOn(api.animaisApi, 'mine').mockResolvedValue([adopted])
    vi.spyOn(api.animaisApi, 'adopt').mockResolvedValue({})
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    const user = await renderAnimals()
    await user.click(screen.getByRole('button', { name: /Meus anúncios/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Marcar como disponível/i })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /Marcar como disponível/i }))

    await waitFor(() => {
      expect(api.animaisApi.adopt).toHaveBeenCalledWith(1, { action: 'undo' })
    })
  })

  it('exibe mensagem quando filtros não retornam resultados', async () => {
    await renderAnimals()

    await selectFilter(/espécie/i, 'Gato')
    await selectFilter(/idade/i, 'Idoso')

    await waitFor(() => {
      expect(screen.getByText(/Nenhum resultado/i)).toBeInTheDocument()
    })
  })
})
