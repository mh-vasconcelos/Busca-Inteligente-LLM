import os
from groq import Groq
from dotenv import load_dotenv
from strings import prompt_off, JSON_CABELO, JSON_MANICURE
import pandas as pd
import time
import json

load_dotenv()
    
SCHEMA_HAIRCARE = JSON_CABELO
SCHEMA_MANICURE = JSON_MANICURE

if not os.getenv("GROQ_API_KEY"):
    print("ERRO: A chave GROQ_API_KEY não foi encontrada no arquivo .env")
    exit()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

prompt_mdm = prompt_off

df = pd.read_csv('manicure_cabelo_total.csv') # Arquivo novo unificado
am_cabelo = df[df['categoria_familia'] == 'CUIDADO CAPILAR'].sample(50)
am_unha = df[df['categoria_familia'] == 'MANICURE E PEDICURE'].sample(50)
amostra = pd.concat([am_cabelo, am_unha])
dados_processados = []

for index, row in amostra.iterrows():
    produto_sujo = row['descricao_detalhada']
    familia = str(row['categoria_familia']).upper()
    
    # 1. ROTEADOR (Decide qual Schema usar)
    if "CUIDADO CAPILAR" in familia:
        schema_escolhido = SCHEMA_HAIRCARE
        role_especialista = "Especialista em Haircare e Tratamentos Capilares"
    elif "MANICURE" in familia:
        schema_escolhido = SCHEMA_MANICURE
        role_especialista = "Especialista em Manicure, Unhas e Acessórios"
    else:
        continue # Pula categorias desconhecidas

    # 2. CONTEXTO (Usa as colunas unificadas para dar dica a IA)
    contexto_auxiliar = f"Tipo: {row['tipo_produto']} | Detalhe: {row['subtipo_funcao']}"

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""
                    {prompt_off}
                    ATUE COMO: {role_especialista}
                    
                    REGRAS:
                    1. Analise o produto e preencha o JSON abaixo.
                    2. Se um campo não se aplicar ao produto, preencha como null.
                    
                    SCHEMA DE SAÍDA (JSON):
                    {schema_escolhido}
                    """, 
                },
                {
                    "role": "user",
                    "content": f"""
                    PRODUTO: {produto_sujo}
                    CONTEXTO TÉCNICO: {contexto_auxiliar}
                    """,
                }
            ],
            model="qwen/qwen3-32b", # Ou o modelo de sua preferência
            temperature=0, 
            response_format={"type": "json_object"}
        )
        
        # Processamento da Resposta
        resposta_texto = chat_completion.choices[0].message.content
        resposta_dict = json.loads(resposta_texto)
        
        # Achatar o JSON (Opcional, mas ajuda a salvar em CSV plano)
        # Se a IA retornar aninhado, você pode salvar o dict inteiro ou extrair chaves principais
        # Aqui salvamos o dict bruto + metadados
        flat_dict = {}
        for grupo, atributos in resposta_dict.items():
            if isinstance(atributos, dict):
                flat_dict.update(atributos)
            else:
                flat_dict[grupo] = atributos # Caso venha solto
                
        flat_dict["input_original"] = produto_sujo
        flat_dict["familia_origem"] = familia
        
        dados_processados.append(flat_dict)
        print(f"✅ Sucesso: {produto_sujo[:30]}...")

    except Exception as e:
        print(f"❌ Erro ao processar '{produto_sujo}': {e}")
    
    time.sleep(1) 


df_final = pd.DataFrame(dados_processados)

# Lista de colunas prioritárias para busca (junta as de Cabelo e Unha)
cols_soup = [
    'tipo_produto', 'marca', 'linha', 'nome_cor', 'cor_visual', 
    'acabamento_efeito', 'curvatura_indicada', 'beneficio_principal', 
    'tom_cor', 'volume_peso', 'material'
]

# Cria o soup concatenando apenas as colunas que existem no resultado
df_final['soup'] = ''
for col in cols_soup:
    if col in df_final.columns:
        df_final['soup'] += ' ' + df_final[col].fillna('').astype(str)

df_final['soup'] = df_final['soup'].str.lower().str.strip()

print("\n--- AMOSTRA PROCESSADA ---")
print(df_final[['input_original', 'soup']].head())

df_final.to_csv("resultado_normalizacao_ia_unificado.csv", index=False)