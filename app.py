import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------------------------------------------------
# 🎛 Sayfa Ayarları
# -------------------------------------------------------------------
st.set_page_config(page_title="Anket Analizi", layout="wide")

st.title("📊 Çalışan Deneyimi Anket Analizi")

# -------------------------------------------------------------------
# 1) Excel'i yükleme
# -------------------------------------------------------------------
file_path = "anket.xlsx"

@st.cache_data
def load_data(path):
    return pd.read_excel(path)

try:
    df = load_data(file_path)
except FileNotFoundError:
    st.error(f"❌ '{file_path}' dosyası bulunamadı. Dosya adını ve konumunu kontrol et.")
    st.stop()

# -------------------------------------------------------------------
# 2) Likert ve Demografik Tanımlar
# -------------------------------------------------------------------
likert_values = [
    "Kesinlikle Katılıyorum",
    "Katılıyorum",
    "Kararsızım",
    "Katılmıyorum",
    "Kesinlikle Katılmıyorum"
]

# Demografik kolonlar (Excel'deki başlıklara birebir)
gender_col = "1.Cinsiyetiniz nedir?"
age_col = "2. Yaş aralığınız nedir?"
exp_col = "3.Şirkette ne kadar süredir çalışıyorsunuz?"
pos_col = "Pozisyon grubunuz nedir?"
dept_col = "Departmanınız nedir?"

demographic_columns = {
    "Cinsiyet": gender_col,
    "Yaş Aralığı": age_col,
    "Çalışma Süresi": exp_col,
    "Pozisyon": pos_col,
    "Departman": dept_col
}

# Önce demografik kolonlar gerçekten var mı kontrol edelim
missing_demo_cols = [col for col in demographic_columns.values() if col not in df.columns]

if missing_demo_cols:
    st.error(f"❌ Excel içinde bulunamayan demografik kolon(lar): {missing_demo_cols}")
    st.write("Mevcut kolonlar:", df.columns.tolist())
    st.stop()

# -------------------------------------------------------------------
# 3) Soru Kolonlarını Belirleme
#    (Demografik olmayan tüm kolonlar soru kabul edilir)
# -------------------------------------------------------------------
all_cols = df.columns.tolist()
demo_cols_list = list(demographic_columns.values())

question_cols = [c for c in all_cols if c not in demo_cols_list]

if not question_cols:
    st.error("❌ Soru kolonları bulunamadı. Demografik kolonlar dışındaki sütunlar soru olarak kabul edilecekti.")
    st.write("Tüm kolonlar:", all_cols)
    st.stop()

with st.expander("📂 Debug: Kolon Listesi (kontrol için)", expanded=False):
    st.write("Tüm kolonlar:", all_cols)
    st.write("Demografik kolonlar:", demo_cols_list)
    st.write("Soru kolonları:", question_cols)

# -------------------------------------------------------------------
# 4) Filtre Alanı (Sidebar)
# -------------------------------------------------------------------
st.sidebar.header("🔍 Filtreler")

filtered_df = df.copy()

for ui_label, col_name in demographic_columns.items():
    unique_vals = df[col_name].dropna().unique().tolist()
    unique_vals = sorted(unique_vals)  # daha düzenli görünmesi için

    selected = st.sidebar.multiselect(ui_label, unique_vals)

    if selected:
        filtered_df = filtered_df[filtered_df[col_name].isin(selected)]

# Filtre sonrası hiç veri kalmadıysa uyarı ver
if filtered_df.empty:
    st.warning("⚠ Seçili filtrelere uyan katılımcı bulunamadı. Filtreleri azaltmayı deneyin.")
    st.stop()

# -------------------------------------------------------------------
# 5) Analiz Edilecek Soru Seçimi
# -------------------------------------------------------------------
selected_question = st.selectbox("Bir soru seçiniz:", question_cols)

st.subheader(f"📌 Soru Analizi: **{selected_question}**")

# Seçilen soru kolonunun gerçekten var olup olmadığını garanti edelim
if selected_question not in filtered_df.columns:
    st.error(f"❌ Seçilen soru kolonu bulunamadı: {selected_question}")
    st.stop()

# -------------------------------------------------------------------
# 6) Yüzdelikleri Hesaplama
# -------------------------------------------------------------------
# Değerleri say, normalize=True → oran; 100 ile çarp → yüzde
value_counts = (
    filtered_df[selected_question]
    .value_counts(normalize=True)
    .reindex(likert_values)   # Likert sırasını korumak için
    .fillna(0) * 100
)

result_df = pd.DataFrame({
    "Cevap": likert_values,
    "Yüzde (%)": value_counts.values
})

st.write("🔢 Yüzdelik Dağılımı")
st.dataframe(result_df, use_container_width=True)

# -------------------------------------------------------------------
# 7) Grafik Gösterimi
# -------------------------------------------------------------------
fig = px.bar(
    result_df,
    x="Cevap",
    y="Yüzde (%)",
    color="Cevap",
    title=f"{selected_question} - Cevap Dağılımı",
    text="Yüzde (%)",
    template="plotly_white"
)

fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
fig.update_layout(
    yaxis=dict(range=[0, 100]),
    xaxis_title="Cevap",
    yaxis_title="Yüzde (%)",
    legend_title="Cevap"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------------
# 8) Genel Özet
# -------------------------------------------------------------------
total_participants = len(filtered_df)

st.info(
    f"📌 **Filtre uygulanmış toplam katılımcı sayısı:** {total_participants}\n\n"
    f"Bu tablo ve grafik, seçili demografik filtrelere göre dinamik olarak güncellenmektedir."
)
