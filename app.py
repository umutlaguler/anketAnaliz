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

# Demografik kolonların varlığını kontrol et
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
# 6) Seçilen Soru İçin Yüzde + Adet Hesaplama
# -------------------------------------------------------------------
q_series = filtered_df[selected_question]

# Adet
counts = (
    q_series
    .value_counts(dropna=False)
    .reindex(likert_values)
    .fillna(0)
    .astype(int)
)

total_answers = counts.sum()

if total_answers == 0:
    st.warning("Bu soru için geçerli cevap bulunamadı.")
else:
    # Yüzde
    perc = (counts / total_answers * 100).round(2)

    result_df = pd.DataFrame({
        "Cevap": likert_values,
        "Adet": counts.values,
        "Yüzde (%)": perc.values
    })

    # Bar üstünde hem adet hem yüzde gösterelim: "12 (%34.3)"
    result_df["Etiket"] = result_df.apply(
        lambda r: f"{int(r['Adet'])} (%{r['Yüzde (%)']:.1f})",
        axis=1
    )

    st.write("🔢 Seçilen Soru İçin Yüzdelik ve Adet Dağılımı")
    st.dataframe(result_df, use_container_width=True)

    # -------------------------------------------------------------------
    # 7) Seçilen Soru İçin Grafik
    # -------------------------------------------------------------------
    fig = px.bar(
        result_df,
        x="Cevap",
        y="Yüzde (%)",
        color="Cevap",
        title=f"{selected_question} - Cevap Dağılımı (Adet + Yüzde)",
        text="Etiket",
        template="plotly_white"
    )

    fig.update_traces(textposition='outside')
    fig.update_layout(
        yaxis=dict(range=[0, 100]),
        xaxis_title="Cevap",
        yaxis_title="Yüzde (%)",
        legend_title="Cevap",
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------------
# 8) TÜM SORULAR İÇİN GENEL LİKERT DAĞILIMI
# -------------------------------------------------------------------
st.subheader("🌍 Genel Dağılım: Tüm Soruların Cevapları")

# Tüm soru kolonlarını al, uzun formata çevir
all_answers_series = filtered_df[question_cols].melt(value_name="Cevap")["Cevap"]

# Sadece tanımlı Likert cevaplarını dikkate al (diğerlerini drop)
all_answers_series = all_answers_series[all_answers_series.isin(likert_values)]

all_counts = (
    all_answers_series
    .value_counts()
    .reindex(likert_values)
    .fillna(0)
    .astype(int)
)

all_total = all_counts.sum()

if all_total == 0:
    st.warning("Genel dağılım için geçerli cevap bulunamadı.")
else:
    all_perc = (all_counts / all_total * 100).round(2)

    overall_df = pd.DataFrame({
        "Cevap": likert_values,
        "Adet": all_counts.values,
        "Yüzde (%)": all_perc.values
    })

    overall_df["Etiket"] = overall_df.apply(
        lambda r: f"{int(r['Adet'])} (%{r['Yüzde (%)']:.1f})",
        axis=1
    )

    st.write("🔢 Tüm Sorular İçin Toplam Cevap Dağılımı (Filtreler Dikkate Alınarak)")
    st.dataframe(overall_df, use_container_width=True)

    fig_overall = px.bar(
        overall_df,
        x="Cevap",
        y="Yüzde (%)",
        color="Cevap",
        title="Tüm Sorular - Genel Likert Dağılımı (Adet + Yüzde)",
        text="Etiket",
        template="plotly_white"
    )

    fig_overall.update_traces(textposition='outside')
    fig_overall.update_layout(
        yaxis=dict(range=[0, 100]),
        xaxis_title="Cevap",
        yaxis_title="Yüzde (%)",
        legend_title="Cevap",
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    st.plotly_chart(fig_overall, use_container_width=True)

# -------------------------------------------------------------------
# 9) Genel Özet
# -------------------------------------------------------------------
total_participants = len(filtered_df)

st.info(
    f"📌 **Filtre uygulanmış toplam katılımcı sayısı:** {total_participants}\n\n"
    f"Yukarıdaki ilk grafik yalnızca seçili soruyu, ikinci grafik ise aynı filtrelerle **tüm soruların toplam cevap dağılımını** göstermektedir."
)
