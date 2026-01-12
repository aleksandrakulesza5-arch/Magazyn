import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. KONFIGURACJA POŁĄCZENIA Z SUPABASE
# Zastąp poniższe dane swoimi danymi z panelu Supabase (Project Settings -> API)
SUPABASE_URL = "TWOJ_URL_SUPABASE"
SUPABASE_KEY = "TWOJ_KLUCZ_API_ANON"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- INTERFEJS UŻYTKOWNIKA ---
st.set_page_config(page_title="WMS Supabase", layout="wide")
st.title("📦 Magazyn WMS z Supabase")

# Sidebar - Nawigacja
menu = st.sidebar.selectbox("Menu", ["Produkty", "Kategorie"])

# --- SEKCJA KATEGORII ---
if menu == "Kategorie":
    st.header("🗂️ Zarządzanie Kategoriami")
    
    # Dodawanie kategorii
    with st.form("add_category_form"):
        nowa_kat = st.text_input("Nazwa nowej kategorii")
        if st.form_submit_button("Dodaj kategorię"):
            if nowa_kat:
                supabase.table("kategorie").insert({"nazwa": nowa_kat}).execute()
                st.success(f"Dodano kategorię: {nowa_kat}")
                st.rerun()

    # Wyświetlanie i usuwanie kategorii
    res_kat = supabase.table("kategorie").select("*").execute()
    if res_kat.data:
        df_kat = pd.DataFrame(res_kat.data)
        st.table(df_kat)
        
        kat_to_delete = st.selectbox("Wybierz kategorię do usunięcia", df_kat['nazwa'].tolist())
        if st.button("Usuń kategorię"):
            supabase.table("kategorie").delete().eq("nazwa", kat_to_delete).execute()
            st.warning(f"Usunięto kategorię: {kat_to_delete}")
            st.rerun()

# --- SEKCJA PRODUKTÓW ---
else:
    st.header("📦 Zarządzanie Produktami")

    # Pobieranie kategorii do selectboxa
    res_kat = supabase.table("kategorie").select("nazwa").execute()
    list_kat = [item['nazwa'] for item in res_kat.data] if res_kat.data else []

    if not list_kat:
        st.error("Najpierw dodaj przynajmniej jedną kategorię!")
    else:
        # Formularz dodawania produktu
        with st.expander("➕ Dodaj nowy produkt"):
            with st.form("add_product_form"):
                nazwa = st.text_input("Nazwa produktu")
                kategoria = st.selectbox("Kategoria", list_kat)
                ilosc = st.number_input("Ilość", min_value=0, step=1)
                cena = st.number_input("Cena (PLN)", min_value=0.0, format="%.2f")
                
                if st.form_submit_button("Dodaj do magazynu"):
                    if nazwa:
                        data = {
                            "nazwa": nazwa,
                            "kategoria": kategoria,
                            "ilosc": ilosc,
                            "cena": cena
                        }
                        supabase.table("produkty").insert(data).execute()
                        st.success("Produkt dodany!")
                        st.rerun()

    # Wyświetlanie tabeli produktów
    res_prod = supabase.table("produkty").select("*").execute()
    if res_prod.data:
        df_prod = pd.DataFrame(res_prod.data)
        st.dataframe(df_prod, use_container_width=True)

        # Usuwanie produktu
        with st.expander("🗑️ Usuń produkt"):
            prod_to_delete = st.selectbox("Wybierz produkt do usunięcia", df_prod['nazwa'].tolist())
            if st.button("Potwierdź usunięcie produktu"):
                supabase.table("produkty").delete().eq("nazwa", prod_to_delete).execute()
                st.warning(f"Usunięto produkt: {prod_to_delete}")
                st.rerun()
    else:
        st.info("Brak produktów w bazie.")
