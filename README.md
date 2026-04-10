# ⚔ LoL Screen Translator

Traduz automaticamente textos do League of Legends para **Português BR** usando IA.

---

##  O que ele traduz?

- Descrições de **itens**
- Descrições de **habilidades** (Q/W/E/R/Passiva)
- Textos de **runas** e **feitiços**
- **Qualquer texto** visível na tela

---

## Instalação

### Pré-requisitos

| Programa | Link |
|----------|------|
| Python 3.10+ | https://www.python.org/downloads/ |
| Tesseract OCR | https://github.com/UB-Mannheim/tesseract/wiki |

> ⚠️ Ao instalar Python e Tesseract, marque **"Add to PATH"**!

 Passos

1. Extraia os arquivos em uma pasta
2. Dê duplo clique em **`instalar.bat`**
3. Aguarde a instalação terminar
4. Abra **`iniciar.bat`**

---

##  Configuração da API Key

O programa usa a API do Claude (Anthropic) para traduzir com precisão.

1. Crie uma conta gratuita em: https://console.anthropic.com
2. Gere uma API Key em *API Keys*
3. Cole no campo **"Anthropic API Key"** no programa e clique **Salvar**

A key fica salva no arquivo `.env` — você não precisa digitar toda vez.

---

## ⌨️ Como usar

| Tecla | Ação |
|-------|------|
| **F9** | Captura a região ao redor do mouse (ideal para tooltips) |
| **F10** | Captura a tela inteira |
| **F11** | Encerra o programa |

### Dica de uso no LoL

1. Passe o mouse **em cima de um item ou habilidade**
2. Aguarde o tooltip aparecer
3. Pressione **F9**
4. A tradução aparece em 2-3 segundos ✅

---

## 🖥️ Interface

- A **janela de controle** fica sempre no topo — você pode minimizá-la
- A **janela de tradução** aparece ao lado do mouse e fecha sozinha em 25s
- Você pode **arrastar** a janela de tradução

---

#  Problemas comuns

**"Tesseract não encontrado"**
→ Instale o Tesseract e reinicie o computador (ou abra novo terminal)

**"API Key inválida"**
→ Verifique se a key está correta em console.anthropic.com

**"Nenhum texto detectado"**
→ Tente F10 (tela inteira) em vez de F9; certifique-se que o jogo não está em modo exclusivo fullscreen (use Borderless Windowed)

**O jogo fica em fullscreen exclusivo e não captura**
→ Configure o LoL para **"Janela sem bordas"** (Borderless) nas configurações de vídeo
---
# Notas

- O programa **não interfere** no jogo — apenas lê a tela
- Não há risco de **ban** (funciona como um screenshot externo)
- Funciona com **qualquer idioma** do LoL
- Requer **conexão com internet** para traduzir
