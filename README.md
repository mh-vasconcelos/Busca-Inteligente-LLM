# 🔍 Busca Inteligente: Feature Extraction com LLM & Search Engine Híbrido

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Status](https://img.shields.io/badge/Status-Completed-success)
![Focus](https://img.shields.io/badge/Focus-NLP%20%26%20Information%20Retrieval-orange)

Este projeto implementa um **Motor de Busca Semântica Híbrido** focado em e-commerce (Higiene, Beleza e Varejo). O objetivo é resolver o problema da **ambiguidade na busca** e da **falta de estruturação de dados** em catálogos de produtos.

Diferente de buscas tradicionais (SQL `LIKE`), este sistema utiliza **Large Language Models (LLMs)** para estruturar dados brutos e **Lógica Fuzzy** segmentada para encontrar resultados precisos, mesmo com erros de digitação ou inversão de palavras.

---

## 💡 O Contexto e a Solução

### O Problema
Em catálogos de e-commerce, os títulos dos produtos são frequentemente uma "sopa de letrinhas" não estruturada (ex: *"Kit 3 Potes Creme Skala 1kg Expert Cachos"*). Isso gera dois problemas:
1.  **Busca Imprecisa:** Buscar por "Creme Expert" pode falhar se a string não for exata.
2.  **Falsos Positivos:** Buscar "Esmalte" retorna "Removedor de Esmalte".

### A Solução
Inspirado em papers de **Information Retrieval** (como o case PAVE da Magalu), desenhei uma arquitetura em 3 etapas:
1.  **Feature Extraction (LLM):** Uso de IA Generativa para "ler" o título e separar semanticamente o que é Marca, Linha, Volume e Benefício.
2.  **Normalização (AI-Assisted):** Criação automática de dicionários de sinônimos para corrigir erros de digitação do usuário.
3.  **Hybrid Search Engine:** Um algoritmo que decide qual estratégia matemática usar (Ratio, Partial ou Token Set) dependendo do atributo pesquisado.

---

## 📂 Arquitetura dos Scripts

O projeto é modularizado para separar a etapa de "Engenharia de Dados" (ETL/Offline) da etapa de "Busca" (Runtime).

### 1. `off.py` (O Engenheiro de Dados)
**Função:** Extração de Features Offline.
* Responsável por ler o dataset bruto (CSV com títulos bagunçados).
* Utiliza a API do **Groq (Modelo Qwen 2.5)** para processar cada título.
* **Prompt Engineering:** Força o LLM a retornar um JSON estruturado, ignorando ruídos e preenchendo lacunas.
* *Output:* Gera um CSV "Gold" com colunas separadas (`marca`, `linha`, `ingrediente_principal`, etc).

### 2. `mapper.py` (O Filólogo)
**Função:** Criação de Glossário e Sinônimos.
* Resolve o problema de vocabulário do usuário (ex: "Esmaute" vs "Esmalte").
* Utiliza a API do **Google Gemini** para ler as colunas únicas do dataset e gerar um arquivo `synonyms.txt` e dicionários Python.
* Padroniza termos regionais e variações de escrita para garantir que a busca funcione independente de como o usuário digita.

### 3. `busca.py` (O Coração do Motor)
**Função:** Lógica de Busca Híbrida (Fuzzy Logic).
* Aqui reside a inteligência algorítmica. Não tratamos todos os campos iguais. Implementa a arquitetura **"Scanner"**:
    * **Strict Matching (`fuzz.ratio`):** Para atributos curtos (Cor, Tipo), penalizando strings parecidas mas diferentes (evita falsos positivos).
    * **Partial Matching (`fuzz.partial_ratio`):** Para campos longos (Ingredientes), permitindo achar "Karité" dentro de "Manteiga de Karité".
    * **Token Set Ratio:** Para Marcas, resolvendo problemas de ordem ("Risqué Esmalte" == "Esmalte Risqué").
* Configuração de pesos (`REGRAS_PESOS`) para priorizar o que importa mais no negócio.

### 4. `main.py` (A Interface)
**Função:** Orquestração e Teste.
* Carrega os dados processados e o motor de busca.
* Simula queries de usuários para validar a eficácia do algoritmo.
* Exibe o ranking de relevância (Score 0-100) e os motivos do match.

---

## ⚠️ Disclaimer sobre os Dados

**Nota Importante:** O dataset original utilizado para treinar e validar este modelo **não está incluído neste repositório** por motivos de propriedade intelectual e privacidade.

### Como testar este projeto?
O código é agnóstico ao domínio. Para rodar na sua máquina:

1.  Crie um arquivo `.env` com suas chaves de API (`GROQ_API_KEY` e `GEMINI_API_KEY`).
2.  Adicione um arquivo `dataset.csv` na raiz com uma coluna de títulos de produtos.
3.  Ajuste o prompt no `off.py` para refletir as colunas que você deseja extrair do seu produto.
4.  Rode o pipeline:
    ```bash
    python off.py    # Gera os dados estruturados
    python mapper.py # Gera os sinônimos
    python main.py   # Roda a busca
    ```

---

## 🛠️ Tecnologias Utilizadas

* **Python 3.10+**
* **Pandas:** Manipulação de dados tabulares.
* **Rapidfuzz:** Biblioteca de alta performance para string matching (Lógica Fuzzy).
* **Groq API (Qwen 2.5):** LLM open-source para feature extraction de alta velocidade.
* **Google Gemini API:** LLM para tarefas de raciocínio e geração de sinônimos.

---

### 📬 Contato
Projeto desenvolvido como portfólio de **Engenharia de Machine Learning** e **NLP**.
Sinta-se à vontade para abrir issues ou sugerir melhorias na lógica de busca.
