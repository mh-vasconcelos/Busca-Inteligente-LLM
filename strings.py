import pandas as pd

prompt_off = """
SYSTEM ROLE:
Você é um especialista em MDM de Farmácia e Perfumaria.
Sua missão é interpretar descrições de produtos abreviadas e estruturar os dados.

DICIONÁRIO DE SIGLAS (Para Interpretação):
- SHP = Shampoo
- COND = Condicionador
- HID = Hidratante
- LC = Loção
- AG / AG MICEL = Água Micelar
- PROT SOL / FPS = Protetor Solar
- ESM = Esmalte
- TINT = Tintura/Coloração
- DEO = Desodorante/Colônia

CONTEXTO SEMÂNTICO:
- 'CR' em Cabelo/Pele = "Creme" (Textura).
- 'CR' em Esmaltes = "Cremoso" (Acabamento).
- Numerações em TINTURAS (Ex: 7.1, 12.11) referem-se à COR/TOM.
- Nomes criativos após a marca em ESMALTES (Ex: "Deixa Rolar", "Renda") referem-se à COR.

PADRONIZAÇÃO:
- Normalizar unidades de medida (Ex: "100 ml" vira "100ml").
- Usar ponto para decimais.
"""

df = pd.read_csv('resultado_normalizacao_ia_unificado.csv')

# 1. Ajuste de Coluna: Usamos 'tipo_produto' que é a coluna padronizada no passo anterior
categorias_reais = sorted(df['tipo_produto'].dropna().unique())
marcas_reais = sorted(df['marca'].dropna().unique())

# Contexto para a IA não alucinar
lista_categorias_str = "\n".join([f"- {cat}" for cat in categorias_reais])
lista_marcas_str = ", ".join(marcas_reais[:20]) 


JSON_CABELO = """
{
  "identificacao_basica": {
    "tipo_produto": "Ex: Shampoo, Condicionador, Máscara, Tinta, Escova, Gel",
    "marca": "Ex: Elseve, Dove, Salon Line, L'Oréal",
    "linha": "Ex: Cachos dos Sonhos, Liso Intenso, Nutritive Solutions",
    "publico_alvo": "Ex: Adulto, Infantil, Masculino, Feminino",
    "apresentacao": "Ex: Frasco, Pote, Tubo, Kit, Sachê"
  },
  "atributos_tratamento": {
    "volume_peso": "Ex: 200ml, 1kg, 300g (Padronizar unidade)",
    "curvatura_indicada": "Ex: Liso, Ondulado, Cacheado, Crespo, Todos os tipos",
    "tipo_fio_condicao": "Ex: Oleoso, Seco, Misto, Danificado, Quimicamente Tratado",
    "beneficio_principal": "Ex: Hidratação, Reconstrução, Anticaspa, Antiqueda, Matizador",
    "ingredientes_destaque": "Ex: Queratina, Óleo de Coco, Babosa, Biotina",
    "tecnica_liberada": "Ex: Low Poo, No Poo (Preencher se explícito)"
  },
  "atributos_coloracao": {
    "tipo_coloracao": "Ex: Permanente, Semipermanente, Tonalizante, Descolorante",
    "tom_cor": "Ex: Louro Muito Claro, Castanho Escuro, Vermelho Intenso, Preto Azulado",
    "numero_cor": "Ex: 7.1, 12.11, 3.0 (Se houver)",
    "com_amonia": "Ex: Sim, Não"
  },
  "atributos_finalizacao_modelagem": {
    "textura_formato": "Ex: Creme, Gel, Óleo, Pomada, Spray, Mousse",
    "nivel_fixacao": "Ex: Leve, Média, Forte, Extra Forte (Para Gel/Pomada/Spray)",
    "efeito_visual": "Ex: Matte (Fosco), Molhado, Brilho",
    "protecao_termica": "Ex: Sim, Não"
  },
  "atributos_acessorios": {
    "tipo_acessorio": "Ex: Escova, Pente, Piranha, Touca, Elástico",
    "material": "Ex: Plástico, Madeira, Cerâmica, Bambu",
    "funcao_uso": "Ex: Desembaraçar, Modelar, Secar, Prender"
  }
}
"""

JSON_MANICURE = """
{
  "identificacao_basica": {
    "tipo_produto": "Ex: Esmalte, Alicate, Removedor, Lixa, Unha Postiça",
    "marca": "Ex: Risqué, Mundial, Impala",
    "linha": "Ex: Diamond Gel, Classic, Technology",
    "publico_alvo": "Ex: Adulto, Infantil, Profissional",
    "quantidade_embalagem": "Ex: 1 un, Kit 3 un, 12 pares"
  },
  "atributos_quimicos": {
    "volume_peso": "Ex: 8ml, 100ml, 50g (Apenas para líquidos/cremes)",
    "cor_visual": "Ex: Vermelho, Renda, Incolor, Preto (Apenas para Esmaltes/Unhas)",
    "nome_cor": "Ex: Gabriela, Rebu, Boneca (Nome fantasia da cor)",
    "acabamento_efeito": "Ex: Cremoso, Cintilante, Gel, Fosco, Glitter (Apenas para Esmaltes)",
    "funcao_tratamento": "Ex: Fortalecedor, Base Seda, Secante, Antimicótico",
    "composicao_especifica": "Ex: Com Acetona, Sem Acetona, Hipoalergênico, 5Free"
  },
  "atributos_instrumentos_acessorios": {
    "material": "Ex: Aço Inox, Aço Carbono, Madeira, Plástico, Vidro",
    "finalidade_uso": "Ex: Cutícula, Cortar Unha, Lixar, Empurrar",
    "tipo_ponta": "Ex: Ponta Fina, Ponta Reta, Curva (Para Alicates/Tesouras)",
    "esterilizavel": "Ex: Sim, Não (Autoclavável)",
    "gramatura_textura": "Ex: Polidora, Fina, Grossa (Para Lixas)"
  },
  "atributos_unhas_posticas": {
    "formato": "Ex: Quadrada, Bailarina, Stiletto, Amendoada",
    "metodo_fixacao": "Ex: Autocolante, Com Cola"
  }
}
"""

# prompt_dict= """
# SYSTEM ROLE:
# Você é um especialista em SEO e Engenharia de Busca para E-commerce Farmacêutico.
# Sua tarefa é gerar uma lista de sinônimos (Synonym Map) para corrigir termos de busca dos usuários.

# O FORMATO DE SAÍDA (Solr Format):
# termo_errado_1, termo_errado_2, giria, abreviacao => termo_padrao

# SEUS ALVOS (TERMOS PADRÃO):
# 1. Unidades: 'g', 'ml', 'mg', 'kg', 'un'
# 2. Categorias: 'Tintura', 'Esmalte', 'Protetor Solar', 'Xarope', 'Fralda'

# TAREFA:
# Para cada termo padrão acima, liste variações que usuários brasileiros reais digitam, incluindo:
# - Erros ortográficos comuns.
# - Abreviações informais.
# - Plurais e singulares.
# - Unidades escritas por extenso.

# EXEMPLO DE SAÍDA DESEJADA:
# gramas, grama, gr, grs, grm, gs => g
# mililitros, mili litros, ml., mls, m.l => ml
# tinta, coloracao, tingir cabelo, tinta de cabelo => Tintura
# esmalte de unha, base de unha, verniz => Esmalte
# protetor, filtro solar, bloqueador solar, sunblock => Protetor Solar

# OBSERVAÇÕES IMPORTANTES:
# 1. NÃO INVADIR CATEGORIAS: Jamais use o nome de uma Categoria Padrão como sinônimo de outra.
#    - Exemplo do ERRO: mapear 'creme => Hidratante' (Proibido, pois 'Creme' já é uma categoria própria).
#    - Exemplo do ERRO: mapear 'esmalte => Base' (Proibido, se 'Base' for uma categoria existente).
# 2. EXCLUSIVIDADE: Se a palavra já existe como termo padrão, ela não pode aparecer no lado esquerdo da seta (=>) de outro termo.

# Gere a lista completa agora.
# """