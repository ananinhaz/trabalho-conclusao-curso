import React from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import { vi } from "vitest";

vi.mock("../../api", () => {
  return {
    animaisApi: {
      list: vi.fn(() =>
        Promise.resolve([
          {
            id: 1,
            nome: "Bolt",
            especie: "cachorro",
            idade: "2",
            cidade: "Curitiba",
            photo_url: null,
            bom_com_criancas: 0,
            adotado_em: null,
          },
        ])
      ),
      count: vi.fn(() => Promise.resolve({ count: 1 })),
    },
  };
});

import MetricsCards from "../MetricsCards";

describe("MetricsCards", () => {
  it("renderiza sem crash e mostra métricas vindas da API", async () => {
    render(<MetricsCards />);

    // Título geral
    expect(screen.getByText(/Visão rápida/i)).toBeInTheDocument();

    // Aguarda os blocos de métricas renderizarem.
    await waitFor(async () => {
      // Verifica que existe o card "Total de anúncios" e que dentro dele aparece '1'
      const totalCard = screen.getByText(/Total de anúncios/i).closest("div");
      expect(totalCard).toBeTruthy();
      // procura dentro do card (evita confusão com outros "1")
      const totalNode = within(totalCard).getAllByText("1");
      expect(totalNode.length).toBeGreaterThanOrEqual(1);

      // Verifica bloco "Disponíveis"
      const disponiveisCard = screen.getByText(/Disponíveis/i).closest("div");
      expect(disponiveisCard).toBeTruthy();
      const dispoValue = within(disponiveisCard).getAllByText("1");
      expect(dispoValue.length).toBeGreaterThanOrEqual(1);

      // Verifica distribuição por espécies (label)
      expect(screen.getByText(/Distribuição por espécies/i)).toBeInTheDocument();
      // e que uma espécie do mock aparece
      expect(screen.getByText(/cachorro/i)).toBeInTheDocument();

      // verifica presença de porcentagem (ex: "100 %")
      expect(screen.getByText(/%/)).toBeInTheDocument();
    });
  });
});
