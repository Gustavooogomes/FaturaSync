import streamlit as st
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

# Configuração da página do Streamlit
st.set_page_config(page_title="FaturaSync", page_icon="💳", layout="centered")

# Carrega as senhas do .env
load_dotenv()
DB_URL = os.getenv('DATABASE_URL')

# Função com cache para o Streamlit não sobrecarregar o banco de dados
@st.cache_data(ttl=10) # Atualiza a cada 10 segundos
def buscar_resumo():
    conn = psycopg2.connect(DB_URL)
    query = "SELECT responsavel, total_devido, quantidade_compras FROM resumo_fatura;"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=10)
def buscar_ultimas_transacoes():
    conn = psycopg2.connect(DB_URL)
    query = """
    SELECT m.nome as "Pessoa", d.valor as "Valor (R$)", d.descricao as "Descrição", 
           to_char(d.data_compra, 'DD/MM/YY HH24:MI') as "Data"
    FROM despesas d 
    JOIN membros m ON d.membro_id = m.id 
    ORDER BY d.data_compra DESC LIMIT 5;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- INTERFACE DO USUÁRIO ---

st.title("💳 FaturaSync - Acerto de Contas")
st.write("Visão geral em tempo real da fatura compartilhada.")

# Puxa os dados da View
df_resumo = buscar_resumo()

if not df_resumo.empty:
    # Cria colunas dinamicamente baseado em quantas pessoas têm dívidas
    colunas = st.columns(len(df_resumo))
    
    for index, row in df_resumo.iterrows():
        with colunas[index]:
            st.metric(
                label=row['responsavel'], 
                value=f"R$ {row['total_devido']:.2f}", 
                delta=f"{row['quantidade_compras']} compras",
                delta_color="off"
            )
            
    st.divider()
    
    # Gráfico simples para visualização
    st.subheader("📊 Proporção da Fatura")
    st.bar_chart(df_resumo.set_index('responsavel')['total_devido'])
else:
    st.success("Nenhuma despesa pendente! Fatura zerada.")

st.divider()

# Tabela com o histórico das últimas 5 compras
st.subheader("🛒 Últimos Gastos Registrados")
df_ultimas = buscar_ultimas_transacoes()
st.dataframe(df_ultimas, use_container_width=True, hide_index=True)