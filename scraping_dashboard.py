import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import streamlit as st
import plotly.express as px


# Verificar se os módulos necessários estão instalados
def check_dependencies():
    try:
        import requests
        import bs4
        import pandas
        import sqlite3
        import streamlit
        import plotly
    except ModuleNotFoundError as e:
        print(f"Erro: Módulo não encontrado: {e.name}")
        sys.exit(1)


check_dependencies()

# 1. Web Scraping - Coletando dados de estatísticas de jogadores
URL = "https://fbref.com/en/comps/9/Premier-League-Stats"
headers = {"User-Agent": "Mozilla/5.0"}
try:
    response = requests.get(URL, headers=headers)
    response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
except requests.exceptions.RequestException as e:
    print(f"Erro na requisição: {e}")
    sys.exit(1)

soup = BeautifulSoup(response.text, 'html.parser')

table = soup.find("table", {"id": "stats_standard_9"})  # Exemplo para Premier League
if table is None:
    print("Erro: Tabela de estatísticas não encontrada.")
    sys.exit(1)

# Extraindo os dados
data = []
for row in table.find_all("tr")[1:]:
    cols = row.find_all("td")
    if cols and len(cols) > 6:
        player = cols[0].text.strip()
        team = cols[1].text.strip()
        goals = cols[5].text.strip() if cols[5].text.strip().isdigit() else "0"
        assists = cols[6].text.strip() if cols[6].text.strip().isdigit() else "0"
        data.append([player, team, int(goals), int(assists)])

# Criando DataFrame
df = pd.DataFrame(data, columns=["Player", "Team", "Goals", "Assists"])

# 2. Salvando os dados no banco de dados SQL
conn = sqlite3.connect("football_stats.db")
df.to_sql("players", conn, if_exists="replace", index=False)
conn.close()

# 3. Criando Dashboard Interativo com Streamlit
st.title("Estatísticas da Premier League")

# Conectando ao banco de dados
conn = sqlite3.connect("football_stats.db")
df = pd.read_sql("SELECT * FROM players", conn)
conn.close()

if df.empty:
    st.error("Nenhum dado disponível. Verifique a fonte dos dados.")
else:
    time_selecionado = st.selectbox("Selecione um time", df["Team"].unique())

    # Filtrando os dados
    df_filtered = df[df["Team"] == time_selecionado]
    st.dataframe(df_filtered)

    # Gráfico interativo
    if not df_filtered.empty:
        fig = px.bar(df_filtered, x="Player", y="Goals", title=f"Gols por Jogador - {time_selecionado}")
        st.plotly_chart(fig)
    else:
        st.warning("Nenhum dado disponível para este time.")
