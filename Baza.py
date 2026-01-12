import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- 1. KONFIGURACJA POŁĄCZENIA ---
# Upewnij się, że używasz klucza 'anon' oraz 'public'
SUPABASE_URL = "https://lebwwcdxktfrnlvfzdpu.supabase.co"
SUPABASE_KEY = "sb_publishable_DesBgdUsTaKyIbwoeK4Yyw_sRqfgEih"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- 2. FUNKCJE DO BAZY ---
def get_data(table_name):
    res = supabase.table(table_name).select("*").execute()
    return res.data

# --- 3. INTERFEJS ---
st.set_page_config(page_title="WMS PRO", layout="wide")
st.title("📦 System Zarządzania Magazynem")

tab_p, tab_k = st.tabs(["🚀 Produkty", "📂 Kategorie"])

# --- SEKCJA KATEGORII ---
with tab_k:
    st.header("Zarządzanie Kategoriami")
    
    # Dodawanie
    with st.form("add_kat", clear_on_submit=True):
        n_kat = st.text_input("Nazwa nowej kategorii")
        if st.form_submit_button("Dodaj kategorię"):
            if n_kat:
                supabase.table("kategorie").insert({"nazwa": n_kat}).execute()
                st.success(f"Dodano: {n_kat}")
                st.rerun()

    # Wyświetlanie i Usuwanie
    kat_list = get_data("kategorie")
    if kat_list:
        df_k = pd.DataFrame(kat_list)
        st.table(df_k[["id", "nazwa"]])
        
        kat_del = st.selectbox("Wybierz kategorię do usunięcia", [k['nazwa'] for k in kat_list])
        if st.button("Usuń kategorię"):
            # Cascade usuwa też produkty z tej kategorii
            supabase.table("kategorie").delete().eq("nazwa", kat_del).execute()
            st.rerun()

# --- SEKCJA PRODUKTÓW ---
with tab_p:
    st.header("Stan Magazynowy")
    
    kat_list = get_data("kategorie")
    nazwy_kat = [k['nazwa'] for k in kat_list]

    if not nazwy_kat:
        st.info("Dodaj najpierw kategorię w zakładce obok.")
    else:
        # Formularz produktu
        with st.expander("➕ Dodaj nowy produkt"):
            with st.form("add_prod", clear_on_submit=True):
                col1, col2 = st.columns(2)
                p_nazwa = col1.text_input("Nazwa")
                p_kat = col1.selectbox("Kategoria", nazwy_kat)
                p_ilosc = col2.number_input("Ilość", min_value=0)
                p_cena = col2.number_input("Cena (PLN)", min_value=0.0)
                
                if st.form_submit_button("Zapisz produkt"):
                    if p_nazwa:
                        supabase.table("produkty").insert({
                            "nazwa": p_nazwa, 
                            "kategoria": p_kat, 
                            "ilosc": p_ilosc, 
                            "cena": p_cena
                        }).execute()
                        st.rerun()

    # Tabela produktów
    prod_list = get_data("produkty")
    if prod_list:
        df_p = pd.DataFrame(prod_list)
        st.dataframe(df_p[["id", "nazwa", "kategoria", "ilosc", "cena"]], use_container_width=True)
        
        p_del = st.selectbox("Wybierz produkt do usunięcia", df_p['nazwa'].tolist())
        if st.button("Usuń produkt"):
            supabase.table("produkty").delete().eq("nazwa", p_del).execute()
            st.rerun()
    else:
        st.write("Brak produktów.")
