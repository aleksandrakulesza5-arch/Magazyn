import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- 1. KONFIGURACJA POŁĄCZENIA ---
SUPABASE_URL = "https://lebwwcdxktfrnlvfzdpu.supabase.co"
SUPABASE_KEY = "sb_publishable_DesBgdUsTaKyIbwoeK4Yyw_sRqfgEih"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- 2. FUNKCJE DO BAZY ---
def get_data(table_name):
    try:
        res = supabase.table(table_name).select("*").execute()
        return res.data
    except Exception as e:
        return []

# --- 3. INTERFEJS ---
st.set_page_config(page_title="WMS PRO + Raporty", layout="wide")
st.title("📦 System Zarządzania Magazynem")

tab_p, tab_k, tab_r = st.tabs(["🚀 Produkty", "📂 Kategorie", "📊 Raporty"])

# --- SEKCJA KATEGORII ---
with tab_k:
    st.header("Zarządzanie Kategoriami")
    with st.form("add_kat", clear_on_submit=True):
        n_kat = st.text_input("Nazwa nowej kategorii")
        if st.form_submit_button("Dodaj kategorię"):
            if n_kat:
                supabase.table("kategorie").insert({"nazwa": n_kat}).execute()
                st.success(f"Dodano: {n_kat}")
                st.rerun()

    kat_list = get_data("kategorie")
    if kat_list:
        df_k = pd.DataFrame(kat_list)
        st.table(df_k[["id", "nazwa"]])
        kat_del = st.selectbox("Wybierz kategorię do usunięcia", [k['nazwa'] for k in kat_list], key="del_kat")
        if st.button("Usuń kategorię"):
            supabase.table("kategorie").delete().eq("nazwa", kat_del).execute()
            st.rerun()

# --- SEKCJA PRODUKTÓW ---
with tab_p:
    st.header("Stan Magazynowy")
    kat_list = get_data("kategorie")
    nazwy_kat = [k['nazwa'] for k in kat_list] if kat_list else []

    if not nazwy_kat:
        st.info("Dodaj najpierw kategorię w zakładce obok.")
    else:
        with st.expander("➕ Dodaj nowy produkt"):
            with st.form("add_prod", clear_on_submit=True):
                col1, col2 = st.columns(2)
                p_nazwa = col1.text_input("Nazwa")
                p_kat = col1.selectbox("Kategoria", nazwy_kat)
                p_ilosc = col2.number_input("Ilość", min_value=0, step=1)
                p_cena = col2.number_input("Cena (PLN)", min_value=0.0, format="%.2f")
                if st.form_submit_button("Zapisz produkt"):
                    if p_nazwa:
                        supabase.table("produkty").insert({"nazwa": p_nazwa, "kategoria": p_kat, "ilosc": p_ilosc, "cena": p_cena}).execute()
                        st.rerun()

    prod_list = get_data("produkty")
    if prod_list:
        df_p = pd.DataFrame(prod_list)
        st.dataframe(df_p[["id", "nazwa", "kategoria", "ilosc", "cena"]], use_container_width=True)
        p_del = st.selectbox("Wybierz produkt do usunięcia", df_p['nazwa'].tolist(), key="del_prod")
        if st.button("Usuń produkt"):
            supabase.table("produkty").delete().eq("nazwa", p_del).execute()
            st.rerun()
    else:
        st.write("Brak produktów.")

# --- SEKCJA RAPORTÓW ---
with tab_r:
    st.header("📊 Raport Magazynowy")
    
    prod_data = get_data("produkty")
    if prod_data:
        df_r = pd.DataFrame(prod_data)
        
        # Obliczenia
        df_r['wartosc_calkowita'] = df_r['ilosc'] * df_r['cena']
        total_value = df_r['wartosc_calkowita'].sum()
        total_items = df_r['ilosc'].sum()
        
        # Wskaźniki (Metrics)
        m1, m2, m3 = st.columns(3)
        m1.metric("Całkowita wartość", f"{total_value:,.2f} PLN")
        m2.metric("Liczba produktów (szt.)", int(total_items))
        m3.metric("Liczba pozycji", len(df_r))
        
        st.divider()
        
        col_charts1, col_charts2 = st.columns(2)
        
        with col_charts1:
            st.subheader("Ilość produktów wg kategorii")
            # Grupowanie danych do wykresu
            chart_data = df_r.groupby('kategoria')['ilosc'].sum()
            st.bar_chart(chart_data)
            
        with col_charts2:
            st.subheader("Wartość towaru wg kategorii")
            val_chart_data = df_r.groupby('kategoria')['wartosc_calkowita'].sum()
            st.area_chart(val_chart_data)

        # Możliwość pobrania raportu do CSV
        st.divider()
        csv = df_r[["nazwa", "kategoria", "ilosc", "cena", "wartosc_calkowita"]].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Pobierz raport jako CSV",
            data=csv,
            file_name='raport_magazynowy.csv',
            mime='text/csv',
        )
    else:
        st.info("Brak danych do wygenerowania raportu. Dodaj produkty do bazy.")
