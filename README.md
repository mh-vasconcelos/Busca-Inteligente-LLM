# 🛍️ Retail Smart Search & MDM Normalizer with GenAI

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![GenAI](https://img.shields.io/badge/GenAI-Gemini%20%2F%20Qwen-green)
![Data Science](https://img.shields.io/badge/Data-Engineering-orange)
![Status](https://img.shields.io/badge/Status-PoC%20Validated-success)

> **De "Busca Burra" para Busca Semântica:** Um pipeline de engenharia de dados que utiliza LLMs para normalizar cadastros sujos de varejo e um motor de busca híbrido (Lexical + Semantic Weights) para recuperar produtos com precisão.

---

## 🎯 O Problema
No varejo farmacêutico e de cosméticos, os dados de produtos (MDM) frequentemente chegam "sujos" e despadronizados:
* **Abreviações Crípticas:** `SHP`, `COND`, `ESM`, `REC INT`.
* **Hierarquias Quebradas:** Shampoos categorizados como "Acessórios".
* **Busca Falha:** Procurar por *"Manteiga de Karité"* retorna *"Grampo Manu"* (devido à coincidência de letras), enquanto o produto real não aparece.

## 🚀 A Solução
Este projeto implementa uma arquitetura em duas fases:
1.  **Normalização & Enriquecimento (LLM):** Uma IA Generativa varre as descrições, identifica o contexto (Cabelo vs. Unha) e preenche um Schema JSON rigoroso, inferindo atributos que não estavam explícitos.
2.  **Motor de Busca Ponderado (Weighted Search):** Um algoritmo de busca customizado que corrige a query do usuário e aplica pesos diferentes para Marca, Tipo e Atributos.

---

## 🛠️ Arquitetura do Pipeline

### 1. Ingestão e Roteamento
O sistema lê CSVs brutos e utiliza um **Semantic Router** simples.
- Se o produto for identificado como *Haircare*, ele é enviado para o `Schema A`.
- Se for *Manicure*, é enviado para o `Schema B`.
- **Benefício:** Evita alucinações (ex: IA inventar "tipo de cacho" para um alicate de unha).

### 2. LLM como Extrator de Atributos
Utilizando Engenharia de Prompt (Few-Shot & Chain-of-Thought), o modelo (ex: Gemini/Qwen) transforma:
* **Input:** `"MASCARA AMEND REC INT COLOR REFLECT"`
* **Output (JSON Enriquecido):**
    ```json
    {
      "tipo_produto": "Máscara",
      "marca": "Amend",
      "linha": "Color Reflect",
      "beneficio_principal": "Reconstrução Interna",
      "publico_alvo": "Cabelos Tingidos" // Inferido pelo contexto "Color Reflect"
    }
    ```

### 3. Motor de Busca Híbrido (The Search Engine)
Diferente de buscas vetoriais puras (que são caras) ou buscas textuais simples (que erram muito), criei um algoritmo **Field-Aware**:

* **Camada 1: Spellcheck Contextual ("Did You Mean")**
    * Corrige `xampu elserve` para `Shampoo Elseve` comparando com o dicionário de marcas reais do dataset.
* **Camada 2: Weighted Multi-Field Scoring**
    * A busca é comparada campo a campo com pesos dinâmicos:
        * 🔴 **Marca:** Peso 4x (Threshold rígido: >80%)
        * 🟡 **Tipo/Cor:** Peso 3x
        * 🔵 **Descrição Geral (Soup):** Peso 1x
    * **Confidence Gate:** Se o match de um campo for baixo (ex: 40%), a pontuação é zerada para evitar falsos positivos.

---

## 📊 Metodologia e Validação

Para garantir que o sistema não é apenas um "wrapper de API", foi aplicada metodologia científica de Data Science:

### Validação com Golden Set
Criou-se um **Golden Set** (Gabarito manual) para uma amostra de queries desafiadoras.

### Métricas (F1-Score)
O desempenho do buscador é medido por:
* **Precision:** Dos produtos retornados, quantos são relevantes? (Evita mostrar "Grampo" na busca de "Manteiga").
* **Recall:** Dos produtos relevantes existentes, quantos foram encontrados?
* **F1-Score:** A média harmônica que define o sucesso do projeto.

---

## 💻 Como Executar

### Pré-requisitos
* Python 3.9+
* Chave de API (Google Gemini ou OpenAI)

### Instalação
1. Clone o repositório:
   ```bash
   git clone [https://github.com/seu-usuario/retail-smart-search.git](https://github.com/seu-usuario/retail-smart-search.git)
