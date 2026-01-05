from busca import carregar_sinonimos, buscar_com_ia, normalizar_dataframe
import pandas as pd

mapper = carregar_sinonimos("synonyms.txt")
df = pd.read_csv('resultado_normalizacao_ia_unificado.csv')
df_normalizado = normalizar_dataframe(df=df)

print("------------- BUSCADOR INTELIGENTE -------------\n")

busca_user = input("Digite sua Busca\n")

results = buscar_com_ia(query_usuario=busca_user, df=df_normalizado, mapper=mapper)
print("------------- RESULTADOS -------------\n")
for i in results:
  print(i)

