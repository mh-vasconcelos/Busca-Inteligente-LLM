# busca.py
from rapidfuzz import process, fuzz
import pandas as pd
import unicodedata

def carregar_sinonimos(caminho_arquivo):
    """
    Lê o arquivo synonyms.txt e cria um dicionário de substituição.
    Entrada: "tinta, tingir => Tintura"
    Saída: {'tinta': 'Tintura', 'tingir': 'Tintura'}
    """
    mapper = {}
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            for linha in f:
                if not linha.strip() or linha.startswith("#"):
                    continue

                # Quebra a linha na seta "=>"
                if "=>" in linha:
                    termos_errados_str, termo_correto = linha.split("=>")
                    termo_correto = termo_correto.strip()
                    
                    # Cria a entrada no dicionário para cada variação
                    variacoes = termos_errados_str.split(",")
                    for v in variacoes:
                        chave = v.strip().lower() # Normaliza para minúsculo
                        if chave:
                            mapper[chave] = termo_correto.strip().lower()
        return mapper
    except FileNotFoundError:
        print("Arquivo de sinônimos não encontrado.")
        return {}

def aplicar_sinonimos_na_query(query_usuario, mapper):
    """
    Pega a frase do usuário e troca as palavras usando o mapper.
    Ex: "comprar tinta loreal" -> "comprar Tintura L'Oréal"
    """
    palavras = query_usuario.lower().split()
    nova_query = []
    
    for palavra in palavras:
        # Se a palavra existe no dicionário, usa a tradução. 
        # Se não, usa a palavra original.
        palavra_traduzida = mapper.get(palavra, palavra)
        nova_query.append(palavra_traduzida)
    
    return " ".join(nova_query)

def remover_acentos(texto: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', texto)
    return "".join(c for c in nfkd_form if not unicodedata.combining(c))

def normalizar_dataframe(df):
    """
    Normaliza todas as colunas de texto de um DataFrame.

    Para cada coluna de texto, esta função:
    1. Preenche valores nulos com uma string vazia.
    2. Converte todo o texto para minúsculas.
    3. Remove acentos e caracteres de combinação.

    Args:
        df (pd.DataFrame): O DataFrame de entrada.

    Returns:
        pd.DataFrame: Um novo DataFrame com as colunas de texto normalizadas.
    """
    df = df.copy()
    colunas_texto = df.select_dtypes(include=['object', 'string']).columns
    for col in colunas_texto:
        df[col] = (
            df[col]
            .fillna('')         
            .astype(str)        
            .str.lower()        
            .apply(remover_acentos)
        )
    
    return df



STOPWORDS_PT = {
    'de', 'da', 'do', 'das', 'dos', 
    'e', 'ou', 'com', 'sem', 'para', 'p', 'pro', 'pra', 
    'em', 'no', 'na', 'kit', 'unid', 'un', 'ml', 'g'
}

def limpar_stopwords(texto):
    """Remove palavras inúteis da frase."""
    palavras = texto.lower().split()
    palavras_uteis = [p for p in palavras if p not in STOPWORDS_PT]
    return " ".join(palavras_uteis) if palavras_uteis else texto

def calcular_melhor_token(query_completa, conteudo_alvo, metodo='ratio'):
    """Testa palavra por palavra para evitar ruído de frases longas."""
    palavras_query = query_completa.split()
    melhor_score = 0
    
    for palavra in palavras_query:
        if len(palavra) < 2 or palavra in STOPWORDS_PT: continue
        
        if metodo == 'ratio':
            score = fuzz.ratio(palavra, conteudo_alvo)
        elif metodo == 'partial':
            score = fuzz.partial_ratio(palavra, conteudo_alvo)
            
        if score > melhor_score:
            melhor_score = score
    return melhor_score

def buscar_com_ia(query_usuario, df, mapper=None):
    query_normalizada = remover_acentos(query_usuario).lower()

    if mapper:
        query_tratada = aplicar_sinonimos_na_query(query_normalizada, mapper)
    else:
        query_tratada = query_normalizada

    query_limpa = limpar_stopwords(query_tratada)
    
    REGRAS_PESOS = {
            'marca':        (4, 80),  # Só ganha 4x se for >80% igual 
            'tipo_produto': (3, 70),  # Só ganha 3x se for >70% igual
            'linha':        (2, 70),  
            'nome_cor':     (3, 85),  # Cor tem que ser precisa
            'numero_cor':   (5, 95),  # Numeração tem que ser exata
            'ingredientes_destaque': (3,70),
            'beneficio_principal': (3,75),
            'apresentacao': (3,75),
            'finalidade_uso': (3,75),
            'composicao_especifica': (3,75),
            'soup':         (1, 60)   # Soup aceita match mais solto
        }
    
    resultados_bons = []
    
    for idx, row in df.iterrows():
        score_total_produto = 0
        motivos = []
        
        for col, (peso, threshold_minimo) in REGRAS_PESOS.items():
            if col not in df.columns or pd.isna(row[col]): continue
            conteudo = str(row[col]).lower()
            
            # SELEÇÃO DE ESTRATÉGIA 
            # mais rigoroso => nome do produto ou cor
            if col in ['tipo_produto', 'nome_cor']:
                score_base = calcular_melhor_token(query_limpa, conteudo, metodo='ratio')
            # menos rigoroso => nomes maiores
            elif col in ['ingredientes_destaque', 'apresentacao']:
                score_base = calcular_melhor_token(query_limpa, conteudo, metodo='partial')
            # complexo
            elif col == 'marca':
                score_base = fuzz.partial_token_set_ratio(query_limpa, conteudo)
            # default
            else:
                score_base = fuzz.token_set_ratio(query_limpa, conteudo)
            
            # --- CONFIDENCE GATE ---
            if score_base >= threshold_minimo:
                pontos = score_base * peso
                score_total_produto += pontos
                motivos.append(f"{col}({score_base})")
        
        if score_total_produto > 0:
            resultados_bons.append({
                "produto": row['input_original'],
                "score": score_total_produto,
                "motivo": ", ".join(motivos),
                "debug": f"Marca: {row.get('marca')} | Tipo: {row.get('tipo_produto')}"
            })
            
    return sorted(resultados_bons, key=lambda x: x['score'], reverse=True)[:5]


