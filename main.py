import io
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from pathlib import Path

script_dir = Path(__file__).parent.resolve()

# --- Sidebar Navigation ---
st.sidebar.title("🔍 Navigation")
page = st.sidebar.selectbox("Go to:", ["📌 Individual Analysis", "📊 Overall Analysis"])

# --- File Upload ---
# st.sidebar.markdown("### 📂 Upload CSV File")
#uploaded_file = st.sidebar.file_uploader("", type=["csv"])
uploaded_file = script_dir / 'input/raw_data.csv'

if uploaded_file:
    df = pd.read_csv(uploaded_file, index_col=0)

    # --- Show Data Preview on Both Pages ---
    st.write("### 📜 Dataset")
    st.dataframe(df)
    n_respondents = len(df.index)
    st.write(f"#### # of respondents: {n_respondents}")

    if page == "📌 Individual Analysis":
        # --- Individual Search Page ---
        st.title("📌 Individual Spiritual Gifts Analysis")

        name = st.selectbox(label='Name to view their spiritual gifts',
                            placeholder="🔍 **Enter a name to view their spiritual gifts:**",
                            options=list(df.index))  

        if name in df.index:
            sorted_gifts = df.loc[name].sort_values(ascending=False)
            top_cutoff, bottom_cutoff = sorted_gifts.nlargest(3).min(), sorted_gifts.nsmallest(3).max()
            top_3 = sorted_gifts[sorted_gifts >= top_cutoff].index.tolist()
            bottom_3 = sorted_gifts[sorted_gifts <= bottom_cutoff].index.tolist()

            st.markdown(f"### ✨ {name}'s Top Spiritual Gifts")
            st.success(", ".join(top_3))

            st.markdown(f"### ⚠️ {name}'s Bottom Spiritual Gifts")
            st.error(", ".join(bottom_3))

        elif name:
            st.warning("⚠️ Name not found in dataset!")

    elif page == "📊 Overall Analysis":
        # --- Overall Analysis Page ---
        st.title("📊 Overall Spiritual Gifts Analysis")
        st.divider()

        top_counts, bottom_counts = Counter(), Counter()
        export_data = []

        for index, row in df.iterrows():
            top_cutoff, bottom_cutoff = row.nlargest(3).min(), row.nsmallest(3).max()
            top_3, bottom_3 = row[row >= top_cutoff].index.tolist(), row[row <= bottom_cutoff].index.tolist()

            top_counts.update(top_3)
            bottom_counts.update(bottom_3)

            export_data.append({"Name": index, "Top Gifts": ", ".join(top_3), "Bottom Gifts": ", ".join(bottom_3)})

        top_df = pd.DataFrame(top_counts.items(), columns=["Gift", "Count"]).sort_values(by="Count", ascending=False)
        bottom_df = pd.DataFrame(bottom_counts.items(), columns=["Gift", "Count"]).sort_values(by="Count", ascending=False)

        # --- Pie Chart Function ---
        def plot_pie_chart(df, title, colors):
            fig, ax = plt.subplots(figsize=(6, 6))

            # Sort values and determine top 5 (including ties)
            df_sorted = df.sort_values(by="Count", ascending=False)
            top_5_cutoff = df_sorted.iloc[6]["Count"] if len(df_sorted) > 6 else df_sorted.iloc[-1]["Count"]
            top_5 = df_sorted[df_sorted["Count"] >= top_5_cutoff]
            others = df_sorted[df_sorted["Count"] < top_5_cutoff]

            # Labels and sizes for top 5
            labels = top_5["Gift"].tolist()
            sizes = top_5["Count"].tolist()
            colors_used = list(plt.cm.Paired.colors[:len(top_5)])

            # If there are "Others", sum them and keep their colors
            if not others.empty:
                labels.append("Others")  # Single label for all others
                sizes.append(others["Count"].sum())
                colors_used.extend(plt.cm.Paired.colors[len(top_5):len(top_5) + len(others)])  # Keep individual colors

            # Function to format autopct (hides percentage for "Others")
            def autopct_func(pct, index):
                actual_count = sizes[index]
                percentage = (actual_count / n_respondents) * 100  # Now uses total_rows
                return f"{percentage:.1f}%" if labels[index] != "Others" else ""

            # Create pie chart
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct=lambda pct: autopct_func(pct, sizes.index(int(round(pct * sum(sizes) / 100)))),
                colors=colors_used,
                startangle=140,
                explode=[0.1 if i < len(top_5) else 0 for i in range(len(labels))],
            )

            ax.set_title(title)
            return fig

        # --- Display Side by Side ---
        st.markdown("### 😇 **Top Spiritual Gifts**")
        st.dataframe(top_df, hide_index=True)

        
        fig1 = plot_pie_chart(top_df, "😇 Top Spiritual Gifts", plt.cm.Paired.colors)
        st.pyplot(fig1)

        st.divider()

        st.markdown("### ⚠️ **Bottom Spiritual Gifts**")
        st.dataframe(bottom_df, hide_index=True)

        fig2 = plot_pie_chart(bottom_df, "⚠️ Bottom Spiritual Gifts", plt.cm.Set3.colors)
        st.pyplot(fig2)

        # --- Save Images for Export ---
        top_img_buffer, bottom_img_buffer = io.BytesIO(), io.BytesIO()
        fig1.savefig(top_img_buffer, format="png", bbox_inches="tight")
        fig2.savefig(bottom_img_buffer, format="png", bbox_inches="tight")
        top_img_buffer.seek(0), bottom_img_buffer.seek(0)

        # --- Export CSV ---
        csv_buffer = io.StringIO()
        pd.DataFrame(export_data).to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        # --- Styled Buttons ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button("📥 Download Top Gifts Chart", top_img_buffer, "top_spiritual_gifts.png", "image/png")
        with col2:
            st.download_button("📥 Download Bottom Gifts Chart", bottom_img_buffer, "bottom_spiritual_gifts.png", "image/png")
        with col3:
            st.download_button("📊 Download Full Report", csv_data, "spiritual_gifts_analysis.csv", "text/csv")

