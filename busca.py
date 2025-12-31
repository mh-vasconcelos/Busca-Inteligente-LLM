from rapidfuzz import fuzz
import pandas as pd

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
                # Ignora comentários e linhas vazias
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
                            mapper[chave] = termo_correto
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



# def buscar_com_ia(query_usuario, df, mapper):
#     # Passo A: Traduzir a intenção
#     query_tunada = aplicar_sinonimos_na_query(query_usuario, mapper)
#     print(f"IA Interpretou: '{query_usuario}' --> '{query_tunada}'")
    
#     resultados_bons = []
#     todos_resultados = []
    
#     # Passo B: Calcular Score para TODOS os produtos
#     for idx, row in df.iterrows():
#         full_text = str(row['soup']).lower()
        
#         #partial garante que "disco de algodao" tenha boa correspondencia com "disco", por exemplo.
#         score = fuzz.token_set_ratio(query_tunada, full_text)
        
#         item = {
#             "produto_original": row['input_original'],
#             "interpretacao_ia": f"{row['familia_origem']} {row['marca']}",
#             "score": round(score, 1)
#         }
        
#         todos_resultados.append(item)
        
#         if score >= 65:
#             resultados_bons.append(item)
    
#     # Passo C: Lógica de Fallback (Plano B)
#     if len(resultados_bons) == 0:
#         print("⚠️ Nenhum match acima do treeshold encontrado. Exibindo resultados aproximados (Fallback).")
#         todos_ordenados = sorted(todos_resultados, key=lambda x: x['score'], reverse=True)
#         return todos_ordenados[:5]
            
#     # Passo D: Se achou coisa boa, ordena e retorna só os bons
#     resultados_finais = sorted(resultados_bons, key=lambda x: x['score'], reverse=True)
    
#     return resultados_finais[:5]

from rapidfuzz import process, fuzz
import numpy as np

def buscar_com_ia(query_usuario, df, mapper):
    # --- CONFIGURAÇÃO INTELIGENTE ---
    # Estrutura: 'coluna': (Peso, Threshold_Minimo)
    # Threshold_Minimo: Nota mínima (0-100) para o peso ser ativado.
    # Isso impede que "Amorável" (Score 43) ganhe peso 4x.
    REGRAS_PESOS = {
        'marca':        (4, 80),  # Só ganha 4x se for >80% igual (Evita ruído)
        'tipo_produto': (3, 70),  # Só ganha 3x se for >70% igual
        'linha':        (2, 70),  
        'nome_cor':     (3, 85),  # Cor tem que ser precisa
        'numero_cor':   (5, 95),  # Numeração tem que ser exata
        'ingredientes_destaque': (3,70),
        'beneficio_principal': (3,70),
        'soup':         (1, 60)   # Soup aceita match mais solto
    }
    
    # 1. Tratamento da Query
    query_tunada = aplicar_sinonimos_na_query(query_usuario, mapper)
    
    # 2. Correção de Marca (A "Vacina" para elserve -> Elseve)
    # Tenta achar token de marca dentro da query composta
    marcas_conhecidas = df['marca'].dropna().unique().tolist()
    
    # Busca parcial para pegar "Elseve" dentro de "Shampoo Elseve"
    match_marca_parcial = process.extractOne(
        query_tunada, 
        marcas_conhecidas, 
        scorer=fuzz.partial_ratio # Aqui o partial brilha!
    )
    
    if match_marca_parcial and match_marca_parcial[1] > 85:
        marca_detectada = match_marca_parcial[0]
        # Se achou a marca, garante que ela esteja escrita certa na query
        # Isso transforma "elserve" em "Elseve" implicitamente na comparação futura
        print(f"🔧 Marca Detectada na frase: '{marca_detectada}'")
        # Opcional: Você pode forçar a query a ser APENAS a marca ou concatenar
    
    resultados_bons = []
    todos_resultados = []
    
    # Passo B: Score Ponderado com Trava de Segurança
    for idx, row in df.iterrows():
        melhor_score_produto = 0
        campo_vencedor = "nenhum"
        
        for col, (peso, threshold_minimo) in REGRAS_PESOS.items():
            if col not in df.columns or pd.isna(row[col]): continue
            
            conteudo = str(row[col]).lower()
            if not conteudo: continue
            
            # Scorer Selection
            if col in ['marca', 'nome_cor', 'numero_cor']:
                # Marcas e Cores preferem match exato ou partial
                # Partial ajuda se query="Shampoo Elseve" e Marca="Elseve" -> 100%
                score_base = fuzz.token_set_ratio(query_tunada.lower(), conteudo)
            else:
                score_base = fuzz.token_set_ratio(query_tunada.lower(), conteudo)
            
            # --- O PULO DO GATO (CONFIDENCE GATE) ---
            if score_base < threshold_minimo:
                # Se o match foi ruim (ex: Amorável = 43), IGNORA O PESO.
                # Score final vira 0 ou muito baixo, matando o falso positivo.
                score_final = 0 
            else:
                score_final = score_base * peso
            
            if score_final > melhor_score_produto:
                melhor_score_produto = score_final
                campo_vencedor = col

        item = {
            "produto": row['input_original'],
            "score": melhor_score_produto,
            "motivo": f"Match: {campo_vencedor}"
        }
        
        todos_resultados.append(item)
        
        # Só aceita se tiver pontuado em algum critério relevante
        if melhor_score_produto > 0: 
            resultados_bons.append(item)
    
    # Ordenação e Retorno
    if not resultados_bons:
        print("⚠️ Sem resultados exatos.")
        return sorted(todos_resultados, key=lambda x: x['score'], reverse=True)[:5]
        
    return sorted(resultados_bons, key=lambda x: x['score'], reverse=True)[:5]