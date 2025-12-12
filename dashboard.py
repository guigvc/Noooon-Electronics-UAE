import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import time

# ==========================================
# ⚙️ 1. Configuration
# ==========================================
st.set_page_config(page_title="Noon UAE Bestsellers", layout="wide", page_icon="🌍")

# Anchor for top scrolling
st.markdown('<div id="top_anchor"></div>', unsafe_allow_html=True)

# ⚠️ DATA PATH (Ensure this is correct)
DATA_FILE = "noon_data.parquet"

# Initialize Session State
if 'selected_category_state' not in st.session_state:
    st.session_state.selected_category_state = None

# Initialize scroll trigger (0 means inactive on load)
if 'scroll_trigger_id' not in st.session_state:
    st.session_state.scroll_trigger_id = 0 

# ==========================================
# 📂 2. Data Loading & Cleaning
# ==========================================
@st.cache_data
def load_data():
    try:
        df = pd.read_parquet(DATA_FILE)
        
        # Map Chinese column names to internal variables if needed, 
        # or just ensure target column exists.
        if '类目' in df.columns: df['Target_Category'] = df['类目']
        elif '所属类目' in df.columns: df['Target_Category'] = df['所属类目']
        else: st.error("Error: Category column missing."); st.stop()

        # Default country if missing
        if '国家' not in df.columns: df['国家'] = '阿联酋'

        # Fix numeric columns (remove commas)
        cols_to_fix = ['销量数字', '评论数', '价格', '评分', '排名']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '').str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

df_raw = load_data()
if df_raw.empty: st.stop()

# ==========================================
# 🌍 3. Country Selection (English UI)
# ==========================================
st.sidebar.header("🌍 Region Selection")

# Create a mapping for UI display (English) -> Data value (Chinese)
country_map = {
    "UAE": "阿联酋",
    "KSA": "沙特"
}

# Determine default index
available_countries_cn = df_raw['国家'].unique().tolist()
available_countries_en = [k for k, v in country_map.items() if v in available_countries_cn]

default_idx = 0
if "UAE" in available_countries_en: 
    default_idx = available_countries_en.index("UAE")

selected_country_en = st.sidebar.radio(
    "Select Target Market:",
    options=available_countries_en,
    index=default_idx,
    horizontal=True
)

# Filter data based on Chinese value
selected_country_cn = country_map[selected_country_en]
df = df_raw[df_raw['国家'] == selected_country_cn].copy()

# Set Currency Symbol
currency_symbol = "AED"
if selected_country_en == "KSA": currency_symbol = "SAR"
elif selected_country_en == "UAE": currency_symbol = "AED"

st.sidebar.markdown("---")

# ==========================================
# 🧮 4. Data Aggregation
# ==========================================
base_stats = df.groupby('Target_Category').agg(
    product_count=('产品名', 'count'),
    total_sales=('销量数字', 'sum'),
    total_reviews=('评论数', 'sum')
).reset_index()

def get_top10_sum(group):
    return group.nlargest(10, '销量数字')['销量数字'].sum()

top10_stats = df.groupby('Target_Category').apply(get_top10_sum).reset_index(name='top10_sales')
category_stats = pd.merge(base_stats, top10_stats, on='Target_Category')

# ==========================================
# 🎨 5. Filters & Sorting (English UI)
# ==========================================
st.sidebar.header("🔍 Filters & Sorting")

sort_options = ["By Total Sales (Heat)", "By Total Reviews (Maturity)"]
sort_mode = st.sidebar.radio("Sort Categories By:", sort_options, index=0)

st.sidebar.markdown("---")

min_products = st.sidebar.slider(
    "Min Products per Category", 
    0, int(category_stats['product_count'].max()), 10
)
min_sales = st.sidebar.slider(
    "Min Total Sales Volume", 
    0, int(category_stats['total_sales'].max()), 0
)

# Apply Filters
filtered_cats_df = category_stats[
    (category_stats['product_count'] >= min_products) & 
    (category_stats['total_sales'] >= min_sales)
]

# Apply Sorting
if sort_mode == "By Total Sales (Heat)":
    filtered_cats_df = filtered_cats_df.sort_values(by='total_sales', ascending=False)
else:
    filtered_cats_df = filtered_cats_df.sort_values(by='total_reviews', ascending=False)

valid_categories = filtered_cats_df['Target_Category'].tolist()
df_filtered = df[df['Target_Category'].isin(valid_categories)]

# ==========================================
# 📊 6. Main Dashboard
# ==========================================
st.title(f"Noon Bestsellers - {selected_country_en}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("📦 Filtered Cats", f"{len(valid_categories)}")
c2.metric("🛒 Total Products", f"{len(df_filtered):,}")
c3.metric("🔥 Total Sales", f"{filtered_cats_df['total_sales'].sum():,}")
c4.metric("💬 Total Reviews", f"{filtered_cats_df['total_reviews'].sum():,}")
st.markdown("---")

# ==========================================
# 🔲 7. Category Matrix
# ==========================================
st.subheader(f"📋 {selected_country_en} - Category Matrix")
st.caption(f"Current Sort: {sort_mode}")

cols_per_row = 5
rows = [valid_categories[i:i + cols_per_row] for i in range(0, len(valid_categories), cols_per_row)]

for row_cats in rows:
    cols = st.columns(cols_per_row)
    for index, cat_name in enumerate(row_cats):
        cat_data = filtered_cats_df[filtered_cats_df['Target_Category'] == cat_name].iloc[0]
        
        # Dynamic label based on sort mode
        if "Sales" in sort_mode:
            metric_text = f"🔥 Top10 Sales: {int(cat_data['top10_sales']):,}"
        else:
            metric_text = f"💬 Total Reviews: {int(cat_data['total_reviews']):,}"

        with cols[index]:
            label = f"**{cat_name}**\n\n🛒 {cat_data['product_count']} | {metric_text}"
            if st.button(label, key=cat_name, use_container_width=True):
                st.session_state.selected_category_state = cat_name
                # Update timestamp to trigger scroll and image refresh
                st.session_state.scroll_trigger_id = int(time.time())

# Auto-scroll JS Script
if st.session_state.scroll_trigger_id > 0:
    js = f"""
    <script>
        var element = window.parent.document.getElementById("detail_anchor");
        if (element) {{
            element.scrollIntoView({{behavior: "smooth", block: "start"}});
        }}
    </script>
    """
    components.html(js, height=0)

# ==========================================
# 🕵️ 8. Category Details
# ==========================================
st.markdown("---")
st.markdown('<div id="detail_anchor"></div>', unsafe_allow_html=True) 
st.header("🔎 Category Details")

current_cat = st.session_state.selected_category_state
if current_cat not in valid_categories:
    current_cat = valid_categories[0] if valid_categories else None

if current_cat:
    subset = df[df['Target_Category'] == current_cat].sort_values(by='排名', ascending=True)
    
    st.markdown(f"### 📦 Selected: <span style='color:#FF4B4B'>{current_cat}</span> ({selected_country_en})", unsafe_allow_html=True)
    
    view_mode = st.radio("👀 View Mode", ["Large Image List (Recommended)", "Compact Table"], horizontal=True)

    if "Large Image List" in view_mode:
        st.info("💡 Hint: Largest images, best for viewing product details.")
        for _, row in subset.iterrows():
            with st.container(border=True):
                col_img, col_info = st.columns([1, 4])
                with col_img:
                    raw_url = row['原图链接']
                    if raw_url and raw_url.startswith('http'):
                        separator = "&" if "?" in raw_url else "?"
                        # Force refresh image using timestamp
                        refresh_id = st.session_state.scroll_trigger_id if st.session_state.scroll_trigger_id > 0 else 0
                        refresh_url = f"{raw_url}{separator}v={refresh_id}"
                        st.image(refresh_url, use_container_width=True)
                    else:
                        st.text("No Image")
                with col_info:
                    st.markdown(f"### [#{row['排名']}] {row['产品名']}({row['商品链接']})")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Price", f"{row['价格']} {currency_symbol}") 
                    m2.metric("Rating", f"{row['评分']} ⭐ ({int(row['评论数'])})")
                    m3.metric("Recent Sales", f"{int(row['销量数字'])}")
                    m4.markdown(f"**Sales Info:** {row['销量描述']}")
                    
                    sales_val = int(row['销量数字'])
                    max_val = int(df['销量数字'].max())
                    progress_val = min(sales_val / max_val, 1.0) if max_val > 0 else 0
                    st.progress(progress_val, text=f"Global Sales Heat: {int(progress_val*100)}%")
    else:
        # Table Mode Configuration
        possible_cols = ['排名', '原图链接', '产品名', '价格', '评分', '评论数', '销量数字', '销量描述', '商品链接']
        final_cols = [c for c in possible_cols if c in subset.columns]
        
        st.dataframe(
            subset[final_cols],
            column_config={
                "原图链接": st.column_config.ImageColumn("Image", width="large"),
                "商品链接": st.column_config.LinkColumn("Link", display_text="Buy Now"),
                "销量数字": st.column_config.ProgressColumn("Heat", format="%d", min_value=0, max_value=int(df['销量数字'].max())),
                "价格": st.column_config.NumberColumn(f"Price ({currency_symbol})", format="%.2f"),
                "排名": st.column_config.NumberColumn("Rank", format="#%d"),
                "产品名": "Product Name",
                "评分": st.column_config.NumberColumn("Rating", format="%.1f ⭐"),
                "评论数": st.column_config.NumberColumn("Reviews"),
                "销量描述": "Sales Text"
            },
            use_container_width=True,
            height=1000,
            hide_index=True
        )
else:
    st.warning(f"👈 No data matches the filters for {selected_country_en}.")

# ==========================================
# ⬆️ 9. Back to Top
# ==========================================
st.markdown("---")
col_b1, col_b2, col_b3 = st.columns([1, 2, 1])

with col_b2:
    if st.button("⬆️ Back to Top (Select another category)", use_container_width=True):
        js_top = """
        <script>
            var element = window.parent.document.getElementById("top_anchor");
            if (element) {
                element.scrollIntoView({behavior: "smooth", block: "start"});
            }
        </script>
        """

        components.html(js_top, height=0)
