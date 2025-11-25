import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AnimalCard from "../AnimalCard";

describe("AnimalCard", () => {
  const baseAnimal = {
    id: 42,
    nome: "Mingau",
    especie: "Gato",
    raca: null,
    idade: "2",
    porte: "Pequeno",
    descricao: "Fofo e brincalhão",
    cidade: "Curitiba",
    photo_url: null,
    adotado_em: null,
    donor_whatsapp: null,
  };

  it("exibe informações básicas do animal", () => {
    render(<AnimalCard animal={baseAnimal} />);

    expect(screen.getByRole("heading", { name: /mingau/i })).toBeInTheDocument();

    // espécie / idade / cidade
    expect(screen.getByText(/gato/i)).toBeInTheDocument();
    expect(screen.getByText(/\b2\b/)).toBeInTheDocument();
    expect(screen.getByText(/curitiba/i)).toBeInTheDocument();

    // descrição
    expect(screen.getByText(/Fofo e brincalhão/i)).toBeInTheDocument();

    // não deve mostrar chip "meu" por padrão
    expect(screen.queryByText(/meu/i)).toBeNull();

    // não deve mostrar o link para WhatsApp por padrão
    expect(screen.queryByRole("link", { name: /falar com doador/i })).toBeNull();
  });

  it("mostra chip 'meu' quando isMine=true", () => {
    render(<AnimalCard animal={baseAnimal} isMine={true} />);
    expect(screen.getByText(/meu/i)).toBeInTheDocument();
  });

  it("mostra link para WhatsApp quando donor_whatsapp existe", async () => {
    const withWhatsapp = { ...baseAnimal, donor_whatsapp: "5511999999999" };
    render(<AnimalCard animal={withWhatsapp} />);

    // MUI Button com href vira <a> (role 'link')
    const waLink = screen.getByRole("link", { name: /falar com doador/i });
    expect(waLink).toBeInTheDocument();
    expect(waLink).toHaveAttribute(
      "href",
      expect.stringContaining("https://wa.me/5511999999999")
    );

    //  simula clique — não navega no teste,mas garante que é interativo
    await userEvent.click(waLink);
  });
});
